"""路由系统 - 混合策略路由

重构核心：结合规则引擎和LLM分析，提供灵活的路由决策
"""

from typing import Any, Optional

from langchain_core.messages import BaseMessage

from ..core.route import RouteConfig, RouteDecision, RouteStrategy
from ..tools.logging import get_logger
from .intent_analyzer import IntentAnalyzer
from .rule_engine import RuleEngine

logger = get_logger(__name__)


# ============================================================================
# 路由策略枚举
# ============================================================================

class RouterStrategy:
    """路由策略常量"""
    RULE_FIRST = "rule_first"        # 规则优先（快速路径）
    LLM_FIRST = "llm_first"          # LLM 优先（灵活路径）
    HYBRID = "hybrid"                 # 混合策略（规则+LLM）
    LLM_ONLY = "llm_only"            # 仅 LLM
    RULE_ONLY = "rule_only"          # 仅规则


# ============================================================================
# 路由系统
# ============================================================================

class RouterSystem:
    """路由系统 - 混合策略的智能路由
    
    核心职责：
    1. 统一路由入口
    2. 协调规则引擎和LLM分析器
    3. 实现混合路由策略
    4. 提供路由结果
    
    设计理念：
    - 灵活：支持多种路由策略
    - 高效：优先使用快速路径（规则）
    - 智能：必要时使用LLM兜底
    - 可配置：策略可动态切换
    
    路由策略说明：
    1. RULE_FIRST: 先尝试规则匹配，失败则使用LLM（推荐）
    2. LLM_FIRST: 先使用LLM分析，失败则尝试规则
    3. HYBRID: 同时使用规则和LLM，结合结果
    4. LLM_ONLY: 只使用LLM（适合复杂场景）
    5. RULE_ONLY: 只使用规则（适合确定性场景）
    """
    
    def __init__(
        self,
        routes: Optional[list[RouteConfig]] = None,
        strategy: str = RouterStrategy.RULE_FIRST,
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.3,
        enable_llm: bool = True,
        available_nodes: Optional[list[str]] = None,
    ):
        """初始化路由系统
        
        Args:
            routes: 路由配置列表
            strategy: 路由策略
            llm_model: LLM 模型名称
            llm_temperature: LLM 温度参数
            enable_llm: 是否启用 LLM
            available_nodes: 可用节点列表
        """
        self.strategy = strategy
        self.enable_llm = enable_llm
        self.available_nodes = available_nodes or []
        
        # 初始化规则引擎
        self.rule_engine = RuleEngine(routes=routes)
        
        # 初始化意图分析器
        self.intent_analyzer = None
        if enable_llm:
            self.intent_analyzer = IntentAnalyzer(
                llm_model=llm_model,
                temperature=llm_temperature,
                available_nodes=self.available_nodes,
            )
        
        logger.info(
            "RouterSystem initialized",
            strategy=strategy,
            enable_llm=enable_llm,
            routes_count=len(routes) if routes else 0,
            available_nodes_count=len(self.available_nodes)
        )
    
    async def route(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None,
        messages: Optional[list[BaseMessage]] = None,
    ) -> RouteDecision:
        """执行路由决策
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            messages: 历史消息
        
        Returns:
            RouteDecision: 路由决策结果
        """
        logger.info(
            "Routing request",
            strategy=self.strategy,
            input_length=len(user_input)
        )
        
        try:
            if self.strategy == RouterStrategy.RULE_FIRST:
                return await self._route_rule_first(user_input, context, messages)
            
            elif self.strategy == RouterStrategy.LLM_FIRST:
                return await self._route_llm_first(user_input, context, messages)
            
            elif self.strategy == RouterStrategy.HYBRID:
                return await self._route_hybrid(user_input, context, messages)
            
            elif self.strategy == RouterStrategy.LLM_ONLY:
                return await self._route_llm_only(user_input, context, messages)
            
            elif self.strategy == RouterStrategy.RULE_ONLY:
                return await self._route_rule_only(user_input, context, messages)
            
            else:
                logger.warning(f"Unknown strategy: {self.strategy}, using RULE_FIRST")
                return await self._route_rule_first(user_input, context, messages)
        
        except Exception as e:
            logger.error(f"Routing failed: {e}", exc_info=True)
            return self._create_fallback_decision(str(e))
    
    async def _route_rule_first(
        self,
        user_input: str,
        context: Optional[dict[str, Any]],
        messages: Optional[list[BaseMessage]],
    ) -> RouteDecision:
        """规则优先策略"""
        # 1. 先尝试规则匹配
        logger.debug("Rule-first strategy: trying rule engine")
        decision = self.rule_engine.match(user_input, context)
        
        logger.info(
            "Rule engine result",
            has_decision=decision is not None,
            target_nodes=decision.target_nodes if decision else None,
            target_nodes_count=len(decision.target_nodes) if decision and decision.target_nodes else 0
        )
        
        if decision and decision.target_nodes:
            logger.info("Rule matched", target_nodes=decision.target_nodes)
            
            # 规则匹配成功，使用 LLM 生成回复
            if self.intent_analyzer:
                logger.debug("Rule matched, using LLM for response generation")
                llm_decision = await self.intent_analyzer.analyze(
                    user_input, context, messages
                )
                # 合并决策：使用规则的路由 + LLM 的回复
                decision.response = llm_decision.response
                decision.extracted_params.update(llm_decision.extracted_params)
                logger.debug("LLM response merged into decision")
            
            logger.info(
                "Returning rule-based decision",
                target_nodes=decision.target_nodes,
                response_length=len(decision.response)
            )
            return decision
        
        # 2. 规则未匹配，使用 LLM
        if self.intent_analyzer:
            logger.info("No rule matched, using LLM")
            llm_decision = await self.intent_analyzer.analyze(user_input, context, messages)
            logger.info(
                "LLM decision",
                target_nodes=llm_decision.target_nodes,
                target_nodes_count=len(llm_decision.target_nodes),
                confidence=llm_decision.confidence
            )
            return llm_decision
        
        # 3. 都不可用，返回降级决策
        logger.warning("No routing method available, using fallback")
        return self._create_fallback_decision("No routing method available")
    
    async def _route_llm_first(
        self,
        user_input: str,
        context: Optional[dict[str, Any]],
        messages: Optional[list[BaseMessage]],
    ) -> RouteDecision:
        """LLM 优先策略"""
        # 1. 先使用 LLM
        if self.intent_analyzer:
            decision = await self.intent_analyzer.analyze(
                user_input, context, messages
            )
            
            if decision.target_nodes and decision.confidence >= 0.7:
                logger.info("LLM decision confident", confidence=decision.confidence)
                return decision
        
        # 2. LLM 置信度低或不可用，尝试规则
        logger.info("LLM confidence low or unavailable, trying rules")
        rule_decision = self.rule_engine.match(user_input, context)
        
        if rule_decision and rule_decision.target_nodes:
            return rule_decision
        
        # 3. 返回 LLM 决策（即使置信度低）或降级决策
        if self.intent_analyzer and decision:
            return decision
        
        return self._create_fallback_decision("No confident decision")
    
    async def _route_hybrid(
        self,
        user_input: str,
        context: Optional[dict[str, Any]],
        messages: Optional[list[BaseMessage]],
    ) -> RouteDecision:
        """混合策略：同时使用规则和LLM"""
        # 1. 规则匹配
        rule_decision = self.rule_engine.match(user_input, context)
        
        # 2. LLM 分析
        llm_decision = None
        if self.intent_analyzer:
            llm_decision = await self.intent_analyzer.analyze(
                user_input, context, messages
            )
        
        # 3. 合并决策
        if rule_decision and llm_decision:
            # 都有结果，优先使用规则的路由 + LLM 的其他信息
            logger.info("Hybrid: merging rule and LLM decisions")
            return RouteDecision(
                route_id=rule_decision.route_id,
                target_nodes=rule_decision.target_nodes,
                strategy=rule_decision.strategy,
                intent=llm_decision.intent,
                confidence=rule_decision.confidence,
                reasoning=f"规则: {rule_decision.reasoning} | LLM: {llm_decision.reasoning}",
                response=llm_decision.response,
                extracted_params=llm_decision.extracted_params,
                matched_triggers=rule_decision.matched_triggers,
                matched_rules=rule_decision.matched_rules,
                should_wait=llm_decision.should_wait,
                metadata={
                    "hybrid": True,
                    "rule_matched": True,
                    "llm_analyzed": True,
                }
            )
        
        elif rule_decision:
            return rule_decision
        
        elif llm_decision:
            return llm_decision
        
        else:
            return self._create_fallback_decision("No decision from rule or LLM")
    
    async def _route_llm_only(
        self,
        user_input: str,
        context: Optional[dict[str, Any]],
        messages: Optional[list[BaseMessage]],
    ) -> RouteDecision:
        """仅使用 LLM"""
        if not self.intent_analyzer:
            return self._create_fallback_decision("LLM not available")
        
        return await self.intent_analyzer.analyze(user_input, context, messages)
    
    async def _route_rule_only(
        self,
        user_input: str,
        context: Optional[dict[str, Any]],
        messages: Optional[list[BaseMessage]],
    ) -> RouteDecision:
        """仅使用规则"""
        decision = self.rule_engine.match(user_input, context)
        
        if decision:
            return decision
        
        return self._create_fallback_decision("No rule matched")
    
    def _create_fallback_decision(self, reason: str) -> RouteDecision:
        """创建降级决策"""
        logger.warning(f"Creating fallback decision: {reason}")
        
        return RouteDecision(
            intent="unknown",
            confidence=0.0,
            reasoning=f"降级决策: {reason}",
            response="抱歉，我没有理解您的意思。能否再详细描述一下？",
            should_wait=True,
            target_nodes=[],
            metadata={"fallback": True, "reason": reason}
        )
    
    # ========================================================================
    # 配置管理
    # ========================================================================
    
    def add_route(self, route: RouteConfig):
        """添加路由配置"""
        self.rule_engine.add_route(route)
    
    def remove_route(self, route_id: str):
        """移除路由配置"""
        self.rule_engine.remove_route(route_id)
    
    def update_available_nodes(self, nodes: list[str]):
        """更新可用节点列表"""
        self.available_nodes = nodes
        if self.intent_analyzer:
            self.intent_analyzer.update_available_nodes(nodes)
    
    def set_strategy(self, strategy: str):
        """设置路由策略"""
        self.strategy = strategy
        logger.info("Router strategy updated", strategy=strategy)
    
    def register_custom_function(self, name: str, func):
        """注册自定义函数（用于规则引擎）"""
        self.rule_engine.register_function(name, func)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "RouterSystem",
    "RouterStrategy",
]

