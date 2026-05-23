import tempfile
from pathlib import Path
from src.skill_mcp_server.skill.scanner import SkillScanner

scanner = SkillScanner()
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    skill_dir = temp_path / "my_skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.touch()

    print("Checking", skill_file)
    print("Parts:", skill_file.parts)
    print("Excluded Dirs:", scanner.EXCLUDED_DIRS)
    print("Is disjoint:", scanner.EXCLUDED_DIRS.isdisjoint(skill_file.parts))
    print("Is excluded:", scanner._is_excluded(skill_file))

    git_file = temp_path / ".git" / "my_skill" / "SKILL.md"
    git_file.parent.mkdir(parents=True)
    git_file.touch()
    print("\nChecking", git_file)
    print("Parts:", git_file.parts)
    print("Excluded Dirs:", scanner.EXCLUDED_DIRS)
    print("Is disjoint:", scanner.EXCLUDED_DIRS.isdisjoint(git_file.parts))
    print("Is excluded:", scanner._is_excluded(git_file))
