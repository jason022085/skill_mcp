## 2025-06-12 - Optimize Path Exclusion Checks

**Learning:** When scanning directories with `pathlib.Path`, using string conversion and string containment checks (`f"/{excluded}/" in str(path)`) inside a tight loop is an O(N*M) operation that can be unexpectedly slow when dealing with many nested directories. More importantly, it creates subtle bugs for relative paths that lack leading slashes (e.g. `node_modules/foo/bar`).
**Action:** Always replace string-based path component filtering with `not excluded_set.isdisjoint(path.parts)`. It operates in O(1) time per part, accurately matches path components regardless of whether the path is absolute or relative, and is measurably faster (roughly ~65% speedup in benchmarks).
