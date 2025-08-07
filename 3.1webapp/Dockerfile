# AI增强股票分析系统 - 3.1webapp Docker镜像
# Enhanced AI Stock Analysis System - 3.1webapp Docker Image

# 使用Python 3.11获得更好的兼容性
FROM python:3.11-bookworm

# 设置维护者信息
LABEL maintainer="AI Stock Analysis System"
LABEL version="3.1.0"
LABEL description="Enhanced AI Stock Analysis System with Multi-Market Support"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

# 设置工作目录
WORKDIR /app

# 更换apt源为阿里云镜像并安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    tzdata \
    ca-certificates \
    && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
# 复制应用代码
COPY config.json requirements-minimal.txt requirements.txt *.py /app/

# 安装Python依赖 - 分步安装以减少构建失败风险
RUN pip3 install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ \
    && pip3 install --no-cache-dir --only-binary=all -r requirements-minimal.txt -i https://mirrors.aliyun.com/pypi/simple/

# 创建必要的目录
RUN mkdir -p /app/logs /app/cache /app/data

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 启动命令
CMD ["python", "enhanced_flask_server.py"] 