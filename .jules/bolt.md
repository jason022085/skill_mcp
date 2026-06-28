## 2025-02-26 - Path Checking Optimization
**Learning:** `pathlib.Path.is_relative_to` is significantly faster than using `relative_to` within a `try/except ValueError` block for validation, avoiding costly exception handling overhead.
**Action:** Use `is_relative_to()` for negative boundary checks to ensure faster path resolutions.
