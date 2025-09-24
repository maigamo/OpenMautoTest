#!/bin/bash

# OpenMautoTest Metabase 自动化设置脚本
# 自动配置数据源和仪表盘

set -e

# 配置变量
METABASE_URL="http://localhost:3000"
ADMIN_EMAIL="${MB_ADMIN_EMAIL:-admin@openmautotest.com}"
ADMIN_PASSWORD="${MB_ADMIN_PASSWORD:-admin123}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-openmautotest}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 等待Metabase启动
wait_for_metabase() {
    log_info "等待Metabase启动..."
    
    for i in {1..60}; do
        if curl -s "${METABASE_URL}/api/health" > /dev/null 2>&1; then
            log_success "Metabase已启动"
            return 0
        fi
        
        log_info "等待中... ($i/60)"
        sleep 5
    done
    
    log_error "Metabase启动超时"
    return 1
}

# 设置管理员账户
setup_admin() {
    log_info "设置管理员账户..."
    
    # 检查是否已经设置过
    if curl -s "${METABASE_URL}/api/session/properties" | grep -q '"has-user-setup":true'; then
        log_info "管理员账户已存在，跳过设置"
        return 0
    fi
    
    # 创建管理员账户
    local setup_token=$(curl -s "${METABASE_URL}/api/session/properties" | grep -o '"setup-token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$setup_token" ]; then
        log_error "无法获取setup token"
        return 1
    fi
    
    curl -s -X POST "${METABASE_URL}/api/setup" \
        -H "Content-Type: application/json" \
        -d "{
            \"token\": \"${setup_token}\",
            \"user\": {
                \"first_name\": \"OpenMautoTest\",
                \"last_name\": \"Admin\",
                \"email\": \"${ADMIN_EMAIL}\",
                \"password\": \"${ADMIN_PASSWORD}\"
            },
            \"prefs\": {
                \"site_name\": \"OpenMautoTest Analytics\",
                \"allow_tracking\": false
            }
        }" > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "管理员账户设置完成"
    else
        log_error "管理员账户设置失败"
        return 1
    fi
}

# 获取会话token
get_session_token() {
    local response=$(curl -s -X POST "${METABASE_URL}/api/session" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"${ADMIN_EMAIL}\",
            \"password\": \"${ADMIN_PASSWORD}\"
        }")
    
    echo "$response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4
}

# 配置数据库连接
setup_database() {
    log_info "配置数据库连接..."
    
    local session_token=$(get_session_token)
    if [ -z "$session_token" ]; then
        log_error "无法获取会话token"
        return 1
    fi
    
    # 检查数据库连接是否已存在
    local existing_db=$(curl -s -H "X-Metabase-Session: ${session_token}" \
        "${METABASE_URL}/api/database" | grep -o '"name":"OpenMautoTest"')
    
    if [ -n "$existing_db" ]; then
        log_info "数据库连接已存在，跳过配置"
        return 0
    fi
    
    # 创建数据库连接
    curl -s -X POST "${METABASE_URL}/api/database" \
        -H "Content-Type: application/json" \
        -H "X-Metabase-Session: ${session_token}" \
        -d "{
            \"engine\": \"postgres\",
            \"name\": \"OpenMautoTest\",
            \"details\": {
                \"host\": \"${DB_HOST}\",
                \"port\": ${DB_PORT},
                \"dbname\": \"${DB_NAME}\",
                \"user\": \"${DB_USER}\",
                \"password\": \"${DB_PASSWORD}\",
                \"ssl\": false,
                \"additional-options\": \"\"
            },
            \"auto_run_queries\": true,
            \"is_full_sync\": true,
            \"schedules\": {
                \"metadata_sync\": {
                    \"schedule_day\": null,
                    \"schedule_frame\": null,
                    \"schedule_hour\": 0,
                    \"schedule_type\": \"hourly\"
                },
                \"cache_field_values\": {
                    \"schedule_day\": null,
                    \"schedule_frame\": null,
                    \"schedule_hour\": 0,
                    \"schedule_type\": \"hourly\"
                }
            }
        }" > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "数据库连接配置完成"
        
        # 等待数据库同步
        log_info "等待数据库同步..."
        sleep 10
    else
        log_error "数据库连接配置失败"
        return 1
    fi
}

