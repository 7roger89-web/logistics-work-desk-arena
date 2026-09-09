import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, CircleAlert, Download, Eye, FileDown, PenLine, Plus, Trash2, CheckCircle2 } from "lucide-react";
import { Field, GhostBtn, MissingBox, PrimaryBtn, SectionTitle, StateRow, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { fmtVND, downloadTextFile, cx } from "../lib/format";
import type { ContractGoods } from "../lib/data";

const TABS = [
  { id: "thong-tin", label: "Thông tin hợp đồng" },
  { id: "hang-hoa", label: "Hàng hóa & Chứng từ" },
  { id: "lo-lien-ket", label: "Lô hàng liên kết" },
  { id: "tai-chinh", label: "Tài chính hợp đồng" },
  { id: "lich-su", label: "Lịch sử / Phụ lục" },
];

export default function ContractDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { contracts, updateContract, toast, shipments } = useStore();
  const c0 = contracts.find((x) => x.id === id);
  const [tab, setTab] = useState("hang-hoa");
  const [goods, setGoods] = useState<ContractGoods[] | null>(null);
  const [meta, setMeta] = useState<Record<string, string>>({});
  const [reuseHdnt, setReuseHdnt] = useState<boolean | null>(null);
  const [issued, setIssued] = useState<string[]>([]);
  const [buyer, setBuyer] = useState<Record<string, string>>({});
  const m = (k: string, fb: string) => meta[k] ?? fb;

  const g: ContractGoods[] = goods ?? c0?.goods ?? [];
  const totals = useMemo(() => {
    const pre = g.reduce((s, r) => s + r.qty * r.price, 0);
    const vat = Math.round(pre * 0.08);
    return { pre, vat, total: pre + vat };
  }, [g]);
  // Phương án chứng từ: HDNT có sẵn giữ HDNT+PL; còn lại theo ngưỡng 50tr (đúng 50tr → HDMB)
  const route: "HDNT+PL" | "HDMB" = (c0?.type === "HDNT" || !!(c0 && c0.hdntNo)) ? "HDNT+PL" : totals.total < 50000000 ? "HDNT+PL" : "HDMB";
  const c = c0;
  if (!c) return <div className="rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto"><p className="font-extrabold text-[19px]">Không tìm thấy {id}</p><Link to="/hop-dong" className="btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center">Về danh sách</Link></div>;

  const setG = (i: number, k: keyof ContractGoods, v: string | number) => {
    const arr = [...g];
    arr[i] = { ...arr[i], [k]: k === "desc" || k === "unit" ? String(v) : Number(v) || 0 };
    setGoods(arr);
  };
  const addRow = () => { setGoods([...g, { desc: "", unit: "Cái", qty: 1, price: 0 }]); toast("Đã thêm dòng hàng hóa mới", "Nhập mô tả + số lượng + đơn giá — thành tiền tự tính.", "blue"); };
  const delRow = (i: number) => { if (g.length <= 1) { toast("Giữ lại ít nhất 1 dòng", "Hợp đồng cần tối thiểu 1 dòng hàng hóa.", "amber"); return; } setGoods(g.filter((_, j) => j !== i)); };

  const saveGoods = () => {
    const empty = g.some((r) => !r.desc.trim() || !r.qty || !r.price);
    if (empty) { toast("Chưa thể lưu", "Thiếu: mô tả / số lượng / đơn giá ở một số dòng — kiểm tra dòng báo đỏ.", "red"); return; }
    updateContract(c.id, (old) => ({ ...old, goods: g, value: totals.total }));
    toast("Đã lưu hàng hóa " + c.id, `Tiền hàng ${fmtVND(totals.pre)} · VAT 8% ${fmtVND(totals.vat)} · Tổng ${fmtVND(totals.total)}`, "green");
  };

  const saveBuyer = () => {
    const rep = buyer.rep ?? c.companyRep;
    const role = buyer.role ?? c.companyRole;
    if (!rep || !role) { toast("Vẫn thiếu thông tin bên mua", "Cần: Người đại diện + Chức vụ — nhập rồi bấm Lưu.", "red"); return; }
    updateContract(c.id, (old) => ({ ...old, companyRep: rep, companyRole: role, missingBuyerInfo: old.missingBuyerInfo.filter((x) => !x.includes("đại diện") && !x.includes("Chức vụ")) }));
    toast("Đã bổ sung thông tin bên mua", rep + " — " + role, "green");
  };

  const issueDoc = (kind: string, no: string) => {
    if (issued.includes(kind)) return;
    if (kind === "HDMB" && g.length > 1) {
      toast("Chưa thể xuất HDMB", "Vì sao: HDMB V1 hỗ trợ tối đa 1 dòng hàng hóa — hợp đồng này có " + g.length + " dòng. Tiếp theo: gộp thành 1 dòng hoặc tách thành 2 HDMB.", "red");
      return;
    }
    if (kind === "HDMB" && !m("hdmbDate", c.hdmbDate)) { toast("Chưa thể xuất HDMB", "Thiếu Ngày HDMB — nhập ngày rồi bấm Xuất lại.", "amber"); setTab("hang-hoa"); return; }
    setIssued((s) => [...s, kind]);
    updateContract(c.id, (old) => ({ ...old, history: [...old.history, { type: kind, no, date: "09/09/2026", rev: "V1", status: "ĐÃ PHÁT HÀNH", by: "Thu Hằng", created: "09/09/2026" }] }));
    downloadTextFile(no + ".txt", `${no}\n${kind} — ${c.id}\nBên bán: ${c.agentLegal} — MST ${c.agentTax}\nBên mua: ${c.companyLegal} — MST ${c.companyTax}\nTổng sau VAT: ${fmtVND(totals.total)}\n— Prototype: file minh họa —`);
    toast("Đã tạo thành công " + no, "File " + no + ".txt đã tải về. Xem lại ở tab Lịch sử.", "green");
  };

  const hdmbReady = !!m("hdmbDate", c.hdmbDate);
  const readiness = route === "HDMB"
    ? hdmbReady ? { ok: true, label: "Sẵn sàng xuất" } : { ok: false, label: "Thiếu Ngày HDMB" }
    : (m("hdntNo", c.hdntNo) && m("hdntDate", c.hdntDate) && m("plNo", c.plNo) ? { ok: true, label: "Sẵn sàng xuất" } : { ok: false, label: "Thiếu thông tin HDNT/PL" });

  return (
    <div className="space-y-4 max-w-[1300px]">
      <button onClick={() => nav(-1)} className="touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]"><ArrowLeft size={17} /> Quay lại danh sách</button>

      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="h-1.5 bg-gradient-to-r from-emerald-600 via-[#1e5aa8] to-[#0f2a4a]" />
        <div className="p-4 md:p-6">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-[20px] md:text-[24px] font-extrabold text-[#0f2a4a]">{c.id}</h1>
            <span className={cx("text-[12.5px] font-extrabold rounded-md px-2 py-1", c.type === "HDMB" ? "bg-blue-100 text-blue-800" : "bg-emerald-100 text-emerald-800")}>{c.type}</span>
            <ToneBadge tone={c.statusTone}>{c.status}</ToneBadge>
          </div>
          <p className="text-[14.5px] text-slate-600 mt-1">{c.company} · Đại lý {c.agent} · {c.lots} lô liên kết</p>
          <div className="flex gap-2 mt-3 overflow-x-auto no-scrollbar border-t border-slate-100 pt-3">
            {TABS.map((t) => (
              <button key={t.id} onClick={() => setTab(t.id)} className={cx("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14px] font-bold border-2 whitespace-nowrap", tab === t.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 text-slate-600")}>{t.label}</button>
            ))}
          </div>
        </div>
      </div>

      {/* TAB thong tin */}
      {tab === "thong-tin" && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Bên mua — {c.company}</h3>
            <div className="rounded-xl bg-slate-50 border p-3.5 text-[14.5px] space-y-1.5">
              <p><span className="text-slate-500">Tên pháp lý:</span> <b>{c.companyLegal}</b></p>
              <p><span className="text-slate-500">Địa chỉ:</span> {c.companyAddr}</p>
              <p><span className="text-slate-500">MST:</span> <b>{c.companyTax}</b></p>
              <p><span className="text-slate-500">Người đại diện:</span> {(buyer.rep ?? c.companyRep) ? <b>{buyer.rep ?? c.companyRep}</b> : <span className="text-amber-700 font-bold">⚠ Thiếu người đại diện</span>}</p>
              <p><span className="text-slate-500">Chức vụ:</span> {(buyer.role ?? c.companyRole) ? <b>{buyer.role ?? c.companyRole}</b> : <span className="text-amber-700 font-bold">⚠ Thiếu chức vụ</span>}</p>
            </div>
            {(!(buyer.rep ?? c.companyRep) || !(buyer.role ?? c.companyRole)) && (
              <div className="mt-3 rounded-xl border-2 border-dashed border-amber-400 bg-amber-50 p-3.5 space-y-2.5">
                <p className="font-bold text-amber-900 text-[14.5px]">✏️ BỔ SUNG THÔNG TIN — thiếu người đại diện & chức vụ</p>
                <div className="grid sm:grid-cols-2 gap-2.5">
                  <Field label="Người đại diện bên mua" required><input value={buyer.rep ?? c.companyRep} onChange={(e) => setBuyer((b) => ({ ...b, rep: e.target.value }))} placeholder="VD: Phạm Minh Đức" className={inputCls(!(buyer.rep ?? c.companyRep) ? "missing" : "ok")} /></Field>
                  <Field label="Chức vụ" required><input value={buyer.role ?? c.companyRole} onChange={(e) => setBuyer((b) => ({ ...b, role: e.target.value }))} placeholder="VD: Giám đốc" className={inputCls(!(buyer.role ?? c.companyRole) ? "missing" : "ok")} /></Field>
                </div>
                <PrimaryBtn onClick={saveBuyer} className="w-full">💾 LƯU THÔNG TIN BÊN MUA</PrimaryBtn>
              </div>
            )}
          </section>
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Bên bán / Đại lý — {c.agent}</h3>
            <div className="rounded-xl bg-slate-50 border p-3.5 text-[14.5px] space-y-1.5">
              <p><span className="text-slate-500">Tên pháp lý:</span> <b>{c.agentLegal}</b></p>
              <p><span className="text-slate-500">Địa chỉ:</span> {c.agentAddr}</p>
              <p><span className="text-slate-500">MST / mã pháp lý:</span> <b>{c.agentTax}</b></p>
              <p><span className="text-slate-500">Người đại diện:</span> <b>{c.agentRep}</b> · {c.agentRole}</p>
              <p><span className="text-slate-500">Chủ tài khoản:</span> {c.bankOwner}</p>
              <p><span className="text-slate-500">Số TK:</span> <b>{c.bankNo}</b> · {c.bankName}</p>
            </div>
            <div className="mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-[13.5px] text-emerald-900">✅ Thông tin đại lý đầy đủ — không cần bổ sung.</div>
          </section>
        </div>
      )}

      {/* TAB hang hoa */}
      {tab === "hang-hoa" && (
        <div className="space-y-4">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
              <h3 className="font-extrabold text-[17px] text-[#0f2a4a]">Hàng hóa — nhập từng dòng, máy tự tính tiền</h3>
              <span className="text-[13px] text-slate-500">STT · VAT 8% · Thành tiền: tự động, không cần nhập</span>
            </div>
            {/* desktop goods table */}
            <div className="hidden md:block overflow-x-auto mt-2">
              <table className="tbl w-full text-[14.5px] min-w-[860px]">
                <thead><tr><th className="w-[52px]">STT</th><th>Mô tả hàng hóa *</th><th className="w-[110px]">Đơn vị</th><th className="w-[110px]">Số lượng *</th><th className="w-[170px]">Đơn giá chưa VAT *</th><th className="w-[80px]">VAT</th><th className="w-[160px]">Thành tiền</th><th className="w-[70px]"></th></tr></thead>
                <tbody>
                  {g.map((r, i) => {
                    const bad = !r.desc.trim() || !r.qty || !r.price;
                    return (
                      <tr key={i} className={bad ? "bg-red-50/50" : ""}>
                        <td className="font-extrabold text-center">{i + 1}</td>
                        <td><input value={r.desc} onChange={(e) => setG(i, "desc", e.target.value)} placeholder="VD: Máy CNC 5 trục — model VMC-850" className={inputCls(!r.desc.trim() ? "invalid" : "ok")} /></td>
                        <td><select value={r.unit} onChange={(e) => setG(i, "unit", e.target.value)} className={inputCls()}><option>Cái</option><option>Máy</option><option>Bộ</option><option>Lô</option><option>Hệ thống</option><option>Kiện</option><option>Kg</option></select></td>
                        <td><input type="number" min={0} value={r.qty || ""} onChange={(e) => setG(i, "qty", e.target.value)} placeholder="0" className={inputCls(!r.qty ? "invalid" : "ok")} /></td>
                        <td><input type="number" min={0} value={r.price || ""} onChange={(e) => setG(i, "price", e.target.value)} placeholder="0" className={inputCls(!r.price ? "invalid" : "ok")} /></td>
                        <td className="text-center font-bold text-slate-500">8%</td>
                        <td className="font-extrabold text-[#0f2a4a] whitespace-nowrap">{fmtVND(Math.round(r.qty * r.price * 1.08))}</td>
                        <td><button onClick={() => delRow(i)} className="touch-target w-10 h-10 grid place-items-center rounded-lg text-red-500 hover:bg-red-50" title="Xóa dòng"><Trash2 size={17} /></button></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {/* mobile goods cards */}
            <div className="md:hidden space-y-3 mt-2">
              {g.map((r, i) => (
                <div key={i} className="rounded-xl border-2 border-slate-200 p-3.5 space-y-2.5">
                  <div className="flex items-center justify-between"><span className="font-extrabold text-[15px] text-[#0f2a4a]">Dòng {i + 1}</span><button onClick={() => delRow(i)} className="touch-target inline-flex items-center gap-1 text-[13.5px] font-bold text-red-600 border border-red-200 rounded-lg px-3 min-h-[40px]"><Trash2 size={15} /> Xóa</button></div>
                  <Field label="Mô tả hàng hóa" required><input value={r.desc} onChange={(e) => setG(i, "desc", e.target.value)} placeholder="VD: Máy CNC 5 trục" className={inputCls(!r.desc.trim() ? "invalid" : "ok")} /></Field>
                  <div className="grid grid-cols-2 gap-2.5">
                    <Field label="Đơn vị"><select value={r.unit} onChange={(e) => setG(i, "unit", e.target.value)} className={inputCls()}><option>Cái</option><option>Máy</option><option>Bộ</option><option>Lô</option><option>Hệ thống</option><option>Kiện</option><option>Kg</option></select></Field>
                    <Field label="Số lượng" required><input type="number" value={r.qty || ""} onChange={(e) => setG(i, "qty", e.target.value)} className={inputCls(!r.qty ? "invalid" : "ok")} /></Field>
                  </div>
                  <Field label="Đơn giá chưa VAT (VND)" required><input type="number" value={r.price || ""} onChange={(e) => setG(i, "price", e.target.value)} inputMode="numeric" className={inputCls(!r.price ? "invalid" : "ok")} /></Field>
                  <div className="rounded-lg bg-slate-50 border p-2.5 flex justify-between text-[14px]"><span className="text-slate-500">VAT 8% · Thành tiền (tự tính)</span><b>{fmtVND(Math.round(r.qty * r.price * 1.08))}</b></div>
                </div>
              ))}
            </div>
            <div className="flex flex-col sm:flex-row gap-2.5 mt-3">
              <button onClick={addRow} className="btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl border-2 border-dashed border-[#1e5aa8] text-[#1e5aa8] font-extrabold text-[15px] px-5 min-h-[52px] flex-1"><Plus size={19} /> THÊM DÒNG HÀNG HÓA</button>
              <PrimaryBtn onClick={saveGoods} className="flex-1">💾 LƯU HÀNG HÓA</PrimaryBtn>
            </div>
            <div className="mt-3 rounded-2xl bg-[#0f2a4a] text-white p-4 grid grid-cols-3 gap-2 text-center">
              <div><p className="text-[12px] text-blue-200 font-semibold">Tiền hàng</p><p className="font-extrabold text-[15px] md:text-[19px]">{fmtVND(totals.pre)}</p></div>
              <div><p className="text-[12px] text-blue-200 font-semibold">VAT 8%</p><p className="font-extrabold text-[15px] md:text-[19px]">{fmtVND(totals.vat)}</p></div>
              <div className="rounded-xl bg-white/10 py-1"><p className="text-[12px] text-amber-200 font-bold">TỔNG SAU VAT</p><p className="font-extrabold text-[16px] md:text-[21px] text-amber-300">{fmtVND(totals.total)}</p></div>
            </div>
          </section>

          {/* document route */}
          <section className="rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-5">
            <h3 className="font-extrabold text-[17px] text-[#0f2a4a]">✅ PHƯƠNG ÁN CHỨNG TỪ <span className="text-[13px] font-medium text-slate-500">(tự chọn theo tổng sau VAT — đúng 50 tr thuộc HDMB)</span></h3>
            <div className={cx("mt-3 rounded-2xl border-2 p-4 flex flex-col md:flex-row md:items-center gap-3", route === "HDMB" ? "border-blue-300 bg-blue-50" : "border-emerald-300 bg-emerald-50")}>
              <div className="flex-1">
                <p className="text-[13px] font-bold uppercase tracking-wide opacity-70">Tổng sau VAT: {fmtVND(totals.total)}</p>
                <p className="text-[19px] md:text-[22px] font-extrabold text-[#0f2a4a]">{route === "HDMB" ? "→ Lập HỢP ĐỒNG MUA BÁN (HDMB)" : "→ Lập HỢP ĐỒNG NGUYÊN TẮC (HDNT) + PHỤ LỤC (PL)"}</p>
                <p className="text-[13.5px] text-slate-600">Ngưỡng: dưới 50.000.000 ₫ → HDNT + PL · Từ 50.000.000 ₫ trở lên → HDMB.</p>
              </div>
              <span className={cx("inline-flex items-center gap-1.5 rounded-full px-4 py-2 font-extrabold text-[14.5px] whitespace-nowrap", readiness.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white")}>{readiness.ok ? <CheckCircle2 size={17} /> : <CircleAlert size={17} />} {readiness.label}</span>
            </div>

            {route === "HDNT+PL" ? (
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div className="rounded-xl border border-slate-200 p-4 space-y-3">
                  <h4 className="font-extrabold text-[15px]">Hợp đồng nguyên tắc (HDNT)</h4>
                  {c.reusableHdnt && reuseHdnt === null && (
                    <div className="rounded-xl bg-emerald-50 border border-emerald-300 p-3">
                      <p className="font-bold text-[14px] text-emerald-900">✔ CÓ THỂ TÁI SỬ DỤNG HDNT {c.hdntNo} (còn hiệu lực tới {c.hdntTo})</p>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <button onClick={() => { setReuseHdnt(true); toast("Đã chọn tái sử dụng " + c.hdntNo, "Chỉ cần lập Phụ lục mới cho đợt hàng này.", "green"); }} className="touch-target rounded-lg bg-emerald-600 text-white font-bold text-[14px] min-h-[44px]">Tái sử dụng</button>
                        <button onClick={() => setReuseHdnt(false)} className="touch-target rounded-lg border-2 border-slate-200 font-bold text-[14px] min-h-[44px]">Lập HDNT mới</button>
                      </div>
                    </div>
                  )}
                  {(reuseHdnt === false || !c.reusableHdnt) && (
                    <div className="grid sm:grid-cols-2 gap-3">
                      <Field label="Số HDNT" required><input value={m("hdntNo", c.hdntNo)} onChange={(e) => setMeta({ ...meta, hdntNo: e.target.value })} placeholder="VD: HDNT-PA-2026-119" className={inputCls()} /></Field>
                      <Field label="Ngày ký" required><input value={m("hdntDate", c.hdntDate)} onChange={(e) => setMeta({ ...meta, hdntDate: e.target.value })} placeholder="VD: 09/09/2026" className={inputCls()} /></Field>
                      <Field label="Hiệu lực từ"><input value={m("hdntFrom", c.hdntFrom)} onChange={(e) => setMeta({ ...meta, hdntFrom: e.target.value })} className={inputCls()} /></Field>
                      <Field label="Hiệu lực đến"><input value={m("hdntTo", c.hdntTo)} onChange={(e) => setMeta({ ...meta, hdntTo: e.target.value })} className={inputCls()} /></Field>
                    </div>
                  )}
                  {reuseHdnt === true && <p className="text-[13.5px] text-emerald-800 font-semibold">Dùng lại {c.hdntNo} — chuyển sang lập Phụ lục bên phải. <button onClick={() => setReuseHdnt(null)} className="underline">Đổi ý</button></p>}
                </div>
                <div className="rounded-xl border border-slate-200 p-4 space-y-3">
                  <h4 className="font-extrabold text-[15px]">Phụ lục (PL) — HDNT cha: {reuseHdnt ? c.hdntNo : (m("hdntNo", c.hdntNo) || "…")}</h4>
                  <div className="grid sm:grid-cols-2 gap-3">
                    <Field label="Số PL" required><input value={m("plNo", c.plNo)} onChange={(e) => setMeta({ ...meta, plNo: e.target.value })} placeholder="VD: PL-118-B" className={inputCls()} /></Field>
                    <Field label="Ngày PL" required><input value={m("plDate", c.plDate)} onChange={(e) => setMeta({ ...meta, plDate: e.target.value })} placeholder="VD: 09/09/2026" className={inputCls()} /></Field>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-slate-200 p-4 mt-4">
                <h4 className="font-extrabold text-[15px] mb-3">Hợp đồng mua bán (HDMB)</h4>
                {!hdmbReady && <MissingBox what="Ngày HDMB" where="Chưa có ngày ký — nhập để đủ điều kiện xuất" actionLabel="Nhập ngày ngay" onAction={() => document.getElementById("fld-hdmbdate")?.focus()} />}
                <div className="grid sm:grid-cols-2 gap-3 mt-3">
                  <Field label="Số HDMB" required><input value={m("hdmbNo", c.hdmbNo)} onChange={(e) => setMeta({ ...meta, hdmbNo: e.target.value })} className={inputCls()} /></Field>
                  <Field label="Ngày HDMB" required error={!hdmbReady ? "Thiếu Ngày HDMB — VD: 09/09/2026" : undefined}><input id="fld-hdmbdate" value={m("hdmbDate", c.hdmbDate)} onChange={(e) => setMeta({ ...meta, hdmbDate: e.target.value })} placeholder="VD: 09/09/2026" className={inputCls(!hdmbReady ? "missing" : "ok")} /></Field>
                </div>
              </div>
            )}

            <SuccessBtn onClick={() => issueDoc(route === "HDMB" ? "HDMB" : "PL", route === "HDMB" ? m("hdmbNo", c.hdmbNo) || c.id : m("plNo", c.plNo) || "PL-MOI")} className="w-full mt-4 text-[16.5px] min-h-[56px]">🖨 XUẤT CHỨNG TỪ SẴN SÀNG</SuccessBtn>
            {issued.length > 0 && (
              <div className="mt-3 rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4">
                <p className="font-extrabold text-emerald-800 text-[16px]">✅ ĐÃ TẠO THÀNH CÔNG</p>
                {issued.map((k) => (<p key={k} className="text-[14px] mt-1">File: <b>{k === "HDMB" ? m("hdmbNo", c.hdmbNo) || c.id : m("plNo", c.plNo)}.txt</b> <button onClick={() => toast("Đang tải lại file", "File minh họa đã lưu về máy.", "green")} className="inline-flex items-center gap-1 font-bold text-[#1e5aa8] ml-2"><FileDown size={15} /> TẢI LẠI</button></p>))}
              </div>
            )}
          </section>
        </div>
      )}

      {/* TAB linked lots */}
      {tab === "lo-lien-ket" && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-1">Lô hàng liên kết — {c.linkedLots.length} lô</h3>
          <p className="text-[13.5px] text-slate-500 mb-3">PXK làm theo từng lô (không gộp). Bấm MỞ LÔ để xử lý, LÀM PXK để xuất phiếu.</p>
          <div className="hidden md:block overflow-x-auto"><table className="tbl w-full text-[14.5px] min-w-[760px]">
            <thead><tr><th>Mã lô</th><th>Khách hàng</th><th>Trạng thái</th><th>Ngày giao</th><th>PXK</th><th>Hành động</th></tr></thead>
            <tbody>{c.linkedLots.map((l) => (<tr key={l.id} className="hover:bg-slate-50"><td className="font-extrabold text-[#1e5aa8]">{l.id}</td><td>{l.customer}</td><td>{l.status}</td><td>{l.delivery}</td><td>{l.pxk}</td><td><div className="flex gap-1.5"><Link to={"/lo-hang/" + l.id} className="touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[40px]">MỞ LÔ</Link><Link to={"/lo-hang/" + l.id + "?tab=chung-tu"} className="touch-target inline-flex items-center rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]">LÀM PXK</Link></div></td></tr>))}</tbody>
          </table></div>
          <div className="md:hidden space-y-2.5">
            {c.linkedLots.map((l) => (
              <div key={l.id} className="rounded-xl border p-3.5">
                <p className="font-extrabold text-[15.5px]">{l.id} · {l.customer}</p>
                <p className="text-[13.5px] text-slate-500">{l.status} · Giao {l.delivery} · PXK: {l.pxk}</p>
                <div className="grid grid-cols-2 gap-2 mt-2.5"><Link to={"/lo-hang/" + l.id} className="touch-target flex items-center justify-center rounded-xl bg-[#0f2a4a] text-white font-bold min-h-[48px]">MỞ LÔ</Link><Link to={"/lo-hang/" + l.id + "?tab=chung-tu"} className="touch-target flex items-center justify-center rounded-xl border-2 border-slate-200 font-bold min-h-[48px]">LÀM PXK</Link></div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* TAB finance */}
      {tab === "tai-chinh" && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 max-w-[860px]">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Tài chính hợp đồng {c.id}</h3>
          <StateRow label="Giá trị hợp đồng (sau VAT)" value={<span className="font-extrabold text-[19px] text-[#0f2a4a]">{fmtVND(totals.total)}</span>} big />
          <StateRow label="Đã thu (cộng các lô)" value={fmtVND(shipments.filter((s) => s.contract === c.id).reduce((s, x) => s + x.finance.received, 0))} />
          <StateRow label="Còn phải thu" value={<span className="text-red-700 font-bold">{fmtVND(Math.max(0, totals.total - shipments.filter((s) => s.contract === c.id).reduce((s, x) => s + x.finance.received, 0)))}</span>} />
          <Link to="/tai-chinh/thu-tien" className="btn-press touch-target mt-3 inline-flex items-center gap-2 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]">MỞ THU TIỀN & CÔNG NỢ <ArrowRight size={16} /></Link>
        </section>
      )}

      {/* TAB history */}
      {tab === "lich-su" && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Lịch sử phát hành & phụ lục</h3>
          {c.history.length === 0 && <div className="rounded-xl border-2 border-dashed border-slate-300 p-6 text-center text-slate-500 text-[14px]">Chưa phát hành chứng từ nào. Sang tab <button onClick={() => setTab("hang-hoa")} className="font-bold text-[#1e5aa8]">Hàng hóa & Chứng từ</button> để xuất bản đầu tiên.</div>}
          <div className="hidden md:block overflow-x-auto"><table className="tbl w-full text-[14px] min-w-[820px]">
            <thead><tr><th>Loại</th><th>Số</th><th>Ngày</th><th>Revision</th><th>Trạng thái</th><th>Người tạo</th><th></th></tr></thead>
            <tbody>{c.history.map((h, i) => (<tr key={i}><td className="font-bold">{h.type}</td><td className="font-semibold">{h.no}</td><td>{h.date}</td><td>{h.rev}</td><td><span className="inline-flex items-center gap-1 font-extrabold text-[12.5px] bg-emerald-100 text-emerald-800 rounded-full px-2.5 py-1">● {h.status}</span></td><td>{h.by} · {h.created}</td><td><div className="flex gap-1.5"><button onClick={() => toast("Xem " + h.no, "Bản xem trước minh họa hiển thị tại đây.", "blue")} className="touch-target inline-flex items-center gap-1 text-[13px] font-bold border rounded-lg px-2.5 min-h-[40px]"><Eye size={14} /> Xem</button><button onClick={() => { downloadTextFile(h.no + ".txt", h.no + "\n— tải lại từ lịch sử —"); toast("Đã tải lại " + h.no, "File minh họa đã lưu về máy.", "green"); }} className="touch-target inline-flex items-center gap-1 text-[13px] font-bold border rounded-lg px-2.5 min-h-[40px]"><Download size={14} /> Tải lại</button></div></td></tr>))}</tbody>
          </table></div>
          <div className="md:hidden space-y-2.5">{c.history.map((h, i) => (<div key={i} className="rounded-xl border p-3.5"><p className="font-extrabold">{h.type} · {h.no}</p><p className="text-[13px] text-slate-500">{h.date} · {h.rev} · {h.status} · {h.by}</p><div className="grid grid-cols-2 gap-2 mt-2"><button onClick={() => toast("Xem " + h.no, "Bản xem trước minh họa.", "blue")} className="touch-target rounded-lg border font-bold min-h-[44px]">Xem thông tin</button><button onClick={() => toast("Đã tải lại " + h.no, "File minh họa.", "green")} className="touch-target rounded-lg bg-[#0f2a4a] text-white font-bold min-h-[44px]">⬇ Tải lại</button></div></div>))}</div>
        </section>
      )}

      <div className="rounded-2xl bg-blue-50 border border-blue-200 p-4 flex items-start gap-2.5 text-[14px] text-blue-900">
        <PenLine size={18} className="shrink-0 mt-0.5" />
        <p><b>Luồng liên hoàn:</b> Hợp đồng → Hàng hóa → Xuất chứng từ → Tải về → Lô liên kết → PXK từng lô → Thu tiền. Nút nào cũng dẫn đúng nơi cần làm tiếp.</p>
      </div>
    </div>
  );
}
