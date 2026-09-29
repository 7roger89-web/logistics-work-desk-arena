"""Regression guard for cold-start FX latency.

The three bank sources are independent.  A cold view-model render must not pay
their network waits serially; fetch_live_fx("all") joins a short-lived worker
pool before returning and keeps the existing fail-closed result semantics.
"""
from __future__ import annotations

import threading
import unittest
from unittest.mock import patch

from core.fx_sources import fetch_live_fx


class _Headers:
    @staticmethod
    def get_content_charset():
        return "utf-8"


class _Response:
    headers = _Headers()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    @staticmethod
    def read():
        return b"<html><body>no usable rate fixture</body></html>"


class FxFetchConcurrencyTest(unittest.TestCase):
    def test_all_sources_overlap_instead_of_waiting_serially(self):
        lock = threading.Lock()
        barrier = threading.Barrier(3, timeout=0.75)
        active = 0
        max_active = 0

        def fake_urlopen(_request, timeout):
            nonlocal active, max_active
            self.assertEqual(timeout, 4)
            with lock:
                active += 1
                max_active = max(max_active, active)
            try:
                try:
                    barrier.wait()
                except threading.BrokenBarrierError:
                    # Sequential behavior reaches here one source at a time;
                    # the max_active assertion below then fails deterministically.
                    pass
                return _Response()
            finally:
                with lock:
                    active -= 1

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = fetch_live_fx("all", timeout=4)

        self.assertEqual(list(result), ["boc", "agribank", "bidv"])
        self.assertGreaterEqual(max_active, 2)
        self.assertEqual(result["boc"]["status"], "RATE_UNAVAILABLE")
        self.assertEqual(result["agribank"]["status"], "RATE_UNAVAILABLE")
        self.assertEqual(result["bidv"]["status"], "RATE_UNAVAILABLE")

    def test_concurrent_fetch_preserves_source_semantics(self):
        boc_html = b"""<table>
        <tr><th>Currency Name</th><th>Buying Rate</th><th>Cash Buying Rate</th><th>Selling Rate</th><th>Cash Selling Rate</th><th>Middle Rate</th><th>Pub Time</th></tr>
        <tr><td>USD</td><td>669.55</td><td>669.55</td><td>672.45</td><td>672.45</td><td>674.68</td><td>2026/09/23 18:40:28</td></tr>
        </table>"""
        agri_html = """<div>Tỷ giá được cập nhật lúc 11:30 ngày 23/09/2026</div>
        <table><tr><th>Ngoại tệ</th><th>Mua tiền mặt</th><th>Mua chuyển khoản</th><th>Giá bán</th></tr>
        <tr><td>USD</td><td>25,770.00</td><td>25,800.00</td><td>26,180.00</td></tr></table>""".encode("utf-8")
        bidv_html = b"<html><body>BIDV static page without a proven API URL</body></html>"

        class Response(_Response):
            def __init__(self, body):
                self.body = body

            def read(self):
                return self.body

        def fake_urlopen(request, timeout):
            self.assertEqual(timeout, 4)
            url = request.full_url
            if "boc.cn" in url:
                return Response(boc_html)
            if "agribank.com.vn" in url:
                return Response(agri_html)
            if "bidv.com.vn" in url:
                return Response(bidv_html)
            self.fail(f"unexpected URL: {url}")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = fetch_live_fx("all", timeout=4)

        self.assertEqual(list(result), ["boc", "agribank", "bidv"])
        self.assertEqual(result["boc"]["status"], "OK")
        self.assertEqual(str(result["boc"]["usd_to_cny"]), "6.6955")
        self.assertEqual(result["agribank"]["status"], "OK")
        self.assertEqual(str(result["agribank"]["usd_sell_vnd"]), "26180.00")
        self.assertEqual(result["bidv"]["status"], "RATE_UNAVAILABLE")
        self.assertEqual(result["bidv"]["bidv_rate_status"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
