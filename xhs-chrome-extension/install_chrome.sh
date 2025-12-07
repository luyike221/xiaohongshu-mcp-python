#!/bin/bash

# Ubuntu 24 安装 Google Chrome 脚本

echo "开始安装 Google Chrome..."

# 检查是否已安装
if command -v google-chrome &> /dev/null; then
    echo "Chrome 已经安装，版本："
    google-chrome --version
    exit 0
fi

# 创建临时目录
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

echo "正在下载 Chrome..."
# 下载 Chrome .deb 包
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

if [ $? -ne 0 ]; then
    echo "下载失败，请检查网络连接"
    exit 1
fi

echo "正在安装 Chrome..."
# 安装依赖并安装 Chrome
sudo apt update
sudo apt install -y ./google-chrome-stable_current_amd64.deb

if [ $? -eq 0 ]; then
    echo "✅ Chrome 安装成功！"
    echo "版本信息："
    google-chrome --version
    echo ""
    echo "你可以通过以下方式启动 Chrome："
    echo "  - 在应用程序菜单中搜索 'Chrome'"
    echo "  - 或在终端运行: google-chrome"
else
    echo "❌ 安装失败，请检查错误信息"
    exit 1
fi

# 清理临时文件
cd -
rm -rf "$TMP_DIR"
