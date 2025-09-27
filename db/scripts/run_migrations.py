#!/usr/bin/env python3
"""
OpenMautoTest 数据库迁移脚本

使用Alembic运行数据库迁移
"""

import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from common.logger import get_logger
from configs.db import get_db_config


def run_alembic_command(command_args):
    """运行Alembic命令"""
    logger = get_logger("db_migration")
    
    try:
        # 切换到项目根目录
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        # 构建完整命令
        full_command = ['python', '-m', 'alembic'] + command_args
        
        logger.info(f"执行命令: {' '.join(full_command)}")
        
        # 运行命令
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # 恢复原始工作目录
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            logger.info(f"命令执行成功")
            if result.stdout:
                logger.info(f"输出: {result.stdout}")
            return True
        else:
            logger.error(f"命令执行失败，返回码: {result.returncode}")
            if result.stderr:
                logger.error(f"错误输出: {result.stderr}")
            if result.stdout:
                logger.error(f"标准输出: {result.stdout}")
            return False
            
    except Exception as e:
        logger.error(f"运行Alembic命令失败: {e}")
        return False


def upgrade_database(revision="head"):
    """升级数据库到指定版本"""
    logger = get_logger("db_migration")
    
    logger.info(f"开始数据库升级到版本: {revision}")
    
    if run_alembic_command(['upgrade', revision]):
        logger.info("数据库升级完成")
        return True
    else:
        logger.error("数据库升级失败")
        return False


def downgrade_database(revision):
    """降级数据库到指定版本"""
    logger = get_logger("db_migration")
    
    logger.info(f"开始数据库降级到版本: {revision}")
    
    if run_alembic_command(['downgrade', revision]):
        logger.info("数据库降级完成")
        return True
    else:
        logger.error("数据库降级失败")
        return False


def show_current_revision():
    """显示当前数据库版本"""
    logger = get_logger("db_migration")
    
    logger.info("查询当前数据库版本...")
    
    if run_alembic_command(['current']):
        logger.info("版本查询完成")
        return True
    else:
        logger.error("版本查询失败")
        return False


def show_migration_history():
    """显示迁移历史"""
    logger = get_logger("db_migration")
    
    logger.info("查询迁移历史...")
    
    if run_alembic_command(['history']):
        logger.info("历史查询完成")
        return True
    else:
        logger.error("历史查询失败")
        return False


def generate_migration(message):
    """生成新的迁移文件"""
    logger = get_logger("db_migration")
    
    logger.info(f"生成新的迁移文件: {message}")
    
    if run_alembic_command(['revision', '--autogenerate', '-m', message]):
        logger.info("迁移文件生成完成")
        return True
    else:
        logger.error("迁移文件生成失败")
        return False


def check_database_config():
    """检查数据库配置"""
    logger = get_logger("db_migration")
    
    try:
        logger.info("检查数据库配置...")
        db_config = get_db_config()
        
        if not db_config.validate_config():
            logger.error("数据库配置验证失败")
            return False
        
        logger.info("数据库配置检查通过")
        return True
        
    except Exception as e:
        logger.error(f"数据库配置检查失败: {e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_usage()
        return 1
    
    command = sys.argv[1]
    
    # 首先检查数据库配置
    if not check_database_config():
        return 1
    
    if command == 'upgrade':
        revision = sys.argv[2] if len(sys.argv) > 2 else 'head'
        success = upgrade_database(revision)
    elif command == 'downgrade':
        if len(sys.argv) < 3:
            print("错误: downgrade 命令需要指定目标版本")
            return 1
        revision = sys.argv[2]
        success = downgrade_database(revision)
    elif command == 'current':
        success = show_current_revision()
    elif command == 'history':
        success = show_migration_history()
    elif command == 'generate':
        if len(sys.argv) < 3:
            print("错误: generate 命令需要指定迁移消息")
            return 1
        message = ' '.join(sys.argv[2:])
        success = generate_migration(message)
    else:
        print(f"错误: 未知命令 '{command}'")
        show_usage()
        return 1
    
    return 0 if success else 1


def show_usage():
    """显示使用说明"""
    print("""
OpenMautoTest 数据库迁移脚本

使用方法:
    python db/scripts/run_migrations.py <command> [options]

命令:
    upgrade [revision]     - 升级数据库到指定版本 (默认: head)
    downgrade <revision>   - 降级数据库到指定版本
    current               - 显示当前数据库版本
    history               - 显示迁移历史
    generate <message>    - 生成新的迁移文件

示例:
    python db/scripts/run_migrations.py upgrade
    python db/scripts/run_migrations.py upgrade 001
    python db/scripts/run_migrations.py downgrade 001
    python db/scripts/run_migrations.py current
    python db/scripts/run_migrations.py history
    python db/scripts/run_migrations.py generate "add user table"

注意:
    - 确保PostgreSQL数据库服务已启动
    - 确保数据库配置正确 (configs/db.yaml)
    - 确保具有数据库操作权限
    """)


if __name__ == "__main__":
    sys.exit(main())
