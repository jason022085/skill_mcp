## 2025-05-18 - Optimized Path Exclusion Checks
**Learning:** For path-based filtering or exclusion logic using `pathlib.Path`, using `set.isdisjoint(path.parts)` for efficient subset checks is significantly faster than performing substring checks on `str(path)`. It avoids string conversion overhead, scales better with large path/exclusion lists, and is more robust for relative paths that start with an excluded directory name.
**Action:** Prefer `set.isdisjoint(path.parts)` over string conversions and substring checks when filtering `pathlib.Path` objects against a set of excluded directory names.
## 2025-05-18 - Optimized Directory Scanning
**Learning:** For deep directory traversals (like file scanning), using `os.walk` is demonstrably faster than `pathlib.Path.rglob("*")`. `os.walk` yields lists of files and directories directly, avoiding the overhead of instantiating numerous intermediate `Path` objects for every element in the tree when only a subset are needed.
**Action:** Prefer `os.walk` over `Path.rglob()` or `Path.glob("**/*")` in performance-critical file scanning operations, especially when dealing with large directory structures.
