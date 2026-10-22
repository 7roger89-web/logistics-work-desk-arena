"""LOGI-211-HANDOVER-LABEL-MST — 2 select bên giao/bên nhận phải phân biệt
được 3 pháp nhân TRÙNG TÊN (MST + nhãn vai trò) và tên hiển thị của từng
bên sửa được tại công đoạn bàn giao (stage-local, không đụng master).

Pins (RED trước fix → GREEN sau fix):
* (i) 3 pháp nhân CÙNG TÊN khác MST ⇒ 3 option label KHÁC NHAU, chứa MST +
  vai trò của từng bên; thiếu MST thì bỏ đoạn MST (không bịa), vai trò vẫn có.
* (ii) nhập tên hiển thị bên giao/bên nhận ⇒ lưu theo evidence của công đoạn
  rồi đọc lại đúng (stored + values + dòng bằng chứng của stage); để trống
  ⇒ rơi về nhãn từ master.
* Validation chiều bàn giao KHÔNG đổi: cùng bên / ngoài chuỗi vẫn bị từ chối;
  ghi mỗi tên hiển thị không tự hoàn thành bàn giao.
* (iii) F-1 — tên hiển thị BÁM THEO PHÍA: đổi `handover_from`/`handover_to`
  trong một lượt ghi mà lượt đó không gửi kèm tên hiển thị của phía đó ⇒ tên
  cũ của phía đó bị bỏ (dòng bằng chứng rơi về nhãn master của bên MỚI); gửi
  kèm tên mới ⇒ giữ tên mới; không đổi phía ⇒ giữ nguyên tên cũ; phía không
  đổi vẫn chịu luật "không xoá trắng bằng chứng đã ghi".
* (iv) F-2 — `_entity_tax_code` phải đọc theo thứ tự COMPANY-trước
  (`tax_or_legal_code` → `legal_code` → `tax_code` → `mst`) và strip TỪNG giá
  trị: legal form / chuỗi khoảng trắng KHÔNG được che MST thật; không có MST
  nào thì trả "" (không bịa).
* (v) TUỲ CHỌN — cùng lớp lỗi trên 3 chuỗi tên hiển thị (`importer_name` /
  `sub_agent_name` / `signing_company_name`): `legal_name` toàn khoảng trắng
  KHÔNG được che `name` thật của master row.
"""

from __future__ import annotations

from core.shipment_document_workflow import (
    FLOW_TT_ENTRUSTED_SUB,
    ENTRUSTMENT_EVIDENCE_BLOCK,
    _entity_tax_code,
    entrustment_parties,
    project_commercial_flow,
    project_entrustment_stages,
    stored_entrustment_evidence,
    validate_entrustment_evidence_write,
)
from core.shipment_journey import ENTRUSTMENT_HANDOVER_ID, build_journey

SAME_NAME = "CÔNG TY TNHH TRƯỜNG THÀNH (FIXTURE)"

# Ba pháp nhân CÙNG MỘT tên pháp lý — chỉ khác mã + MST. Mỗi master dùng một
# cách ghi MST thật của repo (company: tax_or_legal_code, agent: legal_code).
COMPANIES = {
    "TT-SIGN": {
        "company_id": "TT-SIGN",
        "legal_name": SAME_NAME,
        "tax_or_legal_code": "0100000001",
    },
    "TT-IMP": {
        "company_id": "TT-IMP",
        "legal_name": SAME_NAME,
        "tax_or_legal_code": "0100000003",
    },
}
AGENTS = {
    "TT-CTR": {
        "agent_id": "TT-CTR",
        "legal_name": SAME_NAME,
        "legal_code": "0100000002",
    },
}
# Bên ký + đối tác không có MST trong master (importer vẫn phải có — đó là
# điều kiện ready có sẵn của flow, không thuộc task này).
COMPANIES_SIGNER_NO_MST = {
    "TT-SIGN": {"company_id": "TT-SIGN", "legal_name": SAME_NAME},
    "TT-IMP": dict(COMPANIES["TT-IMP"]),
}
AGENTS_NO_MST = {
    key: {"agent_id": row["agent_id"], "legal_name": row["legal_name"]}
    for key, row in AGENTS.items()
}

LINKED = {"status": "LINKED", "id": "HD-211", "contractNo": "HD-211"}


def _shipment() -> dict:
    return {
        "id": "FIX-211",
        "customer_id": "CUS-211",
        "data": {
            "0.0": {
                "commercial_flow": {
                    "mode": FLOW_TT_ENTRUSTED_SUB,
                    "confirmed": True,
                    "company_id": "TT-SIGN",
                    "sub_agent_id": "TT-CTR",
                    "importer_company_id": "TT-IMP",
                }
            },
            "1.2": {},
            "2.4": {},
            "2.7": {},
        },
    }


