# XHS Content Generator MCP

基于 FastMCP 的小红书内容生成 MCP 服务。

## 功能特性

- 🎨 小红书内容生成
- 📝 生成图文内容大纲（支持多页结构）
- 🔌 基于 FastMCP 框架
- 🚀 支持多种 AI 服务商（Google Gemini、OpenAI 兼容接口）
- 🖼️ 支持参考图片输入，保持风格一致性

## 项目结构

```
xhs-content-generator-mcp/
├── src/
│   └── xhs_content_generator_mcp/
│       ├── __init__.py
│       ├── main.py                    # MCP 服务入口
│       ├── clients/                   # AI 客户端
│       │   ├── genai_client.py        # Google Gemini 客户端
│       │   └── text_client.py         # OpenAI 兼容客户端
│       ├── services/                  # 业务服务
│       │   └── outline_service.py     # 大纲生成服务
│       ├── utils/                     # 工具模块
│       │   ├── image_compressor.py    # 图片压缩工具
│       │   └── error_parser.py        # 错误解析工具
│       └── prompts/                   # 提示词模板
│           └── outline_prompt.txt    # 大纲生成提示词
├── pyproject.toml
└── README.md
```

## 安装

使用 `uv` 进行项目管理：

```bash
# 安装依赖
uv sync

# 运行服务
uv run python -m xhs_content_generator_mcp.main
```

## 配置

### 使用 .env 文件（推荐）

1. **复制示例配置文件：**
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件，填入你的配置：**
   ```env
   # 阿里百炼配置（默认服务商，推荐）
   ALIBABA_BAILIAN_API_KEY=your-api-key
   ALIBABA_BAILIAN_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
   ALIBABA_BAILIAN_MODEL=qwen-plus
   ALIBABA_BAILIAN_TEMPERATURE=0.3

   # OpenAI 兼容接口配置（可选）
   # OPENAI_API_KEY=your-api-key
   # OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   # OPENAI_MODEL=qwen-plus

   # Google Gemini 配置（可选）
   # GEMINI_API_KEY=your-gemini-api-key
   ```
   
   **推荐配置（使用阿里百炼 qwen-plus）：**
   - `ALIBABA_BAILIAN_API_KEY`: 阿里百炼 API Key（必需）
   - `ALIBABA_BAILIAN_ENDPOINT`: 设置为 `https://dashscope.aliyuncs.com/compatible-mode/v1`（默认值，可不设置）
   - `ALIBABA_BAILIAN_MODEL`: 设置为 `qwen-plus`（默认值，可不设置）
   - `ALIBABA_BAILIAN_TEMPERATURE`: 设置为 `0.3`（默认值，可不设置）

3. **配置说明：**
   - **默认使用阿里百炼 qwen-plus（推荐）**
   - 至少需要配置 `ALIBABA_BAILIAN_API_KEY`（默认服务商）
   - 其他参数都有默认值，可以不配置
   - `.env` 文件会被自动加载，无需手动设置环境变量
   - `.env` 文件已添加到 `.gitignore`，不会被提交到版本控制

4. **完整配置项说明：**
   
   查看 `.env.example` 文件获取所有可配置项：
   ```bash
   cat .env.example
   ```
   
   **Google Gemini 配置项：**
   - `GEMINI_API_KEY`: API Key（必需，如果使用 Gemini）
   - `GEMINI_MODEL`: 模型名称（可选，默认: gemini-2.0-flash-exp）
   - `GEMINI_TEMPERATURE`: 温度参数（可选，默认: 1.0，范围: 0.0-2.0）
   - `GEMINI_MAX_OUTPUT_TOKENS`: 最大输出 token 数（可选，默认: 8000）
   - `GEMINI_BASE_URL`: 自定义端点（可选，留空使用默认）
   - `GEMINI_TIMEOUT`: 请求超时时间（可选，默认: 300 秒）
   
   **OpenAI 兼容接口配置项（默认服务商）：**
   - `OPENAI_API_KEY`: API Key（必需，默认使用此服务商）
   - `OPENAI_MODEL`: 模型名称（可选，默认: qwen-plus）
   - `OPENAI_BASE_URL`: 自定义端点（可选，默认: https://api.openai.com，使用 qwen-plus 时建议设置为 https://dashscope.aliyuncs.com/compatible-mode/v1）
   - `OPENAI_TEMPERATURE`: 温度参数（可选，默认: 1.0，范围: 0.0-2.0）
   - `OPENAI_MAX_OUTPUT_TOKENS`: 最大输出 token 数（可选，默认: 8000）
   - `OPENAI_TIMEOUT`: 请求超时时间（可选，默认: 300 秒）
   - `OPENAI_ENDPOINT_TYPE`: 自定义端点路径（可选，默认: /v1/chat/completions）
   - `OPENAI_PROVIDER_NAME`: 模型提供商名称（可选，如 'qwen-plus', 'deepseek-chat', 'alibaba-bailian' 等）
   
   **阿里百炼配置项（兼容模式）：**
   - `ALIBABA_BAILIAN_API_KEY`: API Key（必需，如果使用阿里百炼）
   - `ALIBABA_BAILIAN_ENDPOINT`: API 端点（可选，默认: https://dashscope.aliyuncs.com/compatible-mode/v1）
   - `ALIBABA_BAILIAN_MODEL`: 模型名称（可选，默认: qwen-plus）
   - `ALIBABA_BAILIAN_TEMPERATURE`: 温度参数（可选，默认: 0.3，范围: 0.0-2.0）
   - `ALIBABA_BAILIAN_MAX_TOKENS`: 最大输出 token 数（可选，默认: 8000）
   - `ALIBABA_BAILIAN_TIMEOUT`: 请求超时时间（可选，默认: 60 秒）

