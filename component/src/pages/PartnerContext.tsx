// ============================================================================
// LOGI_PARTNER_CONTEXT_WORKSPACE_01 — /ngu-canh-doi-tac ("Đại Lý Trường Thành").
//
// LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01: the visible workspace is now
// the AGENT MASTER MANAGEMENT desk of Trường Thành — CREATE / EDIT of the
// existing canonical authority_agents master through ONE bounded typed event
// (authority_agent_save → sales_write RBAC → the EXISTING writer
// core.database.save_authority_agent → audit → fresh readback). The linked
// shipment / document / payable context underneath stays exactly what it was:
// a READ-ONLY projection over capabilities that already exist:
//
//   identity/contact  → authority_agents legal master (via views.logi_c1's own
//                       party projection, so one master never renders two ways)
//   operational       → core.entity_context partner/agent shipment index
//   finance           → the C2D canonical payable rows (same ledger truth as
//                       /tai-chinh/cong-no-doi-tac) — re-used, never recomputed
//
// Deliberately NOT a CRM: no relationship/risk/credit score, no partner tier,
// no account manager, no SLA, no notes, no activity timeline, no tags — because
// no backend source for those exists. The "context không khả dụng" panel states
// that plainly instead of leaving an empty tab.
//
// Every selection goes through the ONE bounded typed `partner_context_select`
// event: this page never computes or caches business truth locally. The result
// always arrives from the next fresh view-model read, so the screen shows what
// the backend knows — including "unknown".
//
// Mobile: search + picker + stacked cards, >= 48px targets, no table below
// `md` (linked shipments render as cards), and the Open-Shipment action stays
// reachable without horizontal scroll.
// ============================================================================

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, Building2, CircleAlert, Eye, Handshake, Info, Lock,
  PencilLine, Phone, Plus, Save, Search, ShieldQuestion, Wallet,
} from "lucide-react";
import { Field, SectionTitle, ToneBadge, inputCls } from "../components/ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { cx, fmtCcy, fmtText, isUnknown, UNKNOWN } from "../lib/format";
import { useStore } from "../lib/store";
import { shipmentPath } from "../lib/shipmentRoute";
import {
  getViewModel,
  subscribeViewModel,
  type PartnerContextOption,
  type PartnerContextShipmentRow,
} from "../lib/viewmodel";

// ----------------------------------------------------------------------------
// LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — agent master form contract.
// EXACTLY the fields the existing canonical authority_agents master projects
// (views.logi_c1._party_view ↔ core.database.save_authority_agent): nothing is
// invented here — no tax/credit/SLA/risk/rating field exists, so none is shown.
// ----------------------------------------------------------------------------

type AgentFormValues = {
  agentId: string;
  legalName: string;
  legalCode: string;
  legalAddress: string;
  legalRepresentative: string;
  representativeTitle: string;
  phone: string;
  email: string;
  bankAccountHolder: string;
  bankAccountNumber: string;
  bankName: string;
  bankBranch: string;
};

const EMPTY_AGENT_FORM: AgentFormValues = {
  agentId: "", legalName: "", legalCode: "", legalAddress: "",
  legalRepresentative: "", representativeTitle: "", phone: "", email: "",
  bankAccountHolder: "", bankAccountNumber: "", bankName: "", bankBranch: "",
};

const AGENT_FIELDS: { key: keyof AgentFormValues; label: string; required?: boolean; lockedOnEdit?: boolean; wide?: boolean; mono?: boolean }[] = [
  { key: "agentId", label: "Mã đại lý", required: true, lockedOnEdit: true, mono: true },
  { key: "legalName", label: "Tên pháp lý", required: true, wide: true },
  { key: "legalCode", label: "Mã số / mã pháp lý", mono: true },
  { key: "legalAddress", label: "Địa chỉ", wide: true },
  { key: "legalRepresentative", label: "Người đại diện" },
  { key: "representativeTitle", label: "Chức vụ" },
  { key: "phone", label: "Điện thoại", mono: true },
  { key: "email", label: "Email" },
  { key: "bankAccountHolder", label: "Chủ tài khoản" },
  { key: "bankAccountNumber", label: "Số tài khoản", mono: true },
  { key: "bankName", label: "Ngân hàng" },
  { key: "bankBranch", label: "Chi nhánh ngân hàng" },
];

