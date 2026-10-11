"""LOGI-193 — bounded Admin write path for uploaded Office templates.

The typed event shell for ``/bieu-mau`` (Issue #193).  It mirrors
``views.user_management`` exactly: RBAC pre-check → validate → canonical
capability → fresh readback.  It invents no template engine and no second
document store; the actual work is done by the two narrow modules this slice
adds:

    core.docgen.uploaded_template        detection / mapping / readiness / render
    core.docgen.uploaded_template_store  app_settings registry + GridFS bytes

Write contract:

    typed event → Admin RBAC (core.auth wildcard) → validate BEFORE storing →
    GridFS bytes + app_settings registry → fresh readback projection

Scope, deliberately bounded:

* **Admin only.**  Every handler re-checks ``can_operate_business("*")``
  server-side; hiding the buttons in the UI is a display choice, never the
  security boundary.
* **Validate before store.**  Kind/size/OOXML-structure/safety scan all run
  before a single byte reaches GridFS, so a refused upload persists nothing.
* **No delete.**  Retire only flips ``status``; published version rows and
  their bytes stay, so already-generated documents keep a resolvable template
  identity.
* **No raw paths, no expressions.**  Mapping entries are validated against the
  canonical field whitelist by the engine, not interpreted here.
"""

from __future__ import annotations

from typing import Any, Mapping

DOCGEN_TEMPLATE_EVENTS = {
    "docgen_template_upload",
    "docgen_template_mapping_save",
    "docgen_template_publish",
    "docgen_template_status_set",
    "docgen_template_preview",
}

MAX_UPLOAD_BASE64_CHARS = 8 * 1024 * 1024


def _text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _result(event: str, template_id: str, ok: bool, error: str = "",
            readback: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    return {"event": event, "id": template_id, "templateId": template_id, "ok": ok,
            "error": error, "readback": readback, **extra}


def _actor() -> str:
    from core.auth import current_actor

    return current_actor()


def _admin_gate() -> bool:
    """The ONE Admin boundary this module reuses — never widened here."""
    from core.auth import can_operate_business

    return can_operate_business("*")


def _decode(payload: Mapping[str, Any]) -> bytes:
    """Bounded base64 decode: refuse an oversized body before allocating it."""
    import base64

    from core.docgen.uploaded_template import MAX_TEMPLATE_BYTES, UploadedTemplateError

    encoded = payload.get("base64")
    if not isinstance(encoded, str) or not encoded:
        raise UploadedTemplateError("Thiếu nội dung tệp biểu mẫu.")
    if len(encoded) > MAX_UPLOAD_BASE64_CHARS:
        raise UploadedTemplateError(
            f"Tệp vượt giới hạn {MAX_TEMPLATE_BYTES // (1024 * 1024)} MB — chưa lưu gì."
        )
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError, base64.binascii.Error):
        raise UploadedTemplateError("Nội dung tệp không phải base64 hợp lệ.") from None


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _handle_template_upload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Upload ONE ordinary DOCX/XLSX, detect positions, store as a new draft."""
    from core.docgen import uploaded_template as engine
    from core.docgen import uploaded_template_store as store

    label = _text(payload.get("label"))
    request_id = _text(payload.get("requestId"))

    def out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("docgen_template_upload", label, ok, error, requestId=request_id, **extra)

    if not _admin_gate():
        return out(False, "RBAC: chỉ Admin mới được tải biểu mẫu lên.", gate="BLOCKED_PERMISSION_DENIED")
    if not label:
        return out(False, "Thiếu tên biểu mẫu.", gate="INVALID_REQUEST")

    try:
        data = _decode(payload)
        info = engine.validate_uploaded_template(_text(payload.get("fileName")) or label, data)
        positions = engine.detect_positions(data, info["kind"])
        row = store.create_draft(
            label=label,
            category=_text(payload.get("category")),
            kind=info["kind"],
            mime=info["mime"],
            data=data,
            sha256=info["sha256"],
            positions=positions,
            uploaded_by=_actor(),
        )
    except engine.UploadedTemplateError as exc:
        return out(False, str(exc), gate="TEMPLATE_REJECTED")
    except store.TemplateStoreError as exc:
        return out(False, str(exc), gate="TEMPLATE_STORE_FAILED")
    except Exception as exc:  # noqa: BLE001 - one bad upload must not break the run
        return out(False, f"{type(exc).__name__}: không tải được biểu mẫu.", gate="TEMPLATE_UPLOAD_FAILED")

    return out(
        True,
        f"Đã tải biểu mẫu {info['kind']} và nhận diện {len(positions)} vị trí để xác nhận.",
        gate="DRAFT_CREATED",
        readback=store.project_template(row, include_detected=True),
        detectedCount=len(positions),
    )


def _handle_template_mapping_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Persist ONE Admin-confirmed mapping on a draft template."""
    from core.docgen import uploaded_template as engine
    from core.docgen import uploaded_template_store as store

    template_id = _text(payload.get("templateId"))
    request_id = _text(payload.get("requestId"))

    def out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("docgen_template_mapping_save", template_id, ok, error,
                       requestId=request_id, **extra)

    if not _admin_gate():
        return out(False, "RBAC: chỉ Admin mới được xác nhận mapping.", gate="BLOCKED_PERMISSION_DENIED")
    if not template_id:
        return out(False, "Thiếu templateId.", gate="INVALID_REQUEST")

    try:
        row = store.get_template(template_id)
        if row is None:
            return out(False, "Không tìm thấy biểu mẫu.", gate="TEMPLATE_NOT_FOUND")
        detected = row.get("detected") if isinstance(row.get("detected"), list) else []
        known = {_text(item.get("id")) for item in detected if isinstance(item, Mapping)}
        mapping = engine.normalize_mapping(payload.get("mapping"), _text(row.get("kind")).upper())
        # A mapping may only point at positions detection actually reported.
        unknown = [entry["position"] for entry in mapping if entry["position"] not in known]
        if unknown:
            return out(
                False,
                "Mapping trỏ tới vị trí không có trong kết quả nhận diện: "
                + ", ".join(unknown[:3]),
                gate="UNKNOWN_POSITION",
            )
        saved = store.save_mapping(template_id=template_id, mapping=mapping, actor=_actor())
    except engine.UploadedTemplateError as exc:
        return out(False, str(exc), gate="MAPPING_REJECTED")
    except store.TemplateStoreError as exc:
        return out(False, str(exc), gate="TEMPLATE_STORE_FAILED")

    return out(
        True,
        f"Đã lưu {len(mapping)} vị trí đã xác nhận.",
        gate="MAPPING_SAVED",
        readback=store.project_template(saved, include_detected=True),
    )


