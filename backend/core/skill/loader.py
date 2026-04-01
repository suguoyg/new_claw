import os
import yaml
from pathlib import Path
from typing import List, Optional

from utils.config import get_skill_path, load_config

class SkillLoader:
    """
    Skill Loader - scans and loads skills from filesystem
    """

    def __init__(self):
        self.loaded_skills = {}

    def scan_skills(self) -> List[dict]:
        """Scan skills directory for available skills"""
        config = load_config()
        skills_dir = Path(config.directories.skills).expanduser()

        if not skills_dir.exists():
            return []

        skills = []
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        with open(skill_md, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Parse YAML frontmatter
                        metadata = self._parse_frontmatter(content)

                        skills.append({
                            "name": skill_dir.name,
                            "description": metadata.get("description", ""),
                            "trigger": metadata.get("trigger", ""),
                            "path": str(skill_dir),
                            "status": "active"
                        })
                    except Exception as e:
                        print(f"Error loading skill {skill_dir.name}: {e}")

        return skills

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from content"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 2:
                try:
                    return yaml.safe_load(parts[1]) or {}
                except:
                    pass
        return {}

    def load_all(self) -> dict:
        """Load all skills from disk"""
        skills = self.scan_skills()
        for skill in skills:
            self.loaded_skills[skill["name"]] = skill
        return self.loaded_skills

    def get_skill_path(self, skill_name: str) -> Optional[Path]:
        """Get skill directory path"""
        return get_skill_path(skill_name)

    def skill_exists(self, skill_name: str) -> bool:
        """Check if skill exists"""
        return get_skill_path(skill_name).exists()


# Global skill loader instance
loader = SkillLoader()
