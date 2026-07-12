import time
import tempfile
from pathlib import Path
import os
import shutil

# Benchmark 1: is_excluded
class OldScanner:
    EXCLUDED_DIRS = frozenset({"__pycache__", ".git", "node_modules", ".venv", "venv", ".env"})
    def _is_excluded(self, path: Path) -> bool:
        path_str = str(path)
        for excluded in self.EXCLUDED_DIRS:
            if f"/{excluded}/" in path_str or path_str.endswith(f"/{excluded}"):
                return True
        for part in path.parts:
            if part.startswith(".") and part not in (".", ".."):
                return True
        return False

class NewScanner:
    EXCLUDED_DIRS = frozenset({"__pycache__", ".git", "node_modules", ".venv", "venv", ".env"})
    def _is_excluded(self, path: Path) -> bool:
        if not self.EXCLUDED_DIRS.isdisjoint(path.parts):
            return True
        for part in path.parts:
            if part.startswith(".") and part not in (".", ".."):
                return True
        return False

paths = [Path(f"/var/www/my_project/src/components/button/button_{i}.tsx") for i in range(10000)]
paths += [Path(f"/var/www/my_project/node_modules/react/index_{i}.js") for i in range(10000)]

old_scanner = OldScanner()
t0 = time.time()
for p in paths:
    old_scanner._is_excluded(p)
t1 = time.time()
print(f"Old _is_excluded: {t1 - t0:.4f}s")

new_scanner = NewScanner()
t0 = time.time()
for p in paths:
    new_scanner._is_excluded(p)
t1 = time.time()
print(f"New _is_excluded: {t1 - t0:.4f}s")

# Benchmark 2: list_skill_files
class OldManager:
    def list_files(self, base_dir: Path):
        resources = []
        for file_path in base_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                rel_path = file_path.relative_to(base_dir)
                resources.append(str(rel_path))
        return resources

class NewManager:
    def list_files(self, base_dir: Path):
        resources = []
        base_dir_str = str(base_dir)
        for root, dirs, files in os.walk(base_dir_str):
            for file in files:
                if not file.startswith("."):
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, base_dir_str)
                    resources.append(rel_path)
        return resources

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    for i in range(100):
        d = temp_path / f"dir_{i}"
        d.mkdir()
        for j in range(100):
            (d / f"file_{j}.txt").touch()

    old_manager = OldManager()
    t0 = time.time()
    res1 = old_manager.list_files(temp_path)
    t1 = time.time()
    print(f"Old list_files: {t1 - t0:.4f}s")

    new_manager = NewManager()
    t0 = time.time()
    res2 = new_manager.list_files(temp_path)
    t1 = time.time()
    print(f"New list_files: {t1 - t0:.4f}s")
