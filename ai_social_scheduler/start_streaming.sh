#!/bin/bash
# 一键启动流式前后端服务
# 启动 AI Social Scheduler 流式 API 服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AI Social Scheduler 流式服务启动器${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Python 环境
echo -e "${YELLOW}[1/4] 检查 Python 环境...${NC}"
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓ 找到 uv 工具${NC}"
    PYTHON_CMD="uv run python"
elif command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ 找到 python3${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo -e "${GREEN}✓ 找到 python${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}✗ 未找到 Python 环境${NC}"
    exit 1
fi

# 检查依赖
echo -e "${YELLOW}[2/4] 检查依赖...${NC}"
if [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}✓ 找到项目配置文件${NC}"
else
    echo -e "${RED}✗ 未找到 pyproject.toml${NC}"
    exit 1
fi

# 检查示例文件
echo -e "${YELLOW}[3/4] 检查示例文件...${NC}"
if [ -f "examples/streaming_app_example.py" ]; then
    echo -e "${GREEN}✓ 找到流式应用示例${NC}"
else
    echo -e "${RED}✗ 未找到 examples/streaming_app_example.py${NC}"
    exit 1
fi

# 设置端口（可通过环境变量覆盖）
PORT=${PORT:-8020}
HOST=${HOST:-0.0.0.0}

echo -e "${YELLOW}[4/4] 启动服务...${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  服务信息${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "  前端地址: ${BLUE}http://localhost:${PORT}${NC}"
echo -e "  API 文档: ${BLUE}http://localhost:${PORT}/docs${NC}"
echo -e "  流式接口: ${BLUE}http://localhost:${PORT}/api/v1/chat/stream${NC}"
echo -e "  健康检查: ${BLUE}http://localhost:${PORT}/health${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动中...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}提示: 按 Ctrl+C 停止服务${NC}"
echo ""

# 启动服务
if command -v uv &> /dev/null; then
    uv run python examples/streaming_app_example.py
else
    $PYTHON_CMD examples/streaming_app_example.py
fi

