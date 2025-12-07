#!/bin/bash

# 激活虚拟环境
source /data/mxpt/z-image/venv/bin/activate

# 运行 FastAPI 应用
uvicorn app:app --host 0.0.0.0 --port 8000

