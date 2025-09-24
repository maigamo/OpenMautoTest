"""
OpenMautoTest 字符串处理工具模块

提供字符串生成、清理、验证等字符串处理相关的通用函数
"""

import hashlib
import random
import re
import string
import unicodedata
from typing import List, Optional, Union


def generate_random_string(
    length: int = 8,
    chars: str = string.ascii_letters + string.digits
) -> str:
    """生成随机字符串
    
    Args:
        length: 字符串长度
        chars: 可用字符集
    
    Returns:
        随机字符串
    """
    return ''.join(random.choice(chars) for _ in range(length))


def generate_uuid_string() -> str:
    """生成UUID字符串
    
    Returns:
        UUID字符串
    """
    import uuid
    return str(uuid.uuid4())


def generate_timestamp_string() -> str:
    """生成时间戳字符串
    
    Returns:
        时间戳字符串
    """
    import time
    return str(int(time.time() * 1000))


def sanitize_filename(
    filename: str,
    replacement: str = "_",
    max_length: int = 255
) -> str:
    """清理文件名
    
    Args:
        filename: 原始文件名
        replacement: 替换字符
        max_length: 最大长度
    
    Returns:
        清理后的文件名
    """
    # 移除不安全字符
    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    clean_name = re.sub(unsafe_chars, replacement, filename)
    
    # 移除开头和结尾的空格和点
    clean_name = clean_name.strip(' .')
    
    # 限制长度
    if len(clean_name) > max_length:
        name_part, ext_part = clean_name.rsplit('.', 1) if '.' in clean_name else (clean_name, '')
        max_name_length = max_length - len(ext_part) - (1 if ext_part else 0)
        clean_name = name_part[:max_name_length] + ('.' + ext_part if ext_part else '')
    
    # 确保文件名不为空
    if not clean_name:
        clean_name = "unnamed"
    
    return clean_name


def truncate_string(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
    
    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def mask_sensitive_data(
    text: str,
    patterns: Optional[List[str]] = None,
    mask_char: str = "*"
) -> str:
    """掩码敏感数据
    
    Args:
        text: 原始文本
        patterns: 敏感数据正则模式列表
        mask_char: 掩码字符
    
    Returns:
        掩码后的文本
    """
    if patterns is None:
        # 默认敏感数据模式
        patterns = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 信用卡号
            r'\b\d{3}-\d{2}-\d{4}\b',  # 社会安全号
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 邮箱
            r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',  # 电话号码
            r'password["\s]*[:=]["\s]*[^\s"]+',  # 密码
            r'token["\s]*[:=]["\s]*[^\s"]+',  # 令牌
            r'key["\s]*[:=]["\s]*[^\s"]+',  # 密钥
        ]
    
    masked_text = text
    
    for pattern in patterns:
        def mask_match(match):
            matched_text = match.group(0)
            if len(matched_text) <= 4:
                return mask_char * len(matched_text)
            else:
                # 保留前2个和后2个字符
                return matched_text[:2] + mask_char * (len(matched_text) - 4) + matched_text[-2:]
        
        masked_text = re.sub(pattern, mask_match, masked_text, flags=re.IGNORECASE)
    
    return masked_text


def normalize_whitespace(text: str) -> str:
    """标准化空白字符
    
    Args:
        text: 原始文本
    
    Returns:
        标准化后的文本
    """
    # 替换所有空白字符为单个空格
    normalized = re.sub(r'\s+', ' ', text)
    # 移除开头和结尾的空格
    return normalized.strip()


def remove_accents(text: str) -> str:
    """移除重音符号
    
    Args:
        text: 原始文本
    
    Returns:
        移除重音符号后的文本
    """
    # 使用Unicode标准化
    normalized = unicodedata.normalize('NFD', text)
    # 过滤掉重音符号
    without_accents = ''.join(
        char for char in normalized
        if unicodedata.category(char) != 'Mn'
    )
    return without_accents


def to_snake_case(text: str) -> str:
    """转换为蛇形命名
    
    Args:
        text: 原始文本
    
    Returns:
        蛇形命名字符串
    """
    # 在大写字母前插入下划线
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    # 在小写字母和大写字母之间插入下划线
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    # 替换空格和连字符为下划线
    s3 = re.sub(r'[-\s]+', '_', s2)
    # 转换为小写
    return s3.lower()


def to_camel_case(text: str, capitalize_first: bool = False) -> str:
    """转换为驼峰命名
    
    Args:
        text: 原始文本
        capitalize_first: 是否首字母大写
    
    Returns:
        驼峰命名字符串
    """
    # 分割单词
    words = re.split(r'[-_\s]+', text.lower())
    
    if not words:
        return text
    
    # 第一个单词
    if capitalize_first:
        result = words[0].capitalize()
    else:
        result = words[0]
    
    # 其余单词首字母大写
    for word in words[1:]:
        result += word.capitalize()
    
    return result


