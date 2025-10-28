"""
小红书 MCP 服务器主程序入口
使用 FastMCP 框架实现
"""

import asyncio
import argparse
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP, Context
from loguru import logger

from xiaohongshu_mcp_python.storage.cookie_storage import CookieStorage
from xiaohongshu_mcp_python.browser.browser_manager import BrowserManager
from xiaohongshu_mcp_python.xiaohongshu.simple_login_manager import SimpleLoginManager
from xiaohongshu_mcp_python.xiaohongshu.login_types import LoginStatus
from xiaohongshu_mcp_python.managers.user_session_manager import UserSessionManager


# 创建 FastMCP 实例
mcp = FastMCP("xiaohongshu-mcp-server")

# 全局配置
GLOBAL_HEADLESS = False  # 默认为有头模式
GLOBAL_USER = "luyike"  # 当前用户名

# 全局用户会话管理器实例
_user_session_manager = None

def get_user_session_manager() -> UserSessionManager:
    """获取全局用户会话管理器实例"""
    global _user_session_manager
    if _user_session_manager is None:
        _user_session_manager = UserSessionManager()
    return _user_session_manager




def cli_main():
    """命令行入口"""
    global GLOBAL_HEADLESS
    
    parser = argparse.ArgumentParser(description="小红书 MCP 服务器 (HTTP 模式)")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP 服务器主机地址")
    parser.add_argument("--port", type=int, default=8000, help="HTTP 服务器端口")
    parser.add_argument("--headless", action="store_true", default=False, help="使用无头模式")
    
    args = parser.parse_args()
    
    # 设置全局headless配置
    GLOBAL_HEADLESS = args.headless
    
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level=args.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}"
    )
    
    headless_mode = "无头模式" if GLOBAL_HEADLESS else "有头模式"
    logger.info(f"启动小红书 MCP 服务器 (HTTP 模式) - {args.host}:{args.port} - {headless_mode}")
    
    # 运行 FastMCP 服务器 (HTTP 模式)
    mcp.run(transport="http", host=args.host, port=args.port)


@mcp.tool
async def xiaohongshu_start_login_session(headless: bool = False, fresh: bool = False, username: Optional[str] = None) -> dict:
    """
    启动小红书登录会话（基于用户的会话管理）
    
    Args:
        headless: 是否使用无头模式，默认False（显示浏览器界面）
        fresh: 是否强制创建新会话，默认False（复用现有会话）
        username: 用户名，如果不提供则使用全局用户
        
    Returns:
        包含会话ID和状态的字典
    """
    try:
        # 使用提供的用户名或全局用户名
        current_user = username or GLOBAL_USER
        logger.info(f"为用户 {current_user} 启动登录会话，headless={headless}, fresh={fresh}")
        
        user_session_manager = get_user_session_manager()
        
        if fresh:
            # 强制创建新会话，先清理现有会话
            await user_session_manager.cleanup_user_session(current_user)
        
        # 获取或创建用户会话
        result = await user_session_manager.get_or_create_session(
            username=current_user,
            headless=headless or GLOBAL_HEADLESS
        )
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "message": f"为用户 {current_user} 创建会话失败"
            }
        
        return {
            "success": True,
            "session_id": result["session_id"],
            "status": result["status"],
            "username": current_user,
            "is_new_session": result["is_new"],
            "message": result["message"],
            "instructions": "请使用 xiaohongshu_check_login_session 工具定期查询登录状态"
        }
        
    except Exception as e:
        logger.error(f"启动登录会话失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "启动登录会话失败"
        }


@mcp.tool
async def xiaohongshu_check_login_session(username: Optional[str] = None) -> dict:
    """
    检查登录会话状态（基于用户名查询）
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        包含登录状态信息的字典
    """
    try:
        user_session_manager = get_user_session_manager()
        current_user = username or GLOBAL_USER
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        
        if not user_session_status:
            return {
                "success": False,
                "status": "no_session",
                "username": current_user,
                "message": f"用户 {current_user} 没有活跃会话"
            }
        
        return {
            "success": True,
            "session_id": user_session_status["session_id"],
            "username": current_user,
            "status": user_session_status["status"],
            "message": f"用户 {current_user} 的会话状态: {user_session_status['status']}",
            "logged_in": user_session_status["status"] == "logged_in",
            "initializing": user_session_status["status"] == "initializing",
            "user_info": user_session_status["user_info"],
            "cookies_saved": user_session_status["cookies_saved"]
        }
        
    except Exception as e:
        logger.error(f"检查登录会话失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "检查登录会话失败"
        }


@mcp.tool
async def xiaohongshu_cleanup_login_session(username: Optional[str] = None) -> dict:
    """
    清理登录会话（基于用户名）
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        清理结果
    """
    try:
        user_session_manager = get_user_session_manager()
        current_user = username or GLOBAL_USER
        success = await user_session_manager.cleanup_user_session(current_user)
        
        return {
            "success": success,
            "username": current_user,
            "message": f"用户 {current_user} 的会话已清理" if success else f"清理用户 {current_user} 的会话失败"
        }
        
    except Exception as e:
        logger.error(f"清理登录会话失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "清理登录会话失败"
        }


