## 2025-05-24 - [Pathlib rglob overhead]
**Learning:** `pathlib.Path.rglob()` incurs significant performance overhead during deep directory traversals due to continuous `Path` object instantiation, which is specific to scenarios doing large file scanning where only string representations are needed (like in `list_skill_files()`).
**Action:** Use `os.walk` with direct string manipulation functions (`os.path.join`, `os.path.relpath`) for pure string path collection, avoiding heavy object instantiation. This can speed up directory traversal by 3.5x - 5x.
