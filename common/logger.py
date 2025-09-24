"""
OpenMautoTest 统一日志管理模块

提供多级别日志输出、文件轮转和清理机制
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

import structlog
from loguru import logger as loguru_logger

from configs.settings import get_settings


class OpenMautoTestLogger:
    """OpenMautoTest 日志管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_structlog()
        self._setup_loguru()
    
    def _setup_structlog(self):
        """配置structlog"""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.getLevelName(self.settings.LOG_LEVEL)
            ),
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    def _setup_loguru(self):
        """配置loguru"""
        # 移除默认handler
        loguru_logger.remove()
        
        # 添加控制台输出
        loguru_logger.add(
            sys.stderr,
            level=self.settings.LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # 添加文件输出
        log_file = self.settings.get_logs_dir() / "openmautotest.log"
        loguru_logger.add(
            str(log_file),
            level=self.settings.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
                   "{name}:{function}:{line} - {message}",
            rotation=self.settings.LOG_MAX_SIZE,
            retention=self.settings.LOG_BACKUP_COUNT,
            compression="gz",
            encoding="utf-8"
        )
        
        # 添加错误日志文件
        error_log_file = self.settings.get_logs_dir() / "error.log"
        loguru_logger.add(
            str(error_log_file),
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
                   "{name}:{function}:{line} - {message}\n{exception}",
            rotation="1 day",
            retention="30 days",
            compression="gz",
            encoding="utf-8"
        )
    
    def get_logger(self, name: str, use_structlog: bool = False) -> Union[logging.Logger, structlog.BoundLogger]:
        """获取日志记录器
        
        Args:
            name: 日志记录器名称
            use_structlog: 是否使用structlog
        
        Returns:
            日志记录器实例
        """
        if use_structlog:
            return structlog.get_logger(name)
        
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(getattr(logging, self.settings.LOG_LEVEL))
            
            # 避免重复添加handler
            if not logger.handlers:
                # 控制台handler
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(getattr(logging, self.settings.LOG_LEVEL))
                console_formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler.setFormatter(console_formatter)
                logger.addHandler(console_handler)
                
                # 文件handler
                log_file = self.settings.get_logs_dir() / f"{name}.log"
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=self._parse_size(self.settings.LOG_MAX_SIZE),
                    backupCount=self.settings.LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, self.settings.LOG_LEVEL))
                file_formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节数"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件
        
        Args:
            days: 保留天数
        """
        logs_dir = self.settings.get_logs_dir()
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for log_file in logs_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    print(f"Deleted old log file: {log_file}")
                except Exception as e:
                    print(f"Failed to delete log file {log_file}: {e}")


class TestLogger:
    """测试专用日志记录器"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.logger = get_logger(f"test.{test_name}")
        self.step_count = 0
    
    def step(self, description: str):
        """记录测试步骤"""
        self.step_count += 1
        self.logger.info(f"Step {self.step_count}: {description}")
    
    def assertion(self, condition: bool, message: str):
        """记录断言结果"""
        if condition:
            self.logger.info(f"✓ Assertion passed: {message}")
        else:
            self.logger.error(f"✗ Assertion failed: {message}")
    
    def screenshot(self, screenshot_path: str):
        """记录截图"""
        self.logger.info(f"Screenshot saved: {screenshot_path}")
    
    def error(self, error: Exception, context: str = ""):
        """记录错误"""
        error_msg = f"Error in {context}: {str(error)}" if context else f"Error: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
    
    def performance(self, action: str, duration: float):
        """记录性能数据"""
        self.logger.info(f"Performance - {action}: {duration:.2f}s")


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, logger: logging.Logger, context: str):
        self.logger = logger
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.context}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed {self.context} in {duration:.2f}s")
        else:
            self.logger.error(f"Failed {self.context} after {duration:.2f}s: {exc_val}")
        
        return False  # 不抑制异常


# 全局日志管理器实例
_logger_manager: Optional[OpenMautoTestLogger] = None


def get_logger_manager() -> OpenMautoTestLogger:
    """获取全局日志管理器实例"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = OpenMautoTestLogger()
    return _logger_manager


def get_logger(name: str, use_structlog: bool = False) -> Union[logging.Logger, structlog.BoundLogger]:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称
        use_structlog: 是否使用structlog
    
    Returns:
        日志记录器实例
    """
    return get_logger_manager().get_logger(name, use_structlog)


def get_test_logger(test_name: str) -> TestLogger:
    """获取测试专用日志记录器
    
    Args:
        test_name: 测试名称
    
    Returns:
        测试日志记录器实例
    """
    return TestLogger(test_name)


def get_loguru_logger():
    """获取loguru日志记录器"""
    return loguru_logger


def cleanup_logs(days: int = 30):
    """清理旧日志文件
    
    Args:
        days: 保留天数
    """
    get_logger_manager().cleanup_old_logs(days)


def log_context(logger: logging.Logger, context: str) -> LogContext:
    """创建日志上下文管理器
    
    Args:
        logger: 日志记录器
        context: 上下文描述
    
    Returns:
        日志上下文管理器
    """
    return LogContext(logger, context)


# 便捷函数
def debug(message: str, logger_name: str = "main"):
    """记录调试信息"""
    get_logger(logger_name).debug(message)


def info(message: str, logger_name: str = "main"):
    """记录信息"""
    get_logger(logger_name).info(message)


def warning(message: str, logger_name: str = "main"):
    """记录警告"""
    get_logger(logger_name).warning(message)


def error(message: str, logger_name: str = "main", exc_info: bool = False):
    """记录错误"""
    get_logger(logger_name).error(message, exc_info=exc_info)


def critical(message: str, logger_name: str = "main"):
    """记录严重错误"""
    get_logger(logger_name).critical(message)


if __name__ == "__main__":
    # 测试日志系统
    print("Testing logging system...")
    
    # 基础日志测试
    logger = get_logger("test")
    logger.info("This is a test info message")
    logger.warning("This is a test warning message")
    logger.error("This is a test error message")
    
    # 测试日志记录器
    test_logger = get_test_logger("sample_test")
    test_logger.step("Navigate to login page")
    test_logger.assertion(True, "Login button is visible")
    test_logger.performance("page_load", 2.5)
    
    # loguru日志测试
    loguru = get_loguru_logger()
    loguru.info("This is a loguru test message")
    
    # 上下文日志测试
    with log_context(logger, "test operation"):
        import time
        time.sleep(0.1)
        logger.info("Operation in progress")
    
    print("Logging system tests completed.")
