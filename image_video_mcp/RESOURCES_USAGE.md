# FastMCP Resource 使用指南

本文档说明如何在 Image Video MCP 服务中使用 Resource 功能。

## 📋 概述

本项目已注册了 6 个 Resource 资源，可以在 MCP Inspector 的 **Resources** 标签页中查看和使用。这些资源提供了：

1. 图像风格预设
2. 负面提示词库
3. 图像尺寸预设
4. 视频风格预设
5. 生成配置模板
6. 提示词模板库

## 🚀 快速开始

### 1. 启动 MCP 服务器

```bash
cd /root/project/ai_project/yx_运营/xhs_小红书运营/image_video_mcp
./run.sh
```

### 2. 启动 MCP Inspector

```bash
./inspector_test_mcp.sh --port 8003
```

### 3. 在 MCP Inspector 中查看 Resource

1. 打开浏览器访问 `http://localhost:6274`
2. 选择 **HTTP/HTTPS** 传输方式
3. 输入服务器地址: `http://127.0.0.1:8003/mcp`
4. 点击 **Connect** 连接
5. 切换到 **Resources** 标签页
6. 你将看到所有已注册的 Resource

## 📝 可用的 Resource

### 1. image_styles - 图像风格预设

**URI**: `resource://image_styles`

**内容**: 包含 6 种图像风格预设：
- `realistic` - 写实风格
- `anime` - 动漫风格
- `watercolor` - 水彩风格
- `oil_painting` - 油画风格
- `3d_render` - 3D渲染风格
- `sketch` - 素描风格

**使用示例**:
```python
# 在代码中获取资源
styles = mcp.get_resource("resource://image_styles")
realistic_style = styles["realistic"]
print(realistic_style["keywords"])  # 输出风格关键词
```

### 2. negative_prompts - 负面提示词库

**URI**: `resource://negative_prompts`

**内容**: 包含 4 种类型的负面提示词：
- `general` - 通用负面提示词
- `portrait` - 人物肖像专用
- `landscape` - 风景专用
- `product` - 产品专用

**使用示例**:
```python
negative_prompts = mcp.get_resource("resource://negative_prompts")
general_negative = negative_prompts["general"]
portrait_negative = negative_prompts["portrait"]
```

### 3. image_sizes - 图像尺寸预设

**URI**: `resource://image_sizes`

**内容**: 包含 8 种常用图像尺寸：
- `square_1k` - 正方形 1K (1024x1024)
- `square_2k` - 正方形 2K (2048x2048)
- `portrait_16_9` - 横屏 16:9 (1920x1080)
- `portrait_9_16` - 竖屏 9:16 (1080x1920)
- `portrait_4_3` - 横屏 4:3 (1600x1200)
- `portrait_3_4` - 竖屏 3:4 (1200x1600)
- `wide_21_9` - 超宽屏 21:9 (2560x1080)
- `standard_1280` - 标准 1280x1280

**使用示例**:
```python
sizes = mcp.get_resource("resource://image_sizes")
square_2k = sizes["square_2k"]
width = square_2k["width"]  # 2048
height = square_2k["height"]  # 2048
```

### 4. video_styles - 视频风格预设

**URI**: `resource://video_styles`

**内容**: 包含 5 种视频风格：
- `cinematic` - 电影感
- `documentary` - 纪录片风格
- `commercial` - 商业广告
- `vlog` - Vlog风格
- `timelapse` - 延时摄影

**使用示例**:
```python
video_styles = mcp.get_resource("resource://video_styles")
cinematic = video_styles["cinematic"]
keywords = cinematic["keywords"]
movements = cinematic["camera_movements"]
```

### 5. generation_configs - 生成配置模板

**URI**: `resource://generation_configs`

**内容**: 包含 4 种生成配置：
- `high_quality` - 高质量配置
- `fast_generation` - 快速生成配置
- `social_media` - 社交媒体配置
- `artistic` - 艺术创作配置

**使用示例**:
```python
configs = mcp.get_resource("resource://generation_configs")
high_quality = configs["high_quality"]
width = high_quality["width"]  # 2048
negative = high_quality["negative_prompt"]
```

### 6. prompt_templates - 提示词模板库

**URI**: `resource://prompt_templates`

**内容**: 包含 5 种提示词模板：
- `portrait` - 人物肖像模板
- `landscape` - 风景模板
- `product` - 产品模板
- `animal` - 动物模板
- `abstract` - 抽象模板

**使用示例**:
```python
templates = mcp.get_resource("resource://prompt_templates")
portrait_template = templates["portrait"]
# 使用模板: "{subject}, {style}, {lighting}, {composition}, {quality}"
```

## 🔧 在 Prompt 中使用 Resource

你可以在 Prompt 函数中通过 `mcp.get_resource()` 获取资源：

```python
@mcp.prompt()
def my_prompt(image_type: str) -> str:
    # 获取资源
    negative_prompts = mcp.get_resource("resource://negative_prompts")
    base_negative = negative_prompts.get("general", "")
    
    return f"""使用以下负面提示词: {base_negative}"""
```

## 🧪 在 MCP Inspector 中测试

1. 在 **Resources** 标签页中选择一个资源
2. 点击 **Read** 或 **View** 按钮
3. 查看资源的完整内容
4. 资源内容会以 JSON 格式显示

## 📚 代码示例

### 示例 1: 使用图像风格资源

```python
# 获取图像风格资源
styles = mcp.get_resource("resource://image_styles")
anime_style = styles["anime"]

# 使用风格关键词
prompt = f"a cat, {anime_style['keywords']}"
negative = anime_style["negative_keywords"]
```

### 示例 2: 使用尺寸预设

```python
# 获取尺寸预设
sizes = mcp.get_resource("resource://image_sizes")
social_size = sizes["portrait_9_16"]  # 适合社交媒体的竖屏尺寸

# 使用尺寸
width = social_size["width"]  # 1080
height = social_size["height"]  # 1920
```

### 示例 3: 使用生成配置

```python
# 获取生成配置
configs = mcp.get_resource("resource://generation_configs")
social_config = configs["social_media"]

# 使用配置生成图像
generate_image(
    prompt=f"{user_prompt}, {social_config['quality_tags']}",
    negative_prompt=social_config["negative_prompt"],
    width=social_config["width"],
    height=social_config["height"]
)
```

## 💡 最佳实践

1. **资源缓存**: 资源数据在服务器启动时加载，可以高效访问
2. **组合使用**: 可以组合多个资源来创建更复杂的配置
3. **在 Prompt 中使用**: 在 Prompt 模板中引用资源，让模型使用这些预设数据
4. **类型安全**: 资源返回的是字典类型，使用时要确保键存在

## 🐛 故障排除

### Resource 不显示在 Inspector 中

1. 确保服务器已启动并运行
2. 检查服务器日志，确认 Resource 已注册
3. 刷新 Inspector 页面
4. 检查连接是否正常

### 获取 Resource 失败

1. 检查 URI 是否正确（格式: `resource://资源名称`）
2. 查看服务器日志中的错误信息
3. 确保资源函数返回了有效数据

## 📚 更多信息

- [FastMCP 文档](https://fastmcp.wiki/zh/servers/resources)
- [MCP Protocol 规范](https://modelcontextprotocol.io)
- [MCP Inspector 使用指南](https://modelcontextprotocol.io/inspector)

