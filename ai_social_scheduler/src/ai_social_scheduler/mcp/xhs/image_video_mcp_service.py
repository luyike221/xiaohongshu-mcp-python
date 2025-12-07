"""图像视频生成MCP服务类

基于 LangChain 官方 MCP 适配器 (langchain-mcp-adapters)
特点:
- 官方支持,稳定可靠
- 自动工具转换
- 支持 HTTP 传输方式
- 仅封装 MCP 调用,不创建 Agent

使用示例:
    # 方式1: 直接使用
    service = ImageVideoMCPService()
    result = await service.generate_image(prompt="一只可爱的小猫")
    
    # 方式2: 使用异步上下文管理器
    async with ImageVideoMCPService() as service:
        result = await service.generate_image(prompt="一只可爱的小猫")
    
    # 方式3: 使用工厂函数
    service = await create_image_video_mcp_service()
    result = await service.generate_image(prompt="一只可爱的小猫")
"""

import json
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient

from ...config import mcp_config
from ...tools.logging import get_logger

logger = get_logger(__name__)


class ImageVideoMCPService:
    """图像视频生成MCP服务类
    
    职责：
    - 连接图像视频生成MCP服务
    - 提供图像生成功能（通义万相、Google GenAI）
    - 提供批量图像生成功能
    - 提供视频生成功能
    - 封装MCP工具调用，提供便捷的接口
    """

    def __init__(
        self,
        mcp_url: Optional[str] = None,
        mcp_transport: Optional[str] = None,
    ):
        """初始化图像视频生成MCP服务
        
        Args:
            mcp_url: MCP服务地址，默认从配置读取
            mcp_transport: MCP传输方式，默认从配置读取
        """
        self.mcp_url = mcp_url or mcp_config.image_video_mcp_url
        self.mcp_transport = mcp_transport or mcp_config.image_video_mcp_transport
        self.logger = logger
        
        # 延迟初始化的组件
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._generate_image_tool = None
        self._generate_image_with_google_genai_tool = None
        self._generate_images_batch_tool = None
        self._generate_video_tool = None
        self._initialized = False

    async def _initialize(self):
        """初始化MCP客户端（懒加载）
        
        使用 LangChain 官方 MCP 适配器连接 MCP 服务
        """
        if self._initialized:
            return
        
        try:
            self.logger.info(
                "Initializing Image Video MCP Service",
                mcp_url=self.mcp_url,
                transport=self.mcp_transport
            )
            
            # 1. 创建 MCP 客户端,配置服务器
            # 使用 MultiServerMCPClient 支持多服务器管理
            self._mcp_client = MultiServerMCPClient({
                "image_video": {
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
            
            # 3. 查找所有工具
            for tool in tools:
                if tool.name == "generate_image":
                    self._generate_image_tool = tool
                elif tool.name == "generate_image_with_google_genai":
                    self._generate_image_with_google_genai_tool = tool
                elif tool.name == "generate_images_batch":
                    self._generate_images_batch_tool = tool
                elif tool.name == "generate_video":
                    self._generate_video_tool = tool
            
            if not self._generate_images_batch_tool:
                raise ValueError("generate_images_batch tool not found in MCP tools")
            
            self._initialized = True
            self.logger.info("Image Video MCP Service initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Image Video MCP Service",
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

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1280,
        height: int = 1280,
        seed: Optional[int] = None,
        max_wait_time: int = 600,
    ) -> Dict[str, Any]:
        """生成图像（使用通义万相 WanT2I）
        
        Args:
            prompt: 图像生成提示词
            negative_prompt: 负面提示词（可选）
            width: 图像宽度，默认 1280
            height: 图像高度，默认 1280
            seed: 随机种子（可选）
            max_wait_time: 最大等待时间（秒），默认 600 秒（10分钟）
        
        Returns:
            包含生成结果的字典：
            - success: 是否成功
            - result: 图片 URL 列表
            - message: 消息
            - error: 错误信息（如果失败）
            - task_id: 任务ID（如果超时）
        """
        await self._initialize()
        
        if not self._generate_image_tool:
            raise ValueError("generate_image tool not found in MCP tools")
        
        try:
            self.logger.info(
                "Generating image",
                prompt=prompt[:50] if prompt else None,
                width=width,
                height=height,
                max_wait_time=max_wait_time
            )
            
            # 构建参数
            params: Dict[str, Any] = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "max_wait_time": max_wait_time,
            }
            
            if negative_prompt:
                params["negative_prompt"] = negative_prompt
            if seed:
                params["seed"] = seed
            
            # 调用工具
            raw_result = await self._generate_image_tool.ainvoke(params)
            
            # 调试：记录原始返回值的类型
            self.logger.debug(
                "Tool raw result",
                result_type=type(raw_result).__name__,
                is_str=isinstance(raw_result, str),
                is_dict=isinstance(raw_result, dict),
            )
            
            # 处理返回值
            result = self._parse_tool_result(raw_result)
            
            self.logger.info(
                "Image generated",
                success=result.get("success", False) if isinstance(result, dict) else False,
                url_count=len(result.get("result", [])) if isinstance(result, dict) and result.get("success") else 0
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to generate image",
                error=str(e),
                prompt=prompt[:50] if prompt else None
            )
            return {
                "success": False,
                "error": f"生成图像时发生异常: {str(e)}"
            }

    async def generate_image_with_google_genai(
        self,
        prompt: str,
        aspect_ratio: str = "3:4",
        temperature: float = 1.0,
        model: str = "gemini-3-pro-image-preview",
        reference_image_base64: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """使用 Google GenAI (Gemini) 生成图像
        
        Args:
            prompt: 图像生成提示词
            aspect_ratio: 宽高比，支持 "1:1", "3:4", "4:3", "16:9", "9:16"，默认 "3:4"
            temperature: 温度参数，控制生成随机性，范围 0.0-2.0，默认 1.0
            model: 模型名称，默认 "gemini-3-pro-image-preview"
            reference_image_base64: 参考图片（base64 编码），用于保持风格一致（可选）
            api_key: Google GenAI API Key（可选，如果不提供则从配置读取）
            base_url: 自定义 API 端点（可选）
        
        Returns:
            包含生成结果的字典：
            - success: 是否成功
            - result: 图片的 base64 编码数据
            - format: 格式（"base64"）
            - message: 消息
            - size_bytes: 图片大小（字节）
            - error: 错误信息（如果失败）
        """
        await self._initialize()
        
        if not self._generate_image_with_google_genai_tool:
            raise ValueError("generate_image_with_google_genai tool not found in MCP tools")
        
        try:
            self.logger.info(
                "Generating image with Google GenAI",
                prompt=prompt[:50] if prompt else None,
                aspect_ratio=aspect_ratio,
                model=model,
                has_reference_image=reference_image_base64 is not None
            )
            
            # 构建参数
            params: Dict[str, Any] = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "temperature": temperature,
                "model": model,
            }
            
            if reference_image_base64:
                params["reference_image_base64"] = reference_image_base64
            if api_key:
                params["api_key"] = api_key
            if base_url:
                params["base_url"] = base_url
            
            # 调用工具
            raw_result = await self._generate_image_with_google_genai_tool.ainvoke(params)
            
            # 处理返回值
            result = self._parse_tool_result(raw_result)
            
            self.logger.info(
                "Image generated with Google GenAI",
                success=result.get("success", False) if isinstance(result, dict) else False
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to generate image with Google GenAI",
                error=str(e),
                prompt=prompt[:50] if prompt else None
            )
            return {
                "success": False,
                "error": f"生成图像时发生异常: {str(e)}"
            }

    async def generate_images_batch(
        self,
        pages: List[Dict[str, Any]],
        full_outline: str = "",
        user_topic: str = "",
        user_images_base64: Optional[List[str]] = None,
        max_wait_time: int = 600,
    ) -> Dict[str, Any]:
        """批量生成小红书风格的图片
        
        Args:
            pages: 页面列表，每个页面包含 index、type、content 字段
            full_outline: 完整的内容大纲文本，用于保持所有页面风格一致
            user_topic: 用户的原始需求或主题，用于保持生成图片的意图一致
            user_images_base64: 用户上传的参考图片列表（base64 编码），可选
            max_wait_time: 最大等待时间（秒），默认 600 秒（10分钟）
        
        Returns:
            包含生成结果的字典：
            - success: 是否全部成功生成
            - task_id: 自动生成的任务ID
            - total: 总页面数
            - completed: 成功生成的页面数
            - failed: 失败的页面数
            - images: 成功生成的图片列表，每个元素包含 index、url、type
            - failed_pages: 失败的页面列表，每个元素包含 index、error
        """
        await self._initialize()
        
        if not self._generate_images_batch_tool:
            raise ValueError("generate_images_batch tool not found in MCP tools")
        
        try:
            self.logger.info(
                "Generating images batch",
                pages_count=len(pages),
                user_topic=user_topic[:50] if user_topic else None,
                has_reference_images=user_images_base64 is not None and len(user_images_base64) > 0
            )
            
            # 构建参数
            params: Dict[str, Any] = {
                "pages": pages,
                "full_outline": full_outline,
                "user_topic": user_topic,
                "max_wait_time": max_wait_time,
            }
            
            if user_images_base64:
                params["user_images_base64"] = user_images_base64
            
            # 调用工具
            raw_result = await self._generate_images_batch_tool.ainvoke(params)
            
            # 处理返回值
            result = self._parse_tool_result(raw_result)
            
            self.logger.info(
                "Images batch generated",
                success=result.get("success", False) if isinstance(result, dict) else False,
                completed=result.get("completed", 0) if isinstance(result, dict) else 0,
                failed=result.get("failed", 0) if isinstance(result, dict) else 0
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to generate images batch",
                error=str(e),
                pages_count=len(pages) if pages else 0
            )
            return {
                "success": False,
                "error": f"批量生成图像时发生异常: {str(e)}"
            }

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
    ) -> Dict[str, Any]:
        """生成视频
        
        Args:
            prompt: 视频生成提示词
            duration: 视频时长（秒），默认 5 秒
        
        Returns:
            包含生成结果的字典
        """
        await self._initialize()
        
        if not self._generate_video_tool:
            raise ValueError("generate_video tool not found in MCP tools")
        
        try:
            self.logger.info(
                "Generating video",
                prompt=prompt[:50] if prompt else None,
                duration=duration
            )
            
            # 构建参数
            params: Dict[str, Any] = {
                "prompt": prompt,
                "duration": duration,
            }
            
            # 调用工具
            raw_result = await self._generate_video_tool.ainvoke(params)
            
            # 处理返回值
            result = self._parse_tool_result(raw_result)
            
            self.logger.info(
                "Video generated",
                success=result.get("success", False) if isinstance(result, dict) else False
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to generate video",
                error=str(e),
                prompt=prompt[:50] if prompt else None
            )
            return {
                "success": False,
                "error": f"生成视频时发生异常: {str(e)}"
            }

    async def close(self):
        """关闭MCP客户端连接
        
        清理资源,关闭与 MCP 服务器的连接
        """
        if self._mcp_client:
            # MultiServerMCPClient 会自动清理资源
            # 这里只需要重置状态
            self._mcp_client = None
            self._generate_image_tool = None
            self._generate_image_with_google_genai_tool = None
            self._generate_images_batch_tool = None
            self._generate_video_tool = None
            self._initialized = False
            self.logger.info("Image Video MCP Service closed")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 便捷函数：创建服务实例
async def create_image_video_mcp_service(
    mcp_url: Optional[str] = None,
    mcp_transport: Optional[str] = None,
) -> ImageVideoMCPService:
    """创建并初始化图像视频生成MCP服务（工厂函数）
    
    Args:
        mcp_url: MCP服务地址
        mcp_transport: MCP传输方式
    
    Returns:
        已初始化的ImageVideoMCPService实例
    """
    service = ImageVideoMCPService(
        mcp_url=mcp_url,
        mcp_transport=mcp_transport,
    )
    await service._initialize()
    return service

