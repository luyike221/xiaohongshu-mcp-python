"""小红书内容生成MCP服务类

基于 LangChain 官方 MCP 适配器 (langchain-mcp-adapters)
特点:
- 官方支持,稳定可靠
- 自动工具转换
- 支持 HTTP 传输方式
- 仅封装 MCP 调用,不创建 Agent

使用示例:
    # 方式1: 直接使用
    service = XHSContentGeneratorService()
    result = await service.generate_outline(topic="如何在家做拿铁")
    
    # 方式2: 使用异步上下文管理器
    async with XHSContentGeneratorService() as service:
        result = await service.generate_outline(topic="秋季显白美甲")
    
    # 方式3: 使用工厂函数
    service = await create_xhs_content_generator_service()
    result = await service.generate_outline(topic="产品宣传")
"""

import json
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient

from .....config import mcp_config
from ....tools.logging import get_logger

logger = get_logger(__name__)


class XHSContentGeneratorService:
    """小红书内容生成MCP服务类
    
    职责：
    - 连接小红书内容生成MCP服务
    - 提供内容大纲生成功能
    - 封装MCP工具调用，提供便捷的接口
    """

    def __init__(
        self,
        mcp_url: Optional[str] = None,
        mcp_transport: Optional[str] = None,
    ):
        """初始化小红书内容生成MCP服务
        
        Args:
            mcp_url: MCP服务地址，默认从配置读取
            mcp_transport: MCP传输方式，默认从配置读取
        """
        self.mcp_url = mcp_url or mcp_config.xhs_content_generator_mcp_url
        self.mcp_transport = mcp_transport or mcp_config.xhs_content_generator_mcp_transport
        self.logger = logger
        
        # 延迟初始化的组件
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._generate_outline_tool = None
        self._initialized = False

    async def _initialize(self):
        """初始化MCP客户端（懒加载）
        
        使用 LangChain 官方 MCP 适配器连接 MCP 服务
        """
        if self._initialized:
            return
        
        try:
            self.logger.info(
                "Initializing XHS Content Generator Service",
                mcp_url=self.mcp_url,
                transport=self.mcp_transport
            )
            
            # 1. 创建 MCP 客户端,配置服务器
            # 使用 MultiServerMCPClient 支持多服务器管理
            self._mcp_client = MultiServerMCPClient({
                "xhs_content_generator": {
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
            
            # 3. 查找 generate_outline 工具
            self._generate_outline_tool = next(
                (tool for tool in tools if tool.name == "generate_outline"),
                None
            )
            
            if not self._generate_outline_tool:
                available_tools = [tool.name for tool in tools]
                raise ValueError(
                    f"generate_outline tool not found in MCP tools. "
                    f"Available tools: {available_tools}"
                )
            
            self._initialized = True
            self.logger.info("XHS Content Generator Service initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize XHS Content Generator Service",
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

    async def generate_outline(
        self,
        topic: str,
        provider_type: str = "alibaba_bailian",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_output_tokens: int = 8000,
        images_base64: Optional[List[str]] = None,
        vl_model_provider_type: Optional[str] = None,
        vl_model_api_key: Optional[str] = None,
        vl_model_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """生成小红书图文内容大纲
        
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
            - title: 提取的标题（匹配发布接口）
            - content: 提取的正文内容（匹配发布接口，不包含标题和标签）
            - tags: 提取的标签列表（匹配发布接口）
            - error: 错误信息（如果失败）
        """
        await self._initialize()
        
        try:
            self.logger.info(
                "Generating outline",
                topic=topic[:50] if topic else None,
                provider_type=provider_type,
                model=model,
                has_images=images_base64 is not None and len(images_base64) > 0
            )
            
            # 构建参数
            params: Dict[str, Any] = {
                "topic": topic,
                "provider_type": provider_type,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
            
            if model:
                params["model"] = model
            if images_base64:
                params["images_base64"] = images_base64
            if vl_model_provider_type:
                params["vl_model_provider_type"] = vl_model_provider_type
            if vl_model_api_key:
                params["vl_model_api_key"] = vl_model_api_key
            if vl_model_model:
                params["vl_model_model"] = vl_model_model
            
            # 4. 直接调用工具(不创建 Agent,仅封装 MCP 调用)
            raw_result = await self._generate_outline_tool.ainvoke(params)
            
            # 调试：记录原始返回值的类型
            self.logger.debug(
                "Tool raw result",
                result_type=type(raw_result).__name__,
                is_str=isinstance(raw_result, str),
                is_dict=isinstance(raw_result, dict),
                has_content=hasattr(raw_result, "content") if not isinstance(raw_result, (str, dict)) else False
            )
            
            # 处理返回值：可能是字符串、字典或对象
            result = self._parse_tool_result(raw_result)
            
            self.logger.info(
                "Outline generated",
                success=result.get("success", False) if isinstance(result, dict) else False,
                pages_count=len(result.get("pages", [])) if isinstance(result, dict) and result.get("success") else 0
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to generate outline",
                error=str(e),
                topic=topic[:50] if topic else None
            )
            return {
                "success": False,
                "error": f"生成大纲时发生异常: {str(e)}"
            }

    async def close(self):
        """关闭MCP客户端连接
        
        清理资源,关闭与 MCP 服务器的连接
        """
        if self._mcp_client:
            # MultiServerMCPClient 会自动清理资源
            # 这里只需要重置状态
            self._mcp_client = None
            self._generate_outline_tool = None
            self._initialized = False
            self.logger.info("XHS Content Generator Service closed")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 便捷函数：创建服务实例
async def create_xhs_content_generator_service(
    mcp_url: Optional[str] = None,
    mcp_transport: Optional[str] = None,
) -> XHSContentGeneratorService:
    """创建并初始化小红书内容生成MCP服务（工厂函数）
    
    Args:
        mcp_url: MCP服务地址
        mcp_transport: MCP传输方式
    
    Returns:
        已初始化的XHSContentGeneratorService实例
    """
    service = XHSContentGeneratorService(
        mcp_url=mcp_url,
        mcp_transport=mcp_transport,
    )
    await service._initialize()
    return service

