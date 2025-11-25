#!/bin/bash
# 快速应用超时修复

echo "🔧 正在应用超时修复..."
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ 未找到 .env 文件"
    echo "请创建 .env 文件并添加配置"
    exit 1
fi

# 检查是否已有 TIMEOUT 配置
if grep -q "ALIBABA_BAILIAN_TIMEOUT" .env; then
    echo "✅ .env 中已有 TIMEOUT 配置"
    current_timeout=$(grep "ALIBABA_BAILIAN_TIMEOUT" .env | cut -d'=' -f2)
    echo "   当前值: $current_timeout 秒"
else
    echo "📝 添加 TIMEOUT 配置到 .env..."
    echo "" >> .env
    echo "# LLM 超时配置（秒）" >> .env
    echo "ALIBABA_BAILIAN_TIMEOUT=180" >> .env
    echo "✅ 已添加 ALIBABA_BAILIAN_TIMEOUT=180"
fi

echo ""
echo "✨ 修复完成！现在可以运行测试："
echo "   python3 test_content_publish.py --single"
echo ""
echo "💡 提示："
echo "   - 步骤 2（理解需求）可能需要 1-3 分钟"
echo "   - 步骤 4（生成素材）可能需要 5-10 分钟"
echo "   - 请关注日志中的进度提示（带 emoji 的行）"

