"""
OpenMautoTest 数据处理工具模块

提供数据合并、扁平化、验证等数据处理相关的通用函数
"""

import copy
from typing import Any, Dict, List, Optional, Union

import jsonschema


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """深度合并字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
    
    Returns:
        合并后的字典
    """
    result = copy.deepcopy(dict1)
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    
    return result


def flatten_dict(
    data: Dict,
    separator: str = ".",
    parent_key: str = ""
) -> Dict:
    """扁平化字典
    
    Args:
        data: 要扁平化的字典
        separator: 键分隔符
        parent_key: 父键名
    
    Returns:
        扁平化后的字典
    """
    items = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, separator, new_key).items())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                list_key = f"{new_key}{separator}{i}"
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, separator, list_key).items())
                else:
                    items.append((list_key, item))
        else:
            items.append((new_key, value))
    
    return dict(items)


def unflatten_dict(
    data: Dict,
    separator: str = "."
) -> Dict:
    """反扁平化字典
    
    Args:
        data: 扁平化的字典
        separator: 键分隔符
    
    Returns:
        反扁平化后的字典
    """
    result = {}
    
    for key, value in data.items():
        keys = key.split(separator)
        current = result
        
        for i, k in enumerate(keys[:-1]):
            if k.isdigit():
                k = int(k)
                if not isinstance(current, list):
                    current = []
                while len(current) <= k:
                    current.append({})
                current = current[k]
            else:
                if k not in current:
                    # 检查下一个键是否为数字
                    next_key = keys[i + 1]
                    if next_key.isdigit():
                        current[k] = []
                    else:
                        current[k] = {}
                current = current[k]
        
        # 设置最终值
        final_key = keys[-1]
        if final_key.isdigit():
            final_key = int(final_key)
            if not isinstance(current, list):
                current = []
            while len(current) <= final_key:
                current.append(None)
            current[final_key] = value
        else:
            current[final_key] = value
    
    return result


def safe_get(
    data: Union[Dict, List],
    path: Union[str, List[Union[str, int]]],
    default: Any = None,
    separator: str = "."
) -> Any:
    """安全获取嵌套数据
    
    Args:
        data: 数据对象
        path: 路径，可以是字符串或键列表
        default: 默认值
        separator: 路径分隔符
    
    Returns:
        获取到的值或默认值
    """
    if isinstance(path, str):
        keys = path.split(separator)
    else:
        keys = path
    
    current = data
    
    try:
        for key in keys:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list):
                current = current[int(key)]
            else:
                return default
        
        return current
    
    except (KeyError, IndexError, TypeError, ValueError):
        return default


def safe_set(
    data: Dict,
    path: Union[str, List[str]],
    value: Any,
    separator: str = ".",
    create_missing: bool = True
) -> Dict:
    """安全设置嵌套数据
    
    Args:
        data: 数据字典
        path: 路径
        value: 要设置的值
        separator: 路径分隔符
        create_missing: 是否创建缺失的中间路径
    
    Returns:
        修改后的数据字典
    """
    if isinstance(path, str):
        keys = path.split(separator)
    else:
        keys = path
    
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            if create_missing:
                current[key] = {}
            else:
                raise KeyError(f"Key not found: {key}")
        current = current[key]
    
    current[keys[-1]] = value
    return data


