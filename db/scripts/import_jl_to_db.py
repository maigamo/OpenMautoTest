"""
OpenMautoTest 历史数据导入脚本

将JSONL格式的历史测试数据导入到数据库中
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from common.logger import get_logger
from common.utils.time_utils import Timer
from orchestrator.recorder import HybridRecorder, get_recorder
from configs.settings import get_settings


class DataImporter:
    """数据导入器"""
    
    def __init__(self, batch_size: int = 100):
        """初始化数据导入器
        
        Args:
            batch_size: 批量处理大小
        """
        self.settings = get_settings()
        self.logger = get_logger("data_importer")
        self.batch_size = batch_size
        self.recorder = get_recorder()
        
        # 统计信息
        self.stats = {
            'total_records': 0,
            'imported_records': 0,
            'failed_records': 0,
            'skipped_records': 0
        }
    
    def parse_jsonl_file(self, file_path: Path) -> List[Dict]:
        """解析JSONL文件
        
        Args:
            file_path: JSONL文件路径
        
        Returns:
            解析后的记录列表
        """
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Invalid JSON at line {line_num}: {e}")
                        self.stats['failed_records'] += 1
            
            self.logger.info(f"Parsed {len(records)} records from {file_path}")
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to parse file {file_path}: {e}")
            return []
    
    def transform_record(self, record: Dict) -> Optional[Dict]:
        """转换记录格式
        
        Args:
            record: 原始记录
        
        Returns:
            转换后的记录，失败时返回None
        """
        try:
            # 基础字段映射
            transformed = {
                'run_id': record.get('run_id', 'imported'),
                'project_name': record.get('project_name', 'unknown'),
                'flow_name': record.get('flow_name', 'unknown'),
                'test_case_name': record.get('test_case_name', record.get('name', 'unknown')),
                'status': self._normalize_status(record.get('status', 'unknown')),
                'environment': record.get('environment', record.get('env', 'unknown'))
            }
            
            # 时间字段处理
            if 'start_time' in record:
                transformed['start_time'] = self._parse_timestamp(record['start_time'])
            
            if 'end_time' in record:
                transformed['end_time'] = self._parse_timestamp(record['end_time'])
            
            if 'duration' in record:
                transformed['duration'] = float(record['duration'])
            
            # 错误信息
            if 'error' in record or 'failure_reason' in record:
                transformed['failure_reason'] = record.get('failure_reason', record.get('error', ''))
            
            # 构建信息
            if 'jenkins_url' in record:
                transformed['jenkins_build_url'] = record['jenkins_url']
            
            if 'build_number' in record:
                transformed['build_number'] = str(record['build_number'])
            
            # 浏览器信息
            if 'browser' in record:
                browser_info = record['browser']
                if isinstance(browser_info, dict):
                    transformed['browser_type'] = browser_info.get('name', 'unknown')
                    transformed['browser_version'] = browser_info.get('version', 'unknown')
                else:
                    transformed['browser_type'] = str(browser_info)
            
            # 平台信息
            if 'platform' in record:
                transformed['platform'] = record['platform']
            
            # 测试数据
            if 'test_data' in record:
                transformed['test_data'] = record['test_data']
            
            # 标签
            if 'tags' in record:
                transformed['tags'] = record['tags']
            
            # 性能数据
            if 'page_load_time' in record:
                transformed['page_load_time'] = float(record['page_load_time'])
            
            if 'network_time' in record:
                transformed['network_time'] = float(record['network_time'])
            
            # 截图
            if 'screenshots' in record:
                transformed['screenshots'] = record['screenshots']
            
            # 日志文件
            if 'log_file' in record:
                transformed['log_file_path'] = record['log_file']
            
            # 重试次数
            if 'retry_count' in record:
                transformed['retry_attempt'] = int(record['retry_count'])
            
            return transformed
            
        except Exception as e:
            self.logger.warning(f"Failed to transform record: {e}")
            return None
    
    def _normalize_status(self, status: str) -> str:
        """标准化状态值
        
        Args:
            status: 原始状态
        
        Returns:
            标准化后的状态
        """
        status = status.lower().strip()
        
        if status in ['pass', 'passed', 'success', 'ok']:
            return 'passed'
        elif status in ['fail', 'failed', 'failure', 'error']:
            return 'failed'
        elif status in ['skip', 'skipped', 'ignore', 'ignored']:
            return 'skipped'
        elif status in ['run', 'running', 'executing']:
            return 'running'
        else:
            return 'pending'
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳字符串
        
        Args:
            timestamp_str: 时间戳字符串
        
        Returns:
            解析后的datetime对象
        """
        if not timestamp_str:
            return None
        
        # 尝试多种时间格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d %H:%M:%S.%f'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # 尝试解析Unix时间戳
        try:
            timestamp = float(timestamp_str)
            if timestamp > 1e10:  # 毫秒时间戳
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp)
        except (ValueError, OSError):
            pass
        
        self.logger.warning(f"Failed to parse timestamp: {timestamp_str}")
        return None
    
    def import_records(self, records: List[Dict]) -> None:
        """导入记录
        
        Args:
            records: 记录列表
        """
        self.stats['total_records'] = len(records)
        
        with Timer() as timer:
            for i, record in enumerate(records):
                try:
                    # 转换记录格式
                    transformed = self.transform_record(record)
                    if transformed is None:
                        self.stats['skipped_records'] += 1
                        continue
                    
                    # 导入记录
                    result = self.recorder.record_test_case_run(transformed)
                    if result is not None:
                        self.stats['imported_records'] += 1
                    else:
                        self.stats['failed_records'] += 1
                    
                    # 显示进度
                    if (i + 1) % self.batch_size == 0:
                        progress = (i + 1) / len(records) * 100
                        self.logger.info(f"Progress: {progress:.1f}% ({i + 1}/{len(records)})")
                
                except Exception as e:
                    self.logger.error(f"Failed to import record {i}: {e}")
                    self.stats['failed_records'] += 1
        
        # 输出统计信息
        elapsed_time = timer.elapsed_time()
        self.logger.info(f"Import completed in {elapsed_time:.2f}s")
        self.logger.info(f"Statistics: {self.stats}")
    
    def import_from_file(self, file_path: Path) -> None:
        """从文件导入数据
        
        Args:
            file_path: 文件路径
        """
        self.logger.info(f"Starting import from {file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() == '.jsonl':
            records = self.parse_jsonl_file(file_path)
        elif file_path.suffix.lower() == '.json':
            # 处理单个JSON文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records = data
                    else:
                        records = [data]
            except Exception as e:
                self.logger.error(f"Failed to parse JSON file: {e}")
                return
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        if records:
            self.import_records(records)
        else:
            self.logger.warning("No records found to import")
    
    def import_from_directory(self, directory: Path, pattern: str = "*.jsonl") -> None:
        """从目录导入数据
        
        Args:
            directory: 目录路径
            pattern: 文件模式
        """
        self.logger.info(f"Starting import from directory {directory} with pattern {pattern}")
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        files = list(directory.glob(pattern))
        if not files:
            self.logger.warning(f"No files found matching pattern {pattern}")
            return
        
        self.logger.info(f"Found {len(files)} files to import")
        
        for file_path in files:
            try:
                self.import_from_file(file_path)
            except Exception as e:
                self.logger.error(f"Failed to import from {file_path}: {e}")
    
    def close(self):
        """关闭导入器"""
        if self.recorder:
            self.recorder.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Import historical test data to database')
    parser.add_argument('path', help='Path to JSONL file or directory')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    parser.add_argument('--pattern', default='*.jsonl', help='File pattern for directory import')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # 配置日志级别
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建导入器
    importer = DataImporter(batch_size=args.batch_size)
    
    try:
        path = Path(args.path)
        
        if path.is_file():
            importer.import_from_file(path)
        elif path.is_dir():
            importer.import_from_directory(path, args.pattern)
        else:
            print(f"Error: Path not found: {path}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Import failed: {e}")
        sys.exit(1)
    
    finally:
        importer.close()
    
    print("Import completed successfully")


if __name__ == "__main__":
    main()
