import pytest
from pathlib import Path
from antigravity_cli.skills.parser import SkillParser, SkillMetadata
from antigravity_cli.skills.manager import SkillManager


def test_parse_skill_file(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: custom-test\ndescription: Custom test skill\ncommand: test-cmd\nversion: 2.1.0\n---\n# Instructions\nTest body.",
        encoding="utf-8"
    )

    meta = SkillParser.parse_skill_file(skill_file)
    assert meta is not None
    assert meta.name == "custom-test"
    assert meta.description == "Custom test skill"
    assert meta.command == "test-cmd"
    assert meta.version == "2.1.0"
    assert "Test body" in meta.body_content


def test_skill_manager_discovery(tmp_path):
    user_skills = tmp_path / "user_skills"
    user_skills.mkdir()

    custom_dir = user_skills / "my-skill"
    custom_dir.mkdir()
    (custom_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: User custom skill\ncommand: my-skill\n---\nExecute custom logic.",
        encoding="utf-8"
    )

    sm = SkillManager(user_skills_dir=user_skills)
    skills = sm.list_skills()
    
    # Should discover built-in skills + custom skill
    assert len(skills) >= 5
    assert any(s.name.lower() == "deep-think" for s in skills)
    assert any(s.name.lower() == "my-skill" for s in skills)

    output = sm.execute_skill_action("my-skill")
    assert "Execute custom logic" in output
