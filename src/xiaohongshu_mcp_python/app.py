"""
应用启动文件
整合 MCP 服务器和 HTTP 服务器
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

from loguru import logger

from .http_server import app
from .main import main as mcp_main


class AppServer:
    """应用服务器，整合 MCP 和 HTTP 服务"""
    
    def __init__(self, port: int = 18060, headless: bool = True):
        self.port = port
        self.headless = headless
        self.http_server = None
        self.mcp_server = None
        
    async def start_http_server(self):
        """启动 HTTP 服务器"""
        import uvicorn
        
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
            access_log=True
        )
        
        self.http_server = uvicorn.Server(config)
        logger.info(f"启动 HTTP 服务器: http://0.0.0.0:{self.port}")
        
        # 在后台运行 HTTP 服务器
        await self.http_server.serve()
    
    async def start_mcp_server(self):
        """启动 MCP 服务器"""
        logger.info("启动 MCP 服务器")
        
        # 运行 MCP 服务器
        await mcp_main()
    
    async def start(self):
        """启动所有服务"""
        logger.info("正在启动小红书 MCP 应用服务器...")
        
        # 设置信号处理
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在关闭服务器...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # 并发启动 HTTP 和 MCP 服务器
            await asyncio.gather(
                self.start_http_server(),
                self.start_mcp_server(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"启动服务器失败: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """停止所有服务"""
        logger.info("正在关闭应用服务器...")
        
        if self.http_server:
            self.http_server.should_exit = True
            logger.info("HTTP 服务器已关闭")
        
        if self.mcp_server:
            # MCP 服务器通常通过 stdio 运行，无需特殊关闭
            logger.info("MCP 服务器已关闭")
        
        logger.info("应用服务器已关闭")


def setup_logging(debug: bool = False):
    """设置日志配置"""
    log_level = "DEBUG" if debug else "INFO"
    
    # 配置 loguru
    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 配置标准 logging（用于 FastAPI 和其他库）
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="小红书 MCP 应用服务器")
    parser.add_argument(
        "--port",
        type=int,
        default=18060,
        help="HTTP 服务器端口 (默认: 18060)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="是否使用无头浏览器模式 (默认: True)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    parser.add_argument(
        "--mcp-only",
        action="store_true",
        help="仅启动 MCP 服务器"
    )
    parser.add_argument(
        "--http-only",
        action="store_true",
        help="仅启动 HTTP 服务器"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.debug)
    
    # 创建应用服务器
    app_server = AppServer(port=args.port, headless=args.headless)
    
    try:
        if args.mcp_only:
            # 仅启动 MCP 服务器
            logger.info("仅启动 MCP 服务器模式")
            asyncio.run(app_server.start_mcp_server())
        elif args.http_only:
            # 仅启动 HTTP 服务器
            logger.info("仅启动 HTTP 服务器模式")
            asyncio.run(app_server.start_http_server())
        else:
            # 启动完整服务
            logger.info("启动完整服务模式")
            asyncio.run(app_server.start())
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭...")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()