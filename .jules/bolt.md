
## 2026-05-05 - [pathlib rglob vs os.walk]
**Learning:** `os.walk` is roughly 4.4x faster than `pathlib.Path.rglob()` for deep directory traversals when only string paths are needed because it avoids the overhead of instantiating `Path` objects and calling `stat()` for every file.
**Action:** Use `os.walk` instead of `Path.rglob()` when performing deep directory scans that only need string paths or cross-platform consistency.

## 2026-05-05 - [pathlib exclusion checks]
**Learning:** For path-based filtering or exclusion logic using `pathlib.Path`, iterating over `path.parts` with `any()` expressions is faster and more robust than performing substring checks on `str(path)`.
**Action:** Use `any(part in EXCLUDED_DIRS for part in path.parts)` instead of `path_str = str(path); if f"/{excluded}/" in path_str:` for filtering paths.
