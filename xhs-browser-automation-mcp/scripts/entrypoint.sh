#!/bin/bash
# Docker 容器启动脚本
# 启动 cron 服务和主应用服务

set -e

echo "=========================================="
echo "启动小红书 MCP 服务"
echo "=========================================="

# 启动 cron 服务（用于定期清理日志）
echo "启动 cron 服务..."
service cron start || {
    echo "警告: cron 服务启动失败，日志清理功能可能不可用"
}

# 容器启动时执行一次日志清理
echo "执行初始日志清理..."
/app/scripts/cleanup_logs.sh || {
    echo "警告: 初始日志清理失败"
}

# 启动主服务
echo "启动主服务..."
exec uv run python -m xiaohongshu_mcp_python.main --env production --host 0.0.0.0

