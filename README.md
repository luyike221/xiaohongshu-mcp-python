# 🚀 AI 社交媒体运营全栈解决方案

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![MCP Protocol](https://img.shields.io/badge/MCP-1.0%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**🤖 AI驱动的智能社交媒体运营平台 | 让AI帮你运营小红书**

[快速开始](#-快速开始) • [项目架构](#-项目架构) • [核心功能](#-核心功能) • [使用指南](#-使用指南)

</div>

---

## ✨ 项目简介

这是一个**完整的AI社交媒体运营解决方案**，由六个强大的项目组成，实现从内容生成、图像视频创作、平台操作到AI智能调度的全链路自动化。

### 🎯 核心价值

- **🤖 AI自主运营**：AI模型自主决策和执行运营任务，无需人工干预
- **🔄 事件驱动**：智能响应用户请求、平台通知、定时任务等多种事件
- **📊 数据驱动**：基于数据分析自动优化内容策略和发布时机
- **🔌 模块化设计**：内容生成、平台操作、AI调度三层架构，灵活可扩展
- **🎨 内容创作**：AI自动生成图像和视频，支持完整的内容创作流程
- **📱 多平台支持**：支持小红书、抖音、快手等平台（逐步扩展）

---

## 📖 使用指南

### 场景一：生成内容、图片、并发布于小红书

```
[新对话] 请输入消息: 写个单身程序员如何找富婆的小红书，配9张图，其中有核心图有类似狂飙中大嫂陈舒婷
📤 发送中...
📥 最终生成的小红书
```

**最终发布的小红书：**

![富婆圣经0](ai_social_scheduler/assets/富婆圣经0.png)

![富婆圣经1](ai_social_scheduler/assets/富婆圣经1.png)

## 🏗️ 项目架构

本仓库包含六个独立但协同工作的项目：

### 1️⃣ **ai_social_scheduler** - AI 调度核心层

**定位**：上层智能调度系统，AI自主决策和执行运营任务

- 🤖 **AI自主驱动**：AI模型分析运营目标，自动生成和执行计划
- 🔄 **事件响应**：支持用户请求、平台通知、定时任务等多种事件
- 📊 **策略优化**：基于数据分析自动调整内容策略
- 🎨 **内容创作**：AI生成内容创作计划，调用底层服务执行
- 📈 **数据分析**：内容表现分析、趋势识别、热点追踪
- 🌐 **HTTP API 服务**：提供 FastAPI 接口，支持 HTTP 调用
- 💬 **交互式聊天**：提供命令行聊天客户端，方便快速体验

**核心文件**：
- **`run.py`**：启动 FastAPI 服务器，提供 HTTP API 接口（默认端口 8012）
- **`chat.py`**：交互式聊天客户端，通过命令行与 AI Agent 对话

**适用场景**：需要AI智能运营和自动化调度的场景

### 2️⃣ **xhs-content-generator-mcp** - 小红书内容生成 MCP 服务层

**定位**：内容文案生成引擎，提供AI内容创作能力

- ✍️ **内容生成**：基于主题生成小红书笔记、标题、描述等内容
- 🎯 **多类型支持**：支持笔记、标题、描述等多种内容类型
- 🚀 **FastMCP框架**：使用 FastMCP 快速构建 MCP 服务
- 🔌 **MCP协议实现**：完整支持 Model Context Protocol 规范
- 🎨 **智能创作**：AI驱动的智能内容创作

**适用场景**：需要AI生成小红书文案和内容的场景

### 3️⃣ **xhs-browser-automation-mcp** - 小红书浏览器自动化 MCP 服务层

**定位**：平台操作引擎，提供小红书平台的具体操作能力

- 🎯 **MCP协议实现**：完整实现 Model Context Protocol 规范
- 🚀 **高性能**：基于 Playwright 的异步浏览器自动化
- 📝 **内容发布**：支持图文、视频内容发布
- 🔍 **内容管理**：搜索、获取、互动等完整功能
- 🔐 **账户管理**：登录、会话保持、自动重连

**适用场景**：需要直接操作小红书平台的场景

### 4️⃣ **xhs-image-mcp** - 图像生成 MCP 服务层

**定位**：AI图像生成引擎，提供高质量图像创作能力

- 🎨 **图像生成**：基于提示词生成高质量图像（支持通义万相）
- 🚀 **FastMCP框架**：使用 FastMCP 快速构建 MCP 服务
- 🔌 **MCP协议实现**：完整支持 Model Context Protocol 规范
- 📝 **Prompt模板**：提供5个预定义的Prompt模板
- 📦 **Resource资源**：提供6个预定义的Resource资源（风格预设、配置模板等）
- 🎯 **Resource Template**：提供8个预定义的Resource Template模板，支持动态参数访问
- ⚙️ **灵活配置**：支持自定义尺寸、种子、负面提示词等参数

**适用场景**：需要AI生成图像内容的场景

### 5️⃣ **xhs-video-mcp** - 视频生成 MCP 服务层

**定位**：视频生成引擎，借鉴 MoneyPrinterTurbo 的视频生产逻辑

- 🎬 **自动生成视频脚本**：使用 LLM 生成视频脚本
- 🔍 **自动生成搜索关键词**：智能生成视频素材搜索关键词
- 🗣️ **文本转语音（TTS）**：支持 edge-tts，多种语音选择
- 📝 **自动生成字幕**：自动为视频添加字幕
- 📥 **素材下载**：从 Pexels/Pixabay 下载视频素材
- ✂️ **视频合成**：拼接、添加字幕、背景音乐、转场效果
- 📱 **多尺寸支持**：支持竖屏（9:16）和横屏（16:9）
- ⚡ **GPU加速**：支持NVENC硬件编码加速

**适用场景**：需要AI生成剪辑风格视频的场景

### 6️⃣ **xhs-data-collector-mcp** - 数据收集 MCP 服务层

**定位**：数据收集和分析引擎

- 📊 **数据收集**：收集平台数据，支持运营分析
- 🔍 **数据分析**：内容表现分析、趋势识别
- 📈 **数据可视化**：提供数据统计和可视化功能

**适用场景**：需要数据收集和分析的场景

### 🔗 协同工作

```
┌─────────────────────────────────────────────────────────┐
│   AI Social Scheduler (智能调度层)                        │
│   - AI决策引擎                                           │
│   - 事件监听器                                           │
│   - 任务调度器                                           │
│   - 策略管理器                                           │
└───┬──────────┬──────────┬──────────┬──────────┬────────┘
    │ MCP协议  │ MCP协议  │ MCP协议  │ MCP协议  │ MCP协议
    ↓          ↓          ↓          ↓          ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│xhs-content   │ │xhs-image-mcp │ │xhs-video-mcp  │ │xhs-browser-   │ │xhs-data-      │
│generator     │ │(图像生成)     │ │(视频生成)     │ │automation-mcp │ │collector-mcp │
│              │ │              │ │              │ │(平台操作)     │ │(数据收集)     │
│- 内容生成    │ │- 图像生成     │ │- 视频脚本生成 │ │- 内容发布     │ │- 数据收集     │
│- 文案创作    │ │- Prompt模板   │ │- TTS语音合成 │ │- 内容搜索     │ │- 数据分析     │
│              │ │- Resource    │ │- 视频合成     │ │- 用户互动     │ │- 趋势识别     │
└──────────────┘ └──────────────┘ └──────────────┘ │- 账户管理     │ └──────────────┘
                                                   └────────┬────────┘
                                                        │ 浏览器自动化
                                                        ↓
                                                  ┌──────────┐
                                                  │  小红书平台 │
                                                  └──────────┘
```

---

## 🎯 核心功能

### 🤖 AI 智能运营

- **自主决策**：AI分析运营目标，自动生成内容创作计划
- **智能调度**：根据数据表现自动调整发布策略和时机
- **事件响应**：实时响应平台通知、用户请求、定时任务
- **策略优化**：基于历史数据持续优化运营策略

### 🎨 内容生成

- **图像生成**：基于提示词AI生成高质量图像
- **视频生成**：基于提示词AI生成视频内容
- **文案生成**：AI生成小红书笔记、标题、描述等内容
- **参数定制**：支持自定义尺寸、种子、负面提示词等
- **批量生成**：支持批量生成和异步处理

### 📝 内容发布

- **图文发布**：支持多图片、标签、标题和描述
- **视频发布**：支持视频上传、自动等待处理完成
- **批量操作**：支持批量发布和定时发布
- **内容管理**：搜索、获取、编辑内容

### 📊 数据分析

- **表现分析**：阅读量、点赞、评论、转发等数据统计
- **趋势识别**：内容趋势分析和热点识别
- **用户洞察**：粉丝增长、互动率等用户数据
- **策略建议**：基于数据自动生成优化建议

### 🔍 内容管理

- **内容搜索**：关键词搜索小红书内容
- **推荐获取**：获取首页推荐列表
- **详情分析**：获取帖子详情和互动数据
- **用户管理**：获取用户主页信息

---

## 🚀 快速开始

### 📋 环境要求

- Python >= 3.11
- uv 包管理器
- 支持的操作系统：Linux, macOS, Windows

### 🔧 安装步骤

1. **克隆项目**
   ```bash
   git clone git@github.com:luyike221/xiaohongshu-mcp-python.git
   cd xiaohongshu-mcp-python
   ```

2. **安装 uv 包管理器**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **安装项目依赖**

   **安装图像生成 MCP 服务：**
   ```bash
   cd xhs-image-mcp
   uv sync
   ```

   **安装视频生成 MCP 服务：**
   ```bash
   cd xhs-video-mcp
   uv sync
   ```

   **安装小红书内容生成 MCP 服务：**
   ```bash
   cd xhs-content-generator-mcp
   uv sync
   ```

   **安装小红书浏览器自动化 MCP 服务：**
   ```bash
   cd xhs-browser-automation-mcp
   uv sync
   uv run playwright install chromium
   ```

   **安装数据收集 MCP 服务：**
   ```bash
   cd xhs-data-collector-mcp
   uv sync
   ```

   **安装 AI 调度系统：**
   ```bash
   cd ai_social_scheduler
   uv sync
   ```

### ⚙️ 配置

#### 图像生成 MCP 服务配置

在 `xhs-image-mcp` 目录下创建 `.env` 文件：

```env
# 服务器配置
MCP_HOST=127.0.0.1
MCP_PORT=8003

# 通义万相配置（图像生成）
WANT2I_API_KEY=your_api_key
WANT2I_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### 视频生成 MCP 服务配置

在 `xhs-video-mcp` 目录下创建 `.env` 文件：

```env
# LLM 配置
LLM_PROVIDER=openai  # 或 moonshot, deepseek
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL_NAME=gpt-3.5-turbo

# 视频素材配置（多个key用逗号分隔）
PEXELS_API_KEYS=your_pexels_api_key_1,your_pexels_api_key_2
PIXABAY_API_KEYS=your_pixabay_api_key

# 视频配置
VIDEO_OUTPUT_DIR=./output
MATERIAL_CACHE_DIR=./cache/materials
VIDEO_FPS=30
VIDEO_GPU_ACCELERATION=false  # 启用GPU加速（需要NVIDIA GPU和NVENC支持）
VIDEO_CODEC=auto  # 视频编码器: auto, libx264, h264_nvenc, hevc_nvenc
```

#### 小红书内容生成 MCP 服务配置

在 `xhs-content-generator-mcp` 目录下创建 `.env` 文件（可选）：

```env
# 服务器配置
MCP_HOST=0.0.0.0
MCP_PORT=8001
```

#### 小红书浏览器自动化 MCP 服务配置

在 `xhs-browser-automation-mcp` 目录下创建 `.env` 文件：

```env
# 环境模式: development 或 production
ENV=development

# 服务器配置
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# 默认用户
GLOBAL_USER=your_username
```

#### AI 调度系统配置

在 `ai_social_scheduler` 目录下创建配置文件：

```bash
cp config/config.example.yaml config/config.yaml
# 编辑 config/config.yaml 填入实际配置
```

### 🎯 启动服务

#### 启动图像生成 MCP 服务

```bash
cd xhs-image-mcp
uv run python -m image_video_mcp.main
```

服务将在 `http://localhost:8003` 启动。

#### 启动视频生成 MCP 服务

```bash
cd xhs-video-mcp
# 使用启动脚本（推荐）
./start.sh

# 或使用 uv 命令
uv run xhs-video-mcp

# 或指定主机和端口
uv run xhs-video-mcp --host 0.0.0.0 --port 8005
```

服务将在 `http://localhost:8005` 启动（默认端口）。

#### 启动小红书内容生成 MCP 服务

```bash
cd xhs-content-generator-mcp
uv run python -m xhs_content_generator_mcp.main
```

服务将在 `http://localhost:8001` 启动（默认端口 8000，可通过参数指定）。

#### 启动小红书浏览器自动化 MCP 服务

```bash
cd xhs-browser-automation-mcp
uv run python -m xiaohongshu_mcp_python.main
```

服务将在 `http://localhost:8000` 启动。

#### 启动 AI 调度系统

**方式一：启动 HTTP API 服务（推荐）**

使用 `run.py` 启动 FastAPI 服务器，提供 HTTP 接口：

```bash
cd ai_social_scheduler
uv run python run.py
```

服务将在 `http://0.0.0.0:8012` 启动，提供以下接口：
- `POST /api/v1/chat` - 聊天接口，发送消息获取 AI 回复

**方式二：使用交互式聊天客户端**

使用 `chat.py` 启动交互式命令行客户端：

```bash
cd ai_social_scheduler
uv run python chat.py
```

启动后可以：
- 直接输入消息与 AI Agent 对话
- 输入 `quit` 或 `exit` 退出
- 输入 `reset` 重置对话线程

**方式三：直接运行主程序**

```bash
cd ai_social_scheduler
uv run python main.py
```

---

## 📖 使用指南

### 场景一：使用内容生成服务

如果你需要生成小红书内容，可以使用 `xhs-content-generator-mcp`：

```python
# 通过 MCP 客户端调用
{
  "tool": "generate_content",
  "parameters": {
    "topic": "春日美食",
    "content_type": "note"
  }
}
```

### 场景二：直接使用小红书浏览器自动化 MCP 服务

如果你只需要直接操作小红书平台，可以使用 `xhs-browser-automation-mcp`：

```python
# 通过 MCP 客户端调用
{
  "tool": "xiaohongshu_publish_content",
  "parameters": {
    "title": "春日美景",
    "content": "分享今天拍摄的美丽春景！",
    "images": ["/path/to/image1.jpg", "/path/to/image2.jpg"],
    "tags": ["春天", "摄影", "美景"]
  }
}
```

### 场景三：使用 AI 智能运营

如果你需要AI自主运营，可以使用 `ai_social_scheduler`：

**方式一：使用交互式聊天客户端（最简单）**

```bash
cd ai_social_scheduler
uv run python chat.py
```

启动后直接与 AI 对话：
```
[新对话] 请输入消息: 帮我写一篇关于美食的小红书
📤 发送中...
📥 AI 回复:
好的，我来帮你创建一篇关于美食的小红书内容...
```

**方式二：通过 HTTP API 调用**

1. 启动 API 服务：
```bash
cd ai_social_scheduler
uv run python run.py
```

2. 发送 HTTP 请求：
```bash
curl -X POST http://localhost:8012/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我写一篇关于美食的小红书"}'
```

**AI 处理流程**：
当你说"帮我写一篇关于美食的小红书"时，AI 会：
1. 分析美食主题和需求
2. 调用 `xhs-content-generator-mcp` 生成内容文案
3. 调用 `xhs-image-mcp` 生成配图
4. 调用 `xhs-browser-automation-mcp` 发布内容
5. 监控发布结果
6. 根据数据调整后续策略

**视频生成流程**：
当需要生成视频时，AI 会：
1. 调用 `xhs-video-mcp` 生成视频脚本
2. 使用 TTS 生成语音
3. 从 Pexels/Pixabay 下载视频素材
4. 合成视频（添加字幕、背景音乐、转场效果）
5. 输出最终视频文件

### 场景四：完整集成使用

所有项目可以完美集成，形成完整的运营闭环：

1. **AI 调度系统**监听事件（用户请求、定时任务等）
2. **AI 决策引擎**分析需求，生成执行计划
3. **内容生成服务**生成文案和图片
4. **任务调度器**调用 **MCP 服务**执行具体操作
5. **数据分析**收集结果，优化策略

---

## 🛠️ 技术栈

### 核心技术

- **Python 3.11+**：主要开发语言
- **uv**：现代 Python 包管理工具
- **MCP 协议**：服务间通信标准
- **LangGraph**：AI Agent 框架
- **Playwright**：浏览器自动化
- **FastAPI**：Web 服务框架

### 数据存储

- **SQLite/PostgreSQL**：关系型数据存储
- **Redis**：缓存和任务队列
- **pgvector**：向量数据库（用于AI功能）

---

## 📁 项目结构

```
.
├── xhs-image-mcp/                  # 图像生成 MCP 服务
│   ├── src/
│   │   └── image_video_mcp/
│   │       ├── main.py            # 主程序入口
│   │       ├── clients/           # 客户端模块
│   │       ├── prompts/           # Prompt 模板
│   │       ├── resources/         # Resource 资源
│   │       └── ...
│   └── README.md                  # 详细文档
│
├── xhs-video-mcp/                  # 视频生成 MCP 服务
│   ├── src/
│   │   └── xhs_video_mcp/
│   │       ├── main.py            # 主程序入口
│   │       ├── services/          # 服务模块
│   │       │   ├── llm_service.py        # LLM 服务
│   │       │   ├── voice_service.py      # 语音服务
│   │       │   ├── subtitle_service.py  # 字幕服务
│   │       │   ├── material_service.py  # 素材服务
│   │       │   ├── video_service.py     # 视频服务
│   │       │   └── video_generation_service.py  # 主服务
│   │       ├── config/            # 配置管理
│   │       └── utils/             # 工具模块
│   ├── start.sh                   # 启动脚本
│   └── README.md                  # 详细文档
│
├── xhs-content-generator-mcp/      # 小红书内容生成 MCP 服务
│   ├── src/
│   │   └── xhs_content_generator_mcp/
│   │       ├── __init__.py
│   │       └── main.py           # 主程序入口
│   ├── pyproject.toml
│   └── README.md                  # 详细文档
│
├── xhs-browser-automation-mcp/     # 小红书浏览器自动化 MCP 服务
│   ├── src/
│   │   └── xiaohongshu_mcp_python/
│   │       ├── main.py            # 主程序入口
│   │       ├── server/            # MCP 服务器
│   │       ├── xiaohongshu/       # 小红书操作模块
│   │       └── ...
│   ├── tests/                     # 测试文件
│   └── README.md                  # 详细文档
│
├── xhs-data-collector-mcp/         # 数据收集 MCP 服务
│   ├── src/
│   │   └── xhs_data_collector_mcp/
│   │       └── ...
│   └── README.md                  # 详细文档
│
├── ai_social_scheduler/            # AI 调度系统
│   ├── src/
│   │   └── ai_social_scheduler/
│   │       ├── core/              # AI调度核心层
│   │       │   ├── ai_engine.py  # AI决策引擎
│   │       │   ├── event_listener.py # 事件监听器
│   │       │   └── ...
│   │       ├── api/               # FastAPI 接口层
│   │       │   ├── app.py        # FastAPI 应用
│   │       │   └── ...
│   │       ├── mcp/               # MCP服务层
│   │       └── ...
│   ├── run.py                      # 启动 FastAPI 服务器
│   ├── chat.py                     # 交互式聊天客户端
│   ├── config/                     # 配置文件
│   └── README.md                   # 详细文档
│
└── README.md                       # 本文件
```

---

## 🔌 MCP 客户端接入

### Cursor IDE

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "xhs-image-mcp": {
      "url": "http://localhost:8003",
      "description": "图像生成 MCP 服务"
    },
    "xhs-video-mcp": {
      "url": "http://localhost:8005",
      "description": "视频生成 MCP 服务"
    },
    "xhs-content-generator-mcp": {
      "url": "http://localhost:8001",
      "description": "小红书内容生成 MCP 服务"
    },
    "xhs-browser-automation-mcp": {
      "url": "http://localhost:8000",
      "description": "小红书浏览器自动化 MCP 服务"
    },
    "xhs-data-collector-mcp": {
      "url": "http://localhost:8006",
      "description": "数据收集 MCP 服务"
    }
  }
}
```

### Claude Desktop

在配置文件中添加：

```json
{
  "mcpServers": {
    "xhs-image-mcp": {
      "url": "http://localhost:8003"
    },
    "xhs-video-mcp": {
      "url": "http://localhost:8005"
    },
    "xhs-content-generator-mcp": {
      "url": "http://localhost:8001"
    },
    "xhs-browser-automation-mcp": {
      "url": "http://localhost:8000"
    },
    "xhs-data-collector-mcp": {
      "url": "http://localhost:8006"
    }
  }
}
```

---

## 🎨 功能演示

### AI 自主运营示例

```python
# 用户请求："帮我写一篇关于美食的小红书"
# 
# AI 调度系统处理流程：
# 1. 事件监听器接收用户请求
# 2. AI 引擎分析需求，生成内容计划：
#    - 主题：美食
#    - 内容方向：分享一道家常菜
#    - 图片需求：需要3张图片
#    - 标签：美食、家常菜、生活
# 3. 任务调度器调用 MCP 服务：
#    - 生成内容（调用 xhs-content-generator-mcp）
#    - 生成图片（调用 xhs-image-mcp）
#    - 生成视频（调用 xhs-video-mcp，如需要）
#    - 发布内容（调用 xhs-browser-automation-mcp）
# 4. 监控发布结果
# 5. 根据数据调整后续策略
```

### 定时任务示例

```python
# 设置定时任务："每天下午3点发布一篇内容"
# 
# AI 调度系统会：
# 1. 定时触发任务
# 2. AI 分析当天热点和用户偏好
# 3. 生成合适的内容
# 4. 自动发布
# 5. 收集数据并优化策略
```

### 交互式聊天使用示例

使用 `chat.py` 与 AI Agent 进行对话：

```bash
$ cd ai_social_scheduler
$ uv run python chat.py

