import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle2, CircleAlert, Download, Eye, FileText, MapPin, PenLine, Phone, Truck, Wallet, Package, FileDown, Clock } from "lucide-react";
import { Field, GhostBtn, MissingBox, NextActionBanner, PrimaryBtn, SectionTitle, StateRow, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { fmtMoney, fmtVND, downloadTextFile, cx } from "../lib/format";

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
  const { shipments, updateShipment, toast, contracts } = useStore();
  const nav = useNavigate();
  const s = shipments.find((x) => x.id === id);
  const [showPay, setShowPay] = useState(false);
  const [showDeliver, setShowDeliver] = useState(false);
  const [payAmt, setPayAmt] = useState("");
  const [payKind, setPayKind] = useState("Thu tiền khách");
  const [form, setForm] = useState<Record<string, string>>({});
  const [savedTick, setSavedTick] = useState(0);

  useEffect(() => { setForm({}); }, [id, tab]);
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const val = (k: string, fb: string) => form[k] ?? fb;

  const linkedContract = useMemo(() => contracts.find((c) => c.id === s?.contract), [contracts, s]);

  if (!s) return <div className="rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto"><p className="font-extrabold text-[19px]">Không tìm thấy lô {id}</p><p className="text-slate-500 mt-1 text-[15px]">Mã lô có thể sai. Về danh sách để tìm lại.</p><Link to="/lo-hang" className="btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center">Về danh sách lô</Link></div>;

  const savePickup = () => {
    updateShipment(s.id, (old) => ({
      ...old,
      pickup: { ...old.pickup, plate: val("plate", old.pickup.plate) || old.pickup.plate, driver: val("driver", old.pickup.driver) || old.pickup.driver, driverPhone: val("driverPhone", old.pickup.driverPhone) || old.pickup.driverPhone, pickupTime: val("pickupTime", old.pickup.pickupTime) || old.pickup.pickupTime },
      updated: "09/09/2026 " + new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      timeline: [...old.timeline, { time: "09/09 " + new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }), title: "Đã cập nhật thông tin lấy hàng", desc: "Bổ sung xe TQ / giờ lấy qua workspace", tone: "blue" }],
    }));
    setSavedTick(Date.now());
    toast("Đã lưu thông tin lấy hàng " + s.id, "Xe TQ + giờ lấy đã cập nhật. Việc tiếp theo đã chuyển bước.", "green");
  };

  const saveImport = () => {
    const tk = val("tk", s.importInfo.declarationNo);
    if (!tk) { toast("Chưa thể lưu thông quan", "Thiếu: Số tờ khai nhập khẩu — nhập số TK (12 số) rồi bấm Lưu.", "red"); return; }
    updateShipment(s.id, (old) => ({
      ...old,
      importInfo: { ...old.importInfo, declarationNo: tk, regDate: val("regDate", old.importInfo.regDate) || "09/09/2026", tax: Number(val("tax", String(old.importInfo.tax))) || old.importInfo.tax, vat: Number(val("vat", String(old.importInfo.vat))) || old.importInfo.vat, inspection: val("inspection", old.importInfo.inspection) || old.importInfo.inspection, driverVN: val("driverVN", old.importInfo.driverVN) || old.importInfo.driverVN, plateVN: val("plateVN", old.importInfo.plateVN) || old.importInfo.plateVN },
      missingDocs: old.missingDocs.filter((d) => d !== "Số tờ khai nhập khẩu"),
      status: old.importInfo.clearDate ? old.status : "Chờ thông quan",
      nextAction: "Nộp thuế & chờ phân luồng tờ khai " + tk,
      timeline: [...old.timeline, { time: "09/09 " + new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }), title: "Đã khai tờ khai " + tk, desc: "Chờ phân luồng — nộp thuế để thông quan", tone: "blue" }],
      updated: "09/09/2026 " + new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
    }));
    toast("Đã lưu tờ khai " + tk, "Tiếp theo: nộp thuế NK + VAT để thông quan.", "green");
  };

  const confirmDelivery = () => {
    updateShipment(s.id, (old) => ({ ...old, importInfo: { ...old.importInfo, delivered: true, actualDelivery: "09/09/2026 " + new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) }, status: "Đã giao", statusTone: "green", nextAction: "Thu nốt công nợ & xuất PXK", nextLabel: "THU TIỀN", nextRoute: "/tai-chinh/thu-tien", timeline: [...old.timeline, { time: "09/09 " + new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }), title: "Đã giao hàng — khách ký nhận", desc: "Đủ kiện, không khiếu nại tại chỗ", tone: "green" }] }));
    setShowDeliver(false);
    toast("Đã xác nhận giao hàng " + s.id, "Tiếp theo: xuất Phiếu xuất kho ở tab Chứng từ.", "green");
  };

  const recordPay = () => {
    const amt = Number(payAmt.replace(/\D/g, ""));
    if (!amt) { toast("Chưa nhập số tiền", "Nhập số tiền VND rồi bấm Lưu — ví dụ 50.000.000.", "red"); return; }
    updateShipment(s.id, (old) => ({ ...old, finance: { ...old.finance, received: old.finance.received + amt, payments: [...old.finance.payments, { date: "09/09/2026", kind: payKind, amount: amt, ccy: "VND", by: "Thu Hằng", note: "Ghi nhận từ workspace" }] } }));
    setShowPay(false); setPayAmt("");
    toast("Đã ghi nhận " + fmtVND(amt), payKind + " — lịch sử thanh toán đã cập nhật.", "green");
  };

  const exportPXK = () => {
    const no = s.pxk.number || ("PXK-2026-" + s.id.slice(3));
    updateShipment(s.id, (old) => ({ ...old, pxk: { ...old.pxk, number: no, date: old.pxk.date || "09/09/2026", place: old.pxk.place || old.importInfo.deliveryAddr, receiver: old.pxk.receiver || old.importInfo.receiver, role: old.pxk.role || "Thủ kho", done: true } }));
    downloadTextFile(no + ".txt",
      `${no}\nPHIẾU XUẤT KHO — ${s.id}\nNgày: 09/09/2026\nKhách: ${s.customer}\nĐịa điểm nhận: ${s.importInfo.deliveryAddr}\nNgười nhận: ${s.importInfo.receiver}\nHàng: ${s.cargo.type} — ${s.cargo.packs} kiện — ${s.cargo.weight}\nNguồn: ${s.pxk.source || s.contract}\nĐơn vị: CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH (Đại lý: Phú Anh Logistics VN)\n— Prototype: file minh họa —`);
    toast("Đã xuất " + no, "File đã tải về. Lịch sử chứng từ đã ghi nhận.", "green");
  };

  const missingCount = s.missingDocs.length + s.docs.filter((d) => !d.ok).length;

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
              <MissingBox key={m} what={m} actionLabel="Bổ sung ngay" onAction={() => { if (m.includes("tờ khai") || m.includes("Xe VN")) setSp({ tab: "nhap" }); else if (m.includes("Biển số") || m.includes("giờ lấy") || m.includes("Packing")) setSp({ tab: "lay-hang" }); else setSp({ tab: "tai-chinh" }); setTimeout(() => document.getElementById("missing-anchor")?.scrollIntoView({ behavior: "smooth", block: "center" }), 150); }} />
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
                {[["Số kiện", String(s.cargo.packs)], ["Trọng lượng", s.cargo.weight], ["CBM", String(s.cargo.cbm)], ["Kích thước", s.cargo.dims], ["Loại hàng", s.cargo.type]].map(([k, v]) => (
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
              <Field label="Thuế nhập khẩu (VND)"><input value={val("tax", String(s.importInfo.tax || ""))} onChange={(e) => set("tax", e.target.value)} placeholder="VD: 48200000" inputMode="numeric" className={inputCls()} /></Field>
              <Field label="VAT hàng nhập (VND)"><input value={val("vat", String(s.importInfo.vat || ""))} onChange={(e) => set("vat", e.target.value)} placeholder="VD: 96400000" inputMode="numeric" className={inputCls()} /></Field>
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
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mt-2 mb-2">Chi phí thực tế</h3>
              {s.finance.actual.map((c) => (<StateRow key={c.label} label={c.label} value={<span className="font-bold text-[16px]">{fmtMoney(c.amount, c.ccy)} <span className="text-[12px] font-bold text-emerald-700">{c.ccy}</span></span>} />))}
            </section>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-2"><Wallet size={19} className="text-emerald-600" /> Phải thu khách hàng (VND)</h3>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl bg-slate-50 border p-3"><p className="text-[12px] text-slate-500 font-semibold">Phải thu</p><p className="font-extrabold text-[16px] md:text-[18px]">{(s.finance.receivable / 1e6).toLocaleString("vi-VN")} tr</p></div>
                <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3"><p className="text-[12px] text-emerald-700 font-semibold">Đã thu</p><p className="font-extrabold text-[16px] md:text-[18px] text-emerald-700">{(s.finance.received / 1e6).toLocaleString("vi-VN")} tr</p></div>
                <div className="rounded-xl bg-red-50 border border-red-200 p-3"><p className="text-[12px] text-red-600 font-semibold">Còn phải thu</p><p className="font-extrabold text-[16px] md:text-[18px] text-red-700">{((s.finance.receivable - s.finance.received) / 1e6).toLocaleString("vi-VN")} tr</p></div>
              </div>
              <button onClick={() => setShowPay(true)} className="btn-press touch-target mt-3 w-full rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">＋ GHI NHẬN THANH TOÁN</button>
            </section>
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-2">Phải trả đối tác (VND)</h3>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl bg-slate-50 border p-3"><p className="text-[12px] text-slate-500 font-semibold">Phải trả</p><p className="font-extrabold text-[16px] md:text-[18px]">{(s.finance.payable / 1e6).toLocaleString("vi-VN")} tr</p></div>
                <div className="rounded-xl bg-blue-50 border border-blue-200 p-3"><p className="text-[12px] text-blue-700 font-semibold">Đã trả</p><p className="font-extrabold text-[16px] md:text-[18px] text-blue-700">{(s.finance.paid / 1e6).toLocaleString("vi-VN")} tr</p></div>
                <div className="rounded-xl bg-amber-50 border border-amber-200 p-3"><p className="text-[12px] text-amber-700 font-semibold">Còn phải trả</p><p className="font-extrabold text-[16px] md:text-[18px] text-amber-800">{((s.finance.payable - s.finance.paid) / 1e6).toLocaleString("vi-VN")} tr</p></div>
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
                <p className="text-[14px] text-slate-600 mt-1">{linkedContract.companyLegal} · Giá trị {fmtVND(linkedContract.value || s.finance.receivable)}</p>
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <Link to={"/hop-dong/" + linkedContract.id} className="btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] min-h-[48px]"><Eye size={16} /> MỞ HỢP ĐỒNG</Link>
                  <button onClick={() => { downloadTextFile(linkedContract.id + ".txt", `${linkedContract.id}\nHỢP ĐỒNG MUA BÁN — ${linkedContract.companyLegal}\nGiá trị: ${fmtVND(linkedContract.value || s.finance.receivable)}\n— Prototype: file minh họa —`); toast("Đã tải " + linkedContract.id, "File minh họa đã lưu về máy.", "green"); }} className="btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] min-h-[48px]"><FileDown size={16} /> TẢI HỢP ĐỒNG</button>
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
        {tab === "tai-chinh" && <button onClick={() => setShowPay(true)} className="btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">＋ GHI NHẬN THANH TOÁN</button>}
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
            <p className="text-[13.5px] text-slate-500">Còn phải thu: <b className="text-red-700">{fmtVND(s.finance.receivable - s.finance.received)}</b></p>
            <div className="grid gap-3 mt-3">
              <Field label="Loại khoản"><select value={payKind} onChange={(e) => setPayKind(e.target.value)} className={inputCls()}><option>Thu tiền khách</option><option>Thu tạm ứng</option><option>Thu nốt công nợ</option><option>Trả đối tác</option></select></Field>
              <Field label="Số tiền (VND)" required error={!payAmt ? "Nhập số tiền — VD: 150000000" : undefined}><input value={payAmt} onChange={(e) => setPayAmt(e.target.value)} inputMode="numeric" placeholder="VD: 150000000" className={inputCls(!payAmt ? "missing" : "ok")} /></Field>
            </div>
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
