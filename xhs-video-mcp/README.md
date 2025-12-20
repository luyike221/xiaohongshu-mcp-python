# XHS Video MCP

基于 FastMCP 的小红书视频生成 MCP 服务，借鉴 MoneyPrinterTurbo 的视频生产逻辑。

## 功能特性

- ✅ 自动生成视频脚本（使用 LLM）
- ✅ 自动生成搜索关键词
- ✅ 文本转语音（TTS，支持 edge-tts）
- ✅ 自动生成字幕
- ✅ 从 Pexels/Pixabay 下载视频素材
- ✅ 视频合成（拼接、添加字幕、背景音乐、转场效果）
- ✅ 支持竖屏（9:16）和横屏（16:9）

## 安装

使用 uv 管理项目：

```bash
# 安装依赖
uv sync

# 或使用 pip
pip install -e .
```

## 配置

### 环境变量配置

项目使用 `python-dotenv` 管理环境变量。创建 `.env` 文件配置必要的 API Keys：

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入实际的配置值
```

`.env` 文件示例：

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

### 配置说明

- 所有配置项都可以通过环境变量设置
- 支持多个 API Key（用逗号分隔），系统会自动轮询使用
- 配置文件优先级：环境变量 > .env 文件 > 默认值
- 详细配置项请参考 `.env.example` 文件

## 使用

### 快速启动

**方式一：使用启动脚本（推荐）**

```bash
# 使用默认配置启动（0.0.0.0:8005）
./start.sh

# 或指定主机和端口
./start.sh 0.0.0.0 8005
```

**方式二：使用 uv 命令**

```bash
# 首次运行需要同步依赖
uv sync

# 启动服务
uv run xhs-video-mcp

# 指定主机和端口
uv run xhs-video-mcp --host 0.0.0.0 --port 8005
```

**方式三：使用 Python 模块**

```bash
python -m xhs_video_mcp.main --host 0.0.0.0 --port 8005
```

> 📖 详细的启动说明请查看 [启动指南.md](./启动指南.md)

### 调用 MCP 工具

通过 MCP 客户端调用 `generate_video` 工具：

```python
result = await generate_video(
    video_subject="春天的花海",
    video_aspect="9:16",
    voice_name="zh-CN-XiaoxiaoNeural-Female"
)
```

## 项目结构

```
xhs-video-mcp/
├── src/
│   └── xhs_video_mcp/
│       ├── __init__.py
│       ├── main.py                    # MCP 入口
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py           # 配置管理
│       ├── models/
│       │   ├── __init__.py
│       │   └── schema.py             # 数据模型
│       ├── services/
│       │   ├── __init__.py
│       │   ├── llm_service.py        # LLM 服务
│       │   ├── voice_service.py      # 语音服务
│       │   ├── subtitle_service.py  # 字幕服务
│       │   ├── material_service.py   # 素材服务
│       │   ├── video_service.py      # 视频服务
│       │   └── video_generation_service.py  # 主服务
│       └── utils/
│           ├── __init__.py
│           └── video_effects.py     # 视频特效
├── pyproject.toml
└── README.md
```

## 依赖

主要依赖：
- `fastmcp`: MCP 框架
- `moviepy`: 视频处理
- `edge-tts`: 文本转语音
- `openai`: LLM 调用
- `requests`: HTTP 请求
- `pillow`: 图片处理

## 注意事项

1. 需要配置 Pexels 或 Pixabay API Key 才能下载视频素材
2. 需要配置 LLM API Key（OpenAI/Moonshot/DeepSeek）才能生成脚本
3. 视频生成需要较长时间，建议异步调用
4. 生成的视频文件较大，注意磁盘空间

## 许可证

MIT

