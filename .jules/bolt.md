## 2025-05-04 - Pathlib Object Overhead

**Learning:** `pathlib.Path.rglob()` causes severe performance bottlenecks in this codebase during deep directory traversals for file scanning, as creating heavily instatiated `Path` objects adds a lot of overhead. String checks on `str(path)` inside tight loops for path-based exclusion checking also causes bottlenecks.

**Action:** Prefer `os.walk` with string manipulation instead of `rglob()` for file scanning where only string paths are needed. Use generator expressions utilizing `any()` over `path.parts` instead of `str(path)` substring matching to check path exclusions robustly and faster.
