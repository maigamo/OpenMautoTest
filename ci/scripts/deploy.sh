#!/bin/bash

# OpenMautoTest 部署脚本
# 支持多环境部署和容器化部署

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
DEFAULT_ENVIRONMENT="test"
DEFAULT_REGISTRY="localhost:5000"
DEFAULT_IMAGE_NAME="openmautotest"
DEFAULT_TAG="latest"

# 显示使用帮助
show_help() {
    cat << EOF
OpenMautoTest 部署脚本

用法: $0 [选项] <部署类型>

部署类型:
  docker-build         构建Docker镜像
  docker-push          推送Docker镜像到Registry
  docker-deploy        部署Docker容器
  k8s-deploy           部署到Kubernetes
  local-deploy         本地部署
  metabase-deploy      部署Metabase服务

选项:
  -e, --environment ENV    部署环境 (dev|test|staging|prod) [默认: test]
  -r, --registry URL       Docker Registry地址 [默认: localhost:5000]
  -i, --image NAME         镜像名称 [默认: openmautotest]
  -t, --tag TAG           镜像标签 [默认: latest]
  -n, --namespace NS       Kubernetes命名空间
  --no-cache              Docker构建时不使用缓存
  --force                 强制部署（覆盖现有部署）
  --dry-run               仅显示将要执行的命令
  -h, --help              显示此帮助信息

示例:
  $0 docker-build                           # 构建Docker镜像
  $0 docker-deploy -e staging               # 部署到staging环境
  $0 k8s-deploy -n openmautotest-prod       # 部署到Kubernetes
  $0 metabase-deploy                         # 部署Metabase服务

环境变量:
  DOCKER_REGISTRY         Docker Registry地址
  ENVIRONMENT             部署环境
  IMAGE_NAME              镜像名称
  IMAGE_TAG               镜像标签
EOF
}

# 解析命令行参数
parse_arguments() {
    ENVIRONMENT="${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}"
    REGISTRY="${DOCKER_REGISTRY:-$DEFAULT_REGISTRY}"
    IMAGE_NAME="${IMAGE_NAME:-$DEFAULT_IMAGE_NAME}"
    TAG="${IMAGE_TAG:-$DEFAULT_TAG}"
    NAMESPACE=""
    NO_CACHE="false"
    FORCE="false"
    DRY_RUN="false"
    DEPLOY_TYPE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -i|--image)
                IMAGE_NAME="$2"
                shift 2
                ;;
            -t|--tag)
                TAG="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --no-cache)
                NO_CACHE="true"
                shift
                ;;
            --force)
                FORCE="true"
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
            docker-build|docker-push|docker-deploy|k8s-deploy|local-deploy|metabase-deploy)
                DEPLOY_TYPE="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    if [ -z "$DEPLOY_TYPE" ]; then
        log_error "请指定部署类型"
        show_help
        exit 1
    fi
}

# 验证环境
validate_environment() {
    case $ENVIRONMENT in
        dev|test|staging|prod)
            ;;
        *)
            log_error "无效的环境: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    # 生产环境额外确认
    if [ "$ENVIRONMENT" = "prod" ] && [ "$FORCE" != "true" ]; then
        echo -n "确认要部署到生产环境吗? (yes/no): "
        read -r confirmation
        if [ "$confirmation" != "yes" ]; then
            log_info "部署已取消"
            exit 0
        fi
    fi
}

# 执行命令（支持dry-run）
execute_command() {
    local cmd="$1"
    
    log_info "执行: $cmd"
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "Dry run模式，不实际执行"
        return 0
    fi
    
    eval "$cmd"
}

# 构建Docker镜像
docker_build() {
    log_info "构建Docker镜像..."
    
    local build_args=""
    if [ "$NO_CACHE" = "true" ]; then
        build_args="--no-cache"
    fi
    
    # 构建镜像
    local full_image_name="$REGISTRY/$IMAGE_NAME:$TAG"
    local build_cmd="docker build $build_args -t $full_image_name -f ci/docker/Dockerfile ."
    
    execute_command "$build_cmd"
    
    # 添加环境标签
    if [ "$ENVIRONMENT" != "test" ]; then
        local env_tag="$REGISTRY/$IMAGE_NAME:$ENVIRONMENT-$TAG"
        execute_command "docker tag $full_image_name $env_tag"
    fi
    
    log_success "Docker镜像构建完成: $full_image_name"
}

