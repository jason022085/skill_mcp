import pytest
from pathlib import Path
from skill_mcp_server.skill.manager import SkillManager
from skill_mcp_server.skill.models import SkillInfo

def test_list_skill_files(tmp_path):
    # Setup test directory
    base_dir = tmp_path / "skill1"
    base_dir.mkdir()

    # Create resource directory and files
    assets_dir = base_dir / "assets"
    assets_dir.mkdir()
    (assets_dir / "image.png").write_text("test")
    (assets_dir / ".hidden").write_text("hidden")

    # Create scripts directory and files
    scripts_dir = base_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "script.py").write_text("print('test')")
    (scripts_dir / "helper.txt").write_text("helper text")

    # Create mock skill info
    skill = SkillInfo(
        name="test_skill",
        description="A test skill",
        location=base_dir / "SKILL.md",
        content=""
    )

    manager = SkillManager(resource_dirs=("assets",))
    resources, scripts = manager.list_skill_files(skill)

    # Check paths using normalized cross-platform strings
    # The output is always posixpath on rel_path string conversion on python 3.12+ (in some contexts) or native
    # Let's just check replacing backslashes.

    res = [r.replace('\\', '/') for r in resources]
    scr = [s.replace('\\', '/') for s in scripts]

    assert "assets/image.png" in res
    assert "scripts/helper.txt" in res
    assert "scripts/script.py" in scr
