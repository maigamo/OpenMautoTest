#!/usr/bin/env python3
"""
OpenMautoTest 数据库清理脚本

该脚本提供多种数据库清理选项，包括：
1. 清理所有表数据（保留表结构）
2. 删除所有表和索引（完全清理）
3. 清理指定时间范围的数据
4. 清理指定项目的数据
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, func
from sqlalchemy.exc import SQLAlchemyError

from common.logger import get_logger
from configs.db import get_db_config, DatabaseConfigError
from db.models import Base, TestCaseRun, TestStep, TestRunSummary


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('output/logs/db_cleanup.log', encoding='utf-8')
        ]
    )


def get_table_counts(engine):
    """获取各表的记录数"""
    logger = get_logger("db_cleanup")
    
    counts = {}
    tables = ['test_case_runs', 'test_steps', 'test_run_summaries']
    
    try:
        with engine.connect() as conn:
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    counts[table] = count
                    logger.info(f"表 {table}: {count} 条记录")
                except Exception as e:
                    logger.warning(f"无法获取表 {table} 的记录数: {e}")
                    counts[table] = 0
        
        return counts
    except Exception as e:
        logger.error(f"获取表记录数失败: {e}")
        return {}


def clear_all_data(engine):
    """清理所有表数据（保留表结构）"""
    logger = get_logger("db_cleanup")
    
    try:
        logger.info("开始清理所有表数据...")
        
        # 显示清理前的数据量
        logger.info("清理前数据统计:")
        before_counts = get_table_counts(engine)
        
        with engine.begin() as conn:
            # 按依赖关系顺序删除数据
            # 1. 先删除测试步骤（有外键依赖）
            conn.execute(text("DELETE FROM test_steps"))
            logger.info("已清理 test_steps 表数据")
            
            # 2. 删除测试用例运行记录
            conn.execute(text("DELETE FROM test_case_runs"))
            logger.info("已清理 test_case_runs 表数据")
            
            # 3. 删除测试运行汇总
            conn.execute(text("DELETE FROM test_run_summaries"))
            logger.info("已清理 test_run_summaries 表数据")
            
            # 重置序列（如果使用自增ID）
            conn.execute(text("ALTER SEQUENCE test_case_runs_id_seq RESTART WITH 1"))
            conn.execute(text("ALTER SEQUENCE test_steps_id_seq RESTART WITH 1"))
            conn.execute(text("ALTER SEQUENCE test_run_summaries_id_seq RESTART WITH 1"))
            logger.info("已重置ID序列")
        
        # 显示清理后的数据量
        logger.info("清理后数据统计:")
        after_counts = get_table_counts(engine)
        
        # 统计清理的记录数
        total_deleted = sum(before_counts.values())
        logger.info(f"总计清理了 {total_deleted} 条记录")
        
        logger.info("数据清理完成！")
        return True
        
    except Exception as e:
        logger.error(f"数据清理失败: {e}")
        return False


def drop_all_tables(engine):
    """删除所有表和索引（完全清理）"""
    logger = get_logger("db_cleanup")
    
    try:
        logger.info("开始删除所有表和索引...")
        
        # 显示删除前的状态
        logger.info("删除前数据统计:")
        get_table_counts(engine)
        
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        
        logger.info("所有表和索引已删除")
        logger.info("完全清理完成！")
        return True
        
    except Exception as e:
        logger.error(f"完全清理失败: {e}")
        return False


def clear_data_by_date_range(engine, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None):
    """按时间范围清理数据"""
    logger = get_logger("db_cleanup")
    
    try:
        logger.info(f"开始按时间范围清理数据: {start_date} 到 {end_date}")
        
        # 构建时间条件
        conditions = []
        params = {}
        
        if start_date:
            conditions.append("created_at >= :start_date")
            params['start_date'] = start_date
        
        if end_date:
            conditions.append("created_at <= :end_date")
            params['end_date'] = end_date
        
        if not conditions:
            logger.error("必须指定开始时间或结束时间")
            return False
        
        where_clause = " AND ".join(conditions)
        
        with engine.begin() as conn:
            # 1. 删除测试步骤
            step_sql = f"""
            DELETE FROM test_steps 
            WHERE test_case_run_id IN (
                SELECT id FROM test_case_runs WHERE {where_clause}
            )
            """
            result = conn.execute(text(step_sql), params)
            step_count = result.rowcount
            logger.info(f"删除了 {step_count} 条测试步骤记录")
            
            # 2. 删除测试用例运行记录
            case_sql = f"DELETE FROM test_case_runs WHERE {where_clause}"
            result = conn.execute(text(case_sql), params)
            case_count = result.rowcount
            logger.info(f"删除了 {case_count} 条测试用例记录")
            
            # 3. 删除测试运行汇总
            summary_sql = f"DELETE FROM test_run_summaries WHERE {where_clause}"
            result = conn.execute(text(summary_sql), params)
            summary_count = result.rowcount
            logger.info(f"删除了 {summary_count} 条测试汇总记录")
        
        total_deleted = step_count + case_count + summary_count
        logger.info(f"按时间范围清理完成，总计删除 {total_deleted} 条记录")
        return True
        
    except Exception as e:
        logger.error(f"按时间范围清理失败: {e}")
        return False


def clear_data_by_project(engine, project_name: str):
    """按项目名称清理数据"""
    logger = get_logger("db_cleanup")
    
    try:
        logger.info(f"开始清理项目 '{project_name}' 的数据...")
        
        with engine.begin() as conn:
            # 1. 删除测试步骤
            step_sql = """
            DELETE FROM test_steps 
            WHERE test_case_run_id IN (
                SELECT id FROM test_case_runs WHERE project_name = :project_name
            )
            """
            result = conn.execute(text(step_sql), {"project_name": project_name})
            step_count = result.rowcount
            logger.info(f"删除了 {step_count} 条测试步骤记录")
            
            # 2. 删除测试用例运行记录
            case_sql = "DELETE FROM test_case_runs WHERE project_name = :project_name"
            result = conn.execute(text(case_sql), {"project_name": project_name})
            case_count = result.rowcount
            logger.info(f"删除了 {case_count} 条测试用例记录")
            
            # 3. 删除测试运行汇总
            summary_sql = "DELETE FROM test_run_summaries WHERE project_name = :project_name"
            result = conn.execute(text(summary_sql), {"project_name": project_name})
            summary_count = result.rowcount
            logger.info(f"删除了 {summary_count} 条测试汇总记录")
        
        total_deleted = step_count + case_count + summary_count
        logger.info(f"项目数据清理完成，总计删除 {total_deleted} 条记录")
        return True
        
    except Exception as e:
        logger.error(f"项目数据清理失败: {e}")
        return False


def clear_old_data(engine, days: int = 30):
    """清理指定天数之前的旧数据"""
    logger = get_logger("db_cleanup")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    logger.info(f"清理 {days} 天前（{cutoff_date}）的数据")
    
    return clear_data_by_date_range(engine, end_date=cutoff_date)


def show_cleanup_status(engine):
    """显示清理状态和统计信息"""
    logger = get_logger("db_cleanup")
    
    try:
        logger.info("=== 数据库清理状态 ===")
        
        # 显示表记录数
        counts = get_table_counts(engine)
        total_records = sum(counts.values())
        
        logger.info(f"总记录数: {total_records}")
        
        # 显示最早和最新的记录时间
        with engine.connect() as conn:
            # 最早记录
            result = conn.execute(text(
                "SELECT MIN(created_at) FROM test_case_runs"
            ))
            earliest = result.fetchone()[0]
            
            # 最新记录
            result = conn.execute(text(
                "SELECT MAX(created_at) FROM test_case_runs"
            ))
            latest = result.fetchone()[0]
            
            if earliest and latest:
                logger.info(f"数据时间范围: {earliest} 到 {latest}")
            
            # 按项目统计
            result = conn.execute(text(
                "SELECT project_name, COUNT(*) FROM test_case_runs GROUP BY project_name ORDER BY COUNT(*) DESC"
            ))
            projects = result.fetchall()
            
            if projects:
                logger.info("按项目统计:")
                for project, count in projects:
                    logger.info(f"  {project or '未知项目'}: {count} 条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"状态检查失败: {e}")
        return False


def show_usage():
    """显示使用说明"""
    print("""
