// ============================================================================
// LOGI_USER_ACCESS_WORKSPACE_01 / LOGI_USER_MANAGEMENT_01 — /nguoi-dung.
//
// The backend assembles `userAccess` from capability this app already owns:
// the user store read through the canonical password-free public view, the
// single ROLE_PERMISSIONS matrix (delivered verbatim), the real authentication
// mode (multi-user login vs Local Admin) and the current session identity.
//
// For a NON-ADMIN session this page stays exactly what it always was: a
// read-only presentation of that truth, no forms, no buttons that imply a
// write.
//
// For an ADMIN session (`data.canManage === true`) the page additionally
// offers the bounded write path the backend now exposes:
//   CREATE ACCOUNT · CHANGE ROLE · DEACTIVATE/REACTIVATE · SET NEW PASSWORD
// via the ONE component dispatcher (`user_create` / `user_role_set` /
// `user_active_set` / `user_password_reset`). `canManage` is a DISPLAY hint
// only — the real Admin-only boundary is re-checked server-side by
// core.database on every mutation, so hiding the buttons here is never the
// security boundary. Every action:
//   - mints ONE requestId at submit and disables the button while pending;
//   - waits for the authoritative outcome in `lastWrites` matched by that
//     requestId (transport success is never treated as write success);
//   - on backend refusal keeps the editor open and shows the real message;
//   - on backend success closes the editor only once the matching outcome
//     arrives, then relies on the next fresh view-model for role/status.
// Password fields are local component state only, cleared immediately after
// a completed submit, and are NEVER read back from the server — the backend
// never returns password/password_hash, so nothing here could render it even
// by accident. There is no delete-account control anywhere on this page.
// ============================================================================

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import {
  BadgeCheck,
  CircleAlert,
  CircleUserRound,
  Info,
  KeyRound,
  Lock,
  RotateCcwKey,
  ShieldCheck,
  Unlock,
  UserCog,
  UserPlus,
  Users,
} from "lucide-react";
import { ROLE_LABEL, type Role } from "../lib/data";
import { Field, GhostBtn, PrimaryBtn, SectionTitle, ToneBadge, inputCls } from "../components/ui";
import { cx } from "../lib/format";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { useStore } from "../lib/store";
import { getViewModel, subscribeViewModel, userAccessWorkspace } from "../lib/viewmodel";
import type {
  LastWriteOutcome,
  UserAccessAccount,
  UserAccessRoleRow,
} from "../lib/viewmodel";

/** Canonical role names stay verbatim; only the display label is mapped. */
function roleLabel(role: string): string {
  const mapped = ROLE_LABEL[role.toUpperCase() as Role];
  return mapped ?? role;
}

/** Tone per canonical role — a display choice only, never a new rule. */
function roleTone(role: string): "red" | "blue" | "green" | "gray" {
  switch (role.toLowerCase()) {
    case "admin":
      return "red";
    case "support":
      return "blue";
    case "sale":
      return "green";
    default:
      return "gray";
  }
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).slice(0, 2);
  const letters = parts.map((part) => [...part][0] ?? "").join("");
  return (letters || "?").toUpperCase();
}

function newRequestId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

function PermissionChip({ name }: { name: string }) {
  return (
    <span
      className="break-all rounded-md bg-slate-100 px-2 py-1 font-mono text-[11.5px] font-semibold text-slate-700"
      data-testid="user-access-permission"
    >
      {name}
    </span>
  );
}

// ----------------------------------------------------------------------------
// CREATE ACCOUNT — username, display name, optional email, canonical role,
// password + confirmation, active=true by default. Refused duplicates are
// shown verbatim; the form stays open so the operator can pick another name.
// ----------------------------------------------------------------------------

interface CreatePending {
  requestId: string;
  username: string;
}

