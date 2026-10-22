"""Strict import-clearance truth shared by legacy and Journey readers.

Only boolean True and the exact legacy string "true" prove clearance.
Truthy strings such as "false" and "1" are not evidence.
"""
from __future__ import annotations

from typing import Any


def customs_clearance_confirmed(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value == "true")
