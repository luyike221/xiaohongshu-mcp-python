"""内容发布工作流（基于 LangGraph 的多 Agent 编排）"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import END, StateGraph

from .state import AgentState
from ..tools.logging import get_logger

if TYPE_CHECKING:
    from ..supervisor.decision_engine import DecisionEngine
    from ..supervisor.state_manager import StateManager
    from ..supervisor.strategy_manager import StrategyManager

logger = get_logger(__name__)


def _append_log(state: AgentState, entry: Dict[str, Any]) -> Dict[str, Any]:
    """追加单条日志，返回新的日志列表。"""
    logs = list(state.get("logs", []))
    logs.append(entry)
    return {"logs": logs}


def _serialize_result(result: Any) -> Any:
    """将结果序列化为 JSON 兼容格式
    
    处理 LangChain 消息对象等不可序列化的类型
    
    Args:
        result: 需要序列化的结果
    
    Returns:
        可序列化的结果
    """
    if isinstance(result, BaseMessage):
        # 将 LangChain 消息对象转换为字典
        return {
            "type": type(result).__name__,
            "content": result.content if hasattr(result, "content") else str(result),
            "role": getattr(result, "role", None),
        }
    elif isinstance(result, dict):
        # 递归处理字典
        return {k: _serialize_result(v) for k, v in result.items()}
    elif isinstance(result, (list, tuple)):
        # 递归处理列表
        return [_serialize_result(item) for item in result]
    elif hasattr(result, "__dict__"):
        # 处理其他对象，尝试转换为字典
        try:
            return {k: _serialize_result(v) for k, v in result.__dict__.items()}
        except Exception:
            return str(result)
    else:
        # 基本类型直接返回
        return result


def create_content_publish_workflow(
    *,
    decision_engine: "DecisionEngine",
    strategy_manager: "StrategyManager",
    material_agent: Any,
    content_agent: Any,
    publisher_agent: Any,
    state_manager: "StateManager",
) -> Any:
    """构建并编译内容发布工作流图。"""

    workflow = StateGraph(AgentState)

    async def entry_node(state: AgentState) -> Dict[str, Any]:
        request = state.get("request")
        if not request:
            return {
                "error": "request 字段不能为空",
                "failed_step": "entry",
            }

        workflow_id = state.get(
            "workflow_id",
            f"content_publish_{state.get('user_id', 'unknown')}",
        )
        
        logger.info("📋 [步骤 1/7] 初始化工作流", workflow_id=workflow_id, user_request=request[:50] + "...")

        await state_manager.record_execution_result(
            workflow_id=workflow_id,
            step="start",
            result={"workflow": "content_publish"},
            status="running",
        )

        updates: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "workflow_name": "content_publish",
            "status": "running",
            "current_step": "start",
        }
        updates.update(_append_log(state, {"step": "start", "status": "running"}))
        return updates

    async def understand_request_node(state: AgentState) -> Dict[str, Any]:
        workflow_id = state.get("workflow_id", "content_publish_unknown")
        logger.info("🧠 [步骤 2/7] 理解用户需求 - 调用 AI 决策引擎分析意图...")
        try:
            understanding = await decision_engine.understand_request(
                state["request"],
                state.get("context", {}),
            )
            logger.info("✅ 需求理解完成", intent=understanding.get("intent", ""), workflow=understanding.get("workflow", ""))
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="understand_request",
                result=understanding,
                status="success",
            )
            updates = {
                "understanding": understanding,
                "current_step": "understand_request",
            }
            updates.update(
                _append_log(
                    state,
                    {"step": "understand_request", "status": "success"},
                )
            )
            return updates
        except Exception as exc:  # pragma: no cover - 依赖外部LLM
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="understand_request",
                result={"error": str(exc)},
                status="failed",
            )
            return {
                "error": f"意图理解失败：{exc}",
                "failed_step": "understand_request",
            }

    async def strategy_node(state: AgentState) -> Dict[str, Any]:
        workflow_id = state.get("workflow_id", "content_publish_unknown")
        logger.info("📝 [步骤 3/7] 生成内容策略 - 确定话题、风格、关键词...")
        try:
            strategy = await strategy_manager.generate_content_strategy(
                state["request"],
                {
                    "context": state.get("context", {}),
                    "understanding": state.get("understanding", {}),
                },
            )
            logger.info("✅ 策略生成完成", topic=strategy.get("topic", ""), style=strategy.get("style", ""), keywords=strategy.get("keywords", []))
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="generate_strategy",
                result=strategy,
                status="success",
            )
            updates = {
                "strategy": strategy,
                "current_step": "generate_strategy",
            }
            updates.update(
                _append_log(
                    state,
                    {"step": "generate_strategy", "status": "success"},
                )
            )
            return updates
        except Exception as exc:  # pragma: no cover - 依赖外部LLM
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="generate_strategy",
                result={"error": str(exc)},
                status="failed",
            )
            return {
                "error": f"策略生成失败：{exc}",
                "failed_step": "generate_strategy",
            }

    async def material_node(state: AgentState) -> Dict[str, Any]:
        workflow_id = state.get("workflow_id", "content_publish_unknown")
        strategy = state.get("strategy", {})
        image_count = (
            state.get("context", {}).get("image_count")
            or strategy.get("image_count")
            or 3
        )
        logger.info(f"🎨 [步骤 4/7] 生成素材 - MaterialAgent 将生成 {image_count} 张图片（需要较长时间）...")
        prompt = (
            "请为以下小红书图文内容生成素材：\n"
            f"- 主题：{strategy.get('topic')}\n"
            f"- 风格：{strategy.get('style')}\n"
            f"- 关键词：{strategy.get('keywords')}\n"
            f"- 图片数量：{image_count}\n"
            "需要输出结构化的素材描述，包含图片意图、构图建议、光线或氛围提示等。"
        )
        try:
            material_payload = {
                "task": prompt,
                "request": state["request"],
                "context": state.get("context", {}),
                "strategy": strategy,
            }
            material_result = await material_agent.run(material_payload)
            success = material_result.get("success", False)
            logger.info("✅ 素材生成完成" if success else "❌ 素材生成失败")
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="generate_material",
                result=material_result,
                status="success" if success else "failed",
            )
            if not success:
                return {
                    "error": "素材生成失败",
                    "failed_step": "generate_material",
                }
            updates = {
                "materials": material_result.get("result", {}),
                "current_step": "generate_material",
            }
            updates.update(
                _append_log(
                    state,
                    {
                        "step": "generate_material",
                        "status": "success",
                        "detail": f"material_agent: {material_agent.name}",
                    },
                )
            )
            return updates
        except Exception as exc:
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="generate_material",
                result={"error": str(exc)},
                status="failed",
            )
            return {
                "error": f"素材生成异常：{exc}",
                "failed_step": "generate_material",
            }

    async def content_node(state: AgentState) -> Dict[str, Any]:
        workflow_id = state.get("workflow_id", "content_publish_unknown")
        logger.info("✍️  [步骤 5/7] 生成文案 - ContentAgent 创建标题、正文、标签...")
        try:
            result = await content_agent.run(
                {
                    "strategy": state.get("strategy", {}),
                    "materials": state.get("materials", {}),
                    "context": state.get("context", {}),
                    "request": state["request"],
                }
            )
            success = result.get("success", False)
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="content_generation",
                result=result,
                status="success" if success else "failed",
            )
            if not success:
                return {
                    "error": "内容生成失败",
                    "failed_step": "content_generation",
                }
            updates = {
                "content_result": {
                    "title": result.get("title"),
                    "content": result.get("content"),
                    "tags": result.get("tags"),
                },
                "current_step": "content_generation",
            }
            updates.update(
                _append_log(
                    state,
                    {"step": "content_generation", "status": "success"},
                )
            )
            return updates
        except Exception as exc:
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="content_generation",
                result={"error": str(exc)},
                status="failed",
            )
            return {
                "error": f"内容生成异常：{exc}",
                "failed_step": "content_generation",
            }

    async def publish_node(state: AgentState) -> Dict[str, Any]:
        workflow_id = state.get("workflow_id", "content_publish_unknown")
        content_result = state.get("content_result", {})
        strategy = state.get("strategy", {})
        materials = state.get("materials", {})
        
        logger.info("📤 [步骤 6/7] 发布内容 - XiaohongshuAgent 发布到小红书平台...")

        # 序列化 materials，处理可能包含的 LangChain 消息对象
        serialized_materials = _serialize_result(materials)
        
        publish_prompt = (
            "请将以下内容发布到小红书：\n"
            f"- 标题：{content_result.get('title')}\n"
            f"- 标签：{content_result.get('tags')}\n"
            f"- 正文：{content_result.get('content')}\n"
            f"- 关键词：{strategy.get('keywords')}\n"
            f"- 素材：{json.dumps(serialized_materials, ensure_ascii=False)}\n"
            "如果素材是图片，请在调用 publish_content 工具时一并附带。"
        )
        try:
            result = await publisher_agent.run(
                {"messages": [HumanMessage(content=publish_prompt)]}
            )
            success = result.get("success", False)
            logger.info("✅ 内容发布成功" if success else "❌ 内容发布失败")
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="publish_content",
                result=result,
                status="success" if success else "failed",
            )
            if not success:
                return {
                    "error": "内容发布失败",
                    "failed_step": "publish_content",
                }
            updates = {
                "publish_result": result.get("result"),
                "current_step": "publish_content",
            }
            updates.update(
                _append_log(
                    state,
                    {"step": "publish_content", "status": "success"},
                )
            )
            return updates
        except Exception as exc:
            await state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="publish_content",
                result={"error": str(exc)},
                status="failed",
            )
            return {
                "error": f"发布异常：{exc}",
                "failed_step": "publish_content",
            }

    async def record_result_node(state: AgentState) -> Dict[str, Any]:
        workflow_id = state.get("workflow_id", "content_publish_unknown")
        logger.info("💾 [步骤 7/7] 记录结果 - 保存工作流执行记录...")
        final_result = {
            "understanding": state.get("understanding"),
            "strategy": state.get("strategy"),
            "materials": state.get("materials"),
            "content": state.get("content_result"),
            "publish": state.get("publish_result"),
        }
        await state_manager.record_execution_result(
            workflow_id=workflow_id,
            step="complete",
            result=final_result,
            status="success",
        )
        logger.info("🎉 工作流执行完成！所有步骤已成功完成。")
        updates = {
            "status": "completed",
            "result": final_result,
            "current_step": "complete",
        }
        updates.update(
            _append_log(
                state,
                {"step": "complete", "status": "success"},
            )
        )
        return updates

    async def handle_error_node(state: AgentState) -> Dict[str, Any]:
        workflow_id = state.get("workflow_id", "content_publish_unknown")
        error_message = state.get("error") or "未知错误"
        failed_step = state.get("failed_step", "unknown")
        await state_manager.record_execution_result(
            workflow_id=workflow_id,
            step=failed_step,
            result={"error": error_message},
            status="failed",
        )
        return {
            "status": "failed",
            "current_step": failed_step,
            "result": {
                "error": error_message,
                "step": failed_step,
            },
        }

    def _route(target: str) -> Callable[[AgentState], str]:
        def _inner(state: AgentState) -> str:
            return "error" if state.get("error") else target

        return _inner

    workflow.add_node("entry", entry_node)
    workflow.add_node("understand_request", understand_request_node)
    workflow.add_node("generate_strategy", strategy_node)
    workflow.add_node("generate_material", material_node)
    workflow.add_node("content_generation", content_node)
    workflow.add_node("publish_content", publish_node)
    workflow.add_node("record_result", record_result_node)
    workflow.add_node("handle_error", handle_error_node)

    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "understand_request")
    workflow.add_conditional_edges(
        "understand_request",
        _route("generate_strategy"),
        {
            "error": "handle_error",
            "generate_strategy": "generate_strategy",
        },
    )
    workflow.add_conditional_edges(
        "generate_strategy",
        _route("generate_material"),
        {
            "error": "handle_error",
            "generate_material": "generate_material",
        },
    )
    workflow.add_conditional_edges(
        "generate_material",
        _route("content_generation"),
        {
            "error": "handle_error",
            "content_generation": "content_generation",
        },
    )
    workflow.add_conditional_edges(
        "content_generation",
        _route("publish_content"),
        {
            "error": "handle_error",
            "publish_content": "publish_content",
        },
    )
    workflow.add_conditional_edges(
        "publish_content",
        _route("record_result"),
        {
            "error": "handle_error",
            "record_result": "record_result",
        },
    )
    workflow.add_edge("record_result", END)
    workflow.add_edge("handle_error", END)

    return workflow.compile()