OpenMautoTest 数据库清理脚本

使用方法:
    python db/scripts/cleanup_database.py [选项]

选项:
    -h, --help              显示此帮助信息
    --clear-data            清理所有表数据（保留表结构）
    --drop-tables           删除所有表和索引（完全清理）
    --clear-old DAYS        清理指定天数之前的数据（默认30天）
    --clear-project NAME    清理指定项目的数据
    --clear-date-range START END  清理指定时间范围的数据（格式：YYYY-MM-DD）
    --status                显示数据库状态和统计信息

警告:
    - 数据清理操作不可逆，请在执行前备份重要数据
    - --drop-tables 会完全删除所有表结构
    - 建议先使用 --status 查看数据状态

示例:
    # 查看数据库状态
    python db/scripts/cleanup_database.py --status
    
    # 清理所有数据（保留表结构）
    python db/scripts/cleanup_database.py --clear-data
    
    # 清理30天前的数据
    python db/scripts/cleanup_database.py --clear-old 30
    
    # 清理指定项目的数据
    python db/scripts/cleanup_database.py --clear-project "MyProject"
    
    # 清理指定时间范围的数据
    python db/scripts/cleanup_database.py --clear-date-range 2025-01-01 2025-01-31
    
    # 完全清理（删除所有表）
    python db/scripts/cleanup_database.py --drop-tables

