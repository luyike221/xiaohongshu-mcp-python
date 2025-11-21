# 提示词管理模块

## 目录结构

```
prompts/
├── __init__.py                    # 导出所有提示词
├── supervisor/                    # Supervisor 提示词
│   ├── __init__.py
│   └── supervisor_prompts.py    # Supervisor 提示词定义
├── agents/                        # Agents 提示词
│   ├── __init__.py
│   └── agent_prompts.py          # Agents 提示词定义
└── workflows/                     # Workflows 提示词
    └── __init__.py
```

## 使用方式

### 1. 导入提示词

```python
from ai_social_scheduler.prompts import (
    SUPERVISOR_PROMPT,
    CONTENT_GENERATOR_PROMPT,
    XHS_PUBLISHER_PROMPT,
)
```

### 2. 在 Supervisor 中使用

```python
from ai_social_scheduler.prompts.supervisor import CONTENT_PUBLISH_SUPERVISOR_PROMPT

# 使用工作流特定的提示词
prompt = CONTENT_PUBLISH_SUPERVISOR_PROMPT.format(agent_list=agent_list)
```

### 3. 在 Agents 中使用

```python
from ai_social_scheduler.prompts.agents import CONTENT_GENERATOR_PROMPT

# 创建智能体时使用提示词
agent = create_react_agent(
    llm,
    tools=[...],
    prompt=CONTENT_GENERATOR_PROMPT,
    name="content_generator",
)
```

## 提示词分类

### Supervisor 提示词

- `SUPERVISOR_PROMPT` - 通用 Supervisor 提示词
- `CONTENT_PUBLISH_SUPERVISOR_PROMPT` - 内容发布工作流
- `AUTO_REPLY_SUPERVISOR_PROMPT` - 自动回复工作流
- `SCHEDULED_PUBLISH_SUPERVISOR_PROMPT` - 定时发布工作流
- `HOT_TOPIC_TRACKING_SUPERVISOR_PROMPT` - 热点追踪工作流
- `EXCEPTION_HANDLING_SUPERVISOR_PROMPT` - 异常处理工作流
- `COMPETITOR_ANALYSIS_SUPERVISOR_PROMPT` - 竞品分析工作流
- `MESSAGE_HANDLING_SUPERVISOR_PROMPT` - 私信处理工作流
- `PERFORMANCE_ANALYSIS_SUPERVISOR_PROMPT` - 表现分析工作流

### Agents 提示词

- `CONTENT_GENERATOR_PROMPT` - 内容生成智能体
- `CONTENT_STRATEGY_PROMPT` - 内容策略智能体
- `VIDEO_GENERATOR_PROMPT` - 图视频生成智能体
- `XHS_PUBLISHER_PROMPT` - 小红书发布智能体
- `XHS_INTERACTION_PROMPT` - 小红书互动智能体
- `XHS_SEARCH_PROMPT` - 小红书搜索智能体
- `DATA_ANALYZER_PROMPT` - 数据分析智能体
- `PERFORMANCE_ANALYZER_PROMPT` - 表现分析智能体
- `COMPETITOR_ANALYZER_PROMPT` - 竞品分析智能体
- `EXCEPTION_HANDLER_PROMPT` - 异常处理智能体

## 提示词管理最佳实践

1. **集中管理**：所有提示词都放在 `prompts/` 目录下
2. **分类组织**：按 Supervisor、Agents、Workflows 分类
3. **版本控制**：提示词修改要记录在版本控制中
4. **文档说明**：每个提示词都要有清晰的说明
5. **参数化**：使用 `{variable}` 格式支持动态参数
6. **可测试**：提示词要易于测试和调优

## 修改提示词

1. 在对应的提示词文件中修改
2. 更新文档说明
3. 测试修改后的效果
4. 提交代码变更

## 注意事项

- 提示词中的 `{agent_list}` 等参数需要在使用时格式化
- 提示词要清晰、明确，避免歧义
- 定期审查和优化提示词效果

