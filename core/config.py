"""Cấu hình tập trung cho LOGISTICS PRO.

Ưu tiên cấu hình theo thứ tự:
1. Biến môi trường.
2. ``st.secrets`` khi ứng dụng đang chạy bằng ``streamlit run``.
3. File ``.streamlit/secrets.toml`` khi chạy script CLI bằng ``python``.

Module hỗ trợ cả định dạng secrets mới dạng bảng và định dạng cũ dạng key phẳng.
Không lưu credential trong source code.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

try:
    import streamlit as st
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ImportError:
        get_script_run_ctx = None  # type: ignore[assignment]
except ImportError:
    st = None  # type: ignore[assignment]
    get_script_run_ctx = None  # type: ignore[assignment]

BASE_DIR = Path(__file__).resolve().parents[1]


def is_streamlit_runtime() -> bool:
    """Trả về True chỉ khi đang thực sự chạy trong một Streamlit session."""
    if st is None or get_script_run_ctx is None:
        return False
    try:
        return get_script_run_ctx(suppress_warning=True) is not None
    except TypeError:
        try:
            return get_script_run_ctx() is not None
        except Exception:
            return False
    except Exception:
        return False


def _candidate_secrets_files() -> list[Path]:
    candidates: list[Path] = []
    explicit = os.getenv("LOGISTICS_PRO_SECRETS_FILE", "").strip()
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend([
        Path.cwd() / ".streamlit" / "secrets.toml",
        BASE_DIR / ".streamlit" / "secrets.toml",
    ])

    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        resolved = str(path.resolve()) if path.exists() else str(path.absolute())
        if resolved not in seen:
            unique.append(path)
            seen.add(resolved)
    return unique


@lru_cache(maxsize=1)
def _load_file_secrets() -> tuple[dict[str, Any], Path | None]:
    for path in _candidate_secrets_files():
        if not path.is_file():
            continue
        try:
            with path.open("rb") as handle:
                payload = tomllib.load(handle)
            if isinstance(payload, dict):
                return payload, path.resolve()
        except (OSError, tomllib.TOMLDecodeError):
            continue
    return {}, None


def get_loaded_secrets_path() -> str:
    """Đường dẫn secrets.toml được CLI loader sử dụng, không chứa secret value."""
    _, path = _load_file_secrets()
    return str(path) if path else ""


def _lookup(source: Any, path: Iterable[str], default: Any = None) -> Any:
    value = source
    for key in path:
        try:
            value = value[key]
        except (KeyError, TypeError, AttributeError):
            return default
    return value


def _secret_value(*path: str, default: Any = None) -> Any:
    # Không truy cập st.secrets trong bare mode để tránh missing ScriptRunContext.
    if is_streamlit_runtime():
        try:
            value = _lookup(st.secrets, path, default=None)
            if value is not None:
                return value
        except (FileNotFoundError, RuntimeError):
            pass

    file_secrets, _ = _load_file_secrets()
    return _lookup(file_secrets, path, default=default)


def _normalize_path(path: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(path, str):
        return (path,)
    return tuple(path)


def get_setting(
    env_name: str,
    *secret_paths: str | Iterable[str],
    default: str = "",
) -> str:
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return str(env_value)

    for path in secret_paths:
        value = _secret_value(*_normalize_path(path), default=None)
        if value not in (None, ""):
            return str(value)
    return default


def get_raw_setting(env_name: str, *secret_paths: str | Iterable[str], default: Any = None) -> Any:
    """Like :func:`get_setting` but returns the RAW value (never stringified).

    JSON- or table-shaped settings (for example a Google service-account
    payload, which may arrive as a JSON string OR as a TOML table) must not be
    passed through ``str()``, which would corrupt them. Precedence is unchanged:
    environment variable first, then the same secrets paths ``get_setting``
    already supports.
    """
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value

    for path in secret_paths:
        value = _secret_value(*_normalize_path(path), default=None)
        if value not in (None, ""):
            return value
    return default


def _parse_list_env_value(raw: str) -> list[str]:
    """Parse one environment variable as a JSON list or comma-separated list."""
    raw = raw.strip()
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
        if isinstance(decoded, list):
            return [str(item).strip() for item in decoded if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in raw.split(",") if item.strip()]


def get_list_setting(
    env_name: str,
    *secret_paths: str | Iterable[str],
) -> list[str]:
    env_value = os.getenv(env_name)
    if env_value:
        return _parse_list_env_value(env_value)

    for path in secret_paths:
        value = _secret_value(*_normalize_path(path), default=None)
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        if value not in (None, ""):
            return [str(value).strip()]
    return []


# Hỗ trợ cả định dạng mới [mongo] và định dạng cũ MONGO_URI = "...".
MONGO_URI = get_setting("MONGO_URI", ("mongo", "uri"), "MONGO_URI")
MONGO_DB_NAME = get_setting(
    "MONGO_DB_NAME",
    ("mongo", "database"),
    "MONGO_DB_NAME",
    default="",
)

# LOGI_SHIPMENT_DOCUMENTS_GRIDFS_RUNTIME_01 — the bounded attachment selector.
# GridFS is the deployable default because it uses the MongoDB Atlas/PyMongo
# infrastructure already owned by the application. ``drive_shared`` remains an
# explicit, optional legacy path; it never silently becomes a fallback.
ATTACHMENT_STORAGE_BACKEND = get_setting(
    "ATTACHMENT_STORAGE_BACKEND",
    ("attachments", "storage_backend"),
    "ATTACHMENT_STORAGE_BACKEND",
    default="gridfs",
).strip().lower() or "gridfs"
ATTACHMENT_STORAGE_BACKENDS = frozenset({"gridfs", "drive_shared"})


def get_attachment_storage_backend() -> str:
    """Resolve the current bounded selector without treating unknown as valid."""
    # Environment values are intentionally read at call time so isolated tests
    # and preview processes can select a backend without reloading the module.
    return get_setting(
        "ATTACHMENT_STORAGE_BACKEND",
        ("attachments", "storage_backend"),
        "ATTACHMENT_STORAGE_BACKEND",
        default=ATTACHMENT_STORAGE_BACKEND,
    ).strip().lower() or ATTACHMENT_STORAGE_BACKEND

# LG01 (W1): fail-closed data boundary. App chỉ được ghi vào các database
# được phép liệt kê rõ ràng; URI thiếu hoặc tên DB ngoài danh sách sẽ FAIL.
MONGO_ALLOWED_DB_NAMES = get_list_setting(
    "MONGO_ALLOWED_DB_NAMES",
    ("mongo", "allowed_databases"),
    "MONGO_ALLOWED_DB_NAMES",
)
if not MONGO_ALLOWED_DB_NAMES:
    MONGO_ALLOWED_DB_NAMES = ["logistics_workdesk_logc14", "logistics_workdesk_LG01_E2E"]
ENV_IDENTITY = get_setting("ENV_IDENTITY", ("env", "identity"),
    "ENV_IDENTITY", default="DEV").upper()

# DeepL credentials remain server-side.  Keep the list loader shared with the
# existing Gemini configuration so TOML and environment-list forms behave the
# same way without adding a credential-management subsystem.
def _deepl_api_keys() -> list[str]:
    """Resolve DeepL credentials from every supported shape.

    LOGI_TRANSLATION_RUNTIME_UI_PARITY_01 — backward-compatible fix for the
    deployed failure: the previous loader only accepted the PLURAL shapes, so
    a key configured as ``[deepl].api_key`` / ``DEEPL_API_KEY`` (singular)
    yielded an empty list and the whole translation capability reported
    "chưa cấu hình" even though a key WAS present in Streamlit secrets.

    Deterministic precedence — the FIRST non-empty source wins and sources are
    never concatenated, so duplicated credential shapes can never double-bill:

      1. env ``DEEPL_API_KEYS``        (JSON list or comma-separated)
      2. env ``DEEPL_API_KEY``         (single key)
      3. secrets ``[deepl].api_keys``  (then legacy flat ``DEEPL_API_KEYS``)
      4. secrets ``[deepl].api_key``   (then legacy flat ``DEEPL_API_KEY``)

    Normalized result: ``list[str]`` (possibly empty). No value is ever
    logged or returned for display.
    """
    env_plural = os.getenv("DEEPL_API_KEYS")
    if env_plural:
        keys = _parse_list_env_value(env_plural)
        if keys:
            return keys

    env_single = str(os.getenv("DEEPL_API_KEY") or "").strip()
    if env_single:
        return [env_single]

    for path in (("deepl", "api_keys"), "DEEPL_API_KEYS"):
        value = _secret_value(*_normalize_path(path), default=None)
        if isinstance(value, (list, tuple)):
            keys = [str(item).strip() for item in value if str(item).strip()]
            if keys:
                return keys
        if value not in (None, ""):
            cleaned = str(value).strip()
            if cleaned:
                return [cleaned]

    for path in (("deepl", "api_key"), "DEEPL_API_KEY"):
        value = _secret_value(*_normalize_path(path), default=None)
        if value not in (None, ""):
            cleaned = str(value).strip()
            if cleaned:
                return [cleaned]

    return []


DEEPL_API_KEYS = _deepl_api_keys()

# LOG-LG02 release gate (default OFF: production DB remains fail-closed).
def _parse_bool(val: Any) -> bool:
    if isinstance(val, bool): return val
    s = str(val or "").strip().lower()
    return s in ("true", "1", "yes", "on")

MONGO_RELEASE_MODE = _parse_bool(
    get_setting("MONGO_RELEASE_MODE", ("mongo", "release_mode"), "MONGO_RELEASE_MODE")
)

_PRODUCTION_DB_NAMES = frozenset({"logistics_db"})
_STAGING_DB_NAMES = frozenset({"logistics_staging"})


def validate_mongo_identity() -> None:
    """Fail-closed guard: kiểm MONGO_URI + MONGO_DB_NAME trước khi app hoạt động.
    
    LOG-REL-01: Thắt chặt cách ly giữa Production và Staging/Preview.
    """
    if not MONGO_URI:
        raise RuntimeError(
            "Chưa cấu hình MongoDB. Thêm [mongo].uri hoặc MONGO_URI vào "
            ".streamlit/secrets.toml, hoặc đặt biến môi trường MONGO_URI."
        )
    db_name = str(MONGO_DB_NAME or "").strip()
    if not db_name:
        raise RuntimeError(
            "Chưa cấu hình [mongo].database / MONGO_DB_NAME. Không dùng giá trị "
            "mặc định; đặt tên database phát triển tường minh."
        )

    # LOG-REL-01 (W4): Database isolation based on environment identity.
    if ENV_IDENTITY == "PRODUCTION":
        if db_name not in _PRODUCTION_DB_NAMES:
            raise RuntimeError(
                f"LỖI CÁCH LY: App đang chạy ở chế độ PRODUCTION nhưng kết nối tới DB '{db_name}'. "
                f"Chỉ cho phép: {list(_PRODUCTION_DB_NAMES)}"
            )
        if not bool(MONGO_RELEASE_MODE):
            raise RuntimeError(
                "LỖI CẤU HÌNH: Chế độ PRODUCTION yêu cầu MONGO_RELEASE_MODE=true."
            )
    elif ENV_IDENTITY == "STAGING" or ENV_IDENTITY == "PREVIEW":
        if db_name in _PRODUCTION_DB_NAMES:
            raise RuntimeError(
                f"LỖI CÁCH LY NGUY HIỂM: App '{ENV_IDENTITY}' đang cố gắng ghi vào PRODUCTION DB '{db_name}'. "
                "Hành động này bị chặn để bảo vệ dữ liệu khách hàng thực tế."
            )
        if db_name not in _STAGING_DB_NAMES and db_name not in MONGO_ALLOWED_DB_NAMES:
             raise RuntimeError(
                f"LỖI CẤU HÌNH: App '{ENV_IDENTITY}' yêu cầu database staging hoặc được phép. "
                f"Hiện tại: {db_name}. Cho phép: {list(_STAGING_DB_NAMES)}"
            )

    # Fallback legacy checks
    if db_name in _PRODUCTION_DB_NAMES and not bool(MONGO_RELEASE_MODE):
        raise RuntimeError(
            f"MONGO_DB_NAME={db_name} là tên database PRODUCTION. "
            "Chưa bật chế độ phát hành (MONGO_RELEASE_MODE=true). Chỉ Owner được phép bật."
        )
    
    # Ensure the DB is at least in the allowed list if not production/staging
    if db_name not in MONGO_ALLOWED_DB_NAMES and db_name not in _PRODUCTION_DB_NAMES and db_name not in _STAGING_DB_NAMES:
        raise RuntimeError(
            f"MONGO_DB_NAME={db_name} không thuộc danh sách MONGO_ALLOWED_DB_NAMES."
        )


_single_gemini_key = get_setting(
    "GEMINI_API_KEY",
    ("gemini", "api_key"),
    "GEMINI_API_KEY",
)
GEMINI_API_KEYS = get_list_setting(
    "GEMINI_KEYS",
    ("gemini", "api_keys"),
    "GEMINI_KEYS",
)
if _single_gemini_key:
    GEMINI_API_KEYS = [_single_gemini_key] + [
        key for key in GEMINI_API_KEYS if key != _single_gemini_key
    ]
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""
GEMINI_MODEL = get_setting(
    "GEMINI_MODEL",
    ("gemini", "model"),
    "GEMINI_MODEL",
    default="gemini-3.6-flash",
)

TELEGRAM_TOKEN = get_setting(
    "TELEGRAM_TOKEN",
    ("telegram", "token"),
    "TELEGRAM_TOKEN",
)
TELEGRAM_CHAT_ID = get_setting(
    "TELEGRAM_CHAT_ID",
    ("telegram", "chat_id"),
    "TELEGRAM_CHAT_ID",
)
def _load_auth_required() -> bool:
    """Fail closed: missing auth configuration still requires login.

    Local/dev single-user mode remains available only when explicitly selected
    with AUTH_REQUIRED=false or [auth].required=false.
    """
    return get_setting(
        "AUTH_REQUIRED",
        ("auth", "required"),
        "AUTH_REQUIRED",
        default="true",
    ).strip().lower() in {"1", "true", "yes", "on"}


AUTH_REQUIRED = _load_auth_required()

# DISPLAY_COMPANY_NAME — the operating/display brand shown on ordinary
# product surfaces (browser tab title, login card, shell header subtitle).
# This is DISPLAY identity ONLY: the formal legal company identity used by
# contracts, payments and PXK/GNT document generation keeps deriving from
# the authority_companies master (core.database.load_authority_companies).
# Never substitute this brand string for a legal_name or any statutory fact.
DISPLAY_COMPANY_NAME = get_setting(
    "DISPLAY_COMPANY_NAME",
    ("display", "company_name"),
    "DISPLAY_COMPANY_NAME",
    default="Trường Thành Logistics",
)

TARIFF_DB_PATH = Path(get_setting(
    "TARIFF_DB_PATH",
    ("paths", "tariff_db"),
    "TARIFF_DB_PATH",
    default=str(BASE_DIR / "tariff.db"),
))
GNT_TEMPLATE_PATH = Path(get_setting(
    "GNT_TEMPLATE_PATH",
    ("paths", "gnt_template"),
    "GNT_TEMPLATE_PATH",
    default=str(BASE_DIR / "GNT_MAU.xlsx"),
))
TREASURY_FILE_PATH = Path(get_setting(
    "TREASURY_FILE_PATH",
    ("paths", "treasury_file"),
    "TREASURY_FILE_PATH",
    default=str(BASE_DIR / "MA_NGAN_SACH.xlsx"),
))

# LOG-DOCGEN-01: bounded runtime template directory.  The legal template
# binaries are sandbox-only and must NOT be committed to this repository, so we
# never default this to an in-repo path.  When empty the generator reports the
# TEMPLATE_ASSET_STORAGE_OWNER_GATE instead of generating from a wrong file.
_docgen_template_dir = get_setting(
    "DOCGEN_TEMPLATE_DIR",
    ("paths", "docgen_templates"),
    "DOCGEN_TEMPLATE_DIR",
    default="",
).strip()
DOCGEN_TEMPLATE_DIR = Path(_docgen_template_dir) if _docgen_template_dir else None

INCOTERMS = ["EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"]

STATUS_OPTIONS = ["wait", "pending", "done", "cancel"]
STATUS_LABELS = {
    "wait": "Chưa xử lý",
    "pending": "Đang xử lý",
    "done": "Hoàn thành",
    "cancel": "Đã hủy",
}
STATUS_MAP_INV = STATUS_LABELS
STATUS_MAP_FWD = {
    "wait": "Chờ chứng từ",
    "pending": "Đang thông quan/Giao hàng",
    "done": "Hoàn thành",
    "cancel": "Đã hủy",
}

CARRIER_LINKS = {
    "Maersk": "https://www.maersk.com/tracking/{ref}",
    "MSC": "https://www.msc.com/track-a-shipment?agencyPath=usa&trackingNumber={ref}",
    "CMA CGM": "https://www.cma-cgm.com/ebusiness/tracking/search?SearchBy=Container&Reference={ref}",
    "COSCO": "https://elines.coscoshipping.com/ebusiness/cargoTracking?trackingType=CONTAINER&number={ref}",
    "Evergreen": "https://ct.shipmentlink.com/servlet/TDB1_CargoTracking.do?TYPE=BL&BL={ref}",
    "ONE": "https://ecomm.one-line.com/one-ecom/manage-shipment/cargo-tracking?trakNoParam={ref}",
    "Hapag-Lloyd": "https://www.hapag-lloyd.com/en/online-business/track/track-by-container-solution.html?container={ref}",
    "Wan Hai": "https://www.wanhai.com/views/cargoTrack/CargoTrack.xhtml?refNo={ref}",
    "SITC": "https://www.sitc.com/track?number={ref}",
    "DHL": "https://www.dhl.com/global-en/home/tracking.html?tracking-id={ref}",
    "FedEx": "https://www.fedex.com/fedextrack/?trknbr={ref}",
    "UPS": "https://www.ups.com/track?tracknum={ref}",
}

GETFLY_SERVICES_LIST = [
    {"code": "DVK", "name": "Phí dịch vụ khác", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "VCND 40", "name": "Vận chuyển nội địa cont 40", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "DH", "name": "Đóng hộ", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "BHHH", "name": "Bảo hiểm hàng hóa", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "NKOFLCL", "name": "Cước biển hàng LCL nhập khẩu (M3)", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "XKAF", "name": "Cước vận chuyển quốc tế hàng không (AF) hàng xuất", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "NKAF", "name": "Cước vận chuyển quốc tế hàng không (air) hàng NK", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "CNHQ", "name": "Chứng nhận hợp quy", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "XKOFLCL", "name": "Cước vận tải biển quốc tế hàng lẻ (LCL) xuất khẩu", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "NKOF20", "name": "Cước vận tải biển quốc tế hàng NK cont 20", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "NKOF40", "name": "Cước vận tải biển quốc tế hàng NK cont 40", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "XKOF40", "name": "Cước vận tải biển quốc tế hàng xuất container 40", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "XKOF20", "name": "Cước vận tải biển quốc tế hàng xuất container 20", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "TQ", "name": "Dịch vụ thông quan", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "DDC", "name": "Door - to - door", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "LCC", "name": "Local charges (Phụ phí tại cảng)", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "LCX", "name": "Lưu ca xe", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "EXW", "name": "Phí EXWORK", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "NH", "name": "Nâng hạ", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "PKH", "name": "Phí kiểm hóa", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "TTHQ", "name": "Thủ tục hải quan", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "GP", "name": "Giấy phép", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "HT", "name": "Hun trùng", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "HHNKUT", "name": "Tiền hàng NK ủy thác", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "KD", "name": "Kiểm dịch", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "KTCL", "name": "Kiểm tra chất lượng", "unit": "Lần", "group": "DỊCH VỤ XNK"},
    {"code": "CO", "name": "Xin C/O", "unit": "Lần", "group": "DỊCH VỤ XNK"},
]
