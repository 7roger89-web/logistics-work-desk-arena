// ============================================================================
// Chi tiết hợp đồng — Phase C1 work desk, donor Logi-good visual shell.
//
// Tabs: Tổng quan (identity/parties) → Hàng hóa → Chứng từ HDNT/PL/HDMB →
// Lô liên kết. Every write is ONE typed event → the bounded dispatcher →
// RBAC → existing writer/service → audit → fresh backend read:
//   contract_save, contract_goods_save, contract_docgen_generate,
//   contract_docgen_issue, contract_shipment_link.
//
// UNKNOWN != ZERO: blank quantity / unit price stays blank and is never
// coerced to 0; the goods totals and the 50M threshold are backend-decided.
// ============================================================================

import { useEffect, useState } from "react";
import { Link, useNavigate, useLocation, useSearchParams } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, Download, FileText, Link2, Package, Plus, Trash2,
  FileCheck2, Stamp, CircleCheck, Banknote,
} from "lucide-react";
import {
  Field, PlChoice, PrimaryBtn, SearchPicker, StateRow, ToneBadge, inputCls,
} from "../components/ui";
import { useStore } from "../lib/store";
import { cx, downloadBinaryFile, fmtMoney, fmtText, fmtVND, isUnknown } from "../lib/format";
import type { Contract, GoodsLine } from "../lib/viewmodel";

const TABS = [
  { id: "tong-quan", label: "Tổng quan", short: "Tổng quan" },
  { id: "hang-hoa", label: "Hàng hóa hợp đồng", short: "Hàng hóa" },
  { id: "chung-tu", label: "Chứng từ HDNT/PL/HDMB", short: "Chứng từ" },
  { id: "lo-lien-ket", label: "Lô liên kết", short: "Lô liên kết" },
];

const DOC_STATE_TONE: Record<string, "green" | "amber" | "red" | "blue" | "gray"> = {
  READY: "green",
  GENERATED: "blue",
  MISSING_INFO: "amber",
  NOT_APPLICABLE: "gray",
  OWNER_RULE_REQUIRED: "amber",
  BLOCKED: "red",
  DEFERRED: "gray",
  ISSUED: "green",
};

const DOC_STATE_LABEL: Record<string, string> = {
  READY: "Sẵn sàng",
  GENERATED: "Đã sinh",
  MISSING_INFO: "Thiếu thông tin",
  NOT_APPLICABLE: "Không áp dụng",
  OWNER_RULE_REQUIRED: "Cần quy tắc chủ",
  BLOCKED: "Bị chặn",
  DEFERRED: "Hoãn lại",
  ISSUED: "Đã phát hành",
};

interface GoodsRow {
  description: string;
  unit: string;
  quantity: string;
  unitPrice: string;
}

function rowToForm(l: GoodsLine): GoodsRow {
  return {
    description: l.description,
    unit: l.unit,
    quantity: l.quantity == null ? "" : String(l.quantity),
    unitPrice: l.unitPrice == null ? "" : String(l.unitPrice),
  };
}

