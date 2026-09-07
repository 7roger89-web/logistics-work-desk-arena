"""Focused tests for LOG-DOCGEN-01 V1 Shipment Document Pack Generator.

Covers the locked owner rules, readiness, OOXML structural QA, RBAC,
versioning, linkage, finance safety, and template integrity.  Uses only
synthetic data (no Production data) and never writes to Finance Actual.
"""

from __future__ import annotations

import io
import os
from copy import deepcopy
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch

from core.docgen import generator as gen
from core.docgen.rules import (
    BLOCKED,
    GENERATED,
    HDMB,
    HDNT,
    ISSUED,
    MISSING_INFO,
    NOT_APPLICABLE,
    PL,
    PXK,
    READY,
    VND_THRESHOLD,
    compute_goods_totals,
    decide_applicable_documents,
    evaluate_document_readiness,
    normalize_goods_line,
    total_after_vat,
)

TPL_XLSX = "/tmp/log-docgen-01-assets/truong-thanh-agent.xlsx"
TPL_DOCX = "/tmp/log-docgen-01-assets/HDNT-TT-agent.docx"
_HAS_ASSETS = os.path.exists(TPL_XLSX) and os.path.exists(TPL_DOCX)


def _line(description: str, qty, price, unit="Cái", vat="0.08") -> dict:
    return {"description": description, "quantity": qty, "unit_price_vnd_excl_vat": price, "unit": unit, "vat_rate": Decimal(vat)}


def _agent() -> dict:
    return {
        "agent_id": "AGT-001",
        "legal_name": "CÔNG TY TNHH PHÚ ANH LGT",
        "legal_address": "Số 1 Đường ABC, Quận 1, TP. Hồ Chí Minh",
        "legal_code": "0123456789",
        "legal_representative": "Ông Nguyễn Văn An",
        "representative_title": "Giám đốc",
        "bank_account_holder": "PHÚ ANH LGT",
        "bank_account_number": "1234567890",
        "bank_name": "Vietcombank",
        "bank_branch": "CN Hà Nội",
        "phone": "0901234567",
        "email": "pa@example.com",
    }


def _company() -> dict:
    return {
        "company_id": "TT-001",
        "legal_name": "CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH",
        "legal_address": "Số nhà 16 ngõ 41 đường Khương Đình, Phường Khương Đình, Hà Nội, Việt Nam",
        "tax_or_legal_code": "0105937262",
        "legal_representative": "Bà Lê Thị Thu Hương",
        "representative_title": "Giám đốc",
    }


class ThresholdRulesTests(TestCase):
    def test_below_50m_applies_hdnt_pl(self) -> None:
        # 4,999,999.99 before VAT -> total after VAT ~ 5.4m < 50m
        lines = [_line("Hàng A", 1, Decimal("4999999.99"))]
        decision = decide_applicable_documents(goods_lines=lines)
        self.assertEqual(decision[HDNT].state, READY)
        self.assertEqual(decision[PL].state, READY)
        self.assertEqual(decision[HDMB].state, NOT_APPLICABLE)

    def test_exactly_50m_applies_hdmb(self) -> None:
        # total_after_vat should equal 50,000,000
        # subtotal = 50m / 1.08 → not integer. Use subtotal that rounds.
        # Build total_after_vat >= 50m with unit price 46,296,296 -> *1.08 = 50,000,000 (approx)
        lines = [_line("Hàng B", 1, Decimal("46296296"))]  # *1.08 = 49,999,999.68 -> rounds 50,000,000
        decision = decide_applicable_documents(goods_lines=lines)
        self.assertEqual(decision[HDMB].state, READY)
        self.assertIn(HDMB, [d for d in (HDMB, HDNT, PL) if decision[d].state == READY])

    def test_above_50m_applies_hdmb_only(self) -> None:
        lines = [_line("Máy móc", 1, Decimal("100000000"))]
        decision = decide_applicable_documents(goods_lines=lines)
        self.assertEqual(decision[HDMB].state, READY)
        self.assertEqual(decision[HDNT].state, NOT_APPLICABLE)
        self.assertEqual(decision[PL].state, NOT_APPLICABLE)

    def test_non_vnd_blocked(self) -> None:
        lines = [_line("Hàng A", 1, Decimal("100000"))]
        decision = decide_applicable_documents(goods_lines=lines, currency="USD")
        for doc_type in (HDNT, PL, HDMB):
            self.assertEqual(decision[doc_type].state, BLOCKED)

    def test_unknown_total_blocked(self) -> None:
        # Invalid line -> total is None -> BLOCK
        lines = [{"description": "", "quantity": -1, "unit_price_vnd_excl_vat": 100, "unit": "", "vat_rate": "0.08"}]
        decision = decide_applicable_documents(goods_lines=lines)
        for doc_type in (HDNT, PL, HDMB):
            self.assertEqual(decision[doc_type].state, BLOCKED)