def to_kebab_case(text: str) -> str:
    """转换为短横线命名
    
    Args:
        text: 原始文本
    
    Returns:
        短横线命名字符串
    """
    # 转换为蛇形命名然后替换下划线为短横线
    snake_case = to_snake_case(text)
    return snake_case.replace('_', '-')


def extract_numbers(text: str) -> List[Union[int, float]]:
    """提取文本中的数字
    
    Args:
        text: 原始文本
    
    Returns:
        数字列表
    """
    # 匹配整数和浮点数
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            if '.' in match:
                numbers.append(float(match))
            else:
                numbers.append(int(match))
        except ValueError:
            continue
    
    return numbers


def extract_urls(text: str) -> List[str]:
    """提取文本中的URL
    
    Args:
        text: 原始文本
    
    Returns:
        URL列表
    """
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(pattern, text)


def extract_emails(text: str) -> List[str]:
    """提取文本中的邮箱地址
    
    Args:
        text: 原始文本
    
    Returns:
        邮箱地址列表
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)


def is_valid_email(email: str) -> bool:
    """验证邮箱地址是否有效
    
    Args:
        email: 邮箱地址
    
    Returns:
        是否有效
    """
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """验证URL是否有效
    
    Args:
        url: URL地址
    
    Returns:
        是否有效
    """
    pattern = r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))


def calculate_hash(text: str, algorithm: str = "md5") -> str:
    """计算字符串哈希值
    
    Args:
        text: 原始字符串
        algorithm: 哈希算法 (md5, sha1, sha256, sha512)
    
    Returns:
        哈希值
    """
    text_bytes = text.encode('utf-8')
    
    if algorithm == "md5":
        return hashlib.md5(text_bytes).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text_bytes).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(text_bytes).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(text_bytes).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def similarity_ratio(str1: str, str2: str) -> float:
    """计算字符串相似度
    
    Args:
        str1: 第一个字符串
        str2: 第二个字符串
    
    Returns:
        相似度比率 (0-1)
    """
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str1, str2).ratio()


def levenshtein_distance(str1: str, str2: str) -> int:
    """计算编辑距离
    
    Args:
        str1: 第一个字符串
        str2: 第二个字符串
    
    Returns:
        编辑距离
    """
    if len(str1) < len(str2):
        return levenshtein_distance(str2, str1)
    
    if len(str2) == 0:
        return len(str1)
    
    previous_row = list(range(len(str2) + 1))
    for i, c1 in enumerate(str1):
        current_row = [i + 1]
        for j, c2 in enumerate(str2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def highlight_text(
    text: str,
    keywords: List[str],
    start_tag: str = "<mark>",
    end_tag: str = "</mark>",
    case_sensitive: bool = False
) -> str:
    """高亮文本中的关键词
    
    Args:
        text: 原始文本
        keywords: 关键词列表
        start_tag: 开始标签
        end_tag: 结束标签
        case_sensitive: 是否区分大小写
    
    Returns:
        高亮后的文本
    """
    highlighted_text = text
    
    for keyword in keywords:
        if not keyword:
            continue
        
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.escape(keyword)
        replacement = f"{start_tag}{keyword}{end_tag}"
        highlighted_text = re.sub(pattern, replacement, highlighted_text, flags=flags)
    
    return highlighted_text


if __name__ == "__main__":
    # 测试字符串工具函数
    print("Testing string utilities...")
    
    # 随机字符串生成
    random_str = generate_random_string(10)
    print(f"Random string: {random_str}")
    
    # UUID生成
    uuid_str = generate_uuid_string()
    print(f"UUID: {uuid_str}")
    
    # 文件名清理
    unsafe_filename = 'test<>file:name|?.txt'
    safe_filename = sanitize_filename(unsafe_filename)
    print(f"Safe filename: {safe_filename}")
    
    # 命名转换
    text = "HelloWorldTest"
    snake_case = to_snake_case(text)
    camel_case = to_camel_case(snake_case, True)
    kebab_case = to_kebab_case(text)
    print(f"Snake case: {snake_case}")
    print(f"Camel case: {camel_case}")
    print(f"Kebab case: {kebab_case}")
    
    # 敏感数据掩码
    sensitive_text = "My email is john@example.com and password is secret123"
    masked_text = mask_sensitive_data(sensitive_text)
    print(f"Masked text: {masked_text}")
    
    # 字符串相似度
    similarity = similarity_ratio("hello world", "hello word")
    print(f"Similarity: {similarity:.2f}")
    
    print("String utilities tests completed.")


def format_duration(seconds: float) -> str:
    """格式化时间长度
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.2f}s"


def format_bytes(size: int) -> str:
    """格式化字节大小
    
    Args:
        size: 字节大小
    
    Returns:
        格式化的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"