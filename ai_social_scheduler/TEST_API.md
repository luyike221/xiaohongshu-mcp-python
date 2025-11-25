# API 测试指南 - 图文内容场景

## 快速开始

### 1. 启动服务

```bash
# 启动 FastAPI 服务
uvicorn src.ai_social_scheduler.web.app:app --host 0.0.0.0 --port 8000
```

### 2. 测试图文内容发布

#### 方法一：使用 curl 命令

**测试用例1：美食图文内容**
```bash
curl -X POST "http://localhost:8000/api/v1/content/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "request": "我想发布一篇关于家常菜制作的图文笔记，主题是红烧肉的做法，需要配图展示制作步骤",
    "context": {
      "topic": "美食",
      "style": "教程",
      "content_type": "image",
      "image_count": 3,
      "keywords": ["红烧肉", "家常菜", "美食教程"]
    }
  }'
```

**测试用例2：旅行图文内容**
```bash
curl -X POST "http://localhost:8000/api/v1/content/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_002",
    "request": "发布一篇关于云南旅行的图文笔记，分享大理古城的风景和美食",
    "context": {
      "topic": "旅行",
      "style": "分享",
      "content_type": "image",
      "image_count": 4,
      "keywords": ["云南", "大理", "旅行", "古城"]
    }
  }'
```

**测试用例3：穿搭图文内容**
```bash
curl -X POST "http://localhost:8000/api/v1/content/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_003",
    "request": "发布一篇春季穿搭的图文笔记，展示几套不同风格的搭配",
    "context": {
      "topic": "穿搭",
      "style": "分享",
      "content_type": "image",
      "image_count": 5,
      "keywords": ["春季穿搭", "时尚", "搭配"]
    }
  }'
```

#### 方法二：使用 Python 测试脚本

```bash
# 运行测试脚本
python test_content_publish.py
```

### 3. 查询工作流状态

```bash
# 查询工作流状态（替换 workflow_id 为实际的ID）
curl "http://localhost:8000/api/v1/content/status/content_publish_test_user_001"
```

## 请求参数说明

### ContentPublishRequest

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID，用于标识不同的用户 |
| request | string | 是 | 用户请求内容，描述要发布的内容 |
| context | object | 否 | 上下文信息，包含以下可选字段： |

### Context 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| topic | string | 内容主题，如"美食"、"旅行"、"穿搭"等 |
| style | string | 内容风格，如"教程"、"分享"、"评测"等 |
| content_type | string | 内容类型，如"image"（图文）、"video"（视频） |
| image_count | number | 需要的图片数量（图文内容时使用） |
| keywords | array | 关键词列表，用于内容生成和标签 |

## 响应格式

### 成功响应

```json
{
  "success": true,
  "workflow": "content_publish",
  "result": {
    "messages": [...],
    "workflow_id": "content_publish_test_user_001",
    ...
  }
}
```

### 失败响应

```json
{
  "success": false,
  "workflow": "content_publish",
  "result": {},
  "error": "错误信息"
}
```

## 工作流程

1. **API服务层接收** - 接收用户请求
2. **AI决策引擎理解需求** - 分析用户意图和需求
3. **策略管理器生成内容策略** - 生成话题、模板、风格等策略
4. **调用图视频生成服务生成素材** - 使用 `material_generator` agent 生成图片
5. **调用小红书MCP服务发布内容** - 使用 `xiaohongshu_mcp` agent 发布到平台
6. **状态管理器记录执行结果** - 记录执行状态和结果
7. **返回结果给用户** - 返回执行结果

## 注意事项

1. **超时设置**：工作流执行可能需要较长时间（特别是生成图片），建议设置较长的超时时间
2. **服务依赖**：确保以下服务正在运行：
   - 图像视频生成MCP服务（默认：http://127.0.0.1:8003/mcp）
   - 小红书MCP服务（默认：http://127.0.0.1:8002/mcp）
3. **环境变量**：确保已配置必要的环境变量（如 LLM API Key）
4. **日志查看**：可以通过日志查看详细的执行过程

## 故障排查

### 服务无法连接

```bash
# 检查服务是否运行
curl http://localhost:8000/health

# 应该返回: {"status": "healthy"}
```

### 工作流执行失败

1. 检查日志输出
2. 确认 MCP 服务是否正常运行
3. 检查环境变量配置
4. 查看工作流状态接口获取详细错误信息



