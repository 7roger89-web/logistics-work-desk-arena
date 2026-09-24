"""Focused tests for the Logistics Telegram -> VNLAW adapter."""

from __future__ import annotations

import os
import unittest
from datetime import date
from unittest.mock import patch

import requests

from core.vnlaw_telegram import (
    MAX_TELEGRAM_MESSAGE,
    VNLAWConfigError,
    VNLAWServiceError,
    format_vnlaw_result,
    parse_allowed_user_ids,
    parse_question,
    query_vnlaw,
)


class _FakeResponse:
    def __init__(self, payload, *, error: Exception | None = None):
        self._payload = payload
        self._error = error

    def raise_for_status(self):
        if self._error:
            raise self._error

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _FakeResponse(self.payload)


class AccessAndQuestionTests(unittest.TestCase):
    def test_allowlist_parser_accepts_only_numeric_ids(self):
        self.assertEqual(
            parse_allowed_user_ids("123, 456;abc 789"),
            frozenset({"123", "456", "789"}),
        )
        self.assertEqual(parse_allowed_user_ids(""), frozenset())

    def test_plain_text_uses_current_date_but_explicit_law_date_wins(self):
        today = date(2026, 9, 24)
        self.assertEqual(
            parse_question("máy móc cũ nhập khẩu", today=today),
            ("máy móc cũ nhập khẩu", "2026-09-24"),
        )
        self.assertEqual(
            parse_question("/law 2025-01-01 máy móc cũ nhập khẩu", today=today),
            ("máy móc cũ nhập khẩu", "2025-01-01"),
        )


class ClientBoundaryTests(unittest.TestCase):
    def test_remote_service_requires_https_and_token(self):
        with patch.dict(
            os.environ,
            {"VNLAW_API_URL": "https://vnlaw.example.internal"},
            clear=False,
        ):
            os.environ.pop("VNLAW_API_TOKEN", None)
            with self.assertRaises(VNLAWConfigError):
                query_vnlaw("x", "2026-09-24", session=_FakeSession({}))

        with patch.dict(
            os.environ,
            {
                "VNLAW_API_URL": "http://vnlaw.example.internal",
                "VNLAW_API_TOKEN": "secret",
            },
            clear=False,
        ):
            with self.assertRaises(VNLAWConfigError):
                query_vnlaw("x", "2026-09-24", session=_FakeSession({}))

    def test_verified_query_contract_and_bearer_token(self):
        payload = {
            "query": "x",
            "as_of_date": "2026-09-24",
            "legal_hits": [],
            "technical_hits": [],
            "guidance_hits": [],
        }
        fake = _FakeSession(payload)
        with patch.dict(
            os.environ,
            {
                "VNLAW_API_URL": "https://vnlaw.example.internal/",
                "VNLAW_API_TOKEN": "secret",
            },
            clear=False,
        ):
            result = query_vnlaw("x", "2026-09-24", top_k=3, session=fake)

        self.assertIs(result, payload)
        self.assertEqual(len(fake.calls), 1)
        url, kwargs = fake.calls[0]
        self.assertEqual(url, "https://vnlaw.example.internal/verified-query")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(kwargs["json"]["scope"], "verified")
        self.assertEqual(kwargs["json"]["top_k"], 3)

    def test_service_error_fails_closed(self):
        class BrokenSession:
            @staticmethod
            def post(*_args, **_kwargs):
                raise requests.RequestException("down")

        with patch.dict(
            os.environ,
            {
                "VNLAW_API_URL": "https://vnlaw.example.internal",
                "VNLAW_API_TOKEN": "secret",
            },
            clear=False,
        ):
            with self.assertRaises(VNLAWServiceError):
                query_vnlaw("x", "2026-09-24", session=BrokenSession())


class RenderingTests(unittest.TestCase):
    def test_empty_verified_groups_refuse_to_invent_answer(self):
        text = format_vnlaw_result(
            {
                "query": "hàng lạ",
                "as_of_date": "2026-09-24",
                "legal_hits": [],
                "technical_hits": [],
                "guidance_hits": [],
                "discovery_candidates": [
                    {"text": "NỘI DUNG KHÁM PHÁ KHÔNG ĐƯỢC PHÉP HIỆN"}
                ],
            }
        )
        self.assertIn("chưa có đủ bằng chứng đã xác minh", text)
        self.assertIn("không dùng dữ liệu khám phá", text)
        self.assertNotIn("NỘI DUNG KHÁM PHÁ", text)

    def test_verified_legal_hit_keeps_source_and_temporal_state(self):
        text = format_vnlaw_result(
            {
                "query": "đại lý hải quan",
                "as_of_date": "2026-09-24",
                "legal_hits": [
                    {
                        "authority_tier": "VERIFIED_LEGAL_AUTHORITY",
                        "chunk": {
                            "document_number": "12/2015/TT-BTC",
                            "breadcrumb": "12/2015/TT-BTC > Điều 7",
                            "force": "in_force",
                            "valid_from": "2019-07-01",
                            "valid_to": None,
                            "text": "Nội dung điều khoản đã xác minh.",
                            "source_locator": "Điều 1 khoản 5",
                            "source_url": "https://chinhphu.vn/example",
                        },
                    }
                ],
                "technical_hits": [],
                "guidance_hits": [],
            }
        )
        self.assertIn("12/2015/TT-BTC > Điều 7", text)
        self.assertIn("đang có hiệu lực", text)
        self.assertIn("https://chinhphu.vn/example", text)

    def test_telegram_message_stays_bounded(self):
        huge = "x" * 5000
        text = format_vnlaw_result(
            {
                "query": huge,
                "as_of_date": "2026-09-24",
                "legal_hits": [
                    {
                        "chunk": {
                            "breadcrumb": "Điều 1",
                            "force": "in_force",
                            "valid_from": "2026-01-01",
                            "valid_to": None,
                            "text": huge,
                            "source_locator": huge,
                            "source_url": "https://example.com/" + huge,
                        }
                    }
                    for _ in range(10)
                ],
                "technical_hits": [],
                "guidance_hits": [],
            }
        )
        self.assertLessEqual(len(text), MAX_TELEGRAM_MESSAGE)


if __name__ == "__main__":
    unittest.main()
