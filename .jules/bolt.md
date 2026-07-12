## 2025-05-14 - Fast Path Exclusions
**Learning:** For path-based filtering using `pathlib.Path`, using `set.isdisjoint(path.parts)` is an O(1) operation compared to converting `path` to string and doing substring searches or iterating parts and checking against sets. This provides significant performance boosts during large directory tree traversals.
**Action:** Always prefer `path.parts` set operations over string matching when checking directories against blocklists/allowlists in `pathlib`-heavy code.
