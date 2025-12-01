#!/usr/bin/env python3
"""启动 FastAPI 服务器"""

import sys
import uvicorn

from ai_social_scheduler.api import create_app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8012,
        log_level="info",
    )
