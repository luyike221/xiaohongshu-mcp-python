"""大纲生成服务"""
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger

from ..clients.text_client import get_text_chat_client
from ..config import model_config


class OutlineService:
    """大纲生成服务类"""

    def __init__(self, provider_config: Optional[Dict[str, Any]] = None):
        """
        初始化大纲生成服务

        Args:
            provider_config: 服务商配置字典，如果为 None 则使用默认配置
        """
        logger.debug("初始化 OutlineService...")
        self.provider_config = provider_config or self._get_default_config()
        self.client = self._get_client()
        self.title_content_tags_prompt_template = self._load_title_content_tags_prompt_template()
        logger.info(f"OutlineService 初始化完成，使用服务商: {self.provider_config.get('type', 'google_gemini')}")

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
                "1. 设置环境变量 GEMINI_API_KEY 或 OPENAI_API_KEY\n"
                "2. 或在调用时传入 provider_config 参数"
            )

        logger.info(f"使用文本服务商: {self.provider_config.get('type', 'google_gemini')}")
        return get_text_chat_client(self.provider_config)

    def _load_title_content_tags_prompt_template(self) -> str:
        """加载标题正文标签生成提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "title_content_tags_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"标题正文标签生成提示词模板文件不存在: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _generate_title_content_tags(self, topic: str, max_retries: int = 5) -> Dict[str, Any]:
        """
        使用LLM根据主题直接生成标题、正文和标签（带重试和长度验证机制）
        
        Args:
            topic: 用户主题
            max_retries: 最大重试次数（如果超出长度限制会重新生成）
            
        Returns:
            包含 title、content、tags 的字典
        """
        import json
        
        # 从配置中获取模型参数
        model = self.provider_config.get('model', 'gemini-2.0-flash-exp')
        temperature = self.provider_config.get('temperature', 0.3)
        max_output_tokens = self.provider_config.get('max_output_tokens', 2000)
        
        # 长度限制
        MAX_TITLE_LENGTH = 20
        MAX_CONTENT_LENGTH = 1000
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"使用LLM生成标题、正文和标签（尝试 {attempt + 1}/{max_retries}）...")
                
                # 构建提示词（使用replace避免topic中的{}被format解析）
                prompt = self.title_content_tags_prompt_template.replace(
                    "{topic}", topic
                )
                
                # 如果不是第一次尝试，在提示词中强调长度限制
                if attempt > 0:
                    prompt += f"\n\n**重要提醒**：标题必须严格控制在{MAX_TITLE_LENGTH}字符以内，正文必须严格控制在{MAX_CONTENT_LENGTH}字符以内。"
                
                generated_text = self.client.generate_text(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens
                )
                
                # 立即打印生成文本（使用error级别确保显示）
                logger.error(f"[DEBUG-生成文本-立即打印] 长度: {len(generated_text)} 字符")
                logger.error(f"[DEBUG-生成文本-立即打印] 内容: {generated_text}")
                import sys
                sys.stdout.flush()
                # 清理文本，去掉可能存在的代码块标记
                json_text = generated_text.strip()
                
                # 去掉所有可能的代码块标记
                # 去掉 ```json 或 ``` 标记
                json_text = re.sub(r'^```json\s*', '', json_text, flags=re.MULTILINE)
                json_text = re.sub(r'^```\s*', '', json_text, flags=re.MULTILINE)
                json_text = re.sub(r'\s*```$', '', json_text, flags=re.MULTILINE)
                json_text = json_text.strip()
                
                # 尝试找到JSON对象的开始和结束位置
                if not json_text.startswith('{'):
                    # 查找第一个 {
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
                
                # 确保tags是列表
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in re.split(r'[，,、\s]+', tags) if tag.strip()]
                elif not isinstance(tags, list):
                    tags = []
                
                # 验证结果
                if not title and not content:
                    raise ValueError("生成的标题和正文都为空")
                
                # 验证长度限制
                title_length = len(title)
                content_length = len(content)
                
                if title_length > MAX_TITLE_LENGTH or content_length > MAX_CONTENT_LENGTH:
                    logger.warning(
                        f"生成内容超出限制（尝试 {attempt + 1}/{max_retries}）- "
                        f"标题: {title_length}/{MAX_TITLE_LENGTH}, 正文: {content_length}/{MAX_CONTENT_LENGTH}，"
                        f"将重新生成..."
                    )
                    if attempt < max_retries - 1:
                        # 继续下一次循环，重新生成
                        continue
                    else:
                        # 最后一次仍然超出限制，直接报错
                        error_msg = (
                            f"生成内容超出限制（已重试{max_retries}次）- "
                            f"标题: {title_length}/{MAX_TITLE_LENGTH}字符, "
                            f"正文: {content_length}/{MAX_CONTENT_LENGTH}字符。"
                            f"请检查提示词或调整模型参数。"
                        )
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                
                logger.info(f"LLM生成成功（尝试 {attempt + 1}/{max_retries}）- 标题: {len(title)}字符, 正文: {len(content)}字符, 标签: {len(tags)}个")
                
                return {
                    "title": title,
                    "content": content,
                    "tags": tags
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.error(f"[DEBUG-JSON解析失败] JSON解析失败（尝试 {attempt + 1}/{max_retries}）: {e}")
                if 'generated_text' in locals():
                    logger.error(f"[DEBUG-JSON解析失败-生成文本] 长度: {len(generated_text)} 字符")
                    logger.error(f"[DEBUG-JSON解析失败-生成文本] 内容: {generated_text}")
                    logger.error(f"[DEBUG-JSON解析失败-清理后文本] 内容: {json_text if 'json_text' in locals() else 'N/A'}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # 短暂延迟后重试
                    continue
            
            except Exception as e:
                last_error = e
                logger.error(f"[DEBUG-通用异常] 生成标题、正文和标签时发生异常（尝试 {attempt + 1}/{max_retries}）: {e}")
                logger.error(f"[DEBUG-通用异常] 异常类型: {type(e).__name__}")
                import traceback
                logger.error(f"[DEBUG-通用异常] 异常堆栈: {traceback.format_exc()}")
                if 'generated_text' in locals():
                    logger.error(f"[DEBUG-通用异常-生成文本] 长度: {len(generated_text)} 字符")
                    logger.error(f"[DEBUG-通用异常-生成文本] 内容: {generated_text}")
                else:
                    logger.error(f"[DEBUG-通用异常] generated_text 变量不存在")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
        
        # 所有重试都失败
        logger.error(f"使用LLM生成标题、正文和标签失败（已重试{max_retries}次）: {last_error}")
        raise Exception(f"生成标题、正文和标签失败（已重试{max_retries}次）: {last_error}")

    def generate_outline(
        self,
        topic: str
    ) -> Dict[str, Any]:
        """
        生成小红书内容（标题、正文、标签）

        Args:
            topic: 主题

        Returns:
            包含标题、正文、标签的字典
        """
        try:
            logger.info(f"开始生成内容: topic={topic[:50]}...")
            
            # 直接使用LLM生成标题、正文和标签
            extracted = self._generate_title_content_tags(topic)
            
            title = extracted.get("title", "")
            content = extracted.get("content", "")
            tags = extracted.get("tags", [])
            
            logger.info(f"生成完成 - 标题: {title[:30]}..., 正文长度: {len(content)}, 标签数: {len(tags)}")
            
            return {
                "success": True,
                "title": title,
                "content": content,
                "tags": tags
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"大纲生成失败: {error_msg}")

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
                    f"大纲生成失败。\n"
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

