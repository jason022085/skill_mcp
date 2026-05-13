from pathlib import Path
from skill_mcp_server.skill.scanner import SkillScanner

def test_scanner_exclude(temp_dir: Path):
    scanner = SkillScanner()
    # Create some mock paths to test exclusion logic
    # We will just test the `_is_excluded` method directly for now

    assert scanner._is_excluded(Path("/test/.git/something")) == True
    assert scanner._is_excluded(Path("/test/node_modules/something")) == True
    assert scanner._is_excluded(Path("/test/.hidden/something")) == True
    assert scanner._is_excluded(Path("/test/venv")) == True
    assert scanner._is_excluded(Path("/test/valid_dir")) == False
