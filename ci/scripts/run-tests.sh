#!/bin/bash

# OpenMautoTest 测试执行脚本
# 支持多种测试类型和参数配置

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

# 默认配置
DEFAULT_BROWSER="chromium"
DEFAULT_ENVIRONMENT="test"
DEFAULT_PARALLEL_WORKERS="4"
DEFAULT_OUTPUT_DIR="output"
DEFAULT_TEST_TAGS="smoke"

# 显示使用帮助
show_help() {
    cat << EOF
OpenMautoTest 测试执行脚本

用法: $0 [选项]

选项:
  -t, --test-type TYPE        测试类型 (web|mini|api|all) [默认: all]
  -b, --browser BROWSER       浏览器类型 (chromium|firefox|webkit) [默认: chromium]
  -e, --environment ENV       测试环境 (dev|test|staging|prod) [默认: test]
  -m, --markers MARKERS       pytest标记过滤 [默认: smoke]
  -p, --parallel WORKERS      并行worker数量 [默认: 4]
  -o, --output-dir DIR        输出目录 [默认: output]
  --headless                  使用无头模式 [默认: true]
  --no-headless               使用有头模式
  --allure                    生成Allure报告 [默认: true]
  --no-allure                 不生成Allure报告
  --coverage                  生成覆盖率报告
  --verbose                   详细输出
  --dry-run                   仅显示将要执行的命令，不实际运行
  -h, --help                  显示此帮助信息

示例:
  $0                                    # 运行所有冒烟测试
  $0 -t web -b firefox --no-headless   # 运行Web测试，使用Firefox有头模式
  $0 -t api -m regression -p 8         # 运行API回归测试，8个并行worker
  $0 --dry-run -t all                   # 显示将要执行的命令

环境变量:
  BROWSER_TYPE                浏览器类型
  ENVIRONMENT                 测试环境
  HEADLESS                    无头模式 (true/false)
  PARALLEL_WORKERS            并行worker数量
  TEST_TAGS                   测试标记
EOF
}

# 解析命令行参数
parse_arguments() {
    TEST_TYPE="all"
    BROWSER="${BROWSER_TYPE:-$DEFAULT_BROWSER}"
    ENVIRONMENT="${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}"
    MARKERS="${TEST_TAGS:-$DEFAULT_TEST_TAGS}"
    PARALLEL_WORKERS="${PARALLEL_WORKERS:-$DEFAULT_PARALLEL_WORKERS}"
    OUTPUT_DIR="$DEFAULT_OUTPUT_DIR"
    HEADLESS="${HEADLESS:-true}"
    GENERATE_ALLURE="true"
    GENERATE_COVERAGE="false"
    VERBOSE="false"
    DRY_RUN="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--test-type)
                TEST_TYPE="$2"
                shift 2
                ;;
            -b|--browser)
                BROWSER="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -m|--markers)
                MARKERS="$2"
                shift 2
                ;;
            -p|--parallel)
                PARALLEL_WORKERS="$2"
                shift 2
                ;;
            -o|--output-dir)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --headless)
                HEADLESS="true"
                shift
                ;;
            --no-headless)
                HEADLESS="false"
                shift
                ;;
            --allure)
                GENERATE_ALLURE="true"
                shift
                ;;
            --no-allure)
                GENERATE_ALLURE="false"
                shift
                ;;
            --coverage)
                GENERATE_COVERAGE="true"
                shift
                ;;
            --verbose)
                VERBOSE="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 验证参数
validate_arguments() {
    # 验证测试类型
    case $TEST_TYPE in
        web|mini|api|all)
            ;;
        *)
            log_error "无效的测试类型: $TEST_TYPE"
            exit 1
            ;;
    esac
    
    # 验证浏览器类型
    case $BROWSER in
        chromium|firefox|webkit)
            ;;
        *)
            log_error "无效的浏览器类型: $BROWSER"
            exit 1
            ;;
    esac
    
    # 验证并行worker数量
    if ! [[ "$PARALLEL_WORKERS" =~ ^[0-9]+$ ]] || [ "$PARALLEL_WORKERS" -lt 1 ]; then
        log_error "无效的并行worker数量: $PARALLEL_WORKERS"
        exit 1
    fi
    
    # 验证输出目录
    if [ ! -d "$OUTPUT_DIR" ]; then
        log_info "创建输出目录: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"/{screenshots,logs,reports,allure-results,temp}
    fi
}

