# Báo cáo xác minh false-done đợt 2 — P2P_LAW_PREFLIGHT + OE_GATE

**Ngày:** 2026-10-18  
**Branch:** `arena/da9aa3db-logistics-work-desk-arena` @ 51422c9  
**Scope:** Chỉ sửa file đã liệt kê, không đổi cấu trúc stage hay hình học map, dùng facts/writer hiện có. Mỗi lỗi có test âm/dương trong `tests/test_false_done_batch2_negative.py` (17 tests, 1 skipped khi thiếu streamlit). STOP khi test xanh, không merge/deploy.

---

## P0 — Rào chắn pháp lý / hiển thị

### 1) `component/src/components/JourneyBubble.tsx:45-50` — tách “có tệp” khỏi “chứng từ đã chấp nhận”

**Kết quả xác minh:** **[CẦN XÁC MINH] — Không phải lỗi hiện tại, không có file riêng.**

- `grep -rn JourneyBubble` toàn workspace rỗng. `git log --all --diff-filter=A -- "*JourneyBubble*"` rỗng. `ls component/src/components` chỉ có `ShipmentJourney.tsx` (897 dòng), `JourneyMap.tsx` (143 dòng), `JourneyQuickPanel.tsx`.
- Logic bubble thực tế nằm trong `ShipmentJourney.tsx` (`ModuleStepButton`/`ModuleCard`/`SeaExportFacts`) và `JourneyMap.tsx`.
- Kiểm tra `ShipmentJourney.tsx`:
  - `ModuleStepButton` render `META[node.state]` (COMPLETED/CURRENT/WAITING/PROBLEM/UPCOMING) — state từ backend `node.state`, **không** từ `documentIds.length`.
  - `files = s.attachments?.filter(f => n.documentIds.includes(f.id))` chỉ để hiển thị số tệp và nút “Đã có tệp”, không suy `completed`.
  - `WorkModuleStepPanel`: `const done = Boolean(step?.completed) || node.completed;` — completed là business fact đã lưu (ai/khi nào), không từ upload. Thông báo “Tệp đã tải lên không tự xác nhận bước này.”
  - `JourneyMap` hiển thị `📄 {n.documentIds.length}` và `⚠ {n.blockers.length}` nhưng `data-state` và màu từ `n.state`, không từ file count. `core/work_modules.py:696` đã tách `completed = step.completed` khỏi `documentIds` filter.
- **Kết luận:** Hiện đã tách. Nếu spec yêu cầu file riêng, cần tạo `JourneyBubble.tsx` mới từ `ShipmentJourney` bubble logic với guard `documentAccepted` thay vì `files.length>0`. Không sửa logic map hình học. Đánh dấu [CẦN XÁC MINH] để không đụng nhầm.

**Test:** Không thêm file mới để tránh tạo stage/map mới; xác minh bằng `grep documentIds` (6 vị trí) và đọc `ShipmentJourney` 600-750. Nếu cần, có thể khôi phục file cũ từ ZIP `cfe20232` và áp tách `const done = Boolean(step?.completed)` thay `files.length>0`.

---

### 2) `core/shipment_document_workflow.py:514-525` — tách `GNT_GENERATED` khỏi `TAX_PAID`

**Trước:** `elif gnt.get("done") or document: STATE_COMPLETE "Giấy nộp thuế đã được tạo cho lô."` — GNT tồn tại ⇒ coi như đã nộp thuế.

**Sau (đã sửa):**
```python
tax_paid = bool(gnt.get("taxPaid") or gnt.get("taxPaidAt") or gnt.get("paidAt"))
has_gnt_doc = bool(gnt.get("done") or _mapping(gnt.get("document")))
if not gnt_gate["allowed"]: MISSING
elif tax_paid: COMPLETE "Đã nộp thuế nhập khẩu (có bằng chứng thanh toán)."
elif has_gnt_doc: READY "Đã tạo GNT, chờ chứng từ nộp thuế — chưa có bằng chứng đã nộp."
elif noPayable: NOT_APPLICABLE ...
```

- **Fact cho “đã nộp”:** `gnt.taxPaid` boolean, `gnt.taxPaidAt` / `paidAt` ISO date (persisted tại `data[2.4].gnt.taxPaid` / `tax_paid_at`, đọc qua `_gnt_projection` mới thêm `taxPaid`/`taxPaidAt` từ `gnt_customs`/`customs`). Dùng writer hiện có (`shipment_field_save` qua `data[2.4].gnt`), không thêm engine.
- **Tách rõ:** `done/document` ≠ `taxPaid`. UI `CustomsImportQuickPanel` đã honest “Thuế đã nộp: Chưa có bằng chứng” — nay workflow cũng honest.

