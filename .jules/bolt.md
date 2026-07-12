## 2025-02-18 - Path filtering performance
**Learning:** For path-based filtering or exclusion logic using `pathlib.Path`, using `set.isdisjoint(path.parts)` for O(1) subset checks and iterating over `path.parts` with `any()` expressions is significantly faster than performing substring checks on `str(path)`.
**Action:** Use `isdisjoint()` and `any()` on `path.parts` instead of string matching when evaluating exclusions against `pathlib.Path` objects.
