"""大纲生成服务"""
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

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
        self.prompt_template = self._load_prompt_template()
        self.compress_prompt_template = self._load_compress_prompt_template()
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

    def _load_prompt_template(self) -> str:
        """加载提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "outline_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"提示词模板文件不存在: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def _load_compress_prompt_template(self) -> str:
        """加载压缩提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "compress_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"压缩提示词模板文件不存在: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def _load_title_content_tags_prompt_template(self) -> str:
        """加载标题正文标签生成提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "title_content_tags_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"标题正文标签生成提示词模板文件不存在: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_outline(self, outline_text: str) -> List[Dict[str, Any]]:
        """解析大纲文本为页面列表"""
        # 按 <page> 分割页面（兼容旧的 --- 分隔符）
        if '<page>' in outline_text:
            pages_raw = re.split(r'<page>', outline_text, flags=re.IGNORECASE)
        else:
            # 向后兼容：如果没有 <page> 则使用 ---
            pages_raw = outline_text.split("---")

        pages = []

        for index, page_text in enumerate(pages_raw):
            page_text = page_text.strip()
            if not page_text:
                continue

            page_type = "content"
            type_match = re.match(r"\[(\S+)\]", page_text)
            if type_match:
                type_cn = type_match.group(1)
                type_mapping = {
                    "封面": "cover",
                    "内容": "content",
                    "总结": "summary",
                }
                page_type = type_mapping.get(type_cn, "content")

            pages.append({
                "index": index,
                "type": page_type,
                "content": page_text
            })

        return pages
    
    def _generate_title_content_tags(self, outline_text: str) -> Dict[str, Any]:
        """
        使用LLM根据大纲生成标题、正文和标签（带重试机制）
        
        Args:
            outline_text: 完整的大纲文本
            
        Returns:
            包含 title、content、tags 的字典
        """
        import json
        
        # 从配置中获取模型参数
        model = self.provider_config.get('model', 'gemini-2.0-flash-exp')
        temperature = self.provider_config.get('temperature', 0.3)
        max_output_tokens = self.provider_config.get('max_output_tokens', 2000)
        
        # 最多重试3次
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"使用LLM生成标题、正文和标签（尝试 {attempt + 1}/{max_retries}）...")
                
                # 构建提示词（使用replace避免outline_text中的{}被format解析）
                prompt = self.title_content_tags_prompt_template.replace(
                    "{outline_text}", outline_text
                )
                
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
    
    def _compress_content(
        self,
        title: str,
        content: str,
        max_title_length: int = 20,
        max_content_length: int = 1000
    ) -> Dict[str, str]:
        """
        使用LLM压缩标题和正文内容
        
        Args:
            title: 原始标题
            content: 原始正文
            max_title_length: 标题最大长度
            max_content_length: 正文最大长度
            
        Returns:
            包含压缩后的 title 和 content 的字典
        """
        try:
            title_length = len(title)
            content_length = len(content)
            
            # 构建压缩提示词
            prompt = self.compress_prompt_template.format(
                title=title,
                content=content,
                max_title_length=max_title_length,
                max_content_length=max_content_length,
                title_length=title_length,
                content_length=content_length
            )
            
            # 从配置中获取模型参数
            model = self.provider_config.get('model', 'gemini-2.0-flash-exp')
            temperature = self.provider_config.get('temperature', 0.3)
            max_output_tokens = 1000  # 压缩任务输出较短，设置为1000
            
            logger.info(f"开始压缩内容 - 标题: {title_length}字符, 正文: {content_length}字符")
            compressed_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
            logger.info(f"压缩结果: {compressed_text}")
            # 解析压缩结果
            compressed_title = title
            compressed_content = content
            
            # 尝试多种格式解析
            # 格式1: 标题：xxx\n正文：xxx
            title_match = re.search(r'标题[：:]\s*(.+?)(?:\n\s*正文[：:]|$)', compressed_text, re.MULTILINE | re.DOTALL)
            if title_match:
                compressed_title = title_match.group(1).strip()
            
            # 格式2: 正文：xxx（可能在标题后面或单独出现）
            content_match = re.search(r'正文[：:]\s*(.+?)(?:\n*$)', compressed_text, re.MULTILINE | re.DOTALL)
            if content_match:
                compressed_content = content_match.group(1).strip()
            
            # 格式3: 如果只有标题行，尝试提取第一行作为标题
            if compressed_title == title and '标题' not in compressed_text.lower():
                # 可能LLM只返回了压缩后的标题，没有格式标记
                lines = compressed_text.strip().split('\n')
                if lines:
                    first_line = lines[0].strip()
                    # 如果第一行看起来像标题（长度合理且不包含"正文"）
                    if len(first_line) <= max_title_length * 2 and '正文' not in first_line:
                        compressed_title = first_line
                        # 剩余部分作为正文
                        if len(lines) > 1:
                            compressed_content = '\n'.join(lines[1:]).strip()
            
            # 如果标题仍然超过限制，只压缩标题
            if len(compressed_title) > max_title_length:
                # 只压缩标题，不压缩正文
                title_only_prompt = f"请将以下标题压缩到{max_title_length}字符以内，保持核心意思：\n{title}"
                try:
                    compressed_title_text = self.client.generate_text(
                        prompt=title_only_prompt,
                        model=model,
                        temperature=temperature,
                        max_output_tokens=500
                    )
                    compressed_title = compressed_title_text.strip()[:max_title_length]
                except:
                    compressed_title = title[:max_title_length]
            
            # 如果正文仍然超过限制，只压缩正文
            if len(compressed_content) > max_content_length:
                # 只压缩正文，不压缩标题
                content_only_prompt = f"请将以下正文压缩到{max_content_length}字符以内，保持核心信息和价值：\n{content}"
                try:
                    compressed_content_text = self.client.generate_text(
                        prompt=content_only_prompt,
                        model=model,
                        temperature=temperature,
                        max_output_tokens=1000
                    )
                    compressed_content = compressed_content_text.strip()[:max_content_length]
                except:
                    compressed_content = content[:max_content_length]
            
            logger.info(f"压缩完成 - 标题: {len(compressed_title)}字符, 正文: {len(compressed_content)}字符")
            
            return {
                "title": compressed_title,
                "content": compressed_content
            }
            
        except Exception as e:
            logger.error(f"压缩内容失败: {e}")
            raise

    def generate_outline(
        self,
        topic: str,
        images: Optional[List[bytes]] = None,
        image_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成大纲

        Args:
            topic: 主题
            images: 参考图片列表（可选，仅当文本模型支持图片时使用）
            image_description: 图片描述文本（可选，当使用 VL 模型分析图片后传入）

        Returns:
            包含大纲信息的字典
        """
        try:
            logger.info(f"开始生成大纲: topic={topic[:50]}..., images={len(images) if images else 0}, has_description={image_description is not None}")
            prompt = self.prompt_template.format(topic=topic)

            # 处理图片描述或图片
            if image_description:
                # 如果提供了图片描述（来自 VL 模型分析），添加到 prompt
                prompt += f"\n\n【参考图片分析结果】\n用户提供了参考图片，VL 模型分析结果如下：\n{image_description}\n\n请根据以上图片分析结果，在生成大纲时充分考虑图片的内容、风格和特点，使生成的内容与图片高度关联。"
                logger.debug("已将 VL 模型分析的图片描述添加到提示词")
            elif images and len(images) > 0:
                # 如果直接提供了图片（文本模型支持图片），添加到 prompt
                prompt += f"\n\n注意：用户提供了 {len(images)} 张参考图片，请在生成大纲时考虑这些图片的内容和风格。这些图片可能是产品图、个人照片或场景图，请根据图片内容来优化大纲，使生成的内容与图片相关联。"
                logger.debug(f"添加了 {len(images)} 张参考图片到提示词（直接传递）")

            # 从配置中获取模型参数
            model = self.provider_config.get('model', 'gemini-2.0-flash-exp')
            temperature = self.provider_config.get('temperature', 1.0)
            max_output_tokens = self.provider_config.get('max_output_tokens', 8000)

            logger.info(f"调用文本生成 API: model={model}, temperature={temperature}")

            outline_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                images=images  # 如果使用了 VL 模型，这里 images 为 None
            )

            logger.debug(f"API 返回文本长度: {len(outline_text)} 字符")
            logger.error(f"[DEBUG-生成文本-立即打印] 内容: {outline_text}")
            pages = self._parse_outline(outline_text)
            logger.info(f"大纲解析完成，共 {len(pages)} 页")
            
            # 使用LLM生成标题、正文和标签（替代原有的提取逻辑）
            extracted = self._generate_title_content_tags(outline_text)
            # 打印生成结果（使用error级别确保显示）
            logger.error(f"[DEBUG-生成结果] 标题、正文和标签生成完成: {extracted}")
            title = extracted.get("title", "")
            content = extracted.get("content", "")
            tags = extracted.get("tags", [])
            
            # 验证字符数限制并压缩
            MAX_TITLE_LENGTH = 20
            MAX_CONTENT_LENGTH = 1000
            title_length = len(title)
            content_length = len(content)
            
            need_compress = title_length > MAX_TITLE_LENGTH or content_length > MAX_CONTENT_LENGTH
            
            if need_compress:
                logger.info(f"内容超过限制 - 标题: {title_length}/{MAX_TITLE_LENGTH}, 正文: {content_length}/{MAX_CONTENT_LENGTH}，开始压缩...")
                
                # 最多重试3次
                max_retries = 3
                compressed_title = title
                compressed_content = content
                
                for attempt in range(max_retries):
                    try:
                        # 尝试压缩
                        compressed = self._compress_content(
                            title=compressed_title,
                            content=compressed_content,
                            max_title_length=MAX_TITLE_LENGTH,
                            max_content_length=MAX_CONTENT_LENGTH
                        )
                        
                        compressed_title = compressed.get("title", compressed_title)
                        compressed_content = compressed.get("content", compressed_content)
                        
                        # 验证压缩结果
                        new_title_length = len(compressed_title)
                        new_content_length = len(compressed_content)
                        
                        if new_title_length <= MAX_TITLE_LENGTH and new_content_length <= MAX_CONTENT_LENGTH:
                            logger.info(f"压缩成功 (尝试 {attempt + 1}/{max_retries}) - 标题: {new_title_length}, 正文: {new_content_length}")
                            title = compressed_title
                            content = compressed_content
                            break
                        else:
                            logger.warning(f"压缩后仍超过限制 (尝试 {attempt + 1}/{max_retries}) - 标题: {new_title_length}/{MAX_TITLE_LENGTH}, 正文: {new_content_length}/{MAX_CONTENT_LENGTH}")
                            if attempt == max_retries - 1:
                                # 第三次仍超过限制，直接截断
                                logger.warning(f"第 {max_retries} 次压缩后仍超过限制，直接截断")
                                if new_title_length > MAX_TITLE_LENGTH:
                                    compressed_title = compressed_title[:MAX_TITLE_LENGTH]
                                    logger.info(f"标题截断: {new_title_length} -> {len(compressed_title)} 字符")
                                if new_content_length > MAX_CONTENT_LENGTH:
                                    compressed_content = compressed_content[:MAX_CONTENT_LENGTH]
                                    logger.info(f"正文截断: {new_content_length} -> {len(compressed_content)} 字符")
                                title = compressed_title
                                content = compressed_content
                                break
                            # 继续重试
                            continue
                    
                    except Exception as e:
                        logger.error(f"压缩失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                        if attempt == max_retries - 1:
                            # 最后一次失败，直接截断
                            logger.warning("所有压缩尝试失败，使用截断方式")
                            if len(compressed_title) > MAX_TITLE_LENGTH:
                                compressed_title = compressed_title[:MAX_TITLE_LENGTH]
                                logger.info(f"标题截断: {len(compressed_title)} 字符")
                            if len(compressed_content) > MAX_CONTENT_LENGTH:
                                compressed_content = compressed_content[:MAX_CONTENT_LENGTH]
                                logger.info(f"正文截断: {len(compressed_content)} 字符")
                            title = compressed_title
                            content = compressed_content
                            break
                        continue
                
                # 更新最终结果
                title = compressed_title
                content = compressed_content
                logger.info(f"最终结果 - 标题: {len(title)}字符, 正文: {len(content)}字符")
            
            logger.info(f"提取结果 - 标题: {title[:30]}..., 正文长度: {len(content)}, 标签数: {len(tags)}")

            return {
                "success": True,
                "outline": outline_text,
                "pages": pages,
                "has_images": images is not None and len(images) > 0,
                # 新增：匹配发布接口的数据结构
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

