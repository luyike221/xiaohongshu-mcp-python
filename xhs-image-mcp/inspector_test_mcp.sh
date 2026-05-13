#!/bin/bash

# MCP Inspector 调试脚本
# 用于启动 MCP Inspector 连接到图像和视频生成 MCP 服务进行调试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_HOST="localhost"
DEFAULT_PORT="8003"
MCP_ENDPOINT="/mcp"

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 显示帮助信息
show_help() {
    cat << EOF
${GREEN}MCP Inspector 调试脚本${NC}

${BLUE}用法:${NC}
    ./inspector.sh [选项]

${BLUE}选项:${NC}
    --host HOST          MCP 服务器主机地址（默认: ${DEFAULT_HOST}）
    --port PORT          MCP 服务器端口（默认: ${DEFAULT_PORT}）
    --endpoint PATH      MCP 端点路径（默认: ${MCP_ENDPOINT}）
    --auto-start         自动启动 MCP 服务器（如果未运行）
    --no-auto-start      不自动启动服务器，仅检查并连接（默认）
    --skip-confirm       跳过启动确认，直接启动 Inspector
    --help, -h           显示此帮助信息

${BLUE}示例:${NC}
    ./inspector_test_mcp.sh                          # 连接到默认服务器 (http://localhost:8003/mcp)
    ./inspector_test_mcp.sh --port 9000              # 连接到自定义端口
    ./inspector_test_mcp.sh --auto-start             # 自动启动服务器并连接
    ./inspector_test_mcp.sh --host 0.0.0.0 --port 8003  # 连接到指定主机和端口
    ./inspector_test_mcp.sh --skip-confirm           # 跳过确认，直接启动 Inspector
    ./inspector_test_mcp.sh --auto-start --skip-confirm  # 自动启动服务器并跳过确认

${BLUE}说明:${NC}
    - 如果使用 --auto-start，脚本会在后台启动 MCP 服务器，然后启动 Inspector
    - 脚本退出时会自动清理后台服务器进程
    - 确保已安装 Node.js 和 npx

EOF
}

# 检查是否安装了 Node.js 和 npx
check_node() {
    if ! command -v node &> /dev/null; then
        echo -e "${RED}错误: 未找到 Node.js${NC}"
        echo -e "${YELLOW}请先安装 Node.js:${NC}"
        echo "  https://nodejs.org/"
        exit 1
    fi
    
    if ! command -v npx &> /dev/null; then
        echo -e "${RED}错误: 未找到 npx${NC}"
        echo -e "${YELLOW}npx 通常随 Node.js 一起安装，请检查安装${NC}"
        exit 1
    fi
}

# 检查服务器是否运行
check_server() {
    local host=$1
    local port=$2
    local url="http://${host}:${port}${MCP_ENDPOINT}"
    
    echo -e "${CYAN}检查服务器状态: ${url}${NC}"
    
    # 尝试连接服务器
    if command -v curl &> /dev/null; then
        if curl -s --connect-timeout 2 "${url}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 服务器正在运行${NC}"
            return 0
        fi
    elif command -v wget &> /dev/null; then
        if wget --quiet --timeout=2 --spider "${url}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 服务器正在运行${NC}"
            return 0
        fi
    else
        # 如果没有 curl 或 wget，尝试使用 Python
        if python3 -c "import urllib.request; urllib.request.urlopen('${url}', timeout=2)" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 服务器正在运行${NC}"
            return 0
        fi
    fi
    
    echo -e "${YELLOW}✗ 服务器未运行或无法连接${NC}"
    return 1
}

# 启动 MCP 服务器（后台）
start_server() {
    local host=$2
    local port=$3
    
    echo -e "${CYAN}正在启动 MCP 服务器...${NC}"
    
    # 使用 run.sh 启动服务器
    if [ -f "./run.sh" ]; then
        ./run.sh --host "$host" --port "$port" > /tmp/image-video-mcp-server.log 2>&1 &
        SERVER_PID=$!
        echo -e "${GREEN}服务器已启动（PID: ${SERVER_PID}）${NC}"
        echo -e "${BLUE}日志文件: /tmp/image-video-mcp-server.log${NC}"
        
        # 等待服务器启动
        echo -e "${CYAN}等待服务器启动...${NC}"
        local max_attempts=30
        local attempt=0
        
        while [ $attempt -lt $max_attempts ]; do
            if check_server "$host" "$port" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ 服务器启动成功！${NC}"
                return 0
            fi
            sleep 1
            attempt=$((attempt + 1))
            echo -n "."
        done
        echo ""
        echo -e "${RED}错误: 服务器启动超时${NC}"
        echo -e "${YELLOW}请检查日志: /tmp/image-video-mcp-server.log${NC}"
        kill $SERVER_PID 2>/dev/null || true
        return 1
    else
        echo -e "${RED}错误: 未找到 run.sh 脚本${NC}"
        return 1
    fi
}

