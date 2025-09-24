"""
OpenMautoTest 文件操作工具模块

提供文件读写、目录操作、JSON处理等文件相关的通用函数
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


def get_project_root() -> Path:
    """获取项目根目录
    
    Returns:
        项目根目录路径
    """
    current_file = Path(__file__).resolve()
    # 从 common/utils/file_utils.py 向上找到项目根目录
    return current_file.parent.parent.parent


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在，不存在则创建
    
    Args:
        path: 目录路径
    
    Returns:
        目录路径对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_file_dir(file_path: Union[str, Path]) -> Path:
    """确保文件所在目录存在
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件路径对象
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    return file_path


def read_text_file(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    default: Optional[str] = None
) -> str:
    """读取文本文件
    
    Args:
        file_path: 文件路径
        encoding: 编码格式
        default: 文件不存在时的默认值
    
    Returns:
        文件内容
    
    Raises:
        FileNotFoundError: 文件不存在且未指定默认值
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()


def write_text_file(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True
) -> Path:
    """写入文本文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码格式
        create_dirs: 是否自动创建目录
    
    Returns:
        文件路径对象
    """
    file_path = Path(file_path)
    
    if create_dirs:
        ensure_file_dir(file_path)
    
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)
    
    return file_path


def read_json_file(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    default: Optional[Any] = None
) -> Any:
    """读取JSON文件
    
    Args:
        file_path: 文件路径
        encoding: 编码格式
        default: 文件不存在时的默认值
    
    Returns:
        JSON数据
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {file_path}: {e}")


