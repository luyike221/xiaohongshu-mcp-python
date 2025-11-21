"""后台任务"""

from .celery_app import celery_app


@celery_app.task
def background_content_publish(content_id: str):
    """后台内容发布任务"""
    # TODO: 实现后台内容发布逻辑
    pass


@celery_app.task
def background_interaction_response(interaction_id: str):
    """后台互动回复任务"""
    # TODO: 实现后台互动回复逻辑
    pass

