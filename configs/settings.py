"""
OpenMautoTest 全局配置管理模块

提供统一的配置管理，支持环境变量读取和配置验证
配置优先级：环境变量 > 配置文件 > 默认值
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class OpenMautoTestSettings(BaseSettings):
    """OpenMautoTest 全局配置类"""
    
    # ===================
    # 基础项目配置
    # ===================
    PROJECT_NAME: str = Field(default="OpenMautoTest", description="项目名称")
    PROJECT_VERSION: str = Field(default="1.0.0", description="项目版本")
    PROJECT_ROOT: Path = Field(default_factory=lambda: Path(__file__).parent.parent, description="项目根目录")
    
    # ===================
    # 环境配置
    # ===================
    ENVIRONMENT: str = Field(default="development", description="运行环境")
    DEBUG: bool = Field(default=False, description="调试模式")
    TESTING: bool = Field(default=False, description="测试模式")
    
    # ===================
    # 数据库配置
    # ===================
    DATABASE_URL: Optional[str] = Field(default=None, description="数据库连接URL")
    DATABASE_HOST: str = Field(default="localhost", description="数据库主机")
    DATABASE_PORT: int = Field(default=5432, description="数据库端口")
    DATABASE_NAME: str = Field(default="openmautotest", description="数据库名称")
    DATABASE_USER: str = Field(default="postgres", description="数据库用户")
    DATABASE_PASSWORD: str = Field(default="", description="数据库密码")
    
    # MongoDB 配置
    MONGODB_URL: Optional[str] = Field(default=None, description="MongoDB连接URL")
    MONGODB_HOST: str = Field(default="localhost", description="MongoDB主机")
    MONGODB_PORT: int = Field(default=27017, description="MongoDB端口")
    MONGODB_DATABASE: str = Field(default="openmautotest", description="MongoDB数据库名")
    
    # Redis 配置
    REDIS_URL: Optional[str] = Field(default=None, description="Redis连接URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_DB: int = Field(default=0, description="Redis数据库编号")
    
    # ===================
    # 环境变量别名（兼容性）
    # ===================
    # 数据库别名
    DB_HOST: Optional[str] = Field(default=None, description="数据库主机（别名）")
    DB_PORT: Optional[int] = Field(default=None, description="数据库端口（别名）")
    DB_NAME: Optional[str] = Field(default=None, description="数据库名称（别名）")
    DB_USER: Optional[str] = Field(default=None, description="数据库用户（别名）")
    DB_PASSWORD: Optional[str] = Field(default=None, description="数据库密码（别名）")
    
    # MongoDB 别名
    MONGO_HOST: Optional[str] = Field(default=None, description="MongoDB主机（别名）")
    MONGO_PORT: Optional[int] = Field(default=None, description="MongoDB端口（别名）")
    MONGO_DB: Optional[str] = Field(default=None, description="MongoDB数据库（别名）")
    MONGO_USER: Optional[str] = Field(default=None, description="MongoDB用户（别名）")
    MONGO_PASSWORD: Optional[str] = Field(default=None, description="MongoDB密码（别名）")
    
    # ===================
    # Jenkins 配置
    # ===================
    JENKINS_URL: Optional[str] = Field(default=None, description="Jenkins服务器URL")
    JENKINS_USER: Optional[str] = Field(default=None, description="Jenkins用户名")
    JENKINS_TOKEN: Optional[str] = Field(default=None, description="Jenkins访问令牌")
    JENKINS_JOB_NAME: Optional[str] = Field(default=None, description="Jenkins作业名称")
    
    # ===================
    # 浏览器配置
    # ===================
    BROWSER_TYPE: str = Field(default="chromium", description="浏览器类型")
    BROWSER_HEADLESS: bool = Field(default=True, description="无头模式")
    BROWSER_TIMEOUT: int = Field(default=30000, description="浏览器超时时间(毫秒)")
    BROWSER_SLOW_MO: int = Field(default=0, description="浏览器慢速模式延迟(毫秒)")
    
    # ===================
    # 微信小程序配置
    # ===================
    WECHAT_MINI_APP_ID: Optional[str] = Field(default=None, description="小程序AppID")
    WECHAT_MINI_IDE_PORT: int = Field(default=9420, description="小程序开发工具端口")
    WECHAT_MINI_PROJECT_PATH: Optional[str] = Field(default=None, description="小程序项目路径")
    
    # ===================
    # 测试环境配置
    # ===================
    TEST_ENV: str = Field(default="dev", description="测试环境标识")
    BASE_URL: str = Field(default="http://localhost:3000", description="测试基础URL")
    API_BASE_URL: str = Field(default="http://localhost:8000/api", description="API基础URL")
    
    # ===================
    # 日志配置
    # ===================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE_PATH: str = Field(default="output/logs/openmautotest.log", description="日志文件路径")
    LOG_MAX_SIZE: str = Field(default="100MB", description="日志文件最大大小")
    LOG_BACKUP_COUNT: int = Field(default=10, description="日志文件备份数量")
    
    # ===================
    # Allure 报告配置
    # ===================
    ALLURE_RESULTS_DIR: str = Field(default="output/allure-results", description="Allure结果目录")
    ALLURE_REPORT_DIR: str = Field(default="output/allure-report", description="Allure报告目录")
    
    # ===================
    # Metabase 配置
    # ===================
    METABASE_URL: str = Field(default="http://localhost:3000", description="Metabase URL")
    METABASE_USER: Optional[str] = Field(default=None, description="Metabase用户")
    METABASE_PASSWORD: Optional[str] = Field(default=None, description="Metabase密码")
    
    # ===================
    # 通知配置
    # ===================
    # 邮件通知
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP服务器")
    SMTP_PORT: int = Field(default=587, description="SMTP端口")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP用户")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP密码")
    SMTP_TLS: bool = Field(default=True, description="SMTP TLS")
    
    # 企业微信通知
    WECHAT_WORK_WEBHOOK: Optional[str] = Field(default=None, description="企业微信Webhook")
    
    # 钉钉通知
    DINGTALK_WEBHOOK: Optional[str] = Field(default=None, description="钉钉Webhook")
    
    # ===================
    # 性能配置
    # ===================
    MAX_WORKERS: int = Field(default=4, description="最大工作线程数")
    ASYNC_TIMEOUT: int = Field(default=300, description="异步超时时间(秒)")
    RETRY_COUNT: int = Field(default=3, description="重试次数")
    RETRY_DELAY: int = Field(default=5, description="重试延迟(秒)")
    
    # ===================
    # 安全配置
    # ===================
    SECRET_KEY: Optional[str] = Field(default=None, description="密钥")
    ENCRYPTION_KEY: Optional[str] = Field(default=None, description="加密密钥")
    
    # ===================
    # 验证器
    # ===================
    @field_validator('DATABASE_HOST', mode='before')
    @classmethod
    def resolve_database_host(cls, v: str, info) -> str:
        """解析数据库主机（优先使用别名）"""
        if hasattr(info, 'data') and info.data:
            return info.data.get('DB_HOST', v) or v
        return v
    
    @field_validator('DATABASE_PORT', mode='before')
    @classmethod
    def resolve_database_port(cls, v: int, info) -> int:
        """解析数据库端口（优先使用别名）"""
        if hasattr(info, 'data') and info.data:
            alias_port = info.data.get('DB_PORT')
            if alias_port is not None:
                return int(alias_port)
        return v
    
    @field_validator('DATABASE_NAME', mode='before')
    @classmethod
    def resolve_database_name(cls, v: str, info) -> str:
        """解析数据库名称（优先使用别名）"""
        if hasattr(info, 'data') and info.data:
            return info.data.get('DB_NAME', v) or v
        return v
    
    @field_validator('DATABASE_USER', mode='before')
    @classmethod
    def resolve_database_user(cls, v: str, info) -> str:
        """解析数据库用户（优先使用别名）"""
        if hasattr(info, 'data') and info.data:
            return info.data.get('DB_USER', v) or v
        return v
    
    @field_validator('DATABASE_PASSWORD', mode='before')
    @classmethod
    def resolve_database_password(cls, v: str, info) -> str:
        """解析数据库密码（优先使用别名）"""
        if hasattr(info, 'data') and info.data:
            return info.data.get('DB_PASSWORD', v) or v
        return v

    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def build_database_url(cls, v: Optional[str], info) -> str:
        """构建数据库连接URL"""
        if isinstance(v, str) and v:
            return v
        
        # 使用默认值，因为在这个阶段其他字段可能还未验证
        return f"postgresql://postgres:@localhost:5432/openmautotest"
    
    @field_validator('MONGODB_HOST', mode='before')
    @classmethod
    def resolve_mongodb_host(cls, v: str, info) -> str:
        """解析MongoDB主机（优先使用别名）"""
        if hasattr(info, 'data') and info.data:
            return info.data.get('MONGO_HOST', v) or v
        return v
    
    @field_validator('MONGODB_PORT', mode='before')
    @classmethod
    def resolve_mongodb_port(cls, v: int, info) -> int:
        """解析MongoDB端口（优先使用别名）"""
        if hasattr(info, 'data') and info.data:
            alias_port = info.data.get('MONGO_PORT')
            if alias_port is not None:
                return int(alias_port)
        return v
    
    @field_validator('MONGODB_DATABASE', mode='before')
    @classmethod
    def resolve_mongodb_database(cls, v: str, info) -> str:
        """解析MongoDB数据库（优先使用别名）"""
        if hasattr(info, 'data') and info.data:
            return info.data.get('MONGO_DB', v) or v
        return v

    @field_validator('MONGODB_URL', mode='before')
    @classmethod
    def build_mongodb_url(cls, v: Optional[str], info) -> str:
        """构建MongoDB连接URL"""
        if isinstance(v, str) and v:
            return v
        return f"mongodb://localhost:27017/openmautotest"
    
    @field_validator('REDIS_URL', mode='before')
    @classmethod
    def build_redis_url(cls, v: Optional[str], info) -> str:
        """构建Redis连接URL"""
        if isinstance(v, str) and v:
            return v
        return f"redis://localhost:6379/0"
    
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v.upper()
    
    @field_validator('BROWSER_TYPE')
    @classmethod
    def validate_browser_type(cls, v: str) -> str:
        """验证浏览器类型"""
        valid_browsers = ['chromium', 'firefox', 'webkit']
        if v.lower() not in valid_browsers:
            raise ValueError(f'BROWSER_TYPE must be one of {valid_browsers}')
        return v.lower()
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证环境类型"""
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f'ENVIRONMENT must be one of {valid_envs}')
        return v.lower()
    
    # ===================
    # 配置方法
    # ===================
    def get_output_dir(self) -> Path:
        """获取输出目录"""
        output_dir = self.PROJECT_ROOT / "output"
        output_dir.mkdir(exist_ok=True)
        return output_dir
    
    def get_logs_dir(self) -> Path:
        """获取日志目录"""
        logs_dir = self.get_output_dir() / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
    
    def get_screenshots_dir(self) -> Path:
        """获取截图目录"""
        screenshots_dir = self.get_output_dir() / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        return screenshots_dir
    
    def get_allure_results_dir(self) -> Path:
        """获取Allure结果目录"""
        results_dir = self.PROJECT_ROOT / self.ALLURE_RESULTS_DIR
        results_dir.mkdir(parents=True, exist_ok=True)
        return results_dir
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.ENVIRONMENT == "testing" or self.TESTING
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )


def load_settings() -> OpenMautoTestSettings:
    """加载配置"""
    # 加载.env文件
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
    
    return OpenMautoTestSettings()


def validate_config(settings: OpenMautoTestSettings) -> List[str]:
    """验证配置完整性"""
    errors = []
    
    # 检查必需的配置项
    if not settings.SECRET_KEY and settings.is_production():
        errors.append("SECRET_KEY is required in production environment")
    
    if settings.JENKINS_URL and not settings.JENKINS_TOKEN:
        errors.append("JENKINS_TOKEN is required when JENKINS_URL is set")
    
    if settings.SMTP_HOST and not settings.SMTP_USER:
        errors.append("SMTP_USER is required when SMTP_HOST is set")
    
    # 检查路径是否存在
    if settings.WECHAT_MINI_PROJECT_PATH:
        mini_path = Path(settings.WECHAT_MINI_PROJECT_PATH)
        if not mini_path.exists():
            errors.append(f"WECHAT_MINI_PROJECT_PATH does not exist: {mini_path}")
    
    return errors


# 全局配置实例
SETTINGS = load_settings()


def get_settings() -> OpenMautoTestSettings:
    """获取全局配置实例"""
    return SETTINGS


# 配置检查函数
def check_config() -> bool:
    """检查配置是否正确"""
    try:
        settings = get_settings()
        errors = validate_config(settings)
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("Configuration validation passed")
        return True
    
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    # 测试配置加载
    print("Loading configuration...")
    settings = get_settings()
    print(f"Project: {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    
    # 验证配置
    check_config()
