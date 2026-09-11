"""LOGI_NOTEBOOK_WORKSPACE_01 — focused tests for the read-only /so-tay handbook.

The handbook is a *presentation* slice over material that already exists in the
repository. These tests therefore assert passthrough and absence-of-invention
rather than content volume:

* every displayed row equals the canonical source value it came from;
* section provenance carries only what the source records (registry version,
  evidence status), never a manufactured date or owner;
* a deployment with no team notes yields an honest empty section, not a sample
  article;
* the staging view-model exposes the slice;
* no authoring/search/CMS surface was introduced with the page.

Production database is never used.
"""

from __future__ import annotations

import pytest

from views import handbook as hb


# ---------------------------------------------------------------------------
# content is passthrough, never paraphrase
# ---------------------------------------------------------------------------

def test_status_rows_equal_the_config_constants_verbatim():
    from core.config import STATUS_LABELS, STATUS_MAP_FWD, STATUS_OPTIONS

    projection = hb.handbook_projection(field_paths={})
    entry = projection["sections"][0]["entries"][0]
    table = entry["table"]

    assert table["rows"] == [
        [code, STATUS_LABELS[code], STATUS_MAP_FWD[code]] for code in STATUS_OPTIONS
    ]
    assert len(table["rows"]) == len(STATUS_OPTIONS)


def test_service_code_rows_equal_the_getfly_catalogue():
    from core.config import GETFLY_SERVICES_LIST, INCOTERMS

    projection = hb.handbook_projection(field_paths={})
    section = next(s for s in projection["sections"] if s["id"] == "dich-vu")
    codes, services, units, groups = zip(
        *(
            (row[0], row[1], row[2], row[3])
            for row in section["entries"][0]["table"]["rows"]
        )
    )

    assert list(codes) == [item["code"] for item in GETFLY_SERVICES_LIST]
    assert list(services) == [item["name"] for item in GETFLY_SERVICES_LIST]
    assert list(units) == [item["unit"] for item in GETFLY_SERVICES_LIST]
    assert list(groups) == [item["group"] for item in GETFLY_SERVICES_LIST]
    # Incoterms are surfaced as accepted input values only — no rule text added.
    incoterms = section["entries"][1]["table"]
    assert [row[0] for row in incoterms["rows"]] == list(INCOTERMS)
    assert incoterms["rows"][0] == [INCOTERMS[0]]


def test_document_checklist_rows_come_from_the_existing_reader():
    from views.logi_real_data import document_checklist

    projection = hb.handbook_projection(field_paths={})
    section = next(s for s in projection["sections"] if s["id"] == "chung-tu")
    rows = section["entries"][0]["table"]["rows"]
    expected = document_checklist({})

    assert [row[0] for row in rows] == [item["name"] for item in expected]
    # The note column stays the reader's own "not yet" default: the page does not
    # claim any per-shipment completion state of its own.
    assert [row[1] for row in rows] == [item["note"] for item in expected]


def test_docgen_rows_come_from_the_locked_rule_constants():
    from core.docgen import rules

    projection = hb.handbook_projection(field_paths={})
    section = next(s for s in projection["sections"] if s["id"] == "chung-tu")
    entry = section["entries"][1]

    assert [row[0] for row in entry["table"]["rows"]] == list(rules.DOCUMENT_TYPES)
    assert [row[1] for row in entry["table"]["rows"]] == [
        rules._DOC_NAME[code] for code in rules.DOCUMENT_TYPES  # noqa: SLF001
    ]


def test_stage_rows_are_derived_from_the_write_whitelist():
    field_paths = {
        "tk_no": ("data", "2.4", "tk_no"),
        "etd": ("data", "1.2", "etd"),
        "container_no": ("data", "1.2", "container_no"),
        "status": ("status",),
    }
    projection = hb.handbook_projection(field_paths=field_paths)
    rows = dict(projection["sections"][0]["entries"][1]["table"]["rows"])

    assert rows["data.2.4"] == "tk_no"
    assert rows["data.1.2"] == "container_no, etd"
    assert rows["(đỉnh lô hàng)"] == "status"
    # Nothing invented: only the four supplied paths are listed.
    assert sum(len(value.split(", ")) for value in rows.values()) == 4


def test_carrier_and_rbac_rows_pass_through_their_sources():
    from core.auth import ROLE_PERMISSIONS
    from core.config import CARRIER_LINKS

    projection = hb.handbook_projection(field_paths={})
    section = next(s for s in projection["sections"] if s["id"] == "cong-cu")
    carriers = {row[0]: row[1] for row in section["entries"][0]["table"]["rows"]}
    roles = {row[0]: row[1] for row in section["entries"][1]["table"]["rows"]}

    assert carriers == dict(CARRIER_LINKS)
    assert set(roles) == set(ROLE_PERMISSIONS)
    assert roles["admin"] == "*"
    assert roles["viewer"] == ", ".join(sorted(ROLE_PERMISSIONS["viewer"]))


def test_official_source_rows_keep_discovery_status_and_version():
    from core.trade_compliance.sources import load_official_source_registry

    registry = load_official_source_registry()
    projection = hb.handbook_projection(field_paths={})
    section = next(s for s in projection["sections"] if s["id"] == "hai-quan")
    entry = section["entries"][0]

    assert section["provenance"]["version"] == registry.version
    assert registry.registry_id in section["provenance"]["source"]
    assert [row[1] for row in entry["table"]["rows"]] == [
        record.authority
        for _jurisdiction, records in sorted(registry.jurisdictions.items())
        for record in records
    ]
    # Honest evidence state survives: nothing here is presented as verified.
    assert all(row[4] == "NOT_RETRIEVED" for row in entry["table"]["rows"])


