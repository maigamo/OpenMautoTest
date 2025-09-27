#!/usr/bin/env python3
"""
OpenMautoTest 数据库初始化脚本

该脚本用于初始化数据库，创建表结构和必要的索引
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from common.logger import get_logger
from configs.db import get_db_config, DatabaseConfigError
from db.models import Base


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('output/logs/db_init.log', encoding='utf-8')
        ]
    )


def check_database_connection(engine):
    """检查数据库连接"""
    logger = get_logger("db_init")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"数据库连接成功，版本: {version}")
            return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    logger = get_logger("db_init")
    
    try:
        db_config = get_db_config()
        pg_config = db_config.get_postgresql_config()
        
        # 连接到postgres数据库来创建目标数据库
        postgres_url = f"postgresql://{pg_config['username']}"
        if pg_config.get('password'):
            postgres_url += f":{pg_config['password']}"
        postgres_url += f"@{pg_config['host']}:{pg_config['port']}/postgres"
        
        # 创建引擎连接到postgres数据库
        postgres_engine = create_engine(postgres_url)
        
        # 检查目标数据库是否存在
        database_name = pg_config['database']
        
        with postgres_engine.connect() as conn:
            # 设置自动提交模式来执行CREATE DATABASE
            conn = conn.execution_options(autocommit=True)
            
            # 检查数据库是否存在
            result = conn.execute(text(
                "SELECT 1 FROM pg_database WHERE datname = :db_name"
            ), {"db_name": database_name})
            
            if result.fetchone() is None:
                # 数据库不存在，创建它
                logger.info(f"创建数据库: {database_name}")
                conn.execute(text(f'CREATE DATABASE "{database_name}"'))
                logger.info(f"数据库 {database_name} 创建成功")
            else:
                logger.info(f"数据库 {database_name} 已存在")
        
        postgres_engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        return False


def create_tables(engine):
    """创建数据库表"""
    logger = get_logger("db_init")
    
    try:
        logger.info("开始创建数据库表...")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logger.info("数据库表创建成功")
        
        # 验证表是否创建成功
        with engine.connect() as conn:
            # 检查主要表是否存在
            tables_to_check = ['test_case_runs', 'test_steps', 'test_run_summaries']
            
            for table_name in tables_to_check:
                result = conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
                ), {"table_name": table_name})
                
                exists = result.fetchone()[0]
                if exists:
                    logger.info(f"表 {table_name} 验证成功")
                else:
                    logger.error(f"表 {table_name} 创建失败")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        return False


def create_indexes(engine):
    """创建额外的索引（如果需要）"""
    logger = get_logger("db_init")
    
    try:
        logger.info("检查和创建额外索引...")
        
        # 这里可以添加额外的索引创建逻辑
        # 当前版本的索引已经在模型定义中包含了
        
        logger.info("索引检查完成")
        return True
        
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        return False


def init_database():
    """初始化数据库"""
    setup_logging()
    logger = get_logger("db_init")
    
    logger.info("开始数据库初始化...")
    
    try:
        # 1. 加载数据库配置
        logger.info("加载数据库配置...")
        db_config = get_db_config()
        
        if not db_config.validate_config():
            logger.error("数据库配置验证失败")
            return False
        
        # 2. 创建数据库（如果不存在）
        logger.info("检查并创建数据库...")
        if not create_database_if_not_exists():
            logger.error("数据库创建失败")
            return False
        
        # 3. 创建数据库引擎
        logger.info("创建数据库引擎...")
        engine = db_config.create_postgresql_engine()
        
        # 4. 检查数据库连接
        logger.info("检查数据库连接...")
        if not check_database_connection(engine):
            logger.error("数据库连接检查失败")
            return False
        
        # 5. 创建数据库表
        logger.info("创建数据库表...")
        if not create_tables(engine):
            logger.error("数据库表创建失败")
            return False
        
        # 6. 创建索引
        logger.info("创建索引...")
        if not create_indexes(engine):
            logger.error("索引创建失败")
            return False
        
        # 7. 清理资源
        engine.dispose()
        
        logger.info("数据库初始化完成！")
        return True
        
    except DatabaseConfigError as e:
        logger.error(f"数据库配置错误: {e}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"数据库操作错误: {e}")
        return False
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def show_usage():
    """显示使用说明"""
    print("""
OpenMautoTest 数据库初始化脚本

使用方法:
    python db/scripts/init_database.py

功能:
    1. 检查数据库配置
    2. 创建数据库（如果不存在）
    3. 创建数据库表结构
    4. 创建必要的索引
    5. 验证初始化结果

环境要求:
    - PostgreSQL 数据库服务已启动
    - 数据库连接配置正确 (configs/db.yaml)
    - 具有创建数据库的权限

日志文件:
    - output/logs/db_init.log
    """)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_usage()
        sys.exit(0)
    
    success = init_database()
    sys.exit(0 if success else 1)