def _flow(companies=COMPANIES, agents=AGENTS) -> dict:
    flow = project_commercial_flow(_shipment(), companies=companies, agents=agents)
    assert flow["ready"] is True, flow["missing"]
    return flow


def _write(shipment: dict, flow: dict, fields: dict):
    merged, errors = validate_entrustment_evidence_write(
        shipment=shipment, flow=flow, contract=LINKED, fields=fields,
    )
    if merged is not None:
        # Same persist step as the real writer (views/logi_view_model.py):
        # the whole merged block becomes data.0.0.entrustment_evidence.
        shipment["data"]["0.0"][ENTRUSTMENT_EVIDENCE_BLOCK] = merged
    return merged, errors


READY_FIELDS = {
    "entrustment_ready_at": "2026-10-10",
    "entrustment_ready_ref": "HDNT-211 — biên bản phạm vi ủy thác",
}
HANDOVER_FIELDS = {
    "warehouse_handover_at": "2026-10-12",
    "warehouse_handover_from": "TT-SIGN",
    "warehouse_handover_to": "TT-IMP",
    "warehouse_handover_doc_no": "BBGN-211-01",
}


# (i) D1 — label phân biệt được -------------------------------------------------

def test_flow_projection_carries_tax_code_for_all_three_parties():
    flow = _flow()
    assert flow["companyTaxCode"] == "0100000001"
    assert flow["subAgentTaxCode"] == "0100000002"
    assert flow["legalImporterTaxCode"] == "0100000003"


def test_same_name_parties_get_distinguishable_labels():
    parties = entrustment_parties(_flow())
    assert [row["id"] for row in parties] == ["TT-SIGN", "TT-CTR", "TT-IMP"]
    labels = [row["label"] for row in parties]
    # Cùng tên nhưng 3 label phải KHÁC NHAU từng đôi một.
    assert len(set(labels)) == 3, labels
    by_id = {row["id"]: row["label"] for row in parties}
    assert by_id["TT-SIGN"].startswith(SAME_NAME)
    assert "MST 0100000001" in by_id["TT-SIGN"]
    assert "MST 0100000002" in by_id["TT-CTR"]
    assert "MST 0100000003" in by_id["TT-IMP"]
    # Nhãn vai trò phân biệt rõ từng bên trong chuỗi ủy thác.
    assert "ký ủy thác" in by_id["TT-SIGN"]
    assert "đối tác hợp đồng" in by_id["TT-CTR"]
    assert "đứng tên nhập khẩu" in by_id["TT-IMP"]


def test_missing_tax_code_omits_mst_but_keeps_role_and_never_invents():
    parties = entrustment_parties(_flow(COMPANIES_SIGNER_NO_MST, AGENTS_NO_MST))
    labels = [row["label"] for row in parties]
    assert len(set(labels)) == 3, labels  # vẫn phân biệt được nhờ vai trò
    by_id = {row["id"]: row["label"] for row in parties}
    # Thiếu MST ở master ⇒ bỏ hẳn đoạn MST, không bịa số.
    assert "MST" not in by_id["TT-SIGN"], by_id["TT-SIGN"]
    assert "MST" not in by_id["TT-CTR"], by_id["TT-CTR"]
    assert "MST 0100000003" in by_id["TT-IMP"]
    assert all(label.startswith(SAME_NAME) for label in labels), labels


def test_journey_selects_carry_distinguishable_options_and_keep_shape():
    stages = project_entrustment_stages(_flow(), LINKED, {})
    profile = {
        "mode": "ROAD", "loadModel": "FCL", "serviceScopeConfirmed": True,
        "serviceScope": ["MAIN_CARRIAGE", "IMPORT_CUSTOMS", "DELIVERY"],
        "stages": [
            {"code": "MAIN_CARRIAGE", "label": "Chặng chính", "reason": "SERVICE_SCOPE"},
            {"code": "IMPORT_CUSTOMS", "label": "Hải quan nhập", "reason": "SERVICE_SCOPE"},
            {"code": "DELIVERY", "label": "Giao hàng", "reason": "SERVICE_SCOPE"},
        ],
    }
    journey = build_journey(
        _shipment(), profile=profile,
        operational={"main_leg": {}, "pickup_leg": {}},
        primary={}, dashboard={}, attachments=[], entrustment_stages=stages,
    )
    node = next(n for n in journey["nodes"] if n["id"] == ENTRUSTMENT_HANDOVER_ID)
    fields = {f["key"]: f for f in node["factFields"]}
    for key in ("warehouse_handover_from", "warehouse_handover_to"):
        field = fields[key]
        assert field["kind"] == "status"
        options = field["options"]
        # Shape {value,label} giữ nguyên — không thêm/th bớt key nào.
        assert all(set(o) == {"value", "label"} for o in options), options
        assert [o["value"] for o in options] == ["TT-SIGN", "TT-CTR", "TT-IMP"]
        option_labels = [o["label"] for o in options]
        assert len(set(option_labels)) == 3, option_labels
        assert all("MST 010000000" in label for label in option_labels)
    # D2: 2 field text tên hiển thị có mặt trên chính node bàn giao.
    for key in ("warehouse_handover_from_label", "warehouse_handover_to_label"):
        assert fields[key]["kind"] == "text", fields.get(key)


