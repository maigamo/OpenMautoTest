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


def check_table_exists(engine, table_name):
    """检查表是否存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
            ), {"table_name": table_name})
            return result.fetchone()[0]
    except Exception:
        return False


def check_index_exists(engine, index_name):
    """检查索引是否存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = :index_name)"
            ), {"index_name": index_name})
            return result.fetchone()[0]
    except Exception:
        return False


def get_initialization_status(engine):
    """获取数据库初始化状态"""
    logger = get_logger("db_init")
    
    status = {
        'tables': {},
        'indexes': {},
        'initialized': False
    }
    
    # 检查表
    tables_to_check = ['test_case_runs', 'test_steps', 'test_run_summaries']
    for table_name in tables_to_check:
        exists = check_table_exists(engine, table_name)
        status['tables'][table_name] = exists
        logger.info(f"表 {table_name}: {'存在' if exists else '不存在'}")
    
    # 检查关键索引
    indexes_to_check = [
        'idx_run_id', 'idx_project_flow', 'idx_status', 
        'idx_summary_run_id', 'idx_test_case_run_id'
    ]
    for index_name in indexes_to_check:
        exists = check_index_exists(engine, index_name)
        status['indexes'][index_name] = exists
        logger.info(f"索引 {index_name}: {'存在' if exists else '不存在'}")
    
    # 判断是否已初始化
    all_tables_exist = all(status['tables'].values())
    status['initialized'] = all_tables_exist
    
    return status


def create_tables(engine):
    """创建数据库表（支持重复执行）"""
    logger = get_logger("db_init")
    
    try:
        logger.info("开始创建数据库表...")
        
        # 检查当前状态
        status = get_initialization_status(engine)
        
        if status['initialized']:
            logger.info("数据库表已存在，跳过创建")
            return True
        
        # 创建所有表（create_all是幂等的，不会重复创建已存在的表）
        Base.metadata.create_all(bind=engine)
        
        logger.info("数据库表创建完成")
        
        # 再次验证表是否创建成功
        final_status = get_initialization_status(engine)
        
        if final_status['initialized']:
            logger.info("数据库表创建验证成功")
            return True
        else:
            logger.error("数据库表创建验证失败")
            # 显示详细状态
            for table_name, exists in final_status['tables'].items():
                if not exists:
                    logger.error(f"表 {table_name} 创建失败")
            return False
        
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        return False


def create_indexes(engine):
    """创建额外的索引（如果需要）"""
    logger = get_logger("db_init")
    
    try:
        logger.info("检查和创建额外索引...")
        
        # 索引已经在模型定义中包含，create_all会自动创建
        # 这里可以添加额外的自定义索引逻辑
        
        logger.info("索引检查完成")
        return True
        
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        return False


def cleanup_database(engine):
    """清理数据库（删除所有表和数据）"""
    logger = get_logger("db_init")
    
    try:
        logger.warning("开始清理数据库...")
        
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        
        logger.info("数据库清理完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库清理失败: {e}")
        return False


def show_database_status(engine):
    """显示数据库状态"""
    logger = get_logger("db_init")
    
    try:
        logger.info("=== 数据库状态检查 ===")
        status = get_initialization_status(engine)
        
        logger.info(f"数据库初始化状态: {'已完成' if status['initialized'] else '未完成'}")
        
        logger.info("表状态:")
        for table_name, exists in status['tables'].items():
            logger.info(f"  {table_name}: {'✓' if exists else '✗'}")
        
        logger.info("索引状态:")
        for index_name, exists in status['indexes'].items():
            logger.info(f"  {index_name}: {'✓' if exists else '✗'}")
        
        return status
        
    except Exception as e:
        logger.error(f"状态检查失败: {e}")
        return None