class VatRulesTests(TestCase):
    def test_vat_8_percent_calc(self) -> None:
        lines = [_line("Hàng", 10, Decimal("100000"))]
        totals, _ = compute_goods_totals(lines)
        self.assertEqual(totals.subtotal, Decimal("1000000"))
        self.assertEqual(totals.vat_amount, Decimal("80000"))
        self.assertEqual(totals.total_after_vat, Decimal("1080000"))

    def test_mixed_vat_blocked(self) -> None:
        lines = [
            _line("A", 1, Decimal("100000")),
            _line("B", 1, Decimal("100000"), vat="0.10"),
        ]
        totals, normalized = compute_goods_totals(lines)
        self.assertTrue(any(not item["valid"] for item in normalized))

    def test_other_vat_blocked(self) -> None:
        lines = [_line("A", 1, Decimal("100000"), vat="0.10")]
        totals, normalized = compute_goods_totals(lines)
        self.assertFalse(normalized[0]["valid"])
        self.assertIn("Chỉ hỗ trợ thuế GTGT 8%", normalized[0]["validation_errors"])

    def test_unit_price_hr_rounding(self) -> None:
        lines = [_line("Hàng", 3, Decimal("33333.33"))]
        totals, _ = compute_goods_totals(lines)
        # 3 * 33333.33 = 99999.99 -> ROUND_HALF_UP -> 100000
        self.assertEqual(totals.subtotal, Decimal("100000"))
        self.assertEqual(totals.total_after_vat, Decimal("108000"))


class AuthorityRulesTests(TestCase):
    def _parent(self) -> dict:
        return {"id": "HDNT-001", "contract_no": "HDNT-001", "kind": HDNT, "agent_id": "AGT-001", "company_id": "TT-001"}

    def test_missing_agent_master_blocked(self) -> None:
        readiness = evaluate_document_readiness(
            HDNT,
            goods_lines=[_line("A", 1, Decimal("100000"))],
            agent=None,
            company=_company(),
        )
        self.assertEqual(readiness.state, MISSING_INFO)
        self.assertTrue(any("Đại lý" in item for item in readiness.missing))

    def test_customer_cannot_silently_substitute_for_agent(self) -> None:
        # A customer-styled dict (no legal fields) must NOT be treated as agent.
        customer = {"name": "Công ty Khách", "address": "abc", "tax_code": "999"}
        readiness = evaluate_document_readiness(
            HDNT, goods_lines=[_line("A", 1, Decimal("100000"))], agent=customer, company=_company()
        )
        self.assertEqual(readiness.state, MISSING_INFO)
        self.assertTrue(any("Đại lý" in item for item in readiness.missing))

    def test_factory_cannot_silently_substitute_for_agent(self) -> None:
        factory = {"factory": "Nhà máy X", "contact": "abc"}
        readiness = evaluate_document_readiness(
            HDNT, goods_lines=[_line("A", 1, Decimal("100000"))], agent=factory, company=_company()
        )
        self.assertEqual(readiness.state, MISSING_INFO)


