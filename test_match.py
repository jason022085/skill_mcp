import re
from pathlib import PurePath

def translate_glob_to_regex(pattern: str) -> re.Pattern:
    res = []
    i = 0
    n = len(pattern)
    while i < n:
        if pattern[i:i+3] == '**/':
            res.append('(?:.*/)?')
            i += 3
        elif pattern[i:i+2] == '**':
            res.append('.*')
            i += 2
        elif pattern[i] == '*':
            res.append('[^/]*')
            i += 1
        elif pattern[i] == '?':
            res.append('[^/]')
            i += 1
        elif pattern[i] in '[]()|^$.+{}':
            res.append('\\' + pattern[i])
            i += 1
        else:
            res.append(pattern[i])
            i += 1
    return re.compile('^' + ''.join(res) + '$')

p = translate_glob_to_regex("**/SKILL.md")
print("Regex", p.pattern)
print(bool(p.match("SKILL.md")))
print(bool(p.match("foo/SKILL.md")))
print(bool(p.match("foo/bar/SKILL.md")))
