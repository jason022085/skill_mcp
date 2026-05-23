import tempfile
from pathlib import Path
from src.skill_mcp_server.skill.manager import SkillManager
from src.skill_mcp_server.skill.models import SkillInfo

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    res_dir = temp_path / "resources"
    res_dir.mkdir()
    (res_dir / "test.txt").touch()

    scripts_dir = temp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "test.py").touch()
    (scripts_dir / "test.txt").touch()

    class MockSkill:
        base_dir = temp_path

    manager = SkillManager()
    manager.resource_dirs = ("resources",)
    res, scripts = manager.list_skill_files(MockSkill())
    print("Resources:", res)
    print("Scripts:", scripts)
