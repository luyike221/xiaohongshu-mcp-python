"""
小红书内容生成 MCP 服务主入口
"""

import asyncio
from fastmcp import FastMCP
from loguru import logger

# 创建 MCP 应用实例
mcp = FastMCP("XHS Content Generator MCP")


@mcp.tool()
async def generate_content(
    topic: str,
    content_type: str = "note",
) -> dict:
    """
    生成小红书内容
    
    Args:
        topic: 内容主题
        content_type: 内容类型，可选值：note（笔记）、title（标题）、description（描述）
    
    Returns:
        包含生成内容的字典
    """
    try:
        logger.info(f"生成内容 - 主题: {topic}, 类型: {content_type}")
        
        # TODO: 实现内容生成逻辑
        result = {
            "topic": topic,
            "content_type": content_type,
            "content": f"这是关于 {topic} 的{content_type}内容（待实现）",
        }
        
        return result
    except Exception as e:
        logger.error(f"生成内容失败: {e}")
        return {
            "error": str(e),
        }


def main():
    """主函数"""
    import sys
    
    # 从环境变量或命令行参数获取配置
    host = "0.0.0.0"
    port = 8000
    
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

