#!/bin/bash

# MCP Inspector 连接诊断脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MCP Inspector 连接诊断工具${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 MCP 服务器
echo -e "${BLUE}1. 检查 MCP 服务器状态${NC}"
MCP_PORT=${1:-8002}
MCP_HOST=${2:-127.0.0.1}
MCP_URL="http://${MCP_HOST}:${MCP_PORT}/mcp"

if curl -s --connect-timeout 2 -H "Accept: text/event-stream" "${MCP_URL}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MCP 服务器正在运行${NC}"
    echo -e "  地址: ${MCP_URL}"
else
    echo -e "${RED}✗ MCP 服务器未运行或无法连接${NC}"
    echo -e "  请先启动服务器: ./run.sh dev --port ${MCP_PORT}"
    exit 1
fi

echo ""

# 检查 Inspector 代理
echo -e "${BLUE}2. 检查 MCP Inspector 代理状态${NC}"
PROXY_PORT=6277

if netstat -tlnp 2>/dev/null | grep -q ":${PROXY_PORT}" || ss -tlnp 2>/dev/null | grep -q ":${PROXY_PORT}"; then
    echo -e "${GREEN}✓ Inspector 代理正在运行 (端口 ${PROXY_PORT})${NC}"
else
    echo -e "${YELLOW}⚠ Inspector 代理未运行${NC}"
    echo -e "  请先启动 Inspector: ./inspector_test_mcp.sh"
fi

echo ""

# 检查 Inspector Web 界面
echo -e "${BLUE}3. 检查 Inspector Web 界面${NC}"
INSPECTOR_PORT=6274

if netstat -tlnp 2>/dev/null | grep -q ":${INSPECTOR_PORT}" || ss -tlnp 2>/dev/null | grep -q ":${INSPECTOR_PORT}"; then
    echo -e "${GREEN}✓ Inspector Web 界面正在运行${NC}"
    echo -e "  访问地址: http://localhost:${INSPECTOR_PORT}"
else
    echo -e "${YELLOW}⚠ Inspector Web 界面未运行${NC}"
fi

echo ""

# 提供连接指南
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  连接指南${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}在 MCP Inspector 界面中：${NC}"
echo -e "  ${CYAN}1.${NC} 选择传输方式: ${GREEN}HTTP/HTTPS${NC} (不是 STDIO)"
echo -e "  ${CYAN}2.${NC} 输入服务器地址: ${GREEN}${MCP_URL}${NC}"
echo -e "  ${CYAN}3.${NC} 点击 ${GREEN}Connect${NC} 按钮"
echo ""
echo -e "${YELLOW}如果仍然无法连接，请检查：${NC}"
echo -e "  • 服务器地址是否正确: ${MCP_URL}"
echo -e "  • 传输方式是否选择了 HTTP/HTTPS"
echo -e "  • 浏览器控制台是否有错误信息"
echo ""

