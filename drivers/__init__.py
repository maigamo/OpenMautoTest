"""
OpenMautoTest 驱动器模块

导出所有测试驱动器：Web端、小程序端、API客户端
"""

from .web import BaseWebDriver, WebPage, WebDriverError
from .mini import BaseMiniDriver, MiniPage, MiniDriverError
from .api import BaseAPIClient, APIClientError

__all__ = [
    # Web端驱动器
    'BaseWebDriver',
    'WebPage',
    'WebDriverError',
    
    # 小程序驱动器
    'BaseMiniDriver', 
    'MiniPage',
    'MiniDriverError',
    
    # API客户端
    'BaseAPIClient',
    'APIClientError'
]

# 版本信息
__version__ = '1.0.0'