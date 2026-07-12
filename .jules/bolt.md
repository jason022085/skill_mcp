## 2025-04-29 - O(1) set lookup for path parts
**Learning:** Checking for excluded directories by iterating through a frozenset and checking `if f'/{excluded}/' in str(path) or path.endswith(f'/{excluded}')` is slow.
**Action:** Utilizing `path.parts` and `frozenset.isdisjoint` provides a >2x performance increase (O(1) intersection checks vs O(N) string matches) and natively handles edge cases (e.g. paths starting with excluded dirs without leading slashes).
