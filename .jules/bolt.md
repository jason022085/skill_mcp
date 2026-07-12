## 2025-03-02 - [Fast Path Filtering]
**Learning:** Using `str(path)` and looping through multiple substring checks (`in path_str` or `path_str.endswith`) is expensive for path filtering. `pathlib.Path.parts` combined with `frozenset.isdisjoint()` provides an O(1) subset check, bypassing string manipulation overhead completely.
**Action:** Default to `set.isdisjoint(path.parts)` and generators with `any()` over substring matching when building path exclusion or inclusion rules.
