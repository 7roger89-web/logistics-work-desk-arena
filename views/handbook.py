"""LOGI_NOTEBOOK_WORKSPACE_01 — bounded, READ-ONLY handbook projection for /so-tay.

This is deliberately **not** a CMS, wiki, knowledge platform or search engine.  It
reads the operational reference material that the repository ALREADY owns and
that the running features already use, and groups it for the ``/so-tay`` reader:

    core.config               → workflow statuses, Incoterms, carrier tracking
                                links, GetFly service codes
    views/logi_real_data      → the canonical per-shipment document-check frame
    core.docgen.rules         → the locked document-generation rules
    core/trade_compliance     → the official VN discovery registry (with its
                                own version and NOT_RETRIEVED evidence state)
    core.auth                 → the single role → permission matrix
    core.database.load_knowledge_base() → the team's real work notes (existing
                                reader; empty when the deployment has none)

Guarantees enforced by this module:

* No new content store: nothing here is persisted, and no value is copied into a
  second file.  Every row is read from the canonical module at build time.
* No invented operational, legal, tax or customs facts.  Where the repository
  holds no material (Incoterm rule texts, customs rates, legal conclusions) the
  section says so instead of filling the gap.
* No write path: authoring stays in the legacy Streamlit notebook view, which is
  the only writer of ``knowledge_base``.  This projection never calls a saver.
* Provenance passthrough: each section carries its own source; every note keeps
  the date/category/tags recorded with it.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

SECTION_IDS = (
    "quy-trinh",
    "chung-tu",
    "dich-vu",
    "hai-quan",
    "cong-cu",
    "ghi-chu",
)

# Explicit limits: the handbook is a small static reference, so the payload stays
# bounded without a paging service or an index.
MAX_NOTE_ENTRIES = 60


# ---------------------------------------------------------------------------
# small builders (no I/O, no mutation of any source)
# ---------------------------------------------------------------------------


def _provenance(source: str, note: str, *, version: str | None = None) -> dict[str, Any]:
    """Provenance of one section — only fields the source really carries.

    ``updated`` / ``owner`` stay ``None`` unless the underlying material records
    them: an absent date is displayed as absent, never as a guessed one.
    """
    return {
        "source": source,
        "version": version,
        "updated": None,
        "owner": None,
        "note": note,
    }


def _table(columns: Iterable[str], rows: Iterable[Iterable[Any]]) -> dict[str, Any]:
    body = [[("" if cell is None else str(cell)) for cell in row] for row in rows]
    return {"columns": [str(col) for col in columns], "rows": body}


def _entry(
    entry_id: str,
    title: str,
    summary: str,
    *,
    bullets: Iterable[str] = (),
    table: dict[str, Any] | None = None,
    links: Iterable[Mapping[str, str]] = (),
    tags: Iterable[str] = (),
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": entry_id,
        "title": title,
        "summary": summary,
        "bullets": [str(item) for item in bullets],
        "table": table,
        "links": [
            {"label": str(link["label"]), "href": str(link["href"])} for link in links
        ],
        "tags": [str(tag) for tag in tags],
        "provenance": provenance,
    }


def _section(
    section_id: str,
    label: str,
    icon: str,
    lead: str,
    provenance: dict[str, Any],
    entries: list[dict[str, Any]],
    *,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": section_id,
        "label": label,
        "icon": icon,
        "lead": lead,
        "provenance": provenance,
        "entries": entries,
        "state": state,
    }


# ---------------------------------------------------------------------------
# the sections
# ---------------------------------------------------------------------------


def _status_table() -> dict[str, Any]:
    """Verbatim status constants from core.config — no added meaning."""
    from core.config import STATUS_LABELS, STATUS_MAP_FWD, STATUS_OPTIONS

    return _table(
        ["Mã trong hệ thống", "Nhãn việc cần làm", "Nhãn trạng thái lô"],
        [
            (
                code,
                STATUS_LABELS.get(code, ""),
                STATUS_MAP_FWD.get(code, ""),
            )
            for code in STATUS_OPTIONS
        ],
    )


def _stage_table(field_paths: Mapping[str, Any]) -> dict[str, Any]:
    """Which document path each component-editable field writes to.

    Derived from the existing ``FIELD_PATHS`` whitelist in
    ``views/logi_view_model.py`` — the same map that already guards every write.
    """
    grouped: dict[str, list[str]] = {}
    for key, path in field_paths.items():
        parts = [str(part) for part in (path or ())]
        section = parts[1] if len(parts) >= 3 and parts[0] == "data" else "gốc"
        grouped.setdefault(section, []).append(parts[-1] if parts else key)
    return _table(
        ["Nhánh dữ liệu", "Trường được phép cập nhật"],
        [
            (
                f"data.{section}" if section != "gốc" else "(đỉnh lô hàng)",
                ", ".join(sorted(grouped[section])),
            )
            for section in sorted(grouped)
        ],
    )


def _workflow_section(field_paths: Mapping[str, Any]) -> dict[str, Any]:
    return _section(
        "quy-trinh",
        "Luồng lô hàng",
        "truck",
        "Trạng thái và khung dữ liệu mà chính ứng dụng đang dùng cho một lô.",
        _provenance(
            "core/config.py · views/logi_view_model.py",
            "Giá trị nguyên bản từ hằng số đang chạy trong app; đây là tài liệu "
            "tham chiếu của hệ thống, không phải quy định bên ngoài.",
        ),
        [
            _entry(
                "trang-thai",
                "Bốn trạng thái lô hàng",
                "Danh sách trạng thái hợp lệ và nhãn app hiển thị cho từng trạng thái.",
                table=_status_table(),
                bullets=[
                    "Không có trạng thái thứ năm: bộ lọc và kiểm tra của app chỉ nhận các mã ở bảng này.",
                ],
                tags=["trạng thái", "workflow"],
                links=[{"label": "Mở Lô Hàng", "href": "/lo-hang"}],
            ),
            _entry(
                "nganh-du-lieu",
                "Mỗi giai đoạn lưu trường nào",
                "Bộ trường một lô hàng được tổ chức theo nhánh dữ liệu. Danh sách "
                "này lấy đúng từ whitelist mà mọi thao tác sửa đang đi qua.",
                table=_stage_table(field_paths),
                bullets=[
                    "Ngoài danh sách này, không có trường nào khác được cập nhật từ màn hình.",
                    "Số liệu chưa có vẫn để trống — app không thay thế bằng 0.",
                ],
                tags=["dữ liệu", "nhập liệu"],
                links=[{"label": "Mở Chi Tiết Lô 360°", "href": "/lo-hang"}],
            ),
        ],
    )


def _document_checklist_table() -> dict[str, Any]:
    """The canonical check frame, produced by the existing reader itself.

    ``document_checklist`` is called with an empty shipment so the projection
    enumerates the frame it owns; the ``note`` column then shows the honest
    "chưa có" default instead of any fabricated per-shipment state.
    """
    from views.logi_real_data import document_checklist

    rows = document_checklist({})
    return _table(
        ["Mục kiểm tra", "Mặc định khi lô chưa có dữ liệu"],
        [(row.get("name", ""), row.get("note", "")) for row in rows],
    )


def _docgen_rules_table() -> dict[str, Any]:
    from core.docgen import rules

    names = rules._DOC_NAME  # noqa: SLF001 — the single name map of the module
    numbers = rules._DOC_NO_KEY  # noqa: SLF001
    dates = rules._DOC_DATE_KEY  # noqa: SLF001
    return _table(
        ["Loại", "Tên chứng từ", "Trường số", "Trường ngày"],
        [
            (code, names.get(code, ""), numbers.get(code, ""), dates.get(code, ""))
            for code in rules.DOCUMENT_TYPES
        ],
    )


def _documents_section() -> dict[str, Any]:
    from core.docgen import rules

    return _section(
        "chung-tu",
        "Chứng từ",
        "filecheck",
        "Khung kiểm tra chứng từ và các quy tắc sinh chứng từ đã chốt trong app.",
        _provenance(
            "views/logi_real_data.py · core/docgen/rules.py",
            "Quy tắc sinh chứng từ là RULE NỘI BỘ đã chốt cho bộ sinh chứng từ "
            "(LOG-DOCGEN-01 V1) — không phải hướng dẫn nghiệp vụ hải quan hay "
            "quy định pháp luật.",
        ),
        [
            _entry(
                "kiem-tra-chung-tu",
                "Bốn mục kiểm tra của một lô nhập",
                "Khung checklist mà hệ thống tự đánh giá cho từng lô. Trạng thái "
                "thật của mỗi lô hiển thị trong Chi Tiết Lô 360°.",
                table=_document_checklist_table(),
                bullets=[
                    "Bảng này liệt kê KHUNG kiểm tra; cột bên phải là mặc định khi "
                    "chưa có dữ liệu, không phải trạng thái của một lô cụ thể.",
                ],
                tags=["chứng từ", "checklist", "nhập khẩu"],
                links=[{"label": "Mở Lô Hàng", "href": "/lo-hang"}],
            ),
            _entry(
                "chung-tu-sinh",
                "Chứng từ bộ sinh tạo ra",
                "Bốn loại chứng từ và trường định danh pháp lý của từng loại.",
                table=_docgen_rules_table(),
                bullets=[
                    f"Loại áp dụng cho hợp đồng: {', '.join(rules.APPLICABLE_DOCUMENT_TYPES)}",
                    f"Số dòng tối đa — HDMB: {rules.MAX_HDMB_LINES} · Phụ lục: {rules.MAX_PL_LINES}",
                    f"Trạng thái bộ sinh: {', '.join((rules.READY, rules.MISSING_INFO, rules.NOT_APPLICABLE, rules.OWNER_RULE_REQUIRED, rules.BLOCKED))}",
                    f"Trạng thái bản soạn: {', '.join((rules.DRAFT, rules.GENERATED, rules.ISSUED))}",
                ],
                tags=["docgen", "hợp đồng", "chứng từ"],
                links=[{"label": "Mở Hợp Đồng", "href": "/hop-dong"}],
            ),
        ],
    )


def _service_section() -> dict[str, Any]:
    from core.config import GETFLY_SERVICES_LIST, INCOTERMS

    return _section(
        "dich-vu",
        "Dịch vụ & mã phí",
        "calc",
        "Danh mục mã dịch vụ dùng khi nhập/xuất file GetFly, và bộ Incoterm app cho phép.",
        _provenance(
            "core/config.py",
            "Danh mục mã do app dùng cho luồng GetFly; Incoterm chỉ là tập mã "
            "được chấp nhận khi nhập — repo không chứa nội dung giải thích quy "
            "tắc Incoterms, nên trang này không tự đặt ra.",
        ),
        [
            _entry(
                "ma-dich-vu",
                f"Mã dịch vụ GetFly ({len(GETFLY_SERVICES_LIST)} mã)",
                "Mã · tên dịch vụ · đơn vị tính · nhóm, đúng như danh mục đang chạy.",
                table=_table(
                    ["Mã", "Tên dịch vụ", "Đơn vị", "Nhóm"],
                    [
                        (
                            item.get("code", ""),
                            item.get("name", ""),
                            item.get("unit", ""),
                            item.get("group", ""),
                        )
                        for item in GETFLY_SERVICES_LIST
                    ],
                ),
                tags=["getfly", "báo giá", "mã phí"],
                links=[{"label": "Mở Báo Giá", "href": "/kinh-doanh-bao-gia"}],
            ),
            _entry(
                "incoterm",
                "Incoterm hệ thống ghi nhận",
                "Các mã Incoterm mà app cho phép lưu trên lô hàng và báo giá.",
                table=_table(["Incoterm"], [(code,) for code in INCOTERMS]),
                bullets=[
                    "Đây là danh sách giá trị nhập liệu của app, KHÔNG phải định "
                    "nghĩa hay quy tắc pháp lý của Incoterms — repo không chứa "
                    "nguồn đó.",
                ],
                tags=["incoterm", "nhập liệu"],
            ),
        ],
    )


def _customs_section() -> dict[str, Any]:
    from core.trade_compliance.sources import load_official_source_registry

    rows: list[tuple[str, ...]] = []
    registry_id = ""
    version: str | None = None
    live_poc: Any = False
    try:
        registry = load_official_source_registry()
        registry_id = registry.registry_id
        version = registry.version
        live_poc = registry.live_source_poc
        for jurisdiction, records in sorted(registry.jurisdictions.items()):
            for record in records:
                rows.append(
                    (
                        jurisdiction,
                        record.authority,
                        record.source_url or "",
                        record.scope_description or "",
                        str(record.evidence_status.value if hasattr(record.evidence_status, "value") else record.evidence_status),
                    )
                )
    except (OSError, ValueError):  # pragma: no cover — registry ships with the repo
        rows = []

    if not rows:
        return _section(
            "hai-quan",
            "Hải quan · tham chiếu",
            "scale",
            "Chưa đọc được danh mục nguồn chính thức trong môi trường này.",
            _provenance(
                "core/trade_compliance/source_registry.json",
                "Bộ đọc nguồn trả về danh mục rỗng; trang không tự thêm nguồn.",
            ),
            [],
            state={
                "tone": "gray",
                "text": "Không có mục nào để hiển thị. Sổ tay không tạo danh sách "
                "nguồn giả định.",
            },
        )

    return _section(
        "hai-quan",
        "Hải quan · tham chiếu",
        "scale",
        "Điểm truy cập nguồn chính thức Việt Nam mà hệ thống đăng ký — kèm trạng "
        "thái chứng cứ thật của từng nguồn.",
        _provenance(
            f"core/trade_compliance/source_registry.json · {registry_id}",
            "Danh mục đăng ký nguồn (discovery) — chưa truy xuất, không chứa thuế "
            "suất hay kết luận pháp lý. Không mục nào ở đây được coi là xác nhận "
            "chính thức cho một lô hàng cụ thể.",
            version=version,
        ),
        [
            _entry(
                "nguon-chinh-thuc",
                f"Điểm truy cập chính thức ({len(rows)} nguồn)",
                "Trạng thái `NOT_RETRIEVED` nghĩa là hệ thống chưa lấy và chưa "
                "xác minh nội dung của nguồn này.",
                table=_table(
                    ["Khu vực pháp lý", "Cơ quan", "URL", "Phạm vi", "Trạng thái chứng cứ"],
                    rows,
                ),
                bullets=[
                    f"Số hóa nguồn sống trong registry: {'BẬT' if live_poc else 'TẮT'}.",
                    "Thuế suất/HS cụ thể phải tra ở mục Tra cứu thuế / HS, không suy ra từ đây.",
                ],
                tags=["hải quan", "nguồn", "trade compliance"],
                links=[{"label": "Mở Tra cứu thuế / HS", "href": "/tra-cuu-thue"}],
            ),
        ],
    )


def _tools_section() -> dict[str, Any]:
    from core.auth import ROLE_PERMISSIONS
    from core.config import CARRIER_LINKS

    return _section(
        "cong-cu",
        "Công cụ & phân quyền",
        "search",
        "Liên kết tracking hãng tàu app dùng, và ma trận quyền duy nhất theo vai trò.",
        _provenance(
            "core/config.py · core/auth.py",
            "Liên kết tracking là mẫu URL cấu hình sẵn (`{ref}` = số vận đơn/"
            "container). Ma trận quyền là CHÍNH SÁCH server-side; UI chỉ hiển thị.",
        ),
        [
            _entry(
                "tracking",
                f"Liên kết theo dõi theo hãng tàu ({len(CARRIER_LINKS)})",
                "Mẫu URL app dùng khi dựng link theo dõi container/vận đơn.",
                table=_table(
                    ["Hãng tàu / hãng chuyển phát", "Mẫu URL"],
                    [(carrier, url) for carrier, url in CARRIER_LINKS.items()],
                ),
                tags=["tracking", "hãng tàu"],
                links=[{"label": "Mở Lô Hàng", "href": "/lo-hang"}],
            ),
            _entry(
                "phan-quyen",
                "Ai được làm gì (ma trận vai trò)",
                "Quyền theo vai trò, đúng như `ROLE_PERMISSIONS` đang chạy.",
                table=_table(
                    ["Vai trò", "Quyền"],
                    [
                        (
                            role,
                            "*" if "*" in perms else ", ".join(sorted(perms)),
                        )
                        for role, perms in sorted(ROLE_PERMISSIONS.items())
                    ],
                ),
                bullets=[
                    "admin = `*` (toàn quyền); các vai trò khác chỉ có quyền liệt kê ở đây.",
                    "Role switcher trên thanh bên chỉ để xem — ranh giới thật là core.auth ở server.",
                ],
                tags=["rbac", "vai trò"],
            ),
        ],
    )


def _note_provenance(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Per-note provenance — only what the stored entry actually carries.

    ``created_by`` / ``updated_by`` are written by the canonical ``_save_document``
    helper, so when they exist they are reported as the owner; when they do not,
    ``owner`` stays ``None`` instead of naming somebody.
    """
    recorded = str(entry.get("date") or entry.get("updated_at") or "").strip()
    owner = next(
        (
            str(entry.get(field) or "").strip()
            for field in ("author", "updated_by", "created_by")
            if str(entry.get(field) or "").strip()
        ),
        "",
    )
    return {
        "source": "knowledge_base (đọc qua core.database.load_knowledge_base)",
        "version": None,
        "updated": recorded or None,
        "owner": owner or None,
        "note": "Ghi chú do đội ngũ tự ghi — nội dung người dùng, không phải quy "
        "định chính thức.",
    }


