"""策略管理器 - 负责策略生成和管理"""

import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, AIMessage

from ..client import QwenClient
from ..tools.logging import get_logger

logger = get_logger(__name__)


class StrategyManager:
    """策略管理器
    
    职责：
    - 生成内容策略
    - 选择话题和模板
    - 优化策略
    - 管理策略库
    """

    def __init__(self, model: str = "qwen-plus", temperature: float = 0.7):
        """初始化策略管理器"""
        self.client = QwenClient(model=model, temperature=temperature)
        self.logger = logger
        # TODO: 从数据库加载策略库
        self.strategy_library: Dict[str, Any] = {}
    
    def _extract_json_from_response(self, response: Any) -> Optional[Dict[str, Any]]:
        """从LLM响应中提取JSON数据
        
        Args:
            response: LLM响应对象（可能是AIMessage或字符串）
        
        Returns:
            解析后的JSON字典，如果解析失败则返回None
        """
        try:
            # 提取响应内容
            if isinstance(response, AIMessage):
                content = response.content
            elif isinstance(response, str):
                content = response
            elif hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # 尝试从markdown代码块中提取JSON
            # 匹配 ```json ... ``` 或 ``` ... ```
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            # 尝试直接查找JSON对象
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            # 解析JSON
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else None
            
        except json.JSONDecodeError as e:
            self.logger.warning(
                "Failed to parse JSON from response",
                error=str(e),
                content_preview=content[:200] if 'content' in locals() else str(response)[:200]
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error while parsing JSON",
                error=str(e),
                response_type=type(response).__name__
            )
            return None

    async def generate_content_strategy(
        self, 
        request: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成内容策略
        
        Args:
            request: 用户请求
            context: 上下文信息（可能包含understanding结果）
        
        Returns:
            内容策略，包含：
            - topic: 话题
            - template: 模板
            - style: 风格
            - keywords: 关键词
        """
        # 从context中提取理解结果
        understanding = context.get("understanding", {}) if context else {}
        entities = understanding.get("entities", {})
        intent = understanding.get("intent", "")
        
        prompt = f"""根据以下请求和上下文信息，生成小红书内容策略：

用户请求：{request}
用户意图：{intent}
提取的实体：{json.dumps(entities, ensure_ascii=False)}
其他上下文：{json.dumps({k: v for k, v in (context or {}).items() if k != "understanding"}, ensure_ascii=False)}

请为小红书平台生成内容策略，要求：
1. 话题（topic）：内容主题，要吸引人且符合小红书用户喜好
2. 模板（template）：内容模板类型（如：教程类/分享类/测评类/生活类等）
3. 风格（style）：内容风格（如：轻松活泼/专业严谨/温馨治愈/时尚潮流等）
4. 关键词（keywords）：3-5个相关关键词，用于SEO和标签

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "topic": "内容主题",
    "template": "模板类型",
    "style": "内容风格",
    "keywords": ["关键词1", "关键词2", "关键词3"]
}}

只返回JSON，不要有其他文字说明。"""
        
        try:
            response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
            
            # 解析JSON响应
            parsed = self._extract_json_from_response(response)
            
            if parsed:
                # 验证和清理数据
                keywords = parsed.get("keywords", [])
                if not isinstance(keywords, list):
                    keywords = [keywords] if keywords else []
                # 确保关键词数量合理
                keywords = keywords[:10]  # 最多10个关键词
                
                result = {
                    "topic": parsed.get("topic", "默认话题"),
                    "template": parsed.get("template", "分享类"),
                    "style": parsed.get("style", "轻松活泼"),
                    "keywords": keywords,
                }
                
                self.logger.info(
                    "Content strategy generated",
                    topic=result["topic"],
                    template=result["template"],
                    style=result["style"],
                    keyword_count=len(result["keywords"])
                )
                return result
            else:
                # 解析失败，使用默认值
                self.logger.warning(
                    "Failed to parse response, using defaults",
                    request_preview=request[:100]
                )
                # 尝试从entities中提取话题
                topic = entities.get("topic", request[:50]) if entities else request[:50]
                keywords = entities.get("keywords", []) if entities else []
                
                return {
                    "topic": topic,
                    "template": "分享类",
                    "style": "轻松活泼",
                    "keywords": keywords if keywords else ["小红书", "分享"],
                }
                
        except Exception as e:
            self.logger.error(
                "Error generating content strategy",
                error=str(e),
                request_preview=request[:100]
            )
            # 返回默认值
            return {
                "topic": request[:50],
                "template": "分享类",
                "style": "轻松活泼",
                "keywords": ["小红书", "分享"],
            }

    async def select_topic_and_template(
        self, 
        content_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """选择话题和模板
        
        Args:
            content_plan: 内容计划
        
        Returns:
            选择结果，包含：
            - topic: 选择的话题
            - template: 选择的模板
        """
        prompt = f"""
        根据以下内容计划选择话题和模板：
        
        内容计划：{content_plan}
        
        请从策略库中选择最合适的话题和模板。
        
        返回 JSON 格式。
        """
        
        response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
        # TODO: 解析响应，返回结构化结果
        return {
            "topic": "selected_topic",
            "template": "selected_template",
        }

    async def match_content_strategy(
        self, 
        hot_topic: Dict[str, Any]
    ) -> Dict[str, Any]:
        """匹配内容策略（用于热点追踪）
        
        Args:
            hot_topic: 热点话题
        
        Returns:
            匹配的策略
        """
        prompt = f"""
        为以下热点话题匹配内容策略：
        
        热点话题：{hot_topic}
        
        请从策略库中匹配最相关的内容策略。
        
        返回 JSON 格式。
        """
        
        response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
        # TODO: 解析响应，返回结构化结果
        return {
            "strategy": "matched_strategy",
            "relevance": 0.8,
        }

    async def optimize_strategy(
        self, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化策略（基于表现数据）
        
        Args:
            performance_data: 表现数据
        
        Returns:
            优化后的策略
        """
        prompt = f"""
        根据以下表现数据优化策略：
        
        表现数据：{performance_data}
        
        请分析高/低表现内容的特征，提取成功模式，生成优化建议。
        
        返回 JSON 格式。
        """
        
        response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
        # TODO: 解析响应，返回结构化结果
        return {
            "optimized_strategy": "new_strategy",
            "improvements": ["改进点1", "改进点2"],
        }

    async def update_strategy(
        self, 
        strategy_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """更新策略
        
        Args:
            strategy_id: 策略ID
            updates: 更新内容
        
        Returns:
            是否成功
        """
        # TODO: 实现策略更新逻辑
        self.logger.info("Strategy updated", strategy_id=strategy_id, updates=updates)
        return True

    async def extract_success_patterns(
        self, 
        high_performance_content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取成功模式
        
        Args:
            high_performance_content: 高表现内容列表
        
        Returns:
            成功模式
        """
        prompt = f"""
        分析以下高表现内容，提取成功模式：
        
        高表现内容：{high_performance_content}
        
        请提取：
        1. 共同特征
        2. 成功要素
        3. 可复制的模式
        
        返回 JSON 格式。
        """
        
        response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
        # TODO: 解析响应，返回结构化结果
        return {
            "patterns": ["模式1", "模式2"],
            "features": ["特征1", "特征2"],
        }

