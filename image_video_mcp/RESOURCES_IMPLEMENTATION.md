# Resource 功能实现说明

## ✅ 已完成的工作

### 1. 创建了 resources 模块

在 `src/image_video_mcp/resources/` 目录下创建了资源模块：

- `resources/__init__.py` - 导出 `register_resources` 函数
- `resources/resources.py` - 包含所有 6 个 Resource 定义

### 2. 添加了 6 个 Resource 资源

使用 `@mcp.resource("resource://uri")` 装饰器注册了以下资源：

1. **image_styles** (`resource://image_styles`)
   - 6 种图像风格预设（写实、动漫、水彩、油画、3D渲染、素描）
   - 每种风格包含名称、描述、关键词、负面关键词

2. **negative_prompts** (`resource://negative_prompts`)
   - 4 种类型的负面提示词库（通用、人物、风景、产品）
   - 用于生成高质量的负面提示词

3. **image_sizes** (`resource://image_sizes`)
   - 8 种常用图像尺寸预设
   - 包含宽度、高度、名称、比例信息

4. **video_styles** (`resource://video_styles`)
   - 5 种视频风格预设（电影感、纪录片、商业广告、Vlog、延时摄影）
   - 每种风格包含关键词和镜头运动建议

5. **generation_configs** (`resource://generation_configs`)
   - 4 种生成配置模板（高质量、快速生成、社交媒体、艺术创作）
   - 包含尺寸、负面提示词、质量标签

6. **prompt_templates** (`resource://prompt_templates`)
   - 5 种提示词模板（人物、风景、产品、动物、抽象）
   - 可复用的提示词结构模板

### 3. 集成到主程序

在 `main.py` 中：
- 导入 `register_resources` 函数
- 在注册 Prompt 之前先注册 Resource
- 确保资源可以在 Prompt 中使用

### 4. 更新了 Prompt 使用 Resource

更新了 `generate_negative_prompt` Prompt，使其使用 `negative_prompts` 资源：
- 从资源中获取负面提示词库
- 根据图像类型选择合适的负面提示词
- 提供更准确的负面提示词建议

### 5. 文档

- ✅ 创建了 `RESOURCES_USAGE.md` - 详细的使用指南
- ✅ 更新了 `README.md` - 添加了 Resource 功能说明
- ✅ 更新了项目结构说明

## 🏗️ 目录结构

```
src/image_video_mcp/
├── main.py
├── prompts/          # Prompt 模块
│   ├── __init__.py
│   └── prompts.py
├── resources/        # ✨ 新建的 Resource 模块
│   ├── __init__.py
│   └── resources.py
├── clients/
└── config/
```

## 🔧 实现方式

### Resource 注册

使用 FastMCP 的 `@mcp.resource()` 装饰器：

```python
@mcp.resource("resource://image_styles")
def get_image_styles() -> dict:
    """获取图像风格预设"""
    return image_styles
```

### 在 Prompt 中使用 Resource

```python
@mcp.prompt()
def generate_negative_prompt(positive_prompt: str, image_type: str) -> str:
    # 获取资源
    negative_prompts = mcp.get_resource("resource://negative_prompts")
    base_negative = negative_prompts.get("general", "")
    
    return f"使用负面提示词: {base_negative}"
```

## 🧪 测试方法

### 1. 启动服务器

```bash
cd /root/project/ai_project/yx_运营/xhs_小红书运营/image_video_mcp
./run.sh
```

### 2. 启动 MCP Inspector

```bash
./inspector_test_mcp.sh --port 8003
```

### 3. 在 Inspector 中查看 Resource

1. 打开浏览器访问 `http://localhost:6274`
2. 选择 **HTTP/HTTPS** 传输方式
3. 输入服务器地址: `http://127.0.0.1:8003/mcp`
4. 点击 **Connect**
5. 切换到 **Resources** 标签页
6. 你应该能看到 6 个已注册的 Resource

### 4. 测试 Resource

选择一个 Resource，点击 **Read** 或 **View** 按钮，查看资源的完整内容。

## 📊 资源统计

- **Resource 数量**: 6 个
- **图像风格**: 6 种
- **负面提示词类型**: 4 种
- **图像尺寸**: 8 种
- **视频风格**: 5 种
- **生成配置**: 4 种
- **提示词模板**: 5 种

## 🎯 使用场景

### 场景 1: 使用风格预设

```python
# 获取风格资源
styles = mcp.get_resource("resource://image_styles")
anime_style = styles["anime"]

# 使用风格关键词生成图像
prompt = f"a cat, {anime_style['keywords']}"
```

### 场景 2: 使用尺寸预设

```python
# 获取尺寸资源
sizes = mcp.get_resource("resource://image_sizes")
social_size = sizes["portrait_9_16"]

# 使用尺寸生成图像
generate_image(
    prompt="a beautiful landscape",
    width=social_size["width"],
    height=social_size["height"]
)
```

### 场景 3: 使用生成配置

```python
# 获取配置资源
configs = mcp.get_resource("resource://generation_configs")
high_quality = configs["high_quality"]

# 使用配置生成图像
generate_image(
    prompt=f"{user_prompt}, {high_quality['quality_tags']}",
    negative_prompt=high_quality["negative_prompt"],
    width=high_quality["width"],
    height=high_quality["height"]
)
```

## 📚 相关文档

- [RESOURCES_USAGE.md](./RESOURCES_USAGE.md) - 详细使用指南
- [PROMPTS_USAGE.md](./PROMPTS_USAGE.md) - Prompt 使用指南
- [README.md](./README.md) - 项目说明
- [FastMCP 文档](https://fastmcp.wiki/zh/servers/resources)

## 🎉 总结

✅ 成功创建了 Resource 模块
✅ 注册了 6 个实用的 Resource 资源
✅ 更新了 Prompt 以使用 Resource
✅ 创建了完整的使用文档
✅ 代码验证通过，功能正常

所有 Resource 资源已注册，可以在 MCP Inspector 的 Resources 标签页中查看和使用！

