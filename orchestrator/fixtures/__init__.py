"""
OpenMautoTest 测试上下文和fixtures模块

导出Web端和小程序端的测试上下文管理功能
"""

from .web_context import WebTestContext, web_driver, web_context, web_test_data
from .mini_context import MiniTestContext, mini_driver, mini_context, mini_test_data

__all__ = [
    # Web测试上下文
    'WebTestContext',
    'web_driver',
    'web_context', 
    'web_test_data',
    
    # 小程序测试上下文
    'MiniTestContext',
    'mini_driver',
    'mini_context',
    'mini_test_data'
]

# 版本信息
__version__ = '1.0.0'
