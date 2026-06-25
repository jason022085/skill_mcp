## 2025-06-25 - Fast path exclusion with set disjoint checks
**Learning:** Checking if a file path is in an excluded set using substring matching (`for x in EXCLUDED: if f"/{x}/" in str(path)`) is computationally expensive O(N*M) during deep globbed traversals.
**Action:** Use `set.isdisjoint(path.parts)` for O(1) single-level directory filtering, combining it with explicit iteration for hidden files and string matching ONLY when absolutely necessary (e.g., multi-segment directories with slashes).