# 设置环境变量
setup_environment_vars() {
    export PYTHONPATH=$(pwd)
    export PYTHONUNBUFFERED=1
    export BROWSER_TYPE="$BROWSER"
    export BROWSER_HEADLESS="$HEADLESS"
    export ENVIRONMENT="$ENVIRONMENT"
    export OUTPUT_DIR="$(pwd)/$OUTPUT_DIR"
    
    log_info "环境配置:"
    log_info "  测试类型: $TEST_TYPE"
    log_info "  浏览器: $BROWSER"
    log_info "  无头模式: $HEADLESS"
    log_info "  测试环境: $ENVIRONMENT"
    log_info "  测试标记: $MARKERS"
    log_info "  并行Workers: $PARALLEL_WORKERS"
    log_info "  输出目录: $OUTPUT_DIR"
}

# 构建pytest命令
build_pytest_command() {
    local test_path=""
    local pytest_args=""
    
    # 根据测试类型设置路径和标记
    case $TEST_TYPE in
        web)
            test_path="flows/ tests/"
            pytest_args="-m 'web_flow and $MARKERS'"
            ;;
        mini)
            test_path="flows/ tests/"
            pytest_args="-m 'mini_flow and $MARKERS'"
            ;;
        api)
            test_path="tests/api/"
            pytest_args="-m '$MARKERS'"
            ;;
        all)
            test_path="flows/ tests/"
            pytest_args="-m '$MARKERS'"
            ;;
    esac
    
    # 构建基础命令
    PYTEST_CMD="python -m pytest $test_path"
    
    # 添加参数
    if [ "$VERBOSE" = "true" ]; then
        PYTEST_CMD="$PYTEST_CMD -v"
    else
        PYTEST_CMD="$PYTEST_CMD -q"
    fi
    
    PYTEST_CMD="$PYTEST_CMD --tb=short"
    PYTEST_CMD="$PYTEST_CMD $pytest_args"
    PYTEST_CMD="$PYTEST_CMD --junitxml=$OUTPUT_DIR/test-results.xml"
    
    # 并行执行
    if [ "$PARALLEL_WORKERS" -gt 1 ]; then
        PYTEST_CMD="$PYTEST_CMD -n $PARALLEL_WORKERS"
    fi
    
    # Allure报告
    if [ "$GENERATE_ALLURE" = "true" ]; then
        PYTEST_CMD="$PYTEST_CMD --alluredir=$OUTPUT_DIR/allure-results"
    fi
    
    # 覆盖率报告
    if [ "$GENERATE_COVERAGE" = "true" ]; then
        PYTEST_CMD="$PYTEST_CMD --cov=common --cov=configs --cov=db --cov=drivers --cov=orchestrator"
        PYTEST_CMD="$PYTEST_CMD --cov-report=xml:$OUTPUT_DIR/coverage.xml"
        PYTEST_CMD="$PYTEST_CMD --cov-report=html:$OUTPUT_DIR/htmlcov"
    fi
}

# 运行测试前检查
pre_test_checks() {
    log_info "执行测试前检查..."
    
    # 检查Python环境
    if ! command -v python >/dev/null 2>&1; then
        log_error "Python未找到"
        exit 1
    fi
    
    # 检查pytest
    if ! python -c "import pytest" 2>/dev/null; then
        log_error "pytest未安装"
        exit 1
    fi
    
    # 检查配置
    if ! python -c "from configs.settings import get_settings; get_settings()" 2>/dev/null; then
        log_error "配置验证失败"
        exit 1
    fi
    
    # 检查浏览器（如果需要）
    if [[ "$TEST_TYPE" == "web" || "$TEST_TYPE" == "all" ]]; then
        if ! python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.$BROWSER.launch(); p.stop()" 2>/dev/null; then
            log_warning "浏览器 $BROWSER 可能不可用"
        fi
    fi
    
    log_success "测试前检查完成"
}

# 执行测试
run_tests() {
    log_info "开始执行测试..."
    
    # 记录开始时间
    START_TIME=$(date +%s)
    
    # 显示将要执行的命令
    log_info "执行命令: $PYTEST_CMD"
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "Dry run模式，不实际执行测试"
        return 0
    fi
    
    # 执行测试
    set +e  # 暂时禁用错误退出
    eval "$PYTEST_CMD"
    TEST_EXIT_CODE=$?
    set -e  # 重新启用错误退出
    
    # 记录结束时间
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # 显示结果
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        log_success "所有测试通过 (用时: ${DURATION}秒)"
    elif [ $TEST_EXIT_CODE -eq 1 ]; then
        log_warning "部分测试失败 (用时: ${DURATION}秒)"
    else
        log_error "测试执行出错 (用时: ${DURATION}秒)"
    fi
    
    return $TEST_EXIT_CODE
}

