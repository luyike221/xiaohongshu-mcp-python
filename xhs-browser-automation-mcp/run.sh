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
    debug                调试模式（启用debugpy，等待调试器连接，端口5678）
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
    ./run.sh debug                        # 调试模式启动（等待调试器连接）
    ./run.sh dev --port 9000              # 开发模式，端口9000
    ./run.sh prod --log-level DEBUG       # 生产模式，DEBUG日志
    ./run.sh dev --log-file logs/app.log  # 开发模式，日志写入文件
    ./run.sh debug --port 9000            # 调试模式，MCP端口9000

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
        debug)
            MODE="debug"
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
elif [ "$MODE" = "debug" ]; then
    ENV_ARGS=("--env" "development")
    if [[ ! " ${EXTRA_ARGS[@]} " =~ " --log-level " ]]; then
        EXTRA_ARGS+=("--log-level" "DEBUG")
    fi
    if [[ ! " ${EXTRA_ARGS[@]} " =~ " --headless " ]] && [[ ! " ${EXTRA_ARGS[@]} " =~ " --no-headless " ]]; then
        EXTRA_ARGS+=("--no-headless")
    fi
    echo -e "${GREEN}🐛 启动调试模式${NC}"
    echo -e "${BLUE}环境: 开发环境${NC}"
    echo -e "${BLUE}浏览器: 有头模式${NC}"
    echo -e "${BLUE}日志: DEBUG${NC}"
    echo -e "${YELLOW}调试器: 等待连接 (端口 5678)${NC}"
    echo -e "${YELLOW}在 VSCode 中使用 '附加到进程' 配置连接调试器${NC}"
    echo ""
    
    # 如果有头模式，检查并设置 DISPLAY 环境变量
    if [[ ! " ${EXTRA_ARGS[@]} " =~ " --headless " ]]; then
        if [ -z "$DISPLAY" ]; then
            # 检查是否有 SSH X11 转发
            if [ -n "$SSH_CONNECTION" ] || [ -n "$SSH_CLIENT" ]; then
                echo -e "${RED}⚠ 警告: 检测到 SSH 远程连接，但未启用 X11 转发${NC}"
                echo -e "${YELLOW}   有头模式的浏览器窗口无法显示在本地${NC}"
                echo -e "${YELLOW}   解决方案：使用 SSH X11 转发: ssh -X 或 ssh -Y${NC}"
                echo -e "${YELLOW}   或使用无头模式: ./run.sh debug --headless${NC}"
                echo ""
            fi
            
            # 尝试设置默认 DISPLAY
            if [ -S /tmp/.X11-unix/X0 ] 2>/dev/null || [ -S /tmp/.X11-unix/X1 ] 2>/dev/null; then
                for x in 0 1; do
                    if [ -S /tmp/.X11-unix/X$x ]; then
                        export DISPLAY=":$x"
                        echo -e "${GREEN}✓ 自动设置 DISPLAY=$DISPLAY${NC}"
                        break
                    fi
                done
            else
                export DISPLAY=":0"
                echo -e "${YELLOW}⚠ 未检测到 X server，设置 DISPLAY=:0（如果失败，请手动设置 DISPLAY 环境变量）${NC}"
            fi
        else
            if echo "$DISPLAY" | grep -q "localhost\|127.0.0.1\|:"; then
                echo -e "${GREEN}✓ 使用现有 DISPLAY=$DISPLAY（X11 转发已启用）${NC}"
            else
                echo -e "${GREEN}✓ 使用现有 DISPLAY=$DISPLAY${NC}"
            fi
        fi
    fi
    
    # 检查是否安装了 debugpy
    if ! uv run python -c "import debugpy" 2>/dev/null; then
        echo -e "${YELLOW}正在安装 debugpy...${NC}"
        uv pip install debugpy
    fi
    
    # 创建临时调试脚本
    DEBUG_SCRIPT=$(mktemp /tmp/xiaohongshu_debug_XXXXXX.py)
    cat > "$DEBUG_SCRIPT" << 'PYTHON_EOF'
import debugpy
import sys
import os

# 配置 debugpy
debugpy.listen(('localhost', 5678))
print('🐛 调试器已启动，等待连接...')
print('📌 在 VSCode 中使用 "小红书MCP - 附加到进程" 配置连接')
print('⏳ 等待调试器连接中...')
debugpy.wait_for_client()
print('✅ 调试器已连接！')

# 设置 PYTHONPATH
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
os.environ['PYTHONPATH'] = os.path.join(os.getcwd(), 'src')