def _notes_section(notes: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
    provenance = _provenance(
        "core/database.load_knowledge_base · views/knowledge_base.py",
        "Sổ tay kinh nghiệm của đội ngũ. Trang này chỉ đọc: thêm/sửa/xóa vẫn "
        "nằm ở màn hình Streamlit cũ, và Sổ tay không tạo nội dung thay thế.",
    )
    rows = [note for note in (notes or ()) if isinstance(note, Mapping)]
    total = len(rows)
    entries: list[dict[str, Any]] = []
    for index, note in enumerate(rows[:MAX_NOTE_ENTRIES]):
        title = str(note.get("title") or "").strip() or "(không tiêu đề)"
        content = str(note.get("content") or "").strip()
        category = str(note.get("category") or "").strip()
        tags = [str(tag) for tag in (note.get("tags") or []) if str(tag).strip()]
        recorded = str(note.get("date") or note.get("updated_at") or "").strip()
        entries.append(
            {
                "id": f"ghi-chu-{index + 1}",
                "title": title,
                "summary": content,
                "bullets": [part for part in (
                    f"Phân loại: {category}" if category else "",
                    f"Cập nhật: {recorded}" if recorded else "Cập nhật: chưa ghi nhận",
                    f"Từ khóa: {', '.join(tags)}" if tags else "",
                ) if part],
                "table": None,
                "links": [],
                "tags": tags or ([category] if category else []),
                "provenance": _note_provenance(note),
            }
        )
        if len(entries) >= MAX_NOTE_ENTRIES:
            break

    if not entries:
        return _section(
            "ghi-chu",
            "Ghi chú đội ngũ",
            "book",
            "Kho ghi chú kinh nghiệm chung của đội, đọc từ cùng một nguồn mà màn hình Sổ tay cũ dùng.",
            provenance,
            [],
            state={
                "tone": "gray",
                "text": "Cơ sở dữ liệu đang dùng chưa có ghi chú nào. Sổ tay hiển "
                "thị đúng trạng thái này và không tự soạn nội dung thay thế.",
            },
        )

    if total > len(entries):
        # The payload stays bounded; the truncation is stated, never hidden.
        lead = (
            f"{len(entries)}/{total} ghi chú kinh nghiệm trong nguồn dùng chung của "
            f"đội (trang hiển thị tối đa {MAX_NOTE_ENTRIES})."
        )
    else:
        lead = f"{total} ghi chú kinh nghiệm đang có trong nguồn dùng chung của đội."

    return _section(
        "ghi-chu",
        "Ghi chú đội ngũ",
        "book",
        lead,
        provenance,
        entries,
    )


# ---------------------------------------------------------------------------
# the one public entry point
# ---------------------------------------------------------------------------


def handbook_projection(
    field_paths: Mapping[str, Any] | None = None,
    notes: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble the ``/so-tay`` handbook slice.  Pure read, pure build."""

    note_rows = [note for note in (notes or ()) if isinstance(note, Mapping)]
    sections = [
        _workflow_section(dict(field_paths or {})),
        _documents_section(),
        _service_section(),
        _customs_section(),
        _tools_section(),
        _notes_section(note_rows),
    ]

    entry_count = sum(len(section["entries"]) for section in sections)
    available = [
        section["label"] for section in sections if section["entries"]
    ]
    empty = [
        section["label"] for section in sections if not section["entries"]
    ]

    return {
        "classification": "STATIC_CONTENT_READY",
        "readOnly": True,
        "sections": sections,
        "counts": {
            "sectionCount": len(sections),
            "availableSectionCount": len(available),
            "entryCount": entry_count,
            "noteCount": len(sections[SECTION_IDS.index("ghi-chu")]["entries"]),
            # The full source count, so a bounded payload never looks like the
            # whole corpus.
            "noteTotal": len(note_rows),
        },
        # What this page explicitly does NOT provide.  These are honest scope
        # statements, not sections with invented content.
        "unavailable": [
            "Không có nội dung hướng dẫn từng bước (tutorial) — repo không chứa "
            "nguồn đó, nên trang không tự viết ra.",
            "Không có quy tắc Incoterms, quy định hải quan, thuế suất hay tư vấn "
            "pháp lý; chỉ có danh mục giá trị/danh mục nguồn mà app đang dùng.",
            "Không có bộ máy soạn thảo, phiên bản, duyệt bài hay tìm kiếm toàn "
            "văn trong trang này; bộ lọc chỉ là so khớp chữ trên dữ liệu đã tải.",
        ],
        "sectionsUnavailable": empty,
        "sectionsAvailable": available,
    }
