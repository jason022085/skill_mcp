## 2025-02-28 - [Path exclusion scanning optimization]
**Learning:** Using `path.parts` combined with `set.isdisjoint` is significantly faster (~2.5x) and more robust than converting paths to strings and doing substring matching. String matching also has issues with relative paths like `node_modules/file.txt` where the leading slash check `f"/{excluded}/"` will fail to exclude it.
**Action:** When filtering paths based on restricted directories in this codebase, avoid `str(path)` and always leverage `Path.parts` combined with set operations.
