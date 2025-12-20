#!/bin/bash
# XHS Video MCP 启动脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "XHS Video MCP 服务启动"
echo "=========================================="

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 文件不存在"
    echo "正在从 env.example 创建 .env 文件..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ 已创建 .env 文件，请编辑后填入实际配置"
    else
        echo "❌ env.example 文件不存在，请手动创建 .env 文件"
        exit 1
    fi
fi

# 检查是否安装了 uv
if ! command -v uv &> /dev/null; then
    echo "❌ 未找到 uv，请先安装 uv:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 同步依赖
echo "📦 同步依赖..."
uv sync

# 启动服务
echo "🚀 启动 MCP 服务..."
echo ""

# 支持命令行参数
HOST="${1:-0.0.0.0}"
PORT="${2:-8005}"

uv run xhs-video-mcp --host "$HOST" --port "$PORT"