@mcp.tool
async def xiaohongshu_publish_content(
    title: str,
    content: str,
    images: list[str],
    tags: Optional[list[str]] = None,
    username: Optional[str] = None,
    context: Optional[Context] = None
) -> dict:
    """
    发布小红书图文内容
    
    Args:
        title: 内容标题（最多20个中文字或英文单词）
        content: 正文内容，不包含以#开头的标签内容
        images: 图片路径列表（至少需要1张图片）。支持HTTP/HTTPS图片链接或本地图片绝对路径
        tags: 话题标签列表（可选），如 ["美食", "旅行", "生活"]
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        发布结果
    """
    try:
        from .service import XiaohongshuService
        from .types import PublishImageContent
        from .browser import BrowserManager
        
        current_user = username or GLOBAL_USER
        user_session_manager = get_user_session_manager()
        
        # 发送进度通知：开始检查登录状态
        if context:
            await context.report_progress(
                progress=10,
                total=100
            )
        
        # 检查用户会话状态
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        if not user_session_status or user_session_status["status"] != "logged_in":
            return {
                "success": False,
                "error": "用户未登录",
                "message": f"用户 {current_user} 未登录，请先使用 xiaohongshu_start_login_session 登录"
            }
        
        # 发送进度通知：开始启动浏览器
        if context:
            await context.report_progress(
                progress=20,
                total=100
            )
        
        # 创建浏览器管理器和服务实例
        browser_manager = BrowserManager()
        await browser_manager.start()
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 发送进度通知：开始发布内容
            if context:
                await context.report_progress(
                    progress=40,
                    total=100
                )
            
            # 构建发布请求
            publish_request = PublishImageContent(
                title=title,
                content=content,
                images=images,
                tags=tags or []
            )
            
            # 执行发布
            result = await service.publish_content(publish_request, current_user, context)
            
            # 发送进度通知：发布完成
            if context:
                await context.report_progress(
                    progress=100,
                    total=100
                )
            
            return {
                "success": result.success,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": result.message if hasattr(result, 'message') else "内容发布完成"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"发布内容失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "发布内容失败"
        }


@mcp.tool
async def xiaohongshu_publish_video(
    title: str,
    content: str,
    video: str,
    tags: Optional[list[str]] = None,
    username: Optional[str] = None,
    context: Optional[Context] = None
) -> dict:
    """
    发布小红书视频内容
    
    Args:
        title: 视频标题（最多20个中文字或英文单词）
        content: 正文内容，不包含以#开头的标签内容
        video: 视频文件路径。支持本地视频文件绝对路径
        tags: 话题标签列表（可选），如 ["美食", "旅行", "生活"]
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        发布结果
    """
    try:
        from .service import XiaohongshuService
        from .types import PublishVideoContent
        from .browser import BrowserManager
        
        current_user = username or GLOBAL_USER
        user_session_manager = get_user_session_manager()
        
        # 发送进度通知：开始检查登录状态
        if context:
            await context.report_progress(
                progress=10,
                total=100
            )
        
        # 检查用户会话状态
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        if not user_session_status or user_session_status["status"] != "logged_in":
            return {
                "success": False,
                "error": "用户未登录",
                "message": f"用户 {current_user} 未登录，请先使用 xiaohongshu_start_login_session 登录"
            }
        
        # 发送进度通知：开始启动浏览器
        if context:
            await context.report_progress(
                progress=20,
                total=100
            )
        
        # 创建浏览器管理器和服务实例
        browser_manager = BrowserManager()
        await browser_manager.start()
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 发送进度通知：开始发布视频
            if context:
                await context.report_progress(
                    progress=40,
                    total=100
                )
            
            # 构建发布请求
            publish_request = PublishVideoContent(
                title=title,
                video_path=video,
                content=content,
                tags=tags or []
            )
            
            # 执行发布
            result = await service.publish_video(publish_request, current_user, context)
            
            # 发送进度通知：发布完成
            if context:
                await context.report_progress(
                    progress=100,
                    total=100
                )
            
            return {
                "success": result.success,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": result.message if hasattr(result, 'message') else "视频发布完成"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"发布视频失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "发布视频失败"
        }


