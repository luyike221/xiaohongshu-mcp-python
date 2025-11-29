#!/bin/bash
# 查找本地浏览器可执行文件路径

echo "正在查找本地浏览器..."
echo ""

# 常见的浏览器路径
BROWSERS=(
    "/usr/bin/google-chrome"
    "/usr/bin/google-chrome-stable"
    "/usr/bin/chromium"
    "/usr/bin/chromium-browser"
    "/snap/bin/chromium"
    "/usr/bin/chrome"
    "/opt/google/chrome/chrome"
)

FOUND=false

for browser in "${BROWSERS[@]}"; do
    if [ -f "$browser" ] && [ -x "$browser" ]; then
        echo "✓ 找到浏览器: $browser"
        echo "  版本信息:"
        "$browser" --version 2>/dev/null | head -1 || echo "  (无法获取版本信息)"
        echo ""
        FOUND=true
    fi
done

if [ "$FOUND" = false ]; then
    echo "❌ 未找到已安装的浏览器"
    echo ""
    echo "请安装以下浏览器之一："
    echo "  - Google Chrome:"
    echo "    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    echo "    sudo dpkg -i google-chrome-stable_current_amd64.deb"
    echo ""
    echo "  - Chromium:"
    echo "    sudo apt-get update"
    echo "    sudo apt-get install chromium-browser"
    echo ""
    echo "或者使用 which 命令查找："
    echo "  which google-chrome"
    echo "  which chromium-browser"
    echo "  which chromium"
fi

