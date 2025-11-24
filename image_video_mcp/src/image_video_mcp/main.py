"""
图像和视频生成 MCP 服务主入口
"""

import asyncio
from typing import Optional
from fastmcp import FastMCP
from loguru import logger

from .clients import WanT2IClient

# 创建 MCP 应用实例
mcp = FastMCP("Image Video MCP")


@mcp.tool()
async def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    width: int = 1280,
    height: int = 1280,
    seed: Optional[int] = None,
    max_wait_time: int = 600,
) -> dict:
    """
    使用通义万相生成图像
    
    Args:
        prompt: 图像生成提示词
        negative_prompt: 负面提示词（可选）
        width: 图像宽度，默认 1280
        height: 图像高度，默认 1280
        seed: 随机种子（可选）
        max_wait_time: 最大等待时间（秒），默认 300 秒（5分钟）
    
    Returns:
        包含生成结果的字典，result 字段包含图片 URL 列表
    """
    try:
        size = f"{width}*{height}"
        async with WanT2IClient() as client:
            # 步骤1：创建任务
            result = await client.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                size=size,
                seed=seed,
            )
            
            output = result.get('output', {})
            task_id = output.get('task_id')
            task_status = output.get('task_status', 'PENDING')
            
            if not task_id:
                raise ValueError("未能获取任务 ID")
            
            logger.info(f"任务创建成功: task_id={task_id}, status={task_status}")
            
            # 步骤2：轮询获取结果
            if task_status in ['PENDING', 'RUNNING']:
                max_polls = max_wait_time // 10  # 每10秒查询一次
                poll_count = 0
                
                while poll_count < max_polls:
                    await asyncio.sleep(10)  # 等待10秒
                    poll_count += 1
                    
                    try:
                        status_result = await client.get_task_status(task_id)
                        status_output = status_result.get('output', {})
                        current_status = status_output.get('task_status', 'UNKNOWN')
                        
                        logger.debug(f"轮询 [{poll_count}/{max_polls}]: status={current_status}")
                        
                        if current_status == 'SUCCEEDED':
                            # 提取所有图片 URL
                            results = status_output.get('results', [])
                            urls = [img.get('url') for img in results if img.get('url')]
                            
                            logger.info(f"图像生成成功: 共 {len(urls)} 张图片")
                            return {
                                "success": True,
                                "result": urls,  # 只返回 URL 列表
                                "message": f"成功生成 {len(urls)} 张图片",
                            }
                        elif current_status == 'FAILED':
                            error_msg = status_output.get('message', '任务执行失败')
                            logger.error(f"任务失败: {error_msg}")
                            return {
                                "success": False,
                                "error": error_msg,
                                "message": "图像生成失败",
                            }
                        elif current_status in ['PENDING', 'RUNNING']:
                            continue
                        else:
                            logger.warning(f"未知任务状态: {current_status}")
                            break
                    except Exception as e:
                        logger.warning(f"查询任务状态时出错: {e}")
                        if poll_count < max_polls:
                            continue
                        raise
                
                # 轮询超时
                logger.warning(f"轮询超时: task_id={task_id}")
                return {
                    "success": False,
                    "error": f"任务处理超时（已等待 {max_wait_time} 秒）",
                    "message": "请稍后使用 task_id 手动查询结果",
                    "task_id": task_id,
                }
            elif task_status == 'SUCCEEDED':
                # 如果创建时就已经成功（不太可能，但处理一下）
                results = output.get('results', [])
                urls = [img.get('url') for img in results if img.get('url')]
                return {
                    "success": True,
                    "result": urls,
                    "message": f"成功生成 {len(urls)} 张图片",
                }
            else:
                error_msg = output.get('message', f'任务状态异常: {task_status}')
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "图像生成失败",
                }
                
    except Exception as e:
        logger.error(f"图像生成失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "图像生成失败",
        }


@mcp.tool()
def generate_video(prompt: str, duration: int = 5) -> str:
    """
    生成视频
    
    Args:
        prompt: 视频生成提示词
        duration: 视频时长（秒），默认 5 秒
    
    Returns:
        生成的视频路径或 URL
    """
    # TODO: 实现视频生成逻辑
    return f"Generated video for prompt: {prompt} ({duration}s)"


def main():
    """启动 MCP 服务器"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(
        description="图像和视频生成 MCP 服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8003")),
        help="MCP 服务器端口 (默认: 8003)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("MCP_HOST", "127.0.0.1"),
        help="MCP 服务器主机 (默认: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("图像和视频生成 MCP 服务启动")
    logger.info(f"服务器地址: http://{args.host}:{args.port}")
    logger.info("=" * 60)
    
    # 启动 FastMCP HTTP 服务器
    mcp.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
