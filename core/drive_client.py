"""LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — the SMALLEST Google Drive byte store.

Ported (source only) from donor PR #49 onto current main; the narrow
google-auth AuthorizedSession + Drive REST v3 path is unchanged.

Google Drive owns attachment BYTES; Mongo owns bounded METADATA only. This
module is the ONE bounded Drive adapter for that slice and it deliberately
stays tiny:

* auth = one explicitly selected credential mode. ``drive_shared`` keeps the
  original service-account JSON and writable Workspace Shared Drive contract.
  ``drive_oauth`` uses an Owner-authorized OAuth refresh token plus client
  credentials to write to the Owner's My Drive. Both modes use the same
  ``GOOGLE_DRIVE_ROOT_FOLDER_ID`` boundary, and neither silently falls back
  to the other;
* transport = ``google-auth`` (``AuthorizedSession``) over the ``requests``
  dependency the app ALREADY ships, talking to the Drive REST v3 endpoints
  directly — the full ``google-api-python-client`` SDK is NOT installed;
* operations = ensure/find folder, upload, fetch metadata, download, plus the
  ONE bounded compensating delete the orphan rule needs. No sync daemon, no
  watcher, no folder migration, no cloud-provider abstraction layer.

Security posture (no exceptions in this module):

* credential material is read from env/secrets at call time and never logged,
  never returned to the browser and never written to Mongo;
* Drive errors are re-raised as :class:`DriveError` carrying an HTTP status or
  an exception CLASS NAME only — no token, no request body, no key material;
* folder/file names are sanitized here as well as in the caller, so a name can
  never introduce a path separator or traverse upwards.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from core.config import get_raw_setting, get_setting

LOGGER = logging.getLogger("logistics_pro.drive")

DRIVE_API = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"
DRIVE_FOLDER_MIME = "application/vnd.google-apps.folder"
#: Scope URL for the service account — a public API identifier, not a secret.
DRIVE_SCOPES = ("https://www.googleapis.com/auth/drive",)
DRIVE_TIMEOUT_SECONDS = 60

#: Logical settings (env var names; the same names work as flat or nested
#: secrets keys — see ``core.config.get_setting`` / ``get_raw_setting``).
ROOT_FOLDER_ENV = "GOOGLE_DRIVE_ROOT_FOLDER_ID"
SERVICE_ACCOUNT_ENV = "GOOGLE_SERVICE_ACCOUNT_JSON"
OAUTH_CLIENT_ID_ENV = "GOOGLE_DRIVE_OAUTH_CLIENT_ID"
OAUTH_CLIENT_SECRET_ENV = "GOOGLE_DRIVE_OAUTH_CLIENT_SECRET"
OAUTH_REFRESH_TOKEN_ENV = "GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN"
OAUTH_TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_MODE_SERVICE_ACCOUNT = "service_account"
AUTH_MODE_USER_OAUTH = "user_oauth"
SERVICE_ACCOUNT_SECRET_PATHS: tuple[tuple[str, ...], ...] = (
    (SERVICE_ACCOUNT_ENV,),
    ("google_drive", "service_account_json"),
    ("google_drive", "service_account"),
)
ROOT_FOLDER_SECRET_PATHS: tuple[tuple[str, ...], ...] = (
    (ROOT_FOLDER_ENV,),
    ("google_drive", "root_folder_id"),
)
OAUTH_CLIENT_ID_SECRET_PATHS: tuple[tuple[str, ...], ...] = (
    (OAUTH_CLIENT_ID_ENV,),
    ("google_drive", "oauth_client_id"),
)
OAUTH_CLIENT_SECRET_SECRET_PATHS: tuple[tuple[str, ...], ...] = (
    (OAUTH_CLIENT_SECRET_ENV,),
    ("google_drive", "oauth_client_secret"),
)
OAUTH_REFRESH_TOKEN_SECRET_PATHS: tuple[tuple[str, ...], ...] = (
    (OAUTH_REFRESH_TOKEN_ENV,),
    ("google_drive", "oauth_refresh_token"),
)

_REQUIRED_SERVICE_ACCOUNT_KEYS = ("client_email", "private_key", "token_uri")
_UNSAFE_NAME_CHARS = re.compile(r"[/\\\x00-\x1f\x7f]")


class DriveError(RuntimeError):
    """Bounded Drive failure with a browser-safe message."""

    def __init__(self, message: str, *, status: int = 0) -> None:
        super().__init__(message)
        self.status = int(status or 0)


def is_unsafe_drive_name(value: Any, *, max_length: int = 200) -> bool:
    """True when a name carries a path/control/traversal risk we refuse outright."""
    raw = str(value or "")
    if not raw.strip():
        return True
    if _UNSAFE_NAME_CHARS.search(raw):
        return True
    if raw.strip() in {".", ".."}:
        return True
    return len(raw.strip()) > max_length


def sanitize_drive_name(value: Any, *, fallback: str = "tep-dinh-kem", max_length: int = 180) -> str:
    """One sanitizer for every Drive name we ever send.

    Path separators and control characters are removed (never trusted), the
    reserved ``.`` / ``..`` values are refused, and the result is bounded in
    length. Unicode letters are preserved so a Vietnamese file name survives
    intact inside the Owner's Shared Drive folder.
    """
    raw = str(value or "").strip()
    cleaned = _UNSAFE_NAME_CHARS.sub("-", raw)
    cleaned = cleaned.strip().strip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return fallback
    if len(cleaned) > max_length:
        head, _, tail = cleaned.rpartition(".")
        if head and len(tail) <= 12:
            keep = max_length - len(tail) - 1
            cleaned = f"{head[:keep]}.{tail}"
        else:
            cleaned = cleaned[:max_length]
    return cleaned or fallback


@dataclass(frozen=True)
class DriveSettings:
    """Deployment settings for one Drive root; secret values never leave server-side config."""

    root_folder_id: str = ""
    service_account: Mapping[str, Any] | None = None
    auth_mode: str = AUTH_MODE_SERVICE_ACCOUNT
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    oauth_refresh_token: str = ""

    @property
    def configured(self) -> bool:
        if not self.root_folder_id:
            return False
        if self.auth_mode == AUTH_MODE_USER_OAUTH:
            return bool(self.oauth_client_id and self.oauth_client_secret and self.oauth_refresh_token)
        return bool(self.service_account)

    @property
    def missing(self) -> list[str]:
        missing: list[str] = []
        if self.auth_mode == AUTH_MODE_USER_OAUTH:
            if not self.oauth_client_id:
                missing.append(OAUTH_CLIENT_ID_ENV)
            if not self.oauth_client_secret:
                missing.append(OAUTH_CLIENT_SECRET_ENV)
            if not self.oauth_refresh_token:
                missing.append(OAUTH_REFRESH_TOKEN_ENV)
        elif not self.service_account:
            missing.append(SERVICE_ACCOUNT_ENV)
        if not self.root_folder_id:
            missing.append(ROOT_FOLDER_ENV)
        return missing

    @property
    def client_email(self) -> str:
        """Service-account identity for Shared Drive mode; blank for user OAuth."""
        return str((self.service_account or {}).get("client_email") or "")

    def describe(self) -> dict[str, Any]:
        """Bounded, credential-free status for logs/UI capability messages."""
        return {
            "configured": self.configured,
            "missing": self.missing,
            "authMode": self.auth_mode,
            "clientEmail": self.client_email,
            "rootFolderConfigured": bool(self.root_folder_id),
        }


def _parse_service_account(raw: Any) -> Mapping[str, Any] | None:
    """Accept a JSON string OR a TOML table, and never echo the payload back."""
    payload: Any = raw
    if isinstance(raw, (str, bytes, bytearray)):
        text = raw.decode("utf-8", "ignore") if isinstance(raw, (bytes, bytearray)) else raw
        text = text.strip()
        if not text:
            return None
        try:
            payload = json.loads(text)
        except (ValueError, TypeError):
            LOGGER.warning("GOOGLE_SERVICE_ACCOUNT_JSON is present but is not valid JSON.")
            return None
    if not isinstance(payload, Mapping):
        return None
    if not all(str(payload.get(key) or "").strip() for key in _REQUIRED_SERVICE_ACCOUNT_KEYS):
        LOGGER.warning("GOOGLE_SERVICE_ACCOUNT_JSON is missing one of its required keys.")
        return None
    info = dict(payload)
    info.setdefault("type", "service_account")
    return info


def load_drive_settings(auth_mode: str = AUTH_MODE_SERVICE_ACCOUNT) -> DriveSettings:
    """Read one Drive root and only the credential family selected by the backend."""
    root = str(get_setting(ROOT_FOLDER_ENV, *ROOT_FOLDER_SECRET_PATHS) or "").strip()
    mode = str(auth_mode or AUTH_MODE_SERVICE_ACCOUNT).strip().lower()
    if mode == AUTH_MODE_USER_OAUTH:
        return DriveSettings(
            root_folder_id=root,
            auth_mode=AUTH_MODE_USER_OAUTH,
            oauth_client_id=str(get_setting(OAUTH_CLIENT_ID_ENV, *OAUTH_CLIENT_ID_SECRET_PATHS) or "").strip(),
            oauth_client_secret=str(get_setting(OAUTH_CLIENT_SECRET_ENV, *OAUTH_CLIENT_SECRET_SECRET_PATHS) or "").strip(),
            oauth_refresh_token=str(get_setting(OAUTH_REFRESH_TOKEN_ENV, *OAUTH_REFRESH_TOKEN_SECRET_PATHS) or "").strip(),
        )
    raw_account = get_raw_setting(SERVICE_ACCOUNT_ENV, *SERVICE_ACCOUNT_SECRET_PATHS)
    return DriveSettings(
        root_folder_id=root,
        service_account=_parse_service_account(raw_account),
        auth_mode=AUTH_MODE_SERVICE_ACCOUNT,
    )


def _escape_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _multipart_body(metadata: Mapping[str, Any], data: bytes, mime: str) -> tuple[bytes, str]:
    """``multipart/related`` body for ONE Drive upload (metadata + bytes)."""
    boundary = f"logi{uuid4().hex}"
    head = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(dict(metadata), ensure_ascii=False)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + data + tail, f"multipart/related; boundary={boundary}"


class GoogleDriveClient:
    """Minimal Drive REST client: folders, upload, metadata, download, delete.

    A caller may inject an already-authorized session (used by focused tests).
    Production builds exactly the credential mode selected by the storage
    backend lazily on first use, so importing this module without Drive
    configured is harmless.
    """

    def __init__(self, settings: DriveSettings, *, session: Any = None) -> None:
        self._settings = settings
        self._session = session
        self._folder_cache: dict[tuple[str, str], str] = {}

    # ------------------------------------------------------------------ auth
    @property
    def settings(self) -> DriveSettings:
        return self._settings

    def _authorized_session(self) -> Any:
        if self._session is not None:
            return self._session
        try:
            from google.auth.transport.requests import AuthorizedSession
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise DriveError("google-auth chưa được cài trên máy chủ.") from exc

        if self._settings.auth_mode == AUTH_MODE_USER_OAUTH:
            if not self._settings.configured:
                raise DriveError(
                    "Chưa cấu hình OAuth Google Drive người dùng: "
                    + ", ".join(self._settings.missing)
                    + "."
                )
            try:
                from google.oauth2.credentials import Credentials
                credentials = Credentials(
                    token=None,
                    refresh_token=self._settings.oauth_refresh_token,
                    token_uri=OAUTH_TOKEN_URI,
                    client_id=self._settings.oauth_client_id,
                    client_secret=self._settings.oauth_client_secret,
                    scopes=DRIVE_SCOPES,
                )
            except (ValueError, TypeError) as exc:
                raise DriveError("OAuth Google Drive không hợp lệ.") from exc
        else:
            if not self._settings.service_account:
                raise DriveError(f"Chưa cấu hình {SERVICE_ACCOUNT_ENV}.")
            try:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_info(
                    dict(self._settings.service_account), scopes=DRIVE_SCOPES
                )
            except (ValueError, KeyError, TypeError) as exc:
                raise DriveError("Google service account JSON không hợp lệ.") from exc

        self._session = AuthorizedSession(credentials)
        return self._session

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        session = self._authorized_session()
        try:
            response = session.request(method, url, timeout=DRIVE_TIMEOUT_SECONDS, **kwargs)
        except DriveError:
            raise
        except Exception as exc:  # noqa: BLE001 - network/proxy/credential-refresh family
            raise DriveError(f"Không gọi được Google Drive ({type(exc).__name__}).") from exc
        status = int(getattr(response, "status_code", 0) or 0)
        if status >= 400:
            # Status only: a Drive error body may quote the request, so it is
            # never surfaced to the browser or written verbatim to Mongo.
            raise DriveError(f"Google Drive từ chối yêu cầu (HTTP {status}).", status=status)
        return response

    # --------------------------------------------------------------- folders
    def find_folder(self, name: str, parent_id: str) -> str:
        query = (
            f"name = '{_escape_query_value(name)}' and "
            f"mimeType = '{DRIVE_FOLDER_MIME}' and "
            f"'{_escape_query_value(parent_id)}' in parents and trashed = false"
        )
        response = self._request(
            "GET",
            f"{DRIVE_API}/files",
            params={
                "q": query,
                "fields": "files(id,name)",
                "pageSize": 1,
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            },
        )
        files = (response.json() or {}).get("files") or []
        return str(files[0].get("id") or "") if files else ""

    def create_folder(self, name: str, parent_id: str) -> str:
        response = self._request(
            "POST",
            f"{DRIVE_API}/files",
            params={"fields": "id,name", "supportsAllDrives": "true"},
            json={"name": name, "mimeType": DRIVE_FOLDER_MIME, "parents": [parent_id]},
        )
        return str((response.json() or {}).get("id") or "")

    def ensure_folder(self, name: str, parent_id: str) -> str:
        """Find-or-create ONE folder, resolved at most once per client instance."""
        safe_name = sanitize_drive_name(name, fallback="thu-muc")
        if not parent_id:
            raise DriveError("Thiếu thư mục cha trên Google Drive.")
        key = (parent_id, safe_name)
        cached = self._folder_cache.get(key)
        if cached:
            return cached
        folder_id = self.find_folder(safe_name, parent_id)
        if not folder_id:
            folder_id = self.create_folder(safe_name, parent_id)
        if not folder_id:
            raise DriveError("Google Drive không trả về id thư mục.")
        self._folder_cache[key] = folder_id
        return folder_id

    # --------------------------------------------------------------- uploads
    def upload_file(self, *, name: str, mime: str, data: bytes, parent_id: str,
                    description: str = "") -> dict[str, Any]:
        """Upload EXACTLY the bytes handed in, returning their Drive metadata."""
        if not isinstance(data, (bytes, bytearray)) or not data:
            raise DriveError("Không có dữ liệu để tải lên Google Drive.")
        if not parent_id:
            raise DriveError("Thiếu thư mục đích trên Google Drive.")
        metadata: dict[str, Any] = {
            "name": sanitize_drive_name(name),
            "parents": [parent_id],
        }
        if description:
            metadata["description"] = description[:1000]
        body, content_type = _multipart_body(metadata, bytes(data), mime)
        response = self._request(
            "POST",
            f"{DRIVE_UPLOAD_API}/files",
            params={
                "uploadType": "multipart",
                "supportsAllDrives": "true",
                "fields": "id,name,mimeType,size,parents,webViewLink",
            },
            data=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )
        payload = response.json() or {}
        file_id = str(payload.get("id") or "")
        if not file_id:
            raise DriveError("Google Drive không trả về file id.")
        return {
            "fileId": file_id,
            "name": str(payload.get("name") or metadata["name"]),
            "mime": str(payload.get("mimeType") or mime),
            "size": int(payload.get("size") or len(data)),
            "parents": list(payload.get("parents") or [parent_id]),
            "webViewLink": str(payload.get("webViewLink") or ""),
        }

    # ------------------------------------------------------------ read/delete
    def file_metadata(self, file_id: str) -> dict[str, Any]:
        response = self._request(
            "GET",
            f"{DRIVE_API}/files/{file_id}",
            params={"fields": "id,name,mimeType,size,parents,trashed", "supportsAllDrives": "true"},
        )
        payload = response.json() or {}
        return {
            "fileId": str(payload.get("id") or ""),
            "name": str(payload.get("name") or ""),
            "mime": str(payload.get("mimeType") or ""),
            "size": int(payload.get("size") or 0),
            "trashed": bool(payload.get("trashed")),
        }

    def download_file(self, file_id: str) -> bytes:
        response = self._request(
            "GET",
            f"{DRIVE_API}/files/{file_id}",
            params={"alt": "media", "supportsAllDrives": "true"},
        )
        content = getattr(response, "content", None)
        if content is None:
            raise DriveError("Google Drive không trả về nội dung tệp.")
        return bytes(content)

    def delete_file(self, file_id: str) -> bool:
        """The ONE bounded compensating delete (used only for a just-created file)."""
        try:
            self._request(
                "DELETE",
                f"{DRIVE_API}/files/{file_id}",
                params={"supportsAllDrives": "true"},
            )
            return True
        except DriveError:
            return False


def build_drive_client(
    settings: DriveSettings | None = None,
    *,
    session: Any = None,
    auth_mode: str = AUTH_MODE_SERVICE_ACCOUNT,
) -> GoogleDriveClient | None:
    """Return a client for the explicitly selected auth mode, or None when unconfigured."""
    resolved = settings if settings is not None else load_drive_settings(auth_mode)
    if not resolved.configured:
        return None
    return GoogleDriveClient(resolved, session=session)


__all__ = [
    "DRIVE_FOLDER_MIME",
    "ROOT_FOLDER_ENV",
    "SERVICE_ACCOUNT_ENV",
    "OAUTH_CLIENT_ID_ENV",
    "OAUTH_CLIENT_SECRET_ENV",
    "OAUTH_REFRESH_TOKEN_ENV",
    "AUTH_MODE_SERVICE_ACCOUNT",
    "AUTH_MODE_USER_OAUTH",
    "DriveError",
    "DriveSettings",
    "GoogleDriveClient",
    "build_drive_client",
    "load_drive_settings",
    "sanitize_drive_name",
]
