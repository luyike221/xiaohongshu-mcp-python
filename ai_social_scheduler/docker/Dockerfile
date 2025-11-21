FROM python:3.11-slim

WORKDIR /app

# 安装 Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装依赖
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["poetry", "run", "uvicorn", "src.xiaohongshu_agent.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

