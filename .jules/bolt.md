## 2024-05-18 - Path Exclusions Performance
**Learning:** Using `set.isdisjoint(path.parts)` is significantly faster (~4x) than iterating and doing string checks (`if f"/{excluded}/" in path_str ...`) for filtering out excluded directories in `Path` traversal operations when dealing with a realistic mix of path inputs.
**Action:** Always prefer `isdisjoint` for O(1) subset checks over O(N*M) string substring evaluations on parts when building path inclusion/exclusion logic using pathlib.