# 导入并运行主程序
from xiaohongshu_mcp_python.main import cli_main
cli_main()
PYTHON_EOF
    
    # 使用 debugpy 启动，等待调试器连接
    exec uv run python "$DEBUG_SCRIPT" "${ENV_ARGS[@]}" "${EXTRA_ARGS[@]}"
fi

# 判断是否为有头模式
IS_HEADED=false
if [[ " ${EXTRA_ARGS[@]} " =~ " --no-headless " ]]; then
    IS_HEADED=true
elif [[ ! " ${EXTRA_ARGS[@]} " =~ " --headless " ]]; then
    # 如果没有明确指定，根据模式判断
    if [ "$MODE" = "dev" ] || [ "$MODE" = "debug" ]; then
        IS_HEADED=true
    fi
fi

# 如果有头模式，检查并设置 DISPLAY 环境变量
if [ "$IS_HEADED" = true ]; then
    if [ -z "$DISPLAY" ]; then
        # 优先检测 VNC 服务器
        VNC_DISPLAY=""
        if command -v vncserver &> /dev/null; then
            VNC_LIST=$(vncserver -list 2>/dev/null | grep -E "^\s*[0-9]+" | awk '{print $1}' | head -1)
            if [ -n "$VNC_LIST" ]; then
                VNC_DISPLAY=":$VNC_LIST"
                # 检查对应的 socket 是否存在
                if [ -S "/tmp/.X11-unix/X${VNC_LIST}" ]; then
                    export DISPLAY="$VNC_DISPLAY"
                    echo -e "${GREEN}✓ 检测到 VNC 服务器，自动设置 DISPLAY=$DISPLAY${NC}"
                    echo -e "${YELLOW}   提示: 请在 VNC 会话的终端中运行此命令，浏览器窗口才会显示在 VNC 桌面中${NC}"
                fi
            fi
        fi
        
        # 如果 VNC 未设置，尝试检测其他 X server
        if [ -z "$DISPLAY" ]; then
            if [ -S /tmp/.X11-unix/X0 ] 2>/dev/null || [ -S /tmp/.X11-unix/X1 ] 2>/dev/null; then
                # 检测可用的 X server（优先 VNC 的 :1）
                for x in 1 0; do
                    if [ -S /tmp/.X11-unix/X$x ]; then
                        export DISPLAY=":$x"
                        echo -e "${GREEN}✓ 自动设置 DISPLAY=$DISPLAY${NC}"
                        # 检查是否是 VNC
                        if vncserver -list 2>/dev/null | grep -q "^\s*$x\s"; then
                            echo -e "${YELLOW}   提示: 检测到这是 VNC 显示，请在 VNC 会话的终端中运行${NC}"
                        fi
                        break
                    fi
                done
            else
                # 如果没有找到 X server，尝试常见的默认值
                export DISPLAY=":0"
                echo -e "${YELLOW}⚠ 未检测到 X server，设置 DISPLAY=:0（如果失败，请手动设置 DISPLAY 环境变量）${NC}"
            fi
        fi
        
        # 如果检测到 SSH 连接但没有 X11 转发
        if [ -n "$SSH_CONNECTION" ] || [ -n "$SSH_CLIENT" ]; then
            if ! echo "$DISPLAY" | grep -q "localhost"; then
                echo -e "${YELLOW}   提示: 当前在 SSH 终端中，浏览器窗口将显示在服务器上${NC}"
                echo -e "${YELLOW}   如需在本地查看，请在 VNC 会话的终端中运行此命令${NC}"
            fi
        fi
    else
        # 检查 DISPLAY 是否是 X11 转发格式（通常包含 localhost 或 IP）
        if echo "$DISPLAY" | grep -q "localhost\|127.0.0.1"; then
            echo -e "${GREEN}✓ 使用现有 DISPLAY=$DISPLAY（X11 转发已启用）${NC}"
        else
            echo -e "${GREEN}✓ 使用现有 DISPLAY=$DISPLAY${NC}"
            # 检查是否是 VNC
            DISPLAY_NUM=$(echo "$DISPLAY" | sed 's/.*:\([0-9]*\).*/\1/')
            if [ -n "$DISPLAY_NUM" ] && vncserver -list 2>/dev/null | grep -q "^\s*$DISPLAY_NUM\s"; then
                echo -e "${YELLOW}   提示: 这是 VNC 显示，请在 VNC 会话的终端中运行${NC}"
            fi
        fi
    fi
fi

echo ""
echo -e "${YELLOW}执行命令:${NC} uv run python -m xiaohongshu_mcp_python.main ${ENV_ARGS[*]} ${EXTRA_ARGS[*]}"
echo ""

# 启动服务器
exec uv run python -m xiaohongshu_mcp_python.main "${ENV_ARGS[@]}" "${EXTRA_ARGS[@]}"

