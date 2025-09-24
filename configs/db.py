"""
OpenMautoTest 数据库配置管理模块

提供数据库连接配置的加载和管理功能
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import QueuePool

from .settings import get_settings


class DatabaseConfigError(Exception):
    """数据库配置错误"""
    pass


class DatabaseConfig:
    """数据库配置管理类"""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """初始化数据库配置
        
        Args:
            config_file: 配置文件路径，默认使用 configs/db.yaml
        """
        self.settings = get_settings()
        
        if config_file is None:
            config_file = Path(__file__).parent / "db.yaml"
        
        self.config_file = Path(config_file)
        self._config: Optional[Dict] = None
        self._engines: Dict[str, Engine] = {}
        
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if not self.config_file.exists():
            raise DatabaseConfigError(f"Database config file not found: {self.config_file}")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 替换环境变量
            content = self._substitute_env_vars(content)
            
            self._config = yaml.safe_load(content)
            
        except yaml.YAMLError as e:
            raise DatabaseConfigError(f"Invalid YAML in database config: {e}")
        except Exception as e:
            raise DatabaseConfigError(f"Failed to load database config: {e}")
    
    def _substitute_env_vars(self, content: str) -> str:
        """替换配置中的环境变量
        
        支持格式：${VAR_NAME:default_value} 或 ${VAR_NAME}
        """
        def replace_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name, default_value)
            else:
                var_value = os.getenv(var_expr)
                if var_value is None:
                    raise DatabaseConfigError(f"Required environment variable not set: {var_expr}")
                return var_value
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, content)
    
    def get_environment_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """获取指定环境的配置
        
        Args:
            environment: 环境名称，默认使用当前环境
        
        Returns:
            环境配置字典
        """
        if environment is None:
            environment = self.settings.ENVIRONMENT
        
        if environment not in self._config:
            raise DatabaseConfigError(f"Environment '{environment}' not found in database config")
        
        return self._config[environment]
    
    def get_postgresql_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """获取PostgreSQL配置"""
        env_config = self.get_environment_config(environment)
        
        if 'postgresql' not in env_config:
            raise DatabaseConfigError("PostgreSQL config not found")
        
        return env_config['postgresql']
    
    def get_mongodb_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """获取MongoDB配置"""
        env_config = self.get_environment_config(environment)
        
        if 'mongodb' not in env_config:
            raise DatabaseConfigError("MongoDB config not found")
        
        return env_config['mongodb']
    
    def get_redis_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """获取Redis配置"""
        env_config = self.get_environment_config(environment)
        
        if 'redis' not in env_config:
            raise DatabaseConfigError("Redis config not found")
        
        return env_config['redis']
    
    def get_postgresql_url(self, environment: Optional[str] = None) -> str:
        """获取PostgreSQL连接URL"""
        config = self.get_postgresql_config(environment)
        
        host = config['host']
        port = config['port']
        database = config['database']
        username = config['username']
        password = config['password']
        
        # 构建连接URL
        url = f"postgresql://{username}"
        if password:
            url += f":{password}"
        url += f"@{host}:{port}/{database}"
        
        # 添加SSL配置
        if config.get('ssl_mode'):
            url += f"?sslmode={config['ssl_mode']}"
        
        return url
    
    def get_mongodb_url(self, environment: Optional[str] = None) -> str:
        """获取MongoDB连接URL"""
        config = self.get_mongodb_config(environment)
        
        host = config['host']
        port = config['port']
        database = config['database']
        username = config.get('username', '')
        password = config.get('password', '')
        
        # 构建连接URL
        if username:
            url = f"mongodb://{username}"
            if password:
                url += f":{password}"
            url += f"@{host}:{port}/{database}"
        else:
            url = f"mongodb://{host}:{port}/{database}"
        
        # 添加认证源
        if config.get('auth_source'):
            url += f"?authSource={config['auth_source']}"
        
        # 添加SSL配置
        if config.get('ssl'):
            separator = '&' if '?' in url else '?'
            url += f"{separator}ssl=true"
        
        return url
    
    def get_redis_url(self, environment: Optional[str] = None) -> str:
        """获取Redis连接URL"""
        config = self.get_redis_config(environment)
        
        host = config['host']
        port = config['port']
        db = config['db']
        password = config.get('password', '')
        
        # 构建连接URL
        if password:
            url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            url = f"redis://{host}:{port}/{db}"
        
        # 添加SSL配置
        if config.get('ssl'):
            url = url.replace('redis://', 'rediss://')
        
        return url
    
    def create_postgresql_engine(self, environment: Optional[str] = None) -> Engine:
        """创建PostgreSQL引擎"""
        if environment is None:
            environment = self.settings.ENVIRONMENT
        
        engine_key = f"postgresql_{environment}"
        
        if engine_key not in self._engines:
            config = self.get_postgresql_config(environment)
            url = self.get_postgresql_url(environment)
            
            # 创建引擎
            engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=config.get('pool_size', 10),
                max_overflow=config.get('max_overflow', 20),
                pool_timeout=config.get('pool_timeout', 30),
                pool_recycle=config.get('pool_recycle', 3600),
                echo=config.get('echo', False),
                echo_pool=config.get('echo_pool', False)
            )
            
            self._engines[engine_key] = engine
        
        return self._engines[engine_key]
    
    def get_table_config(self, table_name: str) -> Dict[str, Any]:
        """获取表配置"""
        tables_config = self._config.get('tables', {})
        
        if table_name not in tables_config:
            raise DatabaseConfigError(f"Table config not found: {table_name}")
        
        return tables_config[table_name]
    
    def get_migration_config(self) -> Dict[str, Any]:
        """获取迁移配置"""
        return self._config.get('migration', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self._config.get('monitoring', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self._config.get('security', {})
    
    def validate_config(self, environment: Optional[str] = None) -> bool:
        """验证配置"""
        try:
            # 验证环境配置存在
            env_config = self.get_environment_config(environment)
            
            # 验证PostgreSQL配置
            if 'postgresql' in env_config:
                pg_config = env_config['postgresql']
                required_fields = ['host', 'port', 'database', 'username']
                for field in required_fields:
                    if field not in pg_config:
                        raise DatabaseConfigError(f"Missing required PostgreSQL field: {field}")
            
            # 验证MongoDB配置
            if 'mongodb' in env_config:
                mongo_config = env_config['mongodb']
                required_fields = ['host', 'port', 'database']
                for field in required_fields:
                    if field not in mongo_config:
                        raise DatabaseConfigError(f"Missing required MongoDB field: {field}")
            
            # 验证Redis配置
            if 'redis' in env_config:
                redis_config = env_config['redis']
                required_fields = ['host', 'port', 'db']
                for field in required_fields:
                    if field not in redis_config:
                        raise DatabaseConfigError(f"Missing required Redis field: {field}")
            
            return True
            
        except Exception as e:
            print(f"Database config validation failed: {e}")
            return False
    
    def test_connections(self, environment: Optional[str] = None) -> Dict[str, bool]:
        """测试数据库连接"""
        results = {}
        
        try:
            # 测试PostgreSQL连接
            if 'postgresql' in self.get_environment_config(environment):
                try:
                    engine = self.create_postgresql_engine(environment)
                    with engine.connect() as conn:
                        conn.execute("SELECT 1")
                    results['postgresql'] = True
                except Exception as e:
                    print(f"PostgreSQL connection failed: {e}")
                    results['postgresql'] = False
        except:
            results['postgresql'] = False
        
        # TODO: 添加MongoDB和Redis连接测试
        
        return results


# 全局数据库配置实例
_db_config: Optional[DatabaseConfig] = None


def get_db_config() -> DatabaseConfig:
    """获取全局数据库配置实例"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_postgresql_engine(environment: Optional[str] = None) -> Engine:
    """获取PostgreSQL引擎"""
    return get_db_config().create_postgresql_engine(environment)


