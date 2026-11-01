#!/usr/bin/env python3
"""Cổng xác minh nội dung cho nguồn đọc Control Tower (stdlib only).

Chỉ trả SUCCESS khi body đã giải mã thành nội dung file Markdown đúng:
- contents_json: JSON GitHub Contents API, encoding=base64, path đúng, decode được.
- raw_text: body thô của file, không phải HTML.
Sau đó: không rỗng, header dòng đầu đúng, sha256 nội dung khớp expected (chặn sai ref).

Phân loại lỗi: NETWORK_FAILURE | NO_ACCESS | NOT_FOUND | CACHE_MISS | HTML_PAGE |
JSON_INVALID | ENCODING_INVALID | EMPTY | HEADER_MISMATCH | WRONG_PATH | WRONG_REF | SUCCESS.
Không tự gọi mạng. Input là status/curl_rc/body đã thu thập từ bên ngoài.
"""
import argparse
import base64
import hashlib
import json
import sys


def classify(kind, status, curl_rc, body, path, header, expect_sha256):
    if curl_rc != 0:
        return "NETWORK_FAILURE", f"curl_rc={curl_rc}"
    if status == 404:
        return "NOT_FOUND", "HTTP 404 trên ref đã chỉ định"
    if status in (401, 403):
        return "NO_ACCESS", f"HTTP {status}"
    if status != 200:
        return "NETWORK_FAILURE", f"HTTP {status}"
    low = body[:400].lower()
    if b"cache miss" in low or b"url not accessible" in low:
        return "CACHE_MISS", "công cụ trả Cache miss / URL not accessible"

    if kind == "contents_json":
        try:
            obj = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            return "JSON_INVALID", str(e)
        if not isinstance(obj, dict) or obj.get("encoding") != "base64" or "content" not in obj:
            return "JSON_INVALID", "thiếu encoding=base64 hoặc content"
        if obj.get("path") != path:
            return "WRONG_PATH", f"path={obj.get('path')!r}"
        try:
            raw = base64.b64decode("".join(obj["content"].split()), validate=True)  # GitHub gửi base64 có xuống dòng
        except (ValueError, TypeError) as e:
            return "ENCODING_INVALID", str(e)
    elif kind == "raw_text":
        head = body[:500].lower()
        if b"<!doctype html" in head or b"<html" in head:
            return "HTML_PAGE", "HTTP 200 nhưng body là trang HTML, không phải nội dung file"
        raw = body
    else:
        raise SystemExit(f"unknown kind {kind}")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return "ENCODING_INVALID", str(e)
    if not text.strip():
        return "EMPTY", "nội dung rỗng"
    if text.lstrip("\ufeff").splitlines()[0].strip() != header:
        return "HEADER_MISMATCH", f"dòng đầu={text.splitlines()[0][:60]!r}"
    digest = hashlib.sha256(raw).hexdigest()
    if expect_sha256 and digest != expect_sha256:
        return "WRONG_REF", f"sha256={digest[:12]} khác expected={expect_sha256[:12]}"
    return "SUCCESS", f"sha256={digest} bytes={len(raw)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=["contents_json", "raw_text"])
    ap.add_argument("--status", type=int, required=True)
    ap.add_argument("--curl-rc", type=int, default=0)
    ap.add_argument("--body", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--header", required=True)
    ap.add_argument("--expect-sha256", default="")
    a = ap.parse_args()
    try:
        body = open(a.body, "rb").read() if a.body != "-" else sys.stdin.buffer.read()
    except OSError:
        body = b""  # không có body (ví dụ curl lỗi trước khi ghi file)
    verdict, reason = classify(a.kind, a.status, a.curl_rc, body, a.path, a.header, a.expect_sha256)
    print(f"{verdict} | {reason}")
    return 0 if verdict == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
