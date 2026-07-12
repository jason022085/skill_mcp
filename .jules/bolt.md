## 2025-02-20 - Fast Path Exclusion with set.isdisjoint
**Learning:** Replaced O(N) string formatting and substring search for path exclusion (`f"/{excluded}/" in str(path)`) with `set.isdisjoint(path.parts)`. String matching on parts was failing to correctly exclude relative paths and was relatively slow. `isdisjoint` brings O(1) hash table performance and better correctness to directory exclusion.
**Action:** Always prefer `set.isdisjoint(path.parts)` over substring search on stringified paths when filtering out explicitly named directories in deep `pathlib.Path` tree traversals.
