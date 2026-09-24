"""NotebookLM domain router for the internal Telegram staff bot.

Consumer NotebookLM has no stable public chat API. This adapter deliberately
isolates the pinned unofficial notebooklm-py dependency so the rest of the bot
remains usable if Google's undocumented transport changes.

Secrets and notebook IDs are runtime configuration only:
- NOTEBOOKLM_AUTH_JSON: bearer-equivalent Google browser/session state.
- NOTEBOOKLM_NOTEBOOKS_JSON: {"HS": "...", "CHEMICAL": "...", ...}

Use a dedicated Google account shared only to the required notebooks. Never
commit or log NOTEBOOKLM_AUTH_JSON.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

MAX_DOMAIN_COUNT = 3
MAX_DOMAIN_ANSWER = 900
MAX_CITATIONS_PER_DOMAIN = 3
SUPPORTED_DOMAINS = ("HS", "CHEMICAL", "BKHCN", "BTTTT")

_DOMAIN_LABELS = {
    "HS": "🏷 Tra mã HS",
    "CHEMICAL": "🧪 Hóa chất",
    "BKHCN": "🔬 Bộ KH&CN",
    "BTTTT": "📡 Bộ TT&TT",
}

_PATTERNS = {
    "HS": (
        r"\bhs\b",
        r"mã\s*hs",
        r"hs\s*code",
        r"phân\s*loại\s*hàng",
        r"biểu\s*thuế",
        r"thuế\s*nhập\s*khẩu",
    ),
    "CHEMICAL": (
        r"hóa\s*chất",
        r"hoá\s*chất",
        r"\bcas\b",
        r"\bmsds\b",
        r"\bsds\b",
        r"thành\s*phần\s*%",
        r"tiền\s*chất",
        r"toluene|acetone|methanol|ethanol|acid|axit",
    ),
    "BKHCN": (
        r"bộ\s*khoa\s*học",
        r"\bbkhcn\b",
        r"kiểm\s*tra\s*chất\s*lượng",
        r"quy\s*chuẩn\s*kỹ\s*thuật",
        r"đo\s*lường",
        r"máy\s*móc\s*đã\s*qua\s*sử\s*dụng",
        r"máy\s*móc\s*cũ",
    ),
    "BTTTT": (
        r"bộ\s*thông\s*tin",
        r"\bbtttt\b",
        r"wifi|wi-fi|bluetooth",
        r"vô\s*tuyến",
        r"tần\s*số",
        r"router|modem",
        r"thiết\s*bị\s*phát\s*sóng",
        r"viễn\s*thông",
        r"ict",
    ),
}

_DEFAULT_TITLE_ALIASES = {
    "HS": ("Tra mã HS",),
    "CHEMICAL": ("Hóa chất", "Hoá chất"),
    "BKHCN": ("Bộ khoa học công nghệ", "BKHCN"),
    "BTTTT": (
        "Bộ Thông Tin truyền thông",
        "Bộ Thông tin và Truyền thông",
        "BTTTT",
    ),
}

_EXPLICIT_COMMANDS = {
    "/hs": "HS",
    "/hoachat": "CHEMICAL",
    "/chemical": "CHEMICAL",
    "/bkhcn": "BKHCN",
    "/btttt": "BTTTT",
}


class NotebookLMConfigError(RuntimeError):
    """Missing or invalid NotebookLM runtime configuration."""


class NotebookLMServiceError(RuntimeError):
    """NotebookLM was configured but the unofficial connector failed."""


@dataclass(frozen=True)
class RoutedQuestion:
    question: str
    domains: tuple[str, ...]
    explicit: bool = False


@dataclass(frozen=True)
class NotebookAnswer:
    domain: str
    notebook_id: str
    answer: str
    references: tuple[dict[str, Any], ...]


def _load_notebook_map(raw: str | None = None) -> dict[str, str]:
    value = raw if raw is not None else os.environ.get("NOTEBOOKLM_NOTEBOOKS_JSON", "")
    if not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise NotebookLMConfigError(
            "NOTEBOOKLM_NOTEBOOKS_JSON không phải JSON hợp lệ."
        ) from exc
    if not isinstance(parsed, dict):
        raise NotebookLMConfigError(
            "NOTEBOOKLM_NOTEBOOKS_JSON phải là object domain -> notebook_id."
        )
    result: dict[str, str] = {}
    for key, notebook_id in parsed.items():
        domain = str(key).upper().strip()
        value_id = str(notebook_id).strip()
        if domain in SUPPORTED_DOMAINS and value_id:
            result[domain] = value_id
    return result


def _normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFD", str(value or "").casefold())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _load_title_aliases() -> dict[str, tuple[str, ...]]:
    aliases = {key: tuple(values) for key, values in _DEFAULT_TITLE_ALIASES.items()}
    raw = os.environ.get("NOTEBOOKLM_NOTEBOOK_TITLES_JSON", "").strip()
    if not raw:
        return aliases
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NotebookLMConfigError(
            "NOTEBOOKLM_NOTEBOOK_TITLES_JSON không phải JSON hợp lệ."
        ) from exc
    if not isinstance(parsed, dict):
        raise NotebookLMConfigError(
            "NOTEBOOKLM_NOTEBOOK_TITLES_JSON phải là object domain -> title/array."
        )
    for key, value in parsed.items():
        domain = str(key).upper().strip()
        if domain not in SUPPORTED_DOMAINS:
            continue
        values = value if isinstance(value, list) else [value]
        cleaned = tuple(str(item).strip() for item in values if str(item).strip())
        if cleaned:
            aliases[domain] = cleaned
    return aliases


async def _resolve_notebooks(client: Any, domains: tuple[str, ...]) -> list[tuple[str, str]]:
    id_map = _load_notebook_map()
    resolved: dict[str, str] = {
        domain: id_map[domain] for domain in domains if domain in id_map
    }
    unresolved = [domain for domain in domains if domain not in resolved]
    if not unresolved:
        return [(domain, resolved[domain]) for domain in domains]

    notebooks = await client.notebooks.list()
    aliases = _load_title_aliases()
    by_title: dict[str, list[Any]] = {}
    for notebook in notebooks:
        key = _normalize_title(getattr(notebook, "title", ""))
        if key:
            by_title.setdefault(key, []).append(notebook)

    for domain in unresolved:
        matches: list[Any] = []
        for alias in aliases.get(domain, ()):
            matches.extend(by_title.get(_normalize_title(alias), []))
        unique = {
            str(getattr(item, "id", "")): item
            for item in matches
            if str(getattr(item, "id", "")).strip()
        }
        if len(unique) == 1:
            resolved[domain] = next(iter(unique))
        elif len(unique) > 1:
            raise NotebookLMConfigError(
                f"Có nhiều notebook trùng tên cho domain {domain}; hãy cấu hình ID."
            )
        else:
            raise NotebookLMConfigError(
                f"Không tìm thấy notebook cho domain {domain}; hãy kiểm tra quyền chia sẻ/tên."
            )

    return [(domain, resolved[domain]) for domain in domains]


def route_question(text: str) -> RoutedQuestion:
    value = " ".join((text or "").strip().split())
    if not value:
        raise ValueError("Câu hỏi đang trống.")

    first, sep, rest = value.partition(" ")
    command = first.split("@", 1)[0].casefold()
    if command in _EXPLICIT_COMMANDS:
        question = rest.strip() if sep else ""
        if not question:
            raise ValueError(f"Thiếu câu hỏi sau {command}.")
        return RoutedQuestion(
            question=question,
            domains=(_EXPLICIT_COMMANDS[command],),
            explicit=True,
        )

    lowered = value.casefold()
    scored: list[tuple[int, str]] = []
    for domain, patterns in _PATTERNS.items():
        score = sum(
            1
            for pattern in patterns
            if re.search(pattern, lowered, flags=re.IGNORECASE)
        )
        if score:
            scored.append((score, domain))
    scored.sort(key=lambda item: (-item[0], SUPPORTED_DOMAINS.index(item[1])))
    domains = tuple(domain for _, domain in scored[:MAX_DOMAIN_COUNT])
    return RoutedQuestion(question=value, domains=domains, explicit=False)


def _clip(text: Any, limit: int) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


async def _ask_notebooks_async(routed: RoutedQuestion) -> list[NotebookAnswer]:
    if not os.environ.get("NOTEBOOKLM_AUTH_JSON", "").strip() and not os.environ.get(
        "NOTEBOOKLM_HOME", ""
    ).strip():
        raise NotebookLMConfigError(
            "Chưa cấu hình NOTEBOOKLM_AUTH_JSON hoặc NOTEBOOKLM_HOME."
        )

    try:
        from notebooklm import NotebookLMClient
    except ImportError as exc:
        raise NotebookLMConfigError(
            "notebooklm-py chưa được cài trên runtime."
        ) from exc

    try:
        async with NotebookLMClient.from_storage() as client:
            configured = await _resolve_notebooks(client, routed.domains)

            async def one(domain: str, notebook_id: str) -> NotebookAnswer:
                result = await client.chat.ask(notebook_id, routed.question)
                sources = await client.sources.list(notebook_id)
                title_by_id = {
                    str(getattr(source, "id", "")): str(
                        getattr(source, "title", "") or "Nguồn không tên"
                    )
                    for source in sources
                }
                refs: list[dict[str, Any]] = []
                for ref in list(getattr(result, "references", []) or [])[
                    :MAX_CITATIONS_PER_DOMAIN
                ]:
                    source_id = str(getattr(ref, "source_id", "") or "")
                    refs.append(
                        {
                            "citation_number": getattr(
                                ref, "citation_number", None
                            ),
                            "source_id": source_id,
                            "source_title": title_by_id.get(
                                source_id, "Nguồn NotebookLM"
                            ),
                            "cited_text": _clip(
                                getattr(ref, "cited_text", ""), 260
                            ),
                        }
                    )
                return NotebookAnswer(
                    domain=domain,
                    notebook_id=notebook_id,
                    answer=_clip(
                        getattr(result, "answer", ""), MAX_DOMAIN_ANSWER
                    ),
                    references=tuple(refs),
                )

            return list(
                await asyncio.gather(
                    *(
                        one(domain, notebook_id)
                        for domain, notebook_id in configured
                    )
                )
            )
    except NotebookLMConfigError:
        raise
    except Exception as exc:
        raise NotebookLMServiceError(
            f"NotebookLM connector failed: {type(exc).__name__}"
        ) from exc


def ask_notebooks(routed: RoutedQuestion) -> list[NotebookAnswer]:
    if not routed.domains:
        return []
    try:
        return asyncio.run(_ask_notebooks_async(routed))
    except RuntimeError as exc:
        if "asyncio.run()" in str(exc):
            raise NotebookLMServiceError(
                "NotebookLM event-loop conflict."
            ) from exc
        raise


def format_notebook_answers(
    routed: RoutedQuestion,
    answers: list[NotebookAnswer],
) -> str:
    if not answers:
        return (
            "🤔 Chưa xác định được nhóm tra cứu.\n"
            "Hãy bổ sung loại hàng/công dụng/thành phần/model, hoặc dùng "
            "/hs, /hoachat, /bkhcn, /btttt."
        )

    lines = [
        "🧠 TRA CỨU NOTEBOOKLM",
        f"Câu hỏi: {_clip(routed.question, 220)}",
    ]
    for item in answers:
        lines.extend(
            [
                "",
                _DOMAIN_LABELS.get(item.domain, item.domain),
                item.answer,
            ]
        )
        if item.references:
            lines.append("Nguồn NotebookLM:")
            for ref in item.references:
                number = ref.get("citation_number")
                prefix = f"[{number}]" if number is not None else "•"
                title = _clip(ref.get("source_title"), 150)
                cited = _clip(ref.get("cited_text"), 220)
                line = f"{prefix} {title}"
                if cited:
                    line += f" — {cited}"
                lines.append(line)

    lines.extend(
        [
            "",
            "⚠️ NotebookLM là lớp tra cứu nghiệp vụ. "
            "Kết luận pháp lý cần đối chiếu VNLAW/nguồn chính thức.",
        ]
    )
    return "\n".join(lines)


def answer_notebook_question(text: str) -> str:
    routed = route_question(text)
    return format_notebook_answers(routed, ask_notebooks(routed))
