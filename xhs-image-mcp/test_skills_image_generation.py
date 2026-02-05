"""
测试 Skills + 图片生成功能

测试内容：
1. Skills 加载和读取
2. 使用 Skills 生成图片提示词
3. 图片生成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from image_video_mcp.skills import SkillManager
from image_video_mcp.services import ImageGenerationService
from image_video_mcp.clients import DashScopeImageClient, ZImageClient


class TestSkillsImageGeneration:
    """Skills + 图片生成测试类"""

    def __init__(self):
        """初始化测试类"""
        self.skill_manager = SkillManager()
        print("=" * 80)
        print("Skills + 图片生成测试")
        print("=" * 80)

    def test_skills_loading(self):
        """测试 1: Skills 加载"""
        print("\n" + "=" * 80)
        print("测试 1: Skills 加载")
        print("=" * 80)

        # 列出所有技能
        skills = self.skill_manager.list_skills()
        print(f"\n✅ 已加载 {len(skills)} 个技能:")
        for skill in skills:
            print(f"  - {skill['name']}: {skill['description']}")

        # 测试读取特定技能
        test_skills = [
            "z_images_system_prompt",
            "z_images_user_prompt",
            "default_system_prompt",
            "z_image_client_template",
        ]

        print("\n测试读取特定技能:")
        for skill_name in test_skills:
            content = self.skill_manager.get_skill(skill_name)
            if content:
                print(f"  ✅ {skill_name}: {len(content)} 字符")
            else:
                print(f"  ❌ {skill_name}: 未找到")

        return True

    def test_skills_formatting(self):
        """测试 2: Skills 格式化（参数替换）"""
        print("\n" + "=" * 80)
        print("测试 2: Skills 格式化（参数替换）")
        print("=" * 80)

        # 测试格式化用户提示词
        test_content = "如何在家做拿铁咖啡\n\n分享几个实用技巧"
        test_style = "真实"

        formatted = self.skill_manager.format_skill(
            "z_images_user_prompt",
            full_content=test_content,
            style=test_style,
        )

        if formatted:
            print(f"\n✅ 格式化成功:")
            print(f"  原始内容: {test_content[:50]}...")
            print(f"  风格: {test_style}")
            print(f"  格式化后长度: {len(formatted)} 字符")
            print(f"\n格式化结果预览（前200字符）:")
            print("-" * 80)
            print(formatted[:200] + "...")
            print("-" * 80)
            return True
        else:
            print(f"\n❌ 格式化失败: z_images_user_prompt 未找到")
            return False

    async def test_image_generation_with_skills(self):
        """测试 3: 使用 Skills 生成图片提示词并生成图片"""
        print("\n" + "=" * 80)
        print("测试 3: 使用 Skills 生成图片提示词并生成图片")
        print("=" * 80)

        # 测试内容
        full_content = """标题：如何在家做拿铁咖啡

正文：分享几个实用技巧

✅ 核心要点：
- 准备咖啡豆
- 磨豆
- 冲泡

💡 注意事项：
选择适合的咖啡豆很重要"""

        style = "真实"

        print(f"\n测试内容:")
        print(f"  内容长度: {len(full_content)} 字符")
        print(f"  风格: {style}")
        print(f"  内容预览: {full_content[:100]}...")

        try:
            # 创建图片生成服务（自动初始化 LLM 客户端）
            print("\n初始化 ImageGenerationService...")
            service = ImageGenerationService(auto_init_qwen=True)

            # 测试：使用 DashScopeImageClient
            print("\n使用 DashScopeImageClient 生成图片...")
            client = DashScopeImageClient()

            # 生成图片（会使用 Skills 中的提示词）
            print("\n开始生成图片（使用 Skills 提示词）...")
            result = await service.generate_images_from_content(
                full_content=full_content,
                style=style,
                max_wait_time=600,
                client=client,
            )

            print("\n" + "=" * 80)
            print("生成结果:")
            print("=" * 80)
            print(f"  任务 ID: {result.get('task_id')}")
            print(f"  总页面数: {result.get('total')}")
            print(f"  成功: {result.get('completed')}")
            print(f"  失败: {result.get('failed')}")
            print(f"  整体成功: {result.get('success')}")

            if result.get("images"):
                print(f"\n生成的图片:")
                for img in result["images"]:
                    print(f"  - 索引: {img.get('index')}, 类型: {img.get('type')}")
                    print(f"    路径: {img.get('url')}")

            if result.get("failed_pages"):
                print(f"\n失败的页面:")
                for failed in result["failed_pages"]:
                    print(f"  - 索引: {failed.get('index')}")
                    print(f"    错误: {failed.get('error')}")

            await client.close()
            return result.get("success", False)

        except ValueError as e:
            print(f"\n❌ 配置错误: {e}")
            print("请确保已设置 DASHSCOPE_API_KEY 和 QWEN_API_KEY 环境变量")
            return False
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def test_direct_image_generation(self):
        """测试 4: 直接使用 Skills 模板生成图片（不通过 LLM）"""
        print("\n" + "=" * 80)
        print("测试 4: 直接使用 Skills 模板生成图片")
        print("=" * 80)

        # 直接使用 Skills 中的模板生成提示词
        page_content = "a steaming hot latte coffee on a warm wooden table, coffee beans and latte art tools beside it, natural sunlight streaming through the window, creating a cozy home atmosphere, ultra detailed, premium quality, photorealistic"

        print(f"\n使用 Skills 模板生成提示词...")
        prompt = self.skill_manager.format_skill(
            "z_image_client_template",
            page_content=page_content,
        )

        if not prompt:
            print("❌ 无法获取 z_image_client_template")
            return False

        print(f"✅ 提示词生成成功: {len(prompt)} 字符")
        print(f"提示词预览: {prompt[:100]}...")

        try:
            # 直接使用客户端生成图片
            print("\n使用 DashScopeImageClient 直接生成图片...")
            client = DashScopeImageClient()

            image_data = await client.generate_image(
                prompt=prompt,
                size="1120*1440",  # z-image-turbo 推荐尺寸
            )

            # 保存图片
            output_path = Path("test_output_skills.png")
            output_path.write_bytes(image_data)
            print(f"\n✅ 图片生成成功: {len(image_data)} bytes")
            print(f"   保存路径: {output_path.absolute()}")

            await client.close()
            return True

        except Exception as e:
            print(f"\n❌ 图片生成失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        results = []

        # 测试 1: Skills 加载
        results.append(("Skills 加载", self.test_skills_loading()))

        # 测试 2: Skills 格式化
        results.append(("Skills 格式化", self.test_skills_formatting()))

        # 测试 3: 使用 Skills 生成图片（需要 LLM）
        results.append(
            ("Skills + 图片生成（完整流程）", await self.test_image_generation_with_skills())
        )

        # 测试 4: 直接使用 Skills 模板生成图片
        results.append(
            ("直接使用 Skills 模板生成图片", await self.test_direct_image_generation())
        )

        # 汇总结果
        print("\n" + "=" * 80)
        print("测试结果汇总")
        print("=" * 80)

        all_passed = True
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {status}: {test_name}")
            if not result:
                all_passed = False

        print("\n" + "=" * 80)
        if all_passed:
            print("✅ 所有测试通过！")
        else:
            print("❌ 部分测试失败")
        print("=" * 80)

        return all_passed


async def main():
    """主函数"""
    tester = TestSkillsImageGeneration()
    success = await tester.run_all_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
