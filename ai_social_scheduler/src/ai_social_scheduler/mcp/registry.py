"""MCP工具统一注册中心

职责：
1. 连接所有MCP服务
2. 将MCP工具转换为LangChain Tools
3. 统一管理工具生命周期
4. 提供工具分类和查询

架构特点：
- 单例模式：全局唯一实例
- 懒加载：按需初始化
- 分类管理：按功能分类工具
- 统一接口：屏蔽MCP底层细节
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from ..config import mcp_config
from ..tools.logging import get_logger

logger = get_logger(__name__)


class MCPToolRegistry:
    """MCP工具注册中心（单例）
    
    使用方式：
        # 初始化
        await mcp_registry.initialize()
        
        # 获取工具
        content_tools = mcp_registry.get_tools_by_category("content")
        
        # 获取单个工具
        tool = mcp_registry.get_tool("generate_outline")
    """
    
    _instance: Optional["MCPToolRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance
    
    def _init_state(self):
        """初始化实例状态"""
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._tools: Dict[str, BaseTool] = {}
        self._tools_by_category: Dict[str, List[BaseTool]] = {
            "content": [],    # 内容生成工具
            "image": [],      # 图片生成工具
            "publish": [],    # 发布工具
            "search": [],     # 搜索工具
            "user": [],       # 用户信息工具
            "login": [],      # 登录管理工具
        }
        self._initialized = False
        self.logger = logger
    
    async def initialize(self):
        """初始化所有MCP连接并注册工具"""
        if self._initialized:
            self.logger.debug("MCP Tool Registry already initialized")
            return
        
        self.logger.info("Initializing MCP Tool Registry...")
        
        try:
            # 1. 创建统一MCP客户端（连接所有MCP服务）
            self._mcp_client = MultiServerMCPClient({
                "xhs_content": {
                    "url": mcp_config.xhs_content_generator_mcp_url,
                    "transport": mcp_config.xhs_content_generator_mcp_transport,
                },
                "xhs_image": {
                    "url": mcp_config.image_video_mcp_url,
                    "transport": mcp_config.image_video_mcp_transport,
                },
                "xhs_browser": {
                    "url": mcp_config.xiaohongshu_mcp_url,
                    "transport": mcp_config.xiaohongshu_mcp_transport,
                },
            })
            
            # 2. 获取所有工具
            all_tools = await self._mcp_client.get_tools()
            self.logger.info(
                "Fetched MCP tools",
                tool_count=len(all_tools),
                tool_names=[tool.name for tool in all_tools]
            )
            
            # 3. 分类注册工具
            for tool in all_tools:
                self._tools[tool.name] = tool
                self._categorize_tool(tool)
            
            # 4. 打印分类统计
            for category, tools in self._tools_by_category.items():
                if tools:
                    self.logger.info(
                        f"Category '{category}' registered tools",
                        count=len(tools),
                        tool_names=[t.name for t in tools]
                    )
            
            self._initialized = True
            self.logger.info("MCP Tool Registry initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize MCP Tool Registry",
                error=str(e),
                exc_info=True
            )
            raise
    
    def _categorize_tool(self, tool: BaseTool):
        """将工具分类到对应类别
        
        分类规则：
        - content: 内容生成相关（generate_outline, generate_content等）
        - image: 图片/视频生成相关（generate_image, generate_video等）
        - publish: 发布相关（publish_content, publish_video等）
        - login: 登录管理相关（start_login, check_login, cleanup_login等）
        - search: 搜索浏览相关（search_feeds, get_feeds, list_feeds等）
        - user: 用户信息相关（get_user_profile等）
        """
        name = tool.name.lower()
        
        # 内容生成工具
        if "generate" in name and ("outline" in name or "content" in name):
            self._tools_by_category["content"].append(tool)
        
        # 图片/视频生成工具
        elif "generate" in name and ("image" in name or "video" in name):
            self._tools_by_category["image"].append(tool)
        
        # 发布工具
        elif "publish" in name:
            self._tools_by_category["publish"].append(tool)
        
        # 登录管理工具
        elif "login" in name or "session" in name:
            self._tools_by_category["login"].append(tool)
        
        # 搜索浏览工具
        elif any(keyword in name for keyword in ["search", "get_feeds", "list_feeds", "feed_detail"]):
            self._tools_by_category["search"].append(tool)
        
        # 用户信息工具
        elif "user" in name or "profile" in name:
            self._tools_by_category["user"].append(tool)
        
        else:
            self.logger.warning(f"Tool '{tool.name}' not categorized")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取单个工具
        
        Args:
            tool_name: 工具名称
        
        Returns:
            工具实例，如果不存在则返回None
        """
        if not self._initialized:
            raise RuntimeError(
                "MCP Tool Registry not initialized. "
                "Call await mcp_registry.initialize() first."
            )
        
        return self._tools.get(tool_name)
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """按类别获取工具
        
        Args:
            category: 工具类别（content, image, publish, login, search, user）
        
        Returns:
            工具列表
        """
        if not self._initialized:
            raise RuntimeError(
                "MCP Tool Registry not initialized. "
                "Call await mcp_registry.initialize() first."
            )
        
        return self._tools_by_category.get(category, [])
    
    def get_tools_by_categories(self, categories: List[str]) -> List[BaseTool]:
        """按多个类别获取工具
        
        Args:
            categories: 工具类别列表
        
        Returns:
            合并后的工具列表（去重）
        """
        tools = []
        tool_names = set()
        
        for category in categories:
            for tool in self.get_tools_by_category(category):
                if tool.name not in tool_names:
                    tools.append(tool)
                    tool_names.add(tool.name)
        
        return tools
    
    def get_all_tools(self) -> List[BaseTool]:
        """获取所有工具
        
        Returns:
            所有工具的列表
        """
        if not self._initialized:
            raise RuntimeError(
                "MCP Tool Registry not initialized. "
                "Call await mcp_registry.initialize() first."
            )
        
        return list(self._tools.values())
    
    def list_categories(self) -> List[str]:
        """列出所有可用的工具类别
        
        Returns:
            类别列表
        """
        return list(self._tools_by_category.keys())
    
    def get_tool_count(self) -> int:
        """获取工具总数
        
        Returns:
            工具数量
        """
        return len(self._tools)
    
    def is_initialized(self) -> bool:
        """检查是否已初始化
        
        Returns:
            是否已初始化
        """
        return self._initialized
    
    async def close(self):
        """关闭所有MCP连接并清理资源"""
        if self._mcp_client:
            # MultiServerMCPClient 会自动清理资源
            self._mcp_client = None
        
        self._tools.clear()
        for category in self._tools_by_category:
            self._tools_by_category[category].clear()
        
        self._initialized = False
        self.logger.info("MCP Tool Registry closed")
    
    def __repr__(self) -> str:
        """字符串表示"""
        if not self._initialized:
            return "<MCPToolRegistry (not initialized)>"
        
        return (
            f"<MCPToolRegistry "
            f"(tools: {len(self._tools)}, "
            f"categories: {len([c for c, t in self._tools_by_category.items() if t])})>"
        )


# ============================================================================
# 全局实例
# ============================================================================

mcp_registry = MCPToolRegistry()

"""全局MCP工具注册表实例

使用方式：
    from ai_social_scheduler.mcp.registry import mcp_registry
    
    # 初始化（只需调用一次）
    await mcp_registry.initialize()
    
    # 获取工具
    tools = mcp_registry.get_tools_by_category("content")
"""