日志文件:
    - output/logs/db_cleanup.log
    """)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenMautoTest 数据库清理脚本', add_help=False)
    parser.add_argument('-h', '--help', action='store_true', help='显示帮助信息')
    parser.add_argument('--clear-data', action='store_true', help='清理所有表数据')
    parser.add_argument('--drop-tables', action='store_true', help='删除所有表和索引')
    parser.add_argument('--clear-old', type=int, metavar='DAYS', help='清理指定天数之前的数据')
    parser.add_argument('--clear-project', type=str, metavar='NAME', help='清理指定项目的数据')
    parser.add_argument('--clear-date-range', nargs=2, metavar=('START', 'END'), help='清理指定时间范围的数据')
    parser.add_argument('--status', action='store_true', help='显示数据库状态')
    
    args = parser.parse_args()
    
    if args.help:
        show_usage()
        return 0
    
    setup_logging()
    logger = get_logger("db_cleanup")
    
    try:
        # 加载数据库配置
        db_config = get_db_config()
        if not db_config.validate_config():
            logger.error("数据库配置验证失败")
            return 1
        
        # 创建数据库引擎
        engine = db_config.create_postgresql_engine()
        
        # 检查数据库连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        success = False
        
        if args.status:
            success = show_cleanup_status(engine)
        elif args.clear_data:
            # 确认操作
            print("警告: 此操作将清理所有表数据（保留表结构），操作不可逆！")
            confirm = input("请输入 'YES' 确认继续: ")
            if confirm == 'YES':
                success = clear_all_data(engine)
            else:
                print("操作已取消")
                return 0
        elif args.drop_tables:
            # 确认操作
            print("警告: 此操作将删除所有表和索引，操作不可逆！")
            confirm = input("请输入 'DELETE ALL TABLES' 确认继续: ")
            if confirm == 'DELETE ALL TABLES':
                success = drop_all_tables(engine)
            else:
                print("操作已取消")
                return 0
        elif args.clear_old is not None:
            success = clear_old_data(engine, args.clear_old)
        elif args.clear_project:
            success = clear_data_by_project(engine, args.clear_project)
        elif args.clear_date_range:
            try:
                start_date = datetime.strptime(args.clear_date_range[0], '%Y-%m-%d')
                end_date = datetime.strptime(args.clear_date_range[1], '%Y-%m-%d')
                success = clear_data_by_date_range(engine, start_date, end_date)
            except ValueError as e:
                logger.error(f"日期格式错误: {e}")
                return 1
        else:
            # 默认显示状态
            success = show_cleanup_status(engine)
        
        engine.dispose()
        return 0 if success else 1
        
    except DatabaseConfigError as e:
        logger.error(f"数据库配置错误: {e}")
        return 1
    except SQLAlchemyError as e:
        logger.error(f"数据库操作错误: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        return 1
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