**Test âm/dương:**
- `test_gnt_document_does_not_mean_tax_paid` — GNT done nhưng `taxPaid:false` ⇒ không COMPLETE, reason chứa “GNT”.
- `test_tax_paid_fact_makes_complete` — `taxPaid:true` ⇒ COMPLETE.
- `test_tax_paid_via_paidAt_also_complete` — `paidAt` date ⇒ COMPLETE.
- Trước sửa, test 1 FAIL (COMPLETE), sau sửa PASS.

---

### 3) `component/src/components/JourneyQuickPanel.tsx:52` — chỉ hiện legal importer đã resolve, thiếu thì UNKNOWN

**Trước:** `{s.importInfo.receiver || s.customer || 'Chưa có thông tin'}` — fallback sang người nhận/Customer khi chưa có legal importer.

**Sau (đã sửa):** `{s.commercialFlow?.legalImporterName || 'UNKNOWN'}`

- **Căn cứ:** `s.commercialFlow` là projection từ `core/shipment_document_workflow` + `project_commercial_flow` (legalImporterKind/TaxCode, `company.tax_or_legal_code` không phải `legal_code`). `receiver` là consignee, `customer` là khách hàng, không phải pháp nhân đứng tờ khai. Spec yêu cầu “chỉ hiện legal importer đã resolve”.
- **Hiển thị thiếu:** `UNKNOWN` (theo spec), không bịa EXW hay tên khách. Styling giữ nguyên.

**Test:** `test_legal_importer_not_customer_fallback` kiểm tra không còn `receiver || s.customer`, có `legalImporterName` và `UNKNOWN`.

---

## P1 — Yêu cầu biển, xe, chứng từ, writer

### 4) `core/shipment_journey.py:188-202` `sea_requirement` — LCL chỉ cần SI, không cần VGM

**Trước:** `for key,label in (('si_status','SI'),('vgm_status','VGM')): if !=ACCEPTED return` — luôn yêu cầu cả SI lẫn VGM, sai cho LCL (hàng ghép, container do hãng chủ, VGM là trách nhiệm carrier).

**Sau (đã sửa):**
```python
load_model = profile.get('loadModel')
required = (('si_status','SI'),) if load_model=='LCL' else (('si_status','SI'),('vgm_status','VGM'))
```
- Đồng thời sửa node `si-vgm` trong `build_journey` (đã sửa):
  - `is_lcl = profile.get('loadModel')=='LCL'`
  - `done = (si=='ACCEPTED') if is_lcl else (si==vgm=='ACCEPTED')`
  - `label = 'SI' if is_lcl else 'SI / VGM'`, `categories = ('si',) if is_lcl else ('si','vgm')`

**Test:** `test_lcl_requires_only_si` (SI ACCEPTED + VGM UNKNOWN ⇒ None), `test_fcl_requires_both...` (FCL cùng input ⇒ VGM block), `test_lcl_missing_si_still_blocks`, `test_lcl_si_vgm_node_done` (LCL node done với chỉ SI).

---

### 5) `views/logi_view_model.py: _handle_sea_facts_save` ~2953 — chặn VGM cho LCL

**Trước:** Chỉ kiểm tra `MAIN_CARRIAGE in scope` cho `si_/vgm_`, không phân biệt LCL.

**Sau (đã sửa):**
```python
if profile.get("loadModel") == "LCL" and any(k.startswith("vgm_") for k in fields):
    return out(False, "LCL là hàng ghép — không yêu cầu VGM riêng, chỉ cần SI.")
```

- Giữ `si_status` cho LCL, chỉ chặn `vgm_*`. Dùng writer hiện có, không thêm route.

**Test:** `test_writer_rejects_vgm_for_lcl` — file chứa `LCL` + `vgm_`, runtime (khi có streamlit) tạo lot LCL rồi `shipment_sea_facts_save {vgm_status:ACCEPTED}` ⇒ `ok:false` và error chứa LCL. Trong env thiếu streamlit, chỉ kiểm file (pass, skipped runtime).

---

### 6) `core/shipment_journey.py:99` — pickup completed theo `atd` — **[CẦN XÁC MINH] Không phải false-done**

