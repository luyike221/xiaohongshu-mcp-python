# 小红书运营Agent使用指南

## 概述

本系统实现了基于Supervisor架构的小红书内容发布工作流，包含以下组件：

- **Supervisor（主管）**：协调各个专业智能体
  - AI决策引擎：理解需求、分析内容、生成决策
  - 策略管理器：生成内容策略、选择话题和模板
  - 状态管理器：记录执行结果、管理全局状态

- **专业智能体（Agents）**：
  - 图视频生成智能体（material_generator）
  - 小红书MCP服务智能体（xiaohongshu_mcp）
  - 内容生成智能体（content_generator）
  - 数据分析智能体（data_analysis）
  - 异常处理智能体（exception_handling）

## 工作流程

### 流程1：用户请求内容发布

```
用户输入请求
    ↓
API服务层接收
    ↓
AI决策引擎理解需求
    ↓
策略管理器生成内容策略
    ↓
调用图视频生成服务生成素材
    ↓
调用小红书MCP服务发布内容
    ↓
状态管理器记录执行结果
    ↓
返回结果给用户
```

## 使用方法

### 1. 启动API服务

```bash
# 使用uvicorn启动FastAPI服务
uvicorn src.ai_social_scheduler.web.app:app --host 0.0.0.0 --port 8000
```

### 2. 调用API发布内容

```bash
# 发送POST请求到 /api/v1/content/publish
curl -X POST "http://localhost:8000/api/v1/content/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "request": "我想发布一篇关于Python编程技巧的笔记",
    "context": {
      "topic": "编程",
      "style": "教程"
    }
  }'
```

### 3. 查询工作流状态

```bash
# 获取工作流状态
curl "http://localhost:8000/api/v1/content/status/content_publish_user123"
```

## 代码示例

### 直接使用Supervisor

```python
from ai_social_scheduler.ai_agent.supervisor.factory import create_supervisor_with_agents

# 创建Supervisor和所有智能体
supervisor = await create_supervisor_with_agents(
    llm_model="qwen-plus",
    llm_temperature=0.7,
    mcp_url="http://localhost:8000/mcp",
    mcp_transport="streamable_http"
)

# 执行内容发布工作流
result = await supervisor.execute_workflow(
    workflow_name="content_publish",
    input_data={
        "user_id": "user123",
        "request": "我想发布一篇关于Python编程技巧的笔记",
        "context": {
            "topic": "编程",
            "style": "教程"
        }
    }
)

print(result)
```

### 使用工作流类

```python
from ai_social_scheduler.ai_agent.workflows.content_publish import ContentPublishWorkflow
from ai_social_scheduler.ai_agent.supervisor.factory import create_supervisor_with_agents

# 创建Supervisor
supervisor = await create_supervisor_with_agents()

# 创建工作流
workflow = ContentPublishWorkflow(supervisor)

# 执行工作流
result = await workflow.execute({
    "user_id": "user123",
    "request": "我想发布一篇关于Python编程技巧的笔记"
})

print(result)
```

## 配置

### 环境变量

在`.env`文件中配置以下变量：

```env
# LLM配置
ALIBABA_BAILIAN_API_KEY=your_api_key
ALIBABA_BAILIAN_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
ALIBABA_BAILIAN_MODEL=qwen-plus

# MCP配置
XIAOHONGSHU_MCP_URL=http://localhost:8000/mcp
XIAOHONGSHU_MCP_TRANSPORT=streamable_http
```

## 架构说明

### Supervisor架构

```
┌─────────────────────────────────────────┐
│         Supervisor（主管）                │
│  ┌───────────────────────────────────┐  │
│  │  AI决策引擎                        │  │
│  │  - 理解需求                        │  │
│  │  - 分析内容                        │  │
│  │  - 生成决策                        │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  策略管理器                         │  │
│  │  - 生成内容策略                     │  │
│  │  - 选择话题和模板                   │  │
│  │  - 优化策略                         │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  状态管理器                         │  │
│  │  - 记录执行结果                     │  │
│  │  - 管理全局状态                     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
           │
           │ 分配任务
           ▼
┌─────────────────────────────────────────┐
│        专业智能体（Agents）               │
├─────────────────────────────────────────┤
│  • 图视频生成智能体                      │
│  • 小红书MCP服务智能体                   │
│  • 数据分析智能体                        │
│  • 内容生成智能体                        │
│  • 异常处理智能体                        │
└─────────────────────────────────────────┘
```

## 注意事项

1. **初始化顺序**：确保在使用Supervisor之前，所有智能体都已正确初始化
2. **MCP服务**：确保小红书MCP服务正在运行并可访问
3. **API密钥**：确保已正确配置LLM API密钥
4. **错误处理**：系统会自动记录执行结果和错误信息，可通过状态管理器查询

## 扩展

### 添加新的智能体

1. 创建新的智能体类，继承`BaseAgent`
2. 实现`execute`方法
3. 在`factory.py`中注册新智能体
4. 更新Supervisor提示词（如需要）

### 添加新的工作流

1. 创建新的工作流类，继承`BaseWorkflow`
2. 实现`execute`方法
3. 在`supervisor_prompts.py`中添加对应的提示词
4. 在`Supervisor._create_supervisor`中注册新工作流

