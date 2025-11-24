"""AI决策引擎 - 负责理解和决策"""

import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, AIMessage

from ..client import QwenClient
from ..tools.logging import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """AI决策引擎
    
    职责：
    - 理解用户需求
    - 分析内容（评论、私信、热点等）
    - 生成决策
    - 评估风险和影响
    """
    
    # 可用的工作流列表及其描述
    AVAILABLE_WORKFLOWS = {
        "content_publish": "用户请求内容发布 - 用于用户主动请求发布内容到小红书",
        "auto_reply": "自动回复评论 - 用于自动回复小红书笔记的评论",
        "scheduled_publish": "定时内容发布 - 用于定时自动发布内容",
        "hot_topic_tracking": "热点内容追踪与发布 - 用于追踪热点话题并发布相关内容",
        "exception_handling": "数据异常处理 - 用于处理数据异常和系统异常",
        "competitor_analysis": "竞品分析与策略调整 - 用于分析竞品内容并调整策略",
        "message_handling": "私信自动处理 - 用于自动处理小红书私信",
        "performance_analysis": "内容表现分析与优化 - 用于分析内容表现数据并优化策略",
    }

    def __init__(self, model: str = "qwen-plus", temperature: float = 0.7):
        """初始化决策引擎"""
        self.client = QwenClient(model=model, temperature=temperature)
        self.logger = logger
    
    def _get_workflow_list_text(self) -> str:
        """获取工作流列表的文本描述
        
        Returns:
            格式化的工作流列表文本
        """
        workflow_list = []
        for name, description in self.AVAILABLE_WORKFLOWS.items():
            workflow_list.append(f"- {name}: {description}")
        return "\n".join(workflow_list)
    
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

    async def understand_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """理解用户请求
        
        Args:
            request: 用户请求文本
            context: 上下文信息
        
        Returns:
            理解结果，包含：
            - intent: 意图
            - entities: 实体
            - workflow: 推荐的工作流
        """
        # 获取工作流列表
        workflow_list_text = self._get_workflow_list_text()
        
        prompt = f"""分析以下用户请求，理解其意图和需求：

用户请求：{request}

上下文：{context or {}}

可用的工作流列表：
{workflow_list_text}

请根据用户请求的意图，从上述工作流列表中选择最合适的工作流。

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "intent": "用户意图描述",
    "entities": {{
        "topic": "话题",
        "keywords": ["关键词1", "关键词2"],
        "style": "内容风格",
        "target_audience": "目标受众"
    }},
    "workflow": "工作流名称（必须从可用工作流列表中选择一个）"
}}

只返回JSON，不要有其他文字说明。"""
        
        try:
            response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
            
            # 解析JSON响应
            parsed = self._extract_json_from_response(response)
            
            if parsed:
                # 验证必需字段
                result = {
                    "intent": parsed.get("intent", "未知意图"),
                    "entities": parsed.get("entities", {}),
                    "workflow": parsed.get("workflow", "content_publish"),
                }
                
                # 验证工作流名称
                valid_workflows = list(self.AVAILABLE_WORKFLOWS.keys())
                if result["workflow"] not in valid_workflows:
                    self.logger.warning(
                        "Invalid workflow name, defaulting to content_publish",
                        workflow=result["workflow"]
                    )
                    result["workflow"] = "content_publish"
                
                self.logger.info(
                    "Request understood",
                    intent=result["intent"],
                    workflow=result["workflow"]
                )
                return result
            else:
                # 解析失败，使用默认值
                self.logger.warning(
                    "Failed to parse response, using defaults",
                    request_preview=request[:100]
                )
                return {
                    "intent": "内容发布",
                    "entities": {"topic": request[:50]},
                    "workflow": "content_publish",
                }
                
        except Exception as e:
            self.logger.error(
                "Error understanding request",
                error=str(e),
                request_preview=request[:100]
            )
            # 返回默认值
            return {
                "intent": "内容发布",
                "entities": {"topic": request[:50]},
                "workflow": "content_publish",
            }

    async def analyze_content(self, content: str, content_type: str = "comment") -> Dict[str, Any]:
        """分析内容（评论、私信等）
        
        Args:
            content: 内容文本
            content_type: 内容类型（comment, message, etc.）
        
        Returns:
            分析结果，包含：
            - sentiment: 情感倾向
            - category: 内容类别
            - needs_human: 是否需要人工介入
            - suggested_reply: 建议回复
        """
        prompt = f"""分析以下{content_type}内容：

内容：{content}

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "sentiment": "正面/中性/负面",
    "category": "咨询/投诉/建议/其他",
    "needs_human": true/false,
    "suggested_reply": "建议回复内容（如果需要人工介入则为空字符串）"
}}

只返回JSON，不要有其他文字说明。"""
        
        try:
            response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
            
            # 解析JSON响应
            parsed = self._extract_json_from_response(response)
            
            if parsed:
                result = {
                    "sentiment": parsed.get("sentiment", "中性"),
                    "category": parsed.get("category", "其他"),
                    "needs_human": bool(parsed.get("needs_human", True)),
                    "suggested_reply": parsed.get("suggested_reply", ""),
                }
                
                # 验证情感倾向
                valid_sentiments = ["正面", "中性", "负面", "positive", "neutral", "negative"]
                if result["sentiment"] not in valid_sentiments:
                    result["sentiment"] = "中性"
                
                self.logger.info(
                    "Content analyzed",
                    sentiment=result["sentiment"],
                    category=result["category"],
                    needs_human=result["needs_human"]
                )
                return result
            else:
                # 解析失败，使用默认值
                self.logger.warning("Failed to parse response, using defaults")
                return {
                    "sentiment": "中性",
                    "category": "其他",
                    "needs_human": True,
                    "suggested_reply": "",
                }
                
        except Exception as e:
            self.logger.error("Error analyzing content", error=str(e))
            return {
                "sentiment": "中性",
                "category": "其他",
                "needs_human": True,
                "suggested_reply": "",
            }

    async def analyze_hot_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """分析热点话题相关性
        
        Args:
            topic: 热点话题信息
        
        Returns:
            分析结果，包含：
            - relevance: 相关性评分
            - match_strategy: 匹配的策略
            - content_plan: 内容方案
        """
        prompt = f"""分析以下热点话题的相关性：

热点话题：{json.dumps(topic, ensure_ascii=False)}

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "relevance": 0.0-1.0之间的浮点数,
    "match_strategy": "策略名称",
    "content_plan": {{
        "topic": "内容主题",
        "angle": "切入角度",
        "keywords": ["关键词1", "关键词2"]
    }}
}}

只返回JSON，不要有其他文字说明。"""
        
        try:
            response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
            
            # 解析JSON响应
            parsed = self._extract_json_from_response(response)
            
            if parsed:
                relevance = float(parsed.get("relevance", 0.5))
                # 确保relevance在0-1之间
                relevance = max(0.0, min(1.0, relevance))
                
                result = {
                    "relevance": relevance,
                    "match_strategy": parsed.get("match_strategy", "trending_topic"),
                    "content_plan": parsed.get("content_plan", {}),
                }
                
                self.logger.info(
                    "Hot topic analyzed",
                    relevance=result["relevance"],
                    strategy=result["match_strategy"]
                )
                return result
            else:
                # 解析失败，使用默认值
                self.logger.warning("Failed to parse response, using defaults")
                return {
                    "relevance": 0.5,
                    "match_strategy": "trending_topic",
                    "content_plan": {},
                }
                
        except Exception as e:
            self.logger.error("Error analyzing hot topic", error=str(e))
            return {
                "relevance": 0.5,
                "match_strategy": "trending_topic",
                "content_plan": {},
            }

    async def analyze_exception(self, exception_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析异常原因和影响
        
        Args:
            exception_data: 异常数据
        
        Returns:
            分析结果，包含：
            - cause: 异常原因
            - impact: 影响评估
            - risk_level: 风险等级
            - suggested_action: 建议处理动作
        """
        prompt = f"""分析以下数据异常：

异常数据：{json.dumps(exception_data, ensure_ascii=False)}

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "cause": "异常原因描述",
    "impact": "高/中/低",
    "risk_level": "高/中/低",
    "suggested_action": "pause/adjust/continue"
}}

