#!/bin/bash

# 小红书 MCP 服务器启动脚本（固定：debugpy 调试 + 开发环境；默认有头浏览器）
# 用法: ./run.sh [选项]

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

固定行为：启用 debugpy（端口 5678，等待调试器连接）、开发环境、默认有头浏览器。
可选在无显示环境使用 ${BLUE}--headless${NC}。

${BLUE}用法:${NC}
    ./run.sh [选项]

${BLUE}选项:${NC}
    --port PORT         MCP HTTP 端口（默认: 8003）
    --headless          无头浏览器（无图形环境时使用）
    help, --help, -h    显示此帮助信息

${BLUE}示例:${NC}
    ./run.sh
    ./run.sh --port 9000
    ./run.sh --headless

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

EXTRA_ARGS=()
ENV_ARGS=("--env" "development")

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
        --headless)
            EXTRA_ARGS+=("--headless")
            shift
            ;;
        *)
            echo -e "${RED}错误: 未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

if [[ ! " ${EXTRA_ARGS[*]} " =~ " --port " ]]; then
    EXTRA_ARGS+=("--port" "8003")
fi

check_uv
check_dependencies

# 默认有头：覆盖 .env 中 BROWSER_HEADLESS，除非显式 --headless
if [[ " ${EXTRA_ARGS[*]} " =~ " --headless " ]]; then
    export BROWSER_HEADLESS=true
else
    export BROWSER_HEADLESS=false
fi

echo -e "${GREEN}🐛 启动（debugpy 调试模式）${NC}"
echo -e "${BLUE}环境: 开发环境${NC}"
echo -e "${BLUE}浏览器: $([ "${BROWSER_HEADLESS}" = "true" ] && echo "无头模式" || echo "有头模式")${NC}"
echo -e "${YELLOW}调试器: 等待连接 (端口 5678)${NC}"
echo -e "${YELLOW}在 VSCode 中使用「附加到进程」配置连接调试器${NC}"
echo ""

# 有头模式：DISPLAY / VNC / X11
if [[ ! " ${EXTRA_ARGS[*]} " =~ " --headless " ]]; then
    if [ -z "$DISPLAY" ]; then
        VNC_DISPLAY=""
        if command -v vncserver &> /dev/null; then
            VNC_LIST=$(vncserver -list 2>/dev/null | grep -E "^\s*[0-9]+" | awk '{print $1}' | head -1)
            if [ -n "$VNC_LIST" ]; then
                VNC_DISPLAY=":$VNC_LIST"
                if [ -S "/tmp/.X11-unix/X${VNC_LIST}" ]; then
                    export DISPLAY="$VNC_DISPLAY"
                    echo -e "${GREEN}✓ 检测到 VNC 服务器，自动设置 DISPLAY=$DISPLAY${NC}"
                    echo -e "${YELLOW}   提示: 请在 VNC 会话的终端中运行此命令，浏览器窗口才会显示在 VNC 桌面中${NC}"
                fi
            fi
        fi

        if [ -z "$DISPLAY" ]; then
            if [ -S /tmp/.X11-unix/X0 ] 2>/dev/null || [ -S /tmp/.X11-unix/X1 ] 2>/dev/null; then
                for x in 1 0; do
                    if [ -S /tmp/.X11-unix/X$x ]; then
                        export DISPLAY=":$x"
                        echo -e "${GREEN}✓ 自动设置 DISPLAY=$DISPLAY${NC}"
                        if vncserver -list 2>/dev/null | grep -q "^\s*$x\s"; then
                            echo -e "${YELLOW}   提示: 检测到这是 VNC 显示，请在 VNC 会话的终端中运行${NC}"
                        fi
                        break
                    fi
                done
            else
                export DISPLAY=":0"
                echo -e "${YELLOW}⚠ 未检测到 X server，设置 DISPLAY=:0（若失败请手动设置 DISPLAY）${NC}"
            fi
        fi

        if [ -n "$SSH_CONNECTION" ] || [ -n "$SSH_CLIENT" ]; then
            if ! echo "$DISPLAY" | grep -q "localhost"; then
                echo -e "${YELLOW}   提示: 当前在 SSH 终端中，浏览器窗口将显示在服务器上${NC}"
                echo -e "${YELLOW}   如需在本地查看，请在 VNC 会话的终端中运行；无图形环境请使用: ./run.sh --headless${NC}"
            fi
        fi
    else
        if echo "$DISPLAY" | grep -q "localhost\|127.0.0.1"; then
            echo -e "${GREEN}✓ 使用现有 DISPLAY=$DISPLAY（X11 转发已启用）${NC}"
        else
            echo -e "${GREEN}✓ 使用现有 DISPLAY=$DISPLAY${NC}"
            DISPLAY_NUM=$(echo "$DISPLAY" | sed 's/.*:\([0-9]*\).*/\1/')
            if [ -n "$DISPLAY_NUM" ] && vncserver -list 2>/dev/null | grep -q "^\s*$DISPLAY_NUM\s"; then
                echo -e "${YELLOW}   提示: 这是 VNC 显示，请在 VNC 会话的终端中运行${NC}"
            fi
        fi
    fi
fi

if ! uv run python -c "import debugpy" 2>/dev/null; then
    echo -e "${YELLOW}正在安装 debugpy...${NC}"
    uv pip install debugpy
fi

DEBUG_SCRIPT=$(mktemp /tmp/xiaohongshu_debug_XXXXXX.py)
cat > "$DEBUG_SCRIPT" << 'PYTHON_EOF'
import debugpy
import sys
import os

debugpy.listen(('localhost', 5678))
print('🐛 调试器已启动，等待连接...')
print('📌 在 VSCode 中使用 "小红书MCP - 附加到进程" 配置连接')
print('⏳ 等待调试器连接中...')
debugpy.wait_for_client()
print('✅ 调试器已连接！')

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
os.environ['PYTHONPATH'] = os.path.join(os.getcwd(), 'src')

from xiaohongshu_mcp_python.main import cli_main
cli_main()
PYTHON_EOF

echo ""
echo -e "${YELLOW}执行命令:${NC} uv run python $DEBUG_SCRIPT ${ENV_ARGS[*]} ${EXTRA_ARGS[*]}"
echo ""

exec uv run python "$DEBUG_SCRIPT" "${ENV_ARGS[@]}" "${EXTRA_ARGS[@]}"
