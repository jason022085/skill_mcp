import pytest
from pathlib import Path
from skill_mcp_server.skill.manager import SkillManager
from skill_mcp_server.skill.models import SkillInfo

def test_list_skill_files(skills_dir):
    manager = SkillManager(skill_dirs=[skills_dir])
    skills = manager.discover()
    assert "sample-skill" in skills
    skill = skills["sample-skill"]

    resources, scripts = manager.list_skill_files(skill)

    # resources should include assets/template.txt and references/doc.md
    assert any("assets/template.txt" in r for r in resources)
    assert any("references/doc.md" in r for r in resources)

    # scripts should include scripts/hello.py
    assert any("scripts/hello.py" in s for s in scripts)
