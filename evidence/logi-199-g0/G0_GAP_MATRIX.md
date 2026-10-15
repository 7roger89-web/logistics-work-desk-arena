# LOGI-199 — G0 Baseline & Gap Matrix (Owner Visual Fidelity Override 15/10/2026)

**Trạng thái:** `G0 PARTIAL` · `VISUAL_FIDELITY=FAIL` · `BUSINESS_PASS` không được tuyên bố trong tài liệu này
**Nguồn chuẩn (SHA-256 đã kiểm):** `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html` = `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`
**Checkpoint tích hợp:** `arena/d8927583-logistics-work-desk-arena` @ `3f42a77` (T0–T6, 113 commit trên `main`)
**Môi trường chụp hiện trạng:** Streamlit thật (`scripts/logi199_t6_staging_app.py`, mongomock sandbox, `AUTH_REQUIRED=false`), Chromium 131 headless, 1440×900 và 390×844. Đây là staging, không phải production.

## 1. Ảnh chuẩn (oracle) — `reference-html/`

| File | Trạng thái |
|---|---|
| `ref-01-journey-initial.png` | Journey toàn màn hình, chưa chọn node, nền giấy hải đồ, node nhỏ nối tuyến |
| `ref-02-node-bubble.png` | Chọn node PICKUP → bong bóng công việc gắn ngay cạnh node |
| `ref-03-task-popup.png` | Bấm công việc PK-04 → **modal giữa màn hình ~510px**, nền mờ; header có mã PK-04, tên node, chip trạng thái, nút đóng; các trường chính (thời điểm, người bàn giao, ghi chú, chứng từ đính kèm) ở trên; `Xem thêm chi tiết (người phụ trách, hạn & trạng thái)` gấp; banner lý do chưa đủ điều kiện hoàn thành; footer `Đóng · Lưu · Xác nhận hoàn thành` |
| `ref-04-mobile-initial.png`, `ref-04b-mobile-node.png` | Mobile 390 bản đồ là trung tâm, node lớn hơn, nút zoom nổi |
| `ref-05-finance-overlay.png` | Overlay "Hồ sơ & Tài chính" mở từ nút ở góc trên phải (**chụp, chưa phân tích chi tiết ở G0**) |

Ghi chú G0: bong bóng và popup đã được chụp từ cùng một luồng click (`ref-02` → `ref-03`). Font: bản HTML khai báo Be Vietnam Pro / IBM Plex Mono nhưng không có `@font-face`; quan sát trên ảnh là sans-serif gần Be Vietnam Pro, **chưa chứng minh font đã tải** (`document.fonts` chưa được kiểm trên bản HTML).

## 2. Hiện trạng app — `current-baseline/`

| File | Nội dung |
|---|---|
| `desktop-01-home.png` | Trang chủ |
| `desktop-02-lots-list.png` | Danh sách lô hàng |
| `desktop-03-journey-initial.png` | Journey T6-FCL mặc định: bản đồ **bị nhét cột ~340px** bên trái, dashboard thẻ trắng ("Shipment overview / Next action / Current / Documents / Finance") chiếm bên phải |
| `desktop-03b-journey-fit.png` | Sau Fit Journey: toàn bộ sơ đồ thu còn ~28%, chữ không đọc được |
| `desktop-04-node-selected.png` | Chọn node BOOKING: không có bong bóng công việc nổi trên bản đồ |
| `desktop-05-popup-workspace.png` | "Mở công việc" mở **panel bên phải kiểu tài liệu** (Công việc / Chứng từ), không phải popup ngắn gọn kiểu HTML |
| `mobile-01-journey.png` | Mobile: bản đồ kéo ngang nhưng node cắt mép, khối trạng thái/chip và bottom-tab kiểu app thường |

## 3. Bảng so sánh theo màn hình / thành phần

Đánh giá: ✅ khớp · ⚠️ gần nhưng lệch · ❌ sai · ⬜ chưa kiểm (chưa chụp đủ)

