"""
Skills Manager - 核心模块
提供 Skills 的加载、管理和格式化功能
"""

from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger


class SkillManager:
    """技能管理器 - 负责加载和管理所有技能"""
    
    def __init__(self, skills_dir: Optional[str] = None):
        """
        初始化技能管理器
        
        Args:
            skills_dir: 技能文件目录路径，如果为 None 则使用默认路径
        """
        if skills_dir is None:
            # 默认使用相对于当前文件的 skills 目录
            current_file = Path(__file__).resolve()
            skills_dir = current_file.parent / "skills"
        
        self.skills_dir = Path(skills_dir)
        self.skills: List[Dict[str, str]] = []
        self._load_all_skills()
    
    def _load_all_skills(self):
        """从 markdown 文件加载所有技能"""
        if not self.skills_dir.exists():
            logger.warning(f"⚠️  技能目录不存在: {self.skills_dir}")
            return
        
        for skill_file in self.skills_dir.glob("*.md"):
            skill = self._parse_skill_file(skill_file)
            if skill:
                self.skills.append(skill)
        
        logger.info(f"✅ 已加载 {len(self.skills)} 个技能")
    
    def _parse_skill_file(self, file_path: Path) -> Optional[Dict[str, str]]:
        """
        解析技能文件（markdown 格式）
        
        格式要求：
        # Skill Name
        > Description
        
        Content...
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.strip().split('\n')
            
            # 解析名称（第一行 # 标题）
            name = file_path.stem  # 默认使用文件名
            description = ""
            skill_content = []
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('# '):
                    name = line[2:].strip()
                elif line.startswith('> '):
                    description = line[2:].strip()
                elif line:  # 非空行作为内容
                    skill_content.append(lines[i])
                i += 1
            
            return {
                "name": name,
                "description": description or f"{name}相关知识",
                "content": '\n'.join(skill_content),
                "file_stem": file_path.stem  # 保存文件名（不含扩展名）
            }
        except Exception as e:
            logger.error(f"❌ 解析技能文件失败 {file_path}: {e}")
            return None
    
    def get_skill(self, skill_name: str) -> Optional[str]:
        """
        获取指定技能的内容
        
        Args:
            skill_name: 技能名称（文件名或 # 标题中的名称）
        
        Returns:
            技能内容字符串，如果未找到则返回 None
        """
        # 先按名称匹配
        for skill in self.skills:
            if skill["name"] == skill_name:
                return skill["content"]
        
        # 再按文件名匹配（不包含扩展名）
        for skill in self.skills:
            if skill.get("file_stem") == skill_name:
                return skill["content"]
        
        return None
    
    def format_skill(self, skill_name: str, **kwargs) -> Optional[str]:
        """
        格式化技能内容，支持参数替换
        
        Args:
            skill_name: 技能名称
            **kwargs: 用于替换模板中的参数
        
        Returns:
            格式化后的技能内容，如果未找到则返回 None
        
        Example:
            skill_manager.format_skill("user_prompt", full_content="测试", style="真实")
        """
        content = self.get_skill(skill_name)
        if content is None:
            return None
        
        if kwargs:
            try:
                return content.format(**kwargs)
            except KeyError as e:
                logger.warning(f"格式化技能 '{skill_name}' 时缺少参数: {e}")
                return content
            except Exception as e:
                logger.error(f"格式化技能 '{skill_name}' 时出错: {e}")
                return content
        
        return content
    
    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有可用技能（仅名称和描述）"""
        return [{"name": s["name"], "description": s["description"]} for s in self.skills]
    
    def has_skill(self, skill_name: str) -> bool:
        """检查技能是否存在"""
        return self.get_skill(skill_name) is not None
