"""
小红书内容生成 MCP 服务主入口
"""
import base64
from typing import Optional, List
from fastmcp import FastMCP
from loguru import logger

from .config import model_config
from .services.outline_service import OutlineService
from .services.vision_service import get_vision_service

# 创建 MCP 应用实例
mcp = FastMCP("XHS Content Generator MCP")


@mcp.tool()
async def generate_outline(
    topic: str,
    provider_type: str = "alibaba_bailian",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_output_tokens: int = 8000,
    images_base64: Optional[List[str]] = None,
    vl_model_provider_type: Optional[str] = None,
    vl_model_api_key: Optional[str] = None,
    vl_model_model: Optional[str] = None,
) -> dict:
    """
    生成小红书图文内容大纲
    
    Args:
        topic: 内容主题，例如"如何在家做拿铁"、"秋季显白美甲"等
        provider_type: AI 服务商类型，可选值：alibaba_bailian（默认，使用阿里百炼 qwen-plus）、openai_compatible、google_gemini
        model: 模型名称，如果不提供则使用默认值（alibaba_bailian 默认: qwen-plus）
        temperature: 温度参数（0.0-2.0），默认 0.3
        max_output_tokens: 最大输出 token 数，默认 8000
        images_base64: 参考图片列表（base64 编码），可选，用于保持风格一致性
        vl_model_provider_type: VL 模型服务商类型（用于图片分析），可选值：openai_compatible（默认，使用 qwen3-vl-plus）、google_gemini
        vl_model_api_key: VL 模型 API Key（可选，如果不提供则尝试使用环境变量 DASHSCOPE_API_KEY 或 VL_MODEL_API_KEY）
        vl_model_model: VL 模型名称（可选，默认使用 qwen3-vl-plus）
    
    Returns:
        包含生成结果的字典：
        - success: 是否成功
        - outline: 完整的大纲文本
        - pages: 解析后的页面列表，每个页面包含 index、type、content
        - has_images: 是否使用了参考图片
        - image_analysis_used: 是否使用了 VL 模型分析图片
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
        
        # 处理参考图片
        images = None
        if images_base64:
            images = []
            for img_b64 in images_base64:
                # 移除可能的 data URL 前缀
                if ',' in img_b64:
                    img_b64 = img_b64.split(',')[1]
                try:
                    images.append(base64.b64decode(img_b64))
                except Exception as e:
                    logger.warning(f"图片解码失败: {e}")
        
        # 判断文本模型是否支持图片
        provider_type = provider_config.get('type', '')
        model_name = provider_config.get('model', '').lower()
        text_model_supports_images = provider_type == 'google_gemini'
        
        # 如果文本模型不支持图片，且有图片，使用 VL 模型分析
        image_description = None
        image_analysis_used = False
        
        if images and len(images) > 0 and not text_model_supports_images:
            # 文本模型不支持图片，需要使用 VL 模型分析
            logger.info(f"文本模型 {provider_type}/{model_name} 不支持图片，使用 VL 模型分析图片...")
            
            # 获取 VL 模型配置
            vl_model_config = None
            if vl_model_api_key or vl_model_provider_type:
                # 使用传入的参数
                vl_model_config = {}
                if vl_model_provider_type:
                    vl_model_config['type'] = vl_model_provider_type
                else:
                    vl_model_config['type'] = 'openai_compatible'  # 默认使用 openai_compatible (qwen3-vl-plus)
                    vl_model_config['base_url'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
                    vl_model_config['model'] = 'qwen3-vl-plus'
                
                if vl_model_api_key:
                    vl_model_config['api_key'] = vl_model_api_key
                else:
                    # 尝试从配置中获取
                    try:
                        vl_config = model_config.get_vl_model_config()
                        if vl_config:
                            vl_model_config = vl_config.copy()
                    except Exception as e:
                        logger.warning(f"获取 VL 模型配置失败: {e}")
                
                if vl_model_model:
                    vl_model_config['model'] = vl_model_model
            else:
                # 尝试从配置中获取 VL 模型配置
                try:
                    vl_model_config = model_config.get_vl_model_config()
                except Exception as e:
                    logger.debug(f"获取 VL 模型配置失败: {e}")
            
            # 使用 VL 模型分析图片
            if vl_model_config:
                try:
                    vision_service = get_vision_service(vl_model_config)
                    image_description = vision_service.analyze_images(
                        images=images,
                        context=f"主题：{topic}"
                    )
                    image_analysis_used = True
                    logger.info("VL 模型分析图片完成")
                    # 清空 images，因为已经转换为文本描述
                    images = None
                except Exception as e:
                    logger.error(f"VL 模型分析图片失败: {e}")
                    return {
                        "success": False,
                        "error": f"VL 模型分析图片失败：{str(e)}\n请检查 VL 模型配置（DASHSCOPE_API_KEY 或 VL_MODEL_API_KEY）"
                    }
            else:
                logger.error("未配置 VL 模型，无法分析图片")
                return {
                    "success": False,
                    "error": "文本模型不支持图片输入，但未配置 VL 模型。\n解决方案：\n1. 设置环境变量 DASHSCOPE_API_KEY（推荐，用于 qwen3-vl-plus）\n2. 或设置环境变量 VL_MODEL_API_KEY\n3. 或在调用时传入 vl_model_api_key 参数"
                }
        
        # 创建服务并生成大纲
        service = OutlineService(provider_config=provider_config)
        result = service.generate_outline(
            topic=topic,
            images=images,  # 如果文本模型支持图片，传入图片；否则为 None
            image_description=image_description  # 如果使用 VL 模型分析，传入描述
        )
        
        # 添加是否使用了 VL 模型分析的标记
        result['image_analysis_used'] = image_analysis_used
        
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
async def generate_content(
    topic: str,
    content_type: str = "note",
) -> dict:
    """
    生成小红书内容（已弃用，请使用 generate_outline）
    
    Args:
        topic: 内容主题
        content_type: 内容类型，可选值：note（笔记）、title（标题）、description（描述）
    
    Returns:
        包含生成内容的字典
    """
    logger.warning("generate_content 已弃用，请使用 generate_outline")
    return {
        "success": False,
        "error": "该工具已弃用，请使用 generate_outline 生成大纲"
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