# ---------------------------------------------------------------------------
# provenance honesty: absent metadata stays absent
# ---------------------------------------------------------------------------

def test_provenance_never_invents_date_or_owner():
    projection = hb.handbook_projection(field_paths={})
    for section in projection["sections"]:
        provenance = section["provenance"]
        assert provenance["source"]
        if section["id"] != "hai-quan":
            assert provenance["version"] is None
        # No source in this repo records an owner/date for these constants.
        assert provenance["updated"] is None
        assert provenance["owner"] is None


# ---------------------------------------------------------------------------
# empty content stays empty
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("notes", [None, [], ""])
def test_missing_note_corpus_is_reported_not_filled(notes):
    projection = hb.handbook_projection(field_paths={}, notes=notes or [])
    section = next(s for s in projection["sections"] if s["id"] == "ghi-chu")

    assert section["entries"] == []
    assert section["state"] is not None
    assert "không tự soạn" in section["state"]["text"].lower()
    assert projection["counts"]["noteCount"] == 0
    assert "Ghi chú đội ngũ" in projection["sectionsUnavailable"]
    assert projection["counts"]["availableSectionCount"] == projection["counts"]["sectionCount"] - 1


def test_note_rows_keep_their_own_recorded_metadata():
    notes = [
        {
            "id": "kb-1",
            "title": "Hàng NK cần bill gốc trước khi giao",
            "category": "📄 Chứng Từ (Docs)",
            "content": "Khách yêu cầu bản gốc tại cảng.",
            "tags": ["bill gốc", "giao hàng"],
            "date": "04/09/2026 09:12",
        },
        {"id": "kb-2", "title": "Ghi chú không ngày"},
    ]
    projection = hb.handbook_projection(field_paths={}, notes=notes)
    section = next(s for s in projection["sections"] if s["id"] == "ghi-chu")
    first, second = section["entries"]

    assert first["summary"] == "Khách yêu cầu bản gốc tại cảng."
    assert first["provenance"]["updated"] == "04/09/2026 09:12"
    assert first["tags"] == ["bill gốc", "giao hàng"]
    assert "📄 Chứng Từ (Docs)" in first["bullets"][0]
    # An entry without a recorded date says so; it is not back-dated to today.
    assert second["provenance"]["updated"] is None
    assert "Cập nhật: chưa ghi nhận" in second["bullets"]
    assert projection["counts"]["noteCount"] == 2
    assert "Ghi chú đội ngũ" in projection["sectionsAvailable"]


def test_non_mapping_note_rows_are_ignored():
    projection = hb.handbook_projection(field_paths={}, notes=["stray", None])
    section = next(s for s in projection["sections"] if s["id"] == "ghi-chu")
    assert section["entries"] == []


# ---------------------------------------------------------------------------
# scope honesty
# ---------------------------------------------------------------------------

def test_projection_declares_read_only_scope_limits():
    projection = hb.handbook_projection(field_paths={})

    assert projection["classification"] == "STATIC_CONTENT_READY"
    assert projection["readOnly"] is True
    assert any("Incoterm" in line for line in projection["unavailable"])
    assert any("hướng dẫn từng bước" in line for line in projection["unavailable"])
    assert projection["counts"]["entryCount"] == sum(
        len(section["entries"]) for section in projection["sections"]
    )


def test_no_authoring_or_search_surface_was_added():
    from views import logi_view_model as vm

    # The page needs no server-side action: no event, no writer, no index.
    assert not any(
        token in name
        for name in vm.ALL_EVENTS
        for token in ("note", "handbook", "knowledge", "article", "publish")
    )
    projection = hb.handbook_projection(field_paths={})
    assert "search" not in projection
    assert not any("index" in section for section in projection)


# ---------------------------------------------------------------------------
# the bridge that activates the route
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Clean, isolated mongomock staging database with the deterministic actor.

    The actor is restored to whatever the session held before, so this fixture
    cannot leak a logged-in user into an unrelated test (a pre-existing hazard
    in the repo's staging fixtures).
    """
    import streamlit as st

    from views import logi_sandbox

    previous = st.session_state.get("current_user")
    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    logi_sandbox.reset_backend()
    if previous is None:
        st.session_state.pop("current_user", None)
    else:
        st.session_state["current_user"] = previous


def test_view_model_exposes_the_handbook_slice_on_staging(staging):
    from views import logi_view_model as vm

    model = vm.build_view_model()
    handbook = model["handbook"]

    assert handbook["readOnly"] is True
    assert handbook["counts"]["sectionCount"] == 6
    # Static reference material is always present; notes depend on the database.
    assert handbook["counts"]["entryCount"] >= 8
    assert handbook["counts"]["availableSectionCount"] >= 5
    for section in handbook["sections"]:
        assert section["id"] in hb.SECTION_IDS
        assert section["provenance"]["source"]
    # Every delivered row is non-empty: no decorative placeholder cell.
    for section in handbook["sections"]:
        for entry in section["entries"]:
            assert entry["title"] and entry["summary"]
            if entry["table"]:
                assert all(any(cell.strip() for cell in row) for row in entry["table"]["rows"])
