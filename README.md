# OpenMautoTest - 企业级跨端自动化测试框架

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/framework-pytest-orange.svg)](https://pytest.org)
[![CI/CD](https://img.shields.io/badge/ci%2Fcd-jenkins-brightgreen.svg)](https://jenkins.io)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://docker.com)
[![Allure](https://img.shields.io/badge/reports-allure-yellow.svg)](https://allurereport.org)

OpenMautoTest 是一个企业级的跨端自动化测试框架，支持 Web 端、小程序端和 API 的统一测试。框架集成了完整的 CI/CD 流水线、数据可视化监控、测试报告生成等企业级特性，为项目质量保障和效率提升提供全方位支持。

## 📊 核心价值

- **🎯 质量保障**：全面的自动化测试覆盖，确保产品质量
- **⚡ 效率提升**：自动化执行，节省大量人工测试时间
- **📈 数据驱动**：完整的测试数据记录和可视化分析
- **🔄 持续集成**：无缝集成 CI/CD 流水线，支持持续交付
- **🌐 跨端统一**：一套框架支持多端测试，降低维护成本

## 🚀 核心特性

### 🌟 跨端测试能力
- **Web 端测试**：基于 Playwright，支持 Chromium、Firefox、WebKit
- **小程序测试**：基于 Minium，支持微信小程序自动化
- **API 测试**：支持 REST API 接口测试和数据验证
- **跨浏览器兼容**：一套用例多浏览器执行

### 🔧 企业级功能
- **CI/CD 集成**：完整的 Jenkins Pipeline 支持
- **Docker 容器化**：支持容器化部署和扩展
- **数据可视化**：Metabase 集成，6 个核心质量指标监控
- **Allure 报告**：详细的测试报告和截图管理
- **参数化测试**：支持数据驱动和多场景测试

### 💾 数据持久化
- **多重存储**：支持 PostgreSQL、MySQL、文件存储
- **自动降级**：数据库不可用时自动切换到文件存储
- **数据记录**：完整的测试执行数据和性能指标
- **历史追踪**：测试结果历史趋势分析

### ⚙️ 开发友好
- **异步支持**：基于 async/await 的现代异步架构
- **统一配置**：环境变量和多环境配置管理
- **完善工具库**：时间、文件、数据、字符串处理工具
- **类型提示**：完整的 Python 类型注解支持

## 📋 系统要求

### 🐍 Python 环境
- **Python**: 3.8+ （推荐 3.12）
- **pip**: 最新版本
- **venv**: Python 虚拟环境支持

### 🌐 浏览器支持
- **Chromium/Chrome**: 最新稳定版（推荐）
- **Firefox**: 最新稳定版
- **WebKit/Safari**: 最新稳定版（macOS）

### 📱 小程序测试（可选）
- **Node.js**: 16.0+ （用于小程序工具）
- **微信开发者工具**: 最新稳定版
- **Minium**: 微信小程序自动化框架

### 🗄️ 数据存储（可选）
- **PostgreSQL**: 12+ （生产环境推荐）
- **MySQL**: 8.0+ （备选方案）
- **Redis**: 6.0+ （缓存，可选）

### 🐳 容器化（可选）
- **Docker**: 20.0+
- **Docker Compose**: 2.0+
- **Kubernetes**: 1.20+ （大规模部署）

### 🔧 CI/CD 工具（可选）
- **Jenkins**: 2.400+ （推荐）
- **GitLab CI**: 任意版本
- **GitHub Actions**: 原生支持

## 🛠️ 快速开始

### 1. 环境准备

#### 克隆项目
```bash
git clone https://github.com/your-org/OpenMautoTest.git
cd OpenMautoTest
```

#### Python 环境检查
```bash
python --version  # 确保 Python 3.9+
pip --version     # 确保 pip 可用
```

#### Node.js 环境检查（可选）
```bash
node --version    # 确保 Node.js 16.0+
npm --version     # 确保 npm 可用
```

### 2. 依赖安装

#### 安装 Python 依赖
```bash
# Windows (PowerShell)
pip install -r requirements.txt

# Linux/macOS
pip install -r requirements.txt
```

#### 安装浏览器驱动
```bash
# 安装 Playwright 浏览器
playwright install

# 或者只安装 Chromium
playwright install chromium
```

#### 安装小程序测试依赖（可选）
```bash
# 如果需要小程序测试功能
pip install minium
```

### 3. 环境配置

#### 复制环境配置文件
```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

#### 编辑环境配置
编辑 `.env` 文件，配置必要的环境变量：

```bash
# 基础配置
PROJECT_NAME=OpenMautoTest
VERSION=1.0.0
ENVIRONMENT=development

# 数据库配置（可选）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=openmautotest
DB_USER=postgres
DB_PASSWORD=your_password

# 浏览器配置
BROWSER_TYPE=chromium
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30

# 小程序配置（可选）
WECHAT_MINI_APP_ID=your_app_id
WECHAT_MINI_PROJECT_PATH=/path/to/mini/program
WECHAT_MINI_IDE_PORT=9420

# Jenkins 配置（可选）
JENKINS_URL=http://localhost:8080
JENKINS_USER=admin
JENKINS_TOKEN=your_token

# 日志配置
LOG_LEVEL=INFO
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=10
```

### 4. 数据库配置（可选）

如果使用数据库存储测试结果：

#### PostgreSQL 配置
```bash
# 创建数据库
createdb openmautotest

# 运行数据库迁移
cd db/migrations
alembic upgrade head
```

#### MySQL 配置
```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE openmautotest;"

# 更新配置文件中的数据库连接字符串
# DB_URL=mysql://user:password@localhost:3306/openmautotest
```

### 5. 验证安装

#### 运行系统检查
```bash
# Windows
.\make.ps1 check-env

# Linux/macOS
make check-env
```

#### 运行配置检查
```bash
# Windows
.\make.ps1 check-config

# Linux/macOS  
make check-config
```

#### 测试核心模块
```bash
python -c "
from configs.settings import get_settings
from common.logger import get_logger
from drivers import BaseWebDriver, BaseAPIClient
print('✅ 所有核心模块导入成功！')
print('项目名称:', get_settings().PROJECT_NAME)
"
```

## 🎯 使用方法

### 1. 参数化测试

OpenMautoTest 支持强大的参数化测试功能，可以轻松实现数据驱动测试：

#### 基础参数化
```python
import pytest
from flows.test_data.parametrized_test_config import test_data_factory

class TestLogin:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("username,password,expected", [
        ("user1", "pass1", "success"),
        ("user2", "pass2", "success"),
        ("invalid", "wrong", "failure"),
    ])
    async def test_simple_login(self, web_context, username, password, expected):
        """简单参数化登录测试"""
        web_context.test_data.update({
            "username": username,
            "password": password
        })
        # 执行测试逻辑...
```

#### 数据驱动测试
```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case",
    test_data_factory.get_login_test_cases(tags=["smoke"]),
    ids=lambda tc: tc.id
)
async def test_data_driven_login(self, web_context, test_case):
    """数据驱动登录测试"""
    web_context.test_data.update(test_case.parameters)
    # 执行测试逻辑...
```

#### 跨浏览器测试
```python
@pytest.mark.asyncio
@pytest.mark.parametrize("browser", ["chromium", "firefox", "webkit"])
@pytest.mark.parametrize("user_type", ["normal", "vip"])
async def test_cross_browser_users(self, web_context, browser, user_type):
    """跨浏览器和用户类型组合测试"""
    web_context.test_data.update({
        "browser_type": browser,
        "user_type": user_type
    })
    # 执行测试逻辑...
```

#### 外部数据源
支持从 JSON、CSV、YAML 文件加载测试数据：
```python
# 从 JSON 文件加载
test_cases = test_data_factory.loader.load_from_json("login_cases.json")

# 从 CSV 文件加载  
test_cases = test_data_factory.loader.load_from_csv("test_data.csv")

# 从 YAML 文件加载
test_cases = test_data_factory.loader.load_from_yaml("scenarios.yaml")
```

更多参数化测试示例请查看：`flows/examples/parametrized_examples.py`

### 2. 编写测试用例

#### 参数化测试

OpenMautoTest 支持多种参数化测试方式，让您可以用同一个测试逻辑验证不同的数据场景：

```python
import pytest
from flows.login_and_buy.test_parameterized_flow import TestParameterizedFlow

# 1. 基础参数化
@pytest.mark.parametrize("username,password,expected", [
    ("admin@test.com", "admin123", True),
    ("user@test.com", "user123", True),
    ("invalid@test.com", "wrong", False),
], ids=["admin-login", "user-login", "invalid-login"])
def test_login_scenarios(username, password, expected):
    # 测试逻辑
    pass

# 2. 跨浏览器测试
@pytest.mark.parametrize("browser_type,headless", [
    ("chromium", True),
    ("firefox", True),
    ("webkit", True),
], ids=["chrome", "firefox", "safari"])
async def test_cross_browser(browser_type, headless):
    # 跨浏览器测试逻辑
    pass

# 3. 数据驱动测试
from flows.login_and_buy.test_parameterized_flow import DataDrivenTestUtils

# 从JSON文件加载测试数据
test_data = DataDrivenTestUtils.load_test_data_from_json("test_data/user_data.json")

@pytest.mark.parametrize("user_data", test_data)
def test_with_external_data(user_data):
    # 使用外部数据的测试
    pass

# 4. 嵌套参数化（多维度组合测试）
@pytest.mark.parametrize("env", ["dev", "test", "prod"])
@pytest.mark.parametrize("browser", ["chrome", "firefox"])
@pytest.mark.parametrize("device", ["desktop", "mobile"])
def test_comprehensive_scenarios(env, browser, device):
    # 生成 3×2×2=12 个测试用例
    pass
```

**支持的数据源格式：**
- JSON 文件 (`test_data/user_data.json`)
- CSV 文件 (`test_data/user_data.csv`)
- Excel 文件 (需要安装 pandas)
- 数据库查询
- 动态生成

**运行参数化测试：**
```bash
# 运行所有参数化测试
python -m pytest flows/login_and_buy/test_parameterized_flow.py -v

# 运行特定参数化测试
python -m pytest -k "test_login_scenarios[admin-login]" -v

# 并行运行参数化测试
python -m pytest flows/login_and_buy/test_parameterized_flow.py -n 4
```

#### Web 端测试示例
```python
import pytest
from orchestrator.fixtures import web_context

@pytest.mark.asyncio
async def test_web_login(web_context):
    """Web端登录测试"""
    # 导航到登录页面
    await web_context.navigate_and_record(
        "https://example.com/login",
        step_name="打开登录页面"
    )
    
    # 输入用户名
    await web_context.fill_and_record(
        "#username",
        "test_user",
        step_name="输入用户名"
    )
    
    # 输入密码
    await web_context.fill_and_record(
        "#password", 
        "test_password",
        step_name="输入密码"
    )
    
    # 点击登录按钮
    await web_context.click_and_record(
        "#login-button",
        step_name="点击登录"
    )
    
    # 验证登录成功
    success_element = await web_context.driver.wait_for_element(".welcome")
    assert success_element is not None
```

#### 小程序测试示例
```python
import pytest
from orchestrator.fixtures import mini_context

def test_mini_login(mini_context):
    """小程序登录测试"""
    # 导航到登录页面
    mini_context.navigate_and_record(
        "/pages/login/login",
        step_name="打开登录页面"
    )
    
    # 输入用户名
    mini_context.input_and_record(
        ".username-input",
        "test_user", 
        step_name="输入用户名"
    )
    
    # 点击登录按钮
    mini_context.click_and_record(
        ".login-button",
        step_name="点击登录"
    )
```

#### API 测试示例
```python
import pytest
from drivers.api import BaseAPIClient

def test_api_user_info():
    """API用户信息测试"""
    with BaseAPIClient("https://api.example.com") as client:
        # 设置认证
        client.set_auth_token("your_token")
        
        # 获取用户信息
        response = client.get("/api/user/profile")
        assert response.status_code == 200
        
        user_data = response.json()
        assert "username" in user_data
        assert "email" in user_data
```

### 2. 运行测试

#### 运行所有测试
```bash
# Windows
.\make.ps1 test

# Linux/macOS
make test
```

#### 运行指定测试
```bash
# 运行 Web 端测试
pytest tests/web/ -v

# 运行小程序测试
pytest tests/mini/ -v

# 运行 API 测试
pytest tests/api/ -v

# 运行指定测试文件
pytest tests/web/test_login.py -v
```

#### 并行运行测试
```bash
# 使用 4 个进程并行运行
pytest -n 4 tests/

# 自动检测 CPU 核心数
pytest -n auto tests/
```

### 3. 查看测试报告

#### Allure 报告
```bash
# 生成 Allure 报告
allure generate output/allure-results -o output/allure-report

# 启动报告服务
allure serve output/allure-results
```

#### 查看输出文件
- **截图**: `output/screenshots/`
- **日志**: `output/logs/`
- **测试记录**: `output/records/`
- **视频**: `output/videos/` (如果启用)

## 🐳 Docker 部署

### 1. 构建镜像
```bash
# 构建测试镜像
docker build -t openmautotest:latest .

# 构建带 GUI 支持的镜像
docker build -f ci/docker/Dockerfile -t openmautotest:gui .
```

### 2. 运行容器
```bash
# 运行测试容器
docker run --rm \
  -v $(pwd)/output:/app/output \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  openmautotest:latest

# 运行带 GUI 的容器（需要 X11 支持）
docker run --rm \
  -v $(pwd)/output:/app/output \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  openmautotest:gui
```

### 3. Docker Compose 部署
```bash
# 启动完整服务栈
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f openmautotest
```

## 🔧 Jenkins 集成

### 1. Jenkins Pipeline 配置

创建 `Jenkinsfile`：
```groovy
pipeline {
    agent any
    
    environment {
        PYTHONPATH = "${WORKSPACE}"
        DATABASE_URL = credentials('database-url')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'playwright install chromium'
            }
        }
        
        stage('Test') {
            steps {
                sh 'pytest tests/ --allure-results-directory=output/allure-results'
            }
        }
        
        stage('Report') {
            steps {
                allure([
                    includeProperties: false,
                    jdk: '',
                    properties: [],
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: 'output/allure-results']]
                ])
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'output/**/*', fingerprint: true
            cleanWs()
        }
    }
}
```

### 2. 定时任务配置
```bash
# 每日凌晨 2 点运行
H 2 * * *

# 每小时运行一次
H * * * *

# 工作日每 4 小时运行一次
H */4 * * 1-5
```

## 📊 Metabase 集成

### 1. 启动 Metabase
```bash
# 使用 Docker 启动
docker-compose -f docker-compose.meta.yml up -d

# 访问 Metabase
# http://localhost:3000
```

### 2. 配置数据源
- 数据库类型: PostgreSQL
- 主机: localhost
- 端口: 5432
- 数据库名: openmautotest
- 用户名/密码: 根据配置填写

### 3. 导入仪表盘
```bash
# 导入预配置的仪表盘
curl -X POST http://localhost:3000/api/dashboard \
  -H "Content-Type: application/json" \
  -d @metabase/init/automationOS_dashboard.json
```

## 🔍 故障排除

### 常见问题

#### 1. 浏览器启动失败
```bash
# 解决方案：重新安装浏览器
playwright install chromium --force

# 或者更新 Playwright
pip install playwright --upgrade
```

#### 2. 数据库连接失败
```bash
# 检查数据库服务状态
systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# 检查连接配置
python -c "from configs.db import check_db_config; check_db_config()"
```

#### 3. 小程序测试失败
```bash
# 检查微信开发者工具是否启动
# 检查端口 9420 是否被占用
netstat -an | grep 9420

# 重新安装 minium
pip uninstall minium
pip install minium
```

#### 4. 权限问题
```bash
# Linux/macOS: 给脚本执行权限
chmod +x make.sh

# Windows: 启用 PowerShell 脚本执行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 日志查看
```bash
# 查看应用日志
tail -f output/logs/openmautotest.log

# 查看特定模块日志
grep "web_driver" output/logs/openmautotest.log

# 查看错误日志
grep "ERROR" output/logs/openmautotest.log
```

### 性能监控
```bash
# 查看系统资源使用
htop  # Linux/macOS
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10  # Windows

# 查看测试执行统计
python -c "
from orchestrator.recorder import get_recorder
recorder = get_recorder()
metrics = recorder.get_performance_metrics()
print('性能指标:', metrics)
"
```

## 🏢 企业级部署

### Docker 容器化部署
```bash
# 构建并启动所有服务
docker-compose up -d

# 仅启动核心测试服务
docker-compose up -d openmautotest postgres redis

# 启动完整监控栈
docker-compose -f docker-compose.meta.yml up -d
```

### Kubernetes 部署
```bash
# 部署到 Kubernetes 集群
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n openmautotest

# 查看服务访问地址
kubectl get services -n openmautotest
```

### CI/CD 集成
```yaml
# Jenkins Pipeline 示例
pipeline {
  agent any
  stages {
    stage('Test') {
      steps {
        sh './ci/scripts/run-tests.sh -t web -b chromium'
      }
    }
    stage('Deploy') {
      steps {
        sh './ci/scripts/deploy.sh docker-deploy -e production'
      }
    }
  }
}
```

## 📊 监控与分析

### 核心质量指标
- **历史自动化执行总数**：测试执行趋势监控
- **测试用例数量趋势**：用例规模增长分析
- **测试成功率分布**：质量稳定性评估
- **单次任务总耗时**：性能效率监控
- **节省人时累计**：ROI 投资回报分析
- **失败用例 TOP10**：问题热点识别

### 实时监控面板
```bash
# 访问 Metabase 监控面板
http://localhost:3000

# 访问 Allure 测试报告
http://localhost:5050

# 访问应用健康检查
http://localhost:8080/health
```

### 数据分析 API
```python
from orchestrator.recorder import get_recorder

# 获取测试统计数据
recorder = get_recorder()
stats = recorder.get_test_statistics(days=30)

# 获取性能指标
metrics = recorder.get_performance_metrics()

# 获取失败用例分析
failures = recorder.get_failure_analysis()
```

## 📚 开发文档

- [需求文档](docs/需求文档.md) - 项目需求和功能说明
- [架构文档](docs/项目架构文档.md) - 系统架构设计
- [开发阶段指导](docs/DEVELOPMENT_PHASES1.md) - 开发阶段规划
- [CI/CD 部署指南](ci/README.md) - 持续集成部署文档
- [Metabase 监控指南](metabase/readme.md) - 数据可视化配置
- [参数化测试指南](flows/examples/parametrized_examples.py) - 数据驱动测试
- [代码规范](docs/代码规范文档.md) - 编码标准和最佳实践
- [开发日志](docs/程序开发日志/程序开发日志.md) - 开发过程记录

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📚 相关文档

- **[服务部署说明](docs/服务部署说明.md)** - 详细的生产环境部署指南
- **[开发指南](docs/DEVELOPMENT_PHASES2.md)** - 项目开发阶段说明
- **[API文档](docs/api/)** - 接口文档
- **[故障排除](docs/troubleshooting.md)** - 常见问题解决方案

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙋‍♂️ 支持与反馈

- **问题报告**: [GitHub Issues](https://github.com/your-org/OpenMautoTest/issues)
- **功能请求**: [GitHub Discussions](https://github.com/your-org/OpenMautoTest/discussions)
- **邮件联系**: support@openmautotest.com

---

<div align="center">
  <p>Made with ❤️ by OpenMautoTest Team</p>
  <p>
    <a href="#top">回到顶部</a> •
    <a href="docs/">文档</a> •
    <a href="https://github.com/your-org/OpenMautoTest/releases">发布</a>
  </p>
</div>