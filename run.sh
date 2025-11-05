#!/bin/bash

# 小红书 MCP 服务器启动脚本
# 用法: ./run.sh [dev|prod|development|production] [options]

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
${GREEN}小红书 MCP 服务器启动脚本${NC}

${BLUE}用法:${NC}
    ./run.sh [模式] [选项]

${BLUE}模式:${NC}
    dev, development     开发模式（有头浏览器，DEBUG日志）
    prod, production    生产模式（无头浏览器，INFO日志）
    help, --help, -h    显示此帮助信息

${BLUE}选项:${NC}
    --port PORT         指定服务器端口（默认: 8000）
    --host HOST         指定服务器主机（默认: 127.0.0.1）
    --log-level LEVEL   指定日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
    --log-file FILE     指定日志文件路径
    --headless          强制使用无头模式
    --no-headless       强制使用有头模式

${BLUE}示例:${NC}
    ./run.sh dev                          # 开发模式启动
    ./run.sh prod                         # 生产模式启动
    ./run.sh dev --port 9000              # 开发模式，端口9000
    ./run.sh prod --log-level DEBUG       # 生产模式，DEBUG日志
    ./run.sh dev --log-file logs/app.log  # 开发模式，日志写入文件

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

# 检查 Python 模块是否已安装
check_dependencies() {
    if ! uv run python -c "import xiaohongshu_mcp_python" 2>/dev/null; then
        echo -e "${YELLOW}正在安装依赖...${NC}"
        uv sync
    fi
}

# 解析参数
MODE=""
ENV_ARGS=()
EXTRA_ARGS=()

# 解析第一个参数（模式）
if [ $# -eq 0 ]; then
    # 默认开发模式
    MODE="dev"
else
    case "$1" in
        dev|development)
            MODE="dev"
            shift
            ;;
        prod|production)
            MODE="prod"
            shift
            ;;
        help|--help|-h)
            show_help
            exit 0
            ;;
        *)
            # 如果没有指定模式，默认使用开发模式，并将第一个参数作为额外参数
            MODE="dev"
            ;;
    esac
fi

# 解析剩余参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        help|--help|-h)
            show_help
            exit 0
            ;;
        --port)
            EXTRA_ARGS+=("--port" "$2")
            shift 2
            ;;
        --host)
            EXTRA_ARGS+=("--host" "$2")
            shift 2
            ;;
        --log-level)
            EXTRA_ARGS+=("--log-level" "$2")
            shift 2
            ;;
        --log-file)
            EXTRA_ARGS+=("--log-file" "$2")
            shift 2
            ;;
        --headless)
            EXTRA_ARGS+=("--headless")
            shift
            ;;
        --no-headless)
            EXTRA_ARGS+=("--no-headless")
            shift
            ;;
        *)
            echo -e "${RED}错误: 未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 检查环境
check_uv
check_dependencies

# 根据模式设置环境参数
if [ "$MODE" = "dev" ]; then
    ENV_ARGS=("--env" "development")
    if [[ ! " ${EXTRA_ARGS[@]} " =~ " --log-level " ]]; then
        EXTRA_ARGS+=("--log-level" "DEBUG")
    fi
    if [[ ! " ${EXTRA_ARGS[@]} " =~ " --headless " ]] && [[ ! " ${EXTRA_ARGS[@]} " =~ " --no-headless " ]]; then
        EXTRA_ARGS+=("--no-headless")
    fi
    echo -e "${GREEN}🚀 启动开发模式${NC}"
    echo -e "${BLUE}环境: 开发环境${NC}"
    echo -e "${BLUE}浏览器: 有头模式${NC}"
    echo -e "${BLUE}日志: DEBUG${NC}"
elif [ "$MODE" = "prod" ]; then
    ENV_ARGS=("--env" "production")
    if [[ ! " ${EXTRA_ARGS[@]} " =~ " --log-level " ]]; then
        EXTRA_ARGS+=("--log-level" "INFO")
    fi
    if [[ ! " ${EXTRA_ARGS[@]} " =~ " --headless " ]] && [[ ! " ${EXTRA_ARGS[@]} " =~ " --no-headless " ]]; then
        EXTRA_ARGS+=("--headless")
    fi
    echo -e "${GREEN}🚀 启动生产模式${NC}"
    echo -e "${BLUE}环境: 生产环境${NC}"
    echo -e "${BLUE}浏览器: 无头模式${NC}"
    echo -e "${BLUE}日志: INFO${NC}"
fi

echo ""
echo -e "${YELLOW}执行命令:${NC} uv run python -m xiaohongshu_mcp_python.main ${ENV_ARGS[*]} ${EXTRA_ARGS[*]}"
echo ""

# 启动服务器
exec uv run python -m xiaohongshu_mcp_python.main "${ENV_ARGS[@]}" "${EXTRA_ARGS[@]}"

