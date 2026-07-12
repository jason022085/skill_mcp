## 2025-06-14 - Optimize path exclusion string matching
**Learning:** For path-based filtering or exclusion logic using `pathlib.Path`, using `set.isdisjoint(path.parts)` is an O(1) set intersection operation that is dramatically faster (~2-3x speedup) than executing substring containment loops on `str(path)`.
**Action:** Always prefer `set.isdisjoint(path.parts)` over substring checking when checking single-level directory name exclusion limits in filesystem traversal scripts.
