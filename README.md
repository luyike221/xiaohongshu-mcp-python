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

这是一个**完整的AI社交媒体运营解决方案**，由三个强大的项目组成，实现从内容生成、平台操作到AI智能调度的全链路自动化。

### 🎯 核心价值

- **🤖 AI自主运营**：AI模型自主决策和执行运营任务，无需人工干预
- **🔄 事件驱动**：智能响应用户请求、平台通知、定时任务等多种事件
- **📊 数据驱动**：基于数据分析自动优化内容策略和发布时机
- **🔌 模块化设计**：内容生成、平台操作、AI调度三层架构，灵活可扩展
- **🎨 内容创作**：AI自动生成图像和视频，支持完整的内容创作流程
- **📱 多平台支持**：支持小红书、抖音、快手等平台（逐步扩展）

---

## 🏗️ 项目架构

本仓库包含三个独立但协同工作的项目：

### 1️⃣ **image_video_mcp** - 图像视频生成 MCP 服务层

**定位**：内容创作引擎，提供AI图像和视频生成能力

- 🎨 **图像生成**：基于提示词生成高质量图像（支持通义万相）
- 🎬 **视频生成**：基于提示词生成视频内容
- 🚀 **FastMCP框架**：使用 FastMCP 快速构建 MCP 服务
- 🔌 **MCP协议实现**：完整支持 Model Context Protocol 规范
- ⚙️ **灵活配置**：支持自定义尺寸、种子、负面提示词等参数

**适用场景**：需要AI生成图像或视频内容的场景

### 2️⃣ **xiaohongshu_mcp** - 小红书 MCP 服务层

**定位**：平台操作引擎，提供小红书平台的具体操作能力

- 🎯 **MCP协议实现**：完整实现 Model Context Protocol 规范
- 🚀 **高性能**：基于 Playwright 的异步浏览器自动化
- 📝 **内容发布**：支持图文、视频内容发布
- 🔍 **内容管理**：搜索、获取、互动等完整功能
- 🔐 **账户管理**：登录、会话保持、自动重连

**适用场景**：需要直接操作小红书平台的场景

### 3️⃣ **ai_social_scheduler** - AI 调度核心层

**定位**：上层智能调度系统，AI自主决策和执行运营任务

- 🤖 **AI自主驱动**：AI模型分析运营目标，自动生成和执行计划
- 🔄 **事件响应**：支持用户请求、平台通知、定时任务等多种事件
- 📊 **策略优化**：基于数据分析自动调整内容策略
- 🎨 **内容创作**：AI生成内容创作计划，调用底层服务执行
- 📈 **数据分析**：内容表现分析、趋势识别、热点追踪

**适用场景**：需要AI智能运营和自动化调度的场景

### 🔗 协同工作

```
┌─────────────────────────────────────────┐
│   AI Social Scheduler (智能调度层)        │
│   - AI决策引擎                           │
│   - 事件监听器                           │
│   - 任务调度器                           │
│   - 策略管理器                           │
└──────┬────────────────────┬──────────────┘
       │ 通过 MCP 协议调用   │ 通过 MCP 协议调用
       ↓                    ↓
┌──────────────────┐  ┌─────────────────────────┐
│ image_video_mcp  │  │ xiaohongshu_mcp         │
│ (内容生成服务层)  │  │ (平台操作服务层)         │
│                  │  │                         │
│ - 图像生成        │  │ - 小红书内容发布         │
│ - 视频生成        │  │ - 内容搜索与获取        │
│                  │  │ - 用户互动管理          │
│                  │  │ - 账户管理              │
└──────────────────┘  └──────────┬──────────────┘
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

   **安装图像视频生成 MCP 服务：**
   ```bash
   cd image_video_mcp
   uv sync
   ```

   **安装小红书 MCP 服务：**
   ```bash
   cd xiaohongshu_mcp
   uv sync
   uv run playwright install chromium
   ```

   **安装 AI 调度系统：**
   ```bash
   cd ai_social_scheduler
   uv sync
   ```

### ⚙️ 配置

#### 图像视频生成 MCP 服务配置

在 `image_video_mcp` 目录下创建 `.env` 文件：

```env
# 服务器配置
MCP_HOST=127.0.0.1
MCP_PORT=8003

# 通义万相配置（图像生成）
WANT2I_API_KEY=your_api_key
WANT2I_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### 小红书 MCP 服务配置

在 `xiaohongshu_mcp` 目录下创建 `.env` 文件：

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

#### 启动小红书 MCP 服务

```bash
cd xiaohongshumcp-python
uv run python -m xiaohongshu_mcp_python.main
```

服务将在 `http://localhost:8000` 启动。

#### 启动 AI 调度系统

```bash
cd ai_social_scheduler
uv run python main.py
```

---

## 📖 使用指南

### 场景一：直接使用小红书 MCP 服务

如果你只需要直接操作小红书平台，可以使用 `xiaohongshumcp-python`：

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

### 场景二：使用 AI 智能运营

如果你需要AI自主运营，可以使用 `ai_social_scheduler`：

```python
# AI 会自动分析你的需求，生成内容计划，并调用底层服务执行
# 例如："帮我写一篇关于美食的小红书"
# AI 会：
# 1. 分析美食主题
# 2. 生成内容计划
# 3. 调用 xiaohongshumcp-python 发布内容
# 4. 监控发布结果
# 5. 根据数据调整策略
```

### 场景三：集成使用

两个项目可以完美集成：

1. **AI 调度系统**监听事件（用户请求、定时任务等）
2. **AI 决策引擎**分析需求，生成执行计划
3. **任务调度器**调用 **MCP 服务**执行具体操作
4. **数据分析**收集结果，优化策略

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
├── xiaohongshumcp-python/          # 小红书 MCP 服务
│   ├── src/
│   │   └── xiaohongshu_mcp_python/
│   │       ├── main.py             # 主程序入口
│   │       ├── server/             # MCP 服务器
│   │       ├── xiaohongshu/        # 小红书操作模块
│   │       └── ...
│   ├── tests/                      # 测试文件
│   └── README.md                   # 详细文档
│
├── ai_social_scheduler/            # AI 调度系统
│   ├── src/
│   │   └── ai_social_scheduler/
│   │       ├── core/               # AI调度核心层
│   │       │   ├── ai_engine.py   # AI决策引擎
│   │       │   ├── event_listener.py # 事件监听器
│   │       │   └── ...
│   │       ├── mcp/                # MCP服务层
│   │       └── ...
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
    "xiaohongshu-mcp-python": {
      "url": "http://localhost:8000/mcp",
      "description": "小红书 Python MCP 服务"
    }
  }
}
```

### Claude Desktop

在配置文件中添加：

```json
{
  "mcpServers": {
    "xiaohongshu-mcp-python": {
      "url": "http://localhost:8000/mcp"
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
#    - 生成图片（调用 ComfyUI 服务）
#    - 发布内容（调用小红书 MCP 服务）
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

