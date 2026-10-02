"""Issue #162 — Work Module Library V1.

A **work module** is a reusable, versioned operational procedure ("quy trình
phát sinh") that ONE shipment can carry *in addition to* its base journey:

    base journey (physical / operational position, built by core.shipment_journey)
        ＋  zero or more attached module instances (each bound to an exact version)

Deliberate boundaries of this module:

* It is a small explicit **template + instance** pair — NOT a workflow engine,
  rules DSL, scheduler, graph database or second task/document/finance store.
* A shipment instance binds an exact ``template_id`` + ``template_version``.
  Publishing V2 never changes the meaning of an instance already bound to V1,
  because execution always resolves the **bound** version.
* Factual completion is a persisted business fact (who / when). Visual overlays
  (CURRENT / PROBLEM / attention) are display-only; they never create, erase or
  substitute for completion.
* Gates are written for people — ``Chặn DELIVERY — còn thiếu Result received`` —
  while the machine keeps the explicit node/dependency graph underneath.

Everything in this file is pure: no database, no Streamlit, no writes. The
single seam that persists anything lives in ``core.database`` and is called by
the existing component dispatcher in ``views.logi_view_model``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

# ----------------------------------------------------------------- vocabulary

TEMPLATE_STATUSES = ("DRAFT", "ACTIVE", "RETIRED")
#: The ONLY dependency vocabulary V1 understands. No rules DSL.
DEPENDENCY_TYPES = ("INFORMATIONAL", "PARALLEL_REQUIRED", "BLOCKING")
#: V1 provenance is deliberately bounded. Customer Playbook / regulatory rule /
#: AI recommendation provenance is a later phase and must not be invented here.
PROVENANCE_TYPES = ("MANUAL_ADDITION", "COMPANY_STANDARD")
#: Guidance a template may carry (all optional, all plain text).
GUIDANCE_FIELDS = ("why", "what_to_do", "who", "when", "needs", "done_when", "impact")

#: Readiness only ever consults these. INFORMATIONAL is context, never a gate.
REQUIRED_DEPENDENCY_TYPES = ("PARALLEL_REQUIRED", "BLOCKING")

DEMO_TEMPLATE_ID = "IMPORT_SPECIAL_HANDLING_DEMO_V1"
DEMO_TEMPLATE_NAME = "IMPORT SPECIAL HANDLING"
DEMO_TEMPLATE_DESCRIPTION = (
    "Quy trình xử lý hồ sơ đặc thù cho hàng nhập: chuẩn bị hồ sơ chuyên biệt, "
    "gửi/xử lý và ghi nhận kết quả trước khi giao hàng. Mẫu kiểm chứng kiến trúc, "
    "KHÔNG phải yêu cầu pháp lý cho bất kỳ mặt hàng nào."
)

_MAX_TEXT = 120
_MAX_LONG_TEXT = 600
_MAX_NODES = 30


def _text(value: Any, limit: int = _MAX_TEXT) -> str:
    """Bounded single-line text; never invents a value."""
    if value is None:
        return ""
    raw = " ".join(str(value).split())
    return raw[:limit].strip()


def _long_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())[:_MAX_LONG_TEXT].strip()


def _iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ------------------------------------------------------------------ templates

def template_key(template_id: str, version: int) -> str:
    """The ONE stable identity of an immutable template version."""
    return f"{template_id}:V{int(version)}"


def _normalize_guidance(raw: Any, *, where: str) -> dict[str, str]:
    if raw in (None, ""):
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError(f"Guidance của {where} phải là một đối tượng.")
    unknown = set(raw) - set(GUIDANCE_FIELDS)
    if unknown:
        raise ValueError(
            f"Guidance của {where} chỉ nhận {', '.join(GUIDANCE_FIELDS)}."
        )
    return {key: _long_text(raw.get(key)) for key in GUIDANCE_FIELDS if _long_text(raw.get(key))}


def _normalize_dependencies(raw: Any, *, node_id: str, known: set[str]) -> list[dict[str, str]]:
    if raw in (None, ""):
        return []
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
        raise ValueError(f"Phụ thuộc của bước {node_id} phải là danh sách.")
    out: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            dependency = {"type": "BLOCKING", "nodeId": item}
        elif isinstance(item, Mapping):
            dependency = {
                "type": _text(item.get("type") or item.get("dependency_type")).upper(),
                "nodeId": _text(item.get("nodeId") or item.get("node_id")),
            }
        else:
            raise ValueError(f"Phụ thuộc của bước {node_id} không hợp lệ.")
        if dependency["type"] not in DEPENDENCY_TYPES:
            raise ValueError(
                f"Loại phụ thuộc phải là {', '.join(DEPENDENCY_TYPES)} (bước {node_id})."
            )
        if dependency["nodeId"] not in known:
            raise ValueError(f"Bước {node_id} phụ thuộc bước không tồn tại: {dependency['nodeId']}.")
        if dependency["nodeId"] == node_id:
            raise ValueError(f"Bước {node_id} không thể phụ thuộc chính nó.")
        out.append(dependency)
    seen = [d["nodeId"] for d in out]
    if len(seen) != len(set(seen)):
        raise ValueError(f"Bước {node_id} khai báo phụ thuộc trùng.")
    return out


def normalize_template(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize ONE template version.

    The result is the immutable shape that is persisted and later bound by
    shipment instances. Anything outside the bounded vocabulary is refused
    instead of silently stored.
    """
    if not isinstance(document, Mapping):
        raise ValueError("Mẫu quy trình phải là một đối tượng.")
    raw = document.get("template") if isinstance(document.get("template"), Mapping) else document

    template_id = _text(raw.get("template_id") or raw.get("templateId")).upper()
    if not template_id:
        raise ValueError("Thiếu mã quy trình.")
    if not all(ch.isalnum() or ch in "_-." for ch in template_id):
        raise ValueError("Mã quy trình chỉ nhận chữ, số, gạch dưới, gạch ngang và dấu chấm.")
    name = _text(raw.get("name"))
    if not name:
        raise ValueError("Thiếu tên quy trình.")

    try:
        version = int(raw.get("version") or 1)
    except (TypeError, ValueError) as exc:
        raise ValueError("Phiên bản phải là số nguyên.") from exc
    if version < 1:
        raise ValueError("Phiên bản phải từ 1 trở lên.")

    status = _text(raw.get("status") or "DRAFT").upper()
    if status not in TEMPLATE_STATUSES:
        raise ValueError(f"Trạng thái mẫu phải là {', '.join(TEMPLATE_STATUSES)}.")

    from core.shipment_journey import JOURNEY_STAGE_IDS

    anchor_stage = _text(raw.get("anchor_stage") or raw.get("anchorStage"))
    if anchor_stage not in JOURNEY_STAGE_IDS:
        raise ValueError(f"Công đoạn neo không thuộc hành trình chuẩn: {anchor_stage or '(trống)'}.")
    gate_stage = _text(raw.get("gate_stage") or raw.get("gateStage"))
    if gate_stage and gate_stage not in JOURNEY_STAGE_IDS:
        raise ValueError(f"Cổng chặn không thuộc hành trình chuẩn: {gate_stage}.")

    anchor_dependency = _text(
        (raw.get("anchor_dependency_type") if isinstance(raw, Mapping) else "") or "INFORMATIONAL"
    ).upper()
    if anchor_dependency not in DEPENDENCY_TYPES:
        raise ValueError(f"Loại phụ thuộc neo phải là {', '.join(DEPENDENCY_TYPES)}.")

    raw_nodes = raw.get("nodes")
    if not isinstance(raw_nodes, Iterable) or isinstance(raw_nodes, (str, bytes)):
        raise ValueError("Quy trình phải có danh sách bước.")
    node_list = [n for n in raw_nodes if isinstance(n, Mapping)]
    if not node_list or len(node_list) != len(list(raw_nodes)):
        raise ValueError("Mỗi bước phải là một đối tượng.")
    if len(node_list) > _MAX_NODES:
        raise ValueError(f"V1 giới hạn {_MAX_NODES} bước cho mỗi quy trình.")

    ids: list[str] = []
    for item in node_list:
        node_id = _text(item.get("id") or item.get("nodeId"))
        if not node_id:
            raise ValueError("Mỗi bước phải có mã bước.")
        if not all(ch.isalnum() or ch in "_-" for ch in node_id):
            raise ValueError(f"Mã bước chỉ nhận chữ, số, gạch dưới, gạch ngang: {node_id}.")
        if node_id in ids:
            raise ValueError(f"Mã bước bị trùng: {node_id}.")
        ids.append(node_id)
    known = set(ids)

    nodes: list[dict[str, Any]] = []
    for item in node_list:
        node_id = _text(item.get("id") or item.get("nodeId"))
        label = _text(item.get("label")) or node_id
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "dependencies": _normalize_dependencies(
                    item.get("dependencies"), node_id=node_id, known=known
                ),
                "guidance": _normalize_guidance(item.get("guidance"), where=f"bước {node_id}"),
                "document_categories": [
                    _text(c) for c in (item.get("document_categories") or []) if _text(c)
                ][:6],
            }
        )

    join = raw.get("join")
    join_out: dict[str, str] = {}
    if isinstance(join, Mapping):
        from_node = _text(join.get("from") or join.get("nodeId"))
        join_type = _text(join.get("type") or "BLOCKING").upper()
        if from_node not in known:
            raise ValueError(f"Điểm nối phải là một bước của quy trình: {from_node or '(trống)'}.")
        if join_type not in DEPENDENCY_TYPES:
            raise ValueError(f"Loại nối phải là {', '.join(DEPENDENCY_TYPES)}.")
        join_out = {"from": from_node, "type": join_type}
        if gate_stage:
            join_out["to"] = gate_stage
    elif gate_stage:
        # A declared gate needs an explicit join node: never guess which step
        # releases the gate.
        raise ValueError("Khai báo cổng chặn phải kèm điểm nối (join).")

    categories = [
        _text(c) for c in (raw.get("document_categories") or []) if _text(c)
    ][:6]

    return {
        "template_id": template_id,
        "name": name,
        "version": version,
        "status": status,
        "description": _long_text(raw.get("description")),
        "anchor_stage": anchor_stage,
        "anchor_dependency_type": anchor_dependency,
        "gate_stage": gate_stage,
        "join": join_out,
        "nodes": nodes,
        "document_categories": categories,
        # The ONE stable id of this immutable version.
        "id": template_key(template_id, version),
    }