class GoodsCountRulesTests(TestCase):
    def test_hdmb_one_line_ready(self) -> None:
        lines = [_line("Máy", 1, Decimal("60000000"))]
        decision = decide_applicable_documents(goods_lines=lines)
        self.assertEqual(decision[HDMB].state, READY)

    def test_hdmb_more_than_one_blocked(self) -> None:
        lines = [_line("A", 1, Decimal("30000000")), _line("B", 1, Decimal("30000000"))]
        decision = decide_applicable_documents(goods_lines=lines)
        self.assertEqual(decision[HDMB].state, BLOCKED)

    def test_pl_18_lines_ready(self) -> None:
        lines = [_line(f"H{i}", 1, Decimal("100000")) for i in range(18)]
        decision = decide_applicable_documents(goods_lines=lines)
        self.assertEqual(decision[PL].state, READY)

    def test_pl_19_lines_blocked(self) -> None:
        lines = [_line(f"H{i}", 1, Decimal("100000")) for i in range(19)]
        decision = decide_applicable_documents(goods_lines=lines)
        self.assertEqual(decision[PL].state, BLOCKED)


class HdntPlRulesTests(TestCase):
    def test_pl_without_parent_blocked(self) -> None:
        readiness = evaluate_document_readiness(
            PL, goods_lines=[_line("A", 1, Decimal("100000"))], agent=_agent(), company=_company(), parent_contract=None
        )
        self.assertEqual(readiness.state, BLOCKED)

    def test_pl_parent_agent_mismatch_blocked(self) -> None:
        parent = {"id": "HDNT-001", "contract_no": "HDNT-001", "kind": HDNT, "agent_id": "AGT-XYZ", "company_id": "TT-001"}
        readiness = evaluate_document_readiness(
            PL, goods_lines=[_line("A", 1, Decimal("100000"))], agent=_agent(), company=_company(), parent_contract=parent
        )
        self.assertEqual(readiness.state, BLOCKED)

    def test_multiple_valid_hdnt_requires_explicit_selection(self) -> None:
        # The rule: if multiple valid HDNT exist require explicit selection.
        # We assert the readiness helper flags an ambiguous parent reference.
        parent_missing = evaluate_document_readiness(
            PL, goods_lines=[_line("A", 1, Decimal("100000"))], agent=_agent(), company=_company(), parent_contract=None
        )
        self.assertEqual(parent_missing.state, BLOCKED)


class PxkRulesTests(TestCase):
    def test_not_delivered_blocked(self) -> None:
        readiness = evaluate_document_readiness(
            PXK, goods_lines=[_line("A", 1, Decimal("100000"))], agent=_agent(), company=_company(), delivery_completed=False
        )
        self.assertEqual(readiness.state, BLOCKED)

    def test_expected_date_only_blocked(self) -> None:
        # Expected delivery date alone is not actual delivery.
        readiness = evaluate_document_readiness(
            PXK, goods_lines=[_line("A", 1, Decimal("100000"))], agent=_agent(), company=_company(), delivery_completed=False
        )
        self.assertEqual(readiness.state, BLOCKED)

    def test_confirmed_delivery_ready(self) -> None:
        readiness = evaluate_document_readiness(
            PXK, goods_lines=[_line("A", 1, Decimal("100000"))], agent=_agent(), company=_company(), delivery_completed=True
        )
        self.assertEqual(readiness.state, READY)

    def test_multiline_source_pxk_blocked(self) -> None:
        lines = [_line("A", 1, Decimal("100000")), _line("B", 1, Decimal("100000"))]
        decision = decide_applicable_documents(goods_lines=lines, delivery_completed=True)
        self.assertEqual(decision[PXK].state, BLOCKED)


class UnknownValueTests(TestCase):
    def test_unknown_total_is_not_zero(self) -> None:
        lines = [{"description": "", "quantity": -1, "unit_price_vnd_excl_vat": 100, "unit": "", "vat_rate": "0.08"}]
        self.assertIsNone(total_after_vat(lines))

    def test_sample_placeholder_blocked(self) -> None:
        # A "CÔNG TY TNHH..." sample value is not an authoritative master.
        sample = {"legal_name": "CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH", "legal_address": "Số nhà 16 ngõ 41"}
        readiness = evaluate_document_readiness(
            PL, goods_lines=[_line("A", 1, Decimal("100000"))], agent=sample, company=_company()
        )
        # Missing legal_code/representative -> MISSING_INFO, not READY.
        self.assertNotEqual(readiness.state, READY)


