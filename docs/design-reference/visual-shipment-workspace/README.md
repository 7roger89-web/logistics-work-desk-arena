# Visual Shipment Workspace — reference handoff

This branch exists only as a durable implementation handoff for Issue #160.

## Accepted prototype references

Full source archives are preserved in the Owner's ChatGPT Library:

- /LOG/Visual Shipment Workspace/claude-visual-shipment-workspace-A.zip
  - SHA256: 5d51462e263f25440bbd799bb4dcc04cbe4bb3440c51bdebe552663075c7e369
  - Primary value: state synchronization / one data change updates all views.
- /LOG/Visual Shipment Workspace/claude-visual-shipment-workspace-B.zip
  - SHA256: cfe20232afcd8c0872825658378d08d428f9f5525a6642fa629a457718673cac
  - Primary value: component composition, Stage Workspace, CostTable, HistoryList.

Issue contract:
https://github.com/7roger89-web/logistics-work-desk-arena/issues/160

## Integration target

Do not create a standalone shipment app.

Primary UI:
- component/src/pages/ShipmentDetail.tsx

Primary projection:
- views/logi_real_data.py::shipment_projection

Workflow authority:
- core/shipment_execution_profile.py
- core/shipment_operations.py
- core/shipment_dashboard.py
- core/shipment_document_workflow.py
- core/shipment_attachments.py
- core/logic.py
- core/auth.py

## Accepted Sea Export journey

BOOKING
→ PICKUP
→ CUSTOMS EXPORT
→ parallel SI / VGM + GATE-IN
→ ETD
→ ON BOARD
→ TRANSIT
→ ARRIVAL
→ CUSTOMS IMPORT (when relevant)
→ DELIVERY (when relevant)

This visual detail is accepted by the Owner. Preserve it where supported by real shipment facts.

## Non-negotiable rule

The Journey Map is a visual index over current shipment truth.

Do not add:
- second shipment store
- second workflow engine
- second finance store
- per-node document store
- client-only authoritative business state

UNKNOWN stays UNKNOWN.