function CreateAccountSheet({
  assignableRoles,
  onClose,
  lastWrites,
  onSuccess,
}: {
  assignableRoles: string[];
  onClose: () => void;
  lastWrites: LastWriteOutcome[];
  onSuccess: (username: string) => void;
}) {
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState(assignableRoles[0] ?? "");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [localError, setLocalError] = useState("");
  const [backendError, setBackendError] = useState("");
  const [pending, setPending] = useState<CreatePending | null>(null);

  const submit = () => {
    if (pending) return; // one click = one request while an outcome is in flight
    const cleanUsername = username.trim();
    if (!cleanUsername) { setLocalError("Nhập tên đăng nhập."); return; }
    if (!role) { setLocalError("Chọn vai trò."); return; }
    if (!password || password.length < 8) {
      setLocalError("Mật khẩu phải có ít nhất 8 ký tự.");
      return;
    }
    if (password !== confirm) {
      setLocalError("Mật khẩu xác nhận không khớp.");
      return;
    }
    const requestId = newRequestId("USER-CREATE-REQ");
    const sent = dispatchLogiEvent("user_create", {
      username: cleanUsername,
      displayName: displayName.trim(),
      email: email.trim(),
      role,
      password,
      confirmPassword: confirm,
      active: true,
      requestId,
    });
    if (!sent) {
      setLocalError("Component chưa kết nối backend — chưa gửi được yêu cầu.");
      return;
    }
    setLocalError("");
    setBackendError("");
    setPending({ requestId, username: cleanUsername });
  };

  // Authoritative outcome only — never treat transport success as done.
  useEffect(() => {
    if (!pending) return;
    const outcome = lastWrites.find(
      (w) => w.event === "user_create" && w.requestId === pending.requestId
    );
    if (!outcome) return;
    if (outcome.ok) {
      const created = pending.username;
      setPending(null);
      // Password fields are cleared immediately and never re-rendered.
      setPassword("");
      setConfirm("");
      onSuccess(created);
    } else {
      setPending(null);
      setBackendError(outcome.error || "Backend từ chối tạo tài khoản.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastWrites, pending]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center sm:items-center"
      id="user-create-sheet"
    >
      <div className="absolute inset-0 bg-black/40" onClick={() => !pending && onClose()} />
      <div className="relative w-full max-w-[520px] rounded-t-2xl bg-white p-4 sm:rounded-2xl md:p-5">
        <p className="flex items-center gap-2 text-[16px] font-extrabold text-[#0f2a4a]">
          <UserPlus size={18} /> Thêm tài khoản
        </p>
        <div className="mt-3 space-y-3">
          <Field label="Tên đăng nhập" required>
            <input
              value={username}
              onChange={(e) => { setUsername(e.target.value); setLocalError(""); }}
              placeholder="vd: lan.sale"
              className={inputCls(username.trim() ? "ok" : "missing")}
            />
          </Field>
          <Field label="Tên hiển thị">
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="vd: Lan Sale"
              className={inputCls()}
            />
          </Field>
          <Field label="Email (không bắt buộc)">
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="vd: lan.sale@congty.vn"
              className={inputCls()}
            />
          </Field>
          <Field label="Vai trò" required>
            <select value={role} onChange={(e) => setRole(e.target.value)} className={inputCls()}>
              {assignableRoles.map((r) => (
                <option key={r} value={r}>{roleLabel(r)}</option>
              ))}
            </select>
          </Field>
          <Field label="Mật khẩu" required hint="Tối thiểu 8 ký tự.">
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setLocalError(""); }}
              className={inputCls()}
              autoComplete="new-password"
            />
          </Field>
          <Field label="Xác nhận mật khẩu" required>
            <input
              type="password"
              value={confirm}
              onChange={(e) => { setConfirm(e.target.value); setLocalError(""); }}
              className={inputCls()}
              autoComplete="new-password"
            />
          </Field>
        </div>

        {(localError || backendError) && (
          <div
            className="mt-3 flex items-start gap-2 rounded-xl border-2 border-red-200 bg-red-50 p-3 text-[13px] font-semibold text-red-700"
            role="alert"
            id="user-create-error"
          >
            <CircleAlert size={16} className="mt-0.5 shrink-0" />
            <span className="break-words">{backendError || localError}</span>
          </div>
        )}

        <div className="mt-4 flex gap-2.5">
          <PrimaryBtn onClick={submit} disabled={!!pending} className="flex-1">
            {pending ? "ĐANG TẠO…" : "TẠO TÀI KHOẢN"}
          </PrimaryBtn>
          <GhostBtn onClick={() => !pending && onClose()} className="min-w-[96px]">Hủy</GhostBtn>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// CHANGE ROLE — canonical SUPPORTED_ROLES only, no free-text role.
// ----------------------------------------------------------------------------

function RoleSheet({
  account,
  assignableRoles,
  onClose,
  lastWrites,
  onSuccess,
}: {
  account: UserAccessAccount;
  assignableRoles: string[];
  onClose: () => void;
  lastWrites: LastWriteOutcome[];
  onSuccess: () => void;
}) {
  const [role, setRole] = useState(account.role);
  const [backendError, setBackendError] = useState("");
  const [pending, setPending] = useState<string | null>(null);

  const submit = () => {
    if (pending) return;
    const requestId = newRequestId("USER-ROLE-REQ");
    const sent = dispatchLogiEvent("user_role_set", {
      username: account.username,
      role,
      requestId,
    });
    if (!sent) { setBackendError("Component chưa kết nối backend."); return; }
    setBackendError("");
    setPending(requestId);
  };

  useEffect(() => {
    if (!pending) return;
    const outcome = lastWrites.find(
      (w) => w.event === "user_role_set" && w.requestId === pending
    );
    if (!outcome) return;
    if (outcome.ok) {
      setPending(null);
      onSuccess();
    } else {
      setPending(null);
      setBackendError(outcome.error || "Backend từ chối đổi vai trò.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastWrites, pending]);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" id="user-role-sheet">
      <div className="absolute inset-0 bg-black/40" onClick={() => !pending && onClose()} />
      <div className="relative w-full max-w-[440px] rounded-t-2xl bg-white p-4 sm:rounded-2xl md:p-5">
        <p className="flex items-center gap-2 text-[16px] font-extrabold text-[#0f2a4a]">
          <UserCog size={18} /> Đổi vai trò — {account.display_name || account.username}
        </p>
        <p className="mt-1 break-all font-mono text-[12px] text-slate-500">{account.username}</p>
        <div className="mt-3">
          <Field label="Vai trò mới" required>
            <select value={role} onChange={(e) => setRole(e.target.value)} className={inputCls()}>
              {assignableRoles.map((r) => (
                <option key={r} value={r}>{roleLabel(r)}</option>
              ))}
            </select>
          </Field>
        </div>
        {backendError && (
          <div
            className="mt-3 flex items-start gap-2 rounded-xl border-2 border-red-200 bg-red-50 p-3 text-[13px] font-semibold text-red-700"
            role="alert"
            id="user-role-error"
          >
            <CircleAlert size={16} className="mt-0.5 shrink-0" />
            <span className="break-words">{backendError}</span>
          </div>
        )}
        <div className="mt-4 flex gap-2.5">
          <PrimaryBtn onClick={submit} disabled={!!pending} className="flex-1">
            {pending ? "ĐANG LƯU…" : "LƯU VAI TRÒ"}
          </PrimaryBtn>
          <GhostBtn onClick={() => !pending && onClose()} className="min-w-[96px]">Hủy</GhostBtn>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// DEACTIVATE / REACTIVATE — a single confirm step; no delete anywhere.
// ----------------------------------------------------------------------------

function ActiveSheet({
  account,
  onClose,
  lastWrites,
  onSuccess,
}: {
  account: UserAccessAccount;
  onClose: () => void;
  lastWrites: LastWriteOutcome[];
  onSuccess: () => void;
}) {
  const targetActive = !account.active;
  const [backendError, setBackendError] = useState("");
  const [pending, setPending] = useState<string | null>(null);

  const submit = () => {
    if (pending) return;
    const requestId = newRequestId("USER-ACTIVE-REQ");
    const sent = dispatchLogiEvent("user_active_set", {
      username: account.username,
      active: targetActive,
      requestId,
    });
    if (!sent) { setBackendError("Component chưa kết nối backend."); return; }
    setBackendError("");
    setPending(requestId);
  };

  useEffect(() => {
    if (!pending) return;
    const outcome = lastWrites.find(
      (w) => w.event === "user_active_set" && w.requestId === pending
    );
    if (!outcome) return;
    if (outcome.ok) {
      setPending(null);
      onSuccess();
    } else {
      setPending(null);
      setBackendError(outcome.error || "Backend từ chối cập nhật trạng thái.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastWrites, pending]);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" id="user-active-sheet">
      <div className="absolute inset-0 bg-black/40" onClick={() => !pending && onClose()} />
      <div className="relative w-full max-w-[440px] rounded-t-2xl bg-white p-4 sm:rounded-2xl md:p-5">
        <p className="flex items-center gap-2 text-[16px] font-extrabold text-[#0f2a4a]">
          {targetActive ? <Unlock size={18} /> : <Lock size={18} />}
          {" "}
          {targetActive ? "Kích hoạt lại" : "Vô hiệu hóa"} — {account.display_name || account.username}
        </p>
        <p className="mt-2 text-[13.5px] leading-relaxed text-slate-600">
          {targetActive
            ? "Tài khoản sẽ đăng nhập được trở lại ngay sau khi máy chủ xác nhận."
            : "Tài khoản sẽ không đăng nhập được nữa. Lịch sử tài khoản vẫn được giữ nguyên — đây không phải xóa tài khoản."}
        </p>
        {backendError && (
          <div
            className="mt-3 flex items-start gap-2 rounded-xl border-2 border-red-200 bg-red-50 p-3 text-[13px] font-semibold text-red-700"
            role="alert"
            id="user-active-error"
          >
            <CircleAlert size={16} className="mt-0.5 shrink-0" />
            <span className="break-words">{backendError}</span>
          </div>
        )}
        <div className="mt-4 flex gap-2.5">
          <PrimaryBtn onClick={submit} disabled={!!pending} className="flex-1">
            {pending ? "ĐANG LƯU…" : targetActive ? "KÍCH HOẠT LẠI" : "VÔ HIỆU HÓA"}
          </PrimaryBtn>
          <GhostBtn onClick={() => !pending && onClose()} className="min-w-[96px]">Hủy</GhostBtn>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// SET NEW PASSWORD — Admin enters it directly; no email reset/invite flow.
// ----------------------------------------------------------------------------

function PasswordSheet({
  account,
  onClose,
  lastWrites,
  onSuccess,
}: {
  account: UserAccessAccount;
  onClose: () => void;
  lastWrites: LastWriteOutcome[];
  onSuccess: () => void;
}) {
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [localError, setLocalError] = useState("");
  const [backendError, setBackendError] = useState("");
  const [pending, setPending] = useState<string | null>(null);

  const submit = () => {
    if (pending) return;
    if (!newPassword || newPassword.length < 8) {
      setLocalError("Mật khẩu mới phải có ít nhất 8 ký tự.");
      return;
    }
    if (newPassword !== confirm) {
      setLocalError("Mật khẩu xác nhận không khớp.");
      return;
    }
    const requestId = newRequestId("USER-PWD-REQ");
    const sent = dispatchLogiEvent("user_password_reset", {
      username: account.username,
      newPassword,
      confirmPassword: confirm,
      requestId,
    });
    if (!sent) { setLocalError("Component chưa kết nối backend."); return; }
    setLocalError("");
    setBackendError("");
    setPending(requestId);
  };

  useEffect(() => {
    if (!pending) return;
    const outcome = lastWrites.find(
      (w) => w.event === "user_password_reset" && w.requestId === pending
    );
    if (!outcome) return;
    if (outcome.ok) {
      setPending(null);
      // Never keep the password value around once the write is confirmed.
      setNewPassword("");
      setConfirm("");
      onSuccess();
    } else {
      setPending(null);
      setBackendError(outcome.error || "Backend từ chối đặt lại mật khẩu.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastWrites, pending]);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" id="user-password-sheet">
      <div className="absolute inset-0 bg-black/40" onClick={() => !pending && onClose()} />
      <div className="relative w-full max-w-[440px] rounded-t-2xl bg-white p-4 sm:rounded-2xl md:p-5">
        <p className="flex items-center gap-2 text-[16px] font-extrabold text-[#0f2a4a]">
          <RotateCcwKey size={18} /> Đặt mật khẩu mới — {account.display_name || account.username}
        </p>
        <p className="mt-1 text-[12.5px] leading-relaxed text-slate-500">
          Đặt trực tiếp mật khẩu mới cho tài khoản này (không gửi email, không
          tạo đường dẫn đặt lại).
        </p>
        <div className="mt-3 space-y-3">
          <Field label="Mật khẩu mới" required hint="Tối thiểu 8 ký tự.">
            <input
              type="password"
              value={newPassword}
              onChange={(e) => { setNewPassword(e.target.value); setLocalError(""); }}
              className={inputCls()}
              autoComplete="new-password"
            />
          </Field>
          <Field label="Xác nhận mật khẩu mới" required>
            <input
              type="password"
              value={confirm}
              onChange={(e) => { setConfirm(e.target.value); setLocalError(""); }}
              className={inputCls()}
              autoComplete="new-password"
            />
          </Field>
        </div>
        {(localError || backendError) && (
          <div
            className="mt-3 flex items-start gap-2 rounded-xl border-2 border-red-200 bg-red-50 p-3 text-[13px] font-semibold text-red-700"
            role="alert"
            id="user-password-error"
          >
            <CircleAlert size={16} className="mt-0.5 shrink-0" />
            <span className="break-words">{backendError || localError}</span>
          </div>
        )}
        <div className="mt-4 flex gap-2.5">
          <PrimaryBtn onClick={submit} disabled={!!pending} className="flex-1">
            {pending ? "ĐANG LƯU…" : "ĐẶT MẬT KHẨU MỚI"}
          </PrimaryBtn>
          <GhostBtn onClick={() => !pending && onClose()} className="min-w-[96px]">Hủy</GhostBtn>
        </div>
      </div>
    </div>
  );
}

function AccountCard({
  account,
  canManage,
  onManageRole,
  onManageActive,
  onManagePassword,
}: {
  account: UserAccessAccount;
  canManage: boolean;
  onManageRole: () => void;
  onManageActive: () => void;
  onManagePassword: () => void;
}) {
  const name = account.display_name || account.username;
  return (
    <div
      data-testid="user-access-account"
      data-username={account.username}
      data-role={account.role}
      className="w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-3.5"
    >
      <div className="flex items-start gap-3">
        <span
          className={cx(
            "grid h-10 w-10 shrink-0 place-items-center rounded-xl text-[14px] font-extrabold",
            account.active
              ? "bg-blue-100 text-blue-800"
              : "bg-slate-100 text-slate-400"
          )}
          aria-hidden
        >
          {initials(name)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <p className="min-w-0 break-words text-[15px] font-extrabold text-[#0f2a4a]">
              {name}
            </p>
            <ToneBadge tone={roleTone(account.role)} size="sm">
              {roleLabel(account.role)}
            </ToneBadge>
            {account.active ? (
              <span
                className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[11.5px] font-bold text-emerald-800"
                data-testid="user-access-account-active"
              >
                <BadgeCheck size={12} /> Hoạt động
              </span>
            ) : (
              <span
                className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-[11.5px] font-bold text-slate-500"
                data-testid="user-access-account-inactive"
              >
                <Lock size={12} /> Đã vô hiệu hóa
              </span>
            )}
          </div>
          <p className="mt-1 break-all font-mono text-[12px] text-slate-500">
            {account.username}
          </p>
          {account.email ? (
            <p className="mt-0.5 min-w-0 break-all text-[12.5px] text-slate-500">
              {account.email}
            </p>
          ) : null}
          {account.user_id ? (
            <p className="mt-1 break-all font-mono text-[11px] text-slate-400">
              ID: {account.user_id}
            </p>
          ) : null}

          {canManage && (
            <div className="mt-2.5 flex flex-wrap gap-2" data-testid="user-access-account-actions">
              <GhostBtn onClick={onManageRole} className="min-h-[36px] px-3 text-[13px]">
                <UserCog size={14} /> Đổi vai trò
              </GhostBtn>
              <GhostBtn onClick={onManageActive} className="min-h-[36px] px-3 text-[13px]" danger={account.active}>
                {account.active ? <Lock size={14} /> : <Unlock size={14} />}
                {account.active ? "Vô hiệu hóa" : "Kích hoạt lại"}
              </GhostBtn>
              <GhostBtn onClick={onManagePassword} className="min-h-[36px] px-3 text-[13px]">
                <RotateCcwKey size={14} /> Đặt mật khẩu mới
              </GhostBtn>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function RoleMatrixRow({ row, assignable }: { row: UserAccessRoleRow; assignable: boolean }) {
  return (
    <div
      data-testid="user-access-role-row"
      data-role={row.role}
      className="w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-3.5"
    >
      <div className="flex flex-wrap items-center gap-2">
        <ToneBadge tone={roleTone(row.role)} size="sm">
          {roleLabel(row.role)}
        </ToneBadge>
        {row.wildcard ? (
          <span className="inline-flex items-center gap-1 rounded-md bg-violet-50 px-2 py-0.5 text-[11.5px] font-bold text-violet-800">
            <KeyRound size={12} /> * = toàn quyền
          </span>
        ) : null}
        {assignable ? (
          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-500">
            vai trò gán được
          </span>
        ) : (
          <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-700">
            vai trò tương thích cũ
          </span>
        )}
        <span className="ml-auto text-[11.5px] font-bold text-slate-400">
          {row.permissionCount} quyền
        </span>
      </div>
      {/* Permission chips wrap instead of forcing a wide table — the matrix
          stays readable at phone width without any horizontal scrolling. */}
      <div
        className="mt-2 flex flex-wrap gap-1.5"
        data-testid="user-access-role-permissions"
      >
        {row.wildcard ? (
          <span className="break-words text-[12.5px] leading-relaxed text-slate-500">
            Toàn quyền trên mọi thao tác của hệ thống (dấu * trong ma trận
            nguyên bản của core.auth).
          </span>
        ) : (
          row.permissions.map((permission) => (
            <PermissionChip key={permission} name={permission} />
          ))
        )}
      </div>
    </div>
  );
}

function EmptyUsers() {
  return (
    <div
      data-testid="user-access-empty"
      className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600"
    >
      Nguồn tài khoản của bản dựng này chưa có người dùng nào (hoặc chưa cấu
      hình). Trang hiển thị đúng trạng thái trống và không tự bịa tài khoản,
      vai trò hay quyền nào thay thế.
    </div>
  );
}

export default function UserAccess() {
  const data = userAccessWorkspace();
  const { toast } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  // Authoritative outcomes of user_create/user_role_set/user_active_set/
  // user_password_reset arrive on the SAME `lastWrites` channel every other
  // write path uses — filtered here so each sheet only ever sees its own
  // event family.
  const userWrites = useMemo<LastWriteOutcome[]>(
    () => (vm?.lastWrites ?? []).filter((w) =>
      w.event === "user_create" || w.event === "user_role_set"
      || w.event === "user_active_set" || w.event === "user_password_reset"
    ),
    [vm]
  );

  const { assignableSet, activeCount } = useMemo(() => {
    const assignable = new Set(data?.roles.assignable ?? []);
    const active = (data?.users ?? []).filter((account) => account.active).length;
    return { assignableSet: assignable, activeCount: active };
  }, [data]);

  const [createOpen, setCreateOpen] = useState(false);
  const [roleTarget, setRoleTarget] = useState<UserAccessAccount | null>(null);
  const [activeTarget, setActiveTarget] = useState<UserAccessAccount | null>(null);
  const [passwordTarget, setPasswordTarget] = useState<UserAccessAccount | null>(null);

  if (!data) {
    return (
      <div className="max-w-[1240px] pb-3">
        <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] text-slate-600">
          Chưa có dữ liệu người dùng & phân quyền từ máy chủ. Trang chỉ đọc và
          không tự tạo dữ liệu thay thế.
        </div>
      </div>
    );
  }

  const canManage = data.canManage === true;
  const assignableRoles = data.roles.assignable;
  const writes = userWrites;

  return (
    <div className="max-w-[1240px] space-y-4 pb-3">
      {/* Header — read-only badge only when the session cannot manage accounts. */}
      <section
        className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5"
        data-testid="user-access-header"
      >
        <SectionTitle
          icon={<Users size={20} />}
          title="Người dùng & Vai trò"
          sub={
            canManage
              ? "Quản lý tài khoản, vai trò và trạng thái hoạt động — đúng vai trò gán được của hệ thống, không thêm vai trò mới, không hiện dữ liệu bí mật."
              : "Xem tài khoản, vai trò và ma trận phân quyền đúng như hệ thống đang dùng — không thêm vai trò mới, không hiện dữ liệu bí mật."
          }
          right={
            canManage ? (
              <PrimaryBtn onClick={() => setCreateOpen(true)} className="min-h-[40px] px-4 text-[13.5px]">
                <UserPlus size={16} /> + THÊM TÀI KHOẢN
              </PrimaryBtn>
            ) : (
              <ToneBadge tone="blue" size="sm">CHỈ ĐỌC</ToneBadge>
            )
          }
        />
        <div className="mt-3 flex flex-wrap items-center gap-2 text-[12.5px] font-semibold text-slate-600">
          <span className="rounded-lg bg-slate-100 px-2 py-1" data-testid="user-access-authmode">
            {data.authMode.label}
          </span>
          <span className="rounded-lg bg-slate-100 px-2 py-1" data-testid="user-access-counts">
            {data.counts.userShown === data.counts.userCount
              ? `${data.counts.userCount} tài khoản`
              : `${data.counts.userShown}/${data.counts.userCount} tài khoản (giới hạn hiển thị)`}
          </span>
          <span className="rounded-lg bg-slate-100 px-2 py-1">
            {activeCount} hoạt động · {data.counts.inactiveCount} vô hiệu hóa
          </span>
          <span className="rounded-lg bg-slate-100 px-2 py-1">
            {data.counts.roleCount} vai trò trong ma trận
          </span>
          {!canManage && (
            <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 text-emerald-800">
              <ShieldCheck size={13} /> không sửa từ trang này
            </span>
          )}
        </div>

        {/* Auth-mode honesty: Local Admin is never dressed up as multi-user. */}
        <p
          data-testid="user-access-mode-note"
          className={cx(
            "mt-3 rounded-xl px-3 py-2.5 text-[13px] leading-relaxed",
            data.authMode.required
              ? "border border-blue-200 bg-blue-50 text-blue-900"
              : "border border-amber-200 bg-amber-50 text-amber-900"
          )}
        >
          <b>Chế độ xác thực: {data.authMode.label}.</b> {data.authMode.note}
        </p>

        {/* Current-user indicator — the identity the header already shows. */}
        <div
          data-testid="user-access-current"
          className="mt-3 flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5"
        >
          <CircleUserRound size={22} className="shrink-0 text-[#1e5aa8]" />
          <div className="min-w-0">
            <p className="text-[12px] font-extrabold uppercase tracking-wide text-slate-500">
              Bạn đang đăng nhập
            </p>
            {data.currentUser.present ? (
              <p className="min-w-0 break-words text-[14px] font-extrabold text-[#0f2a4a]">
                {data.currentUser.displayName}{" "}
                <span className="font-mono text-[12px] font-semibold text-slate-500">
                  ({data.currentUser.username})
                </span>{" "}
                · {roleLabel(data.currentUser.role)}
                {data.currentUser.wildcard ? " · toàn quyền (*)" : ` · ${data.currentUser.permissions.length} quyền`}
              </p>
            ) : (
              <p className="text-[14px] font-bold text-slate-500">
                Chưa xác định phiên đăng nhập
              </p>
            )}
          </div>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        {/* Main rail: accounts, then the canonical permission matrix. */}
        <div className="min-w-0 space-y-4">
          <section className="space-y-2.5" data-testid="user-access-accounts">
            <SectionTitle
              icon={<UserCog size={18} />}
              title="Tài khoản"
              sub="Trường công khai chuẩn của tài khoản (tên hiển thị, tài khoản đăng nhập, vai trò, trạng thái). Không có mật khẩu hay hash."
            />
            {data.users.length === 0 ? (
              <EmptyUsers />
            ) : (
              data.users.map((account) => (
                <AccountCard
                  key={account.user_id || account.username}
                  account={account}
                  canManage={canManage}
                  onManageRole={() => setRoleTarget(account)}
                  onManageActive={() => setActiveTarget(account)}
                  onManagePassword={() => setPasswordTarget(account)}
                />
              ))
            )}
          </section>

          <section className="space-y-2.5" data-testid="user-access-matrix">
            <SectionTitle
              icon={<KeyRound size={18} />}
              title="Ma trận phân quyền"
              sub="Nguyên văn ROLE_PERMISSIONS của core.auth — nguồn quyền duy nhất của ứng dụng. Tên quyền giữ nguyên bản, không dịch, không thêm."
            />
            {data.permissionMatrix.map((row) => (
              <RoleMatrixRow
                key={row.role}
                row={row}
                assignable={assignableSet.has(row.role)}
              />
            ))}
            <p className="break-words text-[12px] leading-relaxed text-slate-400">
              Nguồn: {data.roles.source}. Vai trò gán được cho tài khoản:{" "}
              {data.roles.assignable.map((role) => roleLabel(role)).join(", ")}.
              {data.roles.legacy.length > 0
                ? ` Các vai trò còn lại (${data.roles.legacy.map((role) => roleLabel(role)).join(", ")}) chỉ còn trong ma trận để tương thích dữ liệu cũ.`
                : ""}
            </p>
          </section>
        </div>

        {/* Side rail: honest scope of this page. */}
        <aside className="min-w-0 space-y-3">
          <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5">
            <p className="flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500">
              <Info size={14} /> Trang này không có
            </p>
            <ul
              className="mt-1 space-y-1 text-[12.5px] leading-relaxed text-slate-600"
              data-testid="user-access-unavailable"
            >
              {data.unavailable.map((line) => (
                <li key={line} className="break-words">
                  {line}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5">
            <p className="flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500">
              <ShieldCheck size={14} /> Quyền của bạn được kiểm ở đâu
            </p>
            <p className="mt-1 text-[12.5px] leading-relaxed text-slate-600">
              Mọi thao tác ghi trong ứng dụng vẫn được kiểm tra bởi
              <span className="font-mono text-[11.5px] font-semibold"> core.auth </span>
              trên máy chủ theo đúng ma trận trên. Trang này chỉ hiển thị quy
              tắc, không tự nới quyền.
            </p>
          </div>
        </aside>
      </div>

      {canManage && createOpen && (
        <CreateAccountSheet
          assignableRoles={assignableRoles}
          onClose={() => setCreateOpen(false)}
          lastWrites={writes}
          onSuccess={(username) => {
            setCreateOpen(false);
            toast("Đã tạo tài khoản " + username, "Ghi qua core.database.save_user, có audit.", "green");
          }}
        />
      )}
      {canManage && roleTarget && (
        <RoleSheet
          account={roleTarget}
          assignableRoles={assignableRoles}
          onClose={() => setRoleTarget(null)}
          lastWrites={writes}
          onSuccess={() => {
            const name = roleTarget.display_name || roleTarget.username;
            setRoleTarget(null);
            toast("Đã đổi vai trò " + name, "Vai trò mới có hiệu lực từ dữ liệu mới nhất.", "green");
          }}
        />
      )}
      {canManage && activeTarget && (
        <ActiveSheet
          account={activeTarget}
          onClose={() => setActiveTarget(null)}
          lastWrites={writes}
          onSuccess={() => {
            const name = activeTarget.display_name || activeTarget.username;
            const nowActive = !activeTarget.active;
            setActiveTarget(null);
            toast(
              (nowActive ? "Đã kích hoạt lại " : "Đã vô hiệu hóa ") + name,
              "Trạng thái mới có hiệu lực từ dữ liệu mới nhất.",
              "green"
            );
          }}
        />
      )}
      {canManage && passwordTarget && (
        <PasswordSheet
          account={passwordTarget}
          onClose={() => setPasswordTarget(null)}
          lastWrites={writes}
          onSuccess={() => {
            const name = passwordTarget.display_name || passwordTarget.username;
            setPasswordTarget(null);
            toast("Đã đặt mật khẩu mới cho " + name, "Mật khẩu cũ không còn dùng được.", "green");
          }}
        />
      )}
    </div>
  );
}
