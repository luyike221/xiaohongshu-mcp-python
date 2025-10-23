"""
小红书 MCP 服务器主程序入口
使用 FastMCP 框架实现
"""

import asyncio
import argparse
from pathlib import Path
from fastmcp import FastMCP
from loguru import logger

from xiaohongshu_mcp_python.storage.cookie_storage import CookieStorage
from xiaohongshu_mcp_python.browser.browser_manager import BrowserManager
from xiaohongshu_mcp_python.xiaohongshu.login_manager import LoginManager
from xiaohongshu_mcp_python.xiaohongshu.login_types import LoginStatus


# 创建 FastMCP 实例
mcp = FastMCP("xiaohongshu-mcp-server")


@mcp.tool
async def xiaohongshu_check_login_status() -> dict:
    """检查小红书登录状态"""
    try:
        # 初始化组件
        cookie_storage = CookieStorage("cookies.json")
        browser_manager = BrowserManager(browser_type="chromium", headless=True)
        login_manager = LoginManager(browser_manager, cookie_storage)
        
        # 检查登录状态
        await login_manager.initialize()
        status = await login_manager.check_login_status()
        
        # 清理资源
        await login_manager.cleanup()
        
        # 根据LoginStatus枚举返回结果
        is_logged_in = status == LoginStatus.LOGGED_IN
        status_message = {
            LoginStatus.LOGGED_IN: "已登录",
            LoginStatus.NOT_LOGGED_IN: "未登录", 
            LoginStatus.LOGIN_EXPIRED: "登录已过期",
            LoginStatus.UNKNOWN: "状态未知"
        }.get(status, "未知状态")
        
        return {
            "is_logged_in": is_logged_in,
            "status": status.value,
            "message": status_message
        }
    except Exception as e:
        logger.error(f"检查登录状态失败: {e}")
        return {
            "is_logged_in": False,
            "status": "unknown",
            "message": f"检查失败: {str(e)}"
        }


@mcp.tool
async def xiaohongshu_login() -> dict:
    """完整的小红书登录流程"""
    try:
        # 初始化组件
        cookie_storage = CookieStorage("cookies.json")
        browser_manager = BrowserManager(browser_type="chromium", headless=False)
        login_manager = LoginManager(browser_manager, cookie_storage)
        
        # 执行登录流程
        await login_manager.initialize()
        success = await login_manager.login()
        
        # 清理资源
        await login_manager.cleanup()
        
        if success:
            return {
                "success": True,
                "message": "登录成功"
            }
        else:
            return {
                "success": False,
                "message": "登录失败"
            }
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return {
            "success": False,
            "message": f"登录失败: {str(e)}"
        }


@mcp.tool
async def xiaohongshu_logout() -> dict:
    """小红书登出"""
    try:
        # 初始化组件
        cookie_storage = CookieStorage("cookies.json")
        browser_manager = BrowserManager(browser_type="chromium", headless=True)
        login_manager = LoginManager(browser_manager, cookie_storage)
        
        # 执行登出
        await login_manager.initialize()
        success = await login_manager.logout()
        
        # 清理资源
        await login_manager.cleanup()
        
        if success:
            return {
                "success": True,
                "message": "登出成功"
            }
        else:
            return {
                "success": False,
                "message": "登出失败"
            }
    except Exception as e:
        logger.error(f"登出失败: {e}")
        return {
            "success": False,
            "message": f"登出失败: {str(e)}"
        }


def cli_main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="小红书 MCP 服务器 (HTTP 模式)")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP 服务器主机地址")
    parser.add_argument("--port", type=int, default=8000, help="HTTP 服务器端口")
    
    args = parser.parse_args()
    
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level=args.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}"
    )
    
    logger.info(f"启动小红书 MCP 服务器 (HTTP 模式) - {args.host}:{args.port}")
    # 运行 FastMCP 服务器 (HTTP 模式)
    mcp.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    cli_main()