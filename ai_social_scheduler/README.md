# AI Social Scheduler

AI驱动的智能社交媒体运营调度系统，基于 LangGraph 构建，支持小红书等平台的内容发布、互动管理和数据分析。

## 项目简介

本项目是一个基于 **LangGraph** 的自动化社交媒体运营系统，通过统一的调度核心自动化管理多个社交媒体平台，实现内容创作、发布、互动、数据分析的全流程智能化。

### 核心特性

- 🤖 **AI自主驱动**：基于 LangGraph 的智能工作流，AI模型自主决策和执行运营任务
- 🔄 **实时流式处理**：支持 Server-Sent Events (SSE) 实时展示处理进度
- 🎯 **智能路由系统**：基于规则和LLM的混合路由策略，精准匹配用户意图
- 📊 **数据驱动**：基于数据分析优化内容策略
- 🔌 **可扩展架构**：模块化设计，易于接入新平台和服务
- 📱 **多平台支持**：支持小红书、图视频生成等平台（逐步扩展）
- 🛠️ **MCP协议集成**：通过 MCP 协议统一管理各个平台服务

## 技术架构

采用**基于 LangGraph 的分层模块化架构**，以**图执行引擎**为核心，通过**MCP协议**统一管理各个平台服务。

### 架构层次

```
用户交互层 (FastAPI/Web/CLI)
    ↓
API层 (流式API、RESTful API)
    ↓
图执行层 (LangGraph - 路由、节点编排、状态管理)
    ↓
智能体层 (XHS Agent、内容生成 Agent 等)
    ↓
MCP服务层 (小红书浏览器自动化、图视频生成、内容生成等)
    ↓
平台适配层 (浏览器自动化/API调用)
```

### 核心组件

- **Graph Executor**：LangGraph 图执行器，负责工作流的编排和执行
- **Router System**：智能路由系统，支持规则匹配和LLM意图识别
- **Node System**：节点注册和工厂系统，支持中间件扩展
- **State Manager**：状态管理器，支持对话历史持久化
- **Streaming Executor**：流式执行器，支持实时进度展示

## 项目结构

```
ai_social_scheduler/
├── src/
│   └── ai_social_scheduler/          # 主包
│       ├── app.py                    # 应用主入口
│       ├── api/                      # API层
│       │   ├── app.py                # FastAPI应用
│       │   └── streaming_api.py      # 流式API路由
│       ├── graph/                    # 图执行层
│       │   ├── builder.py            # 图构建器
│       │   ├── executor.py           # 图执行器
│       │   └── streaming.py          # 流式执行器
│       ├── router/                   # 路由系统
│       │   ├── router_system.py      # 路由系统核心
│       │   ├── intent_analyzer.py    # 意图分析器
│       │   └── rule_engine.py        # 规则引擎
│       ├── nodes/                    # 节点系统
│       │   ├── registry.py           # 节点注册表
│       │   ├── factory.py            # 节点工厂
│       │   └── base.py               # 节点基类
│       ├── agents/                   # 智能体
│       │   └── xhs_agent.py          # 小红书智能体
│       ├── mcp/                      # MCP服务层
│       │   ├── xhs/                  # 小红书MCP服务
│       │   └── image_video/          # 图视频生成服务
│       ├── orchestrator/             # 编排器
│       │   ├── orchestrator.py      # 编排器核心
│       │   └── task_queue.py        # 任务队列
│       ├── state/                    # 状态管理
│       │   └── manager.py            # 状态管理器
│       ├── core/                      # 核心模型
│       │   ├── models.py             # 数据模型
│       │   ├── node.py               # 节点模型
│       │   └── route.py              # 路由模型
│       ├── config/                    # 配置管理
│       │   ├── config.py             # 配置加载
│       │   ├── mcp_config.py         # MCP配置
│       │   └── model_config.py       # 模型配置
│       ├── client/                    # 客户端
│       │   └── llm/                  # LLM客户端
│       ├── middleware/               # 中间件
│       │   ├── logging_middleware.py # 日志中间件
│       │   └── retry_middleware.py   # 重试中间件
│       ├── workflows/                # 工作流
│       │   └── xhs_content_workflow.py
│       ├── tools/                     # 工具函数
│       └── utils/                     # 工具函数
├── config/                            # 配置文件目录
│   ├── nodes.yaml                     # 节点配置
│   └── routes.yaml                    # 路由配置
├── data/                              # 数据存储目录
├── logs/                              # 日志目录
├── examples/                          # 示例代码
│   ├── streaming_app_example.py      # 流式应用示例
│   ├── streaming_client_example.py   # 流式客户端示例
│   └── streaming_demo.html           # 前端演示页面
├── tests/                             # 测试目录
├── start_streaming.py                 # 流式服务启动脚本
├── start_streaming.sh                 # 启动脚本
└── pyproject.toml                     # 项目配置
```

