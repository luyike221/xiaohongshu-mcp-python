"""LLM服务 - 生成脚本和关键词"""
import json
import re
from typing import List
from loguru import logger
from openai import OpenAI, AzureOpenAI

from ..config import settings


class LLMService:
    """LLM服务，用于生成视频脚本和搜索关键词"""
    
    def __init__(self):
        self.client = self._create_client()
    
    def _create_client(self):
        """创建LLM客户端"""
        provider = settings.llm_provider.lower()
        
        if provider == "openai":
            api_key = settings.openai_api_key
            base_url = settings.openai_base_url or "https://api.openai.com/v1"
            model_name = settings.openai_model_name
            if not api_key:
                raise ValueError("OpenAI API key is not set")
            return OpenAI(api_key=api_key, base_url=base_url)
        
        elif provider == "moonshot":
            api_key = settings.moonshot_api_key
            base_url = "https://api.moonshot.cn/v1"
            model_name = settings.moonshot_model_name
            if not api_key:
                raise ValueError("Moonshot API key is not set")
            return OpenAI(api_key=api_key, base_url=base_url)
        
        elif provider == "deepseek":
            api_key = settings.deepseek_api_key
            base_url = settings.deepseek_base_url
            model_name = settings.deepseek_model_name
            if not api_key:
                raise ValueError("DeepSeek API key is not set")
            return OpenAI(api_key=api_key, base_url=base_url)
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def generate_script(
        self,
        video_subject: str,
        language: str = "",
        paragraph_number: int = 1
    ) -> str:
        """
        生成视频脚本
        
        Args:
            video_subject: 视频主题
            language: 语言（可选）
            paragraph_number: 段落数量
            
        Returns:
            生成的视频脚本
        """
        prompt = f"""
# Role: Video Script Generator

## Goals:
Generate a script for a video, depending on the subject of the video.

## Constrains:
1. the script is to be returned as a string with the specified number of paragraphs.
2. do not under any circumstance reference this prompt in your response.
3. get straight to the point, don't start with unnecessary things like, "welcome to this video".
4. you must not include any type of markdown or formatting in the script, never use a title.
5. only return the raw content of the script.
6. do not include "voiceover", "narrator" or similar indicators of what should be spoken at the beginning of each paragraph or line.
7. you must not mention the prompt, or anything about the script itself. also, never talk about the amount of paragraphs or lines. just write the script.
8. respond in the same language as the video subject.

# Initialization:
- video subject: {video_subject}
- number of paragraphs: {paragraph_number}
""".strip()
        
        if language:
            prompt += f"\n- language: {language}"
        
        logger.info(f"Generating script for subject: {video_subject}")
        
        try:
            # 根据provider选择模型名称
            if settings.llm_provider == "openai":
                model_name = settings.openai_model_name
            elif settings.llm_provider == "moonshot":
                model_name = settings.moonshot_model_name
            elif settings.llm_provider == "deepseek":
                model_name = settings.deepseek_model_name
            else:
                model_name = settings.openai_model_name
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content
            
            # 清理脚本内容
            content = self._format_script(content)
            
            logger.success(f"Script generated successfully, length: {len(content)}")
            return content.strip()
        
        except Exception as e:
            logger.error(f"Failed to generate script: {e}")
            raise
    
    def _format_script(self, response: str) -> str:
        """格式化脚本内容"""
        # 移除星号、井号
        response = response.replace("*", "")
        response = response.replace("#", "")
        
        # 移除markdown语法
        response = re.sub(r"\[.*?\]", "", response)
        response = re.sub(r"\(.*?\)", "", response)
        
        # 按段落分割
        paragraphs = response.split("\n\n")
        
        # 合并段落
        return "\n\n".join(paragraphs)
    
    def generate_terms(
        self,
        video_subject: str,
        video_script: str,
        amount: int = 5
    ) -> List[str]:
        """
        生成搜索关键词
        
        Args:
            video_subject: 视频主题
            video_script: 视频脚本
            amount: 关键词数量
            
        Returns:
            关键词列表（英文）
        """
        prompt = f"""
# Role: Video Search Terms Generator

## Goals:
Generate {amount} search terms for stock videos, depending on the subject of a video.

## Constrains:
1. the search terms are to be returned as a json-array of strings.
2. each search term should consist of 1-3 words, always add the main subject of the video.
3. you must only return the json-array of strings. you must not return anything else. you must not return the script.
4. the search terms must be related to the subject of the video.
5. reply with english search terms only.

## Output Example:
["search term 1", "search term 2", "search term 3","search term 4","search term 5"]

## Context:
### Video Subject
{video_subject}

### Video Script
{video_script}

Please note that you must use English for generating video search terms; Chinese is not accepted.
""".strip()
        
        logger.info(f"Generating terms for subject: {video_subject}")
        
        try:
            # 根据provider选择模型名称
            if settings.llm_provider == "openai":
                model_name = settings.openai_model_name
            elif settings.llm_provider == "moonshot":
                model_name = settings.moonshot_model_name
            elif settings.llm_provider == "deepseek":
                model_name = settings.deepseek_model_name
            else:
                model_name = settings.openai_model_name
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                search_terms = json.loads(content)
                if isinstance(search_terms, list) and all(isinstance(term, str) for term in search_terms):
                    logger.success(f"Terms generated successfully: {search_terms}")
                    return search_terms
            except json.JSONDecodeError:
                # 尝试从文本中提取JSON数组
                match = re.search(r"\[.*?\]", content, re.DOTALL)
                if match:
                    search_terms = json.loads(match.group())
                    if isinstance(search_terms, list) and all(isinstance(term, str) for term in search_terms):
                        logger.success(f"Terms generated successfully: {search_terms}")
                        return search_terms
            
            logger.warning(f"Failed to parse terms from response: {content}")
            return []
        
        except Exception as e:
            logger.error(f"Failed to generate terms: {e}")
            return []