def remove_empty_values(
    data: Union[Dict, List],
    empty_values: tuple = (None, "", [], {})
) -> Union[Dict, List]:
    """移除空值
    
    Args:
        data: 数据对象
        empty_values: 被认为是空值的值元组
    
    Returns:
        移除空值后的数据
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                cleaned_value = remove_empty_values(value, empty_values)
                if cleaned_value not in empty_values:
                    result[key] = cleaned_value
            elif value not in empty_values:
                result[key] = value
        return result
    
    elif isinstance(data, list):
        result = []
        for item in data:
            if isinstance(item, (dict, list)):
                cleaned_item = remove_empty_values(item, empty_values)
                if cleaned_item not in empty_values:
                    result.append(cleaned_item)
            elif item not in empty_values:
                result.append(item)
        return result
    
    else:
        return data


def validate_schema(data: Any, schema: Dict) -> tuple:
    """验证数据模式
    
    Args:
        data: 要验证的数据
        schema: JSON Schema
    
    Returns:
        (是否有效, 错误信息列表)
    """
    try:
        jsonschema.validate(data, schema)
        return True, []
    except jsonschema.ValidationError as e:
        return False, [str(e)]
    except jsonschema.SchemaError as e:
        return False, [f"Schema error: {str(e)}"]


def normalize_data(
    data: Union[Dict, List],
    string_fields: Optional[List[str]] = None,
    number_fields: Optional[List[str]] = None,
    boolean_fields: Optional[List[str]] = None
) -> Union[Dict, List]:
    """标准化数据类型
    
    Args:
        data: 要标准化的数据
        string_fields: 字符串字段列表
        number_fields: 数字字段列表
        boolean_fields: 布尔字段列表
    
    Returns:
        标准化后的数据
    """
    if string_fields is None:
        string_fields = []
    if number_fields is None:
        number_fields = []
    if boolean_fields is None:
        boolean_fields = []
    
    def normalize_value(key: str, value: Any) -> Any:
        if key in string_fields:
            return str(value) if value is not None else ""
        elif key in number_fields:
            try:
                return float(value) if value is not None else 0
            except (ValueError, TypeError):
                return 0
        elif key in boolean_fields:
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value) if value is not None else False
        else:
            return value
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                result[key] = normalize_data(value, string_fields, number_fields, boolean_fields)
            else:
                result[key] = normalize_value(key, value)
        return result
    
    elif isinstance(data, list):
        return [
            normalize_data(item, string_fields, number_fields, boolean_fields)
            if isinstance(item, (dict, list))
            else item
            for item in data
        ]
    
    else:
        return data


def group_by(data: List[Dict], key: str) -> Dict[Any, List[Dict]]:
    """按键分组数据
    
    Args:
        data: 数据列表
        key: 分组键
    
    Returns:
        分组后的数据字典
    """
    groups = {}
    
    for item in data:
        group_key = safe_get(item, key)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)
    
    return groups


def sort_by(
    data: List[Dict],
    key: str,
    reverse: bool = False,
    default_value: Any = 0
) -> List[Dict]:
    """按键排序数据
    
    Args:
        data: 数据列表
        key: 排序键
        reverse: 是否倒序
        default_value: 默认值
    
    Returns:
        排序后的数据列表
    """
    return sorted(
        data,
        key=lambda x: safe_get(x, key, default_value),
        reverse=reverse
    )


def filter_data(
    data: List[Dict],
    filters: Dict[str, Any]
) -> List[Dict]:
    """过滤数据
    
    Args:
        data: 数据列表
        filters: 过滤条件字典
    
    Returns:
        过滤后的数据列表
    """
    result = []
    
    for item in data:
        match = True
        for filter_key, filter_value in filters.items():
            item_value = safe_get(item, filter_key)
            
            if isinstance(filter_value, dict):
                # 支持操作符过滤
                for op, op_value in filter_value.items():
                    if op == "$eq" and item_value != op_value:
                        match = False
                        break
                    elif op == "$ne" and item_value == op_value:
                        match = False
                        break
                    elif op == "$gt" and not (item_value > op_value):
                        match = False
                        break
                    elif op == "$gte" and not (item_value >= op_value):
                        match = False
                        break
                    elif op == "$lt" and not (item_value < op_value):
                        match = False
                        break
                    elif op == "$lte" and not (item_value <= op_value):
                        match = False
                        break
                    elif op == "$in" and item_value not in op_value:
                        match = False
                        break
                    elif op == "$nin" and item_value in op_value:
                        match = False
                        break
                if not match:
                    break
            else:
                # 简单相等过滤
                if item_value != filter_value:
                    match = False
                    break
        
        if match:
            result.append(item)
    
    return result


def aggregate_data(
    data: List[Dict],
    group_key: str,
    aggregations: Dict[str, str]
) -> List[Dict]:
    """聚合数据
    
    Args:
        data: 数据列表
        group_key: 分组键
        aggregations: 聚合配置 {字段名: 聚合类型}
    
    Returns:
        聚合后的数据列表
    """
    groups = group_by(data, group_key)
    result = []
    
    for group_value, group_data in groups.items():
        aggregated = {group_key: group_value}
        
        for field, agg_type in aggregations.items():
            values = [safe_get(item, field, 0) for item in group_data]
            values = [v for v in values if isinstance(v, (int, float))]
            
            if not values:
                aggregated[f"{field}_{agg_type}"] = 0
                continue
            
            if agg_type == "sum":
                aggregated[f"{field}_sum"] = sum(values)
            elif agg_type == "avg":
                aggregated[f"{field}_avg"] = sum(values) / len(values)
            elif agg_type == "min":
                aggregated[f"{field}_min"] = min(values)
            elif agg_type == "max":
                aggregated[f"{field}_max"] = max(values)
            elif agg_type == "count":
                aggregated[f"{field}_count"] = len(group_data)
        
        result.append(aggregated)
    
    return result


def paginate_data(
    data: List,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """分页数据
    
    Args:
        data: 数据列表
        page: 页码（从1开始）
        page_size: 每页大小
    
    Returns:
        分页结果字典
    """
    total = len(data)
    total_pages = (total + page_size - 1) // page_size
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    return {
        "data": data[start_index:end_index],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
    }


if __name__ == "__main__":
    # 测试数据处理工具函数
    print("Testing data utilities...")
    
    # 深度合并测试
    dict1 = {"a": {"b": 1, "c": 2}, "d": 3}
    dict2 = {"a": {"b": 4, "e": 5}, "f": 6}
    merged = deep_merge(dict1, dict2)
    print(f"Deep merge: {merged}")
    
    # 扁平化测试
    nested_data = {"a": {"b": {"c": 1}}, "d": [{"e": 2}, {"f": 3}]}
    flattened = flatten_dict(nested_data)
    print(f"Flattened: {flattened}")
    
    # 安全获取测试
    value = safe_get(nested_data, "a.b.c")
    print(f"Safe get: {value}")
    
    # 数据过滤测试
    test_data = [
        {"name": "Alice", "age": 25, "score": 85},
        {"name": "Bob", "age": 30, "score": 90},
        {"name": "Charlie", "age": 35, "score": 78}
    ]
    
    filtered = filter_data(test_data, {"age": {"$gte": 30}})
    print(f"Filtered data: {filtered}")
    
    # 分组测试
    grouped = group_by(test_data, "age")
    print(f"Grouped keys: {list(grouped.keys())}")
    
    print("Data utilities tests completed.")
