"""小红书浏览器自动化MCP服务类

基于 LangChain 官方 MCP 适配器 (langchain-mcp-adapters)
特点:
- 官方支持,稳定可靠
- 自动工具转换
- 支持 HTTP 传输方式
- 仅封装 MCP 调用,不创建 Agent

使用示例:
    # 方式1: 直接使用
    service = XiaohongshuBrowserMCPService()
    result = await service.publish_content(
        title="测试标题",
        content="测试内容",
        images=["https://example.com/image.jpg"]
    )
    
    # 方式2: 使用异步上下文管理器
    async with XiaohongshuBrowserMCPService() as service:
        result = await service.publish_content(
            title="测试标题",
            content="测试内容",
            images=["https://example.com/image.jpg"]
        )
    
    # 方式3: 使用工厂函数
    service = await create_xiaohongshu_browser_mcp_service()
    result = await service.publish_content(...)
"""

import json
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient

from .....config import mcp_config
from ....tools.logging import get_logger

logger = get_logger(__name__)


class XiaohongshuBrowserMCPService:
    """小红书浏览器自动化MCP服务类
    
    职责：
    - 连接小红书浏览器自动化MCP服务
    - 提供登录管理功能
    - 提供内容发布功能（图文/视频）
    - 提供内容浏览功能（搜索/列表/详情）
    - 提供用户信息查询功能
    - 封装MCP工具调用，提供便捷的接口
    """

    def __init__(
        self,
        mcp_url: Optional[str] = None,
        mcp_transport: Optional[str] = None,
    ):
        """初始化小红书浏览器自动化MCP服务
        
        Args:
            mcp_url: MCP服务地址，默认从配置读取
            mcp_transport: MCP传输方式，默认从配置读取
        """
        self.mcp_url = mcp_url or mcp_config.xiaohongshu_mcp_url
        self.mcp_transport = mcp_transport or mcp_config.xiaohongshu_mcp_transport
        self.logger = logger
        
        # 延迟初始化的组件
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._tools: Dict[str, Any] = {}
        self._initialized = False

    async def _initialize(self):
        """初始化MCP客户端（懒加载）
        
        使用 LangChain 官方 MCP 适配器连接 MCP 服务
        """
        if self._initialized:
            return
        
        try:
            self.logger.info(
                "Initializing Xiaohongshu Browser MCP Service",
                mcp_url=self.mcp_url,
                transport=self.mcp_transport
            )
            
            # 1. 创建 MCP 客户端,配置服务器
            # 使用 MultiServerMCPClient 支持多服务器管理
            self._mcp_client = MultiServerMCPClient({
                "xiaohongshu_browser": {
                    "url": self.mcp_url,
                    "transport": self.mcp_transport,
                }
            })
            
            # 2. 获取所有工具(自动从服务器加载)
            self.logger.info("Fetching MCP tools...")
            tools = await self._mcp_client.get_tools()
            self.logger.info(
                "MCP tools fetched",
                tool_count=len(tools),
                tool_names=[tool.name for tool in tools]
            )
            
            # 3. 缓存所有工具
            for tool in tools:
                self._tools[tool.name] = tool
            
            self._initialized = True
            self.logger.info("Xiaohongshu Browser MCP Service initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Xiaohongshu Browser MCP Service",
                error=str(e),
                mcp_url=self.mcp_url
            )
            raise

    def _parse_tool_result(self, raw_result: Any) -> Dict[str, Any]:
        """解析工具返回结果
        
        LangChain MCP 适配器的工具可能返回：
        - 字符串（JSON 字符串）
        - 字典
        - 对象（有 content 属性）
        
        Args:
            raw_result: 工具原始返回结果
        
        Returns:
            解析后的字典结果
        """
        # 如果已经是字典，直接返回
        if isinstance(raw_result, dict):
            return raw_result
        
        # 如果是字符串，尝试解析为 JSON
        if isinstance(raw_result, str):
            try:
                # 尝试解析 JSON
                parsed = json.loads(raw_result)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    # 如果不是字典，包装为字典
                    return {"success": True, "result": parsed}
            except json.JSONDecodeError:
                # 如果不是 JSON，可能是普通字符串
                # 检查是否包含 JSON 结构
                if raw_result.strip().startswith("{") or raw_result.strip().startswith("["):
                    # 可能是格式化的 JSON，尝试再次解析
                    try:
                        parsed = json.loads(raw_result.strip())
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        pass
                # 无法解析，返回错误
                return {
                    "success": False,
                    "error": f"工具返回了无法解析的字符串: {raw_result[:200]}"
                }
        
        # 如果是对象，尝试提取 content 属性
        if hasattr(raw_result, "content"):
            content = raw_result.content
            if isinstance(content, str):
                return self._parse_tool_result(content)
            elif isinstance(content, dict):
                return content
            else:
                return {"success": True, "result": content}
        
        # 如果是对象，尝试转换为字典
        if hasattr(raw_result, "__dict__"):
            try:
                return dict(raw_result.__dict__)
            except Exception:
                pass
        
        # 其他情况，包装为字典
        return {
            "success": False,
            "error": f"工具返回了无法处理的类型: {type(raw_result).__name__}",
            "raw_result": str(raw_result)
        }

    def _get_tool(self, tool_name: str):
        """获取工具实例
        
        Args:
            tool_name: 工具名称
        
        Returns:
            工具实例
        
        Raises:
            ValueError: 如果工具不存在
        """
        if not self._initialized:
            raise RuntimeError("Service not initialized. Call _initialize() first.")
        
        tool = self._tools.get(tool_name)
        if not tool:
            available_tools = list(self._tools.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )
        return tool

    async def start_login_session(
        self,
        headless: bool = False,
        fresh: bool = False,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """启动小红书登录会话
        
        Args:
            headless: 是否使用无头模式，默认False
            fresh: 是否强制创建新会话，默认False
            username: 用户名（可选）
        
        Returns:
            包含会话ID和状态的字典
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_start_login_session")
        
        try:
            params = {
                "headless": headless,
                "fresh": fresh,
            }
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to start login session: {e}")
            return {
                "success": False,
                "error": f"启动登录会话时发生异常: {str(e)}"
            }

    async def check_login_session(
        self,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """检查登录状态
        
        Args:
            username: 用户名（可选）
        
        Returns:
            包含登录状态的字典
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_check_login_session")
        
        try:
            params = {}
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to check login session: {e}")
            return {
                "success": False,
                "error": f"检查登录状态时发生异常: {str(e)}"
            }

    async def cleanup_login_session(
        self,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """清理登录会话
        
        Args:
            username: 用户名（可选）
        
        Returns:
            包含清理结果的字典
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_cleanup_login_session")
        
        try:
            params = {}
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to cleanup login session: {e}")
            return {
                "success": False,
                "error": f"清理登录会话时发生异常: {str(e)}"
            }

    async def publish_content(
        self,
        title: str,
        content: str,
        images: List[str],
        tags: Optional[List[str]] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发布图文内容
        
        Args:
            title: 内容标题（最多20个中文字或英文单词）
            content: 正文内容，不包含以#开头的标签内容
            images: 图片路径数组，支持HTTP/HTTPS图片链接或本地图片绝对路径（至少需要1张图片）
            tags: 话题标签数组，如 ["美食", "旅行", "生活"]，标签中的 # 号会自动移除
            username: 用户名（可选）
        
        Returns:
            发布结果
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_publish_content")
        
        try:
            params = {
                "title": title,
                "content": content,
                "images": images or [],
            }
            if tags:
                params["tags"] = tags
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to publish content: {e}")
            return {
                "success": False,
                "error": f"发布内容时发生异常: {str(e)}"
            }

    async def publish_video(
        self,
        title: str,
        content: str,
        video: str,
        tags: Optional[List[str]] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发布视频内容
        
        Args:
            title: 视频标题（最多20个中文字或英文单词）
            content: 正文内容，不包含以#开头的标签内容
            video: 视频文件路径，支持本地视频文件绝对路径
            tags: 话题标签数组，如 ["美食", "旅行", "生活"]，标签中的 # 号会自动移除
            username: 用户名（可选）
        
        Returns:
            发布结果
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_publish_video")
        
        try:
            params = {
                "title": title,
                "content": content,
                "video": video,
            }
            if tags:
                params["tags"] = tags
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to publish video: {e}")
            return {
                "success": False,
                "error": f"发布视频时发生异常: {str(e)}"
            }

    async def search_feeds(
        self,
        keyword: str,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """搜索小红书内容
        
        Args:
            keyword: 搜索关键词
            username: 用户名（可选）
        
        Returns:
            搜索结果
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_search_feeds")
        
        try:
            params = {
                "keyword": keyword,
            }
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to search feeds: {e}")
            return {
                "success": False,
                "error": f"搜索内容时发生异常: {str(e)}"
            }

    async def get_feeds(
        self,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取推荐列表
        
        Args:
            username: 用户名（可选）
        
        Returns:
            推荐列表
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_get_feeds")
        
        try:
            params = {}
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to get feeds: {e}")
            return {
                "success": False,
                "error": f"获取推荐列表时发生异常: {str(e)}"
            }

    async def list_feeds(
        self,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取用户发布的内容列表
        
        Args:
            username: 用户名（可选）
        
        Returns:
            内容列表
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_list_feeds")
        
        try:
            params = {}
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to list feeds: {e}")
            return {
                "success": False,
                "error": f"获取内容列表时发生异常: {str(e)}"
            }

    async def get_user_profile(
        self,
        user_id: str,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取用户主页
        
        Args:
            user_id: 用户ID
            username: 用户名（可选，用于登录）
        
        Returns:
            用户主页信息
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_get_user_profile")
        
        try:
            params = {
                "user_id": user_id,
            }
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to get user profile: {e}")
            return {
                "success": False,
                "error": f"获取用户主页时发生异常: {str(e)}"
            }

    async def get_feed_detail(
        self,
        feed_id: str,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取笔记详情
        
        Args:
            feed_id: 笔记ID
            username: 用户名（可选，用于登录）
        
        Returns:
            笔记详情
        """
        await self._initialize()
        
        tool = self._get_tool("xiaohongshu_get_feed_detail")
        
        try:
            params = {
                "feed_id": feed_id,
            }
            if username:
                params["username"] = username
            
            raw_result = await tool.ainvoke(params)
            return self._parse_tool_result(raw_result)
        except Exception as e:
            self.logger.error(f"Failed to get feed detail: {e}")
            return {
                "success": False,
                "error": f"获取笔记详情时发生异常: {str(e)}"
            }

    async def close(self):
        """关闭MCP客户端连接
        
        清理资源,关闭与 MCP 服务器的连接
        """
        if self._mcp_client:
            # MultiServerMCPClient 会自动清理资源
            # 这里只需要重置状态
            self._mcp_client = None
            self._tools = {}
            self._initialized = False
            self.logger.info("Xiaohongshu Browser MCP Service closed")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 便捷函数：创建服务实例
async def create_xiaohongshu_browser_mcp_service(
    mcp_url: Optional[str] = None,
    mcp_transport: Optional[str] = None,
) -> XiaohongshuBrowserMCPService:
    """创建并初始化小红书浏览器自动化MCP服务（工厂函数）
    
    Args:
        mcp_url: MCP服务地址
        mcp_transport: MCP传输方式
    
    Returns:
        已初始化的XiaohongshuBrowserMCPService实例
    """
    service = XiaohongshuBrowserMCPService(
        mcp_url=mcp_url,
        mcp_transport=mcp_transport,
    )
    await service._initialize()
    return service

