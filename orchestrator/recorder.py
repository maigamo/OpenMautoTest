"""
OpenMautoTest 数据记录器模块

实现数据持久化功能，支持批量数据写入和异常处理
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from common.logger import get_logger
from common.utils.file_utils import ensure_dir, write_json_file
from common.utils.time_utils import Timer
from configs.db import get_db_config
from configs.settings import get_settings
from db.models import Base, TestCaseRun, TestStep, TestRunSummary


class RecorderError(Exception):
    """记录器异常"""
    pass


class DatabaseRecorder:
    """数据库记录器"""
    
    def __init__(self, batch_size: int = 100, max_retries: int = 3):
        """初始化数据库记录器
        
        Args:
            batch_size: 批量写入大小
            max_retries: 最大重试次数
        """
        self.settings = get_settings()
        self.logger = get_logger("db_recorder")
        self.batch_size = batch_size
        self.max_retries = max_retries
        
        self._engine = None
        self._session_factory = None
        self._batch_buffer: List[Dict[str, Any]] = []
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化数据库连接"""
        try:
            db_config = get_db_config()
            database_url = db_config.get_postgresql_url()
            
            self._engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                echo=self.settings.is_development()
            )
            
            self._session_factory = sessionmaker(bind=self._engine)
            
            # 测试连接
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.logger.info("Database connection initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database connection: {e}")
            self._engine = None
            self._session_factory = None
    
    def _get_session(self) -> Optional[Session]:
        """获取数据库会话
        
        Returns:
            数据库会话对象
        """
        if self._session_factory is None:
            self.logger.warning("Database not initialized, attempting to reconnect")
            self._initialize_database()
        
        if self._session_factory is not None:
            return self._session_factory()
        
        return None
    
    def _retry_operation(self, operation: callable, *args, **kwargs) -> Any:
        """重试操作
        
        Args:
            operation: 要执行的操作函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            操作结果
        
        Raises:
            RecorderError: 重试失败后抛出
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Operation failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                
                if attempt < self.max_retries:
                    # 指数退避
                    wait_time = (2 ** attempt) * 0.5
                    time.sleep(wait_time)
                    
                    # 尝试重新初始化数据库连接
                    if isinstance(e, SQLAlchemyError):
                        self._initialize_database()
        
        raise RecorderError(f"Operation failed after {self.max_retries + 1} attempts: {last_exception}")
    
    def create_test_case_run(self, data: Dict[str, Any]) -> Optional[int]:
        """创建测试用例执行记录
        
        Args:
            data: 测试用例数据
        
        Returns:
            创建的记录ID，失败时返回None
        """
        def _create_record():
            session = self._get_session()
            if session is None:
                raise RecorderError("Database session not available")
            
            try:
                # 确保必需字段存在
                if 'run_id' not in data:
                    data['run_id'] = str(uuid.uuid4())
                
                if 'test_case_name' not in data:
                    raise ValueError("test_case_name is required")
                
                # 设置默认值
                data.setdefault('status', 'pending')
                data.setdefault('retry_attempt', 0)
                data.setdefault('is_deleted', False)
                
                # 创建记录
                record = TestCaseRun.create_from_dict(data)
                session.add(record)
                session.commit()
                
                record_id = record.id
                self.logger.info(f"Created test case run record: {record_id}")
                return record_id
                
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        
        try:
            return self._retry_operation(_create_record)
        except Exception as e:
            self.logger.error(f"Failed to create test case run: {e}")
            return None
    
    def update_test_case_run(self, record_id: int, data: Dict[str, Any]) -> bool:
        """更新测试用例执行记录
        
        Args:
            record_id: 记录ID
            data: 更新数据
        
        Returns:
            是否更新成功
        """
        def _update_record():
            session = self._get_session()
            if session is None:
                raise RecorderError("Database session not available")
            
            try:
                record = session.query(TestCaseRun).filter_by(id=record_id).first()
                if record is None:
                    raise ValueError(f"Test case run not found: {record_id}")
                
                # 更新字段
                for key, value in data.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                
                # 更新时间
                record.updated_at = datetime.now()
                
                session.commit()
                self.logger.info(f"Updated test case run record: {record_id}")
                return True
                
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        
        try:
            return self._retry_operation(_update_record)
        except Exception as e:
            self.logger.error(f"Failed to update test case run {record_id}: {e}")
            return False
    
    def create_test_step(self, test_case_run_id: int, data: Dict[str, Any]) -> Optional[int]:
        """创建测试步骤记录
        
        Args:
            test_case_run_id: 测试用例执行记录ID
            data: 步骤数据
        
        Returns:
            创建的步骤ID，失败时返回None
        """
        def _create_step():
            session = self._get_session()
            if session is None:
                raise RecorderError("Database session not available")
            
            try:
                # 设置关联ID
                data['test_case_run_id'] = test_case_run_id
                
                # 确保必需字段存在
                if 'step_name' not in data:
                    raise ValueError("step_name is required")
                
                if 'step_order' not in data:
                    raise ValueError("step_order is required")
                
                # 设置默认值
                data.setdefault('status', 'pending')
                
                # 创建步骤记录
                step = TestStep(**data)
                session.add(step)
                session.commit()
                
                step_id = step.id
                self.logger.info(f"Created test step record: {step_id}")
                return step_id
                
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        
        try:
            return self._retry_operation(_create_step)
        except Exception as e:
            self.logger.error(f"Failed to create test step: {e}")
            return None
    
    def create_test_run_summary(self, data: Dict[str, Any]) -> Optional[int]:
        """创建测试运行汇总记录
        
        Args:
            data: 汇总数据
        
        Returns:
            创建的汇总ID，失败时返回None
        """
        def _create_summary():
            session = self._get_session()
            if session is None:
                raise RecorderError("Database session not available")
            
            try:
                # 确保必需字段存在
                if 'run_id' not in data:
                    data['run_id'] = str(uuid.uuid4())
                
                # 设置默认值
                data.setdefault('total_tests', 0)
                data.setdefault('passed_tests', 0)
                data.setdefault('failed_tests', 0)
                data.setdefault('skipped_tests', 0)
                
                # 计算通过率
                if data['total_tests'] > 0:
                    data['pass_rate'] = (data['passed_tests'] / data['total_tests']) * 100
                else:
                    data['pass_rate'] = 0
                
                # 创建汇总记录
                summary = TestRunSummary(**data)
                session.add(summary)
                session.commit()
                
                summary_id = summary.id
                self.logger.info(f"Created test run summary: {summary_id}")
                return summary_id
                
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        
        try:
            return self._retry_operation(_create_summary)
        except Exception as e:
            self.logger.error(f"Failed to create test run summary: {e}")
            return None
    
    def batch_insert(self, records: List[Dict[str, Any]], table_type: str = "test_case_run") -> List[int]:
        """批量插入记录
        
        Args:
            records: 记录列表
            table_type: 表类型 (test_case_run, test_step, test_run_summary)
        
        Returns:
            成功插入的记录ID列表
        """
        def _batch_insert():
            session = self._get_session()
            if session is None:
                raise RecorderError("Database session not available")
            
            try:
                inserted_ids = []
                
                for record_data in records:
                    if table_type == "test_case_run":
                        record = TestCaseRun.create_from_dict(record_data)
                    elif table_type == "test_step":
                        record = TestStep(**record_data)
                    elif table_type == "test_run_summary":
                        record = TestRunSummary(**record_data)
                    else:
                        raise ValueError(f"Unsupported table type: {table_type}")
                    
                    session.add(record)
                
                session.commit()
                
                # 获取插入的ID
                for record_data in records:
                    # 这里需要根据实际情况获取ID
                    inserted_ids.append(0)  # 占位符
                
                self.logger.info(f"Batch inserted {len(records)} {table_type} records")
                return inserted_ids
                
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        
        try:
            return self._retry_operation(_batch_insert)
        except Exception as e:
            self.logger.error(f"Failed to batch insert {table_type} records: {e}")
            return []
    
    def add_to_batch(self, record: Dict[str, Any]):
        """添加记录到批量缓冲区
        
        Args:
            record: 记录数据
        """
        self._batch_buffer.append(record)
        
        if len(self._batch_buffer) >= self.batch_size:
            self.flush_batch()
    
    def flush_batch(self) -> bool:
        """刷新批量缓冲区
        
        Returns:
            是否成功刷新
        """
        if not self._batch_buffer:
            return True
        
        try:
            self.batch_insert(self._batch_buffer)
            self._batch_buffer.clear()
            return True
        except Exception as e:
            self.logger.error(f"Failed to flush batch: {e}")
            return False
    
    def get_test_case_runs(
        self,
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        environment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """查询测试用例执行记录
        
        Args:
            run_id: 运行ID
            status: 状态
            environment: 环境
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            测试用例记录列表
        """
        session = self._get_session()
        if session is None:
            return []
        
        try:
            query = session.query(TestCaseRun).filter(TestCaseRun.is_deleted == False)
            
            if run_id:
                query = query.filter(TestCaseRun.run_id == run_id)
            
            if status:
                query = query.filter(TestCaseRun.status == status)
            
            if environment:
                query = query.filter(TestCaseRun.environment == environment)
            
            records = query.offset(offset).limit(limit).all()
            return [record.to_dict() for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to query test case runs: {e}")
            return []
        finally:
            session.close()
    
    def close(self):
        """关闭记录器"""
        # 刷新剩余的批量数据
        self.flush_batch()
        
        if self._engine:
            self._engine.dispose()
            self.logger.info("Database recorder closed")


class FileRecorder:
    """文件记录器（降级模式）"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """初始化文件记录器
        
        Args:
            output_dir: 输出目录
        """
        self.settings = get_settings()
        self.logger = get_logger("file_recorder")
        
        if output_dir is None:
            output_dir = self.settings.get_output_dir() / "records"
        
        self.output_dir = ensure_dir(output_dir)
        self.logger.info(f"File recorder initialized: {self.output_dir}")
    
    def record(self, data: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """记录数据到文件
        
        Args:
            data: 要记录的数据
            filename: 文件名，为None时自动生成
        
        Returns:
            记录文件路径
        """
        if filename is None:
            timestamp = int(time.time() * 1000)
            filename = f"record_{timestamp}.json"
        
        file_path = self.output_dir / filename
        
        try:
            write_json_file(file_path, data)
            self.logger.info(f"Recorded data to file: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Failed to record data to file: {e}")
            raise RecorderError(f"File recording failed: {e}")


class HybridRecorder:
    """混合记录器（数据库+文件降级）"""
    
    def __init__(self, batch_size: int = 100, max_retries: int = 3):
        """初始化混合记录器
        
        Args:
            batch_size: 批量写入大小
            max_retries: 最大重试次数
        """
        self.logger = get_logger("hybrid_recorder")
        self.db_recorder = DatabaseRecorder(batch_size, max_retries)
        self.file_recorder = FileRecorder()
        self._use_database = self.db_recorder._engine is not None
        
        # 记录数据库状态
        if self._use_database:
            self.logger.info("数据库连接成功，将使用数据库记录测试数据")
        else:
            self.logger.warning("数据库连接失败，将使用文件记录测试数据（降级模式）")
            self.logger.warning("请检查数据库配置和服务状态，或运行数据库初始化脚本")
    
    def record_test_case_run(self, data: Dict[str, Any]) -> Optional[Union[int, Path]]:
        """记录测试用例执行数据
        
        Args:
            data: 测试用例数据
        
        Returns:
            数据库记录ID或文件路径
        """
        if self._use_database:
            try:
                record_id = self.db_recorder.create_test_case_run(data)
                if record_id is not None:
                    return record_id
                else:
                    self.logger.warning("Database recording failed, falling back to file")
                    self._use_database = False
            except Exception as e:
                self.logger.error(f"Database recording error: {e}")
                self._use_database = False
        
        # 降级到文件记录
        try:
            filename = f"test_case_run_{data.get('run_id', 'unknown')}_{int(time.time())}.json"
            return self.file_recorder.record(data, filename)
        except Exception as e:
            self.logger.error(f"File recording also failed: {e}")
            return None
    
    def record_test_step(self, test_case_run_id: Union[int, Path], data: Dict[str, Any]) -> Optional[Union[int, Path]]:
        """记录测试步骤数据
        
        Args:
            test_case_run_id: 测试用例执行记录ID或文件路径
            data: 步骤数据
        
        Returns:
            数据库记录ID或文件路径
        """
        # 如果test_case_run_id是Path对象，说明主记录已经降级到文件模式
        if isinstance(test_case_run_id, Path):
            self.logger.info(f"Parent record is file-based, using file recording for step")
            self._use_database = False
        
        if self._use_database and isinstance(test_case_run_id, int):
            try:
                step_id = self.db_recorder.create_test_step(test_case_run_id, data)
                if step_id is not None:
                    return step_id
                else:
                    self.logger.warning("Database step recording failed, falling back to file")
                    self._use_database = False
            except Exception as e:
                self.logger.error(f"Database step recording error: {e}")
                self._use_database = False
        
        # 降级到文件记录
        try:
            # 对于文件记录，保存关联信息但不依赖数据库ID
            if isinstance(test_case_run_id, Path):
                data['parent_file'] = str(test_case_run_id)
                parent_identifier = test_case_run_id.stem
            else:
                data['test_case_run_id'] = test_case_run_id
                parent_identifier = str(test_case_run_id)
            
            filename = f"test_step_{parent_identifier}_{data.get('step_order', 0)}_{int(time.time())}.json"
            return self.file_recorder.record(data, filename)
        except Exception as e:
            self.logger.error(f"File step recording also failed: {e}")
            return None
    
    def close(self):
        """关闭记录器"""
        if self.db_recorder:
            self.db_recorder.close()


# 全局记录器实例
_recorder: Optional[HybridRecorder] = None


def get_recorder() -> HybridRecorder:
    """获取全局记录器实例
    
    Returns:
        混合记录器实例
    """
    global _recorder
    if _recorder is None:
        _recorder = HybridRecorder()
    return _recorder


def close_recorder():
    """关闭全局记录器"""
    global _recorder
    if _recorder is not None:
        _recorder.close()
        _recorder = None


if __name__ == "__main__":
    # 测试记录器功能
    print("Testing recorder functionality...")
    
    # 创建测试数据
    test_data = {
        'run_id': str(uuid.uuid4()),
        'test_case_name': 'test_login',
        'status': 'passed',
        'environment': 'development',
        'start_time': datetime.now(),
        'end_time': datetime.now(),
        'duration': 5.2,
        'browser_type': 'chromium'
    }
    
    # 测试记录器
    recorder = get_recorder()
    
    try:
        result = recorder.record_test_case_run(test_data)
        print(f"Recorded test case run: {result}")
        
        if isinstance(result, int):
            # 记录测试步骤
            step_data = {
                'step_name': 'enter_username',
                'step_order': 1,
                'status': 'passed',
                'start_time': datetime.now(),
                'duration': 1.0
            }
            
            step_result = recorder.record_test_step(result, step_data)
            print(f"Recorded test step: {step_result}")
    
    finally:
        close_recorder()
    
    print("Recorder tests completed.")
