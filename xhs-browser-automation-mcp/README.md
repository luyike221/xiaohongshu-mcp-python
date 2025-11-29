# xiaohongshu-mcp-python

🐍 **小红书 MCP Python 版本** - 基于 Model Context Protocol 的小红书自动化内容发布工具

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0%2B-green.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🌟 项目简介

xiaohongshu-mcp-python 是一个基于 Python 开发的小红书内容发布自动化工具，通过 Model Context Protocol (MCP) 协议为 AI 客户端提供小红书操作能力。本项目使用现代 Python 技术栈，支持异步操作，提供高效稳定的小红书内容管理服务。

### ✨ 核心特性

- 🚀 **现代 Python 架构**：基于 Python 3.8+ 和异步编程
- 🎯 **MCP 协议支持**：完整实现 Model Context Protocol 规范
- 🌐 **Playwright 驱动**：使用 Playwright 替代 Selenium，性能更优
- 📦 **uv 包管理**：采用现代 Python 包管理工具 uv
- 🔧 **环境配置**：支持开发/生产环境切换，.env 文件配置管理
- 📊 **日志系统**：支持控制台和文件双输出，自动轮转和压缩
- 🛡️ **类型安全**：完整的类型注解支持

## 🎯 主要功能

### 📝 内容发布功能

<details>
<summary><b>🖼️ 图文内容发布</b></summary>

支持发布图文内容到小红书，包括：
- 📄 标题和内容描述（标题限制20字符）
- 🖼️ 多图片上传（支持本地路径和HTTP链接）
- 🏷️ 标签管理
- 📊 发布状态监控

**图片支持格式：**
- 本地文件路径：`/path/to/image.jpg`
- HTTP/HTTPS 链接：`https://example.com/image.png`
- 支持格式：JPG, PNG, GIF, WebP

</details>

<details>
<summary><b>🎬 视频内容发布</b></summary>

支持发布视频内容到小红书：
- 🎥 本地视频文件上传
- 📝 视频标题和描述
- ⏱️ 自动等待视频处理完成
- 🏷️ 视频标签设置

**视频支持格式：**
- 本地文件：`/path/to/video.mp4`
- 支持格式：MP4, MOV, AVI
- 文件大小：建议不超过 1GB

</details>

### 🔍 内容管理功能

<details>
<summary><b>🔐 账户管理</b></summary>

- 登录状态检查
- Cookie 管理
- 会话保持
- 自动重新登录

</details>

<details>
<summary><b>🔍 内容搜索与获取</b></summary>

- 关键词搜索小红书内容
- 获取首页推荐列表
- 帖子详情获取（包含互动数据）
- 用户主页信息获取

</details>

<details>
<summary><b>💬 互动功能</b></summary>

- 发表评论到指定帖子
- 获取评论列表
- 互动数据统计

</details>

## 🚀 快速开始

### 📋 环境要求

- Python 3.8 或更高版本
- uv 包管理器
- 支持的操作系统：Linux, macOS, Windows

### 🔧 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/xiaohongshu-mcp-python.git
   cd xiaohongshu-mcp-python
   ```

2. **安装 uv 包管理器**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **配置国内镜像源（可选）**
   ```bash
   export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. **安装依赖**
   ```bash
   uv sync
   ```

5. **安装 Playwright 浏览器**
   ```bash
   uv run playwright install chromium
   ```

### ⚙️ 环境配置

项目支持**开发环境**和**生产环境**两种模式，可以通过环境变量或 `.env` 文件进行配置。

#### 📋 环境模式说明

| 环境模式 | 浏览器模式 | 日志级别 | 调试模式 | 适用场景 |
|---------|-----------|---------|---------|---------|
| **development** (开发) | 有头模式（显示浏览器） | DEBUG | 启用 | 本地开发、调试 |
| **production** (生产) | 无头模式（后台运行） | INFO | 禁用 | 服务器部署、生产环境 |

#### 🔧 配置方式

**方式一：使用 `.env` 文件（推荐）**

