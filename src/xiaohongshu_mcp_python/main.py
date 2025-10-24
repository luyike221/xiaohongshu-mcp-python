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
from xiaohongshu_mcp_python.xiaohongshu.login_session_manager import get_session_manager
from xiaohongshu_mcp_python.managers.user_session_manager import UserSessionManager


# 创建 FastMCP 实例
mcp = FastMCP("xiaohongshu-mcp-server")

# 全局配置
GLOBAL_HEADLESS = True  # 默认为无头模式
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
    parser.add_argument("--headless", action="store_true", default=True, help="使用无头模式 (默认: True)")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="使用有头模式")
    
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
async def xiaohongshu_check_login_session(session_id: Optional[str] = None, username: Optional[str] = None) -> dict:
    """
    检查登录会话状态（支持按会话ID或用户名查询）
    
    Args:
        session_id: 登录会话ID（可选）
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        包含登录状态信息的字典
    """
    try:
        user_session_manager = get_user_session_manager()
        
        if session_id:
            # 按会话ID查询（兼容旧接口）
            session_manager = get_session_manager()
            result = await session_manager.check_session(session_id)
            
            if result is None:
                return {
                    "success": False,
                    "status": "not_found",
                    "message": f"会话 {session_id} 不存在或已过期"
                }
            
            status, message, cookies_saved = result
            
            return {
                "success": True,
                "session_id": session_id,
                "status": status,
                "message": message,
                "cookies_saved": cookies_saved,
                "logged_in": status == "logged_in",
                "initializing": status == "initializing"
            }
        else:
            # 按用户名查询
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
async def xiaohongshu_cleanup_login_session(session_id: Optional[str] = None, username: Optional[str] = None) -> dict:
    """
    清理登录会话（支持按会话ID或用户名清理）
    
    Args:
        session_id: 登录会话ID（可选）
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        清理结果
    """
    try:
        user_session_manager = get_user_session_manager()
        
        if session_id:
            # 按会话ID清理（兼容旧接口）
            session_manager = get_session_manager()
            await session_manager.remove_session(session_id)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"会话 {session_id} 已清理"
            }
        else:
            # 按用户名清理
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


if __name__ == "__main__":
    cli_main()