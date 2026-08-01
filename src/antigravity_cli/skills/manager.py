from pathlib import Path
from typing import Dict, List, Optional
from antigravity_cli.skills.parser import SkillParser, SkillMetadata


class SkillManager:
    """
    Scans, indexes, and manages built-in and user-defined Antigravity skills.
    """

    def __init__(self, user_skills_dir: Path, builtin_skills_dir: Optional[Path] = None):
        self.user_skills_dir = Path(user_skills_dir)
        if builtin_skills_dir:
            self.builtin_skills_dir = Path(builtin_skills_dir)
        else:
            self.builtin_skills_dir = Path(__file__).parent / "builtin"

        self.skills: Dict[str, SkillMetadata] = {}
        self.reload_skills()

    def reload_skills(self) -> None:
        self.skills.clear()
        
        # 1. Load built-in skills
        if self.builtin_skills_dir.exists():
            for item in self.builtin_skills_dir.glob("**/SKILL.md"):
                meta = SkillParser.parse_skill_file(item)
                if meta:
                    self.skills[meta.name.lower()] = meta

        # 2. Load user custom skills (user skills take precedence if duplicate)
        if self.user_skills_dir.exists():
            for item in self.user_skills_dir.glob("**/SKILL.md"):
                meta = SkillParser.parse_skill_file(item)
                if meta:
                    self.skills[meta.name.lower()] = meta

    def list_skills(self) -> List[SkillMetadata]:
        return sorted(list(self.skills.values()), key=lambda x: x.name)

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        name_clean = name.lower().strip()
        return self.skills.get(name_clean)

    def execute_skill_action(self, name: str) -> str:
        skill = self.get_skill(name)
        if not skill:
            return f"Error: Skill '{name}' not found."
        
        res = [
            f"=== SKILL: {skill.name} (v{skill.version}) ===",
            f"Description: {skill.description}",
            f"Command: /{skill.command}",
            f"Source: {skill.path}",
            "\n--- Skill Instructions ---",
            skill.body_content
        ]
        return "\n".join(res)
