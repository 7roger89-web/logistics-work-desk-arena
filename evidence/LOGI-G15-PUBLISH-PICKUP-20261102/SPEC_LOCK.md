## SPEC_LOCK — LOGI-G15-PUBLISH-PICKUP-20261102 (khóa kỹ thuật trước khi sửa mã)

Đo tại `arena/ae5f9f47-logistics-work-desk-arena` = `d4c7365b3d99485321da2f40e836757535e50a01` (staging hiện hành).
Session branch `arena/e8d51a0b-logistics-work-desk-arena` được reset về đúng HEAD staging này trước khi đo (không merge `main`, không force/reset nhánh khác).

### 0. Trạng thái nguồn đo được (không suy đoán)

| Sự kiện | Bằng chứng tại HEAD staging |
|---|---|
| Không có producer nghiệp vụ nào ghi `public_events` | `grep -rn "public_events" core views` → 11 dòng, **toàn bộ là đọc**; chỉ `tests/**` có `insert_one/insert_many` (fixture). Không có nhánh `insert/update` nào trong app code |
| Publisher Admin đã có | `core/customer_portal_publish.py::list_verified_sources` (dòng 77), `publish_verified_sources` (dòng 129) |
| Reader công bố đã có | `core/customer_portal_sources.py::read_approved_sources` (dòng 81), `core/customer_portal.py::load_customer_dashboard` (dòng 220) |
| Allowlist khách đã có | `core/hexa_customer_publication.py::_public_events` (dòng 82) yêu cầu `verified is True`, `verified_at`, `visibility=CUSTOMER`, `public_title`, `occurred_at`, đúng `customer_id`+`shipment_id`, đúng pin version |
| Màn công bố Admin đã có | `views/customer_dashboard.py::_render_admin_publication_control` (dòng 391), gọi từ `views/web_app.py:185` → `render_owner_portal_access_control` |
| Đường ghi mốc Lấy hàng của staff đã có | React `component/src/components/ShipmentOperations.tsx::saveLegs` → `dispatch("shipment_transport_save", {shipmentId, transportLegs})` → `views/logi_view_model.py::_handle_shipment_transport_save` (dòng 3439) → `core.database.save_shipment_atomic` |
| Fact pickup canonical | `core/shipment_operations.py::compatibility_facts` (dòng 365): `pickup_leg` = chặng `Truck` **đầu tiên**; `core/shipment_journey.py` node `pickup` `done=bool(pickup_leg.atd)` |

**Khoảng trống đã xác nhận:** chuỗi hiện có là `public_events (verified) → publisher → manifest → portal`. Thiếu đúng hai mắt: (a) staff ghi mốc Lấy hàng **không** sinh bản ghi nguồn chờ xác minh; (b) Admin không có thao tác xác minh nguồn chờ (`list_verified_sources` chỉ đọc `verified=True`, không ai set được `verified`). Vì vậy mọi bằng chứng G1.5 trước đây dựa trên fixture `public_events` chèn sẵn.

### 1. Actor, entrypoint, handler

- **Producer**: staff có `shipment_edit` (`core/auth.py::ROLE_PERMISSIONS`: `admin`, `sale`, `support`, …) tại `/lo-hang/<id>?tab=van-tai` (mục “Chặng vận chuyển”, trường `ATD`) → `shipment_transport_save` → `_handle_shipment_transport_save`.
- **Verifier/Publisher**: `admin` tại khối “Cổng khách hàng — duyệt và công bố tiến độ/chứng từ” (`_render_admin_publication_control`) ngay trong app Streamlit hiện có.
- **Reader**: khách đã allowlist `customers.portal_access_email` → `build_customer_principal` → `load_customer_dashboard` → `views/customer_dashboard.py`.

### 2. Nguồn dữ liệu, schema, version

- Nguồn fact: `shipments.data["1.2"].transport_legs[]` (chặng `Truck` đầu tiên: `atd`, `etd`, `origin`, `units[]`). Không đọc `public_events` để suy ra fact.
- Bản ghi nguồn chờ: collection **đang có** `public_events` (không thêm collection/DB/service):
  `{id, version, customer_id, shipment_id, stage_id="pickup", kind="PICKUP", public_title, occurred_at, visibility="CUSTOMER", verified, verified_at, verified_by, content_sha256, recorded_at, recorded_by, source="STAFF_PICKUP_ATD", is_deleted}`
  - `id` = `pickup-<shipment_id>` (ổn định; làm sạch để không chứa `.`/`$`).
  - `version` = 16 hex đầu của SHA-256 nội dung công khai chuẩn hóa (`stage_id`, `occurred_at`, `public_title`, `customer_id`, `shipment_id`). Nội dung không đổi → cùng version (không bắt Admin xác minh lại); nội dung đổi → version mới và `verified` **tự về False**.
  - `content_sha256` đầy đủ để Admin xác minh đúng nội dung, không chỉ đúng ID.
  - `occurred_at` = `atd` (ngày ISO `YYYY-MM-DD`), `public_title` = “Đã lấy hàng” (chỉ text công khai, không biển số/tài xế/giá/ghi chú nội bộ).