# (ii) D2 — sửa tên hiển thị được, stage-local ---------------------------------

def test_display_label_round_trips_and_shows_in_stage_evidence():
    shipment, flow = _shipment(), _flow()
    merged, errors = _write(shipment, flow, READY_FIELDS)
    assert merged is not None, errors
    merged, errors = _write(shipment, flow, {
        **HANDOVER_FIELDS,
        "warehouse_handover_from_label": "Trường Thành kho Bắc Ninh (ghi theo biên bản)",
        "warehouse_handover_to_label": "Trường Thành chi nhánh Hải Phòng",
    })
    assert merged is not None, errors
    # Đọc lại từ block đã lưu — đúng chữ đã ghi, master không bị đụng.
    stored = stored_entrustment_evidence(shipment)
    assert stored["handover_from_label"] == "Trường Thành kho Bắc Ninh (ghi theo biên bản)"
    assert stored["handover_to_label"] == "Trường Thành chi nhánh Hải Phòng"
    stages = project_entrustment_stages(flow, LINKED, stored)
    assert stages["handover"]["done"] is True
    assert stages["values"]["warehouse_handover_from_label"] == stored["handover_from_label"]
    assert stages["values"]["warehouse_handover_to_label"] == stored["handover_to_label"]
    evidence = stages["handover"]["evidence"]
    assert "Trường Thành kho Bắc Ninh (ghi theo biên bản)" in evidence
    assert "Trường Thành chi nhánh Hải Phòng" in evidence


def test_blank_display_label_falls_back_to_master_party_label():
    shipment, flow = _shipment(), _flow()
    assert _write(shipment, flow, READY_FIELDS)[0] is not None
    assert _write(shipment, flow, HANDOVER_FIELDS)[0] is not None
    stored = stored_entrustment_evidence(shipment)
    assert stored["handover_from_label"] == ""
    assert stored["handover_to_label"] == ""
    stages = project_entrustment_stages(flow, LINKED, stored)
    evidence = stages["handover"]["evidence"]
    # Trống ⇒ rơi về nhãn master (tên + MST + vai trò) của đúng từng bên.
    assert "MST 0100000001" in evidence and "ký ủy thác" in evidence
    assert "MST 0100000003" in evidence and "đứng tên nhập khẩu" in evidence


def test_display_label_alone_never_completes_or_requires_handover():
    shipment, flow = _shipment(), _flow()
    assert _write(shipment, flow, READY_FIELDS)[0] is not None
    # Chỉ ghi tên hiển thị: được nhận (trường tuỳ chọn), nhưng KHÔNG biến
    # thành bằng chứng bàn giao và KHÔNG đòi đủ bộ trường bàn giao.
    merged, errors = _write(
        shipment, flow, {"warehouse_handover_from_label": "Tên gọi tại kho"},
    )
    assert merged is not None, errors
    stages = project_entrustment_stages(
        flow, LINKED, stored_entrustment_evidence(shipment),
    )
    assert stages["handover"]["done"] is False


def test_display_labels_do_not_weaken_direction_validation():
    shipment, flow = _shipment(), _flow()
    assert _write(shipment, flow, READY_FIELDS)[0] is not None
    labels = {
        "warehouse_handover_from_label": "Bên A",
        "warehouse_handover_to_label": "Bên B",
    }
    merged, errors = _write(
        shipment, flow,
        {**HANDOVER_FIELDS, **labels, "warehouse_handover_to": "TT-SIGN"},
    )
    assert merged is None and any("phải khác nhau" in e for e in errors), errors
    merged, errors = _write(
        shipment, flow,
        {**HANDOVER_FIELDS, **labels, "warehouse_handover_to": "TT-UNKNOWN"},
    )
    assert merged is None and any("thuộc chuỗi ủy thác" in e for e in errors), errors


def test_overlong_display_label_is_refused():
    shipment, flow = _shipment(), _flow()
    assert _write(shipment, flow, READY_FIELDS)[0] is not None
    merged, errors = _write(
        shipment, flow,
        {**HANDOVER_FIELDS, "warehouse_handover_from_label": "X" * 201},
    )
    assert merged is None and any("dài quá" in e for e in errors), errors


