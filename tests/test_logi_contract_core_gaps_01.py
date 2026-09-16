"""LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — contract workspace gaps.

Focused acceptance for the four contract facts the desk could show but not keep:

  * ``pl_required``   — the operator's explicit "Có PL" / "Không cần PL" choice;
  * ``date``          — the contract signing date ``contract_projection`` reads;
  * ``company_id``    — the buyer company ("Công ty bên mua"), editable after create;
  * ``customer_id``   — the counterparty half of the contract, re-pickable after create;
  * ``customer_getfly_import`` — the only customer data a GetFly DSDH block
    really carries, imported through the EXISTING ``customer_import`` writer.

Write contract under test (identical to every other C1 event):
    typed event → bounded dispatcher → RBAC → core.database.save_contract_to_cloud
    → audit → FRESH read_contract → projection readback.

Transport is the isolated mongomock staging database running the CURRENT
canonical writers unchanged; production is never touched. UNKNOWN != ZERO and
"no invented default" are asserted explicitly: a blank PL answer must come back
as "" (chưa chọn), never as "NO".
"""

from __future__ import annotations

import pytest

from views import logi_c1
from views import logi_sandbox
from views import logi_view_model as vm


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def _as(role: str, username: str) -> None:
    import streamlit as st

    st.session_state["current_user"] = {
        "username": username, "full_name": username, "role": role, "user_id": f"ID-{username}",
    }


def _stored(cid: str):
    """The database's own answer — never the handler's echo."""
    from core.database import load_contracts

    return (load_contracts() or {}).get(cid) or {}


# ---------------------------------------------------------------------------
# 1. PL option — explicit, operator-controlled, preserved on readback
# ---------------------------------------------------------------------------

def test_contract_create_without_pl_stays_unknown(staging, event_seq):
    """No answer on the create form is recorded as "" — never as "Không cần PL"."""
    out = _dispatch(event_seq, "contract_create", {
        "id": "HDMB-PL01", "customerId": "CUST-ANPHAT", "kind": "HDMB",
    })
    assert out["ok"], out["error"]
    assert out["readback"]["plRequired"] == ""
    assert _stored("HDMB-PL01").get("pl_required", "") == ""


@pytest.mark.parametrize("typed,expected", [
    ("Có PL", "YES"),
    ("Co PL", "YES"),
    ("YES", "YES"),
    ("Không cần PL", "NO"),
    ("Khong can PL", "NO"),
    ("NO", "NO"),
    ("", ""),
])
def test_pl_choice_is_stored_and_read_back(staging, event_seq, typed, expected):
    """Every accepted label round-trips through the canonical writer verbatim."""
    assert _dispatch(event_seq, "contract_save",
                     {"id": "HDMB-0306", "pl_required": typed})["ok"]
    assert _stored("HDMB-0306").get("pl_required") == expected
    model = vm.build_view_model()
    row = next(c for c in model["contracts"] if c["id"] == "HDMB-0306")
    assert row["plRequired"] == expected


def test_pl_can_be_flipped_and_cleared_after_create(staging, event_seq):
    """Post-create editability: YES → NO → "" each survive a fresh read."""
    assert _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "pl_required": "Có PL"})["ok"]
    assert _stored("HDMB-0306")["pl_required"] == "YES"

    assert _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "pl_required": "Không cần PL"})["ok"]
    assert _stored("HDMB-0306")["pl_required"] == "NO"

    out = _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "pl_required": ""})
    assert out["ok"] and out["readback"]["plRequired"] == ""
    assert _stored("HDMB-0306")["pl_required"] == ""


def test_pl_refuses_an_unusable_answer_without_touching_the_contract(staging, event_seq):
    """A value the two labels cannot express is refused, not silently defaulted."""
    assert _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "pl_required": "Có PL"})["ok"]
    out = _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "pl_required": "co le"})
    assert not out["ok"]
    assert "PL" in out["error"]
    # Refusal must be total: the previously stored decision survives.
    assert _stored("HDMB-0306")["pl_required"] == "YES"


