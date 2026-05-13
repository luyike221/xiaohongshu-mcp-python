#!/bin/bash

# XHS Content Generator MCP 一键运行脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  XHS Content Generator MCP${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到 uv 命令${NC}"
    echo -e "${YELLOW}请先安装 uv:${NC}"
    echo -e "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ 检查到 uv${NC}"

# 检查并确保使用 Python 3.11（强制使用，不依赖系统 Python）
echo -e "${YELLOW}📦 检查 Python 版本...${NC}"

# 确保 Python 3.11 已安装
if ! uv python find 3.11 > /dev/null 2>&1; then
    echo -e "${CYAN}正在安装 Python 3.11...${NC}"
    uv python install 3.11
fi

# 固定使用 Python 3.11
PYTHON_PATH=$(uv python find 3.11)
if [ -z "$PYTHON_PATH" ]; then
    echo -e "${RED}❌ 错误: 无法找到 Python 3.11${NC}"
    echo -e "${YELLOW}请手动安装: uv python install 3.11${NC}"
    exit 1
fi

# 验证 Python 版本
PYTHON_VERSION=$($PYTHON_PATH --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f1,2)

if [ "$PYTHON_MAJOR_MINOR" != "3.11" ]; then
    echo -e "${RED}❌ 错误: Python 版本必须是 3.11，当前: $PYTHON_VERSION${NC}"
    exit 1
fi

# 设置环境变量，强制 uv 使用 Python 3.11
export UV_PYTHON="$PYTHON_PATH"
echo -e "${GREEN}✓ 强制使用 Python 3.11: $PYTHON_VERSION${NC}"
echo -e "${BLUE}  Python 路径: $PYTHON_PATH${NC}"

# 确保 .python-version 文件存在并正确
if [ ! -f ".python-version" ] || [ "$(cat .python-version)" != "3.11" ]; then
    echo "3.11" > .python-version
    echo -e "${GREEN}✓ 已更新 .python-version 文件${NC}"
fi

# 同步依赖（强制使用 Python 3.11）
echo ""
echo -e "${YELLOW}📦 同步项目依赖（使用 Python 3.11）...${NC}"
uv sync --python 3.11

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 依赖同步失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 依赖同步完成${NC}"

# 检查环境变量
echo ""
echo -e "${YELLOW}🔍 检查环境变量...${NC}"

if [ -z "$GEMINI_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  警告: 未设置 API Key 环境变量${NC}"
    echo -e "${YELLOW}   可以通过以下方式设置:${NC}"
    echo -e "   export GEMINI_API_KEY='your-api-key'"
    echo -e "   或"
    echo -e "   export OPENAI_API_KEY='your-api-key'"
    echo -e "${YELLOW}   也可以在调用工具时通过参数传入${NC}"
    echo ""
else
    if [ -n "$GEMINI_API_KEY" ]; then
        echo -e "${GREEN}✓ 检测到 GEMINI_API_KEY${NC}"
    fi
    if [ -n "$OPENAI_API_KEY" ]; then
        echo -e "${GREEN}✓ 检测到 OPENAI_API_KEY${NC}"
    fi
fi

# 获取端口号（从命令行参数或环境变量，默认 8004）
PORT=${1:-${PORT:-8004}}

echo ""
echo -e "${BLUE}🚀 启动 MCP 服务...${NC}"
echo -e "${BLUE}   端口: $PORT${NC}"
echo -e "${BLUE}   访问: http://localhost:$PORT${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
echo ""

# 运行服务（使用 Python 3.11）
uv run --python 3.11 python -m xhs_content_generator_mcp.main "$PORT"

