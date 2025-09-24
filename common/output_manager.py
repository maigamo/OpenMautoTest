"""
OpenMautoTest 输出目录管理器

管理测试输出文件的组织、清理和归档
"""

import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from common.logger import get_logger
from common.utils.file_utils import ensure_dir
from configs.settings import get_settings


class OutputManager:
    """输出目录管理器"""
    
    def __init__(self, base_output_dir: Union[str, Path] = "output"):
        """初始化输出管理器
        
        Args:
            base_output_dir: 基础输出目录
        """
        self.base_dir = Path(base_output_dir)
        self.logger = get_logger("output_manager")
        self.settings = get_settings()
        
        # 子目录定义
        self.subdirs = {
            "reports": self.base_dir / "reports",
            "screenshots": self.base_dir / "screenshots",
            "logs": self.base_dir / "logs",
            "videos": self.base_dir / "videos",
            "allure-results": self.base_dir / "allure-results",
            "allure-report": self.base_dir / "allure-report",
            "records": self.base_dir / "records",
            "temp": self.base_dir / "temp",
            "archive": self.base_dir / "archive"
        }
        
        # 初始化目录结构
        self._initialize_directories()
    
    def _initialize_directories(self) -> None:
        """初始化目录结构"""
        try:
            # 确保基础目录存在
            ensure_dir(self.base_dir)
            
            # 创建所有子目录
            for name, path in self.subdirs.items():
                ensure_dir(path)
                self.logger.debug(f"Ensured directory exists: {path}")
            
            # 创建.gitkeep文件以保持目录结构
            for path in self.subdirs.values():
                gitkeep_file = path / ".gitkeep"
                if not gitkeep_file.exists():
                    gitkeep_file.write_text("")
            
            self.logger.info(f"Output directory structure initialized: {self.base_dir}")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize output directories: {e}")
            raise
    
    def get_dir(self, dir_name: str) -> Path:
        """获取子目录路径
        
        Args:
            dir_name: 目录名称
        
        Returns:
            目录路径
        """
        if dir_name not in self.subdirs:
            raise ValueError(f"Unknown directory: {dir_name}")
        
        return self.subdirs[dir_name]
    
    def create_run_directory(self, run_id: str, timestamp: Optional[datetime] = None) -> Path:
        """创建运行专用目录
        
        Args:
            run_id: 运行ID
            timestamp: 时间戳
        
        Returns:
            运行目录路径
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        run_dir_name = f"{timestamp_str}_{run_id}"
        run_dir = self.base_dir / "runs" / run_dir_name
        
        ensure_dir(run_dir)
        
        # 创建运行目录的子目录
        for subdir_name in ["screenshots", "logs", "reports", "videos"]:
            ensure_dir(run_dir / subdir_name)
        
        self.logger.info(f"Created run directory: {run_dir}")
        return run_dir
    
    def cleanup_old_files(
        self,
        max_age_days: int = 7,
        directories: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """清理旧文件
        
        Args:
            max_age_days: 最大保留天数
            directories: 要清理的目录列表，None表示清理所有
        
        Returns:
            清理统计信息
        """
        if directories is None:
            directories = ["screenshots", "logs", "reports", "videos", "temp"]
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        cleanup_stats = {}
        
        for dir_name in directories:
            if dir_name not in self.subdirs:
                self.logger.warning(f"Unknown directory for cleanup: {dir_name}")
                continue
            
            dir_path = self.subdirs[dir_name]
            cleaned_count = 0
            
            try:
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file() and file_path.name != ".gitkeep":
                        if file_path.stat().st_mtime < cutoff_timestamp:
                            file_path.unlink()
                            cleaned_count += 1
                
                # 清理空目录
                for dir_path_item in dir_path.rglob("*"):
                    if dir_path_item.is_dir() and not any(dir_path_item.iterdir()):
                        try:
                            dir_path_item.rmdir()
                        except OSError:
                            pass  # 目录可能不为空或有权限问题
                
                cleanup_stats[dir_name] = cleaned_count
                
                if cleaned_count > 0:
                    self.logger.info(f"Cleaned {cleaned_count} old files from {dir_name}")
            
            except Exception as e:
                self.logger.error(f"Failed to cleanup directory {dir_name}: {e}")
                cleanup_stats[dir_name] = 0
        
        total_cleaned = sum(cleanup_stats.values())
        self.logger.info(f"Total cleanup completed: {total_cleaned} files removed")
        
        return cleanup_stats
    
    def archive_old_results(
        self,
        max_age_days: int = 30,
        compress: bool = True
    ) -> List[Path]:
        """归档旧的测试结果
        
        Args:
            max_age_days: 归档阈值天数
            compress: 是否压缩归档
        
        Returns:
            归档文件路径列表
        """
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        archive_files = []
        
        try:
            # 查找需要归档的运行目录
            runs_dir = self.base_dir / "runs"
            if not runs_dir.exists():
                return archive_files
            
            for run_dir in runs_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                
                # 检查目录的修改时间
                dir_mtime = datetime.fromtimestamp(run_dir.stat().st_mtime)
                if dir_mtime < cutoff_time:
                    # 创建归档
                    archive_name = f"{run_dir.name}.zip" if compress else run_dir.name
                    archive_path = self.subdirs["archive"] / archive_name
                    
                    if compress:
                        # 创建ZIP归档
                        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for file_path in run_dir.rglob("*"):
                                if file_path.is_file():
                                    arcname = file_path.relative_to(run_dir)
                                    zipf.write(file_path, arcname)
                    else:
                        # 移动到归档目录
                        shutil.move(str(run_dir), str(archive_path))
                    
                    # 删除原目录（如果是压缩归档）
                    if compress:
                        shutil.rmtree(run_dir)
                    
                    archive_files.append(archive_path)
                    self.logger.info(f"Archived old results: {archive_path}")
            
            if archive_files:
                self.logger.info(f"Archived {len(archive_files)} old result directories")
        
        except Exception as e:
            self.logger.error(f"Failed to archive old results: {e}")
        
        return archive_files
    
    def get_disk_usage(self) -> Dict[str, Dict[str, Union[int, str]]]:
        """获取磁盘使用情况
        
        Returns:
            磁盘使用统计
        """
        usage_stats = {}
        
        for dir_name, dir_path in self.subdirs.items():
            if not dir_path.exists():
                continue
            
            total_size = 0
            file_count = 0
            
            try:
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
                
                # 格式化大小
                size_mb = total_size / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb < 1024 else f"{size_mb/1024:.2f} GB"
                
                usage_stats[dir_name] = {
                    "size_bytes": total_size,
                    "size_formatted": size_str,
                    "file_count": file_count
                }
            
            except Exception as e:
                self.logger.error(f"Failed to calculate disk usage for {dir_name}: {e}")
                usage_stats[dir_name] = {
                    "size_bytes": 0,
                    "size_formatted": "0 MB",
                    "file_count": 0
                }
        
        return usage_stats
    
    def generate_index_html(self) -> Path:
        """生成输出目录索引HTML文件
        
        Returns:
            索引文件路径
        """
        try:
            # 获取磁盘使用情况
            usage_stats = self.get_disk_usage()
            
            # 生成HTML内容
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenMautoTest 输出目录</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .stat-card h3 {{ margin: 0 0 10px 0; color: #495057; }}
        .stat-card p {{ margin: 5px 0; color: #6c757d; }}
        .directories {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .dir-card {{ background: #fff; border: 1px solid #dee2e6; padding: 20px; border-radius: 6px; }}
        .dir-card h3 {{ margin: 0 0 15px 0; color: #495057; }}
        .dir-card a {{ color: #007bff; text-decoration: none; }}
        .dir-card a:hover {{ text-decoration: underline; }}
        .timestamp {{ text-align: center; color: #6c757d; margin-top: 30px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OpenMautoTest 输出目录</h1>
        
        <div class="stats">
            <div class="stat-card">
                <h3>总文件数</h3>
                <p>{sum(stats['file_count'] for stats in usage_stats.values())}</p>
            </div>
            <div class="stat-card">
                <h3>总大小</h3>
                <p>{sum(stats['size_bytes'] for stats in usage_stats.values()) / (1024*1024):.2f} MB</p>
            </div>
            <div class="stat-card">
                <h3>最后更新</h3>
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
        
        <div class="directories">
"""
            
            # 添加每个目录的信息
            for dir_name, dir_path in self.subdirs.items():
                stats = usage_stats.get(dir_name, {"size_formatted": "0 MB", "file_count": 0})
                
                html_content += f"""
            <div class="dir-card">
                <h3>{dir_name}</h3>
                <p><strong>路径:</strong> <a href="{dir_name}/">{dir_path.relative_to(self.base_dir)}/</a></p>
                <p><strong>文件数:</strong> {stats['file_count']}</p>
                <p><strong>大小:</strong> {stats['size_formatted']}</p>
            </div>
"""
            
            html_content += f"""
        </div>
        
        <div class="timestamp">
            生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
            
            # 保存HTML文件
            index_path = self.base_dir / "index.html"
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            self.logger.info(f"Generated output directory index: {index_path}")
            return index_path
        
        except Exception as e:
            self.logger.error(f"Failed to generate index HTML: {e}")
            raise
    
    def get_latest_files(
        self,
        directory: str,
        count: int = 10,
        pattern: str = "*"
    ) -> List[Tuple[Path, datetime]]:
        """获取最新文件列表
        
        Args:
            directory: 目录名称
            count: 返回文件数量
            pattern: 文件模式
        
        Returns:
            文件路径和修改时间的元组列表
        """
        if directory not in self.subdirs:
            raise ValueError(f"Unknown directory: {directory}")
        
        dir_path = self.subdirs[directory]
        files_with_time = []
        
        try:
            for file_path in dir_path.glob(pattern):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    files_with_time.append((file_path, mtime))
            
            # 按修改时间排序，最新的在前
            files_with_time.sort(key=lambda x: x[1], reverse=True)
            
            return files_with_time[:count]
        
        except Exception as e:
            self.logger.error(f"Failed to get latest files from {directory}: {e}")
            return []
    
    def create_symlink(self, target: Path, link_name: str, directory: str = "temp") -> Path:
        """创建符号链接
        
        Args:
            target: 目标文件路径
            link_name: 链接名称
            directory: 链接所在目录
        
        Returns:
            链接路径
        """
        if directory not in self.subdirs:
            raise ValueError(f"Unknown directory: {directory}")
        
        link_path = self.subdirs[directory] / link_name
        
        try:
            if link_path.exists():
                link_path.unlink()
            
            link_path.symlink_to(target)
            self.logger.debug(f"Created symlink: {link_path} -> {target}")
            return link_path
        
        except Exception as e:
            self.logger.error(f"Failed to create symlink: {e}")
            raise


# 全局实例
_global_output_manager: Optional[OutputManager] = None


def get_output_manager() -> OutputManager:
    """获取全局输出管理器实例
    
    Returns:
        输出管理器实例
    """
    global _global_output_manager
    if _global_output_manager is None:
        _global_output_manager = OutputManager()
    return _global_output_manager


if __name__ == "__main__":
    # 测试输出管理器
    print("Testing Output Manager...")
    
    manager = OutputManager("test_output")
    
    # 测试目录创建
    screenshots_dir = manager.get_dir("screenshots")
    print(f"Screenshots directory: {screenshots_dir}")
    
    # 测试运行目录创建
    run_dir = manager.create_run_directory("test_run_123")
    print(f"Run directory created: {run_dir}")
    
    # 测试磁盘使用统计
    usage = manager.get_disk_usage()
    print(f"Disk usage: {usage}")
    
    # 生成索引文件
    index_file = manager.generate_index_html()
    print(f"Index file generated: {index_file}")
    
    print("Output manager test completed successfully!")