def get_postgresql_url(environment: Optional[str] = None) -> str:
    """获取PostgreSQL连接URL"""
    return get_db_config().get_postgresql_url(environment)


def get_mongodb_url(environment: Optional[str] = None) -> str:
    """获取MongoDB连接URL"""
    return get_db_config().get_mongodb_url(environment)


def get_redis_url(environment: Optional[str] = None) -> str:
    """获取Redis连接URL"""
    return get_db_config().get_redis_url(environment)


def check_db_config() -> bool:
    """检查数据库配置"""
    try:
        db_config = get_db_config()
        
        # 验证配置
        if not db_config.validate_config():
            return False
        
        # 测试连接
        results = db_config.test_connections()
        
        print("Database connection test results:")
        for db_type, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {db_type}")
        
        # 如果所有连接都成功，返回True
        return all(results.values())
    
    except Exception as e:
        print(f"Database config check failed: {e}")
        return False


if __name__ == "__main__":
    # 测试数据库配置
    print("Testing database configuration...")
    
    try:
        db_config = get_db_config()
        
        # 显示当前环境配置
        print(f"Current environment: {db_config.settings.ENVIRONMENT}")
        
        # 获取PostgreSQL URL
        try:
            pg_url = get_postgresql_url()
            print(f"PostgreSQL URL: {pg_url}")
        except Exception as e:
            print(f"PostgreSQL config error: {e}")
        
        # 获取MongoDB URL
        try:
            mongo_url = get_mongodb_url()
            print(f"MongoDB URL: {mongo_url}")
        except Exception as e:
            print(f"MongoDB config error: {e}")
        
        # 获取Redis URL
        try:
            redis_url = get_redis_url()
            print(f"Redis URL: {redis_url}")
        except Exception as e:
            print(f"Redis config error: {e}")
        
        # 验证配置
        if db_config.validate_config():
            print("Database configuration validation passed")
        else:
            print("Database configuration validation failed")
        
    except Exception as e:
        print(f"Database configuration test failed: {e}")
    
    print("Database configuration tests completed.")