const STATUS_TONE: Record<string, "green" | "amber" | "red" | "blue" | "gray"> = {
  CONFIRMED: "blue",
  REVIEW_REQUIRED: "amber",
  KNOWN: "green",
  UNKNOWN: "gray",
};

const toneFor = (status: string | null | undefined) =>
  STATUS_TONE[(status ?? "").toUpperCase()] ?? "gray";

/** One label/value pair; UNKNOWN renders as the shared em dash, never "". */
function InfoCell({ label, value, mono }: { label: string; value: string | null | undefined; mono?: boolean }) {
  return (
    <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
      <p className="text-[12px] font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={cx("mt-0.5 font-semibold text-[14.5px] break-words", mono && "font-mono")}>{fmtText(value)}</p>
    </div>
  );
}

function MoneyCell({ label, value, ccy, strong }: { label: string; value: number | null; ccy: string | null; strong?: boolean }) {
  return (
    <div className={cx("rounded-xl border p-2.5 text-center", strong ? "bg-amber-50 border-amber-200" : "bg-white border-slate-200")}>
      <p className={cx("text-[12px] font-semibold", strong ? "text-amber-700" : "text-slate-500")}>{label}</p>
      {/* isUnknown keeps a genuine 0 visible as 0 while null stays "—" */}
      <p className={cx("font-extrabold text-[14px]", strong ? "text-amber-800" : "text-[#0f2a4a]")}>
        {isUnknown(value) ? `${UNKNOWN} ${ccy ?? ""}`.trim() : fmtCcy(value, ccy)}
      </p>
    </div>
  );
}

