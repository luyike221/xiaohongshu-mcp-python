"""统一模型提供商客户端"""
from typing import Optional, Dict, Any
from .text_client import TextChatClient


class ModelProviderClient:
    """统一模型提供商客户端，支持多种模型提供商"""
    
    # 预定义的模型提供商配置
    PROVIDERS = {
        "qwen-plus": {
            "name": "通义千问 Plus",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-plus",
            "endpoint": "/v1/chat/completions",
        },
        "qwen-turbo": {
            "name": "通义千问 Turbo",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-turbo",
            "endpoint": "/v1/chat/completions",
        },
        "qwen-max": {
            "name": "通义千问 Max",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-max",
            "endpoint": "/v1/chat/completions",
        },
        "deepseek-chat": {
            "name": "DeepSeek Chat",
            "base_url": "https://api.deepseek.com",
            "default_model": "deepseek-chat",
            "endpoint": "/v1/chat/completions",
        },
        "deepseek-coder": {
            "name": "DeepSeek Coder",
            "base_url": "https://api.deepseek.com",
            "default_model": "deepseek-coder",
            "endpoint": "/v1/chat/completions",
        },
        "alibaba-bailian": {
            "name": "阿里百炼",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-plus",
            "endpoint": "/v1/chat/completions",
        },
        "openai": {
            "name": "OpenAI",
            "base_url": "https://api.openai.com",
            "default_model": "gpt-4o",
            "endpoint": "/v1/chat/completions",
        },
    }
    
    @classmethod
    def get_provider_config(cls, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        获取提供商配置
        
        Args:
            provider_name: 提供商名称（如 'qwen-plus', 'deepseek-chat' 等）
        
        Returns:
            提供商配置字典，如果不存在返回 None
        """
        return cls.PROVIDERS.get(provider_name)
    
    @classmethod
    def list_providers(cls) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用的模型提供商
        
        Returns:
            所有提供商的配置字典
        """
        return cls.PROVIDERS.copy()
    
    @classmethod
    def create_client(
        cls,
        provider_name: str,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> TextChatClient:
        """
        创建模型提供商客户端
        
        Args:
            provider_name: 提供商名称（如 'qwen-plus', 'deepseek-chat', 'alibaba-bailian' 等）
            api_key: API Key
            model: 模型名称（可选，如果不提供则使用提供商默认模型）
            base_url: API 基础 URL（可选，如果不提供则使用提供商默认 URL）
            endpoint: 端点路径（可选，如果不提供则使用提供商默认端点）
        
        Returns:
            TextChatClient 实例
        
        Raises:
            ValueError: 如果提供商不存在或 API Key 未提供
        """
        if not api_key:
            raise ValueError(f"API Key 未配置（提供商: {provider_name}）")
        
        # 获取提供商配置
        provider_config = cls.get_provider_config(provider_name)
        
        if not provider_config:
            available = ', '.join(cls.PROVIDERS.keys())
            raise ValueError(
                f"不支持的模型提供商: {provider_name}\n"
                f"支持的提供商: {available}\n"
                "提示：可以使用 'openai_compatible' 类型并手动配置 base_url 和 model"
            )
        
        # 使用提供的参数或默认值
        final_base_url = base_url or provider_config["base_url"]
        final_model = model or provider_config["default_model"]
        final_endpoint = endpoint or provider_config.get("endpoint", "/v1/chat/completions")
        
        return TextChatClient(
            api_key=api_key,
            base_url=final_base_url,
            endpoint_type=final_endpoint,
        )


def get_model_provider_client(provider_config: dict) -> TextChatClient:
    """
    根据配置获取模型提供商客户端（统一接口）
    
    这个函数会根据配置自动选择合适的客户端：
    - 如果配置中包含 'provider_name'，使用 ModelProviderClient
    
    Args:
        provider_config: 服务商配置字典
            - provider_name: 模型提供商名称（可选，如 'qwen-plus', 'deepseek-chat', 'alibaba-bailian' 等）
            - api_key: API密钥
            - base_url: API基础URL（可选）
            - endpoint_type: 自定义端点路径（可选）
            - model: 模型名称（可选）
    
    Returns:
        TextChatClient
    """
    provider_name = provider_config.get('provider_name')
    api_key = provider_config.get('api_key')
    base_url = provider_config.get('base_url')
    endpoint_type = provider_config.get('endpoint_type')
    model = provider_config.get('model')
    
    # 如果指定了 provider_name，使用 ModelProviderClient
    if provider_name:
        return ModelProviderClient.create_client(
            provider_name=provider_name,
            api_key=api_key,
            model=model,
            base_url=base_url,
            endpoint=endpoint_type,
        )
    
    # 否则使用标准的 TextChatClient
    return TextChatClient(
        api_key=api_key,
        base_url=base_url,
        endpoint_type=endpoint_type,
    )
