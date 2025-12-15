"""
小红书内容生成 MCP 服务主入口
"""
from typing import Optional
from fastmcp import FastMCP
from loguru import logger

from .config import model_config
from .services.outline_service import OutlineService
from .services.lifestyle_content_service import LifestyleContentService

# 创建 MCP 应用实例
mcp = FastMCP("XHS Content Generator MCP")


@mcp.tool()
async def generate_outline(
    topic: str,
    provider_type: str = "alibaba_bailian",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_output_tokens: int = 8000,
) -> dict:
    """
    生成小红书内容大纲
    
    Args:
        topic: 内容主题，例如"如何在家做拿铁"、"秋季显白美甲"等
        provider_type: AI 服务商类型，可选值：alibaba_bailian（默认，使用阿里百炼 qwen-plus）、openai_compatible、google_gemini
        model: 模型名称，如果不提供则使用默认值（alibaba_bailian 默认: qwen-plus）
        temperature: 温度参数（0.0-2.0），默认 0.3
        max_output_tokens: 最大输出 token 数，默认 8000
    
    Returns:
        包含生成结果的字典：
        - success: 是否成功
        - outline: 完整的大纲文本
        - pages: 解析后的页面列表，每个页面包含 index、type、content
        - title: 提取的标题（匹配发布接口）
        - content: 提取的正文内容（匹配发布接口，不包含标题和标签）
        - tags: 提取的标签列表（匹配发布接口）
        - error: 错误信息（如果失败）
    """
    try:
        logger.info(f"生成大纲 - 主题: {topic[:50]}..., 服务商: {provider_type}")
        
        # 从配置获取服务商配置
        try:
            provider_config = model_config.get_provider_config(
                provider_type=provider_type,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        # 创建服务并生成大纲
        service = OutlineService(provider_config=provider_config)
        result = service.generate_outline(
            topic=topic
        )
        
        logger.info(f"大纲生成完成 - 成功: {result.get('success')}, 页数: {len(result.get('pages', []))}")
        return result
        
    except Exception as e:
        logger.error(f"生成大纲失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": f"生成大纲时发生异常: {str(e)}"
        }


@mcp.tool()
async def generate_lifestyle_content(
    profession: str,
    age: int,
    gender: str,
    personality: str,
    mood: str,
    scene: Optional[str] = None,
    content_type: Optional[str] = None,
    topic_hint: Optional[str] = None,
    provider_type: str = "alibaba_bailian",
    model: Optional[str] = None,
    temperature: float = 0.8,
    max_output_tokens: int = 2000,
) -> dict:
    """
    生成生活化、随意、带情绪的小红书内容（包含图片生成提示词）
    
    Args:
        profession: 职业，例如"程序员"、"设计师"、"学生"、"自由职业者"
        age: 年龄，例如 25、30
        gender: 性别，例如"男"、"女"、"不指定"
        personality: 性格特点，例如"活泼开朗"、"内敛文艺"、"幽默风趣"、"温柔细腻"
        mood: 情绪倾向，例如"开心"、"感慨"、"治愈"、"吐槽"
        scene: 生活场景（可选），例如"周末日常"、"工作间隙"、"深夜emo"、"旅行途中"
        content_type: 内容类型（可选），例如"日常分享"、"心情记录"、"生活感悟"、"好物推荐"
        topic_hint: 话题提示（可选），例如"今天天气真好"、"工作累了"
        provider_type: AI 服务商类型，可选值：alibaba_bailian（默认，使用阿里百炼 qwen-plus）、openai_compatible、google_gemini
        model: 模型名称，如果不提供则使用默认值（alibaba_bailian 默认: qwen-plus）
        temperature: 温度参数（0.0-2.0），默认 0.8（生活化内容使用更高温度）
        max_output_tokens: 最大输出 token 数，默认 2000
    
    Returns:
        包含生成结果的字典（对齐 outline_service 格式）：
        - success: 是否成功
        - outline: 完整的内容文本（标题+正文+标签）
        - pages: 解析后的页面列表，每个页面包含 index、type、content（对齐 outline_service）
        - title: 生成的标题（1-20字符）
        - content: 生成的正文内容（不超过100字，生活化、随意、带情绪）
        - tags: 标签列表（3-5个）
        - persona_context: 人物设定摘要（用于调试/追溯）
        - error: 错误信息（如果失败）
    """
    try:
        logger.info(f"生成生活化内容 - 职业: {profession}, 年龄: {age}, 性别: {gender}, 性格: {personality}, 心情: {mood}")
        
        # 从配置获取服务商配置
        try:
            provider_config = model_config.get_provider_config(
                provider_type=provider_type,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        # 创建服务并生成内容
        service = LifestyleContentService(provider_config=provider_config)
        result = service.generate_lifestyle_content(
            profession=profession,
            age=age,
            gender=gender,
            personality=personality,
            mood=mood,
            scene=scene,
            content_type=content_type,
            topic_hint=topic_hint,
        )
        
        logger.info(f"生活化内容生成完成 - 成功: {result.get('success')}, 标题长度: {len(result.get('title', ''))}, 正文长度: {len(result.get('content', ''))}, 页数: {len(result.get('pages', []))}")
        return result
        
    except Exception as e:
        logger.error(f"生成生活化内容失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": f"生成生活化内容时发生异常: {str(e)}"
        }


def main():
    """主函数"""
    import sys
    
    # 从环境变量或命令行参数获取配置
    host = "0.0.0.0"
    port = 8004
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    logger.info(f"启动 XHS Content Generator MCP 服务 - {host}:{port}")
    
    try:
        mcp.run(transport="http", host=host, port=port)
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务器运行出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
