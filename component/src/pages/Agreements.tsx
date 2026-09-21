// ============================================================================
// Thỏa thuận mua bán / bàn giao — Phase C1, donor Logi-good visual shell.
//
// Agreements are REAL LOG-C13 documents: frozen from an ACCEPTED quote via
// core.commercial_agreements through the ONE bounded dispatcher
// (agreement_create / agreement_edit / agreement_transition), RBAC
// commercial_write, then read back fresh. Commercial terms only — never
// Finance Actual.
// ============================================================================

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Plus, PenLine, FileCheck2, ArrowRight } from "lucide-react";
import {
  Field,
  GhostBtn,
  PrimaryBtn,
  SectionTitle,
  SuccessBtn,
  ToneBadge,
  inputCls,
} from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtMoney, fmtText } from "../lib/format";
import type { Agreement } from "../lib/viewmodel";

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Nháp",
  REVIEWING: "Đang review",
  AGREED: "Đã đồng ý",
  REVISED: "Đã sửa đổi",
  VOID: "Vô hiệu",
};
const STATUS_TONE: Record<string, "green" | "amber" | "red" | "blue" | "gray"> = {
  DRAFT: "gray",
  REVIEWING: "blue",
  AGREED: "green",
  REVISED: "amber",
  VOID: "red",
};

const EVIDENCE_KEYS = ["accepted_quotation", "signed_contract", "customer_confirmation", "entrusted_documentation"] as const;
const EVIDENCE_LABEL: Record<string, string> = {
  accepted_quotation: "Báo giá được khách chốt",
  signed_contract: "Hợp đồng đã ký",
  customer_confirmation: "Khách xác nhận (email/tin nhắn)",
  entrusted_documentation: "Chứng từ ủy thác nhập khẩu",
};