只返回JSON，不要有其他文字说明。"""
        
        try:
            response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
            
            # 解析JSON响应
            parsed = self._extract_json_from_response(response)
            
            if parsed:
                suggested_action = parsed.get("suggested_action", "adjust")
                valid_actions = ["pause", "adjust", "continue"]
                if suggested_action not in valid_actions:
                    suggested_action = "adjust"
                
                result = {
                    "cause": parsed.get("cause", "未知原因"),
                    "impact": parsed.get("impact", "中"),
                    "risk_level": parsed.get("risk_level", "中"),
                    "suggested_action": suggested_action,
                }
                
                self.logger.info(
                    "Exception analyzed",
                    cause=result["cause"],
                    risk_level=result["risk_level"],
                    action=result["suggested_action"]
                )
                return result
            else:
                # 解析失败，使用默认值
                self.logger.warning("Failed to parse response, using defaults")
                return {
                    "cause": "未知原因",
                    "impact": "中",
                    "risk_level": "中",
                    "suggested_action": "adjust",
                }
                
        except Exception as e:
            self.logger.error("Error analyzing exception", error=str(e))
            return {
                "cause": "未知原因",
                "impact": "中",
                "risk_level": "中",
                "suggested_action": "adjust",
            }

    async def generate_decision(self, context: Dict[str, Any], options: List[str]) -> Dict[str, Any]:
        """生成决策
        
        Args:
            context: 上下文信息
            options: 可选方案
        
        Returns:
            决策结果，包含：
            - decision: 决策内容
            - reasoning: 决策理由
            - confidence: 置信度
        """
        prompt = f"""根据以下上下文和选项，生成决策：

