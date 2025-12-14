# FastMCP 如何向外部提供 MCP 服务

本文档说明如何使用 FastMCP 框架向外部提供 MCP (Model Context Protocol) 服务。

## 📋 目录

1. [基本概念](#基本概念)
2. [快速开始](#快速开始)
3. [传输方式](#传输方式)
4. [配置选项](#配置选项)
5. [客户端接入](#客户端接入)
6. [最佳实践](#最佳实践)

## 基本概念

FastMCP 是一个用于构建 MCP 服务器的 Python 框架。它支持多种传输方式，可以将 MCP 服务暴露给外部客户端。

### 核心组件

1. **FastMCP 实例**：创建 MCP 服务器实例
2. **工具注册**：使用装饰器注册 MCP 工具函数
3. **服务启动**：使用 `run()` 方法启动服务

## 快速开始

### 1. 创建 FastMCP 实例

```python
from fastmcp import FastMCP

# 创建 FastMCP 实例
mcp = FastMCP("your-service-name")
```

### 2. 注册工具函数

使用 `@mcp.tool` 装饰器注册工具：

```python
@mcp.tool
async def your_tool_function(
    param1: str,
    param2: int = 10
) -> dict:
    """
    工具函数描述
    
    Args:
        param1: 参数1说明
        param2: 参数2说明（可选，默认值10）
        
    Returns:
        返回结果字典
    """
    # 实现工具逻辑
    return {
        "success": True,
        "result": "操作结果"
    }
```

### 3. 启动服务

```python
# HTTP 传输方式
mcp.run(transport="http", host="0.0.0.0", port=8000)

# SSE 传输方式
mcp.run(transport="sse", host="0.0.0.0", port=8000)

# stdio 传输方式（用于命令行调用）
mcp.run(transport="stdio")
```

## 传输方式

FastMCP 支持三种传输方式：

### 1. HTTP 传输 (`transport="http"`)

**适用场景**：Web 应用、远程服务、Docker 容器

**特点**：
- 支持跨网络访问
- 适合生产环境部署
- 需要指定 host 和 port

**示例**：

```python
# 启动 HTTP 服务
mcp.run(
    transport="http",
    host="0.0.0.0",  # 监听所有网络接口
    port=8000        # 监听端口
)
```

**访问地址**：
- MCP 端点：`http://localhost:8000/mcp`
- 健康检查：`http://localhost:8000/health`

### 2. SSE 传输 (`transport="sse"`)

**适用场景**：需要服务器推送的场景

**特点**：
- 基于 Server-Sent Events
- 支持实时数据推送
- 需要指定 host 和 port

**示例**：

```python
# 启动 SSE 服务
mcp.run(
    transport="sse",
    host="0.0.0.0",
    port=8000
)
```

### 3. stdio 传输 (`transport="stdio"`)

**适用场景**：命令行工具、本地进程通信

**特点**：
- 通过标准输入/输出通信
- 适合本地调用
- 不需要网络端口

**示例**：

```python
# 启动 stdio 服务
mcp.run(transport="stdio")
```

**使用方式**：

```bash
# 通过命令行调用
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python your_script.py
```

## 配置选项

### HTTP/SSE 传输配置

```python
mcp.run(
    transport="http",  # 或 "sse"
    host="0.0.0.0",    # 监听地址
    port=8000,         # 监听端口
    # 其他可选参数
)
```

### 环境变量配置

可以通过环境变量配置服务器：

```bash
# 设置服务器地址
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8000
```

在代码中读取：

```python
import os
from fastmcp import FastMCP

mcp = FastMCP("your-service")

host = os.getenv("SERVER_HOST", "127.0.0.1")
port = int(os.getenv("SERVER_PORT", "8000"))

mcp.run(transport="http", host=host, port=port)
```

### 完整示例

参考项目中的实现：

```python
# src/xiaohongshu_mcp_python/main.py
from fastmcp import FastMCP
from .config import settings
from .server.mcp_tools import mcp

def main():
    # 从配置读取服务器地址和端口
    host = settings.SERVER_HOST  # 默认: 127.0.0.1
    port = settings.SERVER_PORT  # 默认: 8000
    
    # 启动 HTTP 服务
    mcp.run(transport="http", host=host, port=port)
```

## 客户端接入

### 1. Claude Desktop

在 Claude Desktop 配置文件中添加：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "xiaohongshu-mcp": {
      "command": "python",
      "args": [
        "-m",
        "xiaohongshu_mcp_python.main"
      ],
      "env": {
        "ENV": "production"
      }
    }
  }
}
```

### 2. 使用 langchain_mcp_adapters 连接

**安装依赖**：
```bash
pip install langchain-mcp-adapters
```

**HTTP 传输方式**（推荐，适用于已启动的服务）：

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def connect_xiaohongshu_mcp():
    # 连接 MCP 服务（HTTP 传输）
    client = MultiServerMCPClient({
        "xiaohongshu": {
            "url": "http://127.0.0.1:8000/mcp",  # 服务地址
            "transport": "streamable_http",
        }
    })
    
    async with client:
        # 获取所有可用工具
        tools = await client.get_tools()
        print(f"可用工具: {[tool.name for tool in tools]}")
        
        # 调用工具
        login_tool = next((t for t in tools if t.name == "xiaohongshu_check_login_session"), None)
        if login_tool:
            result = await login_tool.ainvoke({})
            print(f"结果: {result}")

# 运行
asyncio.run(connect_xiaohongshu_mcp())
```

**stdio 传输方式**（本地进程）：

```python
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "xiaohongshu": {
        "command": sys.executable,  # Python 解释器路径
        "args": ["-m", "xiaohongshu_mcp_python.main"],
        "transport": "stdio",
    }
})

async with client:
    tools = await client.get_tools()
    # 使用工具...
```

**与 LangChain Agent 结合使用**：

```python
from langchain.agents import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 连接 MCP 服务
client = MultiServerMCPClient({
    "xiaohongshu": {
        "url": "http://127.0.0.1:8000/mcp",
        "transport": "streamable_http",
    }
})

async with client:
    # 获取工具
    tools = await client.get_tools()
    
    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    
    # 创建 Agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个小红书内容管理助手。"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_react_agent(llm, tools, prompt=prompt)
    
    # 使用 Agent
    response = await agent.ainvoke({
        "input": "检查一下我的小红书登录状态",
        "chat_history": []
    })
    
    print(response["messages"][-1].content)
```

**完整示例代码**：参考 `examples/connect_with_langchain.py`

### 3. HTTP 客户端接入（原始方式）

如果使用 HTTP 传输，客户端可以通过 HTTP 请求访问：

```python
import httpx

# 客户端示例
async with httpx.AsyncClient() as client:
    # 调用工具
    response = await client.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "your_tool_function",
                "arguments": {
                    "param1": "value1",
                    "param2": 20
                }
            },
            "id": 1
        }
    )
    result = response.json()
```

### 4. MCP Inspector 测试

使用 MCP Inspector 测试连接：

```bash
# 安装 Inspector
npx @modelcontextprotocol/inspector

# 对于 HTTP 传输
npx @modelcontextprotocol/inspector http://localhost:8000/mcp

# 对于 stdio 传输
npx @modelcontextprotocol/inspector python -m xiaohongshu_mcp_python.main
```

## 最佳实践

### 1. 生产环境部署

**使用 HTTP 传输 + Docker**：

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "-m", "xiaohongshu_mcp_python.main", "--env", "production", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
```

### 2. 开发环境

**使用 stdio 传输**：

```python
# 开发时使用 stdio，方便调试
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### 3. 安全配置

**限制访问地址**：

```python
# 仅允许本地访问
mcp.run(transport="http", host="127.0.0.1", port=8000)

# 允许所有网络接口访问（生产环境）
mcp.run(transport="http", host="0.0.0.0", port=8000)
```

**添加认证**（需要自定义实现）：

```python
from fastapi import Request, HTTPException
from fastmcp import FastMCP

mcp = FastMCP("your-service")

# 自定义中间件（示例）
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token or token != "your-secret-token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)
```

### 4. 日志和监控

```python
from loguru import logger

@mcp.tool
async def your_tool(param: str) -> dict:
    logger.info(f"调用工具，参数: {param}")
    try:
        # 工具逻辑
        result = {"success": True}
        logger.info("工具执行成功")
        return result
    except Exception as e:
        logger.error(f"工具执行失败: {e}")
        return {"success": False, "error": str(e)}
```

### 5. 错误处理

```python
@mcp.tool
async def your_tool(param: str) -> dict:
    try:
        # 参数验证
        if not param:
            return {
                "success": False,
                "error": "参数不能为空"
            }
        
        # 业务逻辑
        result = process(param)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.exception("工具执行异常")
        return {
            "success": False,
            "error": str(e)
        }
```

## 项目示例

参考本项目中的实现：

1. **MCP 实例创建**：`src/xiaohongshu_mcp_python/server/mcp_tools.py`
   ```python
   from fastmcp import FastMCP
   mcp = FastMCP("xiaohongshu-mcp-server")
   ```

2. **工具注册**：使用 `@mcp.tool` 装饰器
   ```python
   @mcp.tool
   async def xiaohongshu_publish_content(...):
       # 工具实现
   ```

3. **服务启动**：`src/xiaohongshu_mcp_python/main.py`
   ```python
   mcp.run(transport="http", host=host, port=port)
   ```

## 常见问题

### Q: 如何同时支持多种传输方式？

A: FastMCP 一次只能使用一种传输方式。如果需要支持多种方式，可以：
- 启动多个进程，每个进程使用不同的传输方式
- 使用反向代理（如 Nginx）将 HTTP 请求转发到不同的服务

### Q: HTTP 传输的端点是什么？

A: 默认端点是 `/mcp`，完整地址为 `http://host:port/mcp`

### Q: 如何测试 MCP 服务？

A: 使用 MCP Inspector：
```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

### Q: 生产环境推荐使用哪种传输方式？

A: 推荐使用 **HTTP 传输**，因为：
- 支持跨网络访问
- 易于部署和监控
- 可以配合负载均衡和反向代理

## 参考资源

- [FastMCP 官方文档](https://github.com/jlowin/fastmcp)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [项目 README](../README.md)

