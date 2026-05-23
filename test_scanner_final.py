import tempfile
from pathlib import Path
from src.skill_mcp_server.skill.scanner import SkillScanner

def test_scanner_exclusion():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Should be scanned
        skill_dir = temp_path / "my_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").touch()

        # Should be excluded
        git_dir = temp_path / ".git" / "my_skill"
        git_dir.mkdir(parents=True)
        (git_dir / "SKILL.md").touch()

        pycache_dir = temp_path / "__pycache__" / "my_skill"
        pycache_dir.mkdir(parents=True)
        (pycache_dir / "SKILL.md").touch()

        scanner = SkillScanner(patterns=("*/SKILL.md",))
        found = list(scanner.scan(temp_path))

        print("Found:", found)
        assert len(found) == 1
        assert found[0].parent.name == "my_skill"
        assert not any(".git" in str(p) for p in found)
        assert not any("__pycache__" in str(p) for p in found)
        print("Test passed!")

if __name__ == "__main__":
    test_scanner_exclusion()
