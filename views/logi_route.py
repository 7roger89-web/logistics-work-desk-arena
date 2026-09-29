"""LOGI_SHIPMENT_SLASH_ROUTE_REPAIR_01 (Issue #138) — the ONE canonical
shipment-detail URL builder for backend-composed routes.

The React shell serves exactly one dynamic shipment segment (``/lo-hang/:id``),
whose shipped matcher compiles to ``([^\\/]+)``. Several live backend
projections compose shipment links as raw f-strings
(``f"/lo-hang/{sid}?tab=…"``) and hand them to the UI as ``nextRoute`` /
``route`` / ``openHref``. When the identity itself contains ``/`` (legacy
shipment numbers shaped like a document number, the same identity shape the
contract desk already had to repair in Issue #59) the composed link becomes
MULTIPLE path segments, no detail route matches it, and the wildcard renders
NotFound.

:func:`shipment_path` builds ONE encoded segment. Its escaping set is
deliberately the same character class as the browser's ``encodeURIComponent``
and as :func:`component/src/lib/shipmentRoute.ts`, so the backend string and the
frontend helper produce byte-identical routes and neither side double-encodes.

Contract:

* the argument is the RAW shipment identity, never an already-composed URL, and
  never the query string or ``#anchor`` (append those after the call);
* canonical plain identities (``LO-0308``, ``108313713320``) are returned
  unchanged — encoding is a no-op for characters that are already safe;
* a literal ``%2F`` inside an identity survives as ``%252F`` on the wire and
  resolves back to the literal ``%2F`` identity in the browser.

No router, registry, route object or second navigation system is introduced:
this module only owns the prefix constant and one pure function.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

#: Existing React route prefix for one shipment (donor route, unchanged).
SHIPMENT_ROUTE_PREFIX = "/lo-hang/"

#: The characters ``encodeURIComponent`` leaves unescaped on top of Python's
#: own always-safe set (letters, digits, ``_ . - ~``), so both languages agree
#: character-for-character.
_ENCODE_URI_COMPONENT_SAFE = "~!*'()"


def normalize_shipment_id(shipment_id: Any) -> str:
    """The canonical browser identity of a shipment.

    Mirrors the projection primitive the UI already receives
    (``views.logi_real_data.text``): ``str(value).strip()``, and an absent
    identity stays the empty string rather than the literal ``"None"``.
    """
    if shipment_id is None:
        return ""
    return str(shipment_id).strip()


def shipment_path(shipment_id: Any) -> str:
    """One shipment identity → exactly ONE encoded route segment."""
    return SHIPMENT_ROUTE_PREFIX + quote(
        normalize_shipment_id(shipment_id), safe=_ENCODE_URI_COMPONENT_SAFE
    )
