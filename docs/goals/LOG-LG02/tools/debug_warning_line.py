"""Trace decode on the exact warning line from the mojibake blob."""
import subprocess

blob = subprocess.run(
    ["git", "show", "83a567c:views/quotations.py"],
    capture_output=True,
).stdout.decode("utf-8")

start = blob.find("quyền thay đổi")
seg = blob[start - 30:start + 40]
print("BLOB SEG:", repr(seg))
print("CODEPOINTS:", [hex(ord(c)) for c in seg])
# NOTE: blob segment IS CLEAN 'quyền thay đổi' — meaning the mojibake for this
# line uses characters already valid unicode? Find the actual mojibake line
idx = blob.find("quyền")
while idx != -1:
    ctx = blob[idx - 25:idx + 25]
    if any(ord(c) > 0xFF for c in ctx):
        print("MOJIBAKE HIT:", repr(ctx))
        print("CODEPOINTS:", [hex(ord(c)) for c in ctx])
        break
    idx = blob.find("quyền", idx + 1)
