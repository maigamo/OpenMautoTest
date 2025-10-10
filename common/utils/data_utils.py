"""
OpenMautoTest 数据处理工具模块

提供数据清理、转换和验证功能
"""

from pathlib import Path
from typing import Any, Dict, List, Union


def sanitize_data_for_database(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理数据以适配数据库存储
    
    主要处理以下问题：
    1. 将Path对象转换为字符串，避免psycopg2适配器错误
    2. 处理其他不兼容的数据类型
    
    Args:
        data: 原始数据字典
        
    Returns:
        清理后的数据字典
        
    Examples:
        >>> from pathlib import Path
        >>> original_data = {
        ...     'file_path': Path('/tmp/test.txt'),
        ...     'name': 'test',
        ...     'count': 42
        ... }
        >>> cleaned_data = sanitize_data_for_database(original_data)
        >>> cleaned_data['file_path']  # 现在是字符串而不是Path对象
        '/tmp/test.txt'
    """
    cleaned_data = {}
    
    for key, value in data.items():
        if isinstance(value, Path):
            # 将Path对象转换为字符串
            cleaned_data[key] = str(value)
        elif isinstance(value, dict):
            # 递归处理嵌套字典
            cleaned_data[key] = sanitize_data_for_database(value)
        elif isinstance(value, list):
            # 处理列表中的Path对象
            cleaned_data[key] = _sanitize_list_for_database(value)
        else:
            cleaned_data[key] = value
    
    return cleaned_data


def _sanitize_list_for_database(lst: List[Any]) -> List[Any]:
    """清理列表中的数据以适配数据库存储
    
    Args:
        lst: 原始列表
        
    Returns:
        清理后的列表
    """
    cleaned_list = []
    
    for item in lst:
        if isinstance(item, Path):
            cleaned_list.append(str(item))
        elif isinstance(item, dict):
            cleaned_list.append(sanitize_data_for_database(item))
        elif isinstance(item, list):
            cleaned_list.append(_sanitize_list_for_database(item))
        else:
            cleaned_list.append(item)
    
    return cleaned_list


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """验证必需字段是否存在
    
    Args:
        data: 数据字典
        required_fields: 必需字段列表
        
    Raises:
        ValueError: 当缺少必需字段时
        
    Examples:
        >>> data = {'name': 'test', 'value': 42}
        >>> validate_required_fields(data, ['name', 'value'])  # 不会抛出异常
        >>> validate_required_fields(data, ['name', 'missing'])  # 抛出ValueError
        Traceback (most recent call last):
        ...
        ValueError: Missing required field: missing
    """
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Missing required field: {field}")


def merge_data_safely(base_data: Dict[str, Any], update_data: Dict[str, Any]) -> Dict[str, Any]:
    """安全地合并两个数据字典
    
    Args:
        base_data: 基础数据字典
        update_data: 更新数据字典
        
    Returns:
        合并后的数据字典
        
    Examples:
        >>> base = {'a': 1, 'b': 2}
        >>> update = {'b': 3, 'c': 4}
        >>> result = merge_data_safely(base, update)
        >>> result
        {'a': 1, 'b': 3, 'c': 4}
    """
    result = base_data.copy()
    result.update(update_data)
    return result


def extract_error_info(exception: Exception) -> Dict[str, Any]:
    """从异常中提取错误信息
    
    Args:
        exception: 异常对象
        
    Returns:
        包含错误信息的字典
        
    Examples:
        >>> try:
        ...     raise ValueError("Test error")
        ... except Exception as e:
        ...     error_info = extract_error_info(e)
        >>> error_info['message']
        'Test error'
        >>> error_info['type']
        'ValueError'
    """
    return {
        'message': str(exception),
        'type': type(exception).__name__,
        'args': list(exception.args) if exception.args else []
    }


if __name__ == "__main__":
    # 测试数据清理功能
    from pathlib import Path
    
    test_data = {
        'file_path': Path('/tmp/test.txt'),
        'screenshot_paths': [Path('/tmp/1.png'), Path('/tmp/2.png')],
        'config': {
            'log_file': Path('/tmp/app.log'),
            'name': 'test_config'
        },
        'normal_field': 'normal_value'
    }
    
    print("原始数据:")
    print(test_data)
    
    cleaned_data = sanitize_data_for_database(test_data)
    
    print("\n清理后的数据:")
    print(cleaned_data)
    
    print("\n数据类型检查:")
    print(f"file_path类型: {type(cleaned_data['file_path'])}")
    print(f"screenshot_paths[0]类型: {type(cleaned_data['screenshot_paths'][0])}")
    print(f"config.log_file类型: {type(cleaned_data['config']['log_file'])}")