export default function Agreements() {
  const { agreements, quotes, dispatch, toast } = useStore();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("ALL");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Agreement | null>(null);
  const [quoteId, setQuoteId] = useState("");
  const [assumptions, setAssumptions] = useState("");
  const [issues, setIssues] = useState("");
  const [evidence, setEvidence] = useState<Record<string, boolean>>({});

  const list = useMemo(
    () =>
      agreements.filter(
        (a) =>
          (status === "ALL" || a.status === status) &&
          (!q || (a.id + a.agreementNo + a.customer + a.quoteReference).toLowerCase().includes(q.toLowerCase()))
      ),
    [agreements, q, status]
  );
  const statuses = ["ALL", ...Array.from(new Set(agreements.map((a) => a.status)))];

  // Quotes eligible to seed an agreement: accepted and not yet frozen.
  const eligibleQuotes = useMemo(() => {
    const used = new Set(agreements.map((a) => a.quoteId).filter(Boolean));
    return quotes.filter((x) => ["ACCEPTED", "READY_TO_CREATE_SHIPMENT"].includes(x.status) && !used.has(x.id));
  }, [quotes, agreements]);

  const openCreate = () => {
    setQuoteId("");
    setCreating(true);
  };
  const openEdit = (a: Agreement) => {
    setAssumptions((a.assumptions || []).join("\n"));
    setIssues((a.unresolvedIssues || []).join("\n"));
    const ev: Record<string, boolean> = {};
    for (const k of EVIDENCE_KEYS) ev[k] = !!a.evidence?.[k];
    setEvidence(ev);
    setEditing(a);
  };

  const submitCreate = () => {
    if (!quoteId) {
      toast("Chưa chọn báo giá", "Thỏa thuận chỉ được tạo từ báo giá đã khách chốt (ACCEPTED).", "red");
      return;
    }
    dispatch("agreement_create", { quoteId });
    toast("Đã gửi tạo thỏa thuận", "Backend đóng băng điều khoản thương mại từ báo giá chốt.", "green");
    setCreating(false);
  };

  const submitEdit = () => {
    if (!editing) return;
    dispatch("agreement_edit", {
      id: editing.id,
      assumptions: assumptions.split("\n").map((s) => s.trim()).filter(Boolean),
      unresolved_issues: issues.split("\n").map((s) => s.trim()).filter(Boolean),
      evidence: {
        ...EVIDENCE_KEYS.reduce((acc, k) => ({ ...acc, [k]: !!evidence[k] }), {}),
        notes: "",
        source: "Bằng chứng đánh dấu thủ công qua work desk; không suy diễn 'đã ký' từ tên file.",
      },
    });
    toast("Đã gửi cập nhật " + editing.id, "Backend ghi + audit; bàn giao được tính lại.", "green");
    setEditing(null);
  };

  const transition = (a: Agreement, next: string) => {
    dispatch("agreement_transition", { id: a.id, nextStatus: next });
    toast("Đã gửi chuyển trạng thái " + a.id, `→ ${STATUS_LABEL[next] ?? next}. Backend kiểm tra đúng luồng.`, "blue");
  };

  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<FileCheck2 size={18} />}
          title="Thỏa thuận mua bán · Bàn giao"
          sub="Đóng băng điều khoản thương mại từ báo giá đã chốt — KHÔNG phải tài chính thực thu/chi"
          right={<button onClick={openCreate} className="btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]"><Plus size={18} /> Tạo thỏa thuận</button>}
        />
        <div className="flex gap-2">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nhập mã thỏa thuận, khách, báo giá nguồn…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
        </div>
        <div className="flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1">
          {statuses.map((s) => (
            <button key={s} onClick={() => setStatus(s)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", status === s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>
              {s === "ALL" ? "Tất cả" : STATUS_LABEL[s] ?? s}
            </button>
          ))}
        </div>
        <p className="text-[13.5px] text-slate-500 mt-1.5">Tìm thấy <b className="text-[#0f2a4a]">{list.length} thỏa thuận</b> · Trạng thái & bàn giao do backend quyết định.</p>
      </div>

      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="tbl w-full text-[14px] min-w-[960px]">
            <thead>
              <tr><th>Mã thỏa thuận</th><th>Khách hàng</th><th>Báo giá nguồn</th><th>Trạng thái</th><th>Bàn giao</th><th>Hành động</th></tr>
            </thead>
            <tbody>
              {list.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50">
                  <td><span className="font-extrabold text-[#1e5aa8] text-[15px]">{a.id}</span><span className="block text-[12px] text-slate-400">{a.agreementNo}</span></td>
                  <td className="font-semibold max-w-[180px]">{a.customer}</td>
                  <td className="text-[13px] text-slate-600">{fmtText(a.quoteReference)}</td>
                  <td><ToneBadge tone={STATUS_TONE[a.status] ?? "gray"} size="sm">{a.statusLabel || a.status}</ToneBadge></td>
                  <td className="max-w-[220px]"><ToneBadge tone={a.handoff.state === "READY_FOR_OPERATIONS" ? "green" : a.handoff.state === "MISSING_REQUIRED_DATA" ? "red" : "amber"} size="sm">{a.handoff.label}</ToneBadge></td>
                  <td>
                    <div className="flex flex-wrap gap-1.5">
                      {a.allowedTransitions.map((t) => (
                        <button key={t} onClick={() => transition(a, t)} className="btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]">{STATUS_LABEL[t] ?? t}</button>
                      ))}
                      <button onClick={() => openEdit(a)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]"><PenLine size={14} /> Sửa</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {list.length === 0 && (
          <div className="p-8 text-center">
            <p className="font-bold text-[16px]">Chưa có thỏa thuận nào</p>
            <p className="text-[14px] text-slate-500 mt-1">Tạo từ báo giá đã được khách chốt (ACCEPTED).</p>
            <button onClick={openCreate} className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5"><Plus size={17} /> Tạo thỏa thuận</button>
          </div>
        )}
      </div>

      <div className="md:hidden space-y-3">
        {list.map((a) => (
          <div key={a.id} className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-extrabold text-[16px] text-[#0f2a4a]">{a.id}</span>
                <ToneBadge tone={STATUS_TONE[a.status] ?? "gray"} size="sm">{a.statusLabel || a.status}</ToneBadge>
              </div>
              <p className="font-semibold text-[14.5px] mt-1">{a.customer}</p>
              <p className="text-[13px] text-slate-500">Nguồn: {fmtText(a.quoteReference)}</p>
              <div className="mt-2"><ToneBadge tone={a.handoff.state === "READY_FOR_OPERATIONS" ? "green" : a.handoff.state === "MISSING_REQUIRED_DATA" ? "red" : "amber"} size="sm">{a.handoff.label}</ToneBadge></div>
            </div>
            <div className="border-t p-3 flex flex-wrap gap-2">
              {a.allowedTransitions.map((t) => (
                <button key={t} onClick={() => transition(a, t)} className="btn-press touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]">{STATUS_LABEL[t] ?? t}</button>
              ))}
              <button onClick={() => openEdit(a)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]"><PenLine size={14} /> Sửa</button>
            </div>
          </div>
        ))}
        {list.length === 0 && (
          <div className="rounded-2xl bg-white border p-8 text-center">
            <p className="font-bold text-[16px]">Chưa có thỏa thuận nào</p>
            <button onClick={openCreate} className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center"><Plus size={17} /> Tạo thỏa thuận</button>
          </div>
        )}
      </div>

      {/* MODAL: create from accepted quote */}
      {creating && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => setCreating(false)} />
          <div className="relative bg-white w-full sm:max-w-[520px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up">
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">Tạo thỏa thuận từ báo giá chốt</h3>
            <p className="text-[13.5px] text-slate-500">Chỉ báo giá ACCEPTED / sẵn sàng tạo lô mới dùng được.</p>
            {eligibleQuotes.length === 0 ? (
              <p className="mt-4 rounded-xl bg-amber-50 border border-amber-200 p-4 text-[14px] text-amber-900">
                Chưa có báo giá ACCEPTED. Vào <Link to="/kinh-doanh-bao-gia" className="font-bold underline">Báo Giá</Link> để chốt khách trước.
              </p>
            ) : (
              <div className="grid gap-3 mt-4">
                <Field label="Báo giá nguồn" required>
                  <select value={quoteId} onChange={(e) => setQuoteId(e.target.value)} className={inputCls(!quoteId ? "missing" : "ok")}>
                    <option value="">-- Chọn báo giá đã chốt --</option>
                    {eligibleQuotes.map((x) => <option key={x.id} value={x.id}>{x.id} · {x.customer} · {fmtMoney(x.sellingPriceTotalVnd ?? x.total)} ₫</option>)}
                  </select>
                </Field>
              </div>
            )}
            <div className="grid grid-cols-2 gap-2.5 mt-5">
              <GhostBtn onClick={() => setCreating(false)}>Hủy</GhostBtn>
              {eligibleQuotes.length > 0 ? (
                <SuccessBtn onClick={submitCreate}>TẠO</SuccessBtn>
              ) : (
                <PrimaryBtn onClick={() => { setCreating(false); }}>ĐÓNG</PrimaryBtn>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL: edit commercial terms + evidence */}
      {editing && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => setEditing(null)} />
          <div className="relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[90vh] overflow-auto" style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" }}>
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">Sửa thỏa thuận {editing.id}</h3>
            <p className="text-[13.5px] text-slate-500">Điều khoản thương mại & bằng chứng bàn giao — ghi qua backend, không phải tài chính.</p>
            <div className="mt-4">
              <p className="font-extrabold text-[14.5px] text-[#0f2a4a] mb-2">Bằng chứng chấp nhận</p>
              <div className="grid sm:grid-cols-2 gap-2">
                {EVIDENCE_KEYS.map((k) => (
                  <label key={k} className="flex items-center gap-2.5 rounded-xl border border-slate-200 p-3 cursor-pointer">
                    <input type="checkbox" checked={!!evidence[k]} onChange={(e) => setEvidence((ev) => ({ ...ev, [k]: e.target.checked }))} className="w-5 h-5 accent-[#0f2a4a]" />
                    <span className="text-[14px] font-semibold text-slate-700">{EVIDENCE_LABEL[k]}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="grid gap-3 mt-4">
              <Field label="Giả định thương mại (mỗi dòng một mục)">
                <textarea value={assumptions} onChange={(e) => setAssumptions(e.target.value)} rows={4} className={inputCls()} />
              </Field>
              <Field label="Vấn đề chưa giải quyết (mỗi dòng một mục)">
                <textarea value={issues} onChange={(e) => setIssues(e.target.value)} rows={3} placeholder="Các vấn đề chặn bàn giao vận hành" className={inputCls()} />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-2.5 mt-5">
              <GhostBtn onClick={() => setEditing(null)}>Hủy</GhostBtn>
              <PrimaryBtn onClick={submitEdit}>💾 LƯU THỎA THUẬN</PrimaryBtn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
