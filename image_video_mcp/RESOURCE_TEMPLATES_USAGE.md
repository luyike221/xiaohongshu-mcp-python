# FastMCP Resource Template 使用指南

本文档说明如何在 Image Video MCP 服务中使用 Resource Template 功能。

## 📋 概述

Resource Templates（资源模板）使用 URI 模板（包含占位符）来定义动态资源。LLM 可以通过提供具体参数来访问不同的资源实例，实现更灵活的数据访问。

本项目已注册了 8 个 Resource Template，可以在 MCP Inspector 的 **Resources** 标签页中查看和使用。

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

### 3. 在 MCP Inspector 中查看 Resource Template

1. 打开浏览器访问 `http://localhost:6274`
2. 选择 **HTTP/HTTPS** 传输方式
3. 输入服务器地址: `http://127.0.0.1:8003/mcp`
4. 点击 **Connect** 连接
5. 切换到 **Resources** 标签页
6. 你将看到所有已注册的 Resource 和 Resource Template

## 📝 可用的 Resource Template

### 1. resource://styles/{style_name} - 图像风格模板

**URI 模板**: `resource://styles/{style_name}`

**参数**:
- `style_name`: 风格名称（realistic, anime, watercolor, oil_painting, 3d_render, sketch）

**示例**:
```
resource://styles/anime
resource://styles/realistic
resource://styles/watercolor
```

**返回**: 指定风格的完整配置（名称、描述、关键词、负面关键词）

---

### 2. resource://negative_prompts/{image_type} - 负面提示词模板

**URI 模板**: `resource://negative_prompts/{image_type}`

**参数**:
- `image_type`: 图像类型（general, portrait, landscape, product）

**示例**:
```
resource://negative_prompts/portrait
resource://negative_prompts/landscape
resource://negative_prompts/general
```

**返回**: 指定类型的负面提示词配置

---

### 3. resource://sizes/{size_name} - 图像尺寸模板

**URI 模板**: `resource://sizes/{size_name}`

**参数**:
- `size_name`: 尺寸名称（square_1k, square_2k, portrait_16_9, portrait_9_16, 等）

**示例**:
```
resource://sizes/square_2k
resource://sizes/portrait_9_16
resource://sizes/wide_21_9
```

**返回**: 指定尺寸的完整配置（宽度、高度、名称、比例）

---

### 4. resource://video_styles/{style_name} - 视频风格模板

**URI 模板**: `resource://video_styles/{style_name}`

**参数**:
- `style_name`: 视频风格名称（cinematic, documentary, commercial, vlog, timelapse）

**示例**:
```
resource://video_styles/cinematic
resource://video_styles/documentary
resource://video_styles/vlog
```

**返回**: 指定视频风格的完整配置（名称、描述、关键词、镜头运动建议）

---

### 5. resource://configs/{config_name} - 生成配置模板

**URI 模板**: `resource://configs/{config_name}`

**参数**:
- `config_name`: 配置名称（high_quality, fast_generation, social_media, artistic）

**示例**:
```
resource://configs/high_quality
resource://configs/social_media
resource://configs/fast_generation
```

**返回**: 指定生成配置的完整信息（尺寸、负面提示词、质量标签）

---

### 6. resource://prompt_templates/{template_name} - 提示词模板

**URI 模板**: `resource://prompt_templates/{template_name}`

**参数**:
- `template_name`: 模板名称（portrait, landscape, product, animal, abstract）

**示例**:
```
resource://prompt_templates/portrait
resource://prompt_templates/landscape
resource://prompt_templates/product
```

**返回**: 指定提示词模板的完整信息

---

### 7. resource://combined_config/{style_name}/{size_name} - 组合配置模板

**URI 模板**: `resource://combined_config/{style_name}/{size_name}`

**参数**:
- `style_name`: 风格名称
- `size_name`: 尺寸名称

**示例**:
```
resource://combined_config/anime/square_2k
resource://combined_config/realistic/portrait_9_16
resource://combined_config/watercolor/square_1k
```

**返回**: 组合后的完整配置（风格 + 尺寸 + 推荐提示词和负面提示词）

---

### 8. resource://generation_plan/{theme}/{style_name}/{size_name} - 完整生成方案模板

**URI 模板**: `resource://generation_plan/{theme}/{style_name}/{size_name}`

**参数**:
- `theme`: 图像主题
- `style_name`: 风格名称
- `size_name`: 尺寸名称

