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
- 🔧 **环境配置**：支持 .env 文件配置管理
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

创建 `.env` 文件：

```env
# 小红书配置
XIAOHONGSHU_HEADLESS=true
XIAOHONGSHU_COOKIES_PATH=./cookies
XIAOHONGSHU_SCREENSHOTS_PATH=./screenshots

# MCP 服务配置
MCP_HOST=localhost
MCP_PORT=18060

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/xiaohongshu-mcp.log
```

### 🎯 启动服务

```bash
# 启动 MCP 服务
uv run python -m src.xiaohongshu_mcp_python.main

# 或使用项目脚本
uv run xiaohongshu-mcp
```

服务将在 `http://localhost:18060/mcp` 启动。

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
├── .env.example                # 环境变量示例
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