# 创建SQL查询
create_queries() {
    log_info "创建SQL查询..."
    
    local session_token=$(get_session_token)
    if [ -z "$session_token" ]; then
        log_error "无法获取会话token"
        return 1
    fi
    
    # 获取数据库ID
    local database_id=$(curl -s -H "X-Metabase-Session: ${session_token}" \
        "${METABASE_URL}/api/database" | grep -A 10 '"name":"OpenMautoTest"' | grep -o '"id":[0-9]*' | cut -d':' -f2)
    
    if [ -z "$database_id" ]; then
        log_error "无法获取数据库ID"
        return 1
    fi
    
    # 创建查询
    local queries=(
        "daily_trend:历史自动化执行总数"
        "pass_rate:测试用例数趋势"
        "avg_duration:测试用例成功率"
        "task_duration:单次任务总耗时"
        "saved_time:节省人时累计"
        "failed_cases_top10:失败用例TOP10"
    )
    
    for query_info in "${queries[@]}"; do
        local query_file=$(echo "$query_info" | cut -d':' -f1)
        local query_name=$(echo "$query_info" | cut -d':' -f2)
        local sql_file="/app/sql/${query_file}.sql"
        
        if [ -f "$sql_file" ]; then
            local sql_content=$(cat "$sql_file")
            
            curl -s -X POST "${METABASE_URL}/api/card" \
                -H "Content-Type: application/json" \
                -H "X-Metabase-Session: ${session_token}" \
                -d "{
                    \"name\": \"${query_name}\",
                    \"dataset_query\": {
                        \"type\": \"native\",
                        \"native\": {
                            \"query\": $(echo "$sql_content" | jq -R -s .)
                        },
                        \"database\": ${database_id}
                    },
                    \"display\": \"table\",
                    \"visualization_settings\": {}
                }" > /dev/null
            
            log_info "创建查询: ${query_name}"
        else
            log_warning "SQL文件不存在: ${sql_file}"
        fi
    done
    
    log_success "SQL查询创建完成"
}

# 导入仪表盘
import_dashboard() {
    log_info "导入仪表盘..."
    
    local session_token=$(get_session_token)
    if [ -z "$session_token" ]; then
        log_error "无法获取会话token"
        return 1
    fi
    
    local dashboard_file="/app/init/automationOS_dashboard.json"
    if [ -f "$dashboard_file" ]; then
        # 这里需要根据实际的Metabase API来调整
        log_info "仪表盘文件存在，需要手动导入或通过API导入"
        log_info "仪表盘文件路径: ${dashboard_file}"
    else
        log_warning "仪表盘文件不存在: ${dashboard_file}"
    fi
}

# 主函数
main() {
    log_info "开始设置OpenMautoTest Metabase..."
    
    # 等待Metabase启动
    if ! wait_for_metabase; then
        exit 1
    fi
    
    # 设置管理员账户
    if ! setup_admin; then
        exit 1
    fi
    
    # 等待一下让设置生效
    sleep 5
    
    # 配置数据库连接
    if ! setup_database; then
        exit 1
    fi
    
    # 创建SQL查询
    if ! create_queries; then
        exit 1
    fi
    
    # 导入仪表盘
    import_dashboard
    
    log_success "OpenMautoTest Metabase设置完成!"
    log_info "访问地址: ${METABASE_URL}"
    log_info "管理员邮箱: ${ADMIN_EMAIL}"
    log_info "管理员密码: ${ADMIN_PASSWORD}"
}

# 运行主函数
main "$@"