**Hiện:** `add('pickup', ..., done=bool(pickup.get('atd')))`

- **Cơ sở:** `operational.pickup_leg` từ `compatibility_facts` (legs canonical), `atd` là **Actual Time of Departure** sau khi bốc xếp, khác `etd` (dự kiến). Xe không thể rời điểm lấy hàng nếu chưa bốc hàng xong (ngoại trừ lỗi nhập liệu). Đây là bằng chứng vận hành, không phải suy từ lịch.
- **Kết luận:** Không tách `atd` khỏi “đã lấy hàng” — `atd` chính là bằng chứng đã lấy. Đánh dấu [CẦN XÁC MINH] để không đổi thành yêu cầu thêm ảnh biên bản.

**Test dương:** `test_pickup_completed_uses_atd` — atd tồn tại ⇒ completed True.

---

### 7) `core/shipment_journey.py:104-106` — `customs-export` không có đường `completed` dù đã thông quan — **[CẦN XÁC MINH] Hiện honest, thiếu authority**

**Hiện:** `add('customs-export', ..., done=False, evidence=f"Tờ khai: {decl}")` — chỉ ghi nhận tờ khai, không đánh completed. Note: *A declaration number proves registration, not clearance completion.*

- **Xác minh:** Chưa có field `export_clearance_at` / `export_customs_status` trong `SEA_FACT_FIELDS` hay `persisted_facts`. Không thể suy `completed=True` từ `china_export_decl_no` — đúng như test `customs-import` (declaration != clearance, `tk_no` + `customs_status`). Hiện không đánh completed là honest.
- Nếu muốn có đường completed, cần thêm fact mới `data[1.2].sea_export.export_clearance_at` (hoặc `clearance_status=ACCEPTED`) và writer `normalize_sea_facts`. Không thêm trong đợt này để giữ “chỉ sửa file liệt kê, không thêm stage”. Đánh dấu [CẦN XÁC MINH].

**Test:** `test_customs_export_not_completed_by_declaration_alone` — decl tồn tại nhưng completed False, evidence chứa “Tờ khai”.

---

### 8) `core/shipment_journey.py:123` — `TRANSIT` `done=bool(atd and ata)` — **[CẦN XÁC MINH] Đã đúng**

**Hiện:** `add('transit', ..., done=bool(atd and ata), evidence=f"ATD: {atd}", deadline=eta)` và `current = 'arrival' if ata else 'transit' if atd else ''`

- `done=True` khi cả ATD lẫn ATA ⇒ transit đã **kết thúc** (tàu đã đến), `current` là `arrival`, không phải “đang vận chuyển”. Khi chỉ có ATD, `done=False`, `current='transit'` ⇒ đang trên đường. Đã tách “đã kết thúc” khỏi “đang ở”.
- Note trong file: `Position is separate from unresolved earlier work. ETA/past ETD are NEVER evidence that a ship departed or arrived.`

**Test:** `test_transit_done_means_ended` (ATD+ATA ⇒ transit+arrival done, current arrival), `test_transit_current_when_only_atd` (chỉ ATD ⇒ transit not done, current transit).

---

### 9) `core/shipment_execution_profile.py:937/944/951/955/963/967/985/1000` — `done=True` khi có scope/chứng từ — **[CẦN XÁC MINH] Không phải false-done theo định nghĩa stage**

**Các dòng:**
- 937 `ORIGIN_PICKUP done=bool(pickupTruckType/trucks)`
- 944 `EXPORT_HANDLING done=True`
- 951 `ORIGIN_HANDOFF done=True`
- 955 `CROSS_BORDER done=True`
- 963/967 `MAIN_CARRIAGE done=True` (scope hoặc `main_documents`)
- 985/1000 `SEA/AIR_DOCUMENTS done=True` khi `NOT_OWNED` dù thiếu mbl/hbl
- 1030 `SEA_CONSOLIDATION done=True` (LCL), 1038 `ROAD_CONSOLIDATION done=True` (LTL)

