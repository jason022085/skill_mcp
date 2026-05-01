from pathlib import Path
from skill_mcp_server.skill.scanner import SkillScanner

def test_is_excluded():
    scanner = SkillScanner()

    # Excluded dirs
    assert scanner._is_excluded(Path("/foo/node_modules/bar")) is True
    assert scanner._is_excluded(Path("/foo/node_modules")) is True
    assert scanner._is_excluded(Path("node_modules/bar")) is True
    assert scanner._is_excluded(Path("/foo/.git")) is True
    assert scanner._is_excluded(Path(".git/config")) is True

    # Hidden files
    assert scanner._is_excluded(Path("/foo/.hidden")) is True
    assert scanner._is_excluded(Path(".hidden")) is True

    # Allowed paths
    assert scanner._is_excluded(Path("foo/bar_node_modules/baz")) is False
    assert scanner._is_excluded(Path("/foo/bar/baz.py")) is False
    assert scanner._is_excluded(Path("foo/bar.git")) is False
