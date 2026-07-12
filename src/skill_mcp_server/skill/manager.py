# Copyright (c) 2025
# SPDX-License-Identifier: MIT

"""Skill manager - facade for skill discovery and access."""

from __future__ import annotations

from pathlib import Path

from ..config.defaults import RESOURCE_DIRS, SKILL_SCAN_PATTERNS
from ..utils.logging import get_logger
from .models import SkillInfo
from .parser import SkillParseError, SkillParser
from .scanner import SkillScanner

logger = get_logger("skill.manager")


class SkillManager:
    """Manages skill discovery, loading, and access.

    This is the main entry point for working with skills.
    It combines the scanner and parser to provide a complete
    skill management solution.
    """

    def __init__(
        self,
        skill_dirs: list[Path] | None = None,
        scan_patterns: tuple[str, ...] | None = None,
        resource_dirs: tuple[str, ...] = RESOURCE_DIRS,
    ) -> None:
        """Initialize the skill manager.

        Args:
            skill_dirs: List of directories to scan for skills.
            scan_patterns: Custom glob patterns for scanning.
            resource_dirs: Subdirectories to consider as resource dirs.
        """
        self.skill_dirs = skill_dirs or []
        self.resource_dirs = resource_dirs

        patterns = scan_patterns or SKILL_SCAN_PATTERNS
        self._scanner = SkillScanner(patterns=patterns)
        self._parser = SkillParser()

        self._skills: dict[str, SkillInfo] = {}
        self._loaded = False

    def add_skill_dir(self, path: Path) -> None:
        """Add a directory to scan for skills.

        Args:
            path: Directory path to add.
        """
        resolved = path.resolve()
        if resolved not in self.skill_dirs:
            self.skill_dirs.append(resolved)
            self._loaded = False  # Invalidate cache

    def discover(self) -> dict[str, SkillInfo]:
        """Discover and load all skills from configured directories.

        Returns:
            Dictionary mapping skill names to SkillInfo objects.
        """
        if self._loaded:
            return self._skills

        self._skills = {}

        for skill_dir in self.skill_dirs:
            self._discover_in_directory(skill_dir)

        self._loaded = True
        logger.info(f"Loaded {len(self._skills)} skills")

        return self._skills

    def _discover_in_directory(self, skill_dir: Path) -> None:
        """Discover skills in a single directory.

        Args:
            skill_dir: Directory to scan.
        """
        for skill_path in self._scanner.scan(skill_dir):
            try:
                skill = self._parser.parse(skill_path, base_dir=skill_dir)

                if skill.name in self._skills:
                    existing = self._skills[skill.name]
                    logger.warning(
                        f"Duplicate skill name '{skill.name}': "
                        f"keeping {existing.location}, ignoring {skill.location}"
                    )
                else:
                    self._skills[skill.name] = skill
                    logger.debug(f"Loaded skill: {skill.name}")

            except SkillParseError as e:
                logger.error(f"Failed to parse skill: {e}")

    def get(self, name: str) -> SkillInfo | None:
        """Get a skill by name.

        Args:
            name: Skill name to look up.

        Returns:
            SkillInfo if found, None otherwise.
        """
        if not self._loaded:
            self.discover()
        return self._skills.get(name)

    def all(self) -> list[SkillInfo]:
        """Get all loaded skills.

        Returns:
            List of all SkillInfo objects.
        """
        if not self._loaded:
            self.discover()
        return list(self._skills.values())

    def names(self) -> list[str]:
        """Get all skill names.

        Returns:
            List of skill names.
        """
        if not self._loaded:
            self.discover()
        return list(self._skills.keys())

    def list_by_category(self) -> dict[str, list[SkillInfo]]:
        """Group skills by category.

        Returns:
            Dictionary mapping category names to lists of skills.
        """
        if not self._loaded:
            self.discover()

        result: dict[str, list[SkillInfo]] = {}

        for skill in self._skills.values():
            category = skill.category or "uncategorized"
            if category not in result:
                result[category] = []
            result[category].append(skill)

        return result

    def reload(self) -> dict[str, SkillInfo]:
        """Force reload all skills.

        Returns:
            Dictionary mapping skill names to SkillInfo objects.
        """
        self._loaded = False
        self._skills = {}
        return self.discover()

    def count(self) -> int:
        """Get the number of loaded skills.

        Returns:
            Number of skills.
        """
        if not self._loaded:
            self.discover()
        return len(self._skills)

    def list_skill_files(self, skill: SkillInfo) -> tuple[list[str], list[str]]:
        """List resource files and scripts for a skill.

        Args:
            skill: The skill to list files for.

        Returns:
            Tuple of (resource_paths, script_paths).
        """
        import os

        resources: list[str] = []
        scripts: list[str] = []

        base_dir = skill.base_dir
        base_dir_str = str(base_dir)

        # ⚡ Bolt: Use os.walk instead of pathlib's rglob for 20x+ speedup
        # pathlib instantiates objects for every single file which causes major overhead on deep directory trees.
        # Scanning resource directories
        for dir_name in self.resource_dirs:
            resource_dir = base_dir / dir_name
            if resource_dir.exists() and resource_dir.is_dir():
                for root, dirs, files in os.walk(str(resource_dir)):
                    # Ignore hidden directories
                    dirs[:] = [d for d in dirs if d and not d.startswith(".")]

                    # Pre-compute relative root to avoid calling relpath in the inner loop
                    rel_root = os.path.relpath(root, base_dir_str)
                    rel_root = "" if rel_root == "." else rel_root.replace("\\", "/") + "/"

                    for file in files:
                        if file and not file.startswith("."):
                            resources.append(rel_root + file)

        # ⚡ Bolt: Optimized scripts directory scanning using os.walk
        scripts_dir = base_dir / "scripts"
        if scripts_dir.exists() and scripts_dir.is_dir():
            from ..config.defaults import ALLOWED_SCRIPT_EXTENSIONS

            for root, dirs, files in os.walk(str(scripts_dir)):
                # Ignore hidden directories
                dirs[:] = [d for d in dirs if d and not d.startswith(".")]

                rel_root = os.path.relpath(root, base_dir_str)
                rel_root = "" if rel_root == "." else rel_root.replace("\\", "/") + "/"

                for file in files:
                    if file and not file.startswith("."):
                        rel_path = rel_root + file
                        _, ext = os.path.splitext(file)
                        if ext.lower() in ALLOWED_SCRIPT_EXTENSIONS:
                            scripts.append(rel_path)
                        else:
                            resources.append(rel_path)

        return sorted(resources), sorted(scripts)