1. 复制示例配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件：
   ```env
   # ============ 环境配置 ============
   # 可选值: development, production
   # development: 开发环境（有头浏览器、DEBUG日志）
   # production: 生产环境（无头浏览器、INFO日志）
   ENV=development

   # ============ 浏览器配置 ============
   # 是否使用无头浏览器模式
   # true: 无头模式（不显示浏览器窗口）
   # false: 有头模式（显示浏览器窗口）
   # 如果未设置，会根据 ENV 自动决定（开发环境=有头，生产环境=无头）
   # BROWSER_HEADLESS=false
   
   # 浏览器可执行文件路径（可选，用于使用本地浏览器）
   # 如果未设置，则使用 Playwright 自带的浏览器
   # Ubuntu 常见路径：
   # - Google Chrome: /usr/bin/google-chrome 或 /usr/bin/google-chrome-stable
   # - Chromium: /usr/bin/chromium 或 /usr/bin/chromium-browser
   # 使用脚本查找: ./scripts/find_browser.sh
   # BROWSER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable

   # ============ 日志配置 ============
   # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
   # 开发环境默认: DEBUG
   # 生产环境默认: INFO
   # LOG_LEVEL=DEBUG

   # 日志文件路径（可选，如果设置则日志会写入文件）
   # LOG_FILE=logs/xiaohongshu-mcp.log

   # ============ 服务器配置 ============
   # 服务器监听地址
   SERVER_HOST=127.0.0.1

   # 服务器端口
   SERVER_PORT=8000

   # ============ 用户配置 ============
   # 默认用户名
   GLOBAL_USER=luyike

   # ============ 超时配置 ============
   # 页面加载超时时间（毫秒）
   PAGE_LOAD_TIMEOUT=60000

   # 元素等待超时时间（毫秒）
   ELEMENT_TIMEOUT=30000
   ```

**方式二：使用环境变量**

```bash
# 开发环境
export ENV=development
export BROWSER_HEADLESS=false
export LOG_LEVEL=DEBUG

# 生产环境
export ENV=production
export BROWSER_HEADLESS=true
export LOG_LEVEL=INFO

# 使用本地浏览器（Ubuntu）
export BROWSER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable
```

**方式三：命令行参数（优先级最高）**

```bash
# 开发模式（默认）
uv run python -m xiaohongshu_mcp_python.main

# 生产模式
uv run python -m xiaohongshu_mcp_python.main --env production

# 开发模式但使用无头浏览器
uv run python -m xiaohongshu_mcp_python.main --env development --headless

# 生产模式但使用有头浏览器（调试用）
uv run python -m xiaohongshu_mcp_python.main --env production --no-headless

# 自定义日志级别
uv run python -m xiaohongshu_mcp_python.main --env development --log-level DEBUG

# 指定日志文件
uv run python -m xiaohongshu_mcp_python.main --log-file logs/app.log
```

#### 🎛️ 可用配置项

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 环境模式 | `ENV` | `development` | `development` 或 `production` |
| 浏览器模式 | `BROWSER_HEADLESS` | 根据 ENV 自动 | `true`/`false`，未设置时自动决定 |
| 浏览器路径 | `BROWSER_EXECUTABLE_PATH` | `None` | 本地浏览器可执行文件路径，未设置则使用 Playwright 自带浏览器 |
| 日志级别 | `LOG_LEVEL` | 根据 ENV 自动 | `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| 日志文件 | `LOG_FILE` | `None` | 日志文件路径，如果设置则同时写入文件 |
| 服务器地址 | `SERVER_HOST` | `127.0.0.1` | HTTP 服务器监听地址 |
| 服务器端口 | `SERVER_PORT` | `8000` | HTTP 服务器端口 |
| 默认用户 | `GLOBAL_USER` | `luyike` | 默认使用的用户名 |
| 页面超时 | `PAGE_LOAD_TIMEOUT` | `60000` | 页面加载超时（毫秒） |
| 元素超时 | `ELEMENT_TIMEOUT` | `30000` | 元素等待超时（毫秒） |

#### 📝 日志系统

日志系统支持以下特性：

- **控制台输出**：默认输出到控制台，支持彩色显示
- **文件输出**：可通过 `LOG_FILE` 配置同时写入文件
- **日志轮转**：文件日志自动轮转（10MB）
- **日志保留**：保留最近 7 天的日志
- **自动压缩**：旧日志自动压缩为 zip 格式

日志格式：
```
{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}
```

#### 🌐 使用本地浏览器（Ubuntu）

默认情况下，项目使用 Playwright 自带的浏览器。如果你想使用系统已安装的浏览器（如 Google Chrome 或 Chromium），可以按以下步骤配置：

**1. 查找本地浏览器路径**

使用提供的脚本查找：
```bash
./scripts/find_browser.sh
```

或者手动查找：
```bash
which google-chrome
which chromium-browser
which chromium
```

**2. 配置浏览器路径**

在 `.env` 文件中添加：
```env
BROWSER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable
```

或者使用环境变量：
```bash
export BROWSER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable
```

**3. 常见浏览器路径（Ubuntu）**

- Google Chrome: `/usr/bin/google-chrome` 或 `/usr/bin/google-chrome-stable`
- Chromium: `/usr/bin/chromium` 或 `/usr/bin/chromium-browser`
- Snap 安装的 Chromium: `/snap/bin/chromium`

**4. 安装浏览器（如果未安装）**

安装 Google Chrome：
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
```

