#!/bin/bash
# 修复 Plasmo 图标路径问题
# Plasmo 需要在根目录的 assets/ 目录中放置 icon.png

echo "🔧 修复图标路径..."

# 创建根目录的 assets 目录
mkdir -p assets

# 检查 src/assets 中是否有图标文件
if [ -f "src/assets/icon-128.png" ]; then
    echo "✅ 找到现有图标，复制到 assets/icon.png"
    cp src/assets/icon-128.png assets/icon.png
    echo "✅ 图标已复制完成"
elif [ -f "src/assets/icon-48.png" ]; then
    echo "✅ 找到现有图标，复制到 assets/icon.png"
    cp src/assets/icon-48.png assets/icon.png
    echo "✅ 图标已复制完成"
elif [ -f "src/assets/icon-16.png" ]; then
    echo "✅ 找到现有图标，复制到 assets/icon.png"
    cp src/assets/icon-16.png assets/icon.png
    echo "✅ 图标已复制完成"
else
    echo "⚠️  未找到现有图标文件"
    echo "📝 请运行以下命令创建图标："
    echo "   python3 create_icon_for_plasmo.py"
    echo "   或者"
    echo "   python3 create_icons_simple.py  # 然后运行此脚本"
fi

echo ""
echo "📋 Plasmo 图标要求："
echo "   - 位置: assets/icon.png (根目录)"
echo "   - 格式: PNG"
echo "   - 推荐尺寸: 512x512 或更大"
echo "   - Plasmo 会自动生成 16x16, 48x48, 128x128 等尺寸"