# 推送Docker镜像
docker_push() {
    log_info "推送Docker镜像到Registry..."
    
    local full_image_name="$REGISTRY/$IMAGE_NAME:$TAG"
    
    # 推送主标签
    execute_command "docker push $full_image_name"
    
    # 推送环境标签
    if [ "$ENVIRONMENT" != "test" ]; then
        local env_tag="$REGISTRY/$IMAGE_NAME:$ENVIRONMENT-$TAG"
        execute_command "docker push $env_tag"
    fi
    
    log_success "Docker镜像推送完成"
}

# 部署Docker容器
docker_deploy() {
    log_info "部署Docker容器..."
    
    local container_name="openmautotest-$ENVIRONMENT"
    local full_image_name="$REGISTRY/$IMAGE_NAME:$TAG"
    
    # 停止现有容器
    if docker ps -q -f name="$container_name" | grep -q .; then
        log_info "停止现有容器: $container_name"
        execute_command "docker stop $container_name"
        execute_command "docker rm $container_name"
    fi
    
    # 创建数据目录
    local data_dir="$HOME/openmautotest-data/$ENVIRONMENT"
    execute_command "mkdir -p $data_dir/{output,config}"
    
    # 启动新容器
    local run_cmd="docker run -d \
        --name $container_name \
        --restart unless-stopped \
        -p 8080:8080 \
        -v $data_dir/output:/app/output \
        -v $data_dir/config:/app/config \
        -e ENVIRONMENT=$ENVIRONMENT \
        -e PYTHONUNBUFFERED=1 \
        $full_image_name"
    
    execute_command "$run_cmd"
    
    # 等待容器启动
    if [ "$DRY_RUN" != "true" ]; then
        log_info "等待容器启动..."
        sleep 5
        
        # 检查容器状态
        if docker ps -f name="$container_name" --format "table {{.Names}}\t{{.Status}}" | grep -q "Up"; then
            log_success "容器启动成功: $container_name"
        else
            log_error "容器启动失败"
            execute_command "docker logs $container_name"
            exit 1
        fi
    fi
}

# 部署到Kubernetes
k8s_deploy() {
    log_info "部署到Kubernetes..."
    
    if [ -z "$NAMESPACE" ]; then
        NAMESPACE="openmautotest-$ENVIRONMENT"
    fi
    
    # 检查kubectl
    if ! command -v kubectl >/dev/null 2>&1; then
        log_error "kubectl未找到"
        exit 1
    fi
    
    # 创建命名空间
    execute_command "kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
    
    # 生成Kubernetes配置
    generate_k8s_config
    
    # 应用配置
    execute_command "kubectl apply -f k8s-config.yaml -n $NAMESPACE"
    
    # 等待部署完成
    if [ "$DRY_RUN" != "true" ]; then
        log_info "等待部署完成..."
        kubectl rollout status deployment/openmautotest -n "$NAMESPACE" --timeout=300s
        log_success "Kubernetes部署完成"
    fi
}

# 生成Kubernetes配置
generate_k8s_config() {
    local full_image_name="$REGISTRY/$IMAGE_NAME:$TAG"
    
    cat > k8s-config.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openmautotest
  labels:
    app: openmautotest
    environment: $ENVIRONMENT
spec:
  replicas: 1
  selector:
    matchLabels:
      app: openmautotest
  template:
    metadata:
      labels:
        app: openmautotest
        environment: $ENVIRONMENT
    spec:
      containers:
      - name: openmautotest
        image: $full_image_name
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "$ENVIRONMENT"
        - name: PYTHONUNBUFFERED
          value: "1"
        volumeMounts:
        - name: output-volume
          mountPath: /app/output
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: output-volume
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: openmautotest-service
spec:
  selector:
    app: openmautotest
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: openmautotest-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
  - host: openmautotest-$ENVIRONMENT.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: openmautotest-service
            port:
              number: 80
EOF
    
    log_info "Kubernetes配置已生成: k8s-config.yaml"
}

# 本地部署
local_deploy() {
    log_info "执行本地部署..."
    
    # 创建部署目录
    local deploy_dir="$HOME/openmautotest-$ENVIRONMENT"
    execute_command "mkdir -p $deploy_dir"
    
    # 复制文件
    execute_command "cp -r . $deploy_dir/"
    
    # 安装依赖
    execute_command "cd $deploy_dir && pip install -r requirements.txt"
    
    # 安装浏览器
    execute_command "cd $deploy_dir && playwright install"
    
    # 创建systemd服务文件（Linux）
    if command -v systemctl >/dev/null 2>&1; then
        create_systemd_service "$deploy_dir"
    fi
    
    log_success "本地部署完成: $deploy_dir"
}