def test_pl_flag_does_not_rewrite_the_docgen_threshold(staging, event_seq):
    """The flag records the operator's decision; core.docgen still decides alone.

    Scope honesty for this slice: the desk must not quietly change WHICH legal
    documents the server's 50-million rule produces. So the claim under test is
    exactly "core.docgen never reads this field", proven on the source itself.
    """
    from core.docgen import __file__ as docgen_init
    from pathlib import Path

    docgen_dir = Path(docgen_init).parent
    docgen_sources = "\n".join(path.read_text(encoding="utf-8") for path in sorted(docgen_dir.glob("*.py")))
    assert "pl_required" not in docgen_sources

    assert _dispatch(event_seq, "contract_save", {"id": "HDNT-0307", "pl_required": "Không cần PL"})["ok"]
    row = next(c for c in vm.build_view_model()["contracts"] if c["id"] == "HDNT-0307")
    # Threshold + document cards still come from build_document_pack unchanged.
    assert row["thresholdVnd"] == 50_000_000
    assert row["plRequired"] == "NO"


# ---------------------------------------------------------------------------
# 2. Buyer company — visible, editable, canonical readback
# ---------------------------------------------------------------------------

def test_buyer_company_is_editable_after_create_and_projects_back(staging, event_seq):
    from core.database import load_authority_companies

    companies = load_authority_companies() or {}
    assert companies, "staging seed must carry the company master"
    target = sorted(companies)[0]

    out = _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "company_id": target})
    assert out["ok"], out["error"]
    assert _stored("HDMB-0306")["company_id"] == target.upper()
    assert out["readback"]["companyId"] == target.upper()
    # The projected name is resolved from the authority master, not stored twice.
    assert out["readback"]["company"] == companies[target].get("legal_name")


def test_buyer_company_survives_a_re_read_after_every_other_save(staging, event_seq):
    """Saving another field must never drop the chosen buyer."""
    from core.database import load_authority_companies

    target = sorted(load_authority_companies() or {})[0]
    assert _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "company_id": target})["ok"]
    assert _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "note": "đổi ghi chú"})["ok"]
    assert _stored("HDMB-0306")["company_id"] == target.upper()


# ---------------------------------------------------------------------------
# 3. Contract date — the field contract_projection already reads
# ---------------------------------------------------------------------------

def test_contract_date_persists_and_reads_back(staging, event_seq):
    out = _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "date": "2026-09-05"})
    assert out["ok"], out["error"]
    assert _stored("HDMB-0306")["date"] == "2026-09-05"
    assert out["readback"]["contractDate"] == "2026-09-05"

    model = vm.build_view_model()
    row = next(c for c in model["contracts"] if c["id"] == "HDMB-0306")
    assert row["contractDate"] == "2026-09-05"


def test_blank_contract_date_is_an_explicit_clear_not_a_default(staging, event_seq):
    """Sending the key with "" clears it; omitting the key leaves it alone."""
    assert _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "date": "2026-09-05"})["ok"]
    assert _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "note": "không đổi ngày"})["ok"]
    assert _stored("HDMB-0306")["date"] == "2026-09-05", "absent key must not blank the date"

    assert _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "date": ""})["ok"]
    assert _stored("HDMB-0306")["date"] == ""


def test_contract_create_accepts_date_and_pl_together(staging, event_seq):
    out = _dispatch(event_seq, "contract_create", {
        "id": "HDMB-PL02", "customerId": "CUST-DUCLONG", "kind": "HDMB",
        "date": "2026-09-07", "pl_required": "Có PL",
    })
    assert out["ok"], out["error"]
    stored = _stored("HDMB-PL02")
    assert stored["date"] == "2026-09-07" and stored["pl_required"] == "YES"
    assert out["readback"]["contractDate"] == "2026-09-07"
    assert out["readback"]["plRequired"] == "YES"


# ---------------------------------------------------------------------------
# 4. Post-create counterparty editability
# ---------------------------------------------------------------------------

