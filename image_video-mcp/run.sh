#!/bin/bash

# 图像和视频生成 MCP 服务启动脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 显示帮助信息
show_help() {
    cat << EOF
${GREEN}图像和视频生成 MCP 服务启动脚本${NC}

${BLUE}用法:${NC}
    ./run.sh [选项]

${BLUE}选项:${NC}
    --port PORT         指定服务器端口（默认: 8003）
    --host HOST         指定服务器主机（默认: 127.0.0.1）
    -h, --help          显示此帮助信息

${BLUE}环境变量:${NC}
    MCP_PORT            服务器端口（默认: 8003）
    MCP_HOST            服务器主机（默认: 127.0.0.1）
    DASHSCOPE_API_KEY    通义万相 API Key（必需）

${BLUE}示例:${NC}
    ./run.sh                          # 使用默认端口 8003 启动
    ./run.sh --port 9000              # 指定端口 9000
    ./run.sh --host 0.0.0.0           # 监听所有网络接口
    ./run.sh --host 0.0.0.0 --port 9000  # 自定义主机和端口

EOF
}

# 检查是否安装了 uv
check_uv() {
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}错误: 未找到 uv 命令${NC}"
        echo -e "${YELLOW}请先安装 uv:${NC}"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

# 解析参数
PORT=8003
HOST="127.0.0.1"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 检查 uv
check_uv

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
    echo -e "${YELLOW}请创建 .env 文件并配置 DASHSCOPE_API_KEY${NC}"
    echo -e "${BLUE}可以复制 .env.example 作为模板:${NC}"
    echo "  cp .env.example .env"
    echo ""
fi

# 显示启动信息
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}启动图像和视频生成 MCP 服务${NC}"
echo -e "${GREEN}============================================================${NC}"
echo -e "${BLUE}服务器地址:${NC} http://${HOST}:${PORT}"
echo -e "${BLUE}项目目录:${NC} ${SCRIPT_DIR}"
echo ""

# 启动服务
echo -e "${GREEN}正在启动服务...${NC}"
uv run python -m image_video_mcp.main --host "$HOST" --port "$PORT"