# (iii) F-1 — tên hiển thị BÁM THEO PHÍA -----------------------------------------
#
# QA độc lập #6307025423 (F-1) tái hiện: ghi tên "Kho Bắc Ninh" cho bên giao
# TT-SIGN, rồi đổi bên giao sang TT-CTR ⇒ dòng bằng chứng vẫn hiện tên cũ cho
# pháp nhân MỚI.  Tên hiển thị là chữ của MỘT phía; đổi phía mà không kèm tên
# mới thì tên cũ không còn thuộc về ai ⇒ bị bỏ, dòng bằng chứng rơi về nhãn
# master của bên mới (tên + MST + vai trò).

FROM_LABEL = "Trường Thành kho Bắc Ninh"
TO_LABEL = "Trường Thành chi nhánh Hải Phòng"


def _with_labels() -> tuple[dict, dict]:
    """Shipment đã có ready + handover đủ 4 fact + 2 tên hiển thị."""
    shipment, flow = _shipment(), _flow()
    assert _write(shipment, flow, READY_FIELDS)[0] is not None
    merged, errors = _write(shipment, flow, {
        **HANDOVER_FIELDS,
        "warehouse_handover_from_label": FROM_LABEL,
        "warehouse_handover_to_label": TO_LABEL,
    })
    assert merged is not None, errors
    return shipment, flow


def test_changing_side_without_label_drops_stale_label_and_falls_back_to_master():
    shipment, flow = _with_labels()
    # Đổi bên giao TT-SIGN -> TT-CTR, KHÔNG gửi kèm tên hiển thị bên giao.
    merged, errors = _write(shipment, flow, {"warehouse_handover_from": "TT-CTR"})
    assert merged is not None, errors
    stored = stored_entrustment_evidence(shipment)
    assert stored["handover_from"] == "TT-CTR"
    # Tên cũ của phía đã đổi bị bỏ; phía KHÔNG đổi giữ nguyên tên của nó.
    assert stored["handover_from_label"] == "", stored
    assert stored["handover_to_label"] == TO_LABEL, stored
    stages = project_entrustment_stages(flow, LINKED, stored)
    evidence = stages["handover"]["evidence"]
    # Dòng bằng chứng dùng nhãn master của bên MỚI, không dính tên của bên cũ.
    assert FROM_LABEL not in evidence, evidence
    assert "MST 0100000002" in evidence and "đối tác hợp đồng" in evidence, evidence
    assert TO_LABEL in evidence, evidence
    # Bỏ tên hiển thị KHÔNG phải xoá bằng chứng: handover vẫn đủ và vẫn done.
    assert stages["handover"]["done"] is True, stages["handover"]["missing"]
    assert stored["handover_at"] == HANDOVER_FIELDS["warehouse_handover_at"]
    assert stored["handover_doc_no"] == HANDOVER_FIELDS["warehouse_handover_doc_no"]


def test_changing_side_with_new_label_keeps_the_new_name():
    shipment, flow = _with_labels()
    merged, errors = _write(shipment, flow, {
        "warehouse_handover_from": "TT-CTR",
        "warehouse_handover_from_label": "Trường Thành — đối tác nhận ủy thác",
    })
    assert merged is not None, errors
    stored = stored_entrustment_evidence(shipment)
    assert stored["handover_from"] == "TT-CTR"
    assert stored["handover_from_label"] == "Trường Thành — đối tác nhận ủy thác"
    assert stored["handover_to_label"] == TO_LABEL
    stages = project_entrustment_stages(flow, LINKED, stored)
    assert "Trường Thành — đối tác nhận ủy thác" in stages["handover"]["evidence"]
    assert FROM_LABEL not in stages["handover"]["evidence"]


def test_unchanged_side_keeps_its_recorded_label():
    shipment, flow = _with_labels()
    # Ghi lại đúng phía cũ (không đổi bên) + sửa fact khác ⇒ tên cũ giữ nguyên.
    merged, errors = _write(shipment, flow, {
        "warehouse_handover_from": "TT-SIGN",
        "warehouse_handover_to": "TT-IMP",
        "warehouse_handover_doc_no": "BBGN-211-02",
    })
    assert merged is not None, errors
    stored = stored_entrustment_evidence(shipment)
    assert stored["handover_from_label"] == FROM_LABEL
    assert stored["handover_to_label"] == TO_LABEL
    assert stored["handover_doc_no"] == "BBGN-211-02"
    stages = project_entrustment_stages(flow, LINKED, stored)
    assert FROM_LABEL in stages["handover"]["evidence"]
    assert TO_LABEL in stages["handover"]["evidence"]


def test_unchanged_side_still_refuses_blanking_a_recorded_label():
    shipment, flow = _with_labels()
    # Phía KHÔNG đổi + caller gửi rỗng ⇒ luật "không xoá bằng chứng đã ghi"
    # vẫn áp (đường bỏ tên chỉ dành cho lần ghi ĐỔI BÊN).
    merged, errors = _write(shipment, flow, {
        "warehouse_handover_from": "TT-SIGN",
        "warehouse_handover_from_label": "",
    })
    assert merged is None and any(
        "Không được xóa bằng chứng đã ghi (handover_from_label)" in e for e in errors
    ), errors
    # Và block đã lưu không bị đụng.
    stored = stored_entrustment_evidence(shipment)
    assert stored["handover_from_label"] == FROM_LABEL


