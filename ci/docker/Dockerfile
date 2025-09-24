# OpenMautoTest Docker镜像
# 基于Ubuntu 22.04构建，包含Python、Node.js和浏览器环境

FROM ubuntu:22.04

# 设置非交互模式
ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

# 标签信息
LABEL maintainer="OpenMautoTest Team <team@openmautotest.com>"
LABEL description="OpenMautoTest - 跨端自动化测试框架容器镜像"
LABEL version="1.0.0"

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    git \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release \
    # Python相关
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    # Node.js相关 (通过NodeSource安装最新LTS)
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    # 浏览器依赖
    && apt-get install -y \
        libnss3 \
        libnspr4 \
        libatk-bridge2.0-0 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libxss1 \
        libasound2 \
        libatspi2.0-0 \
        libgtk-3-0 \
    # 字体支持
    && apt-get install -y \
        fonts-liberation \
        fonts-noto-color-emoji \
        fonts-noto-cjk \
    # 清理缓存
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 创建Python软链接
RUN ln -sf /usr/bin/python3 /usr/bin/python

# 升级pip
RUN python -m pip install --upgrade pip

# 安装Allure (用于测试报告)
RUN wget -O allure.tgz https://github.com/allure-framework/allure2/releases/download/2.24.0/allure-2.24.0.tgz \
    && tar -zxf allure.tgz -C /opt/ \
    && ln -s /opt/allure-2.24.0 /opt/allure \
    && rm allure.tgz

# 设置Allure环境变量
ENV ALLURE_HOME=/opt/allure
ENV PATH="$ALLURE_HOME/bin:$PATH"

# 复制项目文件
COPY requirements.txt /app/
COPY pyproject.toml /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器 (在容器中预安装以加快CI速度)
RUN playwright install chromium firefox webkit \
    && playwright install-deps

# 创建输出目录
RUN mkdir -p /app/output/{screenshots,logs,reports,videos,allure-results,temp}

# 复制应用代码
COPY . /app/

# 设置权限
RUN chmod +x /app/ci/scripts/*.sh 2>/dev/null || true

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 暴露端口 (如果需要Web服务)
EXPOSE 8080

# 默认命令
CMD ["python", "-m", "pytest", "--version"]
