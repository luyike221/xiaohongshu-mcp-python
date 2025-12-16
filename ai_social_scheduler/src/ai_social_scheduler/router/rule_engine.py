"""规则引擎 - 基于规则的快速路由

重构核心：使用规则引擎实现快速、确定性的路由决策
"""

import re
from typing import Any, Callable, Optional

from ..core.route import (
    MatchMode,
    RouteConfig,
    RouteDecision,
    RouteRule,
    RouteTrigger,
    TriggerType,
)
from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 规则引擎
# ============================================================================

class RuleEngine:
    """规则引擎 - 基于规则的路由决策
    
    核心职责：
    1. 加载和管理路由规则
    2. 快速匹配规则
    3. 执行条件判断
    4. 返回路由决策
    
    设计理念：
    - 高效：优先级排序，快速退出
    - 灵活：支持多种匹配模式
    - 可扩展：支持自定义函数
    - 确定性：规则明确，结果可预测
    """
    
    def __init__(self, routes: Optional[list[RouteConfig]] = None):
        """初始化规则引擎
        
        Args:
            routes: 路由配置列表
        """
        self.routes: list[RouteConfig] = routes or []
        self._custom_functions: dict[str, Callable] = {}
        
        # 按优先级排序路由
        self._sort_routes()
        
        logger.info(
            "RuleEngine initialized",
            routes_count=len(self.routes)
        )
    
    def _sort_routes(self):
        """按优先级排序路由（基于规则优先级）"""
        # 简单实现：按第一个规则的优先级排序
        self.routes.sort(
            key=lambda r: max([rule.priority for rule in r.rules] or [0]),
            reverse=True
        )
    
    def add_route(self, route: RouteConfig):
        """添加路由配置"""
        self.routes.append(route)
        self._sort_routes()
        logger.info("Route added", route_id=route.route_id)
    
    def remove_route(self, route_id: str):
        """移除路由配置"""
        self.routes = [r for r in self.routes if r.route_id != route_id]
        logger.info("Route removed", route_id=route_id)
    
    def register_function(self, name: str, func: Callable):
        """注册自定义函数
        
        Args:
            name: 函数名称
            func: 函数对象（签名：func(input: str, context: dict) -> bool）
        """
        self._custom_functions[name] = func
        logger.info("Custom function registered", name=name)
    
    def match(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[RouteDecision]:
        """匹配路由规则
        
        Args:
            user_input: 用户输入
            context: 上下文信息
        
        Returns:
            RouteDecision: 匹配的路由决策，如果没有匹配则返回 None
        """
        context = context or {}
        
        logger.info(
            "Matching rules",
            input_length=len(user_input),
            routes_count=len(self.routes),
            user_input=user_input[:100]  # 添加用户输入日志
        )
        
        # 遍历路由配置
        for route in self.routes:
            logger.debug(
                "Checking route",
                route_id=route.route_id,
                enabled=route.enabled,
                target_nodes=route.target_nodes
            )
            
            if not route.enabled:
                logger.debug(f"Route disabled: {route.route_id}")
                continue
            
            # 检查触发器
            triggered, trigger_names = self._check_triggers(
                route.triggers,
                user_input,
                context
            )
            
            logger.debug(
                "Trigger check result",
                route_id=route.route_id,
                triggered=triggered,
                trigger_names=trigger_names
            )
            
            if not triggered:
                logger.debug(f"Route not triggered: {route.route_id}")
                continue
            
            logger.info(
                "Route triggered",
                route_id=route.route_id,
                triggers=trigger_names
            )
            
            # 检查规则
            matched, matched_rule = self._check_rules(
                route.rules,
                user_input,
                context
            )
            
            logger.debug(
                "Rule check result",
                route_id=route.route_id,
                matched=matched,
                rule_id=matched_rule.rule_id if matched_rule else None
            )
            
            if not matched:
                logger.debug(f"Route rules not matched: {route.route_id}")
                continue
            
            logger.info(
                "Rule matched",
                route_id=route.route_id,
                rule_id=matched_rule.rule_id if matched_rule else None,
                rule_target=matched_rule.target if matched_rule else None
            )
            
            # 生成决策
            decision = self._create_decision(
                route,
                matched_rule,
                trigger_names,
                context
            )
            
            logger.info(
                "RouteDecision created",
                route_id=decision.route_id,
                target_nodes=decision.target_nodes,
                target_nodes_count=len(decision.target_nodes),
                strategy=decision.strategy.value
            )
            
            return decision
        
        logger.info("No rule matched")
        return None
    
    def _check_triggers(
        self,
        triggers: list[RouteTrigger],
        user_input: str,
        context: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """检查触发器
        
        Returns:
            (是否触发, 触发器名称列表)
        """
        if not triggers:
            return True, []
        
        enabled_triggers = [t for t in triggers if t.enabled]
        if not enabled_triggers:
            return True, []
        
        matched_triggers = []
        
        for trigger in enabled_triggers:
            if self._check_single_trigger(trigger, user_input, context):
                matched_triggers.append(trigger.type.value)
        
        # 根据匹配模式判断
        # 这里简化处理，只要有一个触发器匹配就认为触发
        return len(matched_triggers) > 0, matched_triggers
    
    def _check_single_trigger(
        self,
        trigger: RouteTrigger,
        user_input: str,
        context: dict[str, Any],
    ) -> bool:
        """检查单个触发器"""
        try:
            if trigger.type == TriggerType.ALWAYS:
                return True
            
            elif trigger.type == TriggerType.KEYWORD:
                return self._check_keywords(
                    trigger.keywords,
                    user_input,
                    trigger.case_sensitive
                )
            
            elif trigger.type == TriggerType.REGEX:
                return self._check_regex(
                    trigger.patterns,
                    user_input
                )
            
            elif trigger.type == TriggerType.FUNCTION:
                return self._check_function(
                    trigger.function_name,
                    user_input,
                    context
                )
            
            # INTENT 类型需要 LLM，这里不处理
            return False
            
        except Exception as e:
            logger.error(f"Trigger check failed: {e}")
            return False
    
    def _check_keywords(
        self,
        keywords: list[str],
        text: str,
        case_sensitive: bool = False,
    ) -> bool:
        """检查关键词匹配"""
        if not keywords:
            return False
        
        check_text = text if case_sensitive else text.lower()
        
        for keyword in keywords:
            check_keyword = keyword if case_sensitive else keyword.lower()
            if check_keyword in check_text:
                return True
        
        return False
    
    def _check_regex(
        self,
        patterns: list[str],
        text: str,
    ) -> bool:
        """检查正则表达式匹配"""
        if not patterns:
            return False
        
        for pattern in patterns:
            try:
                if re.search(pattern, text):
                    return True
            except re.error as e:
                logger.error(f"Invalid regex pattern: {pattern}, error: {e}")
        
        return False
    
    def _check_function(
        self,
        function_name: Optional[str],
        user_input: str,
        context: dict[str, Any],
    ) -> bool:
        """检查自定义函数"""
        if not function_name:
            return False
        
        func = self._custom_functions.get(function_name)
        if not func:
            logger.warning(f"Function not found: {function_name}")
            return False
        
        try:
            return bool(func(user_input, context))
        except Exception as e:
            logger.error(f"Function execution failed: {function_name}, error: {e}")
            return False
    
    def _check_rules(
        self,
        rules: list[RouteRule],
        user_input: str,
        context: dict[str, Any],
    ) -> tuple[bool, Optional[RouteRule]]:
        """检查路由规则
        
        Returns:
            (是否匹配, 匹配的规则)
        """
        if not rules:
            return True, None
        
        # 按优先级排序
        sorted_rules = sorted(
            [r for r in rules if r.enabled],
            key=lambda x: x.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            if self._evaluate_condition(rule.condition, user_input, context):
                return True, rule
        
        return False, None
    
    def _evaluate_condition(
        self,
        condition: str,
        user_input: str,
        context: dict[str, Any],
    ) -> bool:
        """评估条件表达式
        
        简单实现，支持基本的条件判断
        """
        try:
            logger.debug(
                "Evaluating condition",
                condition=condition,
                user_input=user_input[:50]
            )
            
            # 特殊条件
            if condition == "default" or condition == "always":
                logger.debug("Condition matched: default/always")
                return True
            
            # 包含判断
            if "contains" in condition:
                # 格式：message contains "关键词"
                match = re.search(r'contains\s+"([^"]+)"', condition)
                if match:
                    keyword = match.group(1)
                    result = keyword in user_input
                    logger.debug(
                        "Contains check",
                        keyword=keyword,
                        found=result,
                        user_input=user_input[:50]
                    )
                    return result
                else:
                    logger.warning(f"Failed to parse contains condition: {condition}")
            
            # 支持 or 逻辑
            if " or " in condition:
                parts = condition.split(" or ")
                for part in parts:
                    part = part.strip()
                    if self._evaluate_condition(part, user_input, context):
                        logger.debug(f"OR condition matched: {part}")
                        return True
                logger.debug("OR condition not matched")
                return False
            
            # 等于判断
            if "==" in condition:
                # 简单实现
                parts = condition.split("==")
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip().strip('"\'')
                    
                    # 从 context 获取值
                    if left in context:
                        result = str(context[left]) == right
                        logger.debug(f"Equality check: {left} == {right} -> {result}")
                        return result
            
            # TODO: 支持更复杂的条件表达式
            # 可以考虑使用 simpleeval 库
            
            logger.debug(f"Condition not matched: {condition}")
            return False
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {condition}, error: {e}", exc_info=True)
            return False
    
    def _create_decision(
        self,
        route: RouteConfig,
        rule: Optional[RouteRule],
        trigger_names: list[str],
        context: dict[str, Any],
    ) -> RouteDecision:
        """创建路由决策"""
        logger.debug(
            "Creating RouteDecision",
            route_id=route.route_id,
            route_target_nodes=route.target_nodes,
            rule_target=rule.target if rule else None,
            rule_id=rule.rule_id if rule else None
        )
        
        # 优先使用 rule.target，如果没有则使用 route.target_nodes
        target_nodes = route.target_nodes
        if rule and hasattr(rule, 'target') and rule.target:
            # 如果 rule.target 是单个节点，转换为列表
            if isinstance(rule.target, str):
                target_nodes = [rule.target]
            elif isinstance(rule.target, list):
                target_nodes = rule.target
        
        logger.info(
            "RouteDecision target_nodes determined",
            route_id=route.route_id,
            rule_target=rule.target if rule else None,
            route_target_nodes=route.target_nodes,
            final_target_nodes=target_nodes
        )
        
        return RouteDecision(
            route_id=route.route_id,
            target_nodes=target_nodes,
            strategy=route.strategy,
            intent=route.name,
            confidence=1.0,  # 规则匹配的置信度为 1.0
            reasoning=f"匹配规则: {rule.rule_id if rule else 'default'}",
            response="",  # 规则引擎不生成回复，由后续处理
            matched_triggers=trigger_names,
            matched_rules=[rule.rule_id] if rule else [],
            metadata={
                "engine": "rule",
                "route_id": route.route_id,
            }
        )


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "RuleEngine",
]

