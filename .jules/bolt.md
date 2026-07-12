## 2025-05-21 - [Fast Directory Traversal]
**Learning:** For deep directory traversals where only string paths are needed (such as file scanning in `SkillManager.list_skill_files`), using `os.walk` with string manipulation is significantly faster (often 8x+) than using `pathlib.Path.rglob("*")`. `rglob` incurs heavy object instantiation overhead by creating `Path` objects for every intermediate directory and file.
**Action:** When returning lists of strings representing relative paths from a directory tree, prefer `os.walk` combined with `os.path.relpath`.

## 2025-05-21 - [Fast Path Exclusion Checking]
**Learning:** For path-based filtering or exclusion logic using `pathlib.Path` (as in `SkillScanner._is_excluded`), using `set.isdisjoint(path.parts)` against a set of excluded directory names is about 3x faster than iterating over parts and performing substring or suffix checks on `str(path)`.
**Action:** Use set intersection logic (`isdisjoint`) on path components when doing exact directory name exclusion checks instead of string-based comparisons.
