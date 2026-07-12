## 2025-02-28 - Optimize directory scanning in list_skill_files
**Learning:** `Path.rglob("*")` is slow for deep directory traversals because it creates `Path` objects for every file and doesn't easily skip excluded directories.
**Action:** Replace `Path.rglob("*")` with `os.walk` to efficiently traverse directories and easily exclude hidden folders and files in `src/skill_mcp_server/skill/manager.py`.
