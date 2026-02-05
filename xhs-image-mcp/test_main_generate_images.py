"""
测试 main.py 中的 generate_images_from_content 函数，使用 z-image-turbo
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from image_video_mcp.services import ImageGenerationService
from image_video_mcp.clients import DashScopeImageClient


async def test_generate_images_with_z_image_turbo():
    """测试使用 z-image-turbo 生成图片"""
    print("=" * 80)
    print("测试 generate_images_from_content 函数（使用 z-image-turbo）")
    print("=" * 80)
    
    # 测试内容
    full_content = """标题：如何在家做拿铁咖啡

正文：分享几个实用技巧

✅ 核心要点：
- 准备咖啡豆
- 磨豆
- 冲泡

💡 注意事项：
选择适合的咖啡豆很重要，建议选择中度烘焙的阿拉比卡豆。"""
    
    style = "真实"
    
    print(f"\n测试参数:")
    print(f"  内容长度: {len(full_content)} 字符")
    print(f"  风格: {style}")
    print(f"  模型: z-image-turbo")
    
    try:
        # 创建 z-image-turbo 客户端
        print("\n初始化 DashScopeImageClient (z-image-turbo)...")
        client = DashScopeImageClient(model="z-image-turbo")
        
        # 创建图片生成服务（自动初始化通义千问客户端）
        print("初始化 ImageGenerationService...")
        service = ImageGenerationService(auto_init_qwen=True)
        
        # 调用 generate_images_from_content
        print("\n开始生成图片...")
        result = await service.generate_images_from_content(
            full_content=full_content,
            style=style,
            max_wait_time=600,
            client=client,  # 使用 z-image-turbo 客户端
        )
        
        # 输出结果
        print("\n" + "=" * 80)
        print("生成结果:")
        print("=" * 80)
        print(f"  任务 ID: {result['task_id']}")
        print(f"  总页面数: {result['total']}")
        print(f"  成功: {result['completed']}")
        print(f"  失败: {result['failed']}")
        print(f"  整体成功: {result['success']}")
        
        if result['images']:
            print("\n生成的图片:")
            for img in result['images']:
                print(f"  - 索引: {img['index']}, 类型: {img['type']}")
                print(f"    路径: {img['url']}")
        
        if result.get('failed_pages'):
            print("\n失败的页面:")
            for page in result['failed_pages']:
                print(f"  - 索引: {page['index']}")
                print(f"    错误: {page['error']}")
        
        # 关闭客户端
        await client.close()
        
        print("\n" + "=" * 80)
        if result['success']:
            print("✅ 测试成功！")
        else:
            print("❌ 测试部分失败")
        print("=" * 80)
        
        return result['success']
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_generate_images_with_z_image_turbo())
    sys.exit(0 if success else 1)