### 使用环境变量（可选）

如果不使用 `.env` 文件，也可以通过环境变量配置：

```bash
# Google Gemini
export GEMINI_API_KEY="your-api-key"
export GEMINI_MODEL="gemini-2.0-flash-exp"  # 可选，默认值
export GEMINI_TEMPERATURE="1.0"              # 可选，默认值
export GEMINI_MAX_OUTPUT_TOKENS="8000"      # 可选，默认值
export GEMINI_BASE_URL=""                    # 可选，自定义端点

# OpenAI 兼容接口（默认服务商）
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="qwen-plus"             # 可选，默认值
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 可选，使用 qwen-plus 时建议设置
```

## 使用

### 一键启动（推荐）

使用提供的 `run.sh` 脚本一键启动：

```bash
# 使用默认端口 8004
./run.sh

# 指定端口
./run.sh 8080
```

脚本会自动：
- ✅ 检查 `uv` 是否安装
- ✅ 检查 Python 版本（需要 >= 3.11）
- ✅ 同步项目依赖
- ✅ 检查环境变量配置
- ✅ 启动 MCP 服务

### 手动启动

```bash
# 默认端口 8004
uv run python -m xhs_content_generator_mcp.main

# 指定端口
uv run python -m xhs_content_generator_mcp.main 8080
```

### 在 MCP Inspector 中测试

#### 方式一：使用调试脚本（推荐）

使用提供的 `inspector_test_mcp.sh` 脚本一键启动 Inspector：

```bash
# 基本使用（需要先启动服务器）
./inspector_test_mcp.sh

# 自动启动服务器并连接 Inspector
./inspector_test_mcp.sh --auto-start

# 指定端口
./inspector_test_mcp.sh --port 9000

# 跳过确认，直接启动
./inspector_test_mcp.sh --auto-start --skip-confirm
```

脚本功能：
- ✅ 自动检查服务器状态
- ✅ 可选择自动启动服务器
- ✅ 自动启动 MCP Inspector
- ✅ 退出时自动清理后台进程

#### 方式二：手动启动

1. 启动服务后，打开 MCP Inspector：
   ```bash
   npx @modelcontextprotocol/inspector
   ```

2. 在 Inspector 界面中：
   - 选择 `HTTP/HTTPS` 传输方式
   - 输入服务器地址：`http://localhost:8004`
   - 点击连接

3. 在 Tools 标签页中测试 `generate_outline` 工具

### MCP 工具说明

#### generate_outline

生成小红书图文内容大纲。

**参数：**
- `topic` (必需): 内容主题，例如"如何在家做拿铁"、"秋季显白美甲"等
- `provider_type` (可选): AI 服务商类型，可选值：
  - `alibaba_bailian`（默认）：阿里百炼，使用 qwen-plus 模型
  - `openai_compatible`：OpenAI 兼容接口，支持 qwen-plus、deepseek-chat 等
  - `google_gemini`：Google Gemini
- `model` (可选): 模型名称，如果不提供则使用默认值
  - `alibaba_bailian` 默认: qwen-plus
  - `openai_compatible` 默认: qwen-plus
- `temperature` (可选): 温度参数（0.0-2.0），默认 0.3（阿里百炼推荐值）
- `max_output_tokens` (可选): 最大输出 token 数，默认 8000
- `images_base64` (可选): 参考图片列表（base64 编码），用于保持风格一致性

**注意：** `api_key` 和 `base_url` 必须通过环境变量配置，不能通过参数传入。

**支持的模型提供商：**
- **通义千问**：qwen-plus, qwen-turbo, qwen-max（通过 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 配置）
- **DeepSeek**：deepseek-chat, deepseek-coder（通过 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 配置）
- **阿里百炼**：alibaba-bailian（使用 `ALIBABA_BAILIAN_*` 环境变量或 `provider_type=alibaba_bailian`）
- **OpenAI**：gpt-4o, gpt-3.5-turbo 等（通过 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 配置）

**返回：**
```json
{
  "success": true,
  "outline": "完整的大纲文本...",
  "pages": [
    {
      "index": 0,
      "type": "cover",
      "content": "[封面]\n标题：..."
    },
    {
      "index": 1,
      "type": "content",
      "content": "[内容]\n第一步：..."
    }
  ],
  "has_images": false
}
```

**示例：**

```python
# 使用 Google Gemini（从环境变量读取 API Key）
result = await generate_outline(
    topic="如何在家做拿铁"
)

# 使用 OpenAI 兼容接口（需要先设置环境变量 OPENAI_API_KEY）
result = await generate_outline(
    topic="秋季显白美甲",
    provider_type="openai_compatible",
    model="gpt-4o"
)

# 带参考图片
result = await generate_outline(
    topic="产品宣传",
    images_base64=["data:image/png;base64,iVBORw0KG..."]
)
```

## 开发

### 添加新功能

1. 在 `main.py` 中添加新的 `@mcp.tool()` 装饰的函数
2. 实现具体的业务逻辑
3. 重启服务测试

### 代码结构说明

- **clients/**: AI 客户端封装，支持 Google Gemini 和 OpenAI 兼容接口
- **services/**: 业务逻辑服务，如大纲生成服务
- **utils/**: 工具函数，如图片压缩、错误解析
- **prompts/**: 提示词模板文件

## 许可证

MIT
