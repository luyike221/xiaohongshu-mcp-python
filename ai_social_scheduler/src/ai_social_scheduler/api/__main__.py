"""FastAPI 服务器启动脚本

运行方式：
    python -m ai_social_scheduler.api
    或
    uvicorn ai_social_scheduler.api:app --host 0.0.0.0 --port 8000
"""

import uvicorn

from .app import create_app

if __name__ == "__main__":
    # 创建应用
    app = create_app()
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