## 快速开始

### 环境要求

- Python >= 3.11
- uv (Python包管理器)

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd ai_social_scheduler

# 使用uv安装依赖
uv sync

# 配置环境变量（可选）
# 编辑 .env 文件或设置环境变量
# - LLM_API_KEY (DeepSeek/Qwen等)
# - MCP服务配置
```

### 运行流式服务

```bash
# 方式1: 使用启动脚本（推荐）
python start_streaming.py

# 方式2: 使用shell脚本
bash start_streaming.sh

# 方式3: 使用uv运行
uv run python start_streaming.py

# 服务启动后访问:
# - 前端演示: http://localhost:8020
# - API文档: http://localhost:8020/docs
# - 流式接口: http://localhost:8020/api/v1/chat/stream
```

### 测试流式API

```bash
# 使用curl测试
curl -N "http://localhost:8020/api/v1/chat/stream?message=帮我写一篇小红书"

# 使用Python客户端
python examples/streaming_client_example.py "帮我写一篇小红书"
```

## 核心功能

### 1. 实时流式处理

支持 Server-Sent Events (SSE) 实时展示处理进度：

- ⚡ **实时进度**：毫秒级延迟，实时展示节点执行状态
- 📊 **事件类型**：支持 `started`、`node_start`、`node_output`、`node_end`、`completed` 等事件
- 🎯 **前端集成**：浏览器原生支持，易于集成到前端应用

### 2. 智能路由系统

- 🎯 **规则优先**：基于关键词和模式的快速路由
- 🤖 **LLM增强**：使用LLM进行意图识别和语义理解
- 🔄 **混合策略**：支持规则优先、LLM优先等多种策略

### 3. AI自主驱动

- AI模型分析用户意图和运营目标
- 自动生成内容创作计划
- 调用相应的MCP服务执行任务
- 监控执行结果并自动调整策略

### 4. 模块化节点系统

- 📦 **节点注册**：通过配置文件注册节点
- 🔧 **中间件支持**：支持日志、重试等中间件
- 🔌 **易于扩展**：新增节点只需实现基类接口

### 5. 状态管理

- 💾 **对话持久化**：支持对话历史的持久化存储
- 🔄 **状态恢复**：支持从检查点恢复执行状态
- 📊 **多会话管理**：支持多用户、多会话并发

## 开发计划

### ✅ 已完成

- [x] 基于 LangGraph 的图执行引擎
- [x] 智能路由系统（规则+LLM）
- [x] 流式API支持（SSE）
- [x] 节点系统和中间件
- [x] 状态管理和持久化
- [x] 小红书MCP服务集成
- [x] 图视频生成服务集成
- [x] FastAPI应用和API文档

### 🚧 进行中

- [ ] 完善工作流定义
- [ ] 增强错误处理和重试机制
- [ ] 性能优化和监控

### 📋 计划中

- [ ] 定时任务支持
- [ ] 数据分析功能
- [ ] 自动回复功能
- [ ] 接入更多平台（抖音、快手）
- [ ] Web管理界面

## 技术栈

- **Python 3.11+**：主要开发语言
- **LangGraph**：工作流编排框架
- **LangChain**：LLM应用开发框架
- **FastAPI**：现代Web框架
- **uv**：Python包管理工具
- **MCP协议**：服务间通信标准（Model Context Protocol）
- **Server-Sent Events (SSE)**：实时流式传输
- **SQLite/PostgreSQL**：数据存储（计划中）
- **Playwright**：浏览器自动化
- **ComfyUI**：图像和视频生成

## 相关文档

- [流式处理快速开始](./doc/STREAMING_QUICKSTART.md)
- [流式API完整指南](./doc/STREAMING_API_GUIDE.md)
- [流式架构说明](./doc/STREAMING_ARCHITECTURE.md)
- [项目结构说明](./doc/NEW_PROJECT_STRUCTURE.md)

## 许可证

个人项目，仅供学习使用。