@mcp.tool
async def xiaohongshu_search_feeds(
    keyword: str,
    username: Optional[str] = None
) -> dict:
    """
    搜索小红书内容
    
    Args:
        keyword: 搜索关键词
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        搜索结果
    """
    try:
        from .service import XiaohongshuService
        from .browser import BrowserManager
        
        current_user = username or GLOBAL_USER
        user_session_manager = get_user_session_manager()
        
        # 检查用户会话状态
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        if not user_session_status or user_session_status["status"] != "logged_in":
            return {
                "success": False,
                "error": "用户未登录",
                "message": f"用户 {current_user} 未登录，请先使用 xiaohongshu_start_login_session 登录"
            }
        
        # 创建浏览器管理器和服务实例
        browser_manager = BrowserManager()
        await browser_manager.start()
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 执行搜索
            result = await service.search_content(keyword, username=current_user)
            
            return {
                "success": True,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": f"搜索关键词 '{keyword}' 成功"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"搜索内容失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "搜索内容失败"
        }


@mcp.tool
async def xiaohongshu_get_feeds(
    username: Optional[str] = None
) -> dict:
    """
    获取推荐内容列表
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        推荐内容列表
    """
    try:
        from .service import XiaohongshuService
        from .browser import BrowserManager
        
        current_user = username or GLOBAL_USER
        user_session_manager = get_user_session_manager()
        
        # 检查用户会话状态
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        if not user_session_status or user_session_status["status"] != "logged_in":
            return {
                "success": False,
                "error": "用户未登录",
                "message": f"用户 {current_user} 未登录，请先使用 xiaohongshu_start_login_session 登录"
            }
        
        # 创建浏览器管理器和服务实例
        browser_manager = BrowserManager()
        await browser_manager.start()
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 获取推荐内容
            result = await service.get_feeds_list(username=current_user)
            
            return {
                "success": True,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": "获取推荐内容成功"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"获取推荐内容失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取推荐内容失败"
        }


@mcp.tool
async def xiaohongshu_list_feeds(
    username: Optional[str] = None
) -> dict:
    """
    获取首页推荐Feed列表（使用__INITIAL_STATE__方法，无需登录）
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        首页推荐Feed列表
    """
    try:
        from .service import XiaohongshuService
        from .browser import BrowserManager
        
        current_user = username or GLOBAL_USER
        
        # 创建浏览器管理器和服务实例
        browser_manager = BrowserManager()
        await browser_manager.start()
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 获取首页推荐Feed列表
            result = await service.list_feeds(username=current_user)
            
            return {
                "success": result.success,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": "获取首页推荐Feed成功" if result.success else result.error
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"获取首页推荐Feed失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取首页推荐Feed失败"
        }


@mcp.tool
async def xiaohongshu_get_user_profile(
    user_id: str,
    xsec_token: str,
    username: Optional[str] = None
) -> dict:
    """
    获取小红书用户主页信息
    
    Args:
        user_id: 小红书用户ID，从Feed列表获取
        xsec_token: 访问令牌，从Feed列表的xsecToken字段获取
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        用户主页信息
    """
    try:
        from .service import XiaohongshuService
        from .browser import BrowserManager
        
        current_user = username or GLOBAL_USER
        user_session_manager = get_user_session_manager()
        
        # 检查用户会话状态
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        if not user_session_status or user_session_status["status"] != "logged_in":
            return {
                "success": False,
                "error": "用户未登录",
                "message": f"用户 {current_user} 未登录，请先使用 xiaohongshu_start_login_session 登录"
            }
        
        # 创建浏览器管理器和服务实例
        browser_manager = BrowserManager()
        await browser_manager.start()
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 获取用户资料
            result = await service.get_user_profile(user_id, xsec_token, username=current_user)
            
            return {
                "success": True,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": f"获取用户 {user_id} 的资料成功"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取用户资料失败"
        }


@mcp.tool
async def xiaohongshu_get_feed_detail(
    feed_id: str,
    xsec_token: str = "",
    username: Optional[str] = None
) -> dict:
    """
    获取小红书笔记详情
    
    Args:
        feed_id: 笔记ID
        xsec_token: xsec_token参数（可选，用于访问特定笔记）
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        笔记详情信息，包含笔记内容、互动数据和评论
    """
    # 参数验证
    if not feed_id or not feed_id.strip():
        return {
            "success": False,
            "error": "参数错误",
            "message": "feed_id 不能为空"
        }
    
    try:
        from .service import XiaohongshuService
        from .browser import BrowserManager
        
        current_user = username or GLOBAL_USER
        user_session_manager = get_user_session_manager()
        
        # 检查用户会话状态
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        if not user_session_status or user_session_status["status"] != "logged_in":
            return {
                "success": False,
                "error": "用户未登录",
                "message": f"用户 {current_user} 未登录，请先使用 xiaohongshu_start_login_session 登录"
            }
        
        # 创建浏览器管理器和服务实例
        browser_manager = BrowserManager()
        await browser_manager.start()
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 获取笔记详情
            xsec_token_param = xsec_token if xsec_token else None
            result = await service.get_feed_detail(feed_id, xsec_token_param, username=current_user)
            
            return {
                "success": True,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": f"获取笔记 {feed_id} 的详情成功"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"获取笔记详情失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取笔记详情失败"
        }


def main():
    """主函数，用于外部调用"""
    cli_main()


if __name__ == "__main__":
    cli_main()