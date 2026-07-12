import tempfile
from pathlib import Path
from src.skill_mcp_server.skill.scanner import SkillScanner

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    skill_dir = temp_path / "my_skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.touch()

    print("Pattern checking")
    scanner = SkillScanner(patterns=("SKILL.md",))
    print("Files found by glob:")
    for p in temp_path.glob("SKILL.md"):
        print(p)
    print("Files found by rglob:")
    for p in temp_path.rglob("SKILL.md"):
        print(p)

    print("Using scanner:")
    print(list(scanner.scan(temp_path)))