def write_json_file(
    file_path: Union[str, Path],
    data: Any,
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False,
    create_dirs: bool = True
) -> Path:
    """写入JSON文件
    
    Args:
        file_path: 文件路径
        data: 要写入的数据
        encoding: 编码格式
        indent: 缩进空格数
        ensure_ascii: 是否确保ASCII编码
        create_dirs: 是否自动创建目录
    
    Returns:
        文件路径对象
    """
    file_path = Path(file_path)
    
    if create_dirs:
        ensure_file_dir(file_path)
    
    with open(file_path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    
    return file_path


def read_yaml_file(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    default: Optional[Any] = None
) -> Any:
    """读取YAML文件
    
    Args:
        file_path: 文件路径
        encoding: 编码格式
        default: 文件不存在时的默认值
    
    Returns:
        YAML数据
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in file {file_path}: {e}")


def write_yaml_file(
    file_path: Union[str, Path],
    data: Any,
    encoding: str = "utf-8",
    create_dirs: bool = True
) -> Path:
    """写入YAML文件
    
    Args:
        file_path: 文件路径
        data: 要写入的数据
        encoding: 编码格式
        create_dirs: 是否自动创建目录
    
    Returns:
        文件路径对象
    """
    file_path = Path(file_path)
    
    if create_dirs:
        ensure_file_dir(file_path)
    
    with open(file_path, 'w', encoding=encoding) as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
    
    return file_path


def copy_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    create_dirs: bool = True
) -> Path:
    """复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        create_dirs: 是否自动创建目录
    
    Returns:
        目标文件路径对象
    """
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    if create_dirs:
        ensure_file_dir(dst)
    
    shutil.copy2(src, dst)
    return dst


def copy_directory(
    src: Union[str, Path],
    dst: Union[str, Path],
    ignore_patterns: Optional[List[str]] = None
) -> Path:
    """复制目录
    
    Args:
        src: 源目录路径
        dst: 目标目录路径
        ignore_patterns: 忽略的文件模式列表
    
    Returns:
        目标目录路径对象
    """
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileNotFoundError(f"Source directory not found: {src}")
    
    # 设置忽略模式
    ignore = None
    if ignore_patterns:
        ignore = shutil.ignore_patterns(*ignore_patterns)
    
    shutil.copytree(src, dst, ignore=ignore, dirs_exist_ok=True)
    return dst


def move_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    create_dirs: bool = True
) -> Path:
    """移动文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        create_dirs: 是否自动创建目录
    
    Returns:
        目标文件路径对象
    """
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    if create_dirs:
        ensure_file_dir(dst)
    
    shutil.move(str(src), str(dst))
    return dst


def delete_file(file_path: Union[str, Path], ignore_missing: bool = True) -> bool:
    """删除文件
    
    Args:
        file_path: 文件路径
        ignore_missing: 是否忽略文件不存在的错误
    
    Returns:
        是否成功删除
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        if ignore_missing:
            return True
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        file_path.unlink()
        return True
    except Exception:
        return False


def delete_directory(
    dir_path: Union[str, Path],
    ignore_missing: bool = True
) -> bool:
    """删除目录
    
    Args:
        dir_path: 目录路径
        ignore_missing: 是否忽略目录不存在的错误
    
    Returns:
        是否成功删除
    """
    dir_path = Path(dir_path)
    
    if not dir_path.exists():
        if ignore_missing:
            return True
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    try:
        shutil.rmtree(dir_path)
        return True
    except Exception:
        return False


def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小（字节）
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件大小
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    return file_path.stat().st_size


def get_directory_size(dir_path: Union[str, Path]) -> int:
    """获取目录大小（字节）
    
    Args:
        dir_path: 目录路径
    
    Returns:
        目录大小
    """
    dir_path = Path(dir_path)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    total_size = 0
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    return total_size


def list_files(
    dir_path: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """列出目录中的文件
    
    Args:
        dir_path: 目录路径
        pattern: 文件模式
        recursive: 是否递归搜索
    
    Returns:
        文件路径列表
    """
    dir_path = Path(dir_path)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    if recursive:
        files = list(dir_path.rglob(pattern))
    else:
        files = list(dir_path.glob(pattern))
    
    return [f for f in files if f.is_file()]


def find_files_by_extension(
    dir_path: Union[str, Path],
    extension: str,
    recursive: bool = True
) -> List[Path]:
    """根据扩展名查找文件
    
    Args:
        dir_path: 目录路径
        extension: 文件扩展名（不带点）
        recursive: 是否递归搜索
    
    Returns:
        文件路径列表
    """
    pattern = f"*.{extension.lstrip('.')}"
    return list_files(dir_path, pattern, recursive)


def create_temp_file(
    suffix: str = "",
    prefix: str = "tmp",
    dir: Optional[Union[str, Path]] = None,
    text: bool = True
) -> Path:
    """创建临时文件
    
    Args:
        suffix: 文件后缀
        prefix: 文件前缀
        dir: 临时文件目录
        text: 是否为文本模式
    
    Returns:
        临时文件路径
    """
    fd, temp_path = tempfile.mkstemp(
        suffix=suffix,
        prefix=prefix,
        dir=str(dir) if dir else None,
        text=text
    )
    os.close(fd)  # 关闭文件描述符
    return Path(temp_path)


def create_temp_directory(
    suffix: str = "",
    prefix: str = "tmp",
    dir: Optional[Union[str, Path]] = None
) -> Path:
    """创建临时目录
    
    Args:
        suffix: 目录后缀
        prefix: 目录前缀
        dir: 父目录
    
    Returns:
        临时目录路径
    """
    temp_dir = tempfile.mkdtemp(
        suffix=suffix,
        prefix=prefix,
        dir=str(dir) if dir else None
    )
    return Path(temp_dir)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def clean_filename(filename: str, replacement: str = "_") -> str:
    """清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        replacement: 替换字符
    
    Returns:
        清理后的文件名
    """
    import re
    # 移除或替换不安全字符
    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    clean_name = re.sub(unsafe_chars, replacement, filename)
    
    # 移除开头和结尾的空格和点
    clean_name = clean_name.strip(' .')
    
    # 确保文件名不为空
    if not clean_name:
        clean_name = "unnamed"
    
    return clean_name


class FileWatcher:
    """文件监视器"""
    
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self._last_modified = None
        self._last_size = None
        self._update_stats()
    
    def _update_stats(self):
        """更新文件统计信息"""
        if self.file_path.exists():
            stat = self.file_path.stat()
            self._last_modified = stat.st_mtime
            self._last_size = stat.st_size
        else:
            self._last_modified = None
            self._last_size = None
    
    def has_changed(self) -> bool:
        """检查文件是否已更改"""
        if not self.file_path.exists():
            return self._last_modified is not None
        
        stat = self.file_path.stat()
        changed = (
            stat.st_mtime != self._last_modified or
            stat.st_size != self._last_size
        )
        
        if changed:
            self._update_stats()
        
        return changed


if __name__ == "__main__":
    # 测试文件工具函数
    print("Testing file utilities...")
    
    # 项目根目录
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    # 创建临时文件测试
    temp_file = create_temp_file(suffix=".txt", prefix="test_")
    print(f"Created temp file: {temp_file}")
    
    # 写入和读取文件
    test_data = {"name": "test", "value": 123}
    write_json_file(temp_file.with_suffix(".json"), test_data)
    read_data = read_json_file(temp_file.with_suffix(".json"))
    print(f"JSON data: {read_data}")
    
    # 文件大小
    file_size = get_file_size(temp_file.with_suffix(".json"))
    print(f"File size: {format_file_size(file_size)}")
    
    # 清理临时文件
    delete_file(temp_file)
    delete_file(temp_file.with_suffix(".json"))
    
    print("File utilities tests completed.")
