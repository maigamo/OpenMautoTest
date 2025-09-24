#!/bin/bash

# OpenMautoTest 环境设置脚本
# 用于CI/CD环境的初始化和配置

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Python版本
check_python() {
    log_info "Checking Python version..."
    
    if ! command_exists python; then
        log_error "Python not found. Please install Python 3.8 or higher."
        exit 1
    fi
    
    python_version=$(python --version 2>&1 | awk '{print $2}')
    log_info "Python version: $python_version"
    
    # 检查版本是否满足要求 (3.8+)
    required_version="3.8"
    if python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python version check passed"
    else
        log_error "Python version $python_version is not supported. Requires Python 3.8+"
        exit 1
    fi
}

# 检查Node.js版本
check_nodejs() {
    log_info "Checking Node.js version..."
    
    if ! command_exists node; then
        log_warning "Node.js not found. Mini-program tests will be disabled."
        return 0
    fi
    
    node_version=$(node --version)
    log_info "Node.js version: $node_version"
    
    # 检查版本是否满足要求 (16+)
    if node -e "process.exit(process.version.match(/^v(\d+)/)[1] >= 16 ? 0 : 1)"; then
        log_success "Node.js version check passed"
    else
        log_warning "Node.js version $node_version may not be fully supported. Recommends Node.js 16+"
    fi
}

# 安装Python依赖
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # 升级pip
    python -m pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

# 安装Playwright浏览器
install_browsers() {
    log_info "Installing Playwright browsers..."
    
    # 获取浏览器类型参数，默认安装所有浏览器
    BROWSER_TYPE=${1:-"all"}
    
    case $BROWSER_TYPE in
        "chromium")
            playwright install chromium
            playwright install-deps chromium
            ;;
        "firefox")
            playwright install firefox
            playwright install-deps firefox
            ;;
        "webkit")
            playwright install webkit
            playwright install-deps webkit
            ;;
        "all"|*)
            playwright install
            playwright install-deps
            ;;
    esac
    
    log_success "Playwright browsers installed"
}

# 验证浏览器安装
verify_browsers() {
    log_info "Verifying browser installations..."
    
    # 测试Playwright浏览器
    python -c "
from playwright.sync_api import sync_playwright
import sys

try:
    with sync_playwright() as p:
        # 测试Chromium
        try:
            browser = p.chromium.launch()
            browser.close()
            print('✅ Chromium: OK')
        except Exception as e:
            print(f'❌ Chromium: Failed - {e}')
        
        # 测试Firefox
        try:
            browser = p.firefox.launch()
            browser.close()
            print('✅ Firefox: OK')
        except Exception as e:
            print(f'❌ Firefox: Failed - {e}')
        
        # 测试WebKit
        try:
            browser = p.webkit.launch()
            browser.close()
            print('✅ WebKit: OK')
        except Exception as e:
            print(f'❌ WebKit: Failed - {e}')

except Exception as e:
    print(f'❌ Browser verification failed: {e}')
    sys.exit(1)
"
    
    log_success "Browser verification completed"
}

# 设置环境变量
setup_environment() {
    log_info "Setting up environment variables..."
    
    # 创建.env文件（如果不存在）
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        log_info "Created .env file from .env.example"
    fi
    
    # 设置PYTHONPATH
    export PYTHONPATH=$(pwd)
    echo "export PYTHONPATH=$(pwd)" >> ~/.bashrc
    
    # 设置其他环境变量
    export PYTHONUNBUFFERED=1
    
    log_success "Environment variables configured"
}

# 创建输出目录
create_output_dirs() {
    log_info "Creating output directories..."
    
    mkdir -p output/{screenshots,logs,reports,videos,allure-results,temp,archive}
    
    # 设置权限
    chmod -R 755 output/
    
    log_success "Output directories created"
}

# 验证配置
verify_configuration() {
    log_info "Verifying configuration..."
    
    # 测试配置加载
    python -c "
from configs.settings import get_settings
try:
    settings = get_settings()
    print(f'✅ Project: {settings.PROJECT_NAME}')
    print(f'✅ Environment: {settings.ENVIRONMENT}')
    print('✅ Configuration loaded successfully')
except Exception as e:
    print(f'❌ Configuration verification failed: {e}')
    exit(1)
"
    
    log_success "Configuration verification passed"
}

# 运行基础测试
run_basic_tests() {
    log_info "Running basic functionality tests..."
    
    # 测试导入
    python -c "
import sys
modules_to_test = [
    'common.logger',
    'common.reporter',
    'configs.settings',
    'drivers.web',
    'orchestrator.recorder'
]

failed_imports = []
for module in modules_to_test:
    try:
        __import__(module)
        print(f'✅ {module}')
    except Exception as e:
        print(f'❌ {module}: {e}')
        failed_imports.append(module)

if failed_imports:
    print(f'❌ Failed to import: {failed_imports}')
    sys.exit(1)
else:
    print('✅ All critical modules imported successfully')
"
    
    log_success "Basic functionality tests passed"
}

# 主函数
main() {
    log_info "Starting OpenMautoTest environment setup..."
    
    # 解析参数
    BROWSER_TYPE=${1:-"all"}
    SKIP_BROWSERS=${2:-"false"}
    
    # 执行设置步骤
    check_python
    check_nodejs
    install_python_deps
    
    if [ "$SKIP_BROWSERS" != "true" ]; then
        install_browsers "$BROWSER_TYPE"
        verify_browsers
    else
        log_info "Skipping browser installation"
    fi
    
    setup_environment
    create_output_dirs
    verify_configuration
    run_basic_tests
    
    log_success "OpenMautoTest environment setup completed successfully!"
    
    # 显示使用说明
    echo ""
    log_info "Next steps:"
    echo "  1. Review and update .env file if needed"
    echo "  2. Run tests: python -m pytest"
    echo "  3. Generate reports: allure serve output/allure-results"
    echo "  4. View output: open output/index.html"
}

# 错误处理
trap 'log_error "Setup failed at line $LINENO"; exit 1' ERR

# 运行主函数
main "$@"