| Màn hình / thành phần | Bố cục | Font | Màu/nền | Kích thước/khoảng cách | Nút | Bảng | Popup | Tương tác | Kết luận |
|---|---|---|---|---|---|---|---|---|---|
| Journey desktop mặc định | ❌ map 340px + dashboard | ⬜ chưa xác minh tải font | ❌ nền lưới chấm thay vì giấy hải đồ | ❌ node quá nhỏ ở mặc định | ⚠️ Fit/+/−/Đọc rõ có nhưng vị trí khác | — | ❌ | ❌ không có bong bóng nổi | **FAIL** |
| Thanh thông tin trên Journey | ❌ nhiều dòng chip + card cảnh báo lớn | ⬜ | ⚠️ | ❌ cao hơn nhiều so với thanh gọn của HTML | — | — | — | — | **FAIL** |
| Node | ❌ thẻ trắng viền đỏ/xanh lớn, nhãn in hoa, chip "VẤN ĐỀ" | ⬜ | ⚠️ | ❌ | — | — | — | ✅ bấm được | **FAIL** |
| Bong bóng công việc | ❌ **chưa có** | — | — | — | — | — | — | ❌ | **FAIL** |
| Popup công việc | ❌ panel tài liệu bên phải; oracle là modal ~510px có trường chính + phần gấp + banner điều kiện | ⬜ | ⚠️ | ❌ | ⚠️ | — | ❌ | ⚠️ | **FAIL** |
| Journey mobile | ❌ bản đồ + chip + bottom-tab app | ⬜ | ⚠️ | ❌ node cắt mép | ⚠️ | — | ❌ | ⚠️ kéo được | **FAIL** |
| Shell chung (header, nav) | ❌ nhận diện "TRƯỜNG THÀNH" + tab lớn + thẻ trắng bo tròn kiểu app | ⬜ | ❌ nền xám bên ngoài, khung 1 thẻ lớn | ❌ | ⚠️ | — | — | — | **FAIL** |
| Trang chủ | ❌ dashboard thẻ | ⬜ | ❌ | ❌ | ⚠️ | — | — | ⬜ | **FAIL** |
| Danh sách lô hàng | ❌ | ⬜ | ❌ | ❌ | ⬜ | ⬜ | — | ⬜ | **FAIL** |
| Overlay Hồ sơ & Tài chính | ⬜ chưa chụp app | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | **CHƯA KIỂM** |
| Báo giá, Khách hàng, Tài chính, Công cụ, Admin, Report | ⬜ chưa chụp (21 route + chi tiết + modal) | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | **CHƯA KIỂM** |

## 4. Gap chính (xếp theo mức ưu tiên)

1. **Journey không map-first** — `component/src/components/ShipmentJourney.tsx` dùng `journey-split journey-split-small-map` (`index.css:117` `width:340px`). Comment "Owner 2026-10-13" trong code là quyết định **bị override** bởi 15/10. Đây là lỗi cốt lõi Owner đã nêu.
2. **Không có bong bóng công việc gắn node** — bản HTML: node → bong bóng → popup. App hiện: node → panel bên phải.
3. **Popup không theo mẫu** — app dùng panel tài liệu với tab Công việc/Chứng từ; HTML dùng modal ngắn, trường chính ở trên, phần phụ gấp.
4. **Nền và hình học node** — HTML: giấy hải đồ + node 1 dòng tiêu đề nhỏ, viền trái màu theo trạng thái. App: lưới chấm, thẻ lớn.
5. **Shell/Header** — HTML: header gọn 2 dòng + thanh thông tin. App: khối brand lớn + card cảnh báo + chip.
6. **Font chưa được xác minh** trên cả hai phía: cần kiểm `document.fonts` (status `loaded`) trước khi phủ app.

## 5. Quyết định OE_GATE

`Không bị over engineering chứ?`
- SIMPLER_PATH=YES: dùng HTML làm oracle, tái sử dụng `ShipmentJourney.tsx`, `JourneyMap.tsx`, `ui.tsx`, `index.css`, `shell.css`; không thêm framework/design system thứ hai.
- MATERIAL_PROGRESS=YES: G0 đã có oracle thật và hiện trạng thật; lỗi cốt lõi đã định vị đúng file/dòng.
- NECESSITY=YES: không thể nghiệm thu G2 nếu chưa có bong bóng + popup + mobile đúng mẫu.
- CORE_BEFORE_SUPPORT=YES: làm Journey (G2) trước các màn phụ; shell (G1) đi cùng Journey vì chung CSS.
- SMALLER_VERIFIABLE_SLICE=YES: lát tiếp theo là **G2 slice 1**: đổi Journey sang map-first 1440×900 + một node → bong bóng; chụp before/after cùng oracle.

`OE_VERDICT=DO_IT` cho G2 slice 1 · `DEFER_UNTIL_NEEDED` cho các màn hình G3–G4 cho tới khi G2 được Owner nhìn ảnh đầu tiên.

## 6. Blocker / rủi ro

- Không có `@font-face` trong HTML; cần nạp font thật (file font trong repo hoặc nguồn hợp lệ) rồi xác minh `FontFace.status==='loaded'` trong app.
- Chưa có reviewer độc lập; CI cũ không được dùng làm bằng chứng VISUAL_FIDELITY.
- Owner UAT: chưa mở. Không merge/deploy `main`.
- Không chạy `pytest` toàn bộ trong G0 (chỉ chụp hiện trạng); regression T1–T4 sẽ chạy ở G5.
