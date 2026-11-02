# LOGI-G15-PUBLISH-PICKUP-20261102 — preflight receipts

## 1. P2P law preflight (actor-own, this session)

```
P2P_LAW_SOURCE=LOCAL_PORTABLE
LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md (PROJECTION_DO_NOT_EDIT=YES, CANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md) | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b
```

- File bytes sha256: `75d4d1d589b3bfd4ef70a12a93878664766f65734075fd14f398a76a9fddde1e`
  (khác hash nội dung canonical ghi trong header là đúng thiết kế: header băm nội dung nguồn, không băm file projection).
- `AGENTS.md` tại checkout đã đọc: sha256 `d5ddf490c075bee461efb2f1e2f8078c07229044d3f1ca0a0aeadf1be3b47091`.
- Không thăm dò cross-repo để tạo lỗi fallback (`TARGET_PROJECT != LAW_SOURCE`).
- `docs/NEXT.md` (staging) đã đọc; Issue #263 OPEN đã đọc đầy đủ.

```
EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb
```

- Nguồn: `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json` (sha256 file `9b10fafe…`, `source_content_sha256=208c3ba4…`), 1 record ACTIVE, trigger khớp: `receipt`, `preflight`, `portable`, `consumption`.
- Bài học áp dụng: một law/capability chỉ "hoàn thành vận hành" khi actor thực thi đọc được, dùng được và có receipt gắn nguồn — áp dụng trực tiếp cho producer G1.5 (fixture `public_events` không phải producer, đúng WRONG_PASS của Issue).

## 2. Required skill consumption

```
p2p-skill-consumption-receipt/1
SKILL=debugging
PATH=.agents/skills/debugging/SKILL.md
EXPECTED_SHA256=4f8ef3752148eb28d16a9ead4b60afbc9017436fee65dc962b87707f40a6777e
ACTUAL_SHA256=4f8ef3752148eb28d16a9ead4b60afbc9017436fee65dc962b87707f40a6777e
SKILL_CONSUMPTION=LOADED
```

Chu trình skill đã áp dụng: Phase 1 capture symptom (grep: không có producer) → Phase 2 reproduce (test/DB cô lập) → Phase 3 owner (`_handle_shipment_transport_save`) → Phase 4 root cause (thiếu producer + thiếu action xác minh) → Phase 5 plan (SPEC_LOCK) → Phase 7 fix tối thiểu → Phase 9 verify (pytest + browser thật).

## 3. OE_GATE

Câu hỏi: **Không bị over engineering chứ?**

| Tiêu chí | Đánh giá |
|---|---|
| SIMPLER_PATH | Có đường đơn giản hơn "thêm collection/service/approval mới": tái dùng `public_events` + publisher Admin hiện có ⇒ chọn đường đó |
| MATERIAL_PROGRESS | Có: mở đúng chuỗi bị thiếu (staff → nguồn chờ → Admin xác minh → công bố → khách) |
| NECESSITY | Có: hiện không tồn tại bất kỳ writer nào cho `public_events`; không có đường nào khác để mốc Lấy hàng tới khách |
| CORE_BEFORE_SUPPORT | Có: chỉ làm producer + một action xác minh, không làm thêm UI/UX, filter, dashboard |
| SMALLER_VERIFIABLE_SLICE | Có: một công đoạn (pickup), một handler, một hàm verify, test file riêng + browser loop |

`OE_VERDICT=DO_IT` — lý do: đây là mắt xích còn thiếu duy nhất của chuỗi đã có; mọi thứ khác được tái dùng nguyên trạng, không thêm DB/service/framework/approval.

## 4. Branch gate

```
REPO=7roger89-web/logistics-work-desk-arena
TARGET_BRANCH=arena/ae5f9f47-logistics-work-desk-arena
KNOWN_STAGING_HEAD=d4c7365b3d99485321da2f40e836757535e50a01
FETCHED_HEAD=d4c7365b3d99485321da2f40e836757535e50a01   (git ls-remote --heads origin → khớp)
SESSION_BRANCH=arena/e8d51a0b-logistics-work-desk-arena  (host-fixed, không thể tạo/xoá nhánh khác)
BASE_AFTER_RESET=d4c7365b3d99485321da2f40e836757535e50a01
DIVERGENCE_VS_TARGET=0 0   (git rev-list --left-right --count origin/arena/ae5f9f47...HEAD)
BRANCH_GATE=PASS_VIA_SESSION_BRANCH_REBASED_ON_STAGING
```

Ghi chú trung thực: host chỉ cho phép push `arena/e8d51a0b-logistics-work-desk-arena`; không tạo được nhánh `task/263-*`.
Thay vì ENV_BRANCH_BLOCKED, nhánh phiên được **reset về đúng staging HEAD hiện hành** (không merge `main`, không force/reset staging, không chép control plane). `main` giữ nguyên `23c4e00f2b2d3c43b984db41e99f3f3b74e687e5`.

## 5. Environment

- Python 3.11.2, venv `/tmp/venv` (requirements.txt + pytest 9.2.0), mongomock 4.3.0, Streamlit 1.66.1.
- Chromium 131.0.6778.0 (`@sparticuz/chromium@131.0.1` từ `registry.npmjs.org`, NSS libs từ `al2023.tar.br`) + `puppeteer-core@23`, điều khiển thật.
- Không có `MONGO_URI`: app dùng transport `mongomock` cô lập (`views/logi_sandbox.py`), không chạm DB thật/Cloud.

## 6. Baseline (trước khi sửa) — HEAD `d4c7365`

```
COMMAND=/tmp/venv/bin/python -m pytest tests -q --continue-on-collection-errors
EXIT=1
RESULT=9 failed, 2377 passed, 45 skipped, 10 subtests passed in 114.96s
```

FAILED set (9): xem `baseline/failed-set.txt` (trùng khít sau khi sửa nếu không có lỗi mới).
SKIP set: `baseline/skips.txt`.
