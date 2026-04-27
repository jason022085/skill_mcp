# Copyright (c) 2025
# SPDX-License-Identifier: MIT

"""Skill directory scanner."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ..config.defaults import SKILL_SCAN_PATTERNS
from ..utils.logging import get_logger

logger = get_logger("skill.scanner")


class SkillScanner:
    """Scans directories to discover SKILL.md files.

    This class handles the discovery of skill files without
    parsing them - that's the parser's job.
    """

    # Directories to exclude from scanning
    EXCLUDED_DIRS: frozenset[str] = frozenset(
        {
            "__pycache__",
            ".git",
            ".svn",
            ".hg",
            "node_modules",
            ".venv",
            "venv",
            ".env",
        }
    )

    def __init__(
        self,
        patterns: tuple[str, ...] = SKILL_SCAN_PATTERNS,
    ) -> None:
        """Initialize the scanner.

        Args:
            patterns: Glob patterns to use for discovering skills.
        """
        self.patterns = patterns

    def scan(self, directory: Path) -> Iterator[Path]:
        """Scan a directory for skill files.

        Args:
            directory: Directory to scan.

        Yields:
            Paths to discovered SKILL.md files.
        """
        if not directory.exists():
            logger.warning(f"Skills directory does not exist: {directory}")
            return

        if not directory.is_dir():
            logger.warning(f"Not a directory: {directory}")
            return

        seen: set[Path] = set()

        for pattern in self.patterns:
            for path in directory.glob(pattern):
                # Skip excluded directories
                if self._is_excluded(path):
                    continue

                # Resolve to absolute and deduplicate
                abs_path = path.resolve()
                if abs_path in seen:
                    continue

                seen.add(abs_path)
                logger.debug(f"Found skill file: {abs_path}")
                yield abs_path

    def scan_multiple(self, directories: list[Path]) -> Iterator[Path]:
        """Scan multiple directories for skill files.

        Args:
            directories: List of directories to scan.

        Yields:
            Paths to discovered SKILL.md files (deduplicated).
        """
        seen: set[Path] = set()

        for directory in directories:
            for path in self.scan(directory):
                if path not in seen:
                    seen.add(path)
                    yield path

    def _is_excluded(self, path: Path) -> bool:
        """Check if a path should be excluded.

        Args:
            path: Path to check.

        Returns:
            True if the path should be excluded.
        """
        parts = path.parts

        # Check for excluded directories using set intersection (much faster)
        if not self.EXCLUDED_DIRS.isdisjoint(parts):
            return True

        # Skip hidden files/directories
        return any(part.startswith(".") and part not in (".", "..") for part in parts)

    def count_skills(self, directory: Path) -> int:
        """Count the number of skills in a directory.

        Args:
            directory: Directory to scan.

        Returns:
            Number of skill files found.
        """
        return sum(1 for _ in self.scan(directory))
