## 2025-02-28 - Fast Path Filtering with set.isdisjoint
**Learning:** For path-based filtering or exclusion logic using `pathlib.Path`, `set.isdisjoint(path.parts)` is significantly faster (over 50% in benchmarks) than performing substring checks on `str(path)`. It is also less error-prone since it avoids fragile formatting issues with relative paths or missing slash separators.
**Action:** Always prefer `set.isdisjoint` over string conversion and iteration when checking if any path component belongs to a set of excluded names.
