"""Logi-good donor-structured view layer for LOGISTICS PRO.

This module provides a Streamlit-only UI that mirrors the Logi-good donor
structure (sidebar groups, top header, Home/Tasks/Shipments/ShipmentDetail/
Contracts/Finance/Customers/Sales/CEO/Tools) while remaining a VIEW-LAYER
replacement wired to the existing real core services and business truth.

Architecture
------------
LOGISTICS-PRO views (this package)
    -> real core readers/builders  (core.shipment_dashboard, core.shipment_workspace,
                                    core.review_queue, core.financial_ledger, ...)
    -> current DB business truth

Nothing here renders legacy page functions as the final surface for screens
that have a donor equivalent; those screens are rebuilt per donor structure.
"""
