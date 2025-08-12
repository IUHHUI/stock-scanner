# 🐳 AI增强股票分析系统 - 简化Docker部署指南

## 📋 部署概览

本项目提供了**最简化的Docker容器化部署方案**，采用单容器架构，快速启动，易于管理。

### 🎯 部署特点

- ✅ **单容器部署** - 只有一个Flask应用容器
- ✅ **零依赖** - 不需要Redis、Nginx等额外服务
- ✅ **快速启动** - 一键部署，立即使用
- ✅ **本地存储** - 使用本地目录存储日志和缓存
- ✅ **易于维护** - 配置简单，故障排查容易

## 🚀 快速部署

### 1. 环境准备

```bash
# 确保已安装Docker和Docker Compose
docker --version
docker-compose --version

# 进入项目目录
cd stock-scanner/3.1webapp
```

### 2. 配置API密钥

```bash
# 复制环境变量示例文件
cp env.example .env

# 编辑.env文件，填入您的API密钥
nano .env
```

**必需配置**（至少配置一个）：
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-claude-api-key-here  
ZHIPU_API_KEY=your-zhipu-api-key-here
```

### 3. 一键启动

```bash
# 创建必要的本地目录
mkdir -p logs cache data

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问应用

- **应用地址**: http://localhost:5000
- **API状态**: http://localhost:5000/api/status

## 📊 部署架构

### 简化架构图
```
┌─────────────────┐
│   用户浏览器     │
└─────────┬───────┘
          │ :5000
┌─────────▼───────┐
│  Stock Analyzer │
│   (Flask App)   │
│                 │
│  ┌─────────────┐│
│  │ 本地缓存     ││
│  └─────────────┘│
│  ┌─────────────┐│
│  │ 本地日志     ││
│  └─────────────┘│
└─────────────────┘
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI API密钥 | - | 是* |
| `ANTHROPIC_API_KEY` | Claude API密钥 | - | 是* |
| `ZHIPU_API_KEY` | 智谱AI API密钥 | - | 是* |
| `FLASK_ENV` | Flask环境 | production | 否 |
| `TZ` | 时区 | Asia/Shanghai | 否 |
| `MAX_WORKERS` | 最大工作线程 | 4 | 否 |

*至少需要配置一个AI API密钥

### 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| Flask应用 | 5000 | 主应用服务 |

### 目录结构

```
3.1webapp/
├── docker-compose.yaml    # Docker配置文件
├── Dockerfile            # 镜像构建文件
├── .env                  # 环境变量配置
├── config.json           # 应用配置文件
├── logs/                 # 日志目录 (自动创建)
├── cache/                # 缓存目录 (自动创建)
└── data/                 # 数据目录 (自动创建)
```

## 🔧 常用命令

### 基本操作

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 实时查看最新日志
docker-compose logs --tail=50 -f
```

### 维护操作

```bash
# 更新应用
docker-compose build --no-cache
docker-compose up -d

# 清理旧镜像
docker image prune -f

# 查看资源使用
docker stats stock-analyzer-webapp
```

### 调试操作

```bash
# 进入容器
docker-compose exec stock-analyzer bash

# 查看容器内文件
docker-compose exec stock-analyzer ls -la /app

# 查看配置
docker-compose exec stock-analyzer cat /app/config.json
```

## 📈 性能优化

### 资源配置

根据服务器配置调整`docker-compose.yaml`中的资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'        # CPU核心数
      memory: 2G         # 内存限制
    reservations:
      cpus: '0.5'        # CPU预留
      memory: 512M       # 内存预留
```

### 建议配置

- **最小配置**: 1核CPU + 512MB内存
- **推荐配置**: 2核CPU + 2GB内存
- **高负载配置**: 4核CPU + 4GB内存

## 🛡️ 安全配置

### 1. 启用Web密码保护

编辑`config.json`文件：
```json
{
  "web_auth": {
    "enabled": true,
    "password": "your_secure_password",
    "session_timeout": 3600
  }
}
```

### 2. 防火墙配置

```bash
# 仅开放必要端口
ufw allow 5000/tcp
ufw enable
```

### 3. 定期更新

```bash
# 定期更新镜像
docker-compose pull
docker-compose up -d
```

## 🔍 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看详细错误信息
   docker-compose logs stock-analyzer
   
   # 检查配置文件语法
   docker-compose config
   ```

2. **API密钥错误**
   ```bash
   # 检查环境变量
   docker-compose exec stock-analyzer env | grep API_KEY
   
   # 重新加载环境变量
   docker-compose down
   docker-compose up -d
   ```

3. **端口冲突**
   ```bash
   # 查看端口占用
   netstat -tlnp | grep :5000
   
   # 修改端口映射 (在docker-compose.yaml中)
   ports:
     - "5001:5000"  # 改为5001端口
   ```

4. **磁盘空间不足**
   ```bash
   # 清理日志文件
   rm -rf logs/*
   
   # 清理Docker缓存
   docker system prune -f
   ```

5. **内存不足**
   ```bash
   # 监控内存使用
   docker stats
   
   # 减少工作线程数
   # 在.env文件中设置: MAX_WORKERS=2
   ```

### 日志分析

```bash
# 查看应用日志
docker-compose logs -f stock-analyzer

# 查看本地日志文件
tail -f logs/app.log

# 搜索错误日志
grep -i error logs/*.log
```

## 📦 数据管理

### 备份数据

```bash
# 创建备份目录
mkdir -p backups/$(date +%Y%m%d)

# 备份配置和数据
cp config.json backups/$(date +%Y%m%d)/
cp .env backups/$(date +%Y%m%d)/
cp -r logs backups/$(date +%Y%m%d)/
cp -r cache backups/$(date +%Y%m%d)/
cp -r data backups/$(date +%Y%m%d)/

echo "备份完成: backups/$(date +%Y%m%d)/"
```

### 恢复数据

```bash
# 停止服务
docker-compose down

# 恢复数据
cp -r backups/20240101/* ./

# 重启服务
docker-compose up -d
```

### 清理数据

```bash
# 清理缓存
rm -rf cache/*

# 清理旧日志 (保留最近7天)
find logs/ -name "*.log" -mtime +7 -delete

# 重启服务以重新创建必要文件
docker-compose restart
```

## 🚀 生产环境建议

1. **定期备份** - 设置定时备份脚本
2. **监控告警** - 监控容器健康状态
3. **日志轮转** - 防止日志文件过大
4. **安全更新** - 定期更新基础镜像
5. **资源监控** - 监控CPU和内存使用

### 生产环境检查清单

- [ ] API密钥已正确配置
- [ ] Web密码保护已启用
- [ ] 防火墙规则已设置
- [ ] 备份脚本已配置
- [ ] 监控告警已设置
- [ ] 日志轮转已配置

## 📞 技术支持

如遇到部署问题，请：

1. 查看本文档的故障排除部分
2. 检查容器日志: `docker-compose logs -f`
3. 验证配置文件: `docker-compose config`
4. 提交Issue并附上详细日志

---

**�� 享受简单高效的股票分析服务！** 