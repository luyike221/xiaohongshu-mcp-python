"""
小红书 MCP 服务器主程序入口
使用 FastMCP 框架实现

职责：
- CLI 参数解析
- 日志系统初始化
- MCP 服务器启动
"""

import argparse
import os
from typing import Optional
from loguru import logger

from .config import settings
from .utils.logger_config import setup_logger
from .server.mcp_tools import mcp  # 导入 MCP 实例和所有工具函数（通过导入自动注册）

# 全局配置（从 settings 读取）
GLOBAL_HEADLESS = settings.BROWSER_HEADLESS
GLOBAL_USER = settings.GLOBAL_USER


def cli_main():
    """命令行入口"""
    global GLOBAL_HEADLESS
    
    parser = argparse.ArgumentParser(
        description="小红书 MCP 服务器 (HTTP 模式)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
环境配置:
  当前环境: {settings.ENV}
  浏览器模式: {'无头' if settings.BROWSER_HEADLESS else '有头'}
  日志级别: {settings.LOG_LEVEL}
  
  可以通过环境变量或 .env 文件配置:
  - ENV: development/production
  - BROWSER_HEADLESS: true/false
  - LOG_LEVEL: DEBUG/INFO/WARNING/ERROR
        """
    )
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        default=None,
        help=f"运行环境 (默认: {settings.ENV})"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help=f"日志级别 (默认: {settings.LOG_LEVEL})"
    )
    parser.add_argument(
        "--host",
        default=None,
        help=f"HTTP 服务器主机地址 (默认: {settings.SERVER_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"HTTP 服务器端口 (默认: {settings.SERVER_PORT})"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=None,
        help="使用无头模式（覆盖环境配置）"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="使用有头模式（覆盖环境配置）"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="日志文件路径（如果设置，日志会同时写入文件）"
    )
    
    args = parser.parse_args()
    
    # 处理环境参数
    if args.env:
        # 动态更新环境配置
        settings.ENV = args.env
        settings.IS_DEVELOPMENT = args.env == "development"
        settings.IS_PRODUCTION = args.env == "production"
        # 如果之前使用默认值，重新计算 headless 模式
        _headless_env = os.getenv("BROWSER_HEADLESS", "").strip().lower()
        if not _headless_env:
            settings.BROWSER_HEADLESS = settings.IS_PRODUCTION
    
    # 处理 headless 参数（命令行参数优先级最高）
    if args.headless:
        GLOBAL_HEADLESS = True
    elif args.no_headless:
        GLOBAL_HEADLESS = False
    else:
        GLOBAL_HEADLESS = settings.BROWSER_HEADLESS
    
    # 配置日志
    setup_logger(args.log_level, args.log_file)
    
    # 获取服务器配置
    host = args.host or settings.SERVER_HOST
    port = args.port or settings.SERVER_PORT
    
    # 输出配置信息
    env_mode = "开发环境" if settings.IS_DEVELOPMENT else "生产环境"
    headless_mode = "无头模式" if GLOBAL_HEADLESS else "有头模式"
    
    logger.info("=" * 60)
    logger.info(f"小红书 MCP 服务器启动")
    logger.info(f"运行环境: {env_mode} ({settings.ENV})")
    logger.info(f"浏览器模式: {headless_mode}")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")
    logger.info(f"服务器地址: http://{host}:{port}")
    logger.info(f"默认用户: {settings.GLOBAL_USER}")
    logger.info("=" * 60)
    
    # 运行 FastMCP 服务器 (HTTP 模式)
    mcp.run(transport="http", host=host, port=port)


def main():
    """主函数，用于外部调用"""
    cli_main()


if __name__ == "__main__":
    cli_main()
