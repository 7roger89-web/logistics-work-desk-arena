"""Focused tests for Telegram -> NotebookLM domain routing."""

from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import patch

from core.notebooklm_telegram import (
    NotebookLMConfigError,
    _load_notebook_map,
    answer_notebook_question,
    route_question,
)


class RouterTests(unittest.TestCase):
    def test_wifi_question_routes_btttt(self):
        routed = route_question(
            "Router WiFi công nghiệp 2.4/5GHz có thuộc Bộ Thông tin quản lý không?"
        )
        self.assertIn("BTTTT", routed.domains)

    def test_chemical_hs_question_is_multi_label(self):
        routed = route_question(
            "Keo dán chứa Toluene 25%, CAS 108-88-3 thì mã HS nào?"
        )
        self.assertIn("CHEMICAL", routed.domains)
        self.assertIn("HS", routed.domains)

    def test_used_machine_quality_question_routes_bkhcn(self):
        routed = route_question(
            "Máy móc cũ nhập khẩu có phải kiểm tra chất lượng không?"
        )
        self.assertEqual(routed.domains[0], "BKHCN")

    def test_explicit_command_overrides_auto_router(self):
        routed = route_question("/hs router wifi mã nào")
        self.assertEqual(routed.domains, ("HS",))
        self.assertEqual(routed.question, "router wifi mã nào")
        self.assertTrue(routed.explicit)

    def test_unknown_question_does_not_guess_domain(self):
        routed = route_question("Khách gửi cái này, xem giúp em")
        self.assertEqual(routed.domains, ())

    def test_notebook_map_ignores_unknown_domains(self):
        result = _load_notebook_map(
            '{"HS":"hs-id","CHEMICAL":"chem-id","OTHER":"nope"}'
        )
        self.assertEqual(result, {"HS": "hs-id", "CHEMICAL": "chem-id"})


class _FakeRef:
    source_id = "src-1"
    citation_number = 1
    cited_text = "Đoạn nguồn liên quan"


class _FakeAsk:
    answer = "Câu trả lời có căn cứ [1]"
    references = [_FakeRef()]


class _FakeSource:
    id = "src-1"
    title = "Thông tư thử nghiệm"


class _FakeChat:
    async def ask(self, notebook_id, question):
        assert notebook_id == "hs-id"
        assert question == "mã HS của mặt hàng này"
        return _FakeAsk()


class _FakeSources:
    async def list(self, notebook_id):
        assert notebook_id == "hs-id"
        return [_FakeSource()]


class _FakeClient:
    def __init__(self):
        self.chat = _FakeChat()
        self.sources = _FakeSources()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeNotebookLMClient:
    @classmethod
    def from_storage(cls):
        return _FakeClient()


class AdapterTests(unittest.TestCase):
    def test_answer_uses_configured_notebook_and_surfaces_source_title(self):
        fake_module = types.ModuleType("notebooklm")
        fake_module.NotebookLMClient = _FakeNotebookLMClient
        with patch.dict(
            os.environ,
            {
                "NOTEBOOKLM_AUTH_JSON": '{"cookies":[]}',
                "NOTEBOOKLM_NOTEBOOKS_JSON": '{"HS":"hs-id"}',
            },
            clear=False,
        ), patch.dict(sys.modules, {"notebooklm": fake_module}):
            text = answer_notebook_question("/hs mã HS của mặt hàng này")

        self.assertIn("Tra mã HS", text)
        self.assertIn("Câu trả lời có căn cứ", text)
        self.assertIn("Thông tư thử nghiệm", text)
        self.assertIn("Đoạn nguồn liên quan", text)

    def test_missing_auth_fails_closed(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NOTEBOOKLM_AUTH_JSON", None)
            os.environ.pop("NOTEBOOKLM_HOME", None)
            os.environ["NOTEBOOKLM_NOTEBOOKS_JSON"] = '{"HS":"hs-id"}'
            with self.assertRaises(NotebookLMConfigError):
                answer_notebook_question("/hs mã HS của mặt hàng này")


if __name__ == "__main__":
    unittest.main()