============================================================
小红书运营 Agent 交互式聊天
============================================================

提示:
  - 输入消息后按 Enter 发送
  - 输入 'quit' 或 'exit' 退出
  - 输入 'reset' 重置对话

[新对话] 请输入消息: 帮我写一篇关于春日美食的小红书

📤 发送中...

📥 AI 回复:
好的，我来帮你创建一篇关于春日美食的小红书内容。让我先分析一下需求...

[对话 ID: a1b2c3d4...] 请输入消息: 标题要吸引人一点

📤 发送中...

📥 AI 回复:
好的，我会优化标题，让它更加吸引人...

消息数: 4

[对话 ID: a1b2c3d4...] 请输入消息: reset
✅ 对话已重置

[新对话] 请输入消息: quit
再见！
```

### HTTP API 使用示例

使用 `run.py` 启动服务后，可以通过 HTTP 调用：

```bash
# 启动服务
$ cd ai_social_scheduler
$ uv run python run.py
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8012

# 在另一个终端发送请求
$ curl -X POST http://localhost:8012/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我写一篇关于春日美食的小红书",
    "thread_id": null
  }'

{
  "thread_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "response": "好的，我来帮你创建一篇关于春日美食的小红书内容...",
  "message_count": 2
}

# 继续对话（使用相同的 thread_id）
$ curl -X POST http://localhost:8012/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "标题要吸引人一点",
    "thread_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

---

## ⚠️ 注意事项

### 🔒 账户安全

- 同一账户不要在多个浏览器端同时登录
- 定期检查登录状态，及时处理 Cookie 过期
- 建议使用专门的小红书账户进行自动化操作

### 📊 使用限制

- 遵守小红书平台规则和相关法律法规
- 合理控制发布频率，避免被平台限制
- 本项目仅供学习和研究使用

### 🛡️ 风险提示

使用本工具产生的任何后果由使用者自行承担。请遵守平台规则，合理使用。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。

---

## 🙏 致谢

- [Model Context Protocol](https://modelcontextprotocol.io) - MCP 协议标准
- [Playwright](https://playwright.dev) - 浏览器自动化工具
- [uv](https://github.com/astral-sh/uv) - 现代 Python 包管理工具
- [LangGraph](https://github.com/langchain-ai/langgraph) - AI Agent 框架

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个 Star！**

Made with ❤️ by [luyike221](https://github.com/luyike221)

</div>
