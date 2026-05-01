
## 2024-05-01 - [O(1) Set Intersections for Path Exclusions]
**Learning:** Checking path exclusions by converting paths to strings and using `in` or `endswith` for string searches is ~2.5x slower than using `set.isdisjoint()` against `path.parts` directly.
**Action:** Use set intersections (`not EXCLUDED_DIRS.isdisjoint(path.parts)`) to efficiently filter path components instead of O(N*M) string matching.