def init_database(force_recreate=False):
    """初始化数据库
    
    Args:
        force_recreate: 是否强制重新创建（会先清理现有数据）
    """
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
        
        # 5. 如果强制重新创建，先清理数据库
        if force_recreate:
            logger.info("强制重新创建模式，清理现有数据...")
            if not cleanup_database(engine):
                logger.error("数据库清理失败")
                return False
        
        # 6. 显示当前状态
        show_database_status(engine)
        
        # 7. 创建数据库表
        logger.info("创建数据库表...")
        if not create_tables(engine):
            logger.error("数据库表创建失败")
            return False
        
        # 8. 创建索引
        logger.info("创建索引...")
        if not create_indexes(engine):
            logger.error("索引创建失败")
            return False
        
        # 9. 最终状态检查
        logger.info("最终状态检查...")
        final_status = show_database_status(engine)
        
        # 10. 清理资源
        engine.dispose()
        
        if final_status and final_status['initialized']:
            logger.info("数据库初始化完成！")
            return True
        else:
            logger.error("数据库初始化验证失败")
            return False
        
    except DatabaseConfigError as e:
        logger.error(f"数据库配置错误: {e}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"数据库操作错误: {e}")
        return False
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def cleanup_database_only():
    """仅清理数据库"""
    setup_logging()
    logger = get_logger("db_init")
    
    logger.info("开始数据库清理...")
    
    try:
        # 加载配置
        db_config = get_db_config()
        if not db_config.validate_config():
            logger.error("数据库配置验证失败")
            return False
        
        # 创建引擎
        engine = db_config.create_postgresql_engine()
        
        # 检查连接
        if not check_database_connection(engine):
            logger.error("数据库连接检查失败")
            return False
        
        # 显示清理前状态
        logger.info("清理前状态:")
        show_database_status(engine)
        
        # 清理数据库
        if not cleanup_database(engine):
            logger.error("数据库清理失败")
            return False
        
        # 显示清理后状态
        logger.info("清理后状态:")
        show_database_status(engine)
        
        engine.dispose()
        logger.info("数据库清理完成！")
        return True
        
    except Exception as e:
        logger.error(f"数据库清理失败: {e}")
        return False


def check_database_status():
    """仅检查数据库状态"""
    setup_logging()
    logger = get_logger("db_init")
    
    try:
        # 加载配置
        db_config = get_db_config()
        if not db_config.validate_config():
            logger.error("数据库配置验证失败")
            return False
        
        # 创建引擎
        engine = db_config.create_postgresql_engine()
        
        # 检查连接
        if not check_database_connection(engine):
            logger.error("数据库连接检查失败")
            return False
        
        # 显示状态
        status = show_database_status(engine)
        
        engine.dispose()
        return status is not None
        
    except Exception as e:
        logger.error(f"状态检查失败: {e}")
        return False


def show_usage():
    """显示使用说明"""
    print("""
OpenMautoTest 数据库初始化脚本

使用方法:
    python db/scripts/init_database.py [选项]

选项:
    -h, --help          显示此帮助信息
    --init              初始化数据库（默认操作）
    --force-recreate    强制重新创建数据库（会删除现有数据）
    --cleanup           仅清理数据库（删除所有表和数据）
    --status            仅检查数据库状态

功能:
    1. 检查数据库配置
    2. 创建数据库（如果不存在）
    3. 创建数据库表结构
    4. 创建必要的索引
    5. 验证初始化结果
    6. 支持重复执行（幂等操作）
    7. 提供数据清理功能

环境要求:
    - PostgreSQL 数据库服务已启动
    - 数据库连接配置正确 (configs/db.yaml)
    - 具有创建数据库的权限

日志文件:
    - output/logs/db_init.log

示例:
    # 初始化数据库
    python db/scripts/init_database.py
    
    # 强制重新创建（清除现有数据）
    python db/scripts/init_database.py --force-recreate
    
    # 仅清理数据库
    python db/scripts/init_database.py --cleanup
    
    # 检查数据库状态
    python db/scripts/init_database.py --status
    """)


if __name__ == "__main__":
    import argparse
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='OpenMautoTest 数据库初始化脚本', add_help=False)
    parser.add_argument('-h', '--help', action='store_true', help='显示帮助信息')
    parser.add_argument('--init', action='store_true', help='初始化数据库（默认操作）')
    parser.add_argument('--force-recreate', action='store_true', help='强制重新创建数据库')
    parser.add_argument('--cleanup', action='store_true', help='仅清理数据库')
    parser.add_argument('--status', action='store_true', help='仅检查数据库状态')
    
    args = parser.parse_args()
    
    # 显示帮助
    if args.help:
        show_usage()
        sys.exit(0)
    
    success = False
    
    try:
        if args.cleanup:
            # 清理数据库
            success = cleanup_database_only()
        elif args.status:
            # 检查状态
            success = check_database_status()
        elif args.force_recreate:
            # 强制重新创建
            success = init_database(force_recreate=True)
        else:
            # 默认初始化
            success = init_database(force_recreate=False)
            
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)