# 创建systemd服务
create_systemd_service() {
    local deploy_dir="$1"
    local service_name="openmautotest-$ENVIRONMENT"
    
    cat > "$service_name.service" << EOF
[Unit]
Description=OpenMautoTest $ENVIRONMENT
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$deploy_dir
Environment=PYTHONPATH=$deploy_dir
Environment=ENVIRONMENT=$ENVIRONMENT
ExecStart=$deploy_dir/venv/bin/python -m pytest --version
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    log_info "systemd服务文件已创建: $service_name.service"
    log_info "要安装服务，请运行: sudo cp $service_name.service /etc/systemd/system/ && sudo systemctl enable $service_name"
}

# 部署Metabase
metabase_deploy() {
    log_info "部署Metabase服务..."
    
    # 检查docker-compose
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "docker-compose未找到"
        exit 1
    fi
    
    # 启动Metabase
    execute_command "docker-compose -f docker-compose.meta.yml up -d"
    
    if [ "$DRY_RUN" != "true" ]; then
        log_info "等待Metabase启动..."
        sleep 10
        
        # 检查服务状态
        if docker-compose -f docker-compose.meta.yml ps | grep -q "Up"; then
            log_success "Metabase服务启动成功"
            log_info "访问地址: http://localhost:3000"
        else
            log_error "Metabase服务启动失败"
            execute_command "docker-compose -f docker-compose.meta.yml logs"
            exit 1
        fi
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    case $DEPLOY_TYPE in
        docker-deploy)
            local container_name="openmautotest-$ENVIRONMENT"
            if docker ps -f name="$container_name" --format "{{.Status}}" | grep -q "Up"; then
                log_success "Docker容器运行正常"
            else
                log_error "Docker容器状态异常"
                return 1
            fi
            ;;
        k8s-deploy)
            if [ -n "$NAMESPACE" ]; then
                if kubectl get deployment openmautotest -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' | grep -q "1"; then
                    log_success "Kubernetes部署运行正常"
                else
                    log_error "Kubernetes部署状态异常"
                    return 1
                fi
            fi
            ;;
        metabase-deploy)
            if curl -s http://localhost:3000/api/health | grep -q "ok"; then
                log_success "Metabase服务运行正常"
            else
                log_warning "Metabase服务可能需要更多时间启动"
            fi
            ;;
    esac
}

# 显示部署信息
show_deployment_info() {
    log_info "部署信息:"
    log_info "  环境: $ENVIRONMENT"
    log_info "  镜像: $REGISTRY/$IMAGE_NAME:$TAG"
    log_info "  部署类型: $DEPLOY_TYPE"
    
    case $DEPLOY_TYPE in
        docker-deploy)
            log_info "  容器名称: openmautotest-$ENVIRONMENT"
            log_info "  访问端口: 8080"
            ;;
        k8s-deploy)
            log_info "  命名空间: ${NAMESPACE:-openmautotest-$ENVIRONMENT}"
            log_info "  服务名称: openmautotest-service"
            ;;
        metabase-deploy)
            log_info "  访问地址: http://localhost:3000"
            ;;
    esac
}

# 主函数
main() {
    log_info "OpenMautoTest 部署脚本启动"
    
    # 解析参数
    parse_arguments "$@"
    
    # 验证环境
    validate_environment
    
    # 显示配置
    show_deployment_info
    
    # 执行部署
    case $DEPLOY_TYPE in
        docker-build)
            docker_build
            ;;
        docker-push)
            docker_push
            ;;
        docker-deploy)
            docker_build
            docker_deploy
            ;;
        k8s-deploy)
            docker_build
            docker_push
            k8s_deploy
            ;;
        local-deploy)
            local_deploy
            ;;
        metabase-deploy)
            metabase_deploy
            ;;
        *)
            log_error "未知的部署类型: $DEPLOY_TYPE"
            exit 1
            ;;
    esac
    
    # 健康检查
    if [ "$DRY_RUN" != "true" ]; then
        sleep 5
        health_check
    fi
    
    log_success "部署完成!"
}

# 错误处理
trap 'log_error "部署失败，行号: $LINENO"' ERR

# 运行主函数
main "$@"
