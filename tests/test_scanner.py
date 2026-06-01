import pytest
from pathlib import Path
from src.skill_mcp_server.skill.scanner import SkillScanner
import os

def test_scanner_with_real_files(tmp_path):
    # Setup test directory structure
    d = tmp_path / "test_skills"
    d.mkdir()

    # Create a valid skill
    skill_a = d / "skill_a"
    skill_a.mkdir()
    (skill_a / "SKILL.md").touch()

    # Create an excluded directory
    node_modules = d / "node_modules" / "pkg"
    node_modules.mkdir(parents=True)
    (node_modules / "SKILL.md").touch()

    # Create nested valid skill
    nested = d / "nested" / "skill_b"
    nested.mkdir(parents=True)
    (nested / "SKILL.md").touch()

    scanner = SkillScanner(patterns=("*/SKILL.md", "**/SKILL.md"))

    skills = list(scanner.scan(d))

    assert len(skills) == 2
    paths = [str(p.relative_to(d)) for p in skills]
    assert "skill_a/SKILL.md" in paths
    assert "nested/skill_b/SKILL.md" in paths
