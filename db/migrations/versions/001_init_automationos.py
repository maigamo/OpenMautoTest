"""Initial migration - create test tables

Revision ID: 001
Revises: 
Create Date: 2025-09-23 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_case_runs table
    op.create_table('test_case_runs',
        sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False, comment='唯一标识符'),
        sa.Column('run_id', sa.String(length=255), nullable=False, comment='单次任务ID'),
        sa.Column('project_name', sa.String(length=100), nullable=True, comment='项目/团队名称'),
        sa.Column('flow_name', sa.String(length=255), nullable=True, comment='业务流程名称'),
        sa.Column('test_case_name', sa.Text(), nullable=False, comment='测试用例名称'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='执行结果 (passed/failed/skipped)'),
        sa.Column('environment', sa.String(length=50), nullable=True, comment='测试环境'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, comment='开始时间'),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True, comment='结束时间'),
        sa.Column('duration', sa.Float(), nullable=True, comment='执行耗时(秒)'),
        sa.Column('failure_reason', sa.Text(), nullable=True, comment='失败原因'),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='详细错误信息'),
        sa.Column('retry_attempt', sa.Integer(), nullable=True, comment='重试次数'),
        sa.Column('jenkins_build_url', sa.Text(), nullable=True, comment='Jenkins构建链接'),
        sa.Column('build_number', sa.String(length=50), nullable=True, comment='构建编号'),
        sa.Column('browser_type', sa.String(length=50), nullable=True, comment='浏览器类型'),
        sa.Column('browser_version', sa.String(length=50), nullable=True, comment='浏览器版本'),
        sa.Column('platform', sa.String(length=50), nullable=True, comment='执行平台'),
        sa.Column('test_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='测试数据'),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='测试标签'),
        sa.Column('page_load_time', sa.Float(), nullable=True, comment='页面加载时间'),
        sa.Column('network_time', sa.Float(), nullable=True, comment='网络耗时'),
        sa.Column('screenshots', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='截图文件路径列表'),
        sa.Column('log_file_path', sa.String(length=500), nullable=True, comment='日志文件路径'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, comment='是否删除'),
        sa.CheckConstraint("status IN ('passed', 'failed', 'skipped', 'running', 'pending')", name='ck_status'),
        sa.CheckConstraint('duration >= 0', name='ck_duration_positive'),
        sa.CheckConstraint('retry_attempt >= 0', name='ck_retry_positive'),
        sa.PrimaryKeyConstraint('id'),
        comment='测试用例执行记录表'
    )
    
    # Create indexes for test_case_runs
    op.create_index('idx_run_id', 'test_case_runs', ['run_id'], unique=False)
    op.create_index('idx_project_flow', 'test_case_runs', ['project_name', 'flow_name'], unique=False)
    op.create_index('idx_status', 'test_case_runs', ['status'], unique=False)
    op.create_index('idx_start_time', 'test_case_runs', ['start_time'], unique=False)
    op.create_index('idx_environment', 'test_case_runs', ['environment'], unique=False)
    op.create_index('idx_created_at', 'test_case_runs', ['created_at'], unique=False)
    
    # Create test_steps table
    op.create_table('test_steps',
        sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False, comment='唯一标识符'),
        sa.Column('test_case_run_id', sa.BIGINT(), nullable=False, comment='关联的测试用例ID'),
        sa.Column('step_name', sa.String(length=255), nullable=False, comment='步骤名称'),
        sa.Column('step_description', sa.Text(), nullable=True, comment='步骤描述'),
        sa.Column('step_order', sa.Integer(), nullable=False, comment='步骤顺序'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='步骤状态 (passed/failed/skipped)'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, comment='开始时间'),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True, comment='结束时间'),
        sa.Column('duration', sa.Float(), nullable=True, comment='执行耗时(秒)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误消息'),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='详细错误信息'),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='输入数据'),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='输出数据'),
        sa.Column('expected_result', sa.Text(), nullable=True, comment='期望结果'),
        sa.Column('actual_result', sa.Text(), nullable=True, comment='实际结果'),
        sa.Column('screenshot_path', sa.String(length=500), nullable=True, comment='截图路径'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, comment='创建时间'),
        sa.CheckConstraint("status IN ('passed', 'failed', 'skipped', 'running', 'pending')", name='ck_step_status'),
        sa.CheckConstraint('duration >= 0', name='ck_step_duration_positive'),
        sa.CheckConstraint('step_order >= 0', name='ck_step_order_positive'),
        sa.ForeignKeyConstraint(['test_case_run_id'], ['test_case_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='测试步骤记录表'
    )
    
    # Create indexes for test_steps
    op.create_index('idx_test_case_run_id', 'test_steps', ['test_case_run_id'], unique=False)
    op.create_index('idx_step_name', 'test_steps', ['step_name'], unique=False)
    op.create_index('idx_step_status', 'test_steps', ['status'], unique=False)
    op.create_index('idx_step_order', 'test_steps', ['step_order'], unique=False)
    op.create_index('idx_step_created_at', 'test_steps', ['created_at'], unique=False)
    
    # Create test_run_summaries table
    op.create_table('test_run_summaries',
        sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False, comment='唯一标识符'),
        sa.Column('run_id', sa.String(length=255), nullable=False, comment='运行ID'),
        sa.Column('run_name', sa.String(length=255), nullable=True, comment='运行名称'),
        sa.Column('run_description', sa.Text(), nullable=True, comment='运行描述'),
        sa.Column('project_name', sa.String(length=100), nullable=True, comment='项目名称'),
        sa.Column('environment', sa.String(length=50), nullable=True, comment='测试环境'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, comment='开始时间'),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True, comment='结束时间'),
        sa.Column('duration', sa.Float(), nullable=True, comment='总耗时(秒)'),
        sa.Column('total_tests', sa.Integer(), nullable=True, comment='总测试数'),
        sa.Column('passed_tests', sa.Integer(), nullable=True, comment='通过测试数'),
        sa.Column('failed_tests', sa.Integer(), nullable=True, comment='失败测试数'),
        sa.Column('skipped_tests', sa.Integer(), nullable=True, comment='跳过测试数'),
        sa.Column('pass_rate', sa.Float(), nullable=True, comment='通过率'),
        sa.Column('jenkins_build_url', sa.Text(), nullable=True, comment='Jenkins构建链接'),
        sa.Column('build_number', sa.String(length=50), nullable=True, comment='构建编号'),
        sa.Column('browser_type', sa.String(length=50), nullable=True, comment='浏览器类型'),
        sa.Column('platform', sa.String(length=50), nullable=True, comment='执行平台'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.CheckConstraint('total_tests >= 0', name='ck_total_tests_positive'),
        sa.CheckConstraint('passed_tests >= 0', name='ck_passed_tests_positive'),
        sa.CheckConstraint('failed_tests >= 0', name='ck_failed_tests_positive'),
        sa.CheckConstraint('skipped_tests >= 0', name='ck_skipped_tests_positive'),
        sa.CheckConstraint('pass_rate >= 0 AND pass_rate <= 100', name='ck_pass_rate_range'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id'),
        comment='测试运行汇总表'
    )
    
    # Create indexes for test_run_summaries
    op.create_index('idx_summary_run_id', 'test_run_summaries', ['run_id'], unique=False)
    op.create_index('idx_summary_project_name', 'test_run_summaries', ['project_name'], unique=False)
    op.create_index('idx_summary_environment', 'test_run_summaries', ['environment'], unique=False)
    op.create_index('idx_summary_start_time', 'test_run_summaries', ['start_time'], unique=False)
    op.create_index('idx_summary_created_at', 'test_run_summaries', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('test_run_summaries')
    op.drop_table('test_steps')
    op.drop_table('test_case_runs')
