# FastMCP Prompt 使用指南

本文档说明如何在 Image Video MCP 服务中使用 Prompt 功能。

## 📋 概述

本项目已注册了 5 个 Prompt 模板，可以在 MCP Inspector 的 **Prompts** 标签页中查看和使用。这些 Prompt 可以帮助你：

1. 优化图像生成提示词
2. 生成视频创建提示词
3. 描述图像风格
4. 生成负面提示词
5. 制定批量图像生成计划

## 🚀 快速开始

### 1. 启动 MCP 服务器

```bash
cd /root/project/ai_project/yx_运营/xhs_小红书运营/image_video_mcp
./run.sh
```

或者：

```bash
uv run python -m image_video_mcp.main --host 127.0.0.1 --port 8003
```

### 2. 启动 MCP Inspector

在另一个终端中：

```bash
cd /root/project/ai_project/yx_运营/xhs_小红书运营/image_video_mcp
./inspector_test_mcp.sh --port 8003
```

或者直接使用：

```bash
npx @modelcontextprotocol/inspector
```

### 3. 在 MCP Inspector 中查看 Prompt

1. 打开浏览器访问 `http://localhost:6274`（Inspector 默认端口）
2. 在 Inspector 界面中，选择 **HTTP/HTTPS** 传输方式
3. 输入服务器地址：`http://127.0.0.1:8003/mcp`
4. 点击 **Connect** 连接
5. 切换到 **Prompts** 标签页
6. 你将看到所有已注册的 Prompt 模板

## 📝 可用的 Prompt 模板

### 1. optimize_image_prompt - 图像提示词优化

**用途**：优化原始提示词，使其更加详细和专业

**参数**：
- `original_prompt` (string): 原始提示词

**示例**：
```
原始提示词: "一只猫"
```

**输出**：优化后的提示词、负面提示词建议、推荐尺寸

---

### 2. video_generation_prompt - 视频生成提示词

**用途**：生成详细的视频创建提示词

**参数**：
- `topic` (string): 视频主题
- `duration` (number): 视频时长（秒）
- `style` (string): 视频风格
- `scene` (string): 场景描述
- `action` (string): 动作描述

**示例**：
```
topic: "春日风景"
duration: 10
style: "自然纪录片"
scene: "樱花盛开的公园"
action: "缓慢推拉镜头"
```

---

### 3. image_style_description - 图像风格描述

**用途**：为特定主题生成详细的图像风格描述

**参数**：
- `subject` (string): 图像主题/主体
- `style_type` (string): 风格类型（如：写实、插画、水彩等）
- `purpose` (string): 用途（如：社交媒体、广告等）

**示例**：
```
subject: "咖啡店"
style_type: "温暖插画"
purpose: "社交媒体配图"
```

---

### 4. generate_negative_prompt - 负面提示词生成

**用途**：为正面提示词生成对应的负面提示词

**参数**：
- `positive_prompt` (string): 正面提示词
- `image_type` (string): 图像类型（如：人物、风景、产品等）

**示例**：
```
positive_prompt: "一只坐着的橙色猫，表情开心，活泼可爱，真实准确"
image_type: "动物"
```

**输出**：负面提示词列表，用于排除不想要的元素

---

### 5. batch_image_generation_plan - 批量图像生成计划

**用途**：为批量图像生成制定计划

**参数**：
- `theme` (string): 主题系列
- `count` (number): 生成数量
- `purpose` (string): 用途
- `style_requirement` (string): 风格要求

**示例**：
```
theme: "四季风景"
count: 4
purpose: "社交媒体内容"
style_requirement: "统一风格，但各有特色"
```

**输出**：每张图像的详细提示词和配置建议

## 🧪 测试 Prompt

### 在 MCP Inspector 中测试

1. 在 **Prompts** 标签页中选择一个 Prompt
2. 填写所需的参数
3. 点击 **Run** 或 **Test** 按钮
4. 查看生成的 Prompt 内容

### 使用示例

#### 示例 1：优化图像提示词

1. 选择 `optimize_image_prompt`
2. 输入参数：
   ```
   original_prompt: "一只猫"
   ```
3. 运行后，你将得到：
   - 优化后的详细提示词
   - 负面提示词建议
   - 推荐尺寸

#### 示例 2：生成视频提示词

1. 选择 `video_generation_prompt`
2. 输入参数：
   ```
   topic: "城市夜景"
   duration: 15
   style: "电影感"
   scene: "繁华的都市街道"
   action: "缓慢推进，展示细节"
   ```
3. 运行后，你将得到详细的视频生成提示词

## 🔧 代码示例

如果你想在代码中使用这些 Prompt，可以通过 MCP 客户端调用：

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 连接到 MCP 服务器
async with stdio_client(StdioServerParameters(...)) as (read, write):
    async with ClientSession(read, write) as session:
        # 获取所有 Prompt
        prompts = await session.list_prompts()
        
        # 使用 Prompt
        result = await session.get_prompt(
            name="optimize_image_prompt",
            arguments={
                "original_prompt": "一只猫"
            }
        )
        print(result)
```

## 📚 更多信息

- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [MCP Protocol 规范](https://modelcontextprotocol.io)
- [MCP Inspector 使用指南](https://modelcontextprotocol.io/inspector)

## 🐛 故障排除

### Prompt 不显示在 Inspector 中

1. 确保服务器已启动并运行
2. 检查服务器日志，确认 Prompt 已注册
3. 刷新 Inspector 页面
4. 检查连接是否正常

### Prompt 执行失败

1. 检查参数是否正确填写
2. 查看服务器日志中的错误信息
3. 确保所有必需参数都已提供

## 💡 提示

- Prompt 模板中的 `{variable}` 格式会在运行时被实际值替换
- 参数类型必须匹配（string 或 number）
- 可以在 Inspector 中直接测试 Prompt，无需编写代码