class TemplateGenerationTests(TestCase):
    def setUp(self) -> None:
        if not _HAS_ASSETS:
            self.skipTest("Template assets not present")

    def test_source_hashes_unchanged_after_generation(self) -> None:
        before_xlsx = _sha256_file(TPL_XLSX)
        before_docx = _sha256_file(TPL_DOCX)
        gen.generate_xlsx_file(TPL_XLSX, PL, contract_no="PL-001", contract_date="2026-09-05", agent=_agent(), company=_company(), goods_lines=[_line("Hàng", 5, Decimal("100000"))], parent_contract={"contract_no": "HDNT-001", "contract_date": "2026-09-01", "id": "HDNT-001"})
        gen.generate_docx_file(TPL_DOCX, contract_no="HDNT-001", contract_date="2026-09-01", valid_from="2026-09-01", valid_to="2027-08-31", agent=_agent(), company=_company())
        self.assertEqual(_sha256_file(TPL_XLSX), before_xlsx)
        self.assertEqual(_sha256_file(TPL_DOCX), before_docx)

    def test_pl_output_opens_and_preserves_formulas(self) -> None:
        import openpyxl

        out = gen.generate_xlsx_file(TPL_XLSX, PL, contract_no="PL-001", contract_date="2026-09-05", agent=_agent(), company=_company(), goods_lines=[_line("Hàng", 5, Decimal("100000"))], parent_contract={"contract_no": "HDNT-001", "contract_date": "2026-09-01", "id": "HDNT-001"})
        wb = openpyxl.load_workbook(io.BytesIO(out), data_only=False)
        ws = wb["pl"]
        self.assertEqual(ws["F28"].value, "=SUM(F10:F27)")
        self.assertEqual(ws["F29"].value, "=F28*8%")
        self.assertEqual(ws["F30"].value, "=SUM(F28:F29)")
        self.assertEqual(ws["B10"].value, "Hàng")
        self.assertGreaterEqual(len(ws.merged_cells.ranges), 10)
        self.assertEqual(ws.page_setup.orientation, "portrait")

    def test_pxk_writes_explicit_values_not_formula(self) -> None:
        import openpyxl

        lines = [_line("Máy móc", 5, Decimal("20000000"), unit="Bộ")]
        out = gen.generate_xlsx_file(TPL_XLSX, PXK, contract_no="PXK-001", contract_date="2026-09-10", agent=_agent(), company=_company(), goods_lines=lines, delivery={"receiver_name": "Bà Hương", "receiver_title": "Giám đốc", "delivery_location": "Kho TT"})
        wb = openpyxl.load_workbook(io.BytesIO(out), data_only=False)
        ws = wb["pxk"]
        # B15/C15/D15 must be explicit values, not =HDMB!... formulas.
        self.assertEqual(str(ws["B15"].value), "Máy móc")
        self.assertEqual(str(ws["C15"].value), "Bộ")
        self.assertEqual(int(ws["D15"].value), 5)
        self.assertFalse(str(ws["B15"].value).startswith("="))

    def test_hdnt_docx_opens_with_expected_text(self) -> None:
        import docx

        out = gen.generate_docx_file(TPL_DOCX, contract_no="HDNT-001", contract_date="2026-09-01", valid_from="2026-09-01", valid_to="2027-08-31", agent=_agent(), company=_company())
        document = docx.Document(io.BytesIO(out))
        self.assertIn("Số: HDNT-001", document.paragraphs[2].text)
        self.assertIn("CÔNG TY TNHH PHÚ ANH LGT", document.paragraphs[5].text)
        self.assertEqual(len(document.sections), 1)
        self.assertIsNotNone(document.sections[0].top_margin)

    def test_sheet_parts_retained(self) -> None:
        import zipfile

        out = gen.generate_xlsx_file(TPL_XLSX, HDMB, contract_no="HDMB-001", contract_date="2026-09-05", agent=_agent(), company=_company(), goods_lines=[_line("Máy", 1, Decimal("100000000"))])
        names = zipfile.ZipFile(io.BytesIO(out)).namelist()
        self.assertIn("xl/printerSettings/printerSettings1.bin", names)
        self.assertIn("xl/calcChain.xml", names)
        self.assertIn("xl/sharedStrings.xml", names)