**Xác minh:**
- `derive_stages` doc: *“The RELEVANT operational stages of THIS shipment, each with its reason. A stage appears only when the profile makes it relevant... Nothing else is ever shown”*. `done` cho scope-stage ở đây nghĩa là **“profile đã đủ dữ liệu để định nghĩa stage này, không còn thiếu facts để dựng hồ sơ”**, **không phải** “công việc vận hành đã xong”. Hoàn thành vận hành được đo ở `journey` nodes (`atd`/`ata`/`customs_status`/`is_delivered`), không ở execution profile.
- Ví dụ:
  - `ORIGIN_PICKUP` với `pickupTruckType` — `done=True` cho **nhu cầu lên kế hoạch xe**, không phải “hàng đã rời kho”. Bằng chứng rời kho là `journey.pickup.atd` (đã tách ở §6).
  - `EXPORT_HANDLING`/`ORIGIN_HANDOFF`/`CROSS_BORDER`/`MAIN_CARRIAGE` — `done=True` khi scope được xác nhận, stage đã “relevant”, prompt rỗng nên không phải blocker; `nextAction` vẫn ưu tiên `LOAD_MODEL_REQUIREMENT` (container/truck) và các `missing` thực sự (VD `SEA_DOCUMENTS` khi `owns_main` thiếu booking/mbl).
  - `SEA_DOCUMENTS` khi `NOT_OWNED` (`REASON_PERSISTED_FACT_DEPENDENCY`, `done=True`, `missing=""`) — “chặng ngoài scope, chứng từ chỉ là evidence tham chiếu, không phát sinh task Trường Thành”. Nếu thiếu mbl/hbl mà vẫn đánh `missing` sẽ tạo false task. Test `test_a_sea_document_stage_is_only_demanded_when_the_carriage_is_ours` khẳng định hành vi này là đúng (theirs: carrier Maersk nhưng booking rỗng, vẫn `done=True`, `nextAction != SEA_DOCUMENTS`).
  - `SEA_CONSOLIDATION`/`ROAD_CONSOLIDATION` — LCL/LTL không sở hữu container/xe nguyên, nên `done=True` là đúng (không yêu cầu số container).

**Kết luận:** Không đổi `done` thành `False` + prompt cho các scope này, vì sẽ biến “định nghĩa hồ sơ” thành “việc phải làm”, làm sai `nextAction` và phá test `LOGI_SHIPMENT_EXECUTION_PROFILE_01` (VD `test_a_sea_document_stage...`, `test_sea_lcl_never_demands...`). Đánh dấu **[CẦN XÁC MINH]**.

**Test dương mới (trong file):**
- `test_export_handling_scope_means_relevant_not_operationally_done` — EXPORT_HANDLING với scope CIF ⇒ done True, missing "".
- `test_origin_handoff...`, `test_sea_documents_not_owned...`, `test_pickup_vehicle_sufficiency` — đều assert `done True` là honest cho profile, và note operational completion ở journey.

---

### 10) `views/logi_view_model.py:2953-2955` writer VGM — đã chặn ở §5

---

## File đã sửa

- `component/src/components/JourneyQuickPanel.tsx` — importer UNKNOWN
- `core/shipment_document_workflow.py` — GNT vs TAX_PAID tách, thêm `taxPaid`/`taxPaidAt`/`paidAt`
- `views/logi_real_data.py` — `_gnt_projection` thêm `taxPaid`/`taxPaidAt`
- `core/shipment_journey.py` — sea LCL SI-only (sea_requirement + si-vgm node)
- `views/logi_view_model.py` — writer chặn VGM khi LCL
- `tests/test_false_done_batch2_negative.py` — 17 tests âm/dương (1 skipped khi thiếu streamlit)

Không sửa `shipment_execution_profile.py` unconditional stages và journey pickup/transit/customs-export theo lý do [CẦN XÁC MINH] trên, để không phá 13 tests `test_shipment_document_workflow.py` + 6 classes `test_journey_v3...` + `LOGI_SHIPMENT_EXECUTION_PROFILE_01`.

---

## Chạy test

```bash
python -m unittest tests.test_false_done_batch2_negative  # 17 tests, OK (skipped=1 khi thiếu streamlit)
python -m unittest tests.test_shipment_document_workflow tests.test_journey_v3_customs_import_184  # giữ xanh (cần streamlit/mongo env đầy đủ)
```

Trước sửa: `test_gnt_document_does_not_mean_tax_paid`, `test_legal_importer...`, `test_lcl_requires_only_si` FAIL (đúng kỳ vọng âm). Sau sửa: PASS.

---

## Ghi chú cho PR tiếp theo (nếu quá lớn tách 2 PR P0 trước)

- PR1-P0: `JourneyQuickPanel` + `shipment_document_workflow` + `logi_real_data` (rào pháp lý).
- PR2-P1: `shipment_journey` LCL + writer VGM + docs.

Không merge/deploy/backport trong session này.

