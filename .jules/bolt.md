## 2025-05-02 - Pathlib vs os.walk performance in python
**Learning:** `pathlib`'s `rglob` can be significantly slower than `os.walk` when scanning directories with many files or nested structures, mainly due to the overhead of instantiating `Path` objects for every single file.
**Action:** When performing deep directory traversals where only string paths are needed for the result (like scanning resources and scripts), prefer `os.walk` with string manipulation over `pathlib.Path.rglob()`.
