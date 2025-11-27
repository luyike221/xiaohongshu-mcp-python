# FunctionResource 错误修复说明

## 🐛 问题描述

错误信息：`'FunctionResource' object has no attribute 'get'`

**原因**：在 Resource Template 函数中，通过 `mcp.get_resource()` 调用其他资源时，返回的是 `FunctionResource` 对象（被装饰器包装的函数），而不是实际的字典数据。

## ✅ 修复方案

采用**提取共享数据到模块级别**的方案：

1. **将数据字典提取到模块级别**：在 `resources.py` 中将所有数据字典提取到模块级别（如 `IMAGE_STYLES`, `NEGATIVE_PROMPTS` 等）
2. **直接访问数据**：在 Resource Template 函数中直接访问这些数据字典，而不是通过 `mcp.get_resource()`
3. **移除异步**：由于不再需要调用异步的 `mcp.get_resource()`，所有 Resource Template 函数改回同步函数

## 📝 修复详情

### 1. 数据提取到模块级别

**修复前**（数据在函数内部）：
```python
def register_resources(mcp):
    image_styles = {...}  # 数据在函数内部
    @mcp.resource("resource://image_styles")
    def get_image_styles() -> dict:
        return image_styles
```

**修复后**（数据在模块级别）：
```python
# 模块级别的数据
IMAGE_STYLES = {...}
NEGATIVE_PROMPTS = {...}
IMAGE_SIZES = {...}
# ... 等等

def register_resources(mcp):
    @mcp.resource("resource://image_styles")
    def get_image_styles() -> dict:
        return IMAGE_STYLES  # 返回模块级别的数据
```

### 2. Resource Template 直接访问数据

**修复前**（通过 mcp.get_resource 调用）：
```python
@mcp.resource("resource://negative_prompts/{image_type}")
async def get_negative_prompt_by_type(image_type: str) -> dict:
    # ❌ 错误：返回 FunctionResource 对象
    all_negative = await mcp.get_resource("resource://negative_prompts")
    negative = all_negative.get(image_type.lower(), "")  # ❌ 错误
```

**修复后**（直接访问数据）：
```python
from ..resources import NEGATIVE_PROMPTS

@mcp.resource("resource://negative_prompts/{image_type}")
def get_negative_prompt_by_type(image_type: str) -> dict:
    # ✅ 正确：直接访问数据字典
    negative = NEGATIVE_PROMPTS.get(image_type.lower(), "")  # ✅ 正确
```

### 3. 移除异步

由于不再需要调用异步的 `mcp.get_resource()`，所有 Resource Template 函数改回同步函数：

```python
# 修复前
async def get_image_style(style_name: str) -> dict:
    all_styles = await mcp.get_resource("resource://image_styles")

# 修复后
def get_image_style(style_name: str) -> dict:
    style = IMAGE_STYLES.get(style_name.lower())
```

## 🔧 修复的函数列表

已修复的 8 个 Resource Template 函数：

1. ✅ `get_image_style` - 直接访问 `IMAGE_STYLES`
2. ✅ `get_negative_prompt_by_type` - 直接访问 `NEGATIVE_PROMPTS`
3. ✅ `get_image_size` - 直接访问 `IMAGE_SIZES`
4. ✅ `get_video_style` - 直接访问 `VIDEO_STYLES`
5. ✅ `get_generation_config` - 直接访问 `GENERATION_CONFIGS`
6. ✅ `get_prompt_template` - 直接访问 `PROMPT_TEMPLATES`
7. ✅ `get_combined_config` - 直接访问 `IMAGE_STYLES` 和 `IMAGE_SIZES`
8. ✅ `get_generation_plan` - 直接访问 `IMAGE_STYLES`、`IMAGE_SIZES` 和 `NEGATIVE_PROMPTS`

## 📊 代码结构变化

### 修复前
```
resources.py
  └─ register_resources()
      └─ 数据字典（局部变量）
          └─ Resource 函数返回数据

templates.py
  └─ register_resource_templates()
      └─ Resource Template 函数
          └─ mcp.get_resource() ❌ 返回 FunctionResource
```

### 修复后
```
resources.py
  ├─ 数据字典（模块级别）✅
  └─ register_resources()
      └─ Resource 函数返回模块级别数据

templates.py
  └─ register_resource_templates()
      └─ Resource Template 函数
          └─ 直接访问模块级别数据 ✅
```

## ✅ 验证

代码已通过验证：

```bash
✓ 代码验证成功
✓ 所有 Resource Template 已修复
✓ 已注册 6 个 Resource 资源
✓ 已注册 8 个 Resource Template 模板
✓ 已注册 5 个 Prompt 模板
```

## 💡 最佳实践

1. **数据与接口分离**：将数据定义在模块级别，Resource 函数只负责暴露接口
2. **避免在 Resource 中调用其他 Resource**：使用 `mcp.get_resource()` 会返回 `FunctionResource` 对象
3. **共享数据访问**：如果需要共享数据，提取到模块级别，让多个函数直接访问
4. **同步 vs 异步**：如果不需要异步操作，使用同步函数更简单

## 🎯 测试

修复后，可以在 MCP Inspector 中测试：

1. 启动服务器：`./run.sh`
2. 启动 Inspector：`./inspector_test_mcp.sh --port 8003`
3. 在 Resources 标签页中测试 Resource Template
4. 输入参数（如 `ggg`）应该返回正确的错误信息，而不是 `FunctionResource` 错误

