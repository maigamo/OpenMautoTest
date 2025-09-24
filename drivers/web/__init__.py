"""
OpenMautoTest Web端驱动器模块

导出Web端自动化测试相关的驱动器和页面对象
"""

from .base_web_driver import BaseWebDriver, WebPage, WebDriverError

__all__ = [
    'BaseWebDriver',
    'WebPage', 
    'WebDriverError'
]

# 版本信息
__version__ = '1.0.0'