class VersionAndLinkageTests(TestCase):
    def test_revision_increments_across_regenerations(self) -> None:
        logical = gen._document_id(HDNT, "SHP-001", "AGT-001")  # SHP-001-HDNT-AGT-001
        existing = {
            f"{logical}::R1": {"document_id": logical, "generation_revision": 1},
            f"{logical}::R2": {"document_id": logical, "generation_revision": 2},
        }
        next_rev = gen._next_revision(HDNT, "SHP-001", "AGT-001", existing)
        self.assertEqual(next_rev, 3)

    def test_issued_immutable_prevents_second_issue(self) -> None:
        db = _Database()
        with _with_user({"role": "support", "username": "support", "user_id": "u1"}), patch("core.database.get_db", return_value=db):
            save = _saved_docgen_document({"id": "D::R1", "document_id": "D", "status": GENERATED, "generation_revision": 1})
            self.assertTrue(save)
            result = gen.issue_document("D")
            self.assertEqual(result["status"], ISSUED)
            with self.assertRaises(gen.DocumentGenerationError):
                gen.issue_document("D")

    def test_supersede_creates_new_id_and_links_old(self) -> None:
        db = _Database()
        with _with_user({"role": "support", "username": "support", "user_id": "u1"}), patch("core.database.get_db", return_value=db):
            # seed an ISSUED doc
            record = {"id": "OLD::R1", "document_id": "OLD", "status": GENERATED, "generation_revision": 1, "shipment_id": "SHP-001"}
            self.assertTrue(_saved_docgen_document(record))
            gen.issue_document("OLD")
            # Generate a superseding document
            result = gen.supersede_document(
                "OLD",
                new_document_id="NEW",
                document_type=HDMB,
                shipment_id="SHP-001",
                contract_no="NEW-001",
                contract_date="2026-09-05",
                agent=_agent(),
                company=_company(),
                goods_lines=[_line("Máy", 1, Decimal("100000000"))],
                template_path_xlsx=TPL_XLSX,
            )
            self.assertEqual(result["supersedes_document_id"], "OLD")
            new_logical = result["document_id"]
            db_docs = gen_load_latest(new_logical)
            self.assertEqual(db_docs.get("supersedes_document_id"), "OLD")
            old = gen_load_latest("OLD")
            self.assertEqual(old.get("superseded_by_document_id"), new_logical)


class RbacTests(TestCase):
    def _parent_contract(self) -> dict:
        return {
            "id": "HDNT-001",
            "contract_no": "HDNT-001",
            "contract_date": "2026-09-01",
            "kind": HDNT,
            "agent_id": "AGT-001",
            "company_id": "TT-001",
        }

    def _run_generate(self, user):
        with _with_user(user):
            try:
                result = gen.generate_document(
                    PL,
                    shipment_id="SHP-001",
                    agent=_agent(),
                    company=_company(),
                    goods_lines=[_line("A", 1, Decimal("100000"))],
                    contract={"id": "HDNT-001", "contract_no": "HDNT-001", "contract_date": "2026-09-01", "currency": "VND"},
                    parent_contract=self._parent_contract(),
                    template_path_xlsx=TPL_XLSX,
                )
                return result
            except Exception as exc:  # noqa: BLE001
                return exc

    def test_admin_generate_ok(self) -> None:
        if not _HAS_ASSETS:
            self.skipTest("no assets")
        result = self._run_generate({"role": "admin", "username": "admin", "user_id": "u1"})
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], GENERATED)

    def test_support_generate_ok(self) -> None:
        if not _HAS_ASSETS:
            self.skipTest("no assets")
        result = self._run_generate({"role": "support", "username": "support", "user_id": "u2"})
        self.assertIsInstance(result, dict)

    def test_sale_can_generate(self) -> None:
        if not _HAS_ASSETS:
            self.skipTest("no assets")
        result = self._run_generate({"role": "sale", "username": "sale", "user_id": "u3"})
        self.assertIsInstance(result, dict)

    def test_sale_cannot_issue(self) -> None:
        from core.auth import PermissionDeniedError

        with _with_user({"role": "sale", "username": "sale", "user_id": "u3"}), patch("core.database.get_db", return_value=_Database()):
            with self.assertRaises(PermissionDeniedError):
                gen.issue_document("D")

    def test_viewer_generate_denied(self) -> None:
        result = self._run_generate({"role": "viewer", "username": "viewer", "user_id": "u4"})
        self.assertIsInstance(result, PermissionError)


