# 异步函数修复说明

## 🐛 问题描述

错误信息：`'coroutine' object has no attribute 'get'`

**原因**：`mcp.get_resource()` 是一个异步函数，但在同步函数中调用时没有使用 `await`，导致返回的是协程对象（coroutine）而不是字典。

## ✅ 修复方案

将所有 Resource Template 函数改为异步函数，并在调用 `mcp.get_resource()` 时使用 `await`。

### 修复前（错误）

```python
@mcp.resource("resource://negative_prompts/{image_type}")
def get_negative_prompt_by_type(image_type: str) -> dict:
    # ❌ 错误：没有 await
    all_negative = mcp.get_resource("resource://negative_prompts")
    negative = all_negative.get(image_type.lower(), "")  # ❌ all_negative 是 coroutine，不是 dict
```

### 修复后（正确）

```python
@mcp.resource("resource://negative_prompts/{image_type}")
async def get_negative_prompt_by_type(image_type: str) -> dict:
    # ✅ 正确：使用 await
    all_negative = await mcp.get_resource("resource://negative_prompts")
    negative = all_negative.get(image_type.lower(), "")  # ✅ all_negative 是 dict
```

## 📝 修复的函数列表

已修复的 8 个 Resource Template 函数：

1. ✅ `get_image_style` - 图像风格模板
2. ✅ `get_negative_prompt_by_type` - 负面提示词模板
3. ✅ `get_image_size` - 图像尺寸模板
4. ✅ `get_video_style` - 视频风格模板
5. ✅ `get_generation_config` - 生成配置模板
6. ✅ `get_prompt_template` - 提示词模板
7. ✅ `get_combined_config` - 组合配置模板
8. ✅ `get_generation_plan` - 完整生成方案模板

## 🔧 修复详情

### 1. 函数签名改为异步

```python
# 修复前
def get_image_style(style_name: str) -> dict:

# 修复后
async def get_image_style(style_name: str) -> dict:
```

### 2. 所有 `mcp.get_resource()` 调用添加 `await`

```python
# 修复前
all_styles = mcp.get_resource("resource://image_styles")

# 修复后
all_styles = await mcp.get_resource("resource://image_styles")
```

### 3. 多个资源调用的情况

对于需要调用多个资源的函数（如 `get_combined_config` 和 `get_generation_plan`），所有调用都添加了 `await`：

```python
# 修复前
style = mcp.get_resource(f"resource://styles/{style_name}")
size = mcp.get_resource(f"resource://sizes/{size_name}")
negative = mcp.get_resource("resource://negative_prompts/general")

# 修复后
style = await mcp.get_resource(f"resource://styles/{style_name}")
size = await mcp.get_resource(f"resource://sizes/{size_name}")
negative = await mcp.get_resource("resource://negative_prompts/general")
```

## ✅ 验证

代码已通过验证：

```bash
✓ 代码验证成功
✓ 所有函数已改为异步
✓ 所有 Resource Template 已注册
```

## 📚 相关文档

- [FastMCP Resource Templates 文档](https://fastmcp.wiki/zh/servers/resources)
- [Python 异步编程指南](https://docs.python.org/3/library/asyncio.html)

## 💡 最佳实践

1. **检查函数类型**：如果调用的函数是异步的，必须使用 `await`
2. **函数签名**：如果函数内部使用 `await`，函数本身必须是 `async def`
3. **错误处理**：异步函数中的异常处理与同步函数相同
4. **资源调用**：在 Resource Template 中调用其他资源时，必须使用 `await`

## 🎯 测试

修复后，可以在 MCP Inspector 中测试：

1. 启动服务器：`./run.sh`
2. 启动 Inspector：`./inspector_test_mcp.sh --port 8003`
3. 在 Resources 标签页中测试 Resource Template
4. 输入参数（如 `ggg`）应该不再出现错误