# 生成报告
generate_reports() {
    if [ "$DRY_RUN" = "true" ]; then
        return 0
    fi
    
    log_info "生成测试报告..."
    
    # 生成Allure报告
    if [ "$GENERATE_ALLURE" = "true" ] && command -v allure >/dev/null 2>&1; then
        if [ -d "$OUTPUT_DIR/allure-results" ] && [ "$(ls -A $OUTPUT_DIR/allure-results)" ]; then
            allure generate "$OUTPUT_DIR/allure-results" -o "$OUTPUT_DIR/allure-report" --clean
            log_success "Allure报告已生成: $OUTPUT_DIR/allure-report/index.html"
        else
            log_warning "没有找到Allure结果文件"
        fi
    fi
    
    # 生成自定义报告索引
    python -c "
from common.output_manager import get_output_manager
try:
    om = get_output_manager()
    index_file = om.generate_index_html()
    print(f'✅ 自定义报告索引已生成: {index_file}')
except Exception as e:
    print(f'⚠️ 生成自定义报告失败: {e}')
"
    
    log_success "报告生成完成"
}

# 清理和归档
cleanup_and_archive() {
    if [ "$DRY_RUN" = "true" ]; then
        return 0
    fi
    
    log_info "清理和归档..."
    
    # 清理旧文件
    python -c "
from common.output_manager import get_output_manager
try:
    om = get_output_manager()
    stats = om.cleanup_old_files(max_age_days=1)
    print(f'清理统计: {stats}')
except Exception as e:
    print(f'清理失败: {e}')
"
    
    log_success "清理完成"
}

# 显示测试摘要
show_summary() {
    if [ "$DRY_RUN" = "true" ]; then
        return 0
    fi
    
    log_info "测试摘要:"
    
    # 统计测试结果
    if [ -f "$OUTPUT_DIR/test-results.xml" ]; then
        python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('$OUTPUT_DIR/test-results.xml')
    root = tree.getroot()
    
    tests = int(root.get('tests', 0))
    failures = int(root.get('failures', 0))
    errors = int(root.get('errors', 0))
    skipped = int(root.get('skipped', 0))
    passed = tests - failures - errors - skipped
    
    print(f'  总测试数: {tests}')
    print(f'  通过: {passed}')
    print(f'  失败: {failures}')
    print(f'  错误: {errors}')
    print(f'  跳过: {skipped}')
    
    if tests > 0:
        pass_rate = (passed / tests) * 100
        print(f'  通过率: {pass_rate:.1f}%')
except Exception as e:
    print(f'无法解析测试结果: {e}')
"
    fi
    
    # 显示输出文件
    echo ""
    log_info "输出文件:"
    [ -f "$OUTPUT_DIR/test-results.xml" ] && echo "  测试结果: $OUTPUT_DIR/test-results.xml"
    [ -d "$OUTPUT_DIR/allure-report" ] && echo "  Allure报告: $OUTPUT_DIR/allure-report/index.html"
    [ -f "$OUTPUT_DIR/coverage.xml" ] && echo "  覆盖率报告: $OUTPUT_DIR/coverage.xml"
    [ -d "$OUTPUT_DIR/htmlcov" ] && echo "  HTML覆盖率: $OUTPUT_DIR/htmlcov/index.html"
    [ -f "$OUTPUT_DIR/index.html" ] && echo "  输出索引: $OUTPUT_DIR/index.html"
}

# 主函数
main() {
    log_info "OpenMautoTest 测试执行脚本启动"
    
    # 解析参数
    parse_arguments "$@"
    
    # 验证参数
    validate_arguments
    
    # 设置环境
    setup_environment_vars
    
    # 构建pytest命令
    build_pytest_command
    
    # 执行测试前检查
    pre_test_checks
    
    # 执行测试
    run_tests
    TEST_RESULT=$?
    
    # 生成报告
    generate_reports
    
    # 清理和归档
    cleanup_and_archive
    
    # 显示摘要
    show_summary
    
    # 根据测试结果退出
    if [ $TEST_RESULT -eq 0 ]; then
        log_success "测试执行完成，所有测试通过"
    elif [ $TEST_RESULT -eq 1 ]; then
        log_warning "测试执行完成，但有测试失败"
    else
        log_error "测试执行过程中出现错误"
    fi
    
    exit $TEST_RESULT
}

# 错误处理
trap 'log_error "脚本执行失败，行号: $LINENO"' ERR

# 运行主函数
main "$@"