安装 Chromium：
```bash
sudo apt-get update
sudo apt-get install chromium-browser
```

**注意**：使用本地浏览器时，确保浏览器已正确安装且可执行。如果路径不正确，程序会回退到使用 Playwright 自带的浏览器。

### 🎯 启动服务

```bash
# 开发模式启动（默认）
uv run python -m xiaohongshu_mcp_python.main

# 生产模式启动
uv run python -m xiaohongshu_mcp_python.main --env production

# 查看帮助信息
uv run python -m xiaohongshu_mcp_python.main --help
```

启动后，服务将在 `http://localhost:8000`（或配置的端口）启动。

启动时会显示环境配置信息：
```
============================================================
小红书 MCP 服务器启动
运行环境: 开发环境 (development)
浏览器模式: 有头模式
日志级别: DEBUG
服务器地址: http://127.0.0.1:8000
默认用户: luyike
============================================================
```

## 📖 使用教程

### 1️⃣ 登录小红书

首次使用需要登录小红书账户：

```python
# 使用登录工具
uv run python -m src.xiaohongshu_mcp_python.login
```

### 2️⃣ 验证 MCP 连接

使用 MCP Inspector 验证连接：

```bash
npx @modelcontextprotocol/inspector
```

在浏览器中访问 `http://localhost:18060/mcp` 进行连接测试。

### 3️⃣ 发布内容示例

**发布图文内容：**

```python
# 通过 MCP 工具调用
{
  "tool": "publish_content",
  "parameters": {
    "title": "春日美景",
    "content": "分享今天拍摄的美丽春景，希望大家喜欢！",
    "images": [
      "/path/to/spring1.jpg",
      "/path/to/spring2.jpg"
    ],
    "tags": ["春天", "摄影", "美景"]
  }
}
```

## 🔌 MCP 客户端接入

### Claude Code CLI

```bash
# 添加 MCP 服务
claude mcp add --transport http xiaohongshu-mcp-python http://localhost:18060/mcp

# 验证连接
claude mcp list
```

### Cursor IDE

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "xiaohongshu-mcp-python": {
      "url": "http://localhost:18060/mcp",
      "description": "小红书 Python MCP 服务"
    }
  }
}
```

### VSCode

在项目根目录创建 `.vscode/mcp.json`：

```json
{
  "servers": {
    "xiaohongshu-mcp-python": {
      "url": "http://localhost:18060/mcp",
      "type": "http"
    }
  }
}
```

## 🛠️ 开发指南

### 📁 项目结构

```
xiaohongshu-mcp-python/
├── src/
│   └── xiaohongshu_mcp_python/
│       ├── __init__.py
│       ├── main.py              # 主程序入口
│       ├── mcp_server.py        # MCP 服务器实现
│       ├── xiaohongshu/         # 小红书操作模块
│       ├── utils/               # 工具函数
│       └── config/              # 配置管理
├── tests/                       # 测试文件
├── docs/                        # 文档
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量示例（开发/生产环境配置）
├── .env                        # 环境变量文件（需自行创建，已加入 .gitignore）
└── README.md
```

### 🧪 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_mcp_server.py

# 生成覆盖率报告
uv run pytest --cov=src
```

