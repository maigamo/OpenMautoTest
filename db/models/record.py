"""
OpenMautoTest 测试结果数据模型

定义测试用例执行记录的数据库表结构和ORM映射
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BIGINT, Boolean, Column, DateTime, Float, Integer, String, Text,
    Index, CheckConstraint, ForeignKey
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.types import TypeDecorator, VARCHAR

import json
import uuid


# 创建基类
Base = declarative_base()


class JSONType(TypeDecorator):
    """JSON类型装饰器，兼容不同数据库"""
    
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(Text())
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class TestCaseRun(Base):
    """测试用例执行记录表"""
    
    __tablename__ = 'test_case_runs'
    
    # 主键
    id = Column(BIGINT, primary_key=True, autoincrement=True, comment='唯一标识符')
    
    # 基础信息
    run_id = Column(String(255), nullable=False, comment='单次任务ID')
    project_name = Column(String(100), comment='项目/团队名称')
    flow_name = Column(String(255), comment='业务流程名称')
    test_case_name = Column(Text, nullable=False, comment='测试用例名称')
    
    # 执行结果
    status = Column(String(20), nullable=False, comment='执行结果 (passed/failed/skipped)')
    environment = Column(String(50), comment='测试环境')
    
    # 时间信息
    start_time = Column(DateTime(timezone=True), nullable=False, default=func.now(), comment='开始时间')
    end_time = Column(DateTime(timezone=True), comment='结束时间')
    duration = Column(Float, comment='执行耗时(秒)')
    
    # 错误信息
    failure_reason = Column(Text, comment='失败原因')
    error_details = Column(JSONType, comment='详细错误信息')
    
    # 重试信息
    retry_attempt = Column(Integer, default=0, comment='重试次数')
    
    # 构建信息
    jenkins_build_url = Column(Text, comment='Jenkins构建链接')
    build_number = Column(String(50), comment='构建编号')
    
    # 执行环境信息
    browser_type = Column(String(50), comment='浏览器类型')
    browser_version = Column(String(50), comment='浏览器版本')
    platform = Column(String(50), comment='执行平台')
    
    # 测试数据
    test_data = Column(JSONType, comment='测试数据')
    tags = Column(JSONType, comment='测试标签')
    
    # 性能数据
    page_load_time = Column(Float, comment='页面加载时间')
    network_time = Column(Float, comment='网络耗时')
    
    # 截图和日志
    screenshots = Column(JSONType, comment='截图文件路径列表')
    log_file_path = Column(String(500), comment='日志文件路径')
    
    # 创建和更新时间
    created_at = Column(DateTime(timezone=True), default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 软删除标记
    is_deleted = Column(Boolean, default=False, comment='是否删除')
    
    # 关联关系
    steps = relationship("TestStep", back_populates="test_case_run", cascade="all, delete-orphan")
    
    # 表约束
    __table_args__ = (
        Index('idx_run_id', 'run_id'),
        Index('idx_project_flow', 'project_name', 'flow_name'),
        Index('idx_status', 'status'),
        Index('idx_start_time', 'start_time'),
        Index('idx_environment', 'environment'),
        Index('idx_created_at', 'created_at'),
        CheckConstraint("status IN ('passed', 'failed', 'skipped', 'running', 'pending')", name='ck_status'),
        CheckConstraint('duration >= 0', name='ck_duration_positive'),
        CheckConstraint('retry_attempt >= 0', name='ck_retry_positive'),
        {'comment': '测试用例执行记录表'}
    )
    
    def __repr__(self):
        return f"<TestCaseRun(id={self.id}, test_case_name='{self.test_case_name}', status='{self.status}')>"
    
    def to_dict(self, include_steps: bool = False) -> Dict[str, Any]:
        """转换为字典
        
        Args:
            include_steps: 是否包含步骤信息
        
        Returns:
            字典表示
        """
        result = {
            'id': self.id,
            'run_id': self.run_id,
            'project_name': self.project_name,
            'flow_name': self.flow_name,
            'test_case_name': self.test_case_name,
            'status': self.status,
            'environment': self.environment,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'failure_reason': self.failure_reason,
            'error_details': self.error_details,
            'retry_attempt': self.retry_attempt,
            'jenkins_build_url': self.jenkins_build_url,
            'build_number': self.build_number,
            'browser_type': self.browser_type,
            'browser_version': self.browser_version,
            'platform': self.platform,
            'test_data': self.test_data,
            'tags': self.tags,
            'page_load_time': self.page_load_time,
            'network_time': self.network_time,
            'screenshots': self.screenshots,
            'log_file_path': self.log_file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted
        }
        
        if include_steps:
            result['steps'] = [step.to_dict() for step in self.steps]
        
        return result
    
    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> 'TestCaseRun':
        """从字典创建实例
        
        Args:
            data: 数据字典
        
        Returns:
            TestCaseRun实例
        """
        # 过滤掉None值和不存在的字段
        filtered_data = {}
        for key, value in data.items():
            if value is not None and hasattr(cls, key):
                # 处理时间字段
                if key in ('start_time', 'end_time', 'created_at', 'updated_at') and isinstance(value, str):
                    try:
                        filtered_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                else:
                    filtered_data[key] = value
        
        return cls(**filtered_data)


class TestStep(Base):
    """测试步骤记录表"""
    
    __tablename__ = 'test_steps'
    
    # 主键
    id = Column(BIGINT, primary_key=True, autoincrement=True, comment='唯一标识符')
    
    # 关联的测试用例
    test_case_run_id = Column(BIGINT, ForeignKey('test_case_runs.id', ondelete='CASCADE'), 
                              nullable=False, comment='关联的测试用例ID')
    
    # 步骤信息
    step_name = Column(String(255), nullable=False, comment='步骤名称')
    step_description = Column(Text, comment='步骤描述')
    step_order = Column(Integer, nullable=False, comment='步骤顺序')
    
    # 执行结果
    status = Column(String(20), nullable=False, comment='步骤状态 (passed/failed/skipped)')
    
    # 时间信息
    start_time = Column(DateTime(timezone=True), nullable=False, default=func.now(), comment='开始时间')
    end_time = Column(DateTime(timezone=True), comment='结束时间')
    duration = Column(Float, comment='执行耗时(秒)')
    
    # 错误信息
    error_message = Column(Text, comment='错误消息')
    error_details = Column(JSONType, comment='详细错误信息')
    
    # 步骤数据
    input_data = Column(JSONType, comment='输入数据')
    output_data = Column(JSONType, comment='输出数据')
    expected_result = Column(Text, comment='期望结果')
    actual_result = Column(Text, comment='实际结果')
    
    # 截图
    screenshot_path = Column(String(500), comment='截图路径')
    
    # 创建时间
    created_at = Column(DateTime(timezone=True), default=func.now(), comment='创建时间')
    
    # 关联关系
    test_case_run = relationship("TestCaseRun", back_populates="steps")
    
    # 表约束
    __table_args__ = (
        Index('idx_test_case_run_id', 'test_case_run_id'),
        Index('idx_step_name', 'step_name'),
        Index('idx_status', 'status'),
        Index('idx_step_order', 'step_order'),
        Index('idx_created_at', 'created_at'),
        CheckConstraint("status IN ('passed', 'failed', 'skipped', 'running', 'pending')", name='ck_step_status'),
        CheckConstraint('duration >= 0', name='ck_step_duration_positive'),
        CheckConstraint('step_order >= 0', name='ck_step_order_positive'),
        {'comment': '测试步骤记录表'}
    )
    
    def __repr__(self):
        return f"<TestStep(id={self.id}, step_name='{self.step_name}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            'id': self.id,
            'test_case_run_id': self.test_case_run_id,
            'step_name': self.step_name,
            'step_description': self.step_description,
            'step_order': self.step_order,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'expected_result': self.expected_result,
            'actual_result': self.actual_result,
            'screenshot_path': self.screenshot_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TestRunSummary(Base):
    """测试运行汇总表"""
    
    __tablename__ = 'test_run_summaries'
    
    # 主键
    id = Column(BIGINT, primary_key=True, autoincrement=True, comment='唯一标识符')
    
    # 运行信息
    run_id = Column(String(255), nullable=False, unique=True, comment='运行ID')
    run_name = Column(String(255), comment='运行名称')
    run_description = Column(Text, comment='运行描述')
    
    # 项目信息
    project_name = Column(String(100), comment='项目名称')
    environment = Column(String(50), comment='测试环境')
    
    # 时间信息
    start_time = Column(DateTime(timezone=True), nullable=False, default=func.now(), comment='开始时间')
    end_time = Column(DateTime(timezone=True), comment='结束时间')
    duration = Column(Float, comment='总耗时(秒)')
    
    # 统计信息
    total_tests = Column(Integer, default=0, comment='总测试数')
    passed_tests = Column(Integer, default=0, comment='通过测试数')
    failed_tests = Column(Integer, default=0, comment='失败测试数')
    skipped_tests = Column(Integer, default=0, comment='跳过测试数')
    pass_rate = Column(Float, comment='通过率')
    
    # 构建信息
    jenkins_build_url = Column(Text, comment='Jenkins构建链接')
    build_number = Column(String(50), comment='构建编号')
    
    # 执行环境
    browser_type = Column(String(50), comment='浏览器类型')
    platform = Column(String(50), comment='执行平台')
    
    # 创建时间
    created_at = Column(DateTime(timezone=True), default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 表约束
    __table_args__ = (
        Index('idx_run_id', 'run_id'),
        Index('idx_project_name', 'project_name'),
        Index('idx_environment', 'environment'),
        Index('idx_start_time', 'start_time'),
        Index('idx_created_at', 'created_at'),
        CheckConstraint('total_tests >= 0', name='ck_total_tests_positive'),
        CheckConstraint('passed_tests >= 0', name='ck_passed_tests_positive'),
        CheckConstraint('failed_tests >= 0', name='ck_failed_tests_positive'),
        CheckConstraint('skipped_tests >= 0', name='ck_skipped_tests_positive'),
        CheckConstraint('pass_rate >= 0 AND pass_rate <= 100', name='ck_pass_rate_range'),
        {'comment': '测试运行汇总表'}
    )
    
    def __repr__(self):
        return f"<TestRunSummary(run_id='{self.run_id}', total_tests={self.total_tests}, pass_rate={self.pass_rate})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            'id': self.id,
            'run_id': self.run_id,
            'run_name': self.run_name,
            'run_description': self.run_description,
            'project_name': self.project_name,
            'environment': self.environment,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'skipped_tests': self.skipped_tests,
            'pass_rate': self.pass_rate,
            'jenkins_build_url': self.jenkins_build_url,
            'build_number': self.build_number,
            'browser_type': self.browser_type,
            'platform': self.platform,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 导出所有模型
__all__ = ['Base', 'TestCaseRun', 'TestStep', 'TestRunSummary', 'JSONType']
