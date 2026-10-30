"""Trao đổi theo công đoạn — cùng một luồng cho Trường Thành và cổng khách.

Hai hàm render dùng chung một backend (:mod:`core.journey_notes`) và chung một
kho chứng từ hiện có (GridFS/Drive đã cấu hình). Không có widget nào nhận
``customer_id`` hay ``shipment_id`` từ trình duyệt: phía khách chỉ dùng danh
tính đã được server chứng minh, phía nội bộ dùng lô đang mở.
"""
from __future__ import annotations

import html as html_lib
from typing import Any, Mapping, Sequence

import streamlit as st

from core import journey_notes as notes
from views import journey_focus

_STAGE_OPTIONS = tuple(zip(notes.STAGE_IDS, (notes.STAGE_LABELS[s] for s in notes.STAGE_IDS)))


def _text(value: Any, limit: int = 0) -> str:
    if value in (None, "") or isinstance(value, bool):
        return ""
    text = str(value).strip()
    return text[:limit] if limit else text


def _escape(value: str) -> str:
    return html_lib.escape(str(value), quote=False)


def _stage_label(stage_id: str) -> str:
    return notes.STAGE_LABELS.get(_text(stage_id), _text(stage_id) or "Công đoạn")


def _stage_index(stage_id: str) -> int:
    """Position of one canonical stage in the selector (0 when unknown)."""
    candidate = _text(stage_id, 40).lower()
    return notes.STAGE_IDS.index(candidate) if candidate in notes.STAGE_IDS else 0


def _stage_choice(label: str, key: str, *, index: int = 0) -> str:
    options = [f"{i:02d} · {name}" for i, (_, name) in enumerate(_STAGE_OPTIONS)]
    safe_index = max(0, min(int(index or 0), len(options) - 1))
    picked = st.selectbox(label, options, index=safe_index, key=key)
    return notes.STAGE_IDS[options.index(picked)] if picked in options else notes.STAGE_IDS[0]