def test_changing_receiver_side_without_label_drops_its_stale_label():
    # Cùng luật cho phía BÊN NHẬN (không chỉ bên giao).
    shipment, flow = _with_labels()
    merged, errors = _write(shipment, flow, {"warehouse_handover_to": "TT-CTR"})
    assert merged is not None, errors
    stored = stored_entrustment_evidence(shipment)
    assert stored["handover_to"] == "TT-CTR"
    assert stored["handover_to_label"] == "", stored
    assert stored["handover_from_label"] == FROM_LABEL, stored
    stages = project_entrustment_stages(flow, LINKED, stored)
    evidence = stages["handover"]["evidence"]
    assert TO_LABEL not in evidence, evidence
    assert "MST 0100000002" in evidence and "đối tác hợp đồng" in evidence, evidence
    assert FROM_LABEL in evidence, evidence


# (iv) F-2 — MST đọc ĐÚNG field của pháp nhân, không bị key khác che -----------
# Nguyên nhân gốc: `_entity_tax_code` đọc `legal_code` TRƯỚC `tax_or_legal_code`
# và chỉ strip ở kết quả cuối của chuỗi `or` — nên một `legal_code` giữ vai trò
# "spelling" (legal form) hoặc một giá trị toàn khoảng trắng che mất MST thật.
# 3 pháp nhân Trường Thành CÙNG TÊN nên MST là thứ duy nhất phân biệt được.

# COMPANY master có CẢ `legal_code` (legal form, không phải MST) lẫn
# `tax_or_legal_code` (MST thật) — đúng hình dạng master thật của repo.
COMPANIES_WITH_LEGAL_FORM = {
    "TT-SIGN": {**COMPANIES["TT-SIGN"], "legal_code": "LEGAL-FORM"},
    "TT-IMP": {**COMPANIES["TT-IMP"], "legal_code": "LEGAL-FORM"},
}


def test_company_tax_code_wins_over_legal_code_spelling():
    # (1) Hình dạng thật của COMPANY master: `tax_or_legal_code` là MST,
    # `legal_code` là legal form ⇒ MST thật phải thắng.
    assert _entity_tax_code(
        {"tax_or_legal_code": "0100123456", "legal_code": "LEGAL-FORM"}
    ) == "0100123456"
    # Đường thật: label 2 select bên giao/bên nhận phải mang ĐÚNG MST của pháp
    # nhân được chọn (3 pháp nhân trùng tên, khác MST) — không phải legal form.
    by_id = {
        row["id"]: row["label"]
        for row in entrustment_parties(_flow(COMPANIES_WITH_LEGAL_FORM, AGENTS))
    }
    assert "MST 0100000001" in by_id["TT-SIGN"], by_id["TT-SIGN"]
    assert "MST 0100000003" in by_id["TT-IMP"], by_id["TT-IMP"]
    assert "LEGAL-FORM" not in "".join(by_id.values()), by_id
    assert len(set(by_id.values())) == 3, by_id


def test_blank_spelling_value_does_not_mask_the_real_tax_code():
    # (2) Giá trị toàn khoảng trắng KHÔNG được che MST thật đứng sau nó.
    assert _entity_tax_code({"legal_code": "   ", "tax_code": "0100999888"}) == "0100999888"
    assert _entity_tax_code(
        {"legal_code": " ", "tax_or_legal_code": " 0100123456 ", "mst": "9999999999"}
    ) == "0100123456"
    # Cùng luật cho hàng master trắng ở field đứng trước: MST của bên nhập khẩu
    # vẫn phải resolve đúng, không rơi về rỗng.
    companies = {
        **COMPANIES_WITH_LEGAL_FORM,
        "TT-IMP": {**COMPANIES_WITH_LEGAL_FORM["TT-IMP"], "legal_code": "   "},
    }
    by_id = {row["id"]: row["label"] for row in entrustment_parties(_flow(companies, AGENTS))}
    assert "MST 0100000003" in by_id["TT-IMP"], by_id["TT-IMP"]


def test_no_tax_code_anywhere_stays_blank_and_is_never_invented():
    # (3) Không có MST ở bất kỳ spelling nào ⇒ "", KHÔNG bịa số.
    assert _entity_tax_code({}) == ""
    assert _entity_tax_code(None) == ""
    assert _entity_tax_code(
        {"legal_code": "  ", "tax_or_legal_code": "\t", "tax_code": " ", "mst": "\n"}
    ) == ""
    # Master sạch kiểu "không có MST" cho cả 3 bên ⇒ nhãn bỏ đoạn MST, không bịa.
    parties = entrustment_parties(_flow(COMPANIES_SIGNER_NO_MST, AGENTS_NO_MST))
    signer = next(row["label"] for row in parties if row["id"] == "TT-SIGN")
    assert "MST" not in signer, signer