/** Linked shipment: authoritative id + real open action, no duplicated detail. */
function ShipmentRow({ row }: { row: PartnerContextShipmentRow }) {
  const meta = [
    row.role ? `Vai trò: ${row.role}` : null,
    row.route ? `Tuyến: ${row.route}` : null,
    row.requiredDate ? `Khách cần giao: ${row.requiredDate}` : null,
    row.plannedDate ? `Kế hoạch: ${row.plannedDate}` : null,
    row.status ? `Trạng thái: ${row.status}` : null,
  ].filter(Boolean) as string[];

  return (
    <div className="rounded-2xl bg-white border border-slate-200 p-4">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-extrabold text-[16.5px] text-[#0f2a4a] break-all">{row.shipmentId}</span>
        {row.status ? (
          <ToneBadge tone="blue" size="sm">{row.status}</ToneBadge>
        ) : (
          <ToneBadge tone="gray" size="sm">trạng thái {UNKNOWN}</ToneBadge>
        )}
        {row.financeCurrencies.map((ccy) => (
          <span key={ccy} className="rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold">{ccy}</span>
        ))}
        <span className="ml-auto shrink-0">{row.canOpen
          ? <ToneBadge tone="green" size="sm">mở được</ToneBadge>
          : <ToneBadge tone="amber" size="sm">không mở được</ToneBadge>}</span>
      </div>
      <p className="text-[13.5px] text-slate-600 mt-1.5 leading-relaxed">{meta.length ? meta.join(" · ") : `Bối cảnh lô đang ${UNKNOWN}`}</p>
      {row.attention ? (
        <p className="text-[13.5px] mt-1.5 inline-flex items-start gap-1.5 rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1.5 text-amber-800">
          <CircleAlert size={15} className="shrink-0 mt-0.5" />
          <span>{row.attention}{row.attentionDetail ? ` — ${row.attentionDetail}` : ""}</span>
        </p>
      ) : null}
      <div className="flex flex-wrap items-center gap-2 mt-3">
        {row.canOpen ? (
          <Link
            to={row.openHref}
            className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[13.5px] px-4 min-h-[48px]"
          >
            <Eye size={16} /> Mở lô
          </Link>
        ) : (
          <span className="touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-slate-400 font-bold text-[13.5px] px-4 min-h-[48px]">
            <Lock size={15} /> Lô không có trong dữ liệu hiện tại
          </span>
        )}
        <span className="text-[12px] text-slate-400 break-words">nguồn: {fmtText(row.source)}</span>
      </div>
    </div>
  );
}

export default function PartnerContext() {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const slice = vm?.partnerContext ?? null;
  const { toast } = useStore();
  const [query, setQuery] = useState("");
  const [pendingKey, setPendingKey] = useState<string | null>(null);

  // --------------------------------------------------------------------------
  // Agent master CREATE / EDIT form. Local inputs only — persistence happens
  // EXCLUSIVELY through the ONE bounded `authority_agent_save` event and is
  // confirmed by its authoritative readback in `lastWrites` (never optimistically).
  // --------------------------------------------------------------------------
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [formValues, setFormValues] = useState<AgentFormValues>({ ...EMPTY_AGENT_FORM });
  const [savePending, setSavePending] = useState<{ requestId: string; agentId: string; mode: "create" | "edit" } | null>(null);
  const [saveError, setSaveError] = useState("");

  const openCreateForm = () => {
    setFormMode("create");
    setFormValues({ ...EMPTY_AGENT_FORM });
    setSaveError("");
    setFormOpen(true);
  };

  const openEditForm = () => {
    const current = slice?.identity?.party ?? null;
    if (!current) return;
    setFormMode("edit");
    setFormValues({
      agentId: current.id ?? "",
      legalName: current.legalName ?? "",
      legalCode: current.legalCode ?? "",
      legalAddress: current.legalAddress ?? "",
      legalRepresentative: current.representative ?? "",
      representativeTitle: current.representativeTitle ?? "",
      phone: current.phone ?? "",
      email: current.email ?? "",
      bankAccountHolder: current.bankAccountHolder ?? "",
      bankAccountNumber: current.bankAccountNumber ?? "",
      bankName: current.bankName ?? "",
      bankBranch: current.bankBranch ?? "",
    });
    setSaveError("");
    setFormOpen(true);
  };

  const setField = (key: keyof AgentFormValues, value: string) =>
    setFormValues((v) => ({ ...v, [key]: value }));

  const submitAgentForm = () => {
    if (savePending) return; // one click = one request; backend seq stays intact
    const agentId = formValues.agentId.trim().toUpperCase();
    const legalName = formValues.legalName.trim();
    if (!agentId) { setSaveError("Mã đại lý là bắt buộc."); return; }
    if (!legalName) { setSaveError("Tên pháp lý là bắt buộc — hồ sơ đại lý không tên không dùng được."); return; }
    const requestId = `agent-save-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const sent = dispatchLogiEvent("authority_agent_save", {
      agentId,
      requestId,
      legalName,
      legalCode: formValues.legalCode.trim(),
      legalAddress: formValues.legalAddress.trim(),
      legalRepresentative: formValues.legalRepresentative.trim(),
      representativeTitle: formValues.representativeTitle.trim(),
      phone: formValues.phone.trim(),
      email: formValues.email.trim(),
      bankAccountHolder: formValues.bankAccountHolder.trim(),
      bankAccountNumber: formValues.bankAccountNumber.trim(),
      bankName: formValues.bankName.trim(),
      bankBranch: formValues.bankBranch.trim(),
    });
    if (!sent) {
      setSaveError("Component chưa kết nối backend.");
      return;
    }
    setSaveError("");
    setSavePending({ requestId, agentId, mode: formMode });
  };

  // Consume the AUTHORITATIVE backend outcome once the fresh view-model carries
  // it. Success closes the form (the saved master arrives via the normal
  // readers); failure keeps the form open with the real backend error.
  useEffect(() => {
    if (!savePending || !vm) return;
    const outcome = (vm.lastWrites ?? []).find(
      (w) => w.event === "authority_agent_save" && w.requestId === savePending.requestId
    );
    if (!outcome) return;
    if (outcome.ok) {
      setSavePending(null);
      setFormOpen(false);
      toast("Đã lưu hồ sơ đại lý " + savePending.agentId,
        "Ghi qua writer canonical authority_agents, có audit.", "green");
      if (savePending.mode === "create") {
        // Open the saved master's context immediately (the same bounded
        // READ-ONLY selection event the picker uses — nothing new).
        setPendingKey(savePending.agentId);
        dispatchLogiEvent("partner_context_select", { entityKey: savePending.agentId });
      }
    } else {
      setSavePending(null);
      setSaveError(outcome.error || "Backend từ chối lưu hồ sơ đại lý.");
    }
  }, [vm, savePending, toast]);

  const options = slice?.options ?? [];
  const selectedKey = slice?.selectedKey ?? null;

  // Client-side filter over the terms the backend genuinely matches on. No new
  // index, no fuzzy/vector/AI search: substring on id / name / phone / email.
  const list = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return options;
    return options.filter((o: PartnerContextOption) =>
      [o.key, o.label, o.legalCode, o.phone, o.email]
        .some((value) => (value ?? "").toLowerCase().includes(needle)));
  }, [options, query]);

  // The readback is authoritative: the picker shows a bounded pending state only
  // between the intent and the fresh view-model that answers it.
  const pending = pendingKey !== null && pendingKey !== selectedKey;
  const showContext = Boolean(selectedKey) && !pending;

  /** ONE bounded read-only event; the page never renders a locally-computed context. */
  const select = (key: string) => {
    setPendingKey(key);
    dispatchLogiEvent("partner_context_select", { entityKey: key });
  };

  const clear = () => {
    setPendingKey(null);
    dispatchLogiEvent("partner_context_select", { entityKey: "" });
  };

  const identity = slice?.identity ?? null;
  const party = identity?.party ?? null;
  const finance = slice?.finance ?? null;
  const rows = finance?.rows ?? [];
  const linked = slice?.shipments ?? [];
  const documents = slice?.documents ?? [];
  /** Only ids the existing /lo-hang/:id route can genuinely serve are linkable. */
  const openable = useMemo(
    () => new Set(linked.filter((r) => r.canOpen).map((r) => r.shipmentId.toLowerCase())),
    [linked]
  );
  const gaps = slice?.gaps ?? [];
  const unavailable = slice?.unavailable ?? [];

  return (
    <div className="space-y-4 max-w-[1300px]">
      {/* HEADER + picker */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Handshake size={20} className="text-[#1e5aa8]" />}
          title="Đại Lý Trường Thành"
          sub="Quản lý hồ sơ đại lý của Trường Thành và xem các lô hàng, chứng từ, công nợ liên quan."
          right={
            <button
              onClick={openCreateForm}
              aria-label="Thêm đại lý"
              className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[13.5px] px-4 min-h-[48px]"
            >
              <Plus size={16} /> THÊM ĐẠI LÝ
            </button>
          }
        />

        <div className="flex items-center gap-2 mt-3 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
          <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Tìm theo mã đối tác, tên, điện thoại hoặc email…"
            aria-label="Tìm đối tác"
            className="w-full bg-transparent px-3 py-3 min-h-[48px] text-[15px] outline-none"
          />
        </div>
        <p className="text-[12.5px] text-slate-500 mt-1.5">
          Chỉ tìm trong {(slice?.searchFields ?? []).length} trường hệ thống thật sự lưu:{(slice?.searchFields ?? []).map((f) => ` ${f}`).join(" · ")}
        </p>

        <div className="mt-3">
          {options.length === 0 ? (
            <p className="text-[14px] text-slate-500">
              Chưa có đối tác nào trong dữ liệu hiện tại — trạng thái là <b>chưa xác định</b>, không có danh sách mẫu.
            </p>
          ) : (
            <>
              <p className="text-[13px] font-bold uppercase tracking-wide text-slate-500 mb-2">
                {list.length} / {slice?.optionCount ?? 0} đối tác
                {slice?.optionTruncated ? ` (giới hạn ${slice.optionLimit})` : ""}
              </p>
              <div className="flex flex-wrap gap-2">
                {list.map((o) => (
                  <button
                    key={o.key}
                    onClick={() => select(o.key)}
                    aria-pressed={o.key === selectedKey}
                    className={cx(
                      "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 px-3.5 min-h-[48px] text-[14px] font-bold text-left",
                      o.key === selectedKey ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a]"
                    )}
                  >
                    <Building2 size={16} className="shrink-0" />
                    <span className="break-words">{o.label}</span>
                    <span className={cx("text-[12px] font-semibold", o.key === selectedKey ? "text-white/70" : "text-slate-400")}>
                      {o.master ? "có master" : "chưa có master"}
                    </span>
                  </button>
                ))}
              </div>
              {list.length === 0 && (
                <p className="text-[14px] text-slate-500 mt-2">
                  Không có đối tác nào khớp “{query.trim()}”. Hệ thống không tạo bản ghi mới để thay thế.
                </p>
              )}
            </>
          )}
          {selectedKey && (
            <button onClick={clear} className="btn-press touch-target mt-3 inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 px-3.5 min-h-[44px] text-[13.5px] font-bold text-slate-600">
              Chọn đối tác khác
            </button>
          )}
        </div>
      </div>

      {/* AGENT MASTER FORM — create/edit through the ONE bounded write event.
          The saved master is shown only after the authoritative readback
          arrives; there is no optimistic persistence. */}
      {formOpen && (
        <div className="rounded-2xl bg-white border-2 border-[#1e5aa8]/40 p-4 md:p-5">
          <SectionTitle
            icon={formMode === "create" ? <Plus size={18} /> : <PencilLine size={18} />}
            title={formMode === "create" ? "Thêm đại lý mới" : `Sửa hồ sơ đại lý · ${formValues.agentId}`}
            sub="Ghi vào master authority_agents hiện có qua writer canonical (quyền sales_write, có audit). Trường để trống được giữ là không xác định."
            right={
              <span className="rounded-lg bg-blue-50 px-2.5 py-1 text-[12px] font-bold text-blue-700">
                {formMode === "create" ? "TẠO MỚI" : "CẬP NHẬT"}
              </span>
            }
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
            {AGENT_FIELDS.map((f) => {
              const locked = formMode === "edit" && f.lockedOnEdit;
              return (
                <div key={f.key} className={cx(f.wide && "md:col-span-2")}>
                  <Field label={f.label} required={f.required}>
                    <input
                      value={formValues[f.key]}
                      onChange={(e) => setField(f.key, e.target.value)}
                      disabled={locked || !!savePending}
                      aria-label={f.label}
                      placeholder={locked ? "" : "—"}
                      className={cx(inputCls(formValues[f.key].trim() ? "ok" : undefined),
                        f.mono && "font-mono", locked && "opacity-60 cursor-not-allowed")}
                    />
                  </Field>
                </div>
              );
            })}
          </div>

          {saveError && (
            <div className="mt-4 rounded-xl border-2 border-red-200 bg-red-50 p-3.5 flex items-start gap-2.5" role="alert">
              <CircleAlert size={18} className="text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-extrabold text-[14.5px] text-red-800">Backend từ chối — hồ sơ chưa được lưu</p>
                <p className="text-[13.5px] text-red-700 mt-0.5 break-words">{saveError}</p>
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-2.5 mt-4">
            <button
              onClick={submitAgentForm}
              disabled={!!savePending}
              aria-label="Lưu hồ sơ đại lý"
              className="btn-press touch-target flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-5 min-h-[48px] disabled:opacity-60"
            >
              <Save size={16} /> {savePending ? "ĐANG CHỜ BACKEND XÁC NHẬN…" : "LƯU HỒ SƠ ĐẠI LÝ"}
            </button>
            <button
              onClick={() => { if (!savePending) { setFormOpen(false); setSaveError(""); } }}
              disabled={!!savePending}
              className="btn-press touch-target inline-flex items-center justify-center rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-5 min-h-[48px] disabled:opacity-60"
            >
              Hủy
            </button>
          </div>
        </div>
      )}

      {/* PENDING: the readback is authoritative, so nothing is rendered early */}
      {pending && (
        <div className="rounded-2xl bg-white border border-slate-200 p-8 text-center">
          <p className="text-[15px] font-semibold text-slate-500">Đang đọc ngữ cảnh đối tác…</p>
        </div>
      )}

      {/* NO SOURCE / NOT FOUND — honest states, never a fake workspace */}
      {!pending && slice && slice.status === "NO_PARTNER_SOURCE" && (
        <div className="rounded-2xl bg-white border-2 border-dashed border-amber-300 p-8 text-center">
          <span className="mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center">
            <ShieldQuestion size={26} />
          </span>
          <h3 className="text-[16px] font-extrabold text-[#0f2a4a] mt-3">Chưa có nguồn dữ liệu đối tác</h3>
          <p className="text-[14px] text-slate-500 mt-1 max-w-[640px] mx-auto leading-relaxed">{slice.reason}</p>
        </div>
      )}
      {!pending && slice && slice.status === "PARTNER_NOT_FOUND" && (
        <div className="rounded-2xl bg-white border-2 border-amber-300 p-6 text-center">
          <span className="mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center">
            <Info size={26} />
          </span>
          <h3 className="text-[16px] font-extrabold text-[#0f2a4a] mt-3">Không tìm thấy đối tác</h3>
          <p className="text-[14px] text-slate-500 mt-1 leading-relaxed">{slice.reason}</p>
        </div>
      )}
      {!pending && (!slice || slice.status === "NO_SELECTION") && options.length > 0 && (
        <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center">
          <span className="mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center">
            <Handshake size={26} />
          </span>
          <h3 className="text-[16px] font-extrabold text-[#0f2a4a] mt-3">Bảng ngữ cảnh đang trống</h3>
          <p className="text-[14px] text-slate-500 mt-1">Chọn một đối tác ở trên để xem hồ sơ pháp lý, lô liên kết và công nợ thật.</p>
        </div>
      )}

      {showContext && slice && (
        <>
          {/* IDENTITY */}
          <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <div className="flex items-start gap-2 flex-wrap">
              <div className="min-w-0">
                <p className="text-[12px] font-extrabold uppercase tracking-wider text-[#1e5aa8]">Hồ sơ pháp lý · danh tính</p>
                <h2 className="text-[19px] md:text-[21px] font-extrabold text-[#0f2a4a] break-words mt-0.5">{fmtText(identity?.displayName)}</h2>
                <p className="text-[13px] text-slate-500 mt-0.5 break-all">
                  Mã: {fmtText(identity?.displayId)} · {(slice.matchedSources ?? []).join(" · ") || UNKNOWN}
                </p>
              </div>
              <span className="ml-auto shrink-0 flex items-center gap-1.5">
                <ToneBadge tone={toneFor(identity?.masterStatus)} size="sm">
                  master: {identity?.masterStatus === "KNOWN" ? "CÓ HỒ SƠ" : "CHƯA CÓ"}
                </ToneBadge>
                {party && (
                  <button
                    onClick={openEditForm}
                    aria-label="Sửa hồ sơ đại lý"
                    className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-[#1e5aa8]/50 text-[#1e5aa8] font-bold text-[13px] px-3.5 min-h-[44px]"
                  >
                    <PencilLine size={15} /> Sửa hồ sơ đại lý
                  </button>
                )}
              </span>
            </div>
            <p className="text-[12.5px] text-slate-400 mt-2 break-words">
              Nguồn danh tính: {fmtText(identity?.masterSource)}
              {identity?.contextName ? ` · ngữ cảnh lô ghi nhận: ${identity.contextName}${identity.contextId ? ` (${identity.contextId})` : ""}` : ""}
            </p>

            <div className="grid gap-2 mt-3 sm:grid-cols-2 lg:grid-cols-3">
              <InfoCell label="Mã số thuế / pháp lý" value={party?.legalCode} mono />
              <InfoCell label="Điện thoại" value={party?.phone} mono />
              <InfoCell label="Email" value={party?.email} />
              <InfoCell label="Người đại diện" value={party ? `${party.representative}${party.representativeTitle ? ` — ${party.representativeTitle}` : ""}` : null} />
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 sm:col-span-2 lg:col-span-2">
                <p className="text-[12px] font-bold uppercase tracking-wide text-slate-500">Địa chỉ pháp lý</p>
                <p className="mt-0.5 font-semibold text-[14.5px] break-words">{fmtText(party?.legalAddress)}</p>
              </div>
            </div>

            <div className="mt-3 rounded-xl border-2 border-slate-100 bg-slate-50/60 p-3">
              <p className="text-[12px] font-extrabold uppercase tracking-wider text-slate-500">Tài khoản thanh toán (nguyên văn từ master)</p>
              <div className="grid gap-2 mt-2 sm:grid-cols-2 lg:grid-cols-4">
                <InfoCell label="Chủ tài khoản" value={party?.bankAccountHolder} />
                <InfoCell label="Số tài khoản" value={party?.bankAccountNumber} mono />
                <InfoCell label="Ngân hàng" value={party?.bankName} />
                <InfoCell label="Chi nhánh" value={party?.bankBranch} />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 mt-3">
              <span className="text-[12.5px] font-bold text-slate-500 inline-flex items-center gap-1.5"><Phone size={14} /> Vai trò theo lô:</span>
              {(slice.roles ?? []).length === 0
                ? <span className="text-[13.5px] font-semibold text-slate-400">{UNKNOWN}</span>
                : (slice.roles ?? []).map((role) => (
                    <span key={role} className="rounded-full bg-slate-100 px-3 py-1 text-[12.5px] font-bold text-slate-600">{role}</span>
                  ))}
            </div>
          </div>

          {/* LINKED SHIPMENTS */}
          <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <SectionTitle
              icon={<ArrowRight size={18} />}
              title={`Lô hàng liên kết · ${slice.shipmentCount ?? 0}`}
              sub="Mã lô lấy từ chính dữ liệu; chi tiết lô không bị lặp lại ở đây — bấm Mở lô để sang màn hình Lô hàng."
            />
            {linked.length === 0 ? (
              <p className="text-[14px] text-slate-500 mt-2">
                Chưa có lô nào liên kết với đối tác này trong dữ liệu hiện tại — <b>chưa xác định</b>, không phải 0 lô.
              </p>
            ) : (
              <>
                {/* desktop table */}
                <div className="hidden lg:block mt-3 overflow-x-auto">
                  <table className="tbl w-full text-[14px] min-w-[900px]">
                    <thead>
                      <tr>
                        <th>Lô</th><th>Vai trò</th><th>Tuyến</th><th>Khách cần giao</th><th>Kế hoạch</th><th>Trạng thái</th><th>Chú ý</th><th>Hành động</th>
                      </tr>
                    </thead>
                    <tbody>
                      {linked.map((r) => (
                        <tr key={r.shipmentId} className="hover:bg-slate-50">
                          <td className="font-extrabold text-[#1e5aa8] whitespace-nowrap">{r.shipmentId}</td>
                          <td>{fmtText(r.role)}</td>
                          <td>{fmtText(r.route)}</td>
                          <td className="whitespace-nowrap">{fmtText(r.requiredDate)}</td>
                          <td className="whitespace-nowrap">{fmtText(r.plannedDate)}</td>
                          <td>{fmtText(r.status)}</td>
                          <td className="max-w-[220px] text-[13px]">{fmtText(r.attention)}</td>
                          <td>
                            {r.canOpen ? (
                              <Link to={r.openHref} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]">
                                <Eye size={15} /> Mở lô
                              </Link>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[12.5px] font-bold text-slate-400"><Lock size={13} /> không mở được</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {/* mobile / tablet cards */}
                <div className="lg:hidden space-y-3 mt-3">
                  {linked.map((r) => <ShipmentRow key={r.shipmentId} row={r} />)}
                </div>
                {slice.shipmentTruncated && (
                  <p className="text-[12.5px] text-amber-700 font-semibold mt-2">
                    Danh sách rút gọn — còn {Math.max(0, (slice.shipmentCount ?? 0) - linked.length)} lô khác chưa hiển thị.
                  </p>
                )}
              </>
            )}
          </div>

          {/* FINANCE — existing canonical truth, never re-derived */}
          <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <SectionTitle
              icon={<Wallet size={18} className="text-[#1e5aa8]" />}
              title="Công nợ phải trả theo lô"
              sub={finance?.note ?? ""}
              right={<ToneBadge tone={toneFor(finance?.status)} size="sm">{fmtText(finance?.statusLabel)}</ToneBadge>}
            />
            {rows.length === 0 ? (
              <p className="text-[14px] text-slate-500 mt-2">
                Chưa có nghĩa vụ/thanh toán canonical nào cho đối tác này. Phải trả: <b>chưa xác định</b> — hệ thống không hiển thị 0.
              </p>
            ) : (
              <div className="space-y-2.5 mt-3">
                {rows.map((r, i) => (
                  <div key={r.id ?? `${r.shipmentId}-${r.currency}-${i}`} className="rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      {r.shipmentId && openable.has(r.shipmentId.toLowerCase()) ? (
                        <Link to={shipmentPath(r.shipmentId) + "?tab=tai-chinh"} className="font-extrabold text-[15.5px] text-[#1e5aa8] hover:underline break-all">{r.shipmentId}</Link>
                      ) : (
                        <span className="font-extrabold text-[15.5px] text-[#0f2a4a] break-all">{fmtText(r.shipmentId)}</span>
                      )}
                      <span className="rounded-md bg-white border px-2 py-0.5 text-[12px] font-bold">{fmtText(r.currency)}</span>
                      <ToneBadge tone={toneFor(r.status)} size="sm">{fmtText(r.status)}</ToneBadge>
                      <span className="ml-auto text-[12px] text-slate-400">{r.obligationIds.length} nghĩa vụ</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      <MoneyCell label="Phải trả" value={r.payable} ccy={r.currency} />
                      <MoneyCell label="Đã trả" value={r.paid} ccy={r.currency} />
                      <MoneyCell label="Còn lại" value={r.remaining} ccy={r.currency} strong />
                    </div>
                    <p className="text-[12px] text-slate-400 mt-1.5 break-words">nguồn: {fmtText(r.source)}</p>
                  </div>
                ))}
                <p className="text-[12.5px] text-slate-500">
                  {Object.entries(finance?.byCurrency ?? {}).map(([ccy, bucket]) => `${ccy}: ${bucket.rowCount} dòng · ${bucket.shipmentIds.length} lô`).join(" · ") || UNKNOWN}
                  {" — không cộng gộp khác loại tiền tệ, không tổng hợp công nợ toàn đối tác tại đây."}
                </p>
              </div>
            )}
            <div className="flex flex-wrap gap-2.5 mt-3">
              <Link to={finance?.worklistHref ?? "/tai-chinh/cong-no-doi-tac"} className="btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14px] px-4 min-h-[48px]">
                Mở Công nợ đối tác <ArrowRight size={16} />
              </Link>
              <Link to="/lo-hang" className="btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[48px]">
                Xem Lô Hàng
              </Link>
            </div>
            <p className="text-[12.5px] text-slate-400 mt-2">Số liệu do sổ cái canonical dẫn xuất (C2B/C2D); màn hình này chỉ đọc lại, không tự tính.</p>
          </div>

          {/* EVIDENCE (only when the existing projection really has it) */}
          {documents.length > 0 && (
            <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <SectionTitle icon={<Info size={18} />} title={`Tài liệu bằng chứng theo lô · ${documents.length}`} sub="Dự phóng từ hồ sơ lô hiện có — không có kho tài liệu riêng của đối tác." />
              <div className="grid gap-2 mt-3 sm:grid-cols-2 lg:grid-cols-3">
                {documents.map((d, i) => (
                  <div key={`${d.shipmentId}-${d.document}-${i}`} className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                    <p className="text-[13px] font-extrabold text-[#0f2a4a] break-all">{fmtText(d.document)}</p>
                    <p className="text-[12.5px] text-slate-500 mt-0.5 break-all">{fmtText(d.shipmentId)} · {fmtText(d.status)}</p>
                    <p className="text-[12px] text-slate-400 mt-1 break-words">nguồn: {fmtText(d.source)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* MISSING + UNAVAILABLE — available vs unavailable context */}
          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <p className="text-[12px] font-extrabold uppercase tracking-wider text-amber-700">Context còn thiếu / chưa xác định</p>
              <ul className="mt-2 space-y-1.5">
                {gaps.map((gap) => (
                  <li key={gap} className="text-[13.5px] text-slate-600 flex items-start gap-2">
                    <CircleAlert size={15} className="shrink-0 mt-0.5 text-amber-600" /><span className="break-words">{gap}</span>
                  </li>
                ))}
                {gaps.length === 0 && <li className="text-[13.5px] text-slate-500">Không có missing field nào trong dữ liệu hiện có.</li>}
              </ul>
              <p className="text-[12px] text-slate-400 mt-2.5">
                Trường thiếu hiển thị “{UNKNOWN}” — hệ thống không điền 0 và không suy đoán.
              </p>
            </div>
            <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <p className="text-[12px] font-extrabold uppercase tracking-wider text-slate-500">Context không khả dụng trong hệ thống</p>
              <ul className="mt-2 space-y-1.5">
                {unavailable.map((item) => (
                  <li key={item} className="text-[13.5px] text-slate-600 flex items-start gap-2">
                    <Lock size={14} className="shrink-0 mt-1 text-slate-400" /><span className="break-words">{item}</span>
                  </li>
                ))}
              </ul>
              <p className="text-[12px] text-slate-400 mt-2.5">
                Đây là chủ đích: màn hình không dựng tab/score/activity cho dữ liệu backend chưa tồn tại.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
