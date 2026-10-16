# PR #205 — Historical SELL không được trở thành BUY COST

Ngày: **2026-10-16** · Phạm vi: **sửa finding review, không mở rộng tính năng**.

- PR hiện có: [#205](https://github.com/7roger89-web/logistics-work-desk-arena/pull/205), giữ **Draft**.
- Reviewed head/parent của repair: `2c77bee0d563c6c3481792a3b6e603cc0365a343`.
- Branch duy nhất: `arena/63b3ec32-logistics-work-desk-arena`; append commit và push thường, không force push.
- **Kết luận: PROVEN trong phạm vi regression và app sandbox đã kiểm tra; UAT_PENDING.** Không phải chứng nhận release/production.

## 1. Đã sửa đúng ranh giới SELL/COST

| Nguồn kiểm thử | Kết quả trong app thật | Giá bán của quote mới |
|---|---|---|
| QUOTE: SELL 40.000.000 VND, không cost | Vẫn hiện để so sánh; nhãn **“Giá đã báo/dự kiến — không phải giá vốn”**; nút chọn bị khóa; không thêm phí | Không tự điền |
| ACTUAL: SELL 40.000.000, cost UNKNOWN | Cost vẫn UNKNOWN, không thành SELL 40 triệu **hoặc số 0**; nút chọn bị khóa | Không tự điền |
| ACTUAL: SELL 40.000.000, cost thật 32.000.000 | Chỉ chọn **32.000.000 VND/CONT**, giữ shipment/line ID và provenance `finance.actual.cost` | **Trống**, chưa xác nhận |
| INPUT_RATE: BUY 31.800.000 VND, nguồn hợp lệ | Chọn **31.800.000**; backend rehydrate/khóa cost từ snapshot/row thật trong sandbox | **Trống**, chưa xác nhận |

Cảnh báo hết hạn/chưa rõ hiệu lực vẫn hiện. Không coi giá cũ là giá hiện hành. CostCheck vẫn tìm kiếm, xếp hạng, so sánh và mở quote từ cost thật; nguồn SELL/UNKNOWN không còn đường vòng qua quote editor cũ.

## 2. Thay đổi nhỏ, dùng lại authorities hiện có

- `costHistory.ts`: thêm `priceBasis`/`priceProvenance`; QUOTE vẫn giữ giá SELL cho comparison; ACTUAL chỉ đọc `cost`, không fallback `price`/`amount`. Một guard chung kiểm tra ngữ nghĩa, nguồn, số hữu hạn không âm, unit, currency hỗ trợ và ID nguồn INPUT_RATE. Currency UNKNOWN không bị gán VND để cộng tổng.
- `ExcelQuoteWorkspace.tsx`: hiện lý do không được chọn tại dòng giá; kiểm tra cả nút và handler; copy cost/provenance, luôn để `sell_unit` trống.
- `CostCheck.tsx`/`SalesQuotes.tsx`: áp dụng cùng guard tại đường chuyển tham chiếu sang quote cũ. Không thay thuật toán ranking/applicability.
- Browser lần đầu phát hiện reader chuẩn hóa `cost=null` thành `0`. Sửa bằng **opt-in `preserve_unknown_cost=True` ở nhánh component read hiện có**; dùng lại `to_decimal`, giữ cost UNKNOWN và currency nguồn trước default VND. Mặc định normalizer/writer không đổi; Python financial arithmetic không đổi.
- Không thêm kho giá, collection, API/server thứ hai, price engine, dependency, migration hay chỉnh Journey. Ba bước, shared styles/primitives và dữ liệu bán/lợi nhuận lịch sử không bị viết lại. Build lại bundle tracked.

## 3. Bằng chứng mới — không dùng lại PASS cũ

Toàn bộ bằng chứng lượt sửa nằm tại [`evidence/pr205-historical-sell-buy-cost/`](../evidence/pr205-historical-sell-buy-cost/README.md), tách khỏi `evidence/excel-quote-import-v1/`.

| Kiểm tra thực chạy sau sửa | Kết quả | Bằng chứng |
|---|---:|---|
| Python: raw read truth + Excel import + cost intelligence | **73 PASS**; gồm **17 regression read-truth mới** | `python-regression.txt` |
| Python: finance logic và actual-entry compatibility | **31 PASS**, 2 catalog tests baseline deselected | `finance-compatibility.txt` |
| JS semantic regression mới | **7 nhóm PASS**, gồm 4 ca bắt buộc | `unit-regression.txt` |
| Matcher hiện có / parser hiện có | **PASS / 20 checks PASS** | `existing-matcher.txt`, `existing-parser.txt` |
| Built-bundle DOM quote/CostCheck, steps 1–8c | **13 checks PASS**; Journey không chạy trong slice này | `existing-costcheck-dom.txt` |
| Typecheck / build / bundle scan | **PASS**; 0 executable `process` references | `typecheck.txt`, `build.txt`, `bundle-scan.txt` |
| Playwright trên app Streamlit–React–C1 thật | **11 checks PASS**, desktop 1440×900 / mobile 390×844 | `browser.txt`, `browser-results.json`, 6 ảnh |
| Toàn bộ bản ghi lịch sử dùng trong browser | Hash trước = sau; SELL 40 triệu và cost UNKNOWN/32 triệu nguyên trạng | `history-integrity.json` |

Hai nhóm Python PASS cuối là **104 test khác nhau**, không cộng thêm các test trùng của lượt exploratory.

Runtime: app hiện có, native component channel; historical fixtures lưu đúng schema trong **SANDBOX_STAGING/mongomock**, supplier rates nhập/lưu qua UI Cost Intelligence. Không inject view-model, không mock browser routes, không dựng demo/app thay thế. Fixture workbook dùng generator SYNTHETIC đã có.

Ảnh tiêu biểu:
- [QUOTE chỉ so sánh, không được chọn cost](../evidence/pr205-historical-sell-buy-cost/01-quote-sell40-comparison-only-1440x900.png).
- [ACTUAL UNKNOWN không fallback SELL/0](../evidence/pr205-historical-sell-buy-cost/02-actual-unknown-no-sell-fallback-1440x900.png).
- [ACTUAL 32 triệu, SELL mới trống, có provenance](../evidence/pr205-historical-sell-buy-cost/03-actual-cost32-new-sell-blank-1440x900.png).
- [INPUT_RATE 31,8 triệu, SELL mới trống](../evidence/pr205-historical-sell-buy-cost/04-input-rate318-new-sell-blank-1440x900.png).
- [Nhãn không-phải-cost trên mobile](../evidence/pr205-historical-sell-buy-cost/06-mobile-quote-not-cost-390x844.png).

### Giữ lại failure evidence, không gọi toàn suite green

- `regression-before.txt`: reviewed head trả SELL 40 triệu khi ACTUAL cost UNKNOWN.
- `real-read-before.txt` và `attempt-1/`: lần browser đầu tìm ra UNKNOWN bị reader biến thành 0; regression + read-only opt-in đã sửa ranh giới này.
- `attempt-2/`: bốn ca số tiền/SELL đã đúng, nhưng test kỳ vọng string `rows.amount` sau preview. C1 chủ động thay note phía browser bằng provenance supplier/snapshot/row đáng tin cậy. Chỉnh assertion theo IDs canonical, không đổi authority sản phẩm để làm test xanh.
- Exploratory Python: **84 PASS / 2 FAIL** tại catalog shape (`id`/`source` bổ sung) và group literal `DỊCH VỤ XNK`. Hai lỗi tái hiện độc lập trên nguyên reviewed head; xem `baseline-existing-catalog-failures.txt`. Không sửa ngoài finding. Compatibility cuối chạy 28 actual-entry tests còn lại + 3 finance tests.
- Không claim full Journey DOM/full repository suite PASS. Evidence cũ và lỗi baseline cũ vẫn giữ nguyên.

## 4. Các gate vẫn mở

- **Workbook Lục Giác thật: NOT_RUN / chưa acceptance.** SYNTHETIC không phải bản gốc, giá hiện hành hoặc căn cứ pháp lý.
- **MongoDB staging thật: NOT_RUN / chưa acceptance.** Mongomock không chứng minh disk durability, transaction/replica hay restart của Mongo thật.
- **Owner UAT: UAT_PENDING.** Probe URL public trả `ERR_CONNECTION_CLOSED`; không có đường Owner test đã xác minh. Port nội bộ chỉ phục vụ automation và đã dừng sau test. Không hướng Owner tới localhost 9501/9521.
- Không merge main, không deploy, không kết nối production DB. PR tiếp tục Draft.

## 5. Reproduce trong sandbox kỹ thuật

Không dùng các lệnh này trên production hoặc trên môi trường có Mongo URI thật. Test launcher có guard từ chối real Mongo trước khi seed.

```bash
node tests/component/unit_quote_cost_provenance.mjs
LOGI_COSTCHECK_ONLY=1 node tests/component/dom_acceptance_quote_cost_workflow_ux_01.mjs
.venv/bin/python -m pytest -q tests/test_quote_cost_reference_truth.py tests/test_excel_quote_import_v1.py tests/test_cost_intelligence.py tests/test_cost_intelligence_vietnamese_rates.py
npm --prefix component run typecheck
npm --prefix component run build
npm --prefix component run scan
```

Để chạy browser, khởi động test launcher trên một process riêng với `LOGI_PR205_COST_REGRESSION=1 AUTH_REQUIRED=false`, `streamlit run tests/component/quote_cost_sandbox.py --server.address 0.0.0.0 --server.port 9521 --server.fileWatcherType none --server.enableCORS false --server.enableXsrfProtection false --browser.gatherUsageStats false`; chạy `tests/component/browser_quote_cost_provenance.mjs` với Playwright/Chromium sandbox tương ứng, rồi dừng process. Đường nội bộ trong log **không phải Owner test URL**.

## 6. Reconciliation

`INITIAL_PLANNING_CLASSIFICATION: UIUX` · `FINAL_ROUTING_CLASSIFICATION: UIUX` · `BROWSER_CAPABILITY=PLAYWRIGHT` · `EVIDENCE_LEVEL=RUNTIME_VISUAL_REVIEW`.

Contract nhẹ: giữ thiết kế ba bước/primitives, làm rõ SELL ≠ COST bằng chữ và trạng thái disabled, có nguồn/đơn vị/loại tiền, SELL mới trống. Đã đọc ảnh render desktop/mobile; không claim chứng nhận WCAG hay Owner-device.

**Không bị over engineering chứ?** SIMPLER_PATH=YES; MATERIAL_PROGRESS=YES; NECESSITY=YES; CORE_BEFORE_SUPPORT=YES; SMALLER_VERIFIABLE_SLICE=YES. `OE_VERDICT=DO_IT`: metadata/guard dùng chung và pass-through UNKNOWN trên đúng nhánh đọc; không thêm hệ thống định giá.

`LEARNING_RECONCILIATION=CANDIDATE`: khi tái sử dụng giá lịch sử, kiểm chứng ngữ nghĩa nguồn và toàn đường đọc thật; unit fixture giữ null không đủ nếu normalizer thực biến null thành 0. Trigger: historical price → buy-cost selection. Evidence: pre-fix regression, `attempt-1/`, 17 read-truth regressions, final browser 11 PASS. Chỉ là candidate có bằng chứng; không tự promote vào law/skill/shared experience.

**Stop condition:** finding đã sửa và chứng minh trong scope trên; chỉ bàn giao append commit trên PR Draft #205, không mở thêm tính năng.