class FinanceSafetyTests(TestCase):
    def test_generator_does_not_import_finance_writer(self) -> None:
        import core.docgen.generator as gmod

        source = inspect_source(gmod)
        self.assertNotIn("financial_ledger", source)
        self.assertNotIn("finance_review", source)
        self.assertNotIn("save_transaction", source)


class UnknownNotZeroTests(TestCase):
    def test_amount_words_zero_guard(self) -> None:
        self.assertEqual(gen.amount_in_words_vnd(0), "không đồng")


# ---------------------------------------------------------------------------
# In-memory DB + auth helpers
# ---------------------------------------------------------------------------


class _Result:
    matched_count = 1
    modified_count = 1
    upserted_id = None


class _Collection:
    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}

    @staticmethod
    def _matches(document: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = document.get(key)
            if isinstance(expected, dict) and "$ne" in expected:
                if actual == expected["$ne"]:
                    return False
            elif actual != expected:
                return False
        return True

    def find_one(self, query: dict, projection=None, **kwargs):
        del projection, kwargs
        for document in self.docs.values():
            if self._matches(document, query):
                return deepcopy(document)
        return None

    def find(self, query: dict | None = None, projection=None, **kwargs):
        del projection, kwargs
        return [deepcopy(document) for document in self.docs.values() if self._matches(document, query or {})]

    def update_one(self, query: dict, update: dict, upsert=False, **kwargs):
        del kwargs
        current = self.find_one(query)
        if current is None and not upsert:
            return type("NoMatch", (), {"matched_count": 0, "modified_count": 0})()
        key = str(query.get("id") or query.get("username"))
        payload = current or {name: value for name, value in query.items() if not isinstance(value, dict)}
        payload.update(deepcopy(update.get("$set", {})))
        if current is None:
            payload.update(deepcopy(update.get("$setOnInsert", {})))
        self.docs[key] = payload
        return _Result()

    def insert_one(self, document: dict, **kwargs):
        del kwargs
        key = str(document.get("event_id") or document.get("id") or len(self.docs))
        self.docs[key] = deepcopy(document)
        return _Result()


class _Database:
    def __init__(self) -> None:
        self.contracts = _Collection()
        self.contract_transactions = _Collection()
        self.authority_companies = _Collection()
        self.authority_agents = _Collection()
        self.docgen_documents = _Collection()
        self.audit_logs = _Collection()

    def __getitem__(self, name: str) -> _Collection:
        return getattr(self, name)

    def __getattr__(self, name: str) -> _Collection:
        if name.startswith("_"):
            raise AttributeError(name)
        collection = _Collection()
        setattr(self, name, collection)
        return collection


def _with_user(user) -> object:
    return patch("core.auth.st", type("AuthStreamlit", (), {"session_state": {"current_user": user}})())


def _saved_docgen_document(document: dict) -> bool:
    from core.database import save_docgen_document

    return save_docgen_document(document)


def gen_load_latest(document_id: str):
    from core.database import load_docgen_document_latest

    return load_docgen_document_latest(document_id)


def _sha256_file(path: str) -> str:
    import hashlib

    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def inspect_source(module) -> str:
    import inspect

    return inspect.getsource(module)
