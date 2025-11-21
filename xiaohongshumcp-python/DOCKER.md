# Docker 部署指南

本文档介绍如何使用 Docker 和 Docker Compose 部署小红书 MCP Python 服务。

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+

## 🚀 快速开始

### 1. 构建镜像

```bash
# 使用 docker-compose 构建
docker-compose build

# 或者直接使用 docker 构建
docker build -t xiaohongshu-mcp:latest .
```

### 2. 配置环境变量

创建 `.env` 文件（可选，如果不创建将使用默认值）：

```env
# 环境配置
ENV=production
BROWSER_HEADLESS=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/xiaohongshu-mcp.log

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# 用户配置
GLOBAL_USER=luyike

# 超时配置
PAGE_LOAD_TIMEOUT=60000
ELEMENT_TIMEOUT=30000
```

### 3. 启动服务

```bash
# 生产环境（默认）
docker-compose up -d

# 开发环境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 📁 数据持久化

Docker Compose 配置会自动挂载以下目录和文件，确保数据持久化：

- `./data` - 数据目录
- `./downloads` - 下载文件目录
- `./logs` - 日志目录（已配置自动清理）
- `./cookies.json` - Cookie 文件
- `./cookies_luyike.json` - 用户 Cookie 文件
- `./user_sessions.json` - 用户会话文件
- `./.env` - 环境变量文件（只读）

## 🗑️ 日志清理机制

项目已配置自动日志清理机制，防止日志文件占用过多磁盘空间。

### 自动清理功能

1. **定时清理**：每天凌晨 2 点自动执行日志清理
2. **启动时清理**：容器启动时自动执行一次清理
3. **清理规则**：
   - 删除超过保留天数的日志文件（默认 7 天）
   - 删除超过大小限制的日志文件（默认 100MB）
   - 支持清理 `.log`、`.log.*` 和 `.zip` 格式的日志文件

### 日志清理配置

在 `.env` 文件中可以配置以下参数：

```env
# 日志目录（默认: /app/logs）
LOG_DIR=/app/logs

# 日志保留天数（默认: 7天）
LOG_RETENTION_DAYS=7

# 最大日志文件大小（MB，默认: 100MB）
MAX_LOG_SIZE_MB=100
```

### 手动执行清理

如果需要手动执行日志清理，可以进入容器执行：

```bash
# 进入容器
docker-compose exec xiaohongshu-mcp bash

# 执行清理脚本
/app/scripts/cleanup_logs.sh
```

### 日志轮转

除了自动清理，应用还使用 loguru 的日志轮转功能：

- **文件大小轮转**：当日志文件达到 10MB 时自动轮转
- **自动压缩**：旧日志自动压缩为 zip 格式
- **保留时间**：保留最近 7 天的日志

这些配置在 `src/xiaohongshu_mcp_python/utils/logger_config.py` 中定义。

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ENV` | `production` | 环境模式：`development` 或 `production` |
| `BROWSER_HEADLESS` | `true` | 是否使用无头浏览器 |
| `LOG_LEVEL` | `INFO` | 日志级别：`DEBUG`/`INFO`/`WARNING`/`ERROR` |
| `LOG_FILE` | `logs/xiaohongshu-mcp.log` | 日志文件路径 |
| `LOG_DIR` | `/app/logs` | 日志目录 |
| `LOG_RETENTION_DAYS` | `7` | 日志保留天数（超过此天数的日志会被自动删除） |
| `MAX_LOG_SIZE_MB` | `100` | 最大日志文件大小（MB，超过此大小的文件会被清理） |
| `SERVER_HOST` | `0.0.0.0` | 服务器监听地址 |
| `SERVER_PORT` | `8000` | 服务器端口 |
| `GLOBAL_USER` | `luyike` | 默认用户名 |
| `PAGE_LOAD_TIMEOUT` | `60000` | 页面加载超时（毫秒） |
| `ELEMENT_TIMEOUT` | `30000` | 元素等待超时（毫秒） |

### 端口映射

默认端口映射：`8000:8000`

可以通过环境变量 `SERVER_PORT` 修改容器内端口，或直接修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "9000:8000"  # 主机端口:容器端口
```

## 🐛 调试

### 查看容器日志

```bash
# 实时查看日志
docker-compose logs -f xiaohongshu-mcp

# 查看最近 100 行日志
docker-compose logs --tail=100 xiaohongshu-mcp
```

### 进入容器

```bash
# 进入运行中的容器
docker-compose exec xiaohongshu-mcp bash

# 或者使用 docker 命令
docker exec -it xiaohongshu-mcp bash
```

### 检查服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看健康检查状态
docker inspect xiaohongshu-mcp | grep -A 10 Health
```

### 测试健康检查

```bash
# 从容器内测试
docker-compose exec xiaohongshu-mcp curl http://localhost:8000/health

# 从主机测试
curl http://localhost:8000/health
```

## 🔄 更新服务

```bash
# 停止服务
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

## 🧹 清理

```bash
# 停止并删除容器
docker-compose down

# 删除容器、网络和卷（注意：会删除挂载的数据）
docker-compose down -v

# 删除镜像
docker rmi xiaohongshu-mcp:latest
```

## 📝 常见问题

### 1. 端口被占用

如果端口 8000 已被占用，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "9000:8000"  # 使用 9000 端口
```

### 2. 权限问题

如果遇到文件权限问题，可以修改挂载目录的权限：

```bash
chmod -R 755 data downloads logs
```

### 3. Playwright 浏览器安装失败

如果 Playwright 浏览器安装失败，可以进入容器手动安装：

```bash
docker-compose exec xiaohongshu-mcp uv run playwright install chromium
docker-compose exec xiaohongshu-mcp uv run playwright install-deps chromium
```

### 4. 内存不足

Playwright 浏览器需要一定内存，建议至少 2GB 可用内存。如果内存不足，可以：

- 增加 Docker 内存限制
- 减少并发浏览器实例
- 使用更轻量的浏览器配置

## 🔐 安全建议

1. **不要将敏感信息提交到版本控制**
   - `.env` 文件已添加到 `.gitignore`
   - Cookie 文件包含敏感信息，不要提交

2. **使用强密码和安全的 Cookie**
   - 定期更新 Cookie
   - 不要在公共网络暴露服务

3. **限制网络访问**
   - 使用防火墙限制端口访问
   - 考虑使用反向代理（如 Nginx）

4. **定期更新镜像**
   - 定期拉取最新的基础镜像
   - 更新依赖包以修复安全漏洞

## 📚 相关文档

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [项目 README](./README.md)

