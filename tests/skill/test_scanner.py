import pytest
from pathlib import Path
from skill_mcp_server.skill.scanner import SkillScanner

def test_is_excluded():
    scanner = SkillScanner()

    # Test not excluded
    assert not scanner._is_excluded(Path("skills/my_skill/SKILL.md"))

    # Test exact excluded matches
    assert scanner._is_excluded(Path("skills/node_modules/my_skill/SKILL.md"))
    assert scanner._is_excluded(Path(".venv/my_skill/SKILL.md"))

    # Test hidden directories
    assert scanner._is_excluded(Path("skills/.hidden/SKILL.md"))

    # Should skip exact '.' and '..'
    assert not scanner._is_excluded(Path("skills/./my_skill/SKILL.md"))
    assert not scanner._is_excluded(Path("skills/../my_skill/SKILL.md"))
