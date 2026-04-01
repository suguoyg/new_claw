import yaml
from typing import Dict, Optional, List
from pathlib import Path

from utils.config import get_skill_path

class SkillManager:
    """
    Skill Manager - manages skill loading and execution
    """

    def __init__(self):
        self.skills: Dict[str, dict] = {}

    def parse_skill_md(self, content: str) -> dict:
        """Parse SKILL.md content"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    instructions = parts[2].strip()
                    return {
                        "name": metadata.get("name", ""),
                        "description": metadata.get("description", ""),
                        "trigger": metadata.get("trigger", ""),
                        "instructions": instructions
                    }
                except Exception as e:
                    pass
        return {
            "name": "",
            "description": "",
            "trigger": "",
            "instructions": content
        }

    def load_skill(self, skill_name: str) -> Optional[dict]:
        """Load skill from disk"""
        skill_path = get_skill_path(skill_name)
        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            return None

        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()

        parsed = self.parse_skill_md(content)

        skill_data = {
            "name": skill_name,
            "description": parsed.get("description", ""),
            "trigger": parsed.get("trigger", ""),
            "instructions": parsed.get("instructions", ""),
            "content": content,
            "path": str(skill_path)
        }

        self.skills[skill_name] = skill_data
        return skill_data

    def get_skill(self, skill_name: str) -> Optional[dict]:
        """Get skill (from cache or load)"""
        if skill_name in self.skills:
            return self.skills[skill_name]
        return self.load_skill(skill_name)

    def reload_skill(self, skill_name: str) -> Optional[dict]:
        """Reload skill from disk"""
        if skill_name in self.skills:
            del self.skills[skill_name]
        return self.load_skill(skill_name)

    def list_skills(self) -> List[dict]:
        """List all loaded skills"""
        return [
            {
                "name": name,
                "description": skill.get("description", ""),
                "trigger": skill.get("trigger", "")
            }
            for name, skill in self.skills.items()
        ]

    def get_skill_prompt(self, skill_name: str) -> Optional[str]:
        """Get skill formatted prompt for LLM"""
        skill = self.get_skill(skill_name)
        if not skill:
            return None

        # Format: # Skill: {name}\ndescription: {description}\n\n{instructions}
        return f"""# Skill: {skill['name']}
description: {skill['description']}

{skill['instructions']}"""

    def match_trigger(self, query: str) -> Optional[str]:
        """Match query against skill triggers"""
        query_lower = query.lower()
        for name, skill in self.skills.items():
            trigger = skill.get("trigger", "")
            if trigger and trigger.lower() in query_lower:
                return name
        return None


# Global skill manager instance
manager = SkillManager()
