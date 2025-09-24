"""
OpenMautoTest API客户端模块

导出HTTP API客户端相关功能
"""

from .base_api_client import BaseAPIClient, APIClientError

__all__ = [
    'BaseAPIClient',
    'APIClientError'
]

# 版本信息
__version__ = '1.0.0'