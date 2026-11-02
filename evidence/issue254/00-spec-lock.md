# PRE-CODE SPEC_LOCK — LOGI-254-SHIPMENT-DEBT-20261031

- Date locked (pre-code): `2026-11-01` (UTC)
- Issue spec: `https://github.com/7roger89-web/logistics-work-desk-arena/issues/254` (`id=6136462565`, `comments=0` at lock time; `POST /repos/7roger89-web/logistics-work-desk-arena/issues/254/comments` returned `HTTP 403 Resource not accessible by integration` under the Arena GitHub App token)
- Staging base ref: `arena/ae5f9f47-logistics-work-desk-arena` @ `1ffaea852adc1517fa06139c4579895f738329a6`
- Working branch: `arena/0d73ca3b-logistics-work-desk-arena` (clean pre-code merge `f3ec2fb025fcba9c398c39fbe60ff760f1a3bbd8`)
- Consumed skill: `.agents/skills/p2p-uiux/SKILL.md` (`98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2`)

## 1. Observable Outcome
- Authorized internal operators (`has_permission("finance_view") == True`: `support`, `accounting`, `viewer`, `admin`) see ONE compact read-only service debt summary cluster (`Phải thu` / `Đã thu` / `Còn phải thu`) with explicit currency per number (`VND` / `USD` / `CNY`, zero FX conversion, zero cross-currency sum) on every `/lo-hang` desktop row (`1440x900`) and mobile card (`390x844`) without opening each shipment.
- Clicking into the shipment / cluster opens shipment detail (`Tài chính / Công nợ` / `/lo-hang/<id>`) while preserving existing filters, search params, `"Việc tiếp theo"` (`s.nextRoute`), and mobile/desktop responsiveness without horizontal overflow or 3 separate money columns.
- Unauthorized internal actors (`has_permission("finance_view") == False`, e.g. `sale`, `sales`, `operations`) neither receive `finance_view` money fields in the server payload nor see the service debt summary cluster on `/lo-hang`.

## 2. Measured Source Contract
- `views/logi_real_data.py::finance_projection` (via `core.logic.calculate_from_shipment(shipment)` over `data["3.4"].details` & `data["3.4"].payments`):
  - `hasActualLines = bool(details)`.
  - `UNKNOWN != 0`: when `hasActualLines` is `False`, `receivable` and `outstanding` remain `None` (`"—"`), never `0 VND`, never `"đã thanh toán đủ"`, and never populated from Quote Estimate (`_quote_lines`) or partner payable, even when `received == 0` or a positive quote exists.
  - Recording (`payment_record`) or cancelling/reversing (`payment_correction`: `reversed` / `cancelled` / `void` / `is_reversed`) a customer receipt updates `received` and `outstanding = receivable - received` consistently across `core.logic`, `ShipmentDetail` (`tai-chinh`), and `/lo-hang`.
- `core/auth.py::ROLE_PERMISSIONS` + `core/auth.py::has_permission("finance_view")`:
  - Existing RBAC matrix untouched (`support`, `accounting`, `viewer` have `finance_view`; `admin` has `*`; `sale`, `sales`, `operations` lack `finance_view`).
  - Server-side `finance_view` gating added in `views/logi_real_data.py` and `views/logi_view_model.py` (`build_view_model` and `_projection_for` post-write readback).
- `component/src/pages/Shipments.tsx` & `component/src/lib/format.ts::fmtCcy`.
- Out of scope (untouched): Customer portal (`core/customer_journey.py` keeps `debt_summary.status="UNKNOWN"`), Lục Giác price publication gate, Node 06, RBAC matrix, database writers, `main` merge, Cloud deploy.

## 3. Wrong PASS Gates
1. `/lo-hang` showing `0 VND`, `"đã thanh toán đủ"`, or quote estimate on a quote-only shipment with no Finance Actual lines -> FAIL.
2. Actor without `finance_view` (`sale`) receiving finance actual/debt amounts in server payload OR seeing finance numbers on `/lo-hang` (client-side JSX hide alone) -> FAIL.
3. Stale `Đã thu` / `Còn phải thu` on `/lo-hang` after recording or reversing a customer payment -> FAIL.
