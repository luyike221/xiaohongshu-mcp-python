"""
小红书内容生成 MCP 服务主入口
"""
from typing import Optional
from fastmcp import FastMCP
from loguru import logger

from .config import model_config
from .services.outline_service import OutlineService

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
