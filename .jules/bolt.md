## 2025-06-10 - Path exclusion optimization using `isdisjoint`
**Learning:** Using `set.isdisjoint(path.parts)` is significantly faster (around 2-3x) than using string conversions and `in`/`.endswith` checks when determining if a path contains excluded directories, avoiding string allocation and multiple substring operations.
**Action:** Use `set.isdisjoint` against `path.parts` instead of `str(path)` when checking for excluded directories in a `pathlib.Path`.