# ------------------------------------------------------------------ instances

def normalize_instance(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize ONE shipment-bound module instance."""
    if not isinstance(document, Mapping):
        raise ValueError("Quy trình gắn vào lô phải là một đối tượng.")
    instance_id = _text(document.get("instance_id") or document.get("instanceId")).upper()
    if not instance_id:
        raise ValueError("Thiếu mã lần gắn quy trình.")
    template_id = _text(document.get("template_id") or document.get("templateId")).upper()
    if not template_id:
        raise ValueError("Thiếu mã quy trình được gắn.")
    try:
        version = int(document.get("template_version") or document.get("templateVersion") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Phiên bản quy trình được gắn phải là số nguyên.") from exc
    if version < 1:
        raise ValueError("Phiên bản quy trình được gắn phải từ 1 trở lên.")
    provenance = _text(document.get("provenance") or "MANUAL_ADDITION").upper()
    if provenance not in PROVENANCE_TYPES:
        raise ValueError(f"Nguồn gốc gắn quy trình phải là {', '.join(PROVENANCE_TYPES)}.")

    steps: list[dict[str, str]] = []
    for item in document.get("completed_steps") or []:
        if not isinstance(item, Mapping):
            continue
        node_id = _text(item.get("node_id") or item.get("nodeId"))
        if not node_id:
            continue
        steps.append(
            {
                "node_id": node_id,
                "completed_by": _text(item.get("completed_by")),
                "completed_at": _text(item.get("completed_at"), 40),
                "note": _long_text(item.get("note")),
            }
        )

    return {
        "instance_id": instance_id,
        "template_id": template_id,
        "template_version": version,
        "provenance": provenance,
        "reason": _long_text(document.get("reason")),
        "added_by": _text(document.get("added_by")),
        "added_by_user_id": _text(document.get("added_by_user_id")),
        "added_at": _text(document.get("added_at"), 40),
        "completed_steps": steps,
    }


def build_instance(
    template: Mapping[str, Any],
    *,
    instance_id: str,
    provenance: str = "MANUAL_ADDITION",
    reason: str = "",
    actor: str = "",
    actor_user_id: str = "",
    added_at: str = "",
) -> dict[str, Any]:
    """Create ONE instance bound to the template's exact id + version."""
    return normalize_instance(
        {
            "instance_id": instance_id,
            "template_id": template["template_id"],
            "template_version": template["version"],
            "provenance": provenance,
            "reason": reason,
            "added_by": actor,
            "added_by_user_id": actor_user_id,
            "added_at": added_at or _iso_now(),
            "completed_steps": [],
        }
    )


def instances_of(shipment: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Read the bounded instance block from an existing shipment document.

    The block is additive: a shipment without modules yields ``[]`` and behaves
    exactly as it did before this feature existed.
    """
    raw = shipment.get("work_modules")
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        try:
            out.append(normalize_instance(item))
        except ValueError:
            # An unreadable instance is kept visible as UNKNOWN rather than
            # silently dropped — never silently done/green.
            out.append(
                {
                    "instance_id": _text(item.get("instance_id") or item.get("instanceId")).upper(),
                    "template_id": _text(item.get("template_id") or item.get("templateId")).upper(),
                    "template_version": int(item.get("template_version") or 0),
                    "provenance": _text(item.get("provenance")).upper() or "MANUAL_ADDITION",
                    "reason": _long_text(item.get("reason")),
                    "added_by": _text(item.get("added_by")),
                    "added_by_user_id": "",
                    "added_at": _text(item.get("added_at"), 40),
                    "completed_steps": [],
                    "invalid": True,
                }
            )
    return out


# ------------------------------------------------------------------ templates

def index_templates(templates: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index every stored template version by its stable (id, version) key."""
    out: dict[str, dict[str, Any]] = {}
    for item in templates or []:
        if not isinstance(item, Mapping):
            continue
        try:
            normalized = normalize_template(item)
        except ValueError:
            continue
        out[normalized["id"]] = normalized
    return out


def resolve_template(
    templates: Mapping[str, Mapping[str, Any]], template_id: str, version: int
) -> dict[str, Any] | None:
    """Resolve the EXACT bound version. Never falls back to another version.

    Falling back would silently change the historical meaning of an attached
    instance, which this feature explicitly forbids.
    """
    return templates.get(template_key(template_id, version))


def attachable_templates(templates: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The newest ACTIVE version of each template — the only attachable set."""
    best: dict[str, dict[str, Any]] = {}
    for item in templates or []:
        if not isinstance(item, Mapping):
            continue
        try:
            normalized = normalize_template(item)
        except ValueError:
            continue
        if normalized["status"] != "ACTIVE":
            continue
        current = best.get(normalized["template_id"])
        if current is None or normalized["version"] > current["version"]:
            best[normalized["template_id"]] = normalized
    return sorted(
        (
            {
                "templateId": t["template_id"],
                "version": t["version"],
                "name": t["name"],
                "description": t["description"],
                "anchorStage": t["anchor_stage"],
                "gateStage": t["gate_stage"],
                "stepCount": len(t["nodes"]),
            }
            for t in best.values()
        ),
        key=lambda row: (row["name"], row["templateId"]),
    )


# ------------------------------------------------------------------ execution

def _dependency_closure(template: Mapping[str, Any], start: str) -> set[str]:
    """Every node the gate join decisively depends on (BLOCKING / PARALLEL_REQUIRED).

    INFORMATIONAL edges are context: they are shown, but they can never hold or
    release a gate.
    """
    required: dict[str, list[str]] = {node["id"]: [] for node in template.get("nodes") or []}
    for node in template.get("nodes") or []:
        for dependency in node.get("dependencies") or []:
            if dependency.get("type") in REQUIRED_DEPENDENCY_TYPES:
                required[node["id"]].append(dependency["nodeId"])
    seen: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        for parent in required.get(current, []):
            if parent not in seen:
                seen.add(parent)
                stack.append(parent)
    return seen


def module_execution(
    template: Mapping[str, Any],
    instance: Mapping[str, Any],
    *,
    gate_label: str = "",
) -> dict[str, Any]:
    """Compute the execution view of ONE attached instance — pure, factual.

    ``completed`` comes ONLY from persisted completion facts. Missing evidence
    stays UNKNOWN; it never becomes done, green or unblocked.
    """
    nodes = list(template.get("nodes") or [])
    done = {
        step["node_id"]: step
        for step in instance.get("completed_steps") or []
        if step.get("node_id")
    }
    by_id = {node["id"]: node for node in nodes}

    def missing_required(node_id: str) -> list[str]:
        node = by_id[node_id]
        return [
            d["nodeId"]
            for d in node.get("dependencies") or []
            if d.get("type") in REQUIRED_DEPENDENCY_TYPES and d["nodeId"] not in done
        ]

    steps = []
    for node in nodes:
        fact = done.get(node["id"])
        blocked_by = missing_required(node["id"]) if not fact else []
        steps.append(
            {
                "id": node["id"],
                "label": node["label"],
                "completed": bool(fact),
                "completedAt": (fact or {}).get("completed_at", ""),
                "completedBy": (fact or {}).get("completed_by", ""),
                "note": (fact or {}).get("note", ""),
                "blockedBy": blocked_by,
                "dependencies": [
                    d["nodeId"]
                    for d in node.get("dependencies") or []
                    if d.get("type") in REQUIRED_DEPENDENCY_TYPES
                ],
                "informational": [
                    d["nodeId"]
                    for d in node.get("dependencies") or []
                    if d.get("type") == "INFORMATIONAL"
                ],
                "guidance": dict(node.get("guidance") or {}),
                "documentCategories": list(node.get("document_categories") or []),
                "needsEvidence": not fact,
            }
        )

    total = len(steps)
    completed_count = sum(1 for step in steps if step["completed"])
    is_done = total > 0 and completed_count == total

    join = template.get("join") or {}
    gate_stage = template.get("gate_stage") or ""
    gate_type = _text(join.get("type")).upper()
    gate_required = bool(gate_stage) and gate_type in REQUIRED_DEPENDENCY_TYPES

    closure = _dependency_closure(template, join["from"]) if join.get("from") in by_id else set()
    if gate_required and join.get("from") in by_id:
        closure.add(join["from"])
    blocking_missing = [
        step for step in steps if step["id"] in closure and not step["completed"]
    ]

    if not total:
        status = "UNKNOWN"
    elif is_done:
        status = "DONE"
    elif gate_required and blocking_missing:
        status = "BLOCKING"
    else:
        status = "WAITING"

    # Next relevant step: the first still-missing step the gate depends on,
    # else the first incomplete step in template order.
    next_step = blocking_missing[0] if blocking_missing else next(
        (step for step in steps if not step["completed"]), {}
    )

    gate_text = ""
    if status == "BLOCKING":
        label = gate_label or gate_stage.upper()
        missing = ", ".join(step["label"] for step in blocking_missing)
        gate_text = f"Chặn {label} — còn thiếu {missing}"

    deadline = next((step["guidance"].get("when", "") for step in steps
                     if not step["completed"] and step["guidance"].get("when")), "")
    impact = next((step["guidance"].get("impact", "") for step in blocking_missing
                   if step["guidance"].get("impact")), "")

    return {
        "instanceId": instance.get("instance_id", ""),
        "templateId": template.get("template_id", ""),
        "templateVersion": template.get("version", 0),
        "name": template.get("name", ""),
        "description": template.get("description", ""),
        "status": status,
        "summary": f"{completed_count}/{total} bước" if total else "UNKNOWN",
        "completedCount": completed_count,
        "totalCount": total,
        "nextStep": next_step.get("label", ""),
        "nextStepId": next_step.get("id", ""),
        "deadline": deadline,
        "blocker": impact,
        "gate": (
            {"stage": gate_stage, "label": gate_label or gate_stage.upper(), "type": gate_type}
            if gate_stage and gate_type
            else {}
        ),
        "gateText": gate_text,
        "provenance": instance.get("provenance", ""),
        "addedBy": instance.get("added_by", ""),
        "addedAt": instance.get("added_at", ""),
        "reason": instance.get("reason", ""),
        "steps": steps,
        "documentCategories": list(template.get("document_categories") or []),
    }


def unknown_execution(instance: Mapping[str, Any]) -> dict[str, Any]:
    """An instance whose bound template version cannot be resolved.

    It is surfaced as UNKNOWN with attention — never dropped, never done.
    """
    return {
        "instanceId": instance.get("instance_id", ""),
        "templateId": instance.get("template_id", ""),
        "templateVersion": instance.get("template_version", 0),
        "name": instance.get("template_id", ""),
        "description": "",
        "status": "UNKNOWN",
        "summary": "UNKNOWN",
        "completedCount": 0,
        "totalCount": 0,
        "nextStep": "",
        "nextStepId": "",
        "deadline": "",
        "blocker": "Không đọc được phiên bản quy trình đã gắn.",
        "gate": {},
        "gateText": "",
        "provenance": instance.get("provenance", ""),
        "addedBy": instance.get("added_by", ""),
        "addedAt": instance.get("added_at", ""),
        "reason": instance.get("reason", ""),
        "steps": [],
        "documentCategories": [],
        "unresolved": True,
    }


# ----------------------------------------------------------------- composition

def module_node_id(instance_id: str, node_id: str) -> str:
    """Journey-node id for one module step (namespaced, never colliding with base)."""
    return f"wm-{instance_id}-{node_id}"


def compose_journey_modules(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    *,
    templates: Iterable[Mapping[str, Any]],
    instances: Iterable[Mapping[str, Any]],
    attachments: Iterable[Mapping[str, Any]] = (),
    target_tab: str = "nhap",
) -> list[dict[str, Any]]:
    """Append attached modules to an ALREADY-BUILT base journey.

    Additive by construction: base node ids, labels, evidence, completion facts
    and primary action are never rewritten. What this adds is

    * one compact rollup per instance (the default human view), and
    * the machine graph behind it (module step nodes + join edges), and
    * the human gate sentence on the base stage the module blocks.

    Returns the list of rollups. Called with no instances it returns ``[]`` and
    touches nothing.
    """
    indexed = index_templates(templates)
    rollups: list[dict[str, Any]] = []

    for instance in instances:
        template = resolve_template(indexed, instance.get("template_id", ""),
                                    int(instance.get("template_version") or 0))
        if template is None:
            rollups.append(unknown_execution(instance))
            continue

        anchor = by_id.get(template["anchor_stage"])
        gate_node = by_id.get(template.get("gate_stage") or "")
        execution = module_execution(
            template, instance, gate_label=(gate_node or {}).get("label", "")
        )
        execution["anchorStage"] = template["anchor_stage"]
        execution["anchorLabel"] = (anchor or {}).get("label", "")

        for step in execution["steps"]:
            journey_id = module_node_id(instance["instance_id"], step["id"])
            dependencies = [module_node_id(instance["instance_id"], dep) for dep in step["dependencies"]]
            informational = [
                module_node_id(instance["instance_id"], dep) for dep in step["informational"]
            ]
            if anchor is not None and step["id"] == (template["nodes"][0]["id"] if template["nodes"] else ""):
                if template["anchor_dependency_type"] in REQUIRED_DEPENDENCY_TYPES:
                    dependencies.append(anchor["id"])
                else:
                    informational.append(anchor["id"])
            node = {
                "id": journey_id,
                "label": step["label"],
                "family": template["template_id"],
                "targetTab": (anchor or {}).get("targetTab", target_tab),
                "completed": step["completed"],
                "state": "COMPLETED" if step["completed"] else "UPCOMING",
                "factState": "KNOWN" if step["completed"] else "UNKNOWN",
                "evidence": (
                    f"{step['completedBy']} · {step['completedAt']}" if step["completed"] else ""
                ),
                "deadline": step["guidance"].get("when", ""),
                "owned": True,
                "current": False,
                "blockers": [] if step["completed"] else [],
                "dependencies": dependencies,
                "informationalDependencies": informational,
                "documentCategories": step["documentCategories"],
                # Documents stay canonical: module steps only FILTER the
                # shipment's existing attachments by category, they never own
                # a second file store.
                "documentIds": [
                    a["id"]
                    for a in attachments
                    if a.get("category") in step["documentCategories"]
                ],
                # Module context — everything the existing Quick Panel and
                # Stage Workspace need, without a second workspace.
                "moduleId": instance["instance_id"],
                "moduleTemplateId": template["template_id"],
                "moduleTemplateVersion": template["version"],
                "moduleName": template["name"],
                "moduleNodeId": step["id"],
                "moduleStatus": execution["status"],
                "moduleGateText": execution["gateText"],
                "moduleProvenance": instance.get("provenance", ""),
                "guidance": step["guidance"],
                "moduleSteps": [
                    {"id": s["id"], "label": s["label"], "completed": s["completed"]}
                    for s in execution["steps"]
                ],
            }
            nodes.append(node)
            by_id[journey_id] = node
            # Machine truth: the explicit edge between module steps.
            for parent in dependencies:
                if parent in by_id:
                    edges.append({"from": parent, "to": journey_id})

        # Gate truth: the declared join edge plus the human sentence on the base
        # stage. The base node keeps its own factual completion; a gate only
        # ADDS attention.
        join_stage = template.get("gate_stage") or ""
        if join_stage and gate_node is not None:
            join_id = module_node_id(instance["instance_id"], template["join"]["from"])
            join_type = template["join"]["type"]
            if join_type in REQUIRED_DEPENDENCY_TYPES:
                edges.append({"from": join_id, "to": join_stage})
                if join_id not in gate_node["dependencies"]:
                    gate_node["dependencies"].append(join_id)
            if execution["gateText"]:
                if execution["gateText"] not in gate_node["blockers"]:
                    gate_node["blockers"].append(execution["gateText"])

        rollups.append(execution)

    return rollups


def demo_template() -> dict[str, Any]:
    """The ONE neutral verification module of V1.

    Architecture fixture only — it makes NO legal claim about any commodity.
    """
    return normalize_template(
        {
            "template_id": DEMO_TEMPLATE_ID,
            "name": DEMO_TEMPLATE_NAME,
            "version": 1,
            "status": "ACTIVE",
            "description": DEMO_TEMPLATE_DESCRIPTION,
            "anchor_stage": "customs-import",
            "anchor_dependency_type": "INFORMATIONAL",
            "gate_stage": "delivery",
            "join": {"from": "result-received", "type": "BLOCKING"},
            "document_categories": ["customs"],
            "nodes": [
                {
                    "id": "prepare-file",
                    "label": "Prepare specialist file",
                    "guidance": {
                        "why": "Hồ sơ đặc thù phải đủ trước khi gửi cơ quan/đơn vị xử lý.",
                        "what_to_do": "Tập hợp hồ sơ chuyên biệt cho lô hàng này.",
                        "needs": "Chứng từ lô hàng hiện có.",
                        "done_when": "Hồ sơ đã đủ và được ghi nhận là đã chuẩn bị.",
                    },
                },
                {
                    "id": "submit-process",
                    "label": "Submit / process",
                    "dependencies": [{"type": "BLOCKING", "nodeId": "prepare-file"}],
                    "guidance": {
                        "why": "Chỉ gửi được khi hồ sơ đã chuẩn bị xong.",
                        "what_to_do": "Gửi và theo dõi xử lý.",
                        "done_when": "Đã gửi và được ghi nhận.",
                    },
                },
                {
                    "id": "result-received",
                    "label": "Result received",
                    "dependencies": [{"type": "BLOCKING", "nodeId": "submit-process"}],
                    "guidance": {
                        "why": "Kết quả là bằng chứng cuối cùng để mở cổng giao hàng.",
                        "what_to_do": "Ghi nhận kết quả nhận được.",
                        "done_when": "Đã có kết quả và được ghi nhận.",
                        "impact": "Chặn giao hàng cho tới khi có kết quả.",
                    },
                },
            ],
        }
    )