def _handle_template_publish(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Freeze the draft's bytes + mapping into ONE immutable active version."""
    from core.docgen import uploaded_template as engine
    from core.docgen import uploaded_template_store as store

    template_id = _text(payload.get("templateId"))
    request_id = _text(payload.get("requestId"))

    def out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("docgen_template_publish", template_id, ok, error,
                       requestId=request_id, **extra)

    if not _admin_gate():
        return out(False, "RBAC: chỉ Admin mới được phát hành biểu mẫu.", gate="BLOCKED_PERMISSION_DENIED")
    if not template_id:
        return out(False, "Thiếu templateId.", gate="INVALID_REQUEST")

    try:
        published = store.publish(template_id=template_id, actor=_actor())
    except engine.UploadedTemplateError as exc:
        return out(False, str(exc), gate="PUBLISH_REJECTED")
    except store.TemplateStoreError as exc:
        return out(False, str(exc), gate="TEMPLATE_STORE_FAILED")

    return out(
        True,
        f"Đã phát hành phiên bản v{published.get('activeVersion')} (bất biến).",
        gate="PUBLISHED",
        readback=store.project_template(published, include_detected=True),
    )


def _handle_template_preview(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Render ONE trial file from clearly-labelled sample data, before publish.

    Issue #193 requires the Admin to see the result before activating.  This is
    deliberately the smallest thing that satisfies that: it reuses the SAME
    production renderer over obviously-fake ``[DU LIEU THU]`` facts and hands
    the bytes back to the browser.  It writes NOTHING — no attachment, no
    docgen revision, no shipment record — so a preview can never be mistaken
    for a real document in any history.
    """
    import base64
    import hashlib

    from core.docgen import uploaded_template as engine
    from core.docgen import uploaded_template_store as store

    template_id = _text(payload.get("templateId"))
    request_id = _text(payload.get("requestId"))

    def out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("docgen_template_preview", template_id, ok, error,
                       requestId=request_id, **extra)

    if not _admin_gate():
        return out(False, "RBAC: chỉ Admin mới được xem thử biểu mẫu.",
                   gate="BLOCKED_PERMISSION_DENIED")
    if not template_id:
        return out(False, "Thiếu templateId.", gate="INVALID_REQUEST")

    try:
        template = store.get_template(template_id)
    except store.TemplateStoreError as exc:
        return out(False, str(exc), gate="TEMPLATE_STORE_FAILED")
    if template is None:
        return out(False, "Không tìm thấy biểu mẫu.", gate="TEMPLATE_NOT_FOUND")

    try:
        raw, sha256, mapping = store.preview_source(template)
    except store.TemplateStoreError as exc:
        return out(False, str(exc), gate="TEMPLATE_STORE_FAILED")
    if not mapping:
        return out(False, "Chưa có mapping nào được xác nhận — không có gì để xem thử.",
                   gate="TEMPLATE_NO_MAPPING")

    kind = _text(template.get("kind"))
    try:
        rendered, missing = engine.render_preview(
            raw, kind=kind, template_sha256=sha256, mapping=mapping
        )
    except engine.UploadedTemplateError as exc:
        return out(False, str(exc), gate="PREVIEW_REJECTED")

    label = _text(template.get("label")) or template_id
    file_name = f"XEM-THU_{engine.output_file_name('PREVIEW', label, kind)}"
    return out(
        True,
        "Bản xem thử dùng dữ liệu giả có nhãn; không lưu hồ sơ nào.",
        gate="PREVIEW_READY",
        readback={
            "templateId": template_id,
            "fileName": file_name,
            "mime": engine.MIME_DOCX if kind == engine.KIND_DOCX else engine.MIME_XLSX,
            "bytesBase64": base64.b64encode(rendered).decode("ascii"),
            "sizeBytes": len(rendered),
            "sha256": hashlib.sha256(rendered).hexdigest(),
            "marker": engine.PREVIEW_MARKER,
            "missing": list(missing),
            "persisted": False,
        },
    )


def _handle_template_status_set(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Activate/retire. Retire never deletes bytes or generated history."""
    from core.docgen import uploaded_template as engine
    from core.docgen import uploaded_template_store as store

    template_id = _text(payload.get("templateId"))
    request_id = _text(payload.get("requestId"))
    active = bool(payload.get("active"))

    def out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("docgen_template_status_set", template_id, ok, error,
                       requestId=request_id, **extra)

    if not _admin_gate():
        return out(False, "RBAC: chỉ Admin mới được bật/tắt biểu mẫu.", gate="BLOCKED_PERMISSION_DENIED")
    if not template_id:
        return out(False, "Thiếu templateId.", gate="INVALID_REQUEST")

    try:
        row = store.set_active(template_id=template_id, active=active, actor=_actor())
    except engine.UploadedTemplateError as exc:
        return out(False, str(exc), gate="STATUS_REJECTED")
    except store.TemplateStoreError as exc:
        return out(False, str(exc), gate="TEMPLATE_STORE_FAILED")

    return out(
        True,
        "Đã kích hoạt biểu mẫu." if active else "Đã ngừng dùng biểu mẫu (không xóa lịch sử).",
        gate="ACTIVE" if active else "RETIRED",
        readback=store.project_template(row),
    )


_HANDLERS = {
    "docgen_template_upload": _handle_template_upload,
    "docgen_template_mapping_save": _handle_template_mapping_save,
    "docgen_template_publish": _handle_template_publish,
    "docgen_template_status_set": _handle_template_status_set,
    "docgen_template_preview": _handle_template_preview,
}


def consume_docgen_template_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded template dispatcher (pure over an explicit session).

    Mirrors ``views.user_management.consume_user_management_triggers``: only
    the declared event names are handled, a replayed ``seq`` can never
    double-write, and every outcome (success or refusal) is returned so the
    caller can embed it in ``lastWrites`` for the frontend to match by
    ``requestId``.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(DOCGEN_TEMPLATE_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        if not isinstance(data, dict):
            outcomes.append(_result(event_name, "", False, "Payload không hợp lệ."))
            continue
        handler = _HANDLERS.get(event_name)
        if handler is None:  # pragma: no cover - the two sets agree by construction
            continue
        try:
            outcomes.append(handler(data))
        except Exception as exc:  # noqa: BLE001 - one bad event must not break the run
            outcomes.append(
                _result(event_name, _text(data.get("templateId")), False, f"{type(exc).__name__}: {exc}")
            )
    return outcomes


# ---------------------------------------------------------------------------
# Read projection for /bieu-mau
# ---------------------------------------------------------------------------

def template_workspace_projection(*, db: Any = None, include_detected: bool = True,
                                 registry_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Assemble the Admin template workspace slice (pure read, pure build).

    ``canManage`` is a DISPLAY hint only: the real Admin boundary is re-checked
    server-side by every handler above.

    ``registry_rows`` is a render-local snapshot: when the caller already read
    the registry for this render, pass it in so the registry is not re-read.
    """
    from core.auth import can_operate_business
    from core.docgen import uploaded_template as engine
    from core.docgen import uploaded_template_store as store

    try:
        can_manage = bool(can_operate_business("*"))
    except Exception:  # noqa: BLE001 - a policy read failure is a denial
        can_manage = False
    try:
        rows = store.project_registry(db=db, include_detected=include_detected, registry_rows=registry_rows)
    except Exception:  # noqa: BLE001 - the workspace degrades to an empty list
        rows = []

    active_count = sum(1 for row in rows if row.get("status") == store.STATUS_ACTIVE)
    return {
        "canManage": can_manage,
        "templates": rows,
        "activeCount": active_count,
        "fields": engine.field_catalog_projection(),
        "maxUploadBytes": engine.MAX_TEMPLATE_BYTES,
        "maxUploadLabel": f"{engine.MAX_TEMPLATE_BYTES // (1024 * 1024)} MB",
        "accept": ".docx,.xlsx",
        "notes": [
            "Tệp .doc/.xls cũ và tệp có macro (.docm/.xlsm) bị từ chối; nội dung "
            "tải lên không bao giờ được chạy như Jinja/macro.",
            "Vị trí nhận diện chỉ là gợi ý: Admin xác nhận hoặc sửa một lần, "
            "bản đã phát hành là bất biến.",
            "Chỉ dữ liệu đã xác nhận (công ty, khách hàng, lô hàng, giao hàng, "
            "hợp đồng/dòng hàng duy nhất) được tự điền. Tiền, giá, VAT, điều "
            "khoản thanh toán không phải trường tự điền — phải nhập tay.",
            "Ngừng dùng không xóa phiên bản đã phát hành hay chứng từ đã tạo.",
        ],
    }
