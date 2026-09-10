import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Building2, CheckCircle2, CircleAlert, Download, Eye, FileText, MapPin, PenLine, Phone, Truck, Wallet, Package, FileDown, Clock } from "lucide-react";
import { Field, GhostBtn, MissingBox, NextActionBanner, PrimaryBtn, SectionTitle, StateRow, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { fmtMoney, fmtVND, fmtNum, fmtText, fmtCcy, fmtMillionsCcy, fmtPct, cx } from "../lib/format";

const TABS = [
  { id: "lay-hang", label: "Lấy hàng & Xuất khẩu", short: "Lấy hàng" },
  { id: "nhap", label: "Nhập khẩu & Giao hàng", short: "Nhập & Giao" },
  { id: "tai-chinh", label: "Tài chính / Công nợ", short: "Tài chính" },
  { id: "chung-tu", label: "Chứng từ & PXK", short: "Chứng từ" },
  { id: "lich-su", label: "Lịch sử", short: "Lịch sử" },
];

export default function ShipmentDetail() {
  const { id } = useParams();
  const [sp, setSp] = useSearchParams();
  const tab = sp.get("tab") || "lay-hang";
  const { shipments, updateShipment, toast, contracts, dispatch } = useStore();
  const nav = useNavigate();
  const s = shipments.find((x) => x.id === id);
  const [showPay, setShowPay] = useState(false);
  const [showDeliver, setShowDeliver] = useState(false);
  const [payAmt, setPayAmt] = useState("");
  const [payKind, setPayKind] = useState("Thu tiền khách");
  const [partnerAmt, setPartnerAmt] = useState("");
  const [lineForm, setLineForm] = useState({ name: "", qty: "1", price: "", cost: "", vat: "8" });
  const [form, setForm] = useState<Record<string, string>>({});
  const [savedTick, setSavedTick] = useState(0);

  useEffect(() => { setForm({}); setLineForm({ name: "", qty: "1", price: "", cost: "", vat: "8" }); setPartnerAmt(""); }, [id, tab]);
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const val = (k: string, fb: string) => form[k] ?? fb;

  const linkedContract = useMemo(() => contracts.find((c) => c.id === s?.contract), [contracts, s]);

  if (!s) return <div className="rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto"><p className="font-extrabold text-[19px]">Không tìm thấy lô {id}</p><p className="text-slate-500 mt-1 text-[15px]">Mã lô có thể sai. Về danh sách để tìm lại.</p><Link to="/lo-hang" className="btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center">Về danh sách lô</Link></div>;

  // The ONE authoritative currency of this shipment (shipments.currency →
  // data["3.4"].currency). The backend has no FX engine, so every amount is
  // labelled with this code and amounts of different currencies are never
  // summed. The "VND" fallback mirrors core.logic's own default.
  const ccy = s.finance.currency || "VND";

  // -----------------------------------------------------------------------
  // Phase B write contract: every save is ONE typed event → the single Python
  // dispatcher → RBAC → existing writer → audit → fresh backend read. The UI
  // is then refreshed from the backend; nothing here mutates business state.
  // -----------------------------------------------------------------------
  /**
   * Keep only the fields the operator actually filled. Keys are the canonical
   * shipment paths; values are already resolved by `val()`. Blank stays absent
   * so an UNKNOWN value is never written as an empty/zero fact.
   */
  const onlyFilled = (resolved: Record<string, string | null | undefined>) => {
    const out: Record<string, string> = {};
    for (const [key, value] of Object.entries(resolved)) {
      const next = (value ?? "").trim();
      if (next.length > 0) out[key] = next;
    }
    return out;
  };

  const afterSave = (label: string) => {
    setForm({});
    setSavedTick(Date.now());
    toast(label, "Đã gửi tới backend. Dữ liệu sẽ được đọc lại từ Logistics sau khi ghi.", "green");
  };

  const savePickup = () => {
    const fields = onlyFilled({
      container_no: val("plate", s.pickup.plate),
      etd: val("pickupTime", s.pickup.pickupTime),
      booking_no: val("bookingNo", s.transport?.bookingNo ?? ""),
      carrier: val("carrier", s.transport?.carrier ?? ""),
      pol: val("pol", s.transport?.pol ?? ""),
      pod: val("pod", s.transport?.pod ?? ""),
      qty_pkg: val("qtyPkg", s.transport?.qtyPkg ?? ""),
    });
    if (Object.keys(fields).length === 0) {
      toast("Chưa có gì để lưu", "Nhập ít nhất một trường ở tab Lấy hàng & Xuất khẩu.", "red");
      return;
    }
    dispatch("shipment_field_save", { shipmentId: s.id, fields });
    afterSave("Đã lưu thông tin lấy hàng " + s.id);
  };

  const saveImport = () => {
    const tk = val("tk", s.importInfo.declarationNo);
    if (!tk) { toast("Chưa thể lưu thông quan", "Thiếu: Số tờ khai nhập khẩu — nhập số TK (12 số) rồi bấm Lưu.", "red"); return; }
    // Import tax / VAT are not modelled on the shipment document, so they are
    // never sent (UNKNOWN must not be written as a number).
    const fields: Record<string, string> = {
      tk_no: tk,
      ...onlyFilled({
        phan_luong: val("inspection", s.importInfo.inspection),
        arrival_date: val("arrivalDate", s.importInfo.arrivalDate ?? ""),
        free_time: val("freeTime", s.importInfo.freeTime != null ? String(s.importInfo.freeTime) : ""),
        truck_no: val("plateVN", s.importInfo.plateVN),
        seal_no: val("driverVN", s.importInfo.driverVN),
      }),
    };
    dispatch("shipment_field_save", { shipmentId: s.id, fields });
    afterSave("Đã lưu tờ khai " + tk);
  };

  const confirmDelivery = () => {
    const sent = dispatch("delivery_confirm", {
      shipmentId: s.id,
      deliveredAt: new Date().toISOString().slice(0, 10),
      receiverName: s.importInfo.receiver,
      receiverTitle: s.importInfo.receiverTitle ?? "",
      receiverPhone: s.importInfo.receiverPhone,
      deliveryLocation: s.importInfo.deliveryLocation || s.importInfo.deliveryAddr,
    });
    setShowDeliver(false);
    if (sent) toast("Đã gửi xác nhận giao hàng " + s.id, "Backend ghi nhận + audit; PXK sẽ mở ở tab Chứng từ.", "green");
    else toast("Không gửi được", "Component chưa kết nối backend.", "red");
  };

  // Stable request identity per PAYMENT INTENT.
  //
  // The identity is minted when the payment sheet is opened and then held for
  // that one intent, so a re-render or a double click replays the SAME id and
  // the backend's request registry treats it as one idempotent request. It is
  // deliberately NOT derived from shipmentId|amount|kind: that made a second
  // genuine receipt of the same amount and kind replay the first request and
  // never post. Idempotency is scoped to the request, not to the amount.
  const payRequestRef = useRef("");
  const openPay = () => {
    payRequestRef.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
    setShowPay(true);
  };
  const recordPay = () => {
    const amt = Number(payAmt.replace(/\D/g, ""));
    if (!amt) { toast("Chưa nhập số tiền", `Nhập số tiền ${ccy} rồi bấm Lưu — ví dụ 50.000.000.`, "red"); return; }
    const sent = dispatch("payment_record", {
      shipmentId: s.id,
      amount: amt,
      requestId: payRequestRef.current,
      date: new Date().toISOString().slice(0, 10),
      note: payKind,
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    setShowPay(false); setPayAmt("");
    toast("Đã gửi khoản thu " + fmtCcy(amt, ccy), "Ghi qua save_direct_shipment_payment với request identity — gửi lại cùng intent sẽ không nhân đôi.", "green");
  };

  // C2B — partner payable / payment to partner. SAME contract as receipts:
  // one stable request identity per PAYABLE/PAYMENT INTENT, minted with the
  // amount draft and held until the operator changes it, so a double click
  // replays the SAME id and the canonical action registry absorbs it. A new
  // genuine intent (new amount draft) mints a new id and stays distinct.
  const partnerOblRef = useRef("");
  const partnerPayRef = useRef("");
  const newPartnerIntent = (prefix: string) =>
    `${prefix}-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
  const mintPartnerObl = () => { partnerOblRef.current = newPartnerIntent("POBL"); };
  const mintPartnerPay = () => { partnerPayRef.current = newPartnerIntent("PPAY"); };
  const recordPartnerPayable = () => {
    const partner = s.finance.partner;
    if (!partner?.partnerId) { toast("Chưa chọn đối tác", "Chưa có đối tác trong danh mục để ghi nhận phải trả.", "red"); return; }
    const amt = Number(partnerAmt.replace(/\D/g, ""));
    if (!amt) { toast("Chưa nhập số tiền", `Nhập số tiền phải trả ${ccy} — ví dụ 57.000.000.`, "red"); return; }
    if (!partnerOblRef.current) mintPartnerObl();
    const sent = dispatch("partner_payable_record", {
      shipmentId: s.id,
      partnerId: partner.partnerId,
      amount: amt,
      currency: ccy,
      requestId: partnerOblRef.current,
      note: "Phải trả chi phí đối tác theo thực tế lô",
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    setPartnerAmt("");
    toast("Đã gửi phải trả đối tác " + fmtCcy(amt, ccy), "Ghi qua canonical ledger (obligation) với request identity — gửi lại cùng intent sẽ không nhân đôi.", "green");
  };
  const recordPartnerPayment = () => {
    const partner = s.finance.partner;
    if (!partner?.partnerId) { toast("Chưa chọn đối tác", "Chưa có đối tác để thanh toán — ghi nhận phải trả trước.", "red"); return; }
    const amt = Number(partnerAmt.replace(/\D/g, ""));
    if (!amt) { toast("Chưa nhập số tiền", `Nhập số tiền thanh toán ${ccy} — ví dụ 20.000.000.`, "red"); return; }
    if (!partnerPayRef.current) mintPartnerPay();
    const sent = dispatch("partner_payment_record", {
      shipmentId: s.id,
      partnerId: partner.partnerId,
      amount: amt,
      currency: ccy,
      requestId: partnerPayRef.current,
      date: new Date().toISOString().slice(0, 10),
      note: "Chuyển khoản thanh toán đối tác",
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    setPartnerAmt("");
    toast("Đã gửi thanh toán đối tác " + fmtCcy(amt, ccy), "Ghi qua canonical ledger (transaction + allocation) — backend sẽ đọc lại còn phải trả.", "green");
  };

  // FINANCE ACTUAL — one booked service line in data["3.4"].details, saved
  // through the canonical writer. Quote Estimate is never touched here.
  const lineSet = (k: keyof typeof lineForm, v: string) => setLineForm((f) => ({ ...f, [k]: v }));
  const saveActualLine = () => {
    if (!lineForm.name.trim()) { toast("Thiếu tên dịch vụ", "Nhập tên dòng thực tế — ví dụ: Cước xe TQ.", "red"); return; }
    const sent = dispatch("finance_actual_save", {
      shipmentId: s.id,
      line: {
        name: lineForm.name.trim(),
        qty: lineForm.qty,
        price: lineForm.price,
        cost: lineForm.cost,
        vat: lineForm.vat,
      },
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    toast("Đã gửi dòng thực tế", "Ghi vào data['3.4'].details rồi core.logic tính lại phải thu / chi phí / lợi nhuận.", "green");
    setLineForm({ name: "", qty: "1", price: "", cost: "", vat: "8" });
  };

  const exportPXK = () => {
    // Real docgen path only. Phase B removed the prototype .txt export.
    const sent = dispatch("pxk_generate", { shipmentId: s.id });
    if (sent) toast("Đã gửi yêu cầu xuất PXK", "core.docgen kiểm tra gate giao hàng rồi sinh file Office thật.", "blue");
    else toast("Không gửi được", "Component chưa kết nối backend.", "red");
  };

  // `missingDocs` is already the not-ok subset of `docs`; counting both
  // double-counted the same facts (chip said 8 while the box listed 4).
  // The document checklist emits real Logistics fact names; route each to the
  // tab that actually owns that field (Phase B labels, not Phase A wording).
  const missingTarget = (m: string): string => {
    if (/tờ khai|thông quan|xe giao|giao hàng/i.test(m)) return "nhap";
    if (/lấy hàng|xe TQ|biển số|packing|container/i.test(m)) return "lay-hang";
    if (/chứng từ|PXK|HDMB|PL$/i.test(m)) return "chung-tu";
    return "nhap";
  };

  const missingCount = s.missingDocs.length;

  return (
    <div className="space-y-4 max-w-[1300px]">
      <button onClick={() => nav(-1)} className="touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]"><ArrowLeft size={17} /> Quay lại</button>

      {/* HEADER */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" />
        <div className="p-4 md:p-6">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-[22px] md:text-[26px] font-extrabold text-[#0f2a4a]">{s.id}</h1>
            <ToneBadge tone={s.statusTone}>{s.status}</ToneBadge>
            {missingCount > 0 && <span className="inline-flex items-center gap-1.5 text-[13px] font-bold bg-red-50 text-red-700 border border-red-200 rounded-full px-3 py-1.5"><CircleAlert size={15} /> Thiếu {missingCount} thông tin</span>}
            <span className="ml-auto text-[12.5px] text-slate-400 flex items-center gap-1"><Clock size={14} /> Cập nhật {s.updated}</span>
          </div>
          <p className="font-semibold text-[15.5px] mt-1">{s.customer} <span className="text-slate-400 font-normal">· MST {s.customerMST}</span></p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 mt-3">
            <StateRow label="Tuyến" value={s.route} />
            <StateRow label="Cửa khẩu" value={s.borderVN} />
            <StateRow label="Hợp đồng" value={<Link to={"/hop-dong/" + s.contract} className="text-[#1e5aa8] font-bold hover:underline">{s.contract}</Link>} />
            <StateRow label="Sale · Support" value={<span>{s.sale} · {s.support}</span>} />
          </div>
        </div>
        <div className="px-4 md:px-6 pb-4 md:pb-5">
          <NextActionBanner tone={s.statusTone === "green" ? "green" : s.priority === "Khan" ? "red" : "amber"} title={s.nextAction} desc={s.nextActionDetail} action={s.nextLabel} onAction={() => { const t = sp.get("tab"); if (s.nextRoute.startsWith("/lo-hang")) { const m = s.nextRoute.match(/tab=(\w+)/); setSp(m ? { tab: m[1] } : {}); document.getElementById("workspace-tabs")?.scrollIntoView({ behavior: "smooth" }); } else nav(s.nextRoute); }} />
        </div>
        {/* TABS */}
        <div id="workspace-tabs" className="px-3 md:px-6 pb-3 flex gap-2 overflow-x-auto no-scrollbar border-t border-slate-100 pt-3">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setSp({ tab: t.id })} className={cx("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14.5px] font-bold border-2 whitespace-nowrap", tab === t.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-600")}>
              <span className="hidden md:inline">{t.label}</span><span className="md:hidden">{t.short}</span>
            </button>
          ))}
        </div>
      </div>

      {s.missingDocs.length > 0 && tab !== "chung-tu" && (
        <div className="rounded-2xl bg-white border-2 border-red-200 p-4">
          <p className="font-extrabold text-[15px] text-red-800 flex items-center gap-2 mb-2.5"><CircleAlert size={18} /> Đang thiếu {s.missingDocs.length} thông tin — bấm để bổ sung ngay:</p>
          <div className="grid gap-2 md:grid-cols-2">
            {s.missingDocs.map((m) => (
              <MissingBox key={m} what={m} actionLabel="Bổ sung ngay" onAction={() => { setSp({ tab: missingTarget(m) }); setTimeout(() => document.getElementById("missing-anchor")?.scrollIntoView({ behavior: "smooth", block: "center" }), 150); }} />
            ))}
          </div>
        </div>
      )}

      {/* ============ TAB: PICKUP ============ */}
      {tab === "lay-hang" && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4" id="missing-anchor">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><MapPin size={19} className="text-[#1e5aa8]" /> Nhà máy & lịch lấy hàng</h3>
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-3.5">
              <p className="font-bold text-[15px]">{s.pickup.factory}</p>
              <p className="text-[13.5px] text-slate-500">{s.pickup.address}</p>
              <p className="text-[14px] mt-1.5 flex items-center gap-1.5"><Phone size={15} className="text-slate-400" /> {s.pickup.contact} · {s.pickup.phone}</p>
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Thời gian lấy hàng" required={!s.pickup.pickupTime} error={!val("pickupTime", s.pickup.pickupTime) ? "Thiếu giờ lấy — nhà máy cần báo trước 24h" : undefined}>
                <input value={val("pickupTime", s.pickup.pickupTime)} onChange={(e) => set("pickupTime", e.target.value)} placeholder="VD: 10/09/2026 09:00" className={inputCls(!val("pickupTime", s.pickup.pickupTime) ? "missing" : "ok")} />
              </Field>
              <Field label="Loại / kích thước xe"><input defaultValue={s.pickup.truckType} className={inputCls()} /></Field>
            </div>
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 pt-1"><Truck size={19} className="text-[#1e5aa8]" /> Xe Trung Quốc</h3>
            {(!s.pickup.plate || !s.pickup.driver) && <MissingBox what="biển số + tài xế xe TQ" where="Chưa đặt được xe — bổ sung để nhà máy cho hàng lên xe" actionLabel="Nhập xe ngay" onAction={() => document.getElementById("fld-plate")?.focus()} />}
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Biển số xe" required={!s.pickup.plate}><input id="fld-plate" value={val("plate", s.pickup.plate)} onChange={(e) => set("plate", e.target.value)} placeholder="VD: 粤A·88T36" className={inputCls(!val("plate", s.pickup.plate) ? "missing" : "ok")} /></Field>
              <Field label="Tài xế" required={!s.pickup.driver}><input value={val("driver", s.pickup.driver)} onChange={(e) => set("driver", e.target.value)} placeholder="Tên tài xế" className={inputCls(!val("driver", s.pickup.driver) ? "missing" : "ok")} /></Field>
              <Field label="SĐT tài xế"><input value={val("driverPhone", s.pickup.driverPhone)} onChange={(e) => set("driverPhone", e.target.value)} placeholder="+86…" className={inputCls()} /></Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Ngày dự kiến"><input defaultValue={s.pickup.eta} className={inputCls()} /></Field>
                <Field label="Ngày thực tế"><input defaultValue={s.pickup.ata} placeholder="—" className={inputCls()} /></Field>
              </div>
            </div>
            <PrimaryBtn onClick={savePickup} className="w-full">💾 LƯU THÔNG TIN LẤY HÀNG</PrimaryBtn>
          </section>

          <div className="space-y-4">
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3"><Package size={19} className="text-[#1e5aa8]" /> Hàng hóa</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[["Số kiện / GW", fmtText(s.cargo.qtyPkg)], ["Số kiện", fmtNum(s.cargo.packs)], ["CBM", fmtNum(s.cargo.cbm)], ["Kích thước", fmtText(s.cargo.dims)], ["Loại hàng", fmtText(s.cargo.type)]].map(([k, v]) => (
                  <div key={k} className="rounded-xl bg-slate-50 border border-slate-200 p-3"><p className="text-[12px] font-bold uppercase tracking-wide text-slate-400">{k}</p><p className="font-bold text-[15px] text-[#0f2a4a] mt-0.5">{v}</p></div>
                ))}
              </div>
              {s.cargo.note && <p className="mt-2.5 text-[13.5px] bg-amber-50 border border-amber-200 rounded-xl p-3">📌 Ghi chú: {s.cargo.note}</p>}
            </section>
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Xuất khẩu — {s.exportInfo.border}</h3>
              <StateRow label="Đơn vị khai" value={s.exportInfo.declarant} />
              <StateRow label="Ngày dự kiến / thực tế" value={<span>{s.exportInfo.eta || "—"} / {s.exportInfo.ata || "chưa có"}</span>} />
              <StateRow label="Trạng thái" value={<ToneBadge tone={s.exportInfo.state.includes("Đã") ? "green" : "amber"} size="sm">{s.exportInfo.state}</ToneBadge>} />
            </section>
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-1">Checklist chứng từ xuất khẩu</h3>
              <p className="text-[13px] text-slate-500 mb-3">Hiện trạng → thiếu gì → bấm để bổ sung. Không có cảnh báo cụt.</p>
              <div className="space-y-2">
                {s.docs.map((d) => (
                  <div key={d.name} className={cx("flex items-center gap-3 rounded-xl border-2 p-3", d.ok ? "border-emerald-200 bg-emerald-50/60" : "border-amber-300 bg-amber-50")}>
                    <span className={cx("w-8 h-8 rounded-full grid place-items-center font-extrabold shrink-0", d.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white")}>{d.ok ? "✓" : "!"}</span>
                    <div className="flex-1 min-w-0"><p className="font-bold text-[14.5px]">{d.name} — {d.ok ? <span className="text-emerald-700">✅ Đủ</span> : <span className="text-amber-800">Thiếu</span>}</p>{d.note && <p className="text-[13px] text-slate-600">{d.note}</p>}</div>
                    {!d.ok && <button onClick={() => { setSp({ tab: "chung-tu" }); toast("Mở tab Chứng từ", "Tải file " + d.name + " lên hoặc ghi chú lý do thiếu.", "blue"); }} className="btn-press touch-target shrink-0 inline-flex items-center gap-1 rounded-lg bg-amber-500 text-white text-[13.5px] font-bold px-3 min-h-[44px]"><PenLine size={14} /> Bổ sung</button>}
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      )}

      {/* ============ TAB: IMPORT ============ */}
      {tab === "nhap" && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4" id="missing-anchor">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Tờ khai & thuế nhập khẩu — {s.importInfo.borderVN}</h3>
            {!val("tk", s.importInfo.declarationNo) && <MissingBox what="số tờ khai nhập khẩu" where="Hàng đang chờ ở bãi VN — có số TK mới nộp thuế & phân luồng được" actionLabel="Nhập số TK" onAction={() => document.getElementById("fld-tk")?.focus()} />}
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Số tờ khai" required={!s.importInfo.declarationNo} error={!val("tk", s.importInfo.declarationNo) ? "Nhập 12 số tờ khai — VD: 105588421330" : undefined}>
                <input id="fld-tk" value={val("tk", s.importInfo.declarationNo)} onChange={(e) => set("tk", e.target.value)} placeholder="12 số tờ khai…" className={inputCls(!val("tk", s.importInfo.declarationNo) ? "missing" : "ok")} />
              </Field>
              <Field label="Ngày đăng ký"><input value={val("regDate", s.importInfo.regDate)} onChange={(e) => set("regDate", e.target.value)} placeholder="VD: 09/09/2026" className={inputCls()} /></Field>
              <Field label="Thuế nhập khẩu (VND)"><input value={s.importInfo.tax == null ? "" : String(s.importInfo.tax)} readOnly placeholder="Chưa có dữ liệu — theo dõi ở GNT" className={inputCls()} /></Field>
              <Field label="VAT hàng nhập (VND)"><input value={s.importInfo.vat == null ? "" : String(s.importInfo.vat)} readOnly placeholder="Chưa có dữ liệu — theo dõi ở GNT" className={inputCls()} /></Field>
              <Field label="Phân luồng / kiểm hóa"><input value={val("inspection", s.importInfo.inspection)} onChange={(e) => set("inspection", e.target.value)} className={inputCls()} /></Field>
              <Field label="Giấy phép chuyên ngành"><input defaultValue={s.importInfo.license} className={inputCls()} /></Field>
            </div>
            <PrimaryBtn onClick={saveImport} className="w-full">💾 LƯU TỜ KHAI & THUẾ</PrimaryBtn>
            {val("tk", s.importInfo.declarationNo) && <div className="rounded-xl bg-blue-50 border border-blue-200 p-3 text-[13.5px] text-blue-900">✅ Đã có số TK <b>{val("tk", s.importInfo.declarationNo)}</b>. Tiếp theo: nộp thuế rồi bấm “Thông quan” khi có kết quả phân luồng.</div>}
          </section>

          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><Truck size={19} className="text-[#1e5aa8]" /> Xe Việt Nam & giao hàng</h3>
            {(!s.importInfo.driverVN || !s.importInfo.plateVN) && !s.importInfo.delivered && <MissingBox what="xe VN + tài xế" where="Chưa đặt xe — đặt trước giờ giao ít nhất 4 tiếng" actionLabel="Đặt xe ngay" onAction={() => document.getElementById("fld-platevn")?.focus()} />}
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Loại xe VN"><input defaultValue={s.importInfo.truckVN} className={inputCls()} /></Field>
              <Field label="Biển số VN"><input id="fld-platevn" value={val("plateVN", s.importInfo.plateVN)} onChange={(e) => set("plateVN", e.target.value)} placeholder="VD: 29H-481.36" className={inputCls(!val("plateVN", s.importInfo.plateVN) ? "missing" : "ok")} /></Field>
              <Field label="Tài xế VN"><input value={val("driverVN", s.importInfo.driverVN)} onChange={(e) => set("driverVN", e.target.value)} placeholder="Tên tài xế" className={inputCls()} /></Field>
              <Field label="Lịch giao"><input defaultValue={s.importInfo.schedule} className={inputCls()} /></Field>
            </div>
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-3.5">
              <p className="text-[12.5px] font-bold uppercase tracking-wide text-slate-400">Địa chỉ giao</p>
              <p className="font-bold text-[15px] mt-0.5">{s.importInfo.deliveryAddr}</p>
              <p className="text-[14px] text-slate-600 mt-1">Người nhận: <b>{s.importInfo.receiver}</b> · {s.importInfo.receiverPhone}</p>
              {s.importInfo.actualDelivery && <p className="text-[14px] text-emerald-700 font-bold mt-1">✅ Đã giao: {s.importInfo.actualDelivery}</p>}
            </div>
            {s.importInfo.delivered ? (
              <div className="rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center">
                <p className="font-extrabold text-[17px] text-emerald-800">✅ ĐÃ GIAO HÀNG XONG</p>
                <p className="text-[13.5px] text-emerald-700">{s.importInfo.actualDelivery} · Sang tab Chứng từ để xuất PXK →</p>
                <button onClick={() => setSp({ tab: "chung-tu" })} className="btn-press touch-target mt-2.5 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]">SANG XUẤT PHIẾU XUẤT KHO <ArrowRight size={17} /></button>
              </div>
            ) : (
              <SuccessBtn onClick={() => setShowDeliver(true)} className="w-full text-[17px] min-h-[56px]">✅ XÁC NHẬN ĐÃ GIAO HÀNG</SuccessBtn>
            )}
          </section>
        </div>
      )}

      {/* ============ TAB: FINANCE ============ */}
      {tab === "tai-chinh" && (
        <div className="space-y-4" id="missing-anchor">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <section className="rounded-2xl bg-white border-2 border-dashed border-violet-300 p-4 md:p-5">
              <p className="text-[12px] font-extrabold uppercase tracking-wider text-violet-600 bg-violet-100 inline-block rounded-md px-2 py-0.5">Báo giá / Dự kiến — chưa phải số thực thu/chi</p>
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mt-2 mb-2">Chi phí dự kiến theo báo giá</h3>
              {s.finance.quote.length === 0 && <p className="text-[14px] text-slate-500">Chưa gắn báo giá. <Link to="/kinh-doanh-bao-gia" className="font-bold text-[#1e5aa8]">Mở báo giá →</Link></p>}
              {s.finance.quote.map((c) => (<StateRow key={c.label} label={c.label} value={<span className="font-bold text-[16px]">{fmtMoney(c.amount, c.ccy)} <span className="text-[12px] font-bold text-violet-600">{c.ccy}</span></span>} />))}
              <p className="text-[12.5px] text-slate-400 mt-2">Mỗi đồng tiền ghi rõ VND / USD / CNY — không gộp chung.</p>
            </section>
            <section className="rounded-2xl bg-white border-2 border-emerald-300 p-4 md:p-5">
              <p className="text-[12px] font-extrabold uppercase tracking-wider text-emerald-700 bg-emerald-100 inline-block rounded-md px-2 py-0.5">Thực tế — đã phát sinh, có chứng từ</p>
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mt-2 mb-2">Doanh thu &amp; chi phí thực tế ({ccy})</h3>
              {s.finance.actual.length === 0 && (
                <p className="text-[14px] text-slate-500">Chưa ghi nhận dòng thực tế nào — doanh thu / chi phí / lợi nhuận thực tế đang <b>chưa xác định</b>, không phải 0.</p>
              )}
              {s.finance.actual.map((c, i) => (
                <div key={`${c.label}-${i}`} className="py-2 border-b border-slate-100 last:border-0">
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-[13.5px] text-slate-500 font-medium pt-0.5">{c.label}</span>
                    <span className="text-right font-semibold text-slate-800 text-[14.5px]">
                      <span className="font-bold text-[16px]">{fmtCcy(c.amount, c.ccy)}</span>
                    </span>
                  </div>
                  <p className="text-[12.5px] text-slate-400 mt-0.5 text-right">
                    Chi phí {fmtCcy(c.cost, c.ccy)}{c.qty != null ? ` · SL ${fmtNum(c.qty)}` : ""}{c.vat != null ? ` · VAT ${fmtNum(c.vat)}%` : ""}
                  </p>
                </div>
              ))}
              <StateRow label="Doanh thu thực tế (chưa VAT)" value={<span className="font-bold">{fmtCcy(s.finance.receivableNet, ccy)}</span>} />
              <StateRow label="Chi phí thực tế" value={<span className="font-bold">{fmtCcy(s.finance.payable, ccy)}</span>} />
              {/* ACTUAL PROFIT — from booked actuals only. Never from the quote. */}
              <div className="mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-3">
                <p className="text-[12px] font-extrabold uppercase tracking-wider text-emerald-700">Lợi nhuận thực tế</p>
                <div className="grid grid-cols-2 gap-2 mt-1.5 text-center">
                  <div><p className="text-[12px] text-slate-500 font-semibold">Lãi / Lỗ thực tế</p>
                    <p className={cx("font-extrabold text-[17px]", s.finance.profit == null ? "text-slate-400" : s.finance.profit < 0 ? "text-red-700" : "text-emerald-700")}>{fmtCcy(s.finance.profit, ccy)}</p></div>
                  <div><p className="text-[12px] text-slate-500 font-semibold">Biên lợi nhuận</p>
                    <p className={cx("font-extrabold text-[17px]", s.finance.profitMargin == null ? "text-slate-400" : s.finance.profitMargin < 0 ? "text-red-700" : "text-emerald-700")}>{fmtPct(s.finance.profitMargin)}</p></div>
                </div>
                <p className="text-[12.5px] text-slate-500 mt-2">
                  = Doanh thu thực tế − chi phí thực tế − hoa hồng. Không gồm VAT đầu ra. Không lấy số báo giá để bù chỗ trống.
                </p>
              </div>
              {/* One booked actual service line → the canonical writer. */}
              <div className="mt-3 rounded-xl border border-slate-200 p-3">
                <p className="text-[13px] font-extrabold text-[#0f2a4a] mb-2">Ghi nhận dòng thực tế</p>
                <div className="grid gap-2.5">
                  <Field label="Dịch vụ" required error={!lineForm.name.trim() ? "Nhập tên dịch vụ" : undefined}>
                    <input value={lineForm.name} onChange={(e) => lineSet("name", e.target.value)} placeholder="VD: Cước xe TQ Đông Bằng → Hữu Nghị" className={inputCls(!lineForm.name.trim() ? "missing" : "ok")} />
                  </Field>
                  <div className="grid grid-cols-2 gap-2.5">
                    <Field label={`Giá bán (${ccy})`}><input value={lineForm.price} onChange={(e) => lineSet("price", e.target.value)} inputMode="numeric" placeholder="VD: 62000000" className={inputCls()} /></Field>
                    <Field label={`Chi phí (${ccy})`}><input value={lineForm.cost} onChange={(e) => lineSet("cost", e.target.value)} inputMode="numeric" placeholder="VD: 57000000" className={inputCls()} /></Field>
                  </div>
                  <div className="grid grid-cols-2 gap-2.5">
                    <Field label="Số lượng"><input value={lineForm.qty} onChange={(e) => lineSet("qty", e.target.value)} inputMode="numeric" placeholder="VD: 1" className={inputCls()} /></Field>
                    <Field label="VAT %" hint="Bỏ trống = chưa xác định"><input value={lineForm.vat} onChange={(e) => lineSet("vat", e.target.value)} inputMode="decimal" placeholder="VD: 8" className={inputCls()} /></Field>
                  </div>
                </div>
                <PrimaryBtn onClick={saveActualLine} className="mt-3 w-full">💾 LƯU DÒNG THỰC TẾ</PrimaryBtn>
              </div>
            </section>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-2"><Wallet size={19} className="text-emerald-600" /> Phải thu khách hàng ({ccy})</h3>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl bg-slate-50 border p-3"><p className="text-[12px] text-slate-500 font-semibold">Phải thu</p><p className="font-extrabold text-[16px] md:text-[18px]">{fmtMillionsCcy(s.finance.receivable, ccy)}</p></div>
                <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3"><p className="text-[12px] text-emerald-700 font-semibold">Đã thu</p><p className="font-extrabold text-[16px] md:text-[18px] text-emerald-700">{fmtMillionsCcy(s.finance.received, ccy)}</p></div>
                <div className="rounded-xl bg-red-50 border border-red-200 p-3"><p className="text-[12px] text-red-600 font-semibold">Còn phải thu</p><p className="font-extrabold text-[16px] md:text-[18px] text-red-700">{fmtMillionsCcy(s.finance.outstanding, ccy)}</p></div>
              </div>
              <p className="text-[12.5px] text-slate-400 mt-2">Phải thu = doanh thu thực tế + VAT đầu ra. Còn phải thu = phải thu − đã thu, do backend tính.</p>
              <button onClick={openPay} className="btn-press touch-target mt-3 w-full rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">＋ GHI NHẬN THANH TOÁN</button>
            </section>
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-2">Phải trả đối tác ({ccy})</h3>
              {/* C2B — the selected partner + payable/paid/remaining come from the
                  canonical ledger block (finance.partner), never from client math.
                  UNKNOWN stays “—”; a true zero from the ledger stays 0. */}
              {(() => {
                const partner = s.finance.partner;
                const partnerId = partner?.partnerId ?? "";
                const partnerName = partner?.partnerName;
                const suggested = partner?.suggested === true;
                return (
                  <>
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="text-[12px] text-slate-500 font-semibold">Đối tác:</span>
                      {partnerName ? (
                        <span className="inline-flex items-center gap-1.5 text-[13.5px] font-extrabold text-[#0f2a4a]">
                          <Building2 size={15} className="text-[#1e5aa8]" /> {partnerName}
                          <span className="text-[11.5px] font-bold text-slate-400">{partnerId}</span>
                          {suggested && <span className="text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">đề xuất từ danh mục</span>}
                        </span>
                      ) : (
                        <span className="text-[13.5px] font-bold text-slate-400">—</span>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="rounded-xl bg-slate-50 border p-3"><p className="text-[12px] text-slate-500 font-semibold">Phải trả</p><p className="font-extrabold text-[16px] md:text-[18px]">{fmtMillionsCcy(partner?.payable ?? null, ccy)}</p></div>
                      <div className="rounded-xl bg-blue-50 border border-blue-200 p-3"><p className="text-[12px] text-blue-700 font-semibold">Đã trả</p><p className="font-extrabold text-[16px] md:text-[18px] text-blue-700">{fmtMillionsCcy(partner?.paid ?? null, ccy)}</p></div>
                      <div className="rounded-xl bg-amber-50 border border-amber-200 p-3"><p className="text-[12px] text-amber-700 font-semibold">Còn phải trả</p><p className="font-extrabold text-[16px] md:text-[18px] text-amber-800">{fmtMillionsCcy(partner?.remaining ?? null, ccy)}</p></div>
                    </div>
                  </>
                );
              })()}
              {/* UNKNOWN != ZERO: before any canonical payable/payment record the
                  figures above stay an em dash — they are never shown as 0. Once
                  the ledger has rows, mọi số đều do backend đọc ra. */}
              <p className="text-[12.5px] text-slate-400 mt-2">Phải trả / đã trả / còn lại đọc từ sổ tài chính canonical (nghĩa vụ + thanh toán + phân bổ) theo lô này. Chưa có sổ ⇒ “—”, không suy ra 0. Đơn vị: {ccy} — không quy đổi.</p>

              {/* Payment history — canonical transactions bound to this shipment. */}
              {(s.finance.partner?.payments?.length ?? 0) > 0 && (
                <div className="mt-3">
                  <p className="text-[12px] font-extrabold uppercase tracking-wider text-slate-500 mb-1.5">Lịch sử trả đối tác</p>
                  <div className="space-y-1.5">
                    {s.finance.partner!.payments.map((p, i) => (
                      <div key={p.id || i} className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 p-2.5">
                        <span className="text-[12px] font-bold text-slate-400 w-[80px]">{p.date || "—"}</span>
                        <span className="flex-1 min-w-[140px] text-[12.5px] text-slate-600">{p.note || p.kind}{p.requestId ? ` · ${p.requestId}` : ""}</span>
                        <span className="font-extrabold text-[14.5px]">{fmtMoney(p.amount, p.ccy)} <span className="text-[11px] text-slate-400">{p.ccy}</span></span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* C2B write actions — SAME typed-event contract as receipts:
                  typed event → Python dispatcher → RBAC → canonical writer →
                  audit → fresh backend read. Frontend visibility is NOT
                  authorization; a denied role only sees the backend's refusal.
                  The intent id is minted with the amount draft and held for that
                  one intent (re-click replays the SAME id → idempotent). */}
              <div className="mt-3 rounded-xl border border-slate-200 p-3">
                <p className="text-[13px] font-extrabold text-[#0f2a4a] mb-2">Ghi nhận phải trả & thanh toán đối tác</p>
                <Field label={`Số tiền (${ccy})`} hint="Ví dụ: 20.000.000 — để trống là UNKNOWN, không tự thành 0">
                  <input value={partnerAmt} onChange={(e) => { setPartnerAmt(e.target.value); mintPartnerObl(); mintPartnerPay(); }} inputMode="numeric" placeholder="VD: 20000000" className={inputCls()} />
                </Field>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2.5">
                  <GhostBtn onClick={recordPartnerPayable} className="min-h-[48px]">📌 GHI NHẬN PHẢI TRẢ</GhostBtn>
                  <PrimaryBtn onClick={recordPartnerPayment} className="min-h-[48px]">💸 TRẢ ĐỐI TÁC</PrimaryBtn>
                </div>
              </div>

              <Link to="/tai-chinh/doi-soat" className="btn-press touch-target mt-3 w-full rounded-xl border-2 border-slate-200 font-bold min-h-[52px] flex items-center justify-center">MỞ ĐỐI SOÁT</Link>
            </section>
          </div>
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Lịch sử thu / chi — sửa bằng điều chỉnh, không xóa</h3>
            <div className="space-y-2">
              {s.finance.payments.map((p, i) => (
                <div key={i} className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 p-3">
                  <span className="text-[12.5px] font-bold text-slate-400 w-[92px]">{p.date}</span>
                  <span className="flex-1 min-w-[160px]"><span className="block font-bold text-[14.5px]">{p.kind}</span><span className="block text-[12.5px] text-slate-500">{p.by}{p.note ? " · " + p.note : ""}</span></span>
                  <span className="font-extrabold text-[15.5px]">{fmtMoney(p.amount, p.ccy)} <span className="text-[11.5px] text-slate-400">{p.ccy}</span></span>
                  <button onClick={() => toast("Tạo bút toán điều chỉnh", "Nhập số điều chỉnh (+/-) thay vì xóa — giữ nguyên lịch sử kiểm toán.", "blue")} className="touch-target text-[13px] font-bold text-[#1e5aa8] border border-slate-200 rounded-lg px-3 min-h-[40px]">Điều chỉnh</button>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {/* ============ TAB: DOCS ============ */}
      {tab === "chung-tu" && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3"><FileText size={19} className="text-[#1e5aa8]" /> Hợp đồng liên kết</h3>
            {linkedContract ? (
              <div className="rounded-xl border-2 border-slate-200 p-4">
                <div className="flex flex-wrap items-center gap-2"><span className="font-extrabold text-[17px] text-[#0f2a4a]">{linkedContract.id}</span><ToneBadge tone={linkedContract.statusTone} size="sm">{linkedContract.status}</ToneBadge></div>
                <p className="text-[14px] text-slate-600 mt-1">{linkedContract.companyLegal} · Giá trị {fmtVND(linkedContract.value ?? s.finance.receivable)}</p>
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <Link to={"/hop-dong/" + linkedContract.id} className="btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] min-h-[48px]"><Eye size={16} /> MỞ HỢP ĐỒNG</Link>
                  <button onClick={() => { setSp({ tab: "chung-tu" }); toast("Chứng từ " + linkedContract.id, "Chứng từ được sinh bởi core.docgen (Office thật) ở tab Chứng từ & PXK.", "blue"); }} className="btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] min-h-[48px]"><FileDown size={16} /> MỞ CHỨNG TỪ</button>
                </div>
              </div>
            ) : <p className="text-slate-500 text-[14px]">Lô chưa gắn hợp đồng. <Link to="/hop-dong" className="font-bold text-[#1e5aa8]">Chọn hợp đồng →</Link></p>}
            <div className="mt-4">
              <h4 className="font-bold text-[14.5px] mb-2">Chứng từ lô hàng — bấm để tải / bổ sung</h4>
              <div className="space-y-2">
                {s.docs.map((d) => (
                  <div key={d.name} className="flex items-center gap-2.5 rounded-xl border border-slate-200 p-2.5">
                    <span className={cx("w-7 h-7 rounded-full grid place-items-center text-[13px] font-extrabold", d.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white")}>{d.ok ? "✓" : "!"}</span>
                    <span className="flex-1 font-semibold text-[14px]">{d.name}</span>
                    {d.ok ? <button onClick={() => toast("Đã tải " + d.name, "File minh họa của " + s.id + " đã lưu về máy.", "green")} className="touch-target inline-flex items-center gap-1 text-[13px] font-bold text-[#1e5aa8] border rounded-lg px-2.5 min-h-[40px]"><Download size={14} /> Tải</button>
                    : <button onClick={() => toast("Tải lên " + d.name, "Chọn file PDF/ảnh từ máy — prototype mô phỏng thao tác.", "blue")} className="touch-target inline-flex items-center gap-1 text-[13px] font-bold text-white bg-amber-500 rounded-lg px-2.5 min-h-[40px]">＋ Bổ sung</button>}
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-1">Phiếu xuất kho (PXK) — theo từng lô</h3>
            <p className="text-[13px] text-slate-500 mb-3">PXK gắn với lô đã giao, nguồn từ {s.pxk.source || s.contract}. Mỗi lô 1 PXK riêng.</p>
            {!s.importInfo.delivered && <MissingBox what="xác nhận đã giao hàng" where="Phải giao xong mới được xuất PXK" actionLabel="Sang xác nhận giao" onAction={() => setSp({ tab: "nhap" })} />}
            <div className="grid sm:grid-cols-2 gap-3 mt-3">
              <Field label="Số PXK"><input defaultValue={s.pxk.number} placeholder="Tự sinh khi xuất" className={inputCls()} /></Field>
              <Field label="Ngày PXK"><input defaultValue={s.pxk.date || "09/09/2026"} className={inputCls()} /></Field>
              <Field label="Địa điểm nhận" ><input defaultValue={s.pxk.place || s.importInfo.deliveryAddr} className={inputCls()} /></Field>
              <Field label="Người nhận"><input defaultValue={s.pxk.receiver || s.importInfo.receiver} className={inputCls()} /></Field>
              <Field label="Chức vụ người nhận"><input defaultValue={s.pxk.role || "Thủ kho"} className={inputCls()} /></Field>
              <Field label="Nguồn (HDMB/PL)"><input defaultValue={s.pxk.source || s.contract} className={inputCls()} /></Field>
            </div>
            <div className="mt-3 rounded-xl bg-slate-50 border p-3 text-[13.5px]">
              <p>Đã giao hàng xong: <b className={s.importInfo.delivered ? "text-emerald-700" : "text-red-600"}>{s.importInfo.delivered ? "✅ Rồi — " + s.importInfo.actualDelivery : "❌ Chưa"}</b></p>
              <p>Ngày giao: <b>{s.importInfo.actualDelivery || s.importInfo.schedule}</b></p>
            </div>
            {s.pxk.done ? (
              <div className="mt-3 rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center">
                <p className="font-extrabold text-emerald-800">✅ ĐÃ XUẤT {s.pxk.number}</p>
                <button onClick={exportPXK} className="btn-press touch-target mt-2 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]"><Download size={17} /> TẢI LẠI PXK</button>
              </div>
            ) : (
              <SuccessBtn onClick={exportPXK} className="w-full mt-3 text-[16px] min-h-[56px]">🖨 XUẤT PHIẾU XUẤT KHO</SuccessBtn>
            )}
          </section>
        </div>
      )}

      {/* ============ TAB: HISTORY ============ */}
      {tab === "lich-su" && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 max-w-[800px]">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-4">Dòng thời gian — {s.id}</h3>
          <div className="relative pl-6 space-y-4 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {s.timeline.map((t, i) => (
              <div key={i} className="relative">
                <span className={cx("absolute -left-6 top-1 w-4 h-4 rounded-full border-[3px] border-white shadow", t.tone === "green" ? "bg-emerald-500" : t.tone === "amber" ? "bg-amber-500" : t.tone === "red" ? "bg-red-500" : "bg-blue-500")} />
                <p className="text-[12.5px] font-bold text-slate-400">{t.time}</p>
                <p className="font-bold text-[15px] text-[#0f2a4a]">{t.title}</p>
                {t.desc && <p className="text-[13.5px] text-slate-600">{t.desc}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* sticky mobile primary */}
      <div className="xl:hidden sticky-action -mx-3 px-3 py-3 flex gap-2">
        {tab === "nhap" && !s.importInfo.delivered && <button onClick={() => setShowDeliver(true)} className="btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">✅ XÁC NHẬN ĐÃ GIAO</button>}
        {tab === "chung-tu" && <button onClick={exportPXK} className="btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]">🖨 XUẤT PHIẾU XUẤT KHO</button>}
        {tab === "tai-chinh" && <button onClick={openPay} className="btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">＋ GHI NHẬN THANH TOÁN</button>}
        {(tab === "lay-hang" || tab === "lich-su") && <button onClick={savePickup} className="btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]">💾 LƯU THAY ĐỔI</button>}
      </div>

      {/* MODAL: deliver */}
      {showDeliver && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => setShowDeliver(false)} />
          <div className="relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up">
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">Xác nhận đã giao {s.id}?</h3>
            <p className="text-[14.5px] text-slate-600 mt-1.5">Khách <b>{s.customer}</b> đã ký nhận đủ <b>{s.cargo.packs} kiện</b> tại <b>{s.importInfo.deliveryAddr}</b>? Sau xác nhận, lô chuyển sang “Đã giao” và mở được PXK.</p>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setShowDeliver(false)}>Chưa, để sau</GhostBtn>
              <SuccessBtn onClick={confirmDelivery}>✅ ĐÃ GIAO</SuccessBtn>
            </div>
          </div>
        </div>
      )}
      {/* MODAL: pay */}
      {showPay && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => setShowPay(false)} />
          <div className="relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up">
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">Ghi nhận thanh toán — {s.id}</h3>
            <p className="text-[13.5px] text-slate-500">Còn phải thu: <b className="text-red-700">{fmtCcy(s.finance.outstanding, ccy)}</b></p>
            <div className="grid gap-3 mt-3">
              <Field label="Loại khoản"><select value={payKind} onChange={(e) => setPayKind(e.target.value)} className={inputCls()}><option>Thu tiền khách</option><option>Thu tạm ứng</option><option>Thu nốt công nợ</option><option>Trả đối tác</option></select></Field>
              <Field label={`Số tiền (${ccy})`} required error={!payAmt ? "Nhập số tiền — VD: 150000000" : undefined}><input value={payAmt} onChange={(e) => setPayAmt(e.target.value)} inputMode="numeric" placeholder="VD: 150000000" className={inputCls(!payAmt ? "missing" : "ok")} /></Field>
            </div>
            <p className="text-[12.5px] text-slate-400 mt-2">Ghi theo đồng tiền của lô ({ccy}) — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản thu thứ hai.</p>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setShowPay(false)}>Hủy</GhostBtn>
              <SuccessBtn onClick={recordPay}>💾 LƯU KHOẢN THU</SuccessBtn>
            </div>
          </div>
        </div>
      )}
      {savedTick > 0 && <span className="hidden" />}
    </div>
  );
}
