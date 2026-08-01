import re
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    name: str
    description: str
    command: str
    version: str = "1.0.0"
    author: str = "Antigravity Team"
    path: Optional[str] = None
    body_content: str = ""

    def __str__(self) -> str:
        return f"<Skill name={self.name} command={self.command} version={self.version}>"


class SkillParser:
    """
    Parses SKILL.md definition files cleanly and safely without executing code.
    Reads YAML-style metadata header or markdown sections.
    """

    @classmethod
    def parse_skill_file(cls, file_path: Path) -> Optional[SkillMetadata]:
        if not file_path.exists() or file_path.suffix.lower() != ".md":
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return None

        meta_dict = {}
        body = content

        # Check for YAML frontmatter between --- ... ---
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if frontmatter_match:
            yaml_block = frontmatter_match.group(1)
            body = frontmatter_match.group(2)
            for line in yaml_block.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta_dict[key.strip().lower()] = val.strip().strip("\"'")

        # Fallback metadata extraction from markdown header if not present
        if "name" not in meta_dict:
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            meta_dict["name"] = title_match.group(1).strip() if title_match else file_path.parent.name

        if "description" not in meta_dict:
            meta_dict["description"] = f"Skill loaded from {file_path.name}"

        if "command" not in meta_dict:
            meta_dict["command"] = meta_dict["name"].lower().replace(" ", "-")

        meta_dict["path"] = str(file_path)
        meta_dict["body_content"] = body.strip()

        try:
            return SkillMetadata(**meta_dict)
        except Exception:
            return None