def test_customer_can_be_reassigned_after_create(staging, event_seq):
    from core.database import load_customers

    customers = load_customers() or {}
    target = "CUST-MINHDUC"
    assert target in customers

    out = _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "customerId": target})
    assert out["ok"], out["error"]
    stored = _stored("HDMB-0306")
    assert stored["customer_id"] == target
    # Name + client are written from the master, so the label never drifts.
    assert stored["customer"] == customers[target]["name"] == stored["client"]
    assert out["readback"]["client"] == customers[target]["name"]


def test_customer_reassignment_refuses_unknown_and_blank(staging, event_seq):
    before = dict(_stored("HDMB-0306"))

    unknown = _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "customerId": "CUST-KHONGCO"})
    assert not unknown["ok"] and "danh bạ" in unknown["error"]

    blank = _dispatch(event_seq, "contract_save", {"id": "HDMB-0306", "customerId": ""})
    assert not blank["ok"] and "khách hàng" in blank["error"].lower()

    assert _stored("HDMB-0306") == before, "a refused save must leave the contract untouched"


def test_untouched_legacy_contract_stays_saveable_without_customer_id(staging, event_seq):
    """A contract with no customer_id must not be blocked by the new check."""
    from core.database import save_contract_to_cloud

    save_contract_to_cloud({
        "id": "HDNT-LEGACY", "contract_no": "HDNT-LEGACY", "client": "Khách cũ",
        "kind": "HDNT", "status": "active",
    })
    assert "customer_id" not in _stored("HDNT-LEGACY") or not _stored("HDNT-LEGACY").get("customer_id")

    out = _dispatch(event_seq, "contract_save", {
        "id": "HDNT-LEGACY", "note": "chỉ đổi ghi chú", "pl_required": "Có PL",
    })
    assert out["ok"], out["error"]
    assert _stored("HDNT-LEGACY")["note"] == "chỉ đổi ghi chú"
    assert _stored("HDNT-LEGACY")["pl_required"] == "YES"


# ---------------------------------------------------------------------------
# 5. Audit trail + RBAC on the new write paths
# ---------------------------------------------------------------------------

def test_each_new_contract_write_leaves_an_audit_row(staging, event_seq):
    assert _dispatch(event_seq, "contract_save", {
        "id": "HDMB-0306", "date": "2026-09-09", "pl_required": "Có PL",
    })["ok"]
    actions = [row["action"] for row in logi_c1._audit("contract", "HDMB-0306")]
    assert "update" in actions, actions


@pytest.mark.parametrize("event,payload", [
    ("contract_save", {"id": "HDMB-0306", "pl_required": "Có PL"}),
    ("contract_save", {"id": "HDMB-0306", "date": "2026-09-09"}),
    ("contract_save", {"id": "HDMB-0306", "customerId": "CUST-MINHDUC"}),
    ("customer_getfly_import", {"text": "Mã ĐH;Tên KH;Mã KH\nDH-1;A;CUST-A"}),
])
def test_viewer_is_refused_on_every_new_surface(staging, event_seq, event, payload):
    _as("viewer", "viewer.gap")
    out = _dispatch(event_seq, event, payload)
    assert not out["ok"] and "RBAC" in out["error"]
    if event == "contract_save" and "pl_required" in payload:
        assert _stored("HDMB-0306").get("pl_required", "") == ""


# ---------------------------------------------------------------------------
# 6. GetFly extraction → customer import (reuse, not a second importer)
# ---------------------------------------------------------------------------

GETFLY_TABBED = (
    "Mã ĐH\tNgày đặt hàng\tTên KH\tMã KH\tSố lượng\n"
    "DH-9001\t05/09/2026\tAn Phát JSC\tCUST-ANPHAT\t10\n"
    "DH-9001\t05/09/2026\tAn Phát JSC\tCUST-ANPHAT\t4\n"
    "DH-9002\t06/09/2026\tHà Nội New Co\tCUST-HNNEW\t2\n"
    "DH-9003\t07/09/2026\tKhách thiếu mã\t\t1\n"
)