**示例**:
```
resource://generation_plan/一只可爱的猫/anime/square_2k
resource://generation_plan/美丽的风景/realistic/portrait_16_9
resource://generation_plan/咖啡店/watercolor/square_1k
```

**返回**: 完整的生成方案（主题 + 风格 + 尺寸 + 提示词建议 + 步骤说明）

## 🔧 在 Prompt 中使用 Resource Template

你可以在 Prompt 函数中通过 `mcp.get_resource()` 获取资源模板：

```python
@mcp.prompt()
def my_prompt(style: str, size: str) -> str:
    # 获取资源模板
    style_config = mcp.get_resource(f"resource://styles/{style}")
    size_config = mcp.get_resource(f"resource://sizes/{size}")
    
    return f"""使用风格: {style_config['name']}
尺寸: {size_config['width']}x{size_config['height']}"""
```

## 🧪 在 MCP Inspector 中测试

### 测试单个资源模板

1. 在 **Resources** 标签页中找到资源模板（URI 包含 `{参数}`）
2. 点击资源模板
3. 在参数输入框中填写参数值
4. 点击 **Read** 或 **View** 按钮
5. 查看生成的资源内容

### 示例：测试风格模板

1. 找到 `resource://styles/{style_name}` 资源模板
2. 在参数输入框中输入 `anime`
3. 点击 **Read**
4. 查看返回的动漫风格配置

### 示例：测试组合配置模板

1. 找到 `resource://combined_config/{style_name}/{size_name}` 资源模板
2. 在参数输入框中输入 `anime/square_2k`
3. 点击 **Read**
4. 查看返回的组合配置

## 📚 代码示例

### 示例 1: 使用风格模板

```python
# 获取特定风格的配置
anime_style = mcp.get_resource("resource://styles/anime")
print(anime_style["keywords"])  # 输出动漫风格关键词
print(anime_style["negative_keywords"])  # 输出负面关键词
```

### 示例 2: 使用尺寸模板

```python
# 获取特定尺寸的配置
size = mcp.get_resource("resource://sizes/portrait_9_16")
width = size["width"]  # 1080
height = size["height"]  # 1920
```

### 示例 3: 使用组合配置模板

```python
# 获取组合配置
config = mcp.get_resource("resource://combined_config/realistic/square_2k")
prompt = config["recommended_prompt"]
negative = config["recommended_negative"]
width = config["width"]  # 2048
height = config["height"]  # 2048
```

### 示例 4: 使用完整生成方案模板

```python
# 获取完整生成方案
plan = mcp.get_resource("resource://generation_plan/一只猫/anime/square_2k")
print(plan["prompt_suggestion"])  # 推荐的提示词
print(plan["negative_prompt"])  # 负面提示词
print(plan["steps"])  # 生成步骤
```

## 💡 最佳实践

1. **参数验证**: Resource Template 会自动验证参数，如果参数无效会返回错误信息
2. **组合使用**: 可以组合多个 Resource Template 来创建更复杂的配置
3. **在 Prompt 中使用**: 在 Prompt 模板中引用 Resource Template，让模型动态获取配置
4. **错误处理**: 检查返回结果中是否包含 "error" 字段

## 🆚 Resource vs Resource Template

| 特性 | Resource | Resource Template |
|------|----------|-------------------|
| URI 格式 | `resource://名称` | `resource://路径/{参数}` |
| 参数 | 无 | 支持占位符参数 |
| 使用场景 | 静态数据 | 动态数据 |
| 示例 | `resource://image_styles` | `resource://styles/anime` |

## 🐛 故障排除

### Template 不显示在 Inspector 中

1. 确保服务器已启动并运行
2. 检查服务器日志，确认 Template 已注册
3. 刷新 Inspector 页面
4. 检查连接是否正常

### 获取 Template 失败

1. 检查 URI 格式是否正确（使用 `resource://` scheme，包含占位符 `{参数}`）
2. 确保参数值有效（参考可用参数列表）
3. 查看服务器日志中的错误信息
4. 检查返回结果中的 "error" 字段
5. 确保 URI 使用标准格式：`resource://路径/{参数}`

### 参数错误

如果参数无效，Template 会返回错误信息，包含：
- `error`: 错误描述
- `available_*`: 可用的参数列表

## 📚 更多信息

- [RESOURCES_USAGE.md](./RESOURCES_USAGE.md) - Resource 使用指南
- [PROMPTS_USAGE.md](./PROMPTS_USAGE.md) - Prompt 使用指南
- [README.md](./README.md) - 项目说明
- [FastMCP 文档](https://fastmcp.wiki/zh/servers/resources)