### 🔍 代码质量检查

```bash
# 代码格式化
uv run black src tests

# 类型检查
uv run mypy src

# 代码风格检查
uv run flake8 src tests
```

## 🔧 可用 MCP 工具

| 工具名称 | 功能描述 | 必需参数 | 可选参数 |
|---------|---------|---------|---------|
| `xiaohongshu_start_login_session` | 启动登录会话 | 无 | username |
| `xiaohongshu_check_login_session` | 检查登录状态 | 无 | username |
| `xiaohongshu_cleanup_login_session` | 清理登录会话 | 无 | username |
| `xiaohongshu_publish_content` | 发布图文内容 | title, content, images | tags, username |
| `xiaohongshu_publish_video` | 发布视频内容 | title, content, video | tags, username |
| `xiaohongshu_search_feeds` | 搜索小红书内容 | keyword | username |
| `xiaohongshu_get_feeds` | 获取推荐列表 | 无 | username |
| `xiaohongshu_get_user_profile` | 获取用户主页 | user_id | username |
| `xiaohongshu_get_feed_detail` | 获取笔记详情 | feed_id | username |

### 📝 工具详细说明

#### `xiaohongshu_publish_video` - 视频发布工具

发布视频内容到小红书平台。

**参数说明：**
- `title` (必需): 视频标题，最多20个中文字或英文单词
- `content` (必需): 视频描述内容，不包含以#开头的标签内容  
- `video` (必需): 视频文件路径，支持本地视频文件绝对路径
- `tags` (可选): 话题标签列表，如 ["美食", "旅行", "生活"]
- `username` (可选): 用户名，如果不提供则使用全局用户

**使用示例：**
```python
# 通过 MCP 客户端调用
result = await xiaohongshu_publish_video(
    title="我的旅行视频",
    content="分享一段美好的旅行时光",
    video="/path/to/my_video.mp4",
    tags=["旅行", "生活", "美好时光"]
)
```

**返回结果：**
```json
{
    "success": true,
    "message": "视频发布完成",
    "result": {
        "note_id": "视频笔记ID",
        "success": true
    }
}
```

## ⚠️ 注意事项

### 🔒 账户安全

- 同一账户不要在多个浏览器端同时登录
- 定期检查登录状态，及时处理 Cookie 过期
- 建议使用专门的小红书账户进行自动化操作

### 📊 发布限制

- 标题不超过 20 个字符
- 每日发布量建议控制在合理范围内
- 图片格式：JPG, PNG, GIF, WebP
- 视频格式：MP4, MOV, AVI（建议不超过 1GB）

### 🔐 环境模式最佳实践

#### 开发环境（development）
- ✅ 使用有头浏览器，方便调试和观察
- ✅ DEBUG 级别日志，查看详细执行过程
- ✅ 适合本地开发和问题排查

#### 生产环境（production）
- ✅ 使用无头浏览器，节省资源
- ✅ INFO 级别日志，减少日志量
- ✅ 适合服务器部署和自动化运行

#### 环境切换建议
```bash
# 本地开发
ENV=development python -m xiaohongshu_mcp_python.main

# 服务器部署
ENV=production python -m xiaohongshu_mcp_python.main

# 或者使用 .env 文件
# 开发时：.env 中设置 ENV=development
# 生产时：.env 中设置 ENV=production
```

### 🛡️ 风险提示

本项目仅供学习和研究使用，请遵守小红书平台规则和相关法律法规。使用本工具产生的任何后果由使用者自行承担。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 感谢 [Model Context Protocol](https://modelcontextprotocol.io) 提供的协议标准
- 感谢 [Playwright](https://playwright.dev) 提供的浏览器自动化工具
- 感谢 [uv](https://github.com/astral-sh/uv) 提供的现代 Python 包管理工具

---

⭐ 如果这个项目对你有帮助，请给它一个 Star！