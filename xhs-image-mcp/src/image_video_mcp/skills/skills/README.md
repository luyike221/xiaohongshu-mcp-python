# Skills 目录说明

本目录包含所有图片和视频生成相关的提示词 Skills（技能）。

## Skills 文件格式

每个 Skill 文件遵循以下 Markdown 格式：

```markdown
# skill_name
> 技能描述（一句话说明）

技能详细内容...

支持 {参数} 格式的参数化模板
```

## Skills 列表

### 核心提示词 Skills

- **z_images_system_prompt.md**: Z-Images 客户端专用的系统提示词
- **z_images_user_prompt.md**: Z-Images 客户端专用的用户提示词模板
- **default_system_prompt.md**: 默认的系统提示词（用于非 Z-Images 客户端）
- **default_user_prompt.md**: 默认的用户提示词模板（用于非 Z-Images 客户端）

### 客户端模板 Skills

- **z_image_client_template.md**: Z-Image 客户端的提示词模板
- **wan_t2i_template.md**: 通义万相 T2I 客户端的提示词模板
- **google_genai_template.md**: Google GenAI 客户端的提示词模板

### MCP Prompt Skills

- **image_prompt_optimization.md**: 图像生成提示词优化
- **video_generation.md**: 视频生成提示词
- **image_style_description.md**: 图像风格描述
- **negative_prompt_generation.md**: 负面提示词生成
- **batch_image_planning.md**: 批量图像生成计划
- **xiaohongshu_image_prompt.md**: 小红书风格图片生成提示词

## 使用方式

Skills 通过 `SkillManager` 类进行管理和加载：

```python
from image_video_mcp.skills import SkillManager

# 初始化技能管理器
skill_manager = SkillManager()

# 获取技能内容
content = skill_manager.get_skill("z_images_system_prompt")

# 格式化技能内容（支持参数替换）
formatted = skill_manager.format_skill(
    "z_images_user_prompt",
    full_content="测试内容",
    style="真实"
)
```

## 添加新 Skill

1. 在 `skills/` 目录创建新的 `.md` 文件
2. 按照格式要求编写内容
3. 支持 `{参数名}` 格式的参数化模板
4. 重启服务后自动加载

## 注意事项

- 所有 Skills 文件必须使用 UTF-8 编码
- 参数名使用 `{参数名}` 格式，支持 Python `str.format()` 语法
- 技能名称（`# 标题`）应该清晰描述技能用途