export default function ContractDetail() {
  // React Router 7 params collapse a literal "%2F" into "/" even after
  // segment encoding. Decode the original location segment exactly ONCE.
  const { pathname } = useLocation();
  let id: string | undefined;
  try { id = decodeURIComponent(pathname.slice("/hop-dong/".length)); }
  catch { id = undefined; }
  const [sp, setSp] = useSearchParams();
  const tab = sp.get("tab") || "tong-quan";
  const { contracts, authority, shipments, customers, dispatch, toast } = useStore();
  const nav = useNavigate();
  const c = contracts.find((x) => x.id === id);

  // Identity / party edit state.
  const [form, setForm] = useState<Record<string, string>>({});
  const [goods, setGoods] = useState<GoodsRow[]>([]);
  const [linkShipmentId, setLinkShipmentId] = useState("");

  const resetForms = (contract: Contract) => {
    setForm({
      company_id: contract.companyId ?? "",
      agent_id: contract.agentId ?? "",
      customerId: contract.customerId ?? "",
      kind: contract.kind ?? "",
      value: contract.value == null ? "" : String(contract.value),
      currency: contract.currency || "VND",
      note: contract.note ?? "",
      // The two facts LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 made keepable.
      // Both are seeded from the BACKEND readback, never from a local guess, so
      // a reopened contract shows what is stored ("" = chưa chọn / chưa có).
      date: contract.contractDate ?? "",
      pl_required: contract.plRequired ?? "",
      hdnt_no: contract.identity?.hdntNo ?? "",
      hdnt_date: contract.identity?.hdntDate ?? "",
      valid_from: contract.identity?.validFrom ?? "",
      valid_to: contract.identity?.validTo ?? "",
      pl_no: contract.identity?.plNo ?? "",
      pl_date: contract.identity?.plDate ?? "",
      hdmb_no: contract.identity?.hdmbNo ?? "",
      hdmb_date: contract.identity?.hdmbDate ?? "",
    });
    setGoods(contract.goodsLines.length ? contract.goodsLines.map(rowToForm) : [{ description: "", unit: "", quantity: "", unitPrice: "" }]);
  };

  useEffect(() => {
    if (c) resetForms(c);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [c?.id]);

  if (!c) {
    return (
      <div className="rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto">
        <p className="font-extrabold text-[19px]">Không tìm thấy hợp đồng {id}</p>
        <p className="text-slate-500 mt-1 text-[15px]">Số hợp đồng có thể sai. Về danh sách để tìm lại.</p>
        <Link to="/hop-dong" className="btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center">Về danh sách hợp đồng</Link>
      </div>
    );
  }

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const setGood = (i: number, k: keyof GoodsRow, v: string) => setGoods((g) => g.map((row, idx) => (idx === i ? { ...row, [k]: v } : row)));
  const addGood = () => setGoods((g) => [...g, { description: "", unit: "", quantity: "", unitPrice: "" }]);
  const removeGood = (i: number) => setGoods((g) => (g.length > 1 ? g.filter((_, idx) => idx !== i) : g));

  const saveOverview = () => {
    // The customer half travels ONLY when the operator actually re-picked it:
    // a legacy contract without customer_id must stay saveable, while an
    // explicit re-selection is validated by the backend (unknown/blank id is
    // refused there instead of blanking the client).
    const picked = (form.customerId ?? "").trim();
    const payload: Record<string, string> = {
      id: c.id,
      company_id: form.company_id.trim(),
      agent_id: form.agent_id.trim(),
      kind: form.kind.trim(),
      currency: form.currency.trim(),
      note: form.note.trim(),
      value: form.value.trim(),
      // Explicit and always sent: the backend treats the key as "the operator
      // answered", and "" is a real answer (chưa chọn), not a silent default.
      date: (form.date ?? "").trim(),
      pl_required: (form.pl_required ?? "").trim(),
      hdnt_no: form.hdnt_no.trim(),
      hdnt_date: form.hdnt_date.trim(),
      valid_from: form.valid_from.trim(),
      valid_to: form.valid_to.trim(),
      pl_no: form.pl_no.trim(),
      pl_date: form.pl_date.trim(),
      hdmb_no: form.hdmb_no.trim(),
      hdmb_date: form.hdmb_date.trim(),
    };
    if (picked !== (c.customerId ?? "")) payload.customerId = picked;
    if (!dispatch("contract_save", payload)) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    toast("Đã gửi lưu " + c.id, "Chờ máy chủ xử lý; dữ liệu sẽ được đọc lại từ Logistics.", "blue");
  };

  const saveGoods = () => {
    const rows = goods.map((g) => ({
      description: g.description.trim(),
      unit: g.unit.trim(),
      quantity: g.quantity.trim(),
      unitPrice: g.unitPrice.trim(),
    }));
    if (!dispatch("contract_goods_save", { id: c.id, goodsLines: rows })) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    toast("Đã gửi lưu hàng hóa " + c.id, "Blank số lượng/đơn giá = UNKNOWN (không bao giờ thành 0).", "blue");
  };

  const generateDocs = () => {
    if (!dispatch("contract_docgen_generate", { id: c.id })) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    toast("Đã gửi sinh chứng từ " + c.id, "core.docgen kiểm tra threshold 50 triệu & danh tính pháp lý rồi sinh Office thật.", "blue");
  };

  const issueDoc = (documentId: string, revision: number) => {
    if (!dispatch("contract_docgen_issue", { documentId, revision })) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    toast("Đã gửi phát hành " + documentId, "Chứng từ ISSUED sẽ bất biến (không sửa/xóa).", "blue");
  };

  const linkShipment = () => {
    const sid = linkShipmentId.trim().toUpperCase();
    if (!sid) {
      toast("Thiếu mã lô", "Nhập mã lô để liên kết (VD: LO-0306).", "red");
      return;
    }
    if (!dispatch("contract_shipment_link", { id: c.id, shipmentId: sid })) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    toast("Đã gửi liên kết " + sid, "Chờ máy chủ xử lý liên kết N:M hợp đồng ↔ lô.", "blue");
    setLinkShipmentId("");
  };

  const total = c.goodsTotals?.total_after_vat ?? 0;
  const threshold = c.thresholdVnd ?? 50000000;
  const belowThreshold = c.goodsTotals != null && c.goodsTotals.total_after_vat < threshold;

  const unlinkedShipments = shipments.filter((s) => !c.linkedShipments.some((l) => l.id === s.id));

  return (
    <div className="space-y-4 max-w-[1300px]">
      <button onClick={() => nav(-1)} className="touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]"><ArrowLeft size={17} /> Quay lại</button>

      {/* HEADER */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" />
        <div className="p-4 md:p-6">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-[22px] md:text-[26px] font-extrabold text-[#0f2a4a]">{c.id}</h1>
            <ToneBadge tone="blue" size="sm">{c.kind || "—"}</ToneBadge>
            <ToneBadge tone={c.statusTone} size="sm">{c.status}</ToneBadge>
          </div>
          <p className="font-semibold text-[15.5px] mt-1">{c.client || "—"}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-x-6 mt-3">
            <StateRow label="Công ty bên mua" value={fmtText(c.company)} />
            <StateRow label="Đại lý (bán)" value={fmtText(c.agent)} />
            <StateRow label="Giá trị" value={fmtVND(c.value)} />
            <StateRow label="Số lô liên kết" value={String(c.linkedShipments.length)} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-x-6 mt-1">
            <StateRow label="Khách hàng / đối tác" value={fmtText(c.client)} />
            <StateRow label="Ngày hợp đồng" value={fmtText(c.contractDate)} />
            <StateRow
              label="Phụ lục (PL)"
              value={c.plRequired === "YES" ? "Có PL" : c.plRequired === "NO" ? "Không cần PL" : "Chưa chọn"}
            />
            <StateRow label="Loại" value={fmtText(c.kind)} />
          </div>
        </div>
        <div id="contract-tabs" className="px-3 md:px-6 pb-3 flex gap-2 overflow-x-auto no-scrollbar border-t border-slate-100 pt-3">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setSp({ tab: t.id })} className={cx("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14.5px] font-bold border-2 whitespace-nowrap", tab === t.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-600")}>
              <span className="hidden md:inline">{t.label}</span><span className="md:hidden">{t.short}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ============ TAB: OVERVIEW ============ */}
      {tab === "tong-quan" && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-3">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><FileText size={19} className="text-[#1e5aa8]" /> Danh tính pháp lý</h3>
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Số HDNT"><input value={form.hdnt_no} onChange={(e) => set("hdnt_no", e.target.value)} placeholder="HDNT-…/2026" className={inputCls()} /></Field>
              <Field label="Ngày HDNT"><input value={form.hdnt_date} onChange={(e) => set("hdnt_date", e.target.value)} placeholder="2026-09-01" className={inputCls()} /></Field>
              <Field label="Hiệu lực từ"><input value={form.valid_from} onChange={(e) => set("valid_from", e.target.value)} placeholder="2026-09-01" className={inputCls()} /></Field>
              <Field label="Hiệu lực đến"><input value={form.valid_to} onChange={(e) => set("valid_to", e.target.value)} placeholder="2027-08-31" className={inputCls()} /></Field>
              <Field label="Số PL"><input value={form.pl_no} onChange={(e) => set("pl_no", e.target.value)} placeholder="PL-…/2026" className={inputCls()} /></Field>
              <Field label="Ngày PL"><input value={form.pl_date} onChange={(e) => set("pl_date", e.target.value)} placeholder="2026-09-02" className={inputCls()} /></Field>
              <Field label="Số HDMB"><input value={form.hdmb_no} onChange={(e) => set("hdmb_no", e.target.value)} placeholder="HDMB-…/2026" className={inputCls()} /></Field>
              <Field label="Ngày HDMB"><input value={form.hdmb_date} onChange={(e) => set("hdmb_date", e.target.value)} placeholder="2026-09-03" className={inputCls()} /></Field>
            </div>
          </section>

          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-3">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><Banknote size={19} className="text-[#1e5aa8]" /> Đối tác & thông tin chung</h3>
            <div className="grid sm:grid-cols-2 gap-3">
              {/* LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the buyer is labelled
                  the way the team says it ("Công ty bên mua"), is chosen through
                  a real search over the legal master, and is written through the
                  existing contract_save → save_contract_to_cloud path so the
                  value comes back from the backend on the next read. */}
              <SearchPicker
                label="Công ty bên mua"
                testId="contract-buyer-picker"
                required
                options={authority.companies.map((p) => ({
                  id: p.id,
                  label: p.legalName || p.id,
                  sub: p.legalCode ? `MST ${p.legalCode} · ${p.id}` : p.id,
                }))}
                selectedId={form.company_id}
                selectedLabel={authority.companies.find((p) => p.id === form.company_id)?.legalName ?? ""}
                placeholder="Gõ tên công ty hoặc MST để tìm…"
                emptyHint="Chưa có hồ sơ pháp lý Công ty trong master — bổ sung ở màn Hồ sơ đại lý / Công ty trước."
                onSelect={(idValue) => set("company_id", idValue)}
              />
              <Field label="Đại lý (bên bán)" required>
                <select value={form.agent_id} onChange={(e) => set("agent_id", e.target.value)} className={inputCls(!form.agent_id ? "missing" : "ok")}>
                  <option value="">-- Chọn đại lý --</option>
                  {authority.agents.map((p) => <option key={p.id} value={p.id}>{p.legalName}</option>)}
                </select>
              </Field>
              {/* LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — post-create editability
                  of the counterparty: the picker writes the SAME customer fields
                  the create form uses, through the SAME canonical writer, and the
                  row below it shows what the backend just read back. */}
              <SearchPicker
                label="Khách hàng / đối tác"
                testId="contract-customer-picker"
                options={customers.map((x) => ({
                  id: x.id,
                  label: x.name || x.id,
                  sub: x.mst || x.taxCode ? `MST ${x.mst || x.taxCode} · ${x.id}` : x.id,
                }))}
                selectedId={form.customerId}
                selectedLabel={customers.find((x) => x.id === form.customerId)?.name ?? ""}
                placeholder="Gõ tên khách hoặc mã khách để tìm…"
                emptyHint="Danh bạ khách hàng đang trống — nhập từ GetFly ở màn Tạo hợp đồng."
                onSelect={(idValue) => set("customerId", idValue)}
              />
              <Field label="Ngày hợp đồng" hint="2026-09-05 · để trống = chưa có ngày.">
                <input value={form.date ?? ""} onChange={(e) => set("date", e.target.value)} placeholder="2026-09-05" className={inputCls()} />
              </Field>
              <div className="sm:col-span-2 rounded-xl bg-slate-50 border p-3">
                <PlChoice
                  testId="contract-pl-choice"
                  value={form.pl_required ?? ""}
                  onChange={(next) => set("pl_required", next)}
                  stored={c.plRequired === "YES" ? "Có PL" : c.plRequired === "NO" ? "Không cần PL" : "chưa chọn"}
                />
                <p className="text-[12.5px] text-slate-500 mt-1.5">
                  Bấm một trong hai ô rồi LƯU TỔNG QUAN: lựa chọn được ghi vào hợp đồng và đọc lại
                  đúng nguyên văn. Để nguyên “Chưa chọn” khi chưa có quyết định — app không tự điền.
                </p>
              </div>
              <Field label="Loại"><select value={form.kind} onChange={(e) => set("kind", e.target.value)} className={inputCls()}><option value="HDMB">HDMB</option><option value="HDNT">HDNT</option><option value="PL">PL</option></select></Field>
              <Field label="Giá trị (VND)"><input value={form.value} onChange={(e) => set("value", e.target.value)} inputMode="numeric" className={inputCls()} /></Field>
              <Field label="Tiền tệ"><input value={form.currency} onChange={(e) => set("currency", e.target.value)} className={inputCls()} /></Field>
              <Field label="Ghi chú"><input value={form.note} onChange={(e) => set("note", e.target.value)} className={inputCls()} /></Field>
            </div>
            {c.parties && (c.parties.company || c.parties.agent) && (
              <div className="grid sm:grid-cols-2 gap-3 pt-1">
                {c.parties.company && (
                  <div className="rounded-xl bg-slate-50 border p-3">
                    <p className="text-[12px] font-bold uppercase text-slate-400">Công ty — hồ sơ pháp lý</p>
                    <p className="font-bold text-[14px] mt-1">{c.parties.company.legalName}</p>
                    <p className="text-[12.5px] text-slate-500">{c.parties.company.legalCode} · {c.parties.company.legalAddress}</p>
                  </div>
                )}
                {c.parties.agent && (
                  <div className="rounded-xl bg-slate-50 border p-3">
                    <p className="text-[12px] font-bold uppercase text-slate-400">Đại lý — hồ sơ pháp lý</p>
                    <p className="font-bold text-[14px] mt-1">{c.parties.agent.legalName}</p>
                    <p className="text-[12.5px] text-slate-500">{c.parties.agent.legalCode} · {c.parties.agent.legalAddress}</p>
                  </div>
                )}
              </div>
            )}
            <PrimaryBtn onClick={saveOverview} className="w-full">💾 LƯU TỔNG QUAN</PrimaryBtn>
          </section>
        </div>
      )}

      {/* ============ TAB: GOODS ============ */}
      {tab === "hang-hoa" && (
        <div className="space-y-4">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><Package size={19} className="text-[#1e5aa8]" /> Hàng hóa hợp đồng</h3>
              <button onClick={addGood} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]"><Plus size={15} /> Thêm dòng</button>
            </div>
            <div className="overflow-x-auto -mx-1">
              <table className="tbl w-full text-[14px] min-w-[720px]">
                <thead><tr><th className="w-10">STT</th><th>Mô tả hàng hóa</th><th>Đơn vị</th><th>Số lượng</th><th>Đơn giá (VND)</th><th>VAT</th><th>Thành tiền</th><th /></tr></thead>
                <tbody>
                  {goods.map((g, i) => {
                    const qty = g.quantity.trim() === "" ? null : Number(g.quantity);
                    const price = g.unitPrice.trim() === "" ? null : Number(g.unitPrice);
                    const amount = qty != null && price != null ? qty * price : null;
                    return (
                      <tr key={i}>
                        <td className="font-bold text-slate-400">{i + 1}</td>
                        <td><input value={g.description} onChange={(e) => setGood(i, "description", e.target.value)} placeholder="Mô tả hàng hóa" className={inputCls()} /></td>
                        <td><input value={g.unit} onChange={(e) => setGood(i, "unit", e.target.value)} placeholder="Bộ / chiếc" className={inputCls()} /></td>
                        <td><input value={g.quantity} onChange={(e) => setGood(i, "quantity", e.target.value)} inputMode="numeric" placeholder="—" className={inputCls()} /></td>
                        <td><input value={g.unitPrice} onChange={(e) => setGood(i, "unitPrice", e.target.value)} inputMode="numeric" placeholder="—" className={inputCls()} /></td>
                        <td className="text-slate-600">8%</td>
                        <td className="font-bold whitespace-nowrap">{isUnknown(amount) ? "—" : fmtMoney(amount)}</td>
                        <td><button onClick={() => removeGood(i)} className="touch-target inline-flex items-center justify-center w-9 h-9 rounded-lg text-red-600 hover:bg-red-50" aria-label="Xóa dòng"><Trash2 size={16} /></button></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <PrimaryBtn onClick={saveGoods} className="w-full mt-3">💾 LƯU HÀNG HÓA</PrimaryBtn>
            <p className="text-[13px] text-slate-500 mt-2">Số lượng / đơn giá để trống = UNKNOWN (“—”), không bao giờ tự thành 0. Dòng trống hoàn toàn sẽ bị bỏ qua.</p>
          </section>

          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Tổng & quyết định chứng từ (backend)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
              <div className="rounded-xl bg-slate-50 border p-3"><p className="text-[12px] text-slate-500 font-semibold">Tổng trước thuế</p><p className="font-extrabold text-[17px]">{fmtMoney(c.goodsTotals?.subtotal)}</p></div>
              <div className="rounded-xl bg-slate-50 border p-3"><p className="text-[12px] text-slate-500 font-semibold">VAT 8%</p><p className="font-extrabold text-[17px]">{fmtMoney(c.goodsTotals?.vat_amount)}</p></div>
              <div className="rounded-xl bg-blue-50 border border-blue-200 p-3"><p className="text-[12px] text-blue-700 font-semibold">Sau thuế</p><p className="font-extrabold text-[17px] text-blue-700">{fmtMoney(c.goodsTotals?.total_after_vat)}</p></div>
              <div className="rounded-xl bg-violet-50 border border-violet-200 p-3"><p className="text-[12px] text-violet-700 font-semibold">Ngưỡng</p><p className="font-extrabold text-[17px] text-violet-700">{fmtMoney(threshold)}</p></div>
            </div>
            {c.goodsTotals == null ? (
              <div className="mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13.5px] text-amber-900">Chưa có tổng đáng tin cậy (có dòng UNKNOWN) — không thể thay bằng 0, chứng từ bị chặn cho tới khi đủ dữ liệu.</div>
            ) : (
              <div className={cx("mt-3 rounded-xl border-2 p-3.5", belowThreshold ? "border-emerald-300 bg-emerald-50" : "border-blue-300 bg-blue-50")}>
                <p className="font-extrabold text-[15px]">
                  {belowThreshold ? "Sau thuế < 50.000.000 ₫ → HDNT + PL" : "Sau thuế ≥ 50.000.000 ₫ → HDMB"}
                </p>
                <p className="text-[13.5px] mt-0.5">Áp dụng: <b>{c.applicableDocuments.length ? c.applicableDocuments.join(" + ") : "—"}</b></p>
              </div>
            )}
          </section>
        </div>
      )}

      {/* ============ TAB: DOCGEN ============ */}
      {tab === "chung-tu" && (
        <div className="space-y-4">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><FileCheck2 size={19} className="text-[#1e5aa8]" /> Chứng từ HDNT · PL · HDMB</h3>
              <button onClick={generateDocs} className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]"><Stamp size={17} /> SINH CHỨNG TỪ</button>
            </div>
            <p className="text-[13.5px] text-slate-500 mb-3">Quy tắc backend: VAT 8% · VND · làm tròn nửa lên từng đồng · sau thuế &lt; 50M → HDNT + PL, ≥ 50M → HDMB. Chỉ sinh khi READY.</p>
            <div className="grid sm:grid-cols-2 gap-2.5">
              {c.docCards.map((card) => (
                <div key={card.document_type} className="rounded-xl border-2 p-3.5" style={{ borderColor: "var(--slate-200)" }}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-extrabold text-[14.5px] text-[#0f2a4a]">{card.document_type}</span>
                    <ToneBadge tone={DOC_STATE_TONE[card.state] ?? "gray"} size="sm">{DOC_STATE_LABEL[card.state] ?? card.state}</ToneBadge>
                  </div>
                  <p className="text-[13px] text-slate-600 mt-1">{card.reason}</p>
                  {card.missing.length > 0 && (
                    <ul className="mt-1.5 text-[12.5px] text-amber-800 list-disc pl-4 space-y-0.5">
                      {card.missing.map((m) => <li key={m}>{m}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Chứng từ đã sinh — tải về / phát hành / lịch sử</h3>
            {c.documents.length === 0 ? (
              <p className="text-[14px] text-slate-500">Chưa có chứng từ nào. Nhập hàng hóa rồi bấm “SINH CHỨNG TỪ”.</p>
            ) : (
              <div className="space-y-2">
                {c.documents.map((d) => (
                  <div key={d.id} className="flex flex-wrap items-center gap-2.5 rounded-xl border border-slate-200 p-3">
                    <span className={cx("w-9 h-9 rounded-lg grid place-items-center shrink-0", d.status === "ISSUED" ? "bg-emerald-600 text-white" : "bg-blue-100 text-blue-700")}>
                      {d.status === "ISSUED" ? <CircleCheck size={18} /> : <FileText size={18} />}
                    </span>
                    <div className="flex-1 min-w-[180px]">
                      <p className="font-bold text-[14.5px] text-[#0f2a4a]">{d.documentTypeLabel} · R{d.revision}</p>
                      <p className="text-[12.5px] text-slate-500">{d.fileName} · {d.status} · {d.generatedBy ? "bởi " + d.generatedBy : ""}</p>
                    </div>
                    {d.downloadAvailable && d.downloadBase64 && (
                      <button onClick={() => downloadBinaryFile(d.fileName, d.downloadBase64, d.mime)} className="btn-press touch-target inline-flex items-center gap-1.5 rounded-lg border-2 border-slate-200 font-bold text-[13.5px] px-3 min-h-[44px]"><Download size={16} /> Tải</button>
                    )}
                    {d.status !== "ISSUED" && (
                      <button onClick={() => issueDoc(d.documentId, d.revision)} className="btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 text-white font-bold text-[13.5px] px-3 min-h-[44px]"><Stamp size={15} /> Phát hành</button>
                    )}
                    {d.status === "ISSUED" && <ToneBadge tone="green" size="sm">ISSUED — bất biến</ToneBadge>}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {/* ============ TAB: LINKED SHIPMENTS ============ */}
      {tab === "lo-lien-ket" && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3"><Link2 size={19} className="text-[#1e5aa8]" /> Lô hàng liên kết</h3>
            {c.linkedShipments.length === 0 ? (
              <p className="text-[14px] text-slate-500">Chưa liên kết lô nào.</p>
            ) : (
              <div className="space-y-2">
                {c.linkedShipments.map((s) => (
                  <div key={s.id} className="flex items-center gap-2.5 rounded-xl border border-slate-200 p-3">
                    <span className="w-9 h-9 rounded-lg bg-blue-100 text-blue-700 grid place-items-center"><Package size={18} /></span>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-[14.5px] text-[#0f2a4a]">{s.id}</p>
                      <p className="text-[12.5px] text-slate-500">{s.customer} · {s.status}</p>
                    </div>
                    <Link to={s.to} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]">MỞ <ArrowRight size={15} /></Link>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Liên kết lô mới</h3>
            {unlinkedShipments.length === 0 ? (
              <p className="text-[14px] text-slate-500">Tất cả lô đã được liên kết.</p>
            ) : (
              <div className="grid gap-3">
                <Field label="Chọn lô hàng" required>
                  <select value={linkShipmentId} onChange={(e) => setLinkShipmentId(e.target.value)} className={inputCls(!linkShipmentId ? "missing" : "ok")}>
                    <option value="">-- Chọn lô --</option>
                    {unlinkedShipments.map((s) => <option key={s.id} value={s.id}>{s.id} · {s.customer}</option>)}
                  </select>
                </Field>
                <PrimaryBtn onClick={linkShipment} className="w-full">🔗 LIÊN KẾT LÔ</PrimaryBtn>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