# (v) TUỲ CHỌN — CÙNG LỚP LỖI trên 3 chuỗi tên hiển thị ------------------------
# 3 chuỗi `importer_name` / `sub_agent_name` / `signing_company_name` cũng dùng
# `or` trên RAW value ⇒ `legal_name="  "` (không rỗng nhưng toàn khoảng trắng)
# che `name` thật ⇒ nhãn bên giao/bên nhận mất TÊN, chỉ còn mã + vai trò. Hạng
# mục TUỲ CHỌN của task F-2; RED chứng minh được nên sửa cùng lớp lỗi.

def test_whitespace_legal_name_does_not_mask_the_real_master_name():
    companies = {
        "TT-SIGN": {"company_id": "TT-SIGN", "legal_name": "   ", "name": "TT-SIGN REAL"},
        "TT-IMP": {
            "company_id": "TT-IMP",
            "legal_name": "\t",
            "company_name": "TT-IMP REAL",
            "tax_or_legal_code": "0100000003",
        },
    }
    agents = {
        "TT-CTR": {"agent_id": "TT-CTR", "legal_name": " ", "name": "TT-CTR REAL",
                   "legal_code": "0100000002"},
    }
    flow = project_commercial_flow(_shipment(), companies=companies, agents=agents)
    assert flow["companyName"] == "TT-SIGN REAL", flow["companyName"]
    assert flow["subAgentName"] == "TT-CTR REAL", flow["subAgentName"]
    assert flow["legalImporterName"] == "TT-IMP REAL", flow["legalImporterName"]
    # Nhãn 2 select vì thế mang đúng TÊN THẬT + MST + vai trò, không chỉ mã.
    labels = {row["id"]: row["label"] for row in entrustment_parties(flow)}
    assert labels["TT-SIGN"].startswith("TT-SIGN REAL · "), labels["TT-SIGN"]
    assert labels["TT-CTR"].startswith("TT-CTR REAL · MST 0100000002 · "), labels["TT-CTR"]
    assert labels["TT-IMP"].startswith("TT-IMP REAL · MST 0100000003 · "), labels["TT-IMP"]


# ---------------------------------------------------------------------------
# (vi) W4 — seed danh tính THẬT: 3 vai trò của MỘT pháp nhân Trường Thành
# ---------------------------------------------------------------------------
# Owner cấp dữ liệu thật 2026-10-21 (nguyên văn: "Mst 0105937262, công ty trường
# thành logistics. Cả 3 tên đều như thế"). Ca này KHÁC ca W1 ở đúng chỗ khó
# nhất: W1 mới có TRÙNG TÊN + KHÁC MST (MST còn là thứ phân biệt); ở đây TÊN và
# MST TRÙNG NHAU hoàn toàn, nên thứ duy nhất còn phân biệt 3 lựa chọn bên
# giao/bên nhận là NHÃN VAI TRÒ.
# Pin chạy trên seed THẬT của ``views/logi_staging_seed.py`` (không phải fixture
# tự dựng), đúng đường: master → project_commercial_flow → entrustment_parties
# → 2 select của node bàn giao → writer.

OWNER_LEGAL_NAME = "CÔNG TY TRƯỜNG THÀNH LOGISTICS"
OWNER_TAX_CODE = "0105937262"
# Vai trò 1 — ký hợp đồng ủy thác (id cũ, giữ để không phá tham chiếu sẵn có).
SIGNING_ID = "TT-COMPANY"
# Vai trò 2 — đối tác hợp đồng, resolve từ authority_agents (AGENT master).
SUB_AGENT_ID = "AGT-TRUONGTHANH"
# Vai trò 3 — đứng tên nhập khẩu; id PHẢI khác vai trò 1 (điều kiện của writer).
IMPORTER_ID = "TT-COMPANY-IMPORT"
ROLE_OF = {
    SIGNING_ID: "bên ký ủy thác",
    SUB_AGENT_ID: "đối tác hợp đồng",
    IMPORTER_ID: "đứng tên nhập khẩu",
}
SEED_IDS = [SIGNING_ID, SUB_AGENT_ID, IMPORTER_ID]

_SEED_PROFILE = {
    "mode": "ROAD", "loadModel": "FCL", "serviceScopeConfirmed": True,
    "serviceScope": ["MAIN_CARRIAGE", "IMPORT_CUSTOMS", "DELIVERY"],
    "stages": [
        {"code": "MAIN_CARRIAGE", "label": "Chặng chính", "reason": "SERVICE_SCOPE"},
        {"code": "IMPORT_CUSTOMS", "label": "Hải quan nhập", "reason": "SERVICE_SCOPE"},
        {"code": "DELIVERY", "label": "Giao hàng", "reason": "SERVICE_SCOPE"},
    ],
}


