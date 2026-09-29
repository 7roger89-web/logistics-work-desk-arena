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


if __name__ == "__main__":
    unittest.main()
