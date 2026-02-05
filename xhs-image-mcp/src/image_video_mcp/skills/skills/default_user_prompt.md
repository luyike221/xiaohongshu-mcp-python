# default_user_prompt
> 默认的用户提示词模板（用于非 Z-Images 客户端）

请根据以下完整内容文本，生成适合图片生成模型的提示词（客户端类型：{client_type}）。

完整内容：
{full_content}

{style_section}

请生成适合的图片提示词，返回 JSON 格式：
{{
    "pages": [
        {{
            "index": 0,
            "type": "cover",
            "content": "图片提示词内容"
        }}
    ]
}}
