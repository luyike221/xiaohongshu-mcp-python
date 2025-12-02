# Image Video MCP

基于 FastMCP 的图像和视频生成 MCP 服务。

## 项目简介

提供图像和视频生成能力的 Model Context Protocol (MCP) 服务，使用 FastMCP 框架构建。

## 核心特性

- 🎨 **图像生成**：基于提示词生成图像
- 🎬 **视频生成**：基于提示词生成视频
- 🚀 **FastMCP 框架**：使用 FastMCP 快速构建 MCP 服务
- 🔌 **MCP 协议**：完整支持 Model Context Protocol
- 📝 **Prompt 模板**：提供 5 个预定义的 Prompt 模板，可在 MCP Inspector 中使用
- 📦 **Resource 资源**：提供 6 个预定义的 Resource 资源，包含风格预设、配置模板等
- 🎯 **Resource Template**：提供 8 个预定义的 Resource Template 模板，支持动态参数访问

## 快速开始

### 安装依赖

```bash
uv sync
```

### 运行服务

```bash
uv run python -m image_video_mcp.main
```

## 项目结构

```
image_video-mcp/
├── src/
│   └── image_video_mcp/
│       ├── __init__.py
│       ├── main.py          # 主程序入口
│       ├── prompts/         # Prompt 模板模块
│       │   ├── __init__.py
│       │   └── prompts.py   # Prompt 定义
│       ├── resources/        # Resource 资源模块
│       │   ├── __init__.py
│       │   ├── resources.py # Resource 定义
│       │   └── templates/   # Resource Template 模板模块
│       │       ├── __init__.py
│       │       └── templates.py # Resource Template 定义
│       ├── clients/         # 客户端模块
│       └── config/          # 配置模块
├── pyproject.toml          # 项目配置
└── README.md
```

## Prompt 功能

本服务支持 **FastMCP Prompt** 功能，提供了 5 个预定义的 Prompt 模板：

1. **optimize_image_prompt** - 优化图像生成提示词
2. **video_generation_prompt** - 生成视频创建提示词
3. **image_style_description** - 描述图像风格
4. **generate_negative_prompt** - 生成负面提示词（使用 Resource）
5. **batch_image_generation_plan** - 制定批量图像生成计划

### 使用方法

1. 启动 MCP 服务器
2. 使用 MCP Inspector 连接到服务器
3. 在 **Prompts** 标签页中查看和使用这些模板

详细使用说明请查看 [PROMPTS_USAGE.md](./PROMPTS_USAGE.md)

## Resource 功能

本服务支持 **FastMCP Resource** 功能，提供了 6 个预定义的 Resource 资源：

1. **image_styles** - 图像风格预设（6种风格）
2. **negative_prompts** - 负面提示词库（4种类型）
3. **image_sizes** - 图像尺寸预设（8种尺寸）
4. **video_styles** - 视频风格预设（5种风格）
5. **generation_configs** - 生成配置模板（4种配置）
6. **prompt_templates** - 提示词模板库（5种模板）

### 使用方法

1. 启动 MCP 服务器
2. 使用 MCP Inspector 连接到服务器
3. 在 **Resources** 标签页中查看和使用这些资源
4. 在 Prompt 或 Tool 中通过 `mcp.get_resource("resource://资源名称")` 访问

详细使用说明请查看 [RESOURCES_USAGE.md](./RESOURCES_USAGE.md)

## Resource Template 功能

本服务支持 **FastMCP Resource Template** 功能，提供了 8 个预定义的 Resource Template 模板：

1. **resource://styles/{style_name}** - 根据风格名称获取风格配置
2. **resource://negative_prompts/{image_type}** - 根据图像类型获取负面提示词
3. **resource://sizes/{size_name}** - 根据尺寸名称获取尺寸配置
4. **resource://video_styles/{style_name}** - 根据风格名称获取视频风格配置
5. **resource://configs/{config_name}** - 根据配置名称获取生成配置
6. **resource://prompt_templates/{template_name}** - 根据模板名称获取提示词模板
7. **resource://combined_config/{style_name}/{size_name}** - 组合风格和尺寸生成完整配置
8. **resource://generation_plan/{theme}/{style_name}/{size_name}** - 生成完整的图像生成方案

### 使用方法

1. 启动 MCP 服务器
2. 使用 MCP Inspector 连接到服务器
3. 在 **Resources** 标签页中查看 Resource Template（URI 包含 `{参数}`）
4. 在 Prompt 或 Tool 中通过 `mcp.get_resource("resource://路径/参数值")` 访问

详细使用说明请查看 [RESOURCE_TEMPLATES_USAGE.md](./RESOURCE_TEMPLATES_USAGE.md)

## 开发

项目使用 uv 进行依赖管理，Python 版本要求 >= 3.11。

