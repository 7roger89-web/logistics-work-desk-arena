"""Sửa encoding views/web_app.py (mixed mojibake).

Phân tích: file chứa hỗn hợp single- và double-mojibake tiếng Việt (một số đoạn
chỉ qua 1 bước encode, một số qua 2 bước; NBSP đôi khi bị chuẩn hóa thành space).
Chiến lược: xử lý ở mức byte:

1. Giải mã toàn file theo UTF-8. Với mỗi ký tự thu được:
   - Nếu 0x0080 <= code <= 0x00FF: đây là ký tự mojibake -> emit byte = code.
   - Nếu ký tự nằm trong _ARTIFACT_MAP (cp1252 artifacts như ƒ, ', ", ...):
     emit byte được ánh xạ.
   - Ngược lại: giữ nguyên ký tự, phát UTF-8 bình thường.
2. Bộ đệm byte kết quả được giải mã lại UTF-8 nghiêm ngặt.
3. Khôi phục mất mát NBSP: nếu byte 0xC3 (lead 'à..ÿ') đứng trước 0x20 (space)
   hoặc cuối buffer, giả định continuation byte bị mất khi NBSP (0xA0) bị
   chuẩn hóa thành space -> thay bằng 0xA0 trước khi giải mã cuối.

Kiểm chứng: chuỗi tiếng Việt chuẩn phải xuất hiện và file compile được.
"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[4] / "views" / "web_app.py"

_ARTIFACT_MAP: dict[str, int] = {
    # Ánh xạ cp1252 artifacts: ký tự mojibake -> byte gốc (0x80..0x9F).
    "€": 0x80, "‚": 0x82, "ƒ": 0x83, "„": 0x84, "…": 0x85, "†": 0x86,
    "‡": 0x87, "ˆ": 0x88, "‰": 0x89, "Š": 0x8A, "‹": 0x8B, "Œ": 0x8C,
    "Ž": 0x8E, "‘": 0x91, "’": 0x92, "“": 0x93, "”": 0x94, "•": 0x95,
    "–": 0x96, "—": 0x97, "˜": 0x98, "™": 0x99, "š": 0x9A, "›": 0x9B,
    "œ": 0x9C, "ž": 0x9E, "Ÿ": 0x9F,
}


def decode_mojibake(text: str) -> bytes:
    """Chuyển văn bản mojibake về chuỗi byte gốc."""
    out = bytearray()
    for char in text:
        code = ord(char)
        if 0x0080 <= code <= 0x00FF:
            out.append(code)
        elif char in _ARTIFACT_MAP:
            out.append(_ARTIFACT_MAP[char])
        else:
            out.extend(char.encode("utf-8"))
    return bytes(out)


def fix_contextual(text: str) -> str:
    """Sửa các từ còn sót bị hỏng do mất byte continuation (ngoài NBSP).

    Các mẫu này do byte lead UTF-8 (C4, C3, ...) bị cắt mất byte tiếp theo,
    khiến ký tự hiển thị sai. Ánh xạ theo ngữ cảnh đã xác minh thủ công.
    """
    replacements = [
        # quản lý
        ("quản lị", "quản lý"),
        ("Quản lị", "Quản lý"),
        # tạo/vô hiệu hóa
        ("tào/vô", "tạo/vô"),
        ("Tào/vô", "Tạo/vô"),
        # kết nối
        ("kết nố", "kết nối"),
        # Ā = C4 + continuation bị mất: Đ (C4 90) khi tiếp theo là 90
        ("Ā tạo", "Đã tạo"),
        ("Āp dụng", "Áp dụng"),
        ("Ā thể xóa", "Có thể xóa"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def fix_nbsp_loss(buf: bytes) -> bytes:
    """Khôi phục các byte continuation bị mất do NBSP -> space (0xA0 -> 0x20).

    Quy tắc: byte lead của chuỗi 2 byte UTF-8 (C0..DF) đứng trước byte không
    hợp lệ làm continuation (không thuộc 80..BF) thì giả định continuation
    đáng lẽ là 0xA0 (NBSP đã bị thay bằng space 0x20 khi encode).
    """
    fixed = bytearray()
    i = 0
    n = len(buf)
    while i < n:
        byte = buf[i]
        if 0xC0 <= byte <= 0xDF and i + 1 < n:
            nxt = buf[i + 1]
            if not (0x80 <= nxt <= 0xBF):
                # continuation bị mất/đã thành space.
                fixed.append(byte)
                if nxt == 0x20:
                    fixed.append(0xA0)
                else:
                    fixed.append(nxt)
                i += 2
                continue
        if 0xE0 <= byte <= 0xEF and i + 2 < n:
            a, b = buf[i + 1], buf[i + 2]
            if not (0x80 <= a <= 0xBF and 0x80 <= b <= 0xBF):
                fixed.append(byte)
                fixed.append(a if 0x80 <= a <= 0xBF else (0xA0 if a == 0x20 else a))
                fixed.append(b if 0x80 <= b <= 0xBF else (0xA0 if b == 0x20 else b))
                i += 3
                continue
        fixed.append(byte)
        i += 1
    return bytes(fixed)


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    if original.startswith("\ufeff"):
        original = original[1:]

    artifact_chars = set(_ARTIFACT_MAP.keys())
    if not any(c in artifact_chars for c in original):
        print("SKIP: không còn ký tự mojibake artifact; file đã sạch.")
        return

    buf = decode_mojibake(original)
    buf = fix_nbsp_loss(buf)

    # Pass 2: ký tự U+0080..U+00FF còn sót = single-mojibake (byte utf-8 gốc
    # hiển thị thành ký tự latin). Chuyển ngược về byte.
    fixed_chars = []
    for char in buf.decode("latin-1"):
        code = ord(char)
        if 0x0080 <= code <= 0x00FF:
            fixed_chars.append(char.encode("latin-1"))
        else:
            fixed_chars.append(char.encode("utf-8"))
    fixed = b"".join(fixed_chars).decode("utf-8", errors="replace")
    fixed = fix_contextual(fixed)

    mojib_before = sum(1 for c in original if 0x00C0 <= ord(c) <= 0x00FF)
    mojib_after = sum(1 for c in fixed if 0x00C0 <= ord(c) <= 0x00FF)
    print(f"mojibake chars: before={mojib_before}, after={mojib_after}", flush=True)

    checks = [
        "Đang chạy Local Admin. Bật AUTH_REQUIRED khi triển khai nhiều người dùng.",
        "Tạo Lô Mới",
        "Khách Hàng",
        "Thỏa Thuận & Bàn Giao",
        "Sổ Tay Kinh Nghiệm",
        "quản lý tài khoản, chỉ dành cho vai trò admin",
    ]
    all_ok = True
    for kw in checks:
        ok = kw in fixed
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'MISS'}] {kw}", flush=True)

    fixed.encode("utf-8")
    compile(fixed, str(TARGET), "exec")

    TARGET.write_text(fixed, encoding="utf-8")
    print("FIXED:", TARGET, flush=True)
    if not all_ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