# 清理函数
cleanup() {
    if [ -n "$SERVER_PID" ]; then
        echo -e "\n${YELLOW}正在停止后台服务器（PID: ${SERVER_PID}）...${NC}"
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        echo -e "${GREEN}服务器已停止${NC}"
    fi
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 解析参数
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
AUTO_START=false
SKIP_CONFIRM=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --endpoint)
            MCP_ENDPOINT="$2"
            shift 2
            ;;
        --auto-start)
            AUTO_START=true
            shift
            ;;
        --no-auto-start)
            AUTO_START=false
            shift
            ;;
        --skip-confirm)
            SKIP_CONFIRM=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 检查 Node.js
check_node

# 构建 MCP 服务器 URL
MCP_URL="http://${HOST}:${PORT}${MCP_ENDPOINT}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MCP Inspector 调试工具${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}服务器地址: ${MCP_URL}${NC}"
echo ""

# 检查服务器状态
if ! check_server "$HOST" "$PORT"; then
    if [ "$AUTO_START" = true ]; then
        echo ""
        if ! start_server "" "$HOST" "$PORT"; then
            exit 1
        fi
    else
        echo -e "${YELLOW}提示: 使用 --auto-start 选项可以自动启动服务器${NC}"
        echo -e "${YELLOW}或者先运行: ./run.sh --host ${HOST} --port ${PORT}${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  准备启动 MCP Inspector${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}MCP 服务器信息:${NC}"
echo -e "  ${CYAN}URL:${NC}        ${MCP_URL}"
echo -e "  ${CYAN}主机:${NC}      ${HOST}"
echo -e "  ${CYAN}端口:${NC}      ${PORT}"
echo -e "  ${CYAN}端点:${NC}      ${MCP_ENDPOINT}"
echo ""
echo -e "${YELLOW}使用说明:${NC}"
echo -e "  1. MCP Inspector 启动后，会在浏览器中打开交互界面"
echo -e "  2. 在 Inspector 界面中，选择 ${GREEN}HTTP${NC} 传输方式"
echo -e "  3. 输入服务器地址: ${GREEN}${MCP_URL}${NC}"
echo -e "  4. 点击连接开始调试"
echo -e "  5. 按 ${YELLOW}Ctrl+C${NC} 退出 Inspector"
echo ""

if [ "$SKIP_CONFIRM" = false ]; then
    read -p "$(echo -e ${CYAN}按 Enter 键启动 MCP Inspector（或按 Ctrl+C 取消）...${NC})" -r
    echo ""
fi

echo -e "${CYAN}正在启动 MCP Inspector...${NC}"
echo ""

# 启动 MCP Inspector，使用 streamable HTTP 模式
# 注意：MCP Inspector 会在后台启动，然后我们需要等待它启动完成
# 然后尝试通过浏览器 URL 参数预设 HTTP 连接

echo -e "${BLUE}配置信息:${NC}"
echo -e "  ${CYAN}传输方式:${NC} Streamable HTTP"
echo -e "  ${CYAN}服务器 URL:${NC} ${MCP_URL}"
echo ""
echo -e "${YELLOW}提示:${NC} Inspector 启动后，请在浏览器界面中："
echo -e "  ${GREEN}1.${NC} 选择 ${GREEN}HTTP/HTTPS${NC} 传输方式（不要选择 STDIO）"
echo -e "  ${GREEN}2.${NC} 输入服务器地址: ${GREEN}${MCP_URL}${NC}"
echo -e "  ${GREEN}3.${NC} 点击连接"
echo ""

# 启动 MCP Inspector
# Inspector 会启动一个本地 Web 服务器（通常在 6274 端口）
# 然后在浏览器中打开交互界面
# 注意：Inspector 默认使用 STDIO 模式，需要在界面中手动切换到 HTTP
echo -e "${CYAN}正在启动 MCP Inspector...${NC}"
echo ""

# 启动 Inspector，它会自动打开浏览器
# 用户需要在浏览器界面中选择 HTTP 传输方式并输入服务器 URL
npx --yes @modelcontextprotocol/inspector@0.16.2

