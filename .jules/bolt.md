## 2025-06-27 - [Efficient Path Checking]
**Learning:** Found two common performance patterns in python `pathlib.Path` usage across the codebase.
1. Using `path.relative_to(base)` inside a `try/except ValueError` block to check if a path is within a base directory is slower than checking `path.is_relative_to(base)` (available in Python 3.9+). The codebase targets `>=3.10`.
2. O(N*M) string-based path exclusion checks (`f"/{excluded}/" in str(path)`) in `SkillScanner._is_excluded` can be significantly optimized (up to ~2x speedup) by using `set.isdisjoint(path.parts)` for O(1) membership checks of path segments, while keeping the string fallback for complex paths containing slashes.

**Action:** Use `.is_relative_to(base)` and `set.isdisjoint(path.parts)` to optimize path-related validations and filtering.
