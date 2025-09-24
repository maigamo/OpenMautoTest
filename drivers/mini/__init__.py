"""
OpenMautoTest 小程序驱动器模块

导出小程序自动化测试相关的驱动器和页面对象
"""

from .base_mini_driver import BaseMiniDriver, MiniPage, MiniDriverError

__all__ = [
    'BaseMiniDriver',
    'MiniPage',
    'MiniDriverError'
]

# 版本信息
__version__ = '1.0.0'