上下文：{json.dumps(context, ensure_ascii=False)}
选项：{json.dumps(options, ensure_ascii=False)}

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "decision": "选择的方案（必须是选项列表中的一个）",
    "reasoning": "决策理由",
    "confidence": 0.0-1.0之间的浮点数
}}

只返回JSON，不要有其他文字说明。"""
        
        try:
            response = await self.client.client.ainvoke([HumanMessage(content=prompt)])
            
            # 解析JSON响应
            parsed = self._extract_json_from_response(response)
            
            if parsed:
                decision = parsed.get("decision", options[0] if options else None)
                # 验证决策是否在选项中
                if decision not in options and options:
                    decision = options[0]
                    self.logger.warning(
                        "Decision not in options, using first option",
                        decision=parsed.get("decision"),
                        options=options
                    )
                
                confidence = float(parsed.get("confidence", 0.5))
                confidence = max(0.0, min(1.0, confidence))
                
                result = {
                    "decision": decision,
                    "reasoning": parsed.get("reasoning", "基于上下文分析"),
                    "confidence": confidence,
                }
                
                self.logger.info(
                    "Decision generated",
                    decision=result["decision"],
                    confidence=result["confidence"]
                )
                return result
            else:
                # 解析失败，使用默认值
                self.logger.warning("Failed to parse response, using defaults")
                return {
                    "decision": options[0] if options else None,
                    "reasoning": "基于上下文分析",
                    "confidence": 0.5,
                }
                
        except Exception as e:
            self.logger.error("Error generating decision", error=str(e))
            return {
                "decision": options[0] if options else None,
                "reasoning": "基于上下文分析",
                "confidence": 0.5,
            }

