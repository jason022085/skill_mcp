# Copyright (c) 2025
# SPDX-License-Identifier: MIT

"""Skill directory scanner."""

from __future__ import annotations

import os
import re
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
        dir_str = str(directory)

        # Precompile regexes for glob patterns to handle ** correctly
        regexes = []
        for pattern in self.patterns:
            res = []
            i = 0
            n = len(pattern)
            while i < n:
                if pattern[i : i + 3] == "**/":
                    res.append("(?:.*/)?")
                    i += 3
                elif pattern[i : i + 2] == "**":
                    res.append(".*")
                    i += 2
                elif pattern[i] == "*":
                    res.append("[^/]*")
                    i += 1
                elif pattern[i] == "?":
                    res.append("[^/]")
                    i += 1
                elif pattern[i] in "[]()|^$.+{}":
                    res.append("\\" + pattern[i])
                    i += 1
                else:
                    res.append(pattern[i])
                    i += 1
            regexes.append(re.compile("^" + "".join(res) + "$"))

        # Use os.walk to allow in-place pruning of excluded directories,
        # dramatically improving performance over Path.glob which traverses everything first.
        for root, dirs, files in os.walk(dir_str):
            # Prune excluded and hidden directories in-place
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS and not d.startswith(".")]

            for file in files:
                abs_path = os.path.join(root, file)
                # Safely compute relative path
                rel_path = os.path.relpath(abs_path, dir_str)

                # Normalize separators for regex matching
                rel_path = rel_path.replace(os.sep, "/")

                # Check if the relative path matches any of our glob patterns
                matched = False
                for regex in regexes:
                    if regex.match(rel_path):
                        matched = True
                        break

                if matched:
                    p = Path(abs_path).resolve()
                    if p not in seen:
                        seen.add(p)
                        logger.debug(f"Found skill file: {p}")
                        yield p

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
        path_str = str(path)

        # Check for excluded directories in path
        for excluded in self.EXCLUDED_DIRS:
            if f"/{excluded}/" in path_str or path_str.endswith(f"/{excluded}"):
                return True

        # Skip hidden files/directories
        return any(part.startswith(".") and part not in (".", "..") for part in path.parts)

    def count_skills(self, directory: Path) -> int:
        """Count the number of skills in a directory.

        Args:
            directory: Directory to scan.

        Returns:
            Number of skill files found.
        """
        return sum(1 for _ in self.scan(directory))