def test_getfly_reader_column_map_is_shared_not_duplicated():
    """The Excel path and the paste path must use ONE keyword map."""
    from core.getfly_reader import GETFLY_COLUMN_KEYWORDS, customer_rows_from_text

    assert GETFLY_COLUMN_KEYWORDS["customer_name"] == ["tên kh", "khách hàng"]
    extracted = customer_rows_from_text(GETFLY_TABBED)
    assert [row["id"] for row in extracted["rows"]] == ["CUST-ANPHAT", "CUST-HNNEW"]
    assert extracted["orders"] == ["DH-9001", "DH-9002", "DH-9003"]
    # A customer without a code is reported, never given an invented id.
    assert extracted["skipped"] == ["Khách thiếu mã"]


def test_getfly_import_creates_only_new_customers_through_the_canonical_writer(staging, event_seq):
    from core.database import load_customers

    before = set(load_customers() or {})
    assert "CUST-ANPHAT" in before, "seed already knows An Phát → duplicate path"

    out = _dispatch(event_seq, "customer_getfly_import", {"text": GETFLY_TABBED, "requestId": "REQ-GF-1"})
    assert out["ok"], out["error"]
    assert out["requestId"] == "REQ-GF-1"

    after = load_customers() or {}
    assert "CUST-HNNEW" in after, "new GetFly customer must be persisted"
    assert after["CUST-HNNEW"]["name"] == "Hà Nội New Co"
    # Deduped by customer: the repeated DH-9001 rows create nothing extra.
    assert set(after) - before == {"CUST-HNNEW"}
    # The row without a code is skipped, not invented.
    assert "Khách thiếu mã" not in {doc.get("name") for doc in after.values()}
    assert out["skippedMissing"] == ["Khách thiếu mã"]


def test_getfly_import_readback_proves_persistence_not_transport(staging, event_seq):
    out = _dispatch(event_seq, "customer_getfly_import", {"text": GETFLY_TABBED})
    imported = {row["id"] for row in out["customers"]}
    assert imported == {"CUST-ANPHAT", "CUST-HNNEW"}
    # The view-model the component reads must contain the new customer too.
    model = vm.build_view_model()
    assert any(c["id"] == "CUST-HNNEW" for c in model["customers"])


def test_getfly_import_fails_closed_without_a_header_or_data(staging, event_seq):
    from core.database import load_customers

    before = set(load_customers() or {})

    no_header = _dispatch(event_seq, "customer_getfly_import", {"text": "abc\ndef\n"})
    assert not no_header["ok"] and "tiêu đề" in no_header["error"]

    empty = _dispatch(event_seq, "customer_getfly_import", {"text": ""})
    assert not empty["ok"]

    assert set(load_customers() or {}) == before, "refused imports must write nothing"


def test_getfly_import_is_not_a_second_event_family(staging):
    """Reuse rule: one importer, no new collection, no new writer."""
    assert "customer_getfly_import" in logi_c1.C1_EVENTS
    assert logi_c1.C1_EVENTS <= vm.ALL_EVENTS
    assert logi_c1._HANDLERS["customer_getfly_import"] is not None
    from core.database import get_db

    db = get_db()
    names = set(db.list_collection_names()) if db is not None else set()
    assert not {name for name in names if "getfly" in name.lower()}


def test_pl_and_date_and_customer_save_is_one_atomic_round_trip(staging, event_seq):
    """The three new fields travel together and all come back from the store."""
    out = _dispatch(event_seq, "contract_save", {
        "id": "HDMB-0306", "pl_required": "Không cần PL", "date": "2026-08-01",
        "customerId": "CUST-THIENAN",
    })
    assert out["ok"], out["error"]
    stored = _stored("HDMB-0306")
    assert stored["pl_required"] == "NO"
    assert stored["date"] == "2026-08-01"
    assert stored["customer_id"] == "CUST-THIENAN"
    read = out["readback"]
    assert (read["plRequired"], read["contractDate"], read["customerId"]) == (
        "NO", "2026-08-01", "CUST-THIENAN",
    )
