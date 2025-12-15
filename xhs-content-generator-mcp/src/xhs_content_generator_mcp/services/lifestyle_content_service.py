"""生活化内容生成服务"""
import json
from math import log
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from loguru import logger

from ..clients.text_client import get_text_chat_client
from ..config import model_config


class LifestyleContentService:
    """生活化内容生成服务类"""

    def __init__(self, provider_config: Optional[Dict[str, Any]] = None):
        """
        初始化生活化内容生成服务

        Args:
            provider_config: 服务商配置字典，如果为 None 则使用默认配置
        """
        logger.debug("初始化 LifestyleContentService...")
        self.provider_config = provider_config or self._get_default_config()
        self.client = self._get_client()
        self.content_prompt_template = self._load_content_prompt_template()
        logger.info(f"LifestyleContentService 初始化完成，使用服务商: {self.provider_config.get('type', 'alibaba_bailian')}")

    def _get_default_config(self) -> dict:
        """获取默认配置（使用阿里百炼）"""
        try:
            return model_config.get_provider_config(provider_type='alibaba_bailian')
        except ValueError:
            # 如果配置未设置，尝试使用 openai_compatible
            try:
                return model_config.get_provider_config(provider_type='openai_compatible')
            except ValueError:
                # 如果配置未设置，返回空配置（会在 _get_client 中报错）
                return {
                    'type': 'alibaba_bailian',
                    'api_key': '',
                }

    def _get_client(self):
        """根据配置获取客户端"""
        if not self.provider_config.get('api_key'):
            raise ValueError(
                "API Key 未配置。\n"
                "解决方案：\n"
                "1. 设置环境变量 DASHSCOPE_API_KEY 或 OPENAI_API_KEY\n"
                "2. 或在调用时传入 provider_config 参数"
            )

        logger.info(f"使用文本服务商: {self.provider_config.get('type', 'alibaba_bailian')}")
        return get_text_chat_client(self.provider_config)

    def _load_content_prompt_template(self) -> str:
        """加载内容生成提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "lifestyle_content_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"提示词模板文件不存在: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _generate_content(
        self,
        profession: str,
        age: int,
        gender: str,
        personality: str,
        mood: str,
        scene: Optional[str] = None,
        content_type: Optional[str] = None,
        topic_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成生活化内容
        
        Args:
            profession: 职业
            age: 年龄
            gender: 性别
            personality: 性格特点
            mood: 情绪倾向
            scene: 生活场景（可选）
            content_type: 内容类型（可选）
            topic_hint: 话题提示（可选）
            
        Returns:
            包含 title、content、tags 的字典
        """
        import json
        
        # 从配置中获取模型参数
        model = self.provider_config.get('model', 'qwen-plus')
        temperature = self.provider_config.get('temperature', 0.8)  # 生活化内容使用更高的温度
        max_output_tokens = self.provider_config.get('max_output_tokens', 2000)
        
        # 构建话题提示
        topic_desc = ""
        if topic_hint:
            topic_desc = f"\n话题提示：{topic_hint}"
        
        # 构建提示词（使用 replace 而不是 format，避免 JSON 示例中的大括号被误解析）
        prompt = self.content_prompt_template.replace("{profession}", str(profession))
        prompt = prompt.replace("{age}", str(age))
        prompt = prompt.replace("{gender}", str(gender))
        prompt = prompt.replace("{personality}", str(personality))
        prompt = prompt.replace("{mood}", str(mood))
        prompt = prompt.replace("{scene}", str(scene or "日常生活"))
        prompt = prompt.replace("{content_type}", str(content_type or "生活分享"))
        prompt = prompt.replace("{topic_hint}", topic_desc)
        
        # 最多重试3次
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"生成生活化内容（尝试 {attempt + 1}/{max_retries}）...")
                
                generated_text = self.client.generate_text(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens
                )
                
                logger.debug(f"API 返回文本长度: {len(generated_text)} 字符")
                
                # 清理文本，去掉可能存在的代码块标记
                json_text = generated_text.strip()
                
                # 去掉所有可能的代码块标记
                json_text = re.sub(r'^```json\s*', '', json_text, flags=re.MULTILINE)
                json_text = re.sub(r'^```\s*', '', json_text, flags=re.MULTILINE)
                json_text = re.sub(r'\s*```$', '', json_text, flags=re.MULTILINE)
                json_text = json_text.strip()
                
                # 尝试找到JSON对象的开始和结束位置
                if not json_text.startswith('{'):
                    brace_start = json_text.find('{')
                    if brace_start != -1:
                        json_text = json_text[brace_start:]
                
                # 尝试找到匹配的结束 }
                if json_text.startswith('{'):
                    brace_count = 0
                    json_end_pos = -1
                    for i, char in enumerate(json_text):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end_pos = i + 1
                                break
                    
                    if json_end_pos > 0:
                        json_text = json_text[:json_end_pos]
                
                # 解析JSON
                result = json.loads(json_text)
                title = result.get("title", "").strip()
                content = result.get("content", "").strip()
                tags = result.get("tags", [])
                pages = result.get("pages", [])
                
                # 确保tags是列表
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in re.split(r'[，,、\s]+', tags) if tag.strip()]
                elif not isinstance(tags, list):
                    tags = []
                
                # 确保pages是列表
                if not isinstance(pages, list):
                    pages = []
                
                # 验证结果
                if not title and not content:
                    raise ValueError("生成的标题和正文都为空")
                
                # 验证pages格式
                if not pages:
                    raise ValueError("未生成pages数据")
                
                logger.info(f"内容生成成功（尝试 {attempt + 1}/{max_retries}）- 标题: {len(title)}字符, 正文: {len(content)}字符, 标签: {len(tags)}个, 页数: {len(pages)}个")
                
                return {
                    "title": title,
                    "content": content,
                    "tags": tags,
                    "pages": pages
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.error(f"JSON解析失败（尝试 {attempt + 1}/{max_retries}）: {e}")
                if 'generated_text' in locals():
                    logger.error(f"生成文本内容: {generated_text[:500]}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
            
            except Exception as e:
                last_error = e
                logger.error(f"生成内容时发生异常（尝试 {attempt + 1}/{max_retries}）: {e}")
                import traceback
                logger.error(traceback.format_exc())
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
        
        # 所有重试都失败
        logger.error(f"生成内容失败（已重试{max_retries}次）: {last_error}")
        raise Exception(f"生成内容失败（已重试{max_retries}次）: {last_error}")

    def generate_lifestyle_content(
        self,
        profession: str,
        age: int,
        gender: str,
        personality: str,
        mood: str,
        scene: Optional[str] = None,
        content_type: Optional[str] = None,
        topic_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成生活化内容（包含图片提示词）

        Args:
            profession: 职业，例如"程序员"、"设计师"、"学生"、"自由职业者"
            age: 年龄，例如 25、30
            gender: 性别，例如"男"、"女"、"不指定"
            personality: 性格特点，例如"活泼开朗"、"内敛文艺"、"幽默风趣"、"温柔细腻"
            mood: 情绪倾向，例如"开心"、"感慨"、"治愈"、"吐槽"
            scene: 生活场景（可选），例如"周末日常"、"工作间隙"、"深夜emo"、"旅行途中"
            content_type: 内容类型（可选），例如"日常分享"、"心情记录"、"生活感悟"、"好物推荐"
            topic_hint: 话题提示（可选），例如"今天天气真好"、"工作累了"

        Returns:
            包含生成结果的字典
        """
        try:
            logger.info(f"开始生成生活化内容: {profession}, {age}岁, {gender}, {personality}, {mood}")
            
            # 一次性生成完整数据结构（包含 pages 和 image_prompts）
            content_result = self._generate_content(
                profession=profession,
                age=age,
                gender=gender,
                personality=personality,
                mood=mood,
                scene=scene,
                content_type=content_type,
                topic_hint=topic_hint,
            )
            
            title = content_result.get("title", "")
            content = content_result.get("content", "")
            tags = content_result.get("tags", [])
            pages = content_result.get("pages", [])
            
            # 验证字符数限制
            MAX_TITLE_LENGTH = 20
            MAX_CONTENT_LENGTH = 100
            
            if len(title) > MAX_TITLE_LENGTH:
                logger.warning(f"标题超过限制: {len(title)}/{MAX_TITLE_LENGTH}，进行截断")
                title = title[:MAX_TITLE_LENGTH]
                # 更新封面页的标题
                if pages and pages[0].get("type") == "cover":
                    cover_content = pages[0].get("content", "")
                    cover_content = re.sub(r'标题：[^\n]+', f'标题：{title}', cover_content)
                    pages[0]["content"] = cover_content
            
            # 正文不截断，只记录日志
            if len(content) > MAX_CONTENT_LENGTH:
                logger.info(f"正文长度: {len(content)}字符（限制: {MAX_CONTENT_LENGTH}字符，不截断）")
            
            # 构建人物设定摘要
            persona_context = f"{age}岁{gender}{profession}，性格{personality}，心情{mood}"
            if scene:
                persona_context += f"，场景{scene}"
            if content_type:
                persona_context += f"，内容类型{content_type}"
            
            logger.info(f"生活化内容生成完成 - 标题: {len(title)}字符, 正文: {len(content)}字符, 标签: {len(tags)}个, 页数: {len(pages)}个")
            # 对齐 outline_service 的返回格式
            return {
                "success": True,
                "pages": pages,
                "title": title,
                "content": content,
                "tags": tags,
                "persona_context": persona_context
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"生活化内容生成失败: {error_msg}")
            import traceback
            logger.error(traceback.format_exc())

            # 根据错误类型提供更详细的错误信息
            if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower() or "401" in error_msg:
                detailed_error = (
                    f"API 认证失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. API Key 无效或已过期\n"
                    "2. API Key 没有访问该模型的权限\n"
                    "解决方案：检查并更新 API Key"
                )
            elif "model" in error_msg.lower() or "404" in error_msg:
                detailed_error = (
                    f"模型访问失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. 模型名称不正确\n"
                    "2. 没有访问该模型的权限\n"
                    "解决方案：检查模型名称配置"
                )
            elif "timeout" in error_msg.lower() or "连接" in error_msg:
                detailed_error = (
                    f"网络连接失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. 网络连接不稳定\n"
                    "2. API 服务暂时不可用\n"
                    "3. Base URL 配置错误\n"
                    "解决方案：检查网络连接，稍后重试"
                )
            elif "rate" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                detailed_error = (
                    f"API 配额限制。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. API 调用次数超限\n"
                    "2. 账户配额用尽\n"
                    "解决方案：等待配额重置，或升级 API 套餐"
                )
            else:
                detailed_error = (
                    f"生活化内容生成失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. Text API 配置错误或密钥无效\n"
                    "2. 网络连接问题\n"
                    "3. 模型无法访问或不存在\n"
                    "建议：检查配置和网络连接"
                )

            return {
                "success": False,
                "error": detailed_error
            }