def _seed_masters() -> tuple[dict, dict]:
    """Seed masters đọc đúng hình dạng loader DB trả về: ``{id: row}``."""
    from views import logi_staging_seed as staging_seed

    companies = {row["id"]: row for row in staging_seed.AUTHORITY_COMPANIES}
    agents = {row["id"]: row for row in staging_seed.AUTHORITY_AGENTS}
    return companies, agents


def _seed_shipment() -> dict:
    """Lô TT_ENTRUSTED_SUB chọn đúng 3 vai trò thật của seed."""
    shipment = _shipment()
    flow = shipment["data"]["0.0"]["commercial_flow"]
    flow["company_id"] = SIGNING_ID
    flow["sub_agent_id"] = SUB_AGENT_ID
    flow["importer_company_id"] = IMPORTER_ID
    return shipment


def _seed_flow(companies: dict | None = None, agents: dict | None = None) -> dict:
    seed_companies, seed_agents = _seed_masters()
    return project_commercial_flow(
        _seed_shipment(),
        companies=seed_companies if companies is None else companies,
        agents=seed_agents if agents is None else agents,
    )


def _handover_fields(flow: dict, shipment: dict | None = None) -> dict:
    """2 select bên giao/bên nhận trên node bàn giao, qua journey THẬT."""
    stages = project_entrustment_stages(flow, LINKED, {})
    journey = build_journey(
        _seed_shipment() if shipment is None else shipment,
        profile=_SEED_PROFILE,
        operational={"main_leg": {}, "pickup_leg": {}},
        primary={}, dashboard={}, attachments=[], entrustment_stages=stages,
    )
    node = next(n for n in journey["nodes"] if n["id"] == ENTRUSTMENT_HANDOVER_ID)
    return {f["key"]: f for f in node["factFields"]}


def test_staging_seed_has_three_role_ids_for_one_legal_person():
    companies, agents = _seed_masters()
    assert {SIGNING_ID, IMPORTER_ID} <= set(companies), sorted(companies)
    assert SUB_AGENT_ID in agents, sorted(agents)
    # CÙNG một pháp nhân ⇒ cùng tên thật, cùng MST thật, mỗi master ghi đúng
    # spelling của nó (COMPANY: tax_or_legal_code, AGENT: legal_code).
    assert companies[SIGNING_ID]["legal_name"] == OWNER_LEGAL_NAME
    assert companies[IMPORTER_ID]["legal_name"] == OWNER_LEGAL_NAME
    assert companies[SIGNING_ID]["tax_or_legal_code"] == OWNER_TAX_CODE
    assert companies[IMPORTER_ID]["tax_or_legal_code"] == OWNER_TAX_CODE
    assert agents[SUB_AGENT_ID]["legal_name"] == OWNER_LEGAL_NAME
    assert agents[SUB_AGENT_ID]["legal_code"] == OWNER_TAX_CODE
    # 3 id KHÁC nhau từng đôi một — điều kiện để writer nhận 2 phía khác nhau.
    assert len(set(SEED_IDS)) == 3
    # Record Phú Anh lịch sử KHÔNG bị đổi tên thành Trường Thành (không phải 1
    # trong 3 vai trò của chuỗi ủy thác) — giữ để không phá partner/payable cũ.
    assert "AGT-PHUANH" in agents


def test_staging_seed_source_carries_the_owner_identity_in_every_role_record():
    from pathlib import Path

    source = Path("views/logi_staging_seed.py").read_text(encoding="utf-8")
    # 3 record = 3 lần ghi MST thật + 3 lần ghi tên thật (đếm theo dòng).
    assert source.count(OWNER_TAX_CODE) >= 3, source.count(OWNER_TAX_CODE)
    assert source.count(OWNER_LEGAL_NAME) >= 3, source.count(OWNER_LEGAL_NAME)
    # Danh tính staging cũ đã bị thay hoàn toàn, không còn nằm lại trong seed.
    assert "0100987654" not in source
    assert "GIAO NHẬN QUỐC TẾ" not in source


def test_same_name_and_same_tax_code_are_separated_only_by_role():
    flow = _seed_flow()
    assert flow["ready"] is True, flow["missing"]
    parties = entrustment_parties(flow)
    assert [row["id"] for row in parties] == SEED_IDS
    labels = [row["label"] for row in parties]
    assert len(set(labels)) == 3, labels
    # Trùng tên + trùng MST: label chỉ khác nhau ở ĐUÔI VAI TRÒ, đúng từng bên.
    for row in parties:
        assert row["label"] == (
            f"{OWNER_LEGAL_NAME} · MST {OWNER_TAX_CODE} · {ROLE_OF[row['id']]}"
        ), row["label"]
    assert {label.rsplit(" · ", 1)[0] for label in labels} == {
        f"{OWNER_LEGAL_NAME} · MST {OWNER_TAX_CODE}"
    }, labels


