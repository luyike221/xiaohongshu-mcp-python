"""内容发布API"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...ai_agent.supervisor.factory import create_supervisor_with_agents
from ...ai_agent.supervisor import Supervisor
from ...ai_agent.tools.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/content", tags=["content"])

# 全局Supervisor实例（在实际应用中，应该使用依赖注入或单例模式）
_supervisor: Optional[Supervisor] = None


async def get_supervisor() -> Supervisor:
    """获取Supervisor实例（依赖注入）"""
    global _supervisor
    if _supervisor is None:
        _supervisor = await create_supervisor_with_agents()
    return _supervisor


class ContentPublishRequest(BaseModel):
    """内容发布请求"""
    
    user_id: str = Field(..., description="用户ID")
    request: str = Field(..., description="用户请求内容")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")


class ContentPublishResponse(BaseModel):
    """内容发布响应"""
    
    success: bool = Field(..., description="是否成功")
    workflow: str = Field(..., description="工作流名称")
    result: Dict[str, Any] = Field(..., description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")


@router.post("/publish", response_model=ContentPublishResponse)
async def publish_content(
    request: ContentPublishRequest,
    supervisor: Supervisor = Depends(get_supervisor),
) -> ContentPublishResponse:
    """发布内容
    
    流程：
    1. API服务层接收用户请求
    2. AI决策引擎理解需求
    3. 策略管理器生成内容策略
    4. 调用图视频生成服务生成素材
    5. 调用小红书MCP服务发布内容
    6. 状态管理器记录执行结果
    7. 返回结果给用户
    """
    try:
        logger.info(
            "Content publish request received",
            user_id=request.user_id,
            request=request.request
        )
        
        # 构建输入数据
        input_data = {
            "user_id": request.user_id,
            "request": request.request,
            "content": request.request,  # 兼容性
            "context": request.context or {},
        }
        
        # 执行工作流
        result = await supervisor.execute_workflow(
            workflow_name="content_publish",
            input_data=input_data,
            config={
                "configurable": {
                    "workflow": "content_publish",
                    "thread_id": request.user_id,
                }
            }
        )
        
        logger.info(
            "Content publish completed",
            user_id=request.user_id,
            success=True
        )
        
        return ContentPublishResponse(
            success=True,
            workflow="content_publish",
            result=result,
        )
        
    except Exception as e:
        logger.error(
            "Content publish failed",
            user_id=request.user_id,
            error=str(e),
            exc_info=True
        )
        
        return ContentPublishResponse(
            success=False,
            workflow="content_publish",
            result={},
            error=str(e),
        )


@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    supervisor: Supervisor = Depends(get_supervisor),
) -> Dict[str, Any]:
    """获取工作流状态"""
    try:
        state = supervisor.get_state(workflow_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return state
    except Exception as e:
        logger.error("Failed to get workflow status", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

