# Resource Template 功能实现说明

## ✅ 已完成的工作

### 1. 创建了 templates 模块

在 `src/image_video_mcp/resources/templates/` 目录下创建了资源模板模块：

- `templates/__init__.py` - 导出 `register_resource_templates` 函数
- `templates/templates.py` - 包含所有 8 个 Resource Template 定义

### 2. 添加了 8 个 Resource Template

使用 `@mcp.resource("resource://路径/{参数}")` 装饰器注册了以下资源模板：

1. **resource://styles/{style_name}** - 图像风格模板
   - 根据风格名称获取完整的风格配置
   - 参数: style_name (realistic, anime, watercolor, 等)

2. **resource://negative_prompts/{image_type}** - 负面提示词模板
   - 根据图像类型获取负面提示词
   - 参数: image_type (general, portrait, landscape, product)

3. **resource://sizes/{size_name}** - 图像尺寸模板
   - 根据尺寸名称获取尺寸配置
   - 参数: size_name (square_1k, square_2k, portrait_16_9, 等)

4. **resource://video_styles/{style_name}** - 视频风格模板
   - 根据风格名称获取视频风格配置
   - 参数: style_name (cinematic, documentary, commercial, 等)

5. **resource://configs/{config_name}** - 生成配置模板
   - 根据配置名称获取生成配置
   - 参数: config_name (high_quality, fast_generation, 等)

6. **resource://prompt_templates/{template_name}** - 提示词模板
   - 根据模板名称获取提示词模板
   - 参数: template_name (portrait, landscape, product, 等)

7. **resource://combined_config/{style_name}/{size_name}** - 组合配置模板
   - 组合风格和尺寸生成完整配置
   - 参数: style_name, size_name

8. **resource://generation_plan/{theme}/{style_name}/{size_name}** - 完整生成方案模板
   - 根据主题、风格、尺寸生成完整方案
   - 参数: theme, style_name, size_name

### 3. 集成到主程序

在 `main.py` 中：
- 导入 `register_resource_templates` 函数
- 在注册 Resource 之后、注册 Prompt 之前注册 Resource Template
- 确保 Template 可以使用 Resource 中的数据

### 4. 错误处理

所有 Resource Template 都包含完善的错误处理：
- 参数验证（检查参数是否有效）
- 错误信息返回（包含可用参数列表）
- 异常捕获和日志记录

### 5. 文档

- ✅ 创建了 `RESOURCE_TEMPLATES_USAGE.md` - 详细的使用指南
- ✅ 更新了 `README.md` - 添加了 Resource Template 功能说明
- ✅ 更新了项目结构说明

## 🏗️ 目录结构

```
src/image_video_mcp/
├── main.py
├── prompts/          # Prompt 模块
├── resources/         # Resource 模块
│   ├── __init__.py
│   ├── resources.py   # Resource 定义
│   └── templates/     # ✨ 新建的 Resource Template 模块
│       ├── __init__.py
│       └── templates.py
├── clients/
└── config/
```

## 🔧 实现方式

### Resource Template 注册

使用 FastMCP 的 `@mcp.resource()` 装饰器，URI 中使用 `resource://` scheme 并包含占位符：

```python
@mcp.resource("resource://styles/{style_name}")
def get_image_style(style_name: str) -> dict:
    """根据风格名称获取图像风格配置"""
    # 从基础 Resource 中获取数据
    all_styles = mcp.get_resource("resource://image_styles")
    style = all_styles.get(style_name.lower())
    return style
```

### 在 Prompt 中使用 Resource Template

```python
@mcp.prompt()
def my_prompt(style: str) -> str:
    # 获取资源模板
    style_config = mcp.get_resource(f"resource://styles/{style}")
    
    if "error" in style_config:
        return f"错误: {style_config['error']}"
    
    return f"使用风格: {style_config['name']}"
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

### 3. 在 Inspector 中查看 Resource Template

1. 打开浏览器访问 `http://localhost:6274`
2. 选择 **HTTP/HTTPS** 传输方式
3. 输入服务器地址: `http://127.0.0.1:8003/mcp`
4. 点击 **Connect**
5. 切换到 **Resources** 标签页
6. 你应该能看到 8 个已注册的 Resource Template（URI 包含 `{参数}`）

### 4. 测试 Resource Template

选择一个 Resource Template，填写参数值，然后点击 **Read** 或 **View** 按钮。

## 📊 模板统计

- **Resource Template 数量**: 8 个
- **单参数模板**: 6 个
- **多参数模板**: 2 个
- **组合模板**: 2 个（combined_config, generation_plan）

## 🎯 使用场景

### 场景 1: 动态获取风格配置

```python
# 获取特定风格的配置
anime_style = mcp.get_resource("resource://styles/anime")
keywords = anime_style["keywords"]
```

### 场景 2: 组合配置

```python
# 获取组合配置
config = mcp.get_resource("resource://combined_config/realistic/square_2k")
prompt = config["recommended_prompt"]
width = config["width"]
```

### 场景 3: 完整生成方案

```python
# 获取完整生成方案
plan = mcp.get_resource("resource://generation_plan/一只猫/anime/square_2k")
print(plan["prompt_suggestion"])
print(plan["steps"])
```

## 📚 相关文档

- [RESOURCE_TEMPLATES_USAGE.md](./RESOURCE_TEMPLATES_USAGE.md) - 详细使用指南
- [RESOURCES_USAGE.md](./RESOURCES_USAGE.md) - Resource 使用指南
- [PROMPTS_USAGE.md](./PROMPTS_USAGE.md) - Prompt 使用指南
- [README.md](./README.md) - 项目说明
- [FastMCP 文档](https://fastmcp.wiki/zh/servers/resources)

## 🎉 总结

✅ 成功创建了 Resource Template 模块
✅ 注册了 8 个实用的 Resource Template
✅ 实现了完善的错误处理
✅ 创建了完整的使用文档
✅ 代码验证通过，功能正常

所有 Resource Template 已注册，可以在 MCP Inspector 的 Resources 标签页中查看和使用！