- Công bố: **tái dùng nguyên** `customer_publications` + `shipments.customer_publication_version` + `approved_content_sha256` (không đổi schema, không đổi publisher).

### 3. Quyền và trạng thái trước/sau công bố

| Bước | Ai | Trạng thái bản ghi nguồn | Khách thấy? |
|---|---|---|---|
| Lưu ATD | staff `shipment_edit` | `pending` (`verified=False`) | Không |
| Xác minh | `admin` only | `verified=True`, `verified_at`, `verified_by` giữ nguyên `version`+`content_sha256` | Không (chưa có manifest pin) |
| Công bố | `admin` only, publisher hiện có | manifest `PUBLISHED`, pin `{event_id: version}` | Có, sau reload |
| Sửa ATD sau công bố | staff | version mới → manifest cũ không khớp → lot bị **từ chối** (fail-closed), không hiện dữ liệu sai | Không |

RBAC: producer chỉ chạy sau khi `can_operate_business("shipment_edit")` đã qua (guard sẵn có của handler); verifier/publisher dùng `_admin()` sẵn có; reader giữ nguyên `build_customer_principal` + tenant check. Không nới quyền nào.

### 4. WRONG_PASS (phải FAIL dù test khác xanh)

1. Fixture tự `insert_one` vào `public_events` với `verified=True` rồi gọi publisher → coi như “producer chạy”. **Test nghiệm thu phải bắt đầu từ `dispatch("shipment_transport_save")` của staff và đối chiếu bản ghi DB do chính thao tác đó tạo ra, trước khi Admin xác minh.**
2. Chỉ kiểm tra `ok=True` của handler mà không đọc lại `public_events` → không chứng minh nguồn chờ tồn tại.
3. Cho Admin bấm “xác minh” một bản ghi đã bị sửa nội dung nhưng giữ version (sửa tay DB) → phải bị từ chối bằng `content_sha256`.
4. Công bố `version` cũ sau khi staff sửa ATD → phải bị từ chối.
5. Cho `sale`/`support`/`viewer` gọi xác minh hoặc công bố → phải bị từ chối.
6. Đọc portal của khách B khi A đã công bố → phải rỗng với dữ liệu A.

### 5. Positive / negative tests (sẽ thêm)

Positive: staff `shipment_transport_save` (Truck leg `atd`) → `ok`, readback `atd` đúng, **và** `public_events` có đúng 1 bản ghi `pickup-<lot>` `verified=False`, đúng `customer_id`/`shipment_id`, `occurred_at=atd`; Admin xác minh đúng id+version+hash → `verified=True`; publisher hiện có công bố → khách A `load_customer_dashboard` + `customer_journey.build_lot_model` thấy node Lấy hàng `COMPLETED` với “Đã lấy hàng” + ngày; khách B rỗng.

Negative: trước khi công bố khách A không thấy mốc; nguồn chưa verified không công bố được; sửa ATD sau xác minh → công bố bị từ chối và lot bị từ chối khi đọc; xác minh sai version / sai hash / sai tenant / role không phải admin → từ chối; payload khách không chứa `INTERNAL`, `finance`, giá, ghi chú, biển số, `_id`, tên collection.

### 6. Lệnh nghiệm thu thực tế

```
/tmp/venv/bin/python -m pytest tests/test_customer_portal_sources_g15.py tests/test_customer_portal_publish_g15.py \
  tests/test_customer_portal_g15_independent_challenge.py -q
/tmp/venv/bin/python -m pytest tests/test_g15_pickup_producer.py -q          # file mới của slice này
/tmp/venv/bin/python -m pytest tests -q --continue-on-collection-errors      # trước/sau, so tập FAILED/ERROR/SKIP
python scripts/check_router.py ; ruff check .
```
Browser: `streamlit run` runtime cô lập (mongomock, `MONGO_URI` rỗng) + Chromium 131 thật, desktop 1440×900 và mobile 390×844: staff lưu ATD → Admin xác minh + công bố trên UI → khách A reload thấy mốc, khách B không thấy; ảnh + JSON khẳng định lưu ở `evidence/LOGI-G15-PUBLISH-PICKUP-20261102/`.

### 7. Phạm vi

Chỉ công đoạn Lấy hàng. Không thêm DB/service/collection/framework/approval mới, không đổi schema publisher, không mở sang công đoạn khác, không sửa `main`, không ghi Cloud/production, không merge/deploy.
