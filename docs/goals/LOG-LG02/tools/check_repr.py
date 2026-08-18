"""Dump repr cua cac chuoi nghi ngo trong web_app.py de xac dinh dung ky tu."""
from pathlib import Path
import re

p = Path('views/web_app.py')
s = p.read_text(encoding='utf-8')

patterns = [
    r'Route\("Thỏa Thuận[^)]*\)',
    r'\("Kh[^"]*", "Entity Context"',
    r'"Đang chạy Local Admin[^"]*"',
    r'"Bật AUTH_REQUIRED[^"]*"',
]
out = []
for pat in patterns:
    m = re.search(pat, s)
    if m:
        out.append(f"FOUND: {m.group(0)}")
        # print code points of each char
        codes = [hex(ord(c)) for c in m.group(0) if ord(c) > 127]
        out.append(f"  non-ascii codepoints: {codes}")
    else:
        out.append(f"NOT FOUND: {pat}")

res = '\n'.join(out)
Path('/tmp/repr_check.txt').write_text(res, encoding='utf-8')
print(res)
