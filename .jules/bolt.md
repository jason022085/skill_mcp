## 2025-02-14 - Path Validation Optimization
**Learning:** Using `set.isdisjoint(path.parts)` and `path.is_relative_to()` is significantly faster than stringifying paths and performing substring or `try/except` checks during directory traversals.
**Action:** Use set operations on `path.parts` for exclusions and `is_relative_to` for subpath checks in performance-critical path processing code.
