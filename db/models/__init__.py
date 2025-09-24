"""
OpenMautoTest 数据库模型

导出所有数据库模型和相关功能
"""

from .record import Base, TestCaseRun, TestStep, TestRunSummary, JSONType

__all__ = [
    'Base',
    'TestCaseRun', 
    'TestStep',
    'TestRunSummary',
    'JSONType'
]

# 版本信息
__version__ = '1.0.0'