def test_both_staging_handover_selects_offer_three_role_options_with_same_shape():
    flow = _seed_flow()
    fields = _handover_fields(flow)
    for key in ("warehouse_handover_from", "warehouse_handover_to"):
        field = fields[key]
        assert field["kind"] == "status", field
        options = field["options"]
        # Shape {value,label} giữ nguyên — không thêm/bớt key nào.
        assert all(set(option) == {"value", "label"} for option in options), options
        assert [option["value"] for option in options] == SEED_IDS
        assert len({option["label"] for option in options}) == 3, options
        for option in options:
            assert f"MST {OWNER_TAX_CODE}" in option["label"], option
            assert option["label"].endswith(ROLE_OF[option["value"]]), option
    # 2 field tên hiển thị vẫn là secondary (không thêm field primary nào).
    for key in ("warehouse_handover_from_label", "warehouse_handover_to_label"):
        assert fields[key]["kind"] == "text", fields.get(key)
        assert fields[key]["secondary"] is True, fields.get(key)


def test_handover_between_two_roles_of_one_legal_person_is_accepted_once():
    shipment, flow = _seed_shipment(), _seed_flow()
    assert _write(shipment, flow, READY_FIELDS)[0] is not None
    # Bên giao = vai trò 1, bên nhận = vai trò 3: cùng tên + cùng MST, chỉ khác
    # vai trò ⇒ bàn giao vẫn hợp lệ và dòng bằng chứng phân biệt được 2 bên.
    merged, errors = _write(shipment, flow, {
        "warehouse_handover_at": "2026-10-12",
        "warehouse_handover_from": SIGNING_ID,
        "warehouse_handover_to": IMPORTER_ID,
        "warehouse_handover_doc_no": "BBGN-211-W4",
    })
    assert merged is not None, errors
    stages = project_entrustment_stages(flow, LINKED, stored_entrustment_evidence(shipment))
    assert stages["handover"]["done"] is True, stages["handover"]["missing"]
    evidence = stages["handover"]["evidence"]
    assert ROLE_OF[SIGNING_ID] in evidence, evidence
    assert ROLE_OF[IMPORTER_ID] in evidence, evidence
    # Vai trò khác KHÔNG phải giấy phép chọn cùng một id cho cả 2 phía.
    same_side, same_errors = _write(shipment, flow, {"warehouse_handover_to": SIGNING_ID})
    assert same_side is None and any("khác nhau" in e for e in same_errors), same_errors


def test_missing_tax_code_on_a_role_drops_only_the_mst_segment():
    # Thiếu MST ở vai trò 1 (bên giao) + vai trò 2: bỏ đúng đoạn MST, KHÔNG
    # bịa số; vai trò 3 (bên nhận) vẫn giữ MST nên flow vẫn đủ điều kiện ready.
    companies, agents = _seed_masters()
    signer = {key: value for key, value in companies[SIGNING_ID].items() if key != "tax_or_legal_code"}
    sub_agent = {key: value for key, value in agents[SUB_AGENT_ID].items() if key != "legal_code"}
    companies[SIGNING_ID] = signer
    agents[SUB_AGENT_ID] = sub_agent
    flow = _seed_flow(companies, agents)
    assert flow["ready"] is True, flow["missing"]
    by_id = {row["id"]: row["label"] for row in entrustment_parties(flow)}
    assert by_id[SIGNING_ID] == f"{OWNER_LEGAL_NAME} · {ROLE_OF[SIGNING_ID]}", by_id
    assert by_id[SUB_AGENT_ID] == f"{OWNER_LEGAL_NAME} · {ROLE_OF[SUB_AGENT_ID]}", by_id
    assert by_id[IMPORTER_ID] == (
        f"{OWNER_LEGAL_NAME} · MST {OWNER_TAX_CODE} · {ROLE_OF[IMPORTER_ID]}"
    ), by_id
    # Vẫn 3 lựa chọn phân biệt được, và 2 select vẫn đủ 3 giá trị: ca này chọn
    # bên giao = vai trò 1 (thiếu MST) → bên nhận = vai trò 3 (có MST).
    assert len(set(by_id.values())) == 3
    fields = _handover_fields(flow)
    for key in ("warehouse_handover_from", "warehouse_handover_to"):
        assert [option["value"] for option in fields[key]["options"]] == SEED_IDS
    signer_option = next(
        option for option in fields["warehouse_handover_from"]["options"]
        if option["value"] == SIGNING_ID
    )
    assert "MST" not in signer_option["label"], signer_option
