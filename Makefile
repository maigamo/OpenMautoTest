# OpenMautoTest Makefile
# 提供常用的项目管理命令

.PHONY: help install test check-config meta-up migrate clean lint format setup-dev

# 默认目标
help:
	@echo "OpenMautoTest 可用命令："
	@echo "  make install      - 安装项目依赖"
	@echo "  make test         - 运行所有测试"
	@echo "  make check-config - 检查配置文件"
	@echo "  make meta-up      - 启动 Metabase 服务"
	@echo "  make migrate      - 执行数据库迁移"
	@echo "  make lint         - 代码质量检查"
	@echo "  make format       - 代码格式化"
	@echo "  make setup-dev    - 设置开发环境"
	@echo "  make clean        - 清理临时文件"

# 安装依赖
install:
	@echo "安装 Python 依赖..."
	pip install -r requirements.txt
	@echo "安装 Playwright 浏览器..."
	playwright install
	@echo "检查 Node.js 版本（小程序自动化需要）..."
	node --version || echo "警告: 未找到 Node.js，小程序自动化功能将不可用"

# 运行测试
test:
	@echo "运行测试套件..."
	python -m pytest -v --tb=short --alluredir=output/allure-results

# 运行快速测试（排除慢速测试）
test-fast:
	@echo "运行快速测试..."
	python -m pytest -v -m "not slow" --tb=short

# 运行特定类型的测试
test-web:
	@echo "运行 Web 端测试..."
	python -m pytest -v -m web --tb=short

test-mini:
	@echo "运行小程序测试..."
	python -m pytest -v -m mini --tb=short

test-api:
	@echo "运行 API 测试..."
	python -m pytest -v -m api --tb=short

# 检查配置
check-config:
	@echo "检查项目配置..."
	python -c "from configs.settings import SETTINGS; print('配置检查通过:', SETTINGS)" || echo "配置检查失败"
	@echo "检查数据库连接配置..."
	python -c "from configs.db import check_db_config; check_db_config()" || echo "数据库配置检查失败"

# 启动 Metabase 服务
meta-up:
	@echo "启动 Metabase 和 PostgreSQL 服务..."
	docker-compose -f docker-compose.meta.yml up -d
	@echo "Metabase 将在 http://localhost:3000 启动"
	@echo "PostgreSQL 将在 localhost:5432 启动"

# 停止 Metabase 服务
meta-down:
	@echo "停止 Metabase 和 PostgreSQL 服务..."
	docker-compose -f docker-compose.meta.yml down

# 数据库迁移
migrate:
	@echo "执行数据库迁移..."
	alembic upgrade head

# 创建新的数据库迁移
migrate-create:
	@echo "创建新的数据库迁移脚本..."
	alembic revision --autogenerate -m "$(MSG)"

# 代码质量检查
lint:
	@echo "运行代码质量检查..."
	flake8 common configs db drivers orchestrator llm --max-line-length=88 --exclude=__pycache__,migrations
	mypy common configs db drivers orchestrator llm --ignore-missing-imports

# 代码格式化
format:
	@echo "格式化代码..."
	black common configs db drivers orchestrator llm
	isort common configs db drivers orchestrator llm

# 设置开发环境
setup-dev:
	@echo "设置开发环境..."
	pip install -e ".[dev]"
	@echo "安装 pre-commit hooks..."
	pip install pre-commit
	pre-commit install || echo "pre-commit 安装失败，请手动安装"
	@echo "创建环境变量文件..."
	cp .env.example .env || echo "请手动创建 .env 文件"

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	rm -rf .pytest_cache/ || true
	rm -rf .mypy_cache/ || true
	rm -rf output/logs/* || true
	rm -rf output/screenshots/* || true
	@echo "清理完成"

# 生成测试报告
report:
	@echo "生成 Allure 测试报告..."
	allure generate output/allure-results -o output/allure-report --clean
	@echo "报告生成在 output/allure-report 目录"

# 启动测试报告服务
report-serve:
	@echo "启动 Allure 报告服务..."
	allure serve output/allure-results

# 检查环境依赖
check-env:
	@echo "检查环境依赖..."
	@echo "Python 版本:"
	python --version
	@echo "Node.js 版本:"
	node --version || echo "Node.js 未安装"
	@echo "Docker 版本:"
	docker --version || echo "Docker 未安装"
	@echo "Docker Compose 版本:"
	docker-compose --version || echo "Docker Compose 未安装"

# 数据库初始化
db-init:
	@echo "初始化数据库..."
	alembic init db/migrations || echo "Alembic 已初始化"
	alembic revision --autogenerate -m "Initial migration"
	alembic upgrade head

# 导入历史数据
import-data:
	@echo "导入历史测试数据..."
	python db/scripts/import_jl_to_db.py

# 启动调度服务器
scheduler:
	@echo "启动调度服务器..."
	cd scheduler_server && python main.py

# 运行完整的 CI 流水线
ci: lint test
	@echo "CI 流水线执行完成"

# 部署检查
deploy-check: check-env check-config test
	@echo "部署前检查完成"