def _attachment_rows(note: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [row for row in (note.get("attachments") or ()) if isinstance(row, Mapping)]


def _show_flash(key_prefix: str, stage_id: str) -> None:
    """One-shot confirmation surviving the rerun that refreshes the thread."""
    key = f"{key_prefix}_{stage_id}_flash"
    message = st.session_state.get(key)
    if not message:
        return
    st.success(str(message))
    st.session_state.pop(key, None)


def _render_thread(thread: Sequence[Mapping[str, Any]], *, key_prefix: str, db: Any,
                   actor: Mapping[str, str]) -> None:
    if not thread:
        st.caption("Chưa có trao đổi nào ở công đoạn này.")
        return
    for note in thread:
        internal = _text(note.get("visibility"), 20).upper() == notes.VISIBILITY_INTERNAL
        badge = "🔒 Nội bộ Trường Thành" if internal else "👁 Khách hàng nhìn thấy"
        who = _escape(_text(note.get("author_name"), 60) or "—")
        kind = "Khách hàng" if _text(note.get("author_kind"), 20) == "customer" else "Trường Thành"
        stamp = _escape(_text(note.get("created_at"), 40).replace("T", " ")[:19])
        # The body is operator/customer text: escape it before any HTML render.
        body = _escape(_text(note.get("body"), notes.MAX_BODY))
        st.markdown(
            f"**{who}** · {kind} · {stamp}  \n"
            f"<span style='font-size:11px;color:#64748B'>{badge}</span>\n\n"
            f"<div style='white-space:pre-wrap'>{body}</div>",
            unsafe_allow_html=True,
        )
        for row in _attachment_rows(note):
            label = _escape(
                f"📎 {_text(row.get('name'), 160)} · {_text(row.get('sizeLabel'), 40)}"
            )
            if st.button(label, key=f"{key_prefix}_dl_{_text(row.get('id'), 80)}"):
                outcome = notes.read_note_attachment(
                    note_id=_text(note.get("id"), 80),
                    attachment_id=_text(row.get("id"), 120),
                    actor=actor,
                    db=db,
                )
                if outcome.get("ok"):
                    st.download_button(
                        "⬇️ Tải xuống",
                        data=outcome.get("data") or b"",
                        file_name=outcome.get("name") or "chung-tu",
                        mime=outcome.get("mime") or "application/octet-stream",
                        key=f"{key_prefix}_save_{_text(row.get('id'), 80)}",
                    )
                else:
                    st.warning(_text(outcome.get("error"), 200) or "Không đọc được chứng từ.")
        st.divider()


def _composer(*, key_prefix: str, db: Any, actor: Mapping[str, str], customer_id: str,
              shipment_id: str, stage_id: str, visibility_options: Sequence[str],
              default_visibility: str, help_text: str) -> None:
    # The composer is keyed by a send counter so a saved note clears the box on
    # the next rerun without mutating a live widget's session-state key. The
    # draft is also keyed by the stage: text typed at one công đoạn must never be
    # sent to another one after the operator switches the selector.
    scope = f"{key_prefix}_{stage_id}"
    seq_key = f"{scope}_seq"
    try:
        seq = int(st.session_state.get(seq_key) or 0)
    except (TypeError, ValueError):
        seq = 0
    body = st.text_area(
        "Nội dung trao đổi", key=f"{scope}_body_{seq}", height=90,
        placeholder=help_text,
    )
    visibility = default_visibility
    if len(visibility_options) > 1:
        visibility = st.radio(
            "Ai nhìn thấy nội dung này?", list(visibility_options),
            index=list(visibility_options).index(default_visibility),
            horizontal=True, key=f"{scope}_vis",
        )
    visibility_value = (
        notes.VISIBILITY_CUSTOMER if visibility.startswith("👁") else notes.VISIBILITY_INTERNAL
    )
    uploads = st.file_uploader(
        "Đính chứng từ (tùy chọn)",
        type=None,
        accept_multiple_files=True,
        key=f"{scope}_files_{seq}",
    )
    if not st.button("Gửi", key=f"{scope}_send"):
        return
    if len(uploads or ()) > notes.MAX_FILES_PER_SUBMIT:
        st.error(f"Tối đa {notes.MAX_FILES_PER_SUBMIT} tệp mỗi lần gửi.")
        return
    files: list[dict[str, Any]] = []
    for upload in (uploads or []):
        files.append({
            "name": getattr(upload, "name", ""),
            "mime": getattr(upload, "type", "") or "",
            "data": upload.getvalue(),
            "size": getattr(upload, "size", None),
        })
    try:
        outcome = notes.create_stage_note(
            customer_id=customer_id,
            shipment_id=shipment_id,
            stage_id=stage_id,
            body=body or "",
            visibility=visibility_value,
            actor=actor,
            files=files,
            db=db,
        )
    except notes.JourneyNoteDenied as denied:
        st.error(_text(denied, 300) or "Không gửi được trao đổi.")
        return
    st.session_state[seq_key] = seq + 1
    message = "Đã lưu trao đổi tại công đoạn này."
    # Keep the confirmation across the refresh rerun so the saved note appears
    # in the thread immediately instead of on the next unrelated interaction.
    st.session_state[f"{scope}_flash"] = message
    st.success(message)
    st.rerun()


def render_internal_discussion(
    shipment_id: str,
    customer_id: str,
    user: Mapping[str, Any],
    *,
    db: Any = None,
    key_prefix: str = "jd_internal",
    focus_stage: str = "",
    expanded: bool = False,
) -> None:
    """Trường Thành: đọc + ghi toàn bộ luồng (cả nội bộ lẫn khách nhìn thấy).

    ``focus_stage`` is the canonical stage a Journey Map node click asked for;
    it only opens the selector on that stage and expands THIS lot's pane. It is
    never trusted as data on its own (see :mod:`views.journey_focus`).
    """
    shipment = _text(shipment_id, 120)
    customer = _text(customer_id, 120)
    if not shipment or not customer:
        st.caption("Chưa xác định được khách hàng của lô này để trao đổi.")
        return
    focus = _text(focus_stage, 40).lower()
    focused = focus in notes.STAGE_IDS
    actor = {
        "kind": "user",
        "username": _text(user.get("username"), 100),
        "role": _text(user.get("role"), 40).lower(),
    }
    scoped_prefix = f"{key_prefix}_{customer}_{shipment}"
    # The focused pane is keyed by stage so a Journey Map click really lands on
    # that stage instead of reusing a previously chosen selector value.
    stage_key = f"{scoped_prefix}_stage" + (f"_focus_{focus}" if focused else "")
    title = "💬 Trao đổi theo công đoạn (Trường Thành ↔ khách hàng)"
    if focused:
        title = f"💬 Trao đổi / Chứng từ · lô {shipment} · công đoạn {_stage_label(focus)}"
    with st.expander(title, expanded=expanded or focused):
        if focused:
            st.caption(
                f"Đang mở từ Journey Map · lô {shipment} · công đoạn {_stage_label(focus)}. "
                "Nội dung và chứng từ dưới đây thuộc đúng lô và đúng công đoạn này."
            )
        try:
            stage = _stage_choice(
                "Công đoạn", stage_key, index=_stage_index(focus) if focused else 0,
            )
            thread = notes.list_stage_notes(
                customer_id=customer, shipment_id=shipment, stage_id=stage,
                actor=actor, db=db,
            )
        except notes.JourneyNoteDenied as denied:
            st.error(_text(denied, 300) or "Không đọc được trao đổi.")
            return
        _show_flash(scoped_prefix, stage)
        _render_thread(thread, key_prefix=f"{scoped_prefix}_{stage}", db=db, actor=actor)
        _composer(
            key_prefix=scoped_prefix, db=db, actor=actor, customer_id=customer,
            shipment_id=shipment, stage_id=stage,
            visibility_options=("🔒 Chỉ nội bộ Trường Thành", "👁 Cho khách hàng xem"),
            default_visibility="🔒 Chỉ nội bộ Trường Thành",
            help_text="Ví dụ: chờ khách xác nhận địa chỉ giao hàng…",
        )


def render_customer_discussion(
    cards: Sequence[Any],
    principal: Any,
    *,
    db: Any = None,
    key_prefix: str = "jd_customer",
    focus: Mapping[str, Any] | None = None,
) -> None:
    """Lục Giác: chỉ thấy nội dung đã cho phép, chỉ ghi vào lô của chính mình.

    ``focus`` comes from :mod:`views.journey_focus` and has already been checked
    against the customer's OWN lots; it can only ever select a lot that is in
    ``cards`` and a stage in the canonical tuple.
    """
    if not cards:
        return
    actor = {
        "kind": "customer",
        "customer_id": _text(getattr(principal, "customer_id", ""), 120),
        "name": _text(getattr(principal, "display_name", ""), 100),
    }
    lot_filter = _text((focus or {}).get("shipment_id"), 120)
    focus_stage = _text((focus or {}).get("stage_id"), 40).lower()
    if focus_stage not in notes.STAGE_IDS:
        focus_stage = ""
    if not actor["customer_id"]:
        return
    targets = [card for card in cards
               if not lot_filter or _text(getattr(card, "reference", ""), 120) == lot_filter]
    if not targets:
        return
    for position, card in enumerate(targets):
        shipment = _text(getattr(card, "reference", ""), 120)
        if not shipment:
            continue
        # Isolation is based on the server-proven principal and lot, not the
        # positional card index, which can be reused by another tenant.
        prefix = f"{key_prefix}_{actor['customer_id']}_{shipment}_{position}"
        focused = bool(focus_stage)
        stage_key = f"{prefix}_stage" + (f"_focus_{focus_stage}" if focused else "")
        with st.expander(f"💬 Trao đổi công đoạn · lô {shipment}", expanded=focused):
            if focused:
                st.caption(
                    f"Đang mở từ Journey Map · lô {shipment} · công đoạn "
                    f"{_stage_label(focus_stage)}."
                )
            try:
                stage = _stage_choice(
                    "Công đoạn", stage_key,
                    index=_stage_index(focus_stage) if focused else 0,
                )
                thread = notes.list_stage_notes(
                    customer_id=actor["customer_id"], shipment_id=shipment,
                    stage_id=stage, actor=actor, db=db,
                )
            except notes.JourneyNoteDenied as denied:
                st.error(_text(denied, 300) or "Không đọc được trao đổi.")
                continue
            _show_flash(prefix, stage)
            _render_thread(thread, key_prefix=f"{prefix}_{stage}", db=db, actor=actor)
            _composer(
                key_prefix=prefix, db=db, actor=actor,
                customer_id=actor["customer_id"], shipment_id=shipment, stage_id=stage,
                visibility_options=("👁 Gửi cho Trường Thành",),
                default_visibility="👁 Gửi cho Trường Thành",
                help_text="Ví dụ: xác nhận địa chỉ giao hàng, hỏi chứng từ…",
            )
