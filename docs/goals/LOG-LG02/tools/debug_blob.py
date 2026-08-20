"""Dump code points of mojibake around 'giá‘ang' patterns in the blob."""
import subprocess
import re

blob = subprocess.run(
    ["git", "show", "83a567c:views/quotations.py"],
    capture_output=True,
).stdout.decode("utf-8")

# pattern: 'giá' followed by mojibake of ' đang'
for m in re.finditer(r'giá.{0,8}', blob):
    seg = m.group(0)
    print(repr(seg), " ".join(hex(ord(c)) for c in seg))
    break

# pattern 'Khách ch' + mojibake of 'ốt'
for m in re.finditer(r'Khách ch.{0,4}', blob):
    seg = m.group(0)
    print(repr(seg), " ".join(hex(ord(c)) for c in seg))
    break

# mojibake of 'đ' alone: find 'Báo giá' + mojibake
for m in re.finditer(r'Báo giá.{0,6}', blob):
    seg = m.group(0)
    print(repr(seg), " ".join(hex(ord(c)) for c in seg))
    break
