"""LOGI_COMPANY_IDENTITY_TRUTH_01 — company identity authority evidence.

Proves the Owner-confirmed separation between:

A. DISPLAY identity — the operating brand on ordinary surfaces
   (browser tab title, login card, shell header subtitle). ONE bounded
   authority: ``core.config.DISPLAY_COMPANY_NAME`` (env ``DISPLAY_COMPANY_NAME``
   or secrets ``[display].company_name``; default ``Trường Thành Logistics``).

B. LEGAL identity — the formal company used by contracts, payments and
   PXK/GNT document generation, which MUST keep deriving from the
   ``authority_companies`` master (``core.database.load_authority_companies``).

Hard guards encoded here:
  * no surface presents ``Phú Anh Logistics`` as the operating brand;
  * the company party for finance keeps following the authority master
    verbatim — the display brand is never substituted for a legal_name and
    no statutory fact (tax code, address, representative, bank) is fabricated;
  * the staging legal master (authority_companies seed) keeps carrying the
    Trường Thành company record untouched.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

OWNER_DISPLAY_COMPANY_NAME = "Trường Thành Logistics"
STAGING_LEGAL_NAME = "CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH"


# ---------------------------------------------------------------------------
# A. The ONE display identity authority
# ---------------------------------------------------------------------------


def test_display_authority_default_is_owner_confirmed_brand():
    from core.config import DISPLAY_COMPANY_NAME

    assert DISPLAY_COMPANY_NAME == OWNER_DISPLAY_COMPANY_NAME


def _run_config_probe(env_extra: dict[str, str], assertions: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        secret_path = Path(temp_dir) / "secrets.toml"
        secret_path.write_text(
            textwrap.dedent(
                """
                [display]
                company_name = "Hiển Thị Từ Secrets"
                """
            ),
            encoding="utf-8",
        )
        env = os.environ.copy()
        # Isolate from any local secrets file; only the probes' inputs count.
        env["LOGISTICS_PRO_SECRETS_FILE"] = str(secret_path)
        for key in ("DISPLAY_COMPANY_NAME", "MONGO_URI"):
            env.pop(key, None)
        env.update(env_extra)
        env["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
            [sys.executable, "-c", assertions],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )


def test_display_authority_env_override_wins_over_secrets_and_default():
    result = _run_config_probe(
        {"DISPLAY_COMPANY_NAME": "Hiển Thị Từ Env"},
        "from core.config import DISPLAY_COMPANY_NAME\n"
        "assert DISPLAY_COMPANY_NAME == 'Hiển Thị Từ Env', DISPLAY_COMPANY_NAME\n",
    )
    assert result.returncode == 0, result.stderr


def test_display_authority_secrets_override_wins_over_default():
    result = _run_config_probe(
        {},
        "from core.config import DISPLAY_COMPANY_NAME\n"
        "assert DISPLAY_COMPANY_NAME == 'Hiển Thị Từ Secrets', DISPLAY_COMPANY_NAME\n",
    )
    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# Ordinary surfaces read the ONE authority (login card + shell subtitle input)
# ---------------------------------------------------------------------------


def test_login_screen_carries_display_brand_not_phu_anh():
    import core.auth

    identity = core.auth._LOGIN_IDENTITY_HTML
    assert f"{OWNER_DISPLAY_COMPANY_NAME} · Nội bộ" in identity
    assert "Phú Anh" not in identity


def test_auth_gate_boot_renders_no_phu_anh_brand(monkeypatch):
    """AUTH_REQUIRED=true boots the real auth gate without exceptions, and
    whatever card the gate shows (login card once users exist, first-admin
    bootstrap card on a fresh store), Phú Anh never renders as the brand.
    The login card constant itself is asserted in
    ``test_login_screen_carries_display_brand_not_phu_anh``."""
    import streamlit.testing.v1 as st_testing

    monkeypatch.setenv("AUTH_REQUIRED", "true")
    at = st_testing.AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, f"app raised: {[str(e.value) for e in at.exception]}"
    rendered = "\n".join(block.value for block in at.markdown)
    assert "Phú Anh" not in rendered


def test_view_model_environment_carries_display_name(staging_identity):
    from core.config import DISPLAY_COMPANY_NAME
    from views import logi_view_model

    vm = logi_view_model.build_view_model()
    assert vm["environment"]["displayName"] == DISPLAY_COMPANY_NAME
    assert vm["environment"]["displayName"] == OWNER_DISPLAY_COMPANY_NAME


@pytest.fixture()
def staging_identity():
    """Isolated staging transport + deterministic actor (same shape as the
    docgen reality-check suite) — no production database is ever touched.

    Teardown FULLY clears the actor: bare-mode ``st.session_state`` is
    process-global across test files, and leaving a signed-in actor behind
    would break later unauthenticated assertions (e.g. the LOG-C15 RBAC
    viewer-fallback check)."""
    import streamlit as st

    from views import logi_sandbox

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state.pop("current_user", None)
    logi_sandbox.reset_backend()


# ---------------------------------------------------------------------------
# B. LEGAL identity still derives from authority_companies — never the brand
# ---------------------------------------------------------------------------


def test_company_party_follows_authority_master_verbatim(monkeypatch):
    from views import logi_view_model

    sentinel = {
        "CMP-PROBE": {
            "company_id": "CMP-PROBE",
            "id": "CMP-PROBE",
            "legal_name": "CÔNG TY TNHH PROBE MASTER",
        }
    }

    import core.database

    monkeypatch.setattr(core.database, "load_authority_companies", lambda: dict(sentinel))
    party = logi_view_model._company_party()
    assert party is not None
    assert party["party_type"] == "company"
    assert party["party_id"] == "CMP-PROBE"
    # The payer name is whatever the LEGAL MASTER says — even if it differs
    # from the display brand. The display brand must never be substituted.
    assert party["name"] == "CÔNG TY TNHH PROBE MASTER"
    assert party["name"] != OWNER_DISPLAY_COMPANY_NAME


def test_company_party_fails_closed_without_authority_master(monkeypatch):
    import core.database
    from views import logi_view_model

    monkeypatch.setattr(core.database, "load_authority_companies", lambda: {})
    # No master → no payer identity is invented (no fabricated legal facts).
    assert logi_view_model._company_party() is None


def test_staging_authority_master_keeps_company_legal_record_intact():
    from views import logi_staging_seed

    companies = logi_staging_seed.AUTHORITY_COMPANIES
    assert len(companies) == 1
    company = companies[0]
    assert company["legal_name"] == STAGING_LEGAL_NAME
    # Statutory facts stay present and untouched by this task (no fabrication,
    # no display-brand substitution inside the legal master).
    for field in (
        "tax_or_legal_code",
        "legal_address",
        "legal_representative",
        "bank_account_holder",
        "bank_account_number",
        "bank_name",
    ):
        assert str(company.get(field) or "").strip(), f"legal master missing {field}"
    # The display brand is not a legal master record.
    assert company["legal_name"] != OWNER_DISPLAY_COMPANY_NAME


def test_phu_anh_is_an_agent_master_record_not_the_company():
    from views import logi_staging_seed

    agent_ids = {a.get("id") for a in logi_staging_seed.AUTHORITY_AGENTS}
    assert "AGT-PHUANH" in agent_ids
    for company in logi_staging_seed.AUTHORITY_COMPANIES:
        assert "PHÚ ANH" not in str(company.get("legal_name", "")).upper()
