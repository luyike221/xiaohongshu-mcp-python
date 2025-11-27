# Prompt 功能实现说明

## ✅ 已完成的工作

### 1. 添加了 5 个 Prompt 模板

在 `src/image_video_mcp/prompts/prompts.py` 中使用 `@mcp.prompt()` 装饰器注册了以下 Prompt：

1. **optimize_image_prompt** - 图像提示词优化
   - 参数: `original_prompt` (str)
   - 用途: 优化原始提示词，使其更加详细和专业

2. **video_generation_prompt** - 视频生成提示词
   - 参数: `topic`, `duration`, `style`, `scene`, `action`
   - 用途: 生成详细的视频创建提示词

3. **image_style_description** - 图像风格描述
   - 参数: `subject`, `style_type`, `purpose`
   - 用途: 为特定主题生成详细的图像风格描述

4. **generate_negative_prompt** - 负面提示词生成
   - 参数: `positive_prompt`, `image_type`
   - 用途: 为正面提示词生成对应的负面提示词

5. **batch_image_generation_plan** - 批量图像生成计划
   - 参数: `theme`, `count`, `purpose`, `style_requirement`
   - 用途: 为批量图像生成制定计划

### 2. 实现方式

**目录结构**：
- `src/image_video_mcp/prompts/` - Prompt 模块目录
  - `__init__.py` - 模块初始化文件
  - `prompts.py` - Prompt 定义文件

**代码组织**：
- 所有 Prompt 定义在 `prompts/prompts.py` 中
- 通过 `register_prompts(mcp)` 函数统一注册
- 在 `main.py` 中导入并调用注册函数

使用 FastMCP 的 `@mcp.prompt()` 装饰器方式注册 Prompt：

```python
# prompts/prompts.py
def register_prompts(mcp):
    @mcp.prompt()
    def optimize_image_prompt(original_prompt: str) -> str:
        """Prompt 描述"""
        return f"模板内容，使用 {original_prompt} 作为变量"

# main.py
from .prompts import register_prompts
register_prompts(mcp)
```

### 3. 文档

- ✅ 创建了 `PROMPTS_USAGE.md` - 详细的使用指南
- ✅ 更新了 `README.md` - 添加了 Prompt 功能说明

## 🧪 测试方法

### 1. 启动服务器

```bash
cd /root/project/ai_project/yx_运营/xhs_小红书运营/image_video_mcp
./run.sh
```

或：

```bash
uv run python -m image_video_mcp.main --host 127.0.0.1 --port 8003
```

### 2. 启动 MCP Inspector

```bash
./inspector_test_mcp.sh --port 8003
```

或：

```bash
npx @modelcontextprotocol/inspector
```

### 3. 在 Inspector 中查看 Prompt

1. 打开浏览器访问 `http://localhost:6274`
2. 选择 **HTTP/HTTPS** 传输方式
3. 输入服务器地址: `http://127.0.0.1:8003/mcp`
4. 点击 **Connect**
5. 切换到 **Prompts** 标签页
6. 你应该能看到 5 个已注册的 Prompt

### 4. 测试 Prompt

选择一个 Prompt，填写参数，然后点击 **Run** 或 **Test** 按钮。

## 📝 代码验证

代码已通过语法检查：

```bash
✓ 代码语法正确
✓ Prompt 已注册
```

## 🔍 技术细节

### FastMCP Prompt API

FastMCP 使用装饰器方式注册 Prompt：

```python
@mcp.prompt()
def my_prompt(param1: str, param2: int) -> str:
    """Prompt 描述"""
    return f"模板内容: {param1}, {param2}"
```

### 参数类型

- `str` - 字符串类型
- `int` - 整数类型
- `float` - 浮点数类型
- `bool` - 布尔类型

### 返回值

Prompt 函数应该返回一个字符串，这个字符串会被用作最终的 Prompt 内容。

## 📚 相关文档

- [PROMPTS_USAGE.md](./PROMPTS_USAGE.md) - 详细使用指南
- [README.md](./README.md) - 项目说明
- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [MCP Protocol 规范](https://modelcontextprotocol.io)

## 🎯 下一步

1. 在 MCP Inspector 中测试所有 Prompt
2. 根据实际使用情况调整 Prompt 模板
3. 可以添加更多 Prompt 模板以满足特定需求

