"""Entity context ↔ shipment 360 navigation, on the LIVE contract.

The Streamlit entity workspace (``views.entity_context.ui_entity_context``) was
retired by LOGI-GOOD-V6 Phase A together with the rest of the sidebar SPA.  The
capability itself did NOT go away: ``core.entity_context`` still builds the
customer/factory/partner workspace and ``views.partner_context`` projects it
into the shell as the ``/ngu-canh-doi-tac`` page.

These tests therefore assert the two behaviours the mounted tests protected,
against the readers that actually run:

1. opening an entity workspace really lists that entity's shipments (the 360
   entry point), scoped to the entity — never another customer's lot;
2. every related shipment carries the ONE live 360 route
   (``/lo-hang/<id>``), i.e. the workspace's rows are navigable.
"""

from __future__ import annotations

import pytest

from core.entity_context import build_entity_context
from views import logi_route
from views import partner_context


def _shipments() -> dict[str, dict]:
    return {
        "S-001": {
            "id": "S-001",
            "shipment_id": "S-001",
            "customer": "Acme",
            "customer_id": "CUS-1",
            "status": "pending",
            "partner": {"name": "Blue Agent", "role": "Pickup agent"},
            "data": {
                "0.0": {"created_at": "2026-08-01", "mode": "Sea"},
                "2.7": {"delivery_date": "2026-08-30"},
            },
        },
        "S-002": {
            "id": "S-002",
            "shipment_id": "S-002",
            "customer": "Other",
            "customer_id": "CUS-2",
            "status": "pending",
            "data": {"0.0": {"created_at": "2026-08-01"}},
        },
    }


def _customers() -> dict[str, dict]:
    return {
        "CUS-1": {"id": "CUS-1", "name": "Acme", "contact_person": "Lan", "phone": "0900"},
        "CUS-2": {"id": "CUS-2", "name": "Other"},
    }


def test_entity_workspace_opens_shipment_360() -> None:
    context = build_entity_context(
        "customer",
        "CUS-1",
        customers=_customers(),
        shipments=_shipments(),
    )

    assert context["entity_type"] == "customer"
    assert context["identity"]["name"] == "Acme"
    assert context["read_only"] is True, "the entity workspace never writes"
    related = [row["shipment_id"] for row in context["shipments"]]
    # Tenant scope: only THIS customer's lot is listed.
    assert related == ["S-001"]
    assert [row["shipment_id"] for row in context["active_shipments"]] == ["S-001"]

    # …and the row is navigable to the ONE live 360 route.
    assert logi_route.shipment_path(related[0]) == "/lo-hang/S-001"


def test_shipment_360_workspace_has_entity_context_buttons() -> None:
    """The reverse direction: the entity workspace exposes each shipment's 360.

    In the shell the "entity context" control lives on the shipment detail page
    (``/ngu-canh-doi-tac`` is the workspace, ``/lo-hang/<id>`` the 360), so the
    contract that matters is that a selected partner's workspace lists exactly
    that partner's lots **with a live route** for every row.
    """
    view = partner_context.partner_context_view(
        "Blue Agent",
        agents={},
        customers=_customers(),
        shipments=_shipments(),
        payables={"rows": []},
    )

    assert view["readOnly"] is True
    assert view["selectedKey"], "the selected partner must be echoed back"
    rows = view.get("shipments") or []
    assert rows, "a partner with shipments must list them"
    for row in rows:
        identifier = row.get("shipmentId") or row.get("id")
        assert identifier == "S-001", "never another customer's lot"
        # `openHref` is the live 360 link the workspace renders ("Mở 360°");
        # `route` is the partner's origin → destination text, not a link.
        assert row["canOpen"] is True
        assert row["openHref"] == logi_route.shipment_path(identifier)
