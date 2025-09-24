# OpenMautoTest CI/CD 文档

本目录包含OpenMautoTest项目的持续集成和持续部署(CI/CD)配置文件和脚本。

## 目录结构

```
ci/
├── Jenkinsfile                 # Jenkins Pipeline配置
├── docker/                    # Docker相关配置
│   ├── Dockerfile             # 主应用Docker镜像
│   ├── docker-compose.yml     # Docker Compose配置
│   └── nginx/                 # Nginx反向代理配置
│       ├── nginx.conf
│       └── conf.d/
│           └── default.conf
├── scripts/                   # CI/CD脚本
│   ├── setup-env.sh          # 环境设置脚本
│   ├── run-tests.sh          # 测试执行脚本
│   └── deploy.sh             # 部署脚本
└── README.md                 # 本文档
```

## 快速开始

### 1. 使用Docker Compose部署

```bash
# 进入Docker目录
cd ci/docker

# 复制环境配置文件
cp .env.example .env
# 编辑.env文件，修改必要的配置

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f openmautotest
```

### 2. 使用脚本部署

```bash
# 设置环境
./ci/scripts/setup-env.sh

# 运行测试
./ci/scripts/run-tests.sh -t web -b chromium

# 部署应用
./ci/scripts/deploy.sh docker-deploy -e test
```

### 3. Jenkins Pipeline

1. 在Jenkins中创建新的Pipeline项目
2. 配置Git仓库地址
3. Pipeline脚本选择"Pipeline script from SCM"
4. Script Path设置为"ci/Jenkinsfile"
5. 配置必要的凭据(credentials)

## 配置说明

### 环境变量

主要环境变量说明：

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| ENVIRONMENT | 部署环境 | test |
| BROWSER_TYPE | 浏览器类型 | chromium |
| BROWSER_HEADLESS | 无头模式 | true |
| PARALLEL_WORKERS | 并行Worker数 | 4 |
| DATABASE_URL | 数据库连接URL | - |

### Docker服务

Docker Compose包含以下服务：

- **openmautotest**: 主应用服务
- **postgres**: PostgreSQL数据库
- **redis**: Redis缓存
- **nginx**: 反向代理
- **allure**: Allure报告服务(可选)
- **jenkins**: Jenkins CI/CD服务(可选)
- **portainer**: 容器管理界面(可选)

### 端口映射

| 服务 | 端口 | 描述 |
|------|------|------|
| nginx | 80, 443 | Web入口 |
| openmautotest | 8080 | 应用服务 |
| postgres | 5432 | 数据库 |
| redis | 6379 | 缓存 |
| allure | 5050 | 报告服务 |
| jenkins | 8081 | CI/CD服务 |
| portainer | 9000 | 容器管理 |

## 脚本使用说明

### setup-env.sh

环境设置脚本，用于初始化开发和CI环境。

```bash
# 基本使用
./ci/scripts/setup-env.sh

# 指定浏览器类型
./ci/scripts/setup-env.sh chromium

# 跳过浏览器安装
./ci/scripts/setup-env.sh all true
```

### run-tests.sh

测试执行脚本，支持多种测试类型和配置。

```bash
# 运行所有测试
./ci/scripts/run-tests.sh

# 运行Web测试
./ci/scripts/run-tests.sh -t web -b firefox --no-headless

# 运行回归测试
./ci/scripts/run-tests.sh -m regression -p 8

# 生成覆盖率报告
./ci/scripts/run-tests.sh --coverage

# 仅显示命令(不执行)
./ci/scripts/run-tests.sh --dry-run -t all
```

### deploy.sh

部署脚本，支持多种部署方式。

```bash
# Docker部署
./ci/scripts/deploy.sh docker-deploy -e test

# Kubernetes部署
./ci/scripts/deploy.sh k8s-deploy -n openmautotest-prod

# 本地部署
./ci/scripts/deploy.sh local-deploy

# 部署Metabase
./ci/scripts/deploy.sh metabase-deploy
```

## Jenkins Pipeline详解

### Pipeline阶段

1. **Checkout**: 检出代码
2. **Environment Setup**: 环境设置
   - Python环境
   - 浏览器环境
   - 目录设置
3. **Configuration Check**: 配置检查
4. **Static Code Analysis**: 静态代码分析
   - Flake8代码检查
   - MyPy类型检查
5. **Unit Tests**: 单元测试
6. **Integration Tests**: 集成测试
   - Web测试
   - 小程序测试
   - API测试
7. **Generate Reports**: 生成报告
8. **Cleanup & Archive**: 清理和归档

### Pipeline参数

- **ENVIRONMENT**: 测试环境选择
- **BROWSER**: 浏览器类型选择
- **HEADLESS**: 是否使用无头模式
- **RUN_WEB_TESTS**: 是否运行Web测试
- **RUN_MINI_TESTS**: 是否运行小程序测试
- **RUN_API_TESTS**: 是否运行API测试
- **TEST_TAGS**: 测试标签过滤
- **PARALLEL_WORKERS**: 并行Worker数量

### 凭据配置

在Jenkins中配置以下凭据：

- **database-url**: 数据库连接URL
- **docker-registry-credentials**: Docker Registry认证
- **git-credentials**: Git仓库访问凭据

## 监控和日志

### 服务访问地址

部署完成后，可以通过以下地址访问各个服务：

- 应用主页: http://localhost/app/
- 测试输出: http://localhost/output/
- Allure报告: http://localhost/allure/
- Jenkins: http://localhost:8081/
- Portainer: http://localhost:9000/

### 日志查看

```bash
# 查看应用日志
docker-compose logs -f openmautotest

# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs postgres
```

### 健康检查

```bash
# 检查服务状态
docker-compose ps

# 检查应用健康状态
curl http://localhost/health

# 检查数据库连接
docker-compose exec postgres pg_isready
```

## 故障排除

### 常见问题

1. **容器启动失败**
   - 检查端口是否被占用
   - 检查Docker资源限制
   - 查看容器日志

2. **测试执行失败**
   - 检查浏览器安装
   - 检查网络连接
   - 查看测试日志

3. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 检查网络配置

### 调试命令

```bash
# 进入应用容器
docker-compose exec openmautotest bash

# 进入数据库容器
docker-compose exec postgres psql -U postgres -d openmautotest

# 重启服务
docker-compose restart openmautotest

# 重新构建镜像
docker-compose build --no-cache openmautotest
```

## 性能优化

### Docker优化

1. 使用多阶段构建减小镜像大小
2. 合理设置资源限制
3. 使用Docker层缓存
4. 优化Dockerfile指令顺序

### 测试优化

1. 合理设置并行Worker数量
2. 使用测试标签过滤
3. 启用浏览器缓存
4. 优化等待策略

### CI/CD优化

1. 使用Pipeline缓存
2. 并行执行测试阶段
3. 增量构建和部署
4. 合理的资源分配

## 安全考虑

1. **凭据管理**: 使用Jenkins凭据管理敏感信息
2. **网络安全**: 配置防火墙和网络隔离
3. **镜像安全**: 定期更新基础镜像
4. **访问控制**: 配置RBAC权限控制

## 维护指南

### 定期维护任务

1. 更新依赖包版本
2. 清理旧的测试产物
3. 备份重要数据
4. 监控资源使用情况

### 升级流程

1. 在测试环境验证新版本
2. 备份现有配置和数据
3. 执行滚动更新
4. 验证升级结果

## 支持和反馈

如有问题或建议，请：

1. 查看项目文档
2. 检查已知问题列表
3. 提交Issue或Pull Request
4. 联系开发团队

---

更多详细信息请参考项目主文档和API文档。
