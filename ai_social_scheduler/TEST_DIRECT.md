# 直接测试内容发布工作流 - 图文内容场景

## 说明

本测试脚本直接调用 Supervisor 和工作流，不通过 Web API，适合开发和调试使用。

## 使用方法

### 1. 基本测试（多个用例）

```bash
python test_content_publish.py
```

### 2. 单个用例测试（快速测试）

```bash
python test_content_publish.py --single
```

## 前置条件

### 1. 环境变量配置

确保在 `.env` 文件中配置了必要的环境变量：

```env
# LLM配置
ALIBABA_BAILIAN_API_KEY=your_api_key
ALIBABA_BAILIAN_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
ALIBABA_BAILIAN_MODEL=qwen-plus

# MCP服务配置
XIAOHONGSHU_MCP_URL=http://localhost:8002/mcp
XIAOHONGSHU_MCP_TRANSPORT=streamable_http
IMAGE_VIDEO_MCP_URL=http://localhost:8003/mcp
IMAGE_VIDEO_MCP_TRANSPORT=streamable_http
```

### 2. MCP 服务运行

确保以下服务正在运行：

- **图像视频生成MCP服务**：默认地址 `http://127.0.0.1:8003/mcp`
- **小红书MCP服务**：默认地址 `http://127.0.0.1:8002/mcp`

## 测试用例

脚本包含以下图文内容测试用例：

1. **美食图文内容** - 红烧肉制作教程（3张图片）
2. **旅行图文内容** - 云南大理旅行分享（4张图片）
3. **穿搭图文内容** - 春季穿搭分享（5张图片）

## 工作流程

测试脚本会执行以下流程：

1. 创建 Supervisor 和所有智能体
2. 创建工作流实例（ContentPublishWorkflow）
3. 对每个测试用例：
   - 显示输入数据
   - 执行工作流
   - 显示执行结果
   - 显示成功/失败状态

## 输出示例

```
============================================================
小红书内容发布工作流测试 - 图文内容场景（直接调用）
============================================================

正在创建 Supervisor 和所有智能体...
✅ Supervisor 创建成功

============================================================
测试用例 1: 美食图文内容
============================================================
输入数据:
{
  "user_id": "test_user_001",
  "request": "我想发布一篇关于家常菜制作的图文笔记...",
  "context": {
    "topic": "美食",
    "style": "教程",
    "content_type": "image",
    "image_count": 3,
    "keywords": ["红烧肉", "家常菜", "美食教程"]
  }
}

开始执行工作流...

工作流执行结果:
{
  "success": true,
  "workflow": "content_publish",
  "result": {
    ...
  }
}

✅ 测试通过: 美食图文内容
工作流ID: content_publish_test_user_001
```

## 故障排查

### 1. 导入错误

如果遇到导入错误，确保：
- 在项目根目录运行脚本
- 已安装所有依赖：`uv sync` 或 `pip install -e .`

### 2. Supervisor 创建失败

检查：
- 环境变量是否正确配置
- LLM API Key 是否有效
- 网络连接是否正常

### 3. 工作流执行失败

检查：
- MCP 服务是否正在运行
- MCP 服务地址是否正确
- 查看详细错误信息（脚本会打印 traceback）

### 4. 执行超时

工作流执行可能需要较长时间，特别是：
- 生成图片的步骤（可能需要几分钟）
- LLM 推理步骤

如果经常超时，可以：
- 减少图片数量
- 检查 MCP 服务性能
- 增加超时时间（修改代码中的超时设置）

## 与 Web API 测试的区别

| 特性 | 直接调用 | Web API |
|------|---------|---------|
| 启动服务 | 不需要 | 需要启动 uvicorn |
| 调试 | 更容易（直接看到错误） | 需要通过日志 |
| 性能 | 更快（无网络开销） | 有网络开销 |
| 部署 | 适合开发测试 | 适合生产环境 |
| 错误信息 | 完整的 Python traceback | HTTP 错误响应 |

## 自定义测试用例

可以修改 `test_content_publish.py` 中的 `test_cases` 列表来添加自己的测试用例：

```python
test_cases = [
    {
        "name": "你的测试用例名称",
        "data": {
            "user_id": "your_user_id",
            "request": "你的请求内容",
            "context": {
                "topic": "主题",
                "style": "风格",
                "content_type": "image",
                "image_count": 3,
                "keywords": ["关键词1", "关键词2"]
            }
        }
    }
]
```



