
## 2024-05-18 - Optimize Deep Directory Traversals with `set.isdisjoint`
**Learning:** For path exclusion logic using `pathlib.Path`, iterating and checking substrings with `str(path)` or checking specific formats like `f"/{excluded}/" in str(path)` has an O(N*M) runtime complexity. By using `set.isdisjoint(path.parts)`, you achieve an O(1) subset check which drastically improves directory traversal performance without the need for manual recursion, while preserving expected path behavior.
**Action:** When filtering logic processes many pathlib.Paths based on single-level directory name exclusion, replace custom string manipulation loops with `isdisjoint()` against `path.parts` to ensure scalable performance.
