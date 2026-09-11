// ============================================================================
// LOGI_USER_ACCESS_WORKSPACE_01 — /nguoi-dung: a READ-ONLY user & access page.
//
// The backend already assembled `userAccess` from capability this app owns:
// the user store read through the canonical password-free public view, the
// single ROLE_PERMISSIONS matrix (delivered verbatim), the real authentication
// mode (multi-user login vs Local Admin) and the current session identity.
// This page renders that truth and nothing else.
//
// Deliberately absent: create/update/deactivate actions, password reset, role
// assignment, credential display. No user-management writer is exposed from
// this page — the canonical writers stay in core.database and no UI channel
// has been proven safe to open yet. The scope box below says so on the page.
// ============================================================================

import { useMemo } from "react";
import {
  BadgeCheck,
  CircleUserRound,
  Info,
  KeyRound,
  Lock,
  ShieldCheck,
  UserCog,
  Users,
} from "lucide-react";
import { ROLE_LABEL, type Role } from "../lib/data";
import { SectionTitle, ToneBadge } from "../components/ui";
import { cx } from "../lib/format";
import { userAccessWorkspace } from "../lib/viewmodel";
import type {
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

function AccountCard({ account }: { account: UserAccessAccount }) {
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

  const { assignableSet, activeCount } = useMemo(() => {
    const assignable = new Set(data?.roles.assignable ?? []);
    const active = (data?.users ?? []).filter((account) => account.active).length;
    return { assignableSet: assignable, activeCount: active };
  }, [data]);

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

  return (
    <div className="max-w-[1240px] space-y-4 pb-3">
      {/* Header — read-only by design, and it says so. */}
      <section
        className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5"
        data-testid="user-access-header"
      >
        <SectionTitle
          icon={<Users size={20} />}
          title="Người dùng & Vai trò"
          sub="Xem tài khoản, vai trò và ma trận phân quyền đúng như hệ thống đang dùng — không thêm vai trò mới, không hiện dữ liệu bí mật."
          right={<ToneBadge tone="blue" size="sm">CHỈ ĐỌC</ToneBadge>}
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
          <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 text-emerald-800">
            <ShieldCheck size={13} /> không sửa từ trang này
          </span>
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
                <AccountCard key={account.user_id || account.username} account={account} />
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
              tắc, không thay đổi quy tắc.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
