
## 2025-02-23 - [pathlib.Path performance in exclusion checks]
**Learning:** For path-based filtering or exclusion logic using `pathlib.Path`, checking `set.isdisjoint(path.parts)` for efficient subset checks is 3-7x faster than performing string conversions (`str(path)`) and substring checking (e.g. `endswith` or `in`), especially for large directory trees.
**Action:** Use `set.isdisjoint(path.parts)` when checking if any directory in a path matches a set of excluded directories. Keep basic `for` loops instead of generator expressions (e.g. `any()`) when iterating over parts for the highest performance in CPython.
