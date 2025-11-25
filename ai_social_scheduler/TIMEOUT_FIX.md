# 超时问题解决方案

## 问题描述

在执行工作流时，`understand_request` 步骤报错 `Request timed out.`，这是因为默认的 LLM 超时时间（60秒）不足以完成请求。

## 原因分析

1. **网络延迟**：调用阿里云通义千问 API 可能存在网络延迟
2. **LLM 推理时间**：复杂的意图理解需要较长的 LLM 推理时间
3. **默认超时过短**：`QwenClient` 默认 timeout=60 秒

## 解决方案

### 方案 1：配置环境变量（推荐）

在 `.env` 文件中添加超时配置：

```env
# LLM 配置
ALIBABA_BAILIAN_API_KEY=your_api_key
ALIBABA_BAILIAN_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
ALIBABA_BAILIAN_MODEL=qwen-plus
ALIBABA_BAILIAN_TIMEOUT=180  # 增加到 180 秒（3分钟）
```

### 方案 2：修改代码中的超时时间

如果方案 1 不生效，可以在创建工作流时传递超时参数。

#### 修改 `graph/factory.py`：

```python
async def create_content_publish_graph(
    llm_model: str = "qwen-plus",
    llm_temperature: float = 0.7,
    llm_timeout: int = 180,  # 新增：超时时间（秒）
    llm_api_key: Optional[str] = None,
    ...
) -> Any:
    # ... 现有代码 ...
```

#### 修改 `DecisionEngine` 和 `StrategyManager` 初始化：

需要在这两个类中支持传递 `timeout` 参数给 `QwenClient`。

**修改 `supervisor/decision_engine.py`：**

```python
class DecisionEngine:
    def __init__(
        self, 
        model: str = "qwen-plus", 
        temperature: float = 0.7,
        timeout: int = 180  # 新增
    ):
        """初始化决策引擎"""
        self.client = QwenClient(
            model=model, 
            temperature=temperature,
            timeout=timeout  # 传递超时时间
        )
        self.logger = logger
```

**修改 `supervisor/strategy_manager.py`：**

```python
class StrategyManager:
    def __init__(
        self, 
        model: str = "qwen-plus", 
        temperature: float = 0.7,
        timeout: int = 180  # 新增
    ):
        """初始化策略管理器"""
        self.client = QwenClient(
            model=model, 
            temperature=temperature,
            timeout=timeout  # 传递超时时间
        )
        self.logger = logger
```

**修改 `graph/factory.py` 中的调用：**

```python
decision_engine = DecisionEngine(
    model=llm_model,
    temperature=llm_temperature,
    timeout=llm_timeout  # 传递超时时间
)

strategy_manager = StrategyManager(
    model=llm_model,
    temperature=llm_temperature,
    timeout=llm_timeout  # 传递超时时间
)
```

### 方案 3：网络优化

1. **使用代理**：如果在国内，可能需要配置代理访问阿里云 API
2. **检查网络**：确保服务器与阿里云 API 之间网络通畅
3. **使用更快的模型**：考虑使用 `qwen-turbo` 代替 `qwen-plus`（速度更快但质量稍低）

## 进度可视化改进

已添加详细的进度日志，现在每个步骤都会显示：

```
📋 [步骤 1/7] 初始化工作流
🧠 [步骤 2/7] 理解用户需求 - 调用 AI 决策引擎分析意图...
✅ 需求理解完成
📝 [步骤 3/7] 生成内容策略 - 确定话题、风格、关键词...
✅ 策略生成完成
🎨 [步骤 4/7] 生成素材 - MaterialAgent 将生成 3 张图片（需要较长时间）...
✅ 素材生成完成
✍️  [步骤 5/7] 生成文案 - ContentAgent 创建标题、正文、标签...
✅ 文案生成完成
📤 [步骤 6/7] 发布内容 - XiaohongshuAgent 发布到小红书平台...
✅ 内容发布成功
💾 [步骤 7/7] 记录结果 - 保存工作流执行记录...
🎉 工作流执行完成！所有步骤已成功完成。
```

## 验证修复

运行测试：

```bash
# 方案 1：使用环境变量（推荐）
python3 test_content_publish.py --single

# 方案 2：如果修改了代码
python3 test_content_publish.py --single
```

观察日志输出，确认：
1. ✅ 每个步骤都有清晰的进度提示
2. ✅ 不再出现 timeout 错误
3. ✅ 工作流顺利执行到完成

## 推荐配置

对于生产环境，推荐以下超时配置：

- **DecisionEngine（意图理解）**：180 秒（复杂分析）
- **StrategyManager（策略生成）**：120 秒（中等复杂度）
- **ContentGenerator（文案生成）**：120 秒（中等复杂度）
- **MaterialGenerator（素材生成）**：600 秒（图片生成最慢）
- **XiaohongshuPublisher（发布）**：60 秒（网络请求）

## 故障排查

如果仍然超时：

1. **检查 API Key**：确认 `ALIBABA_BAILIAN_API_KEY` 有效
2. **检查网络**：`curl https://dashscope.aliyuncs.com/compatible-mode/v1/models`
3. **查看详细日志**：设置环境变量 `LOG_LEVEL=DEBUG`
4. **测试单独调用**：

```python
from ai_social_scheduler.ai_agent.client import QwenClient
import asyncio

async def test_llm():
    client = QwenClient(timeout=180)
    from langchain_core.messages import HumanMessage
    response = await client.client.ainvoke([
        HumanMessage(content="你好")
    ])
    print(response.content)

asyncio.run(test_llm())
```

---

**修复完成后可以删除此文件**



