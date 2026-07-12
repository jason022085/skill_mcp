## 2025-05-15 - [Avoid pathlib.Path.rglob for directory traversals]
**Learning:** `pathlib.Path.rglob("*")` is a major performance bottleneck for deep directory traversals because it traverses excluded/hidden directories entirely (like `.git` or `node_modules`) before filtering files.
**Action:** Use `os.walk` with in-place directory pruning (`dirs[:] = [d for d in dirs if not d.startswith(".") and d not in excluded]`) instead to stop traversing into excluded directories.
