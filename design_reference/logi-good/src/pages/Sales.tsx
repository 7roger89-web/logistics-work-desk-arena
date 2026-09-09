import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Calculator, Plus } from "lucide-react";
import { Field, PrimaryBtn, SectionTitle, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import { QUOTES, AGREEMENTS } from "../lib/data";
import { fmtVND, cx } from "../lib/format";
import { useStore } from "../lib/store";

export function Quotes() {
  const { toast } = useStore();
  const [showBuilder, setShowBuilder] = useState(false);
  const [customer, setCustomer] = useState("Công ty CP Công Nghệ Sao Việt");
  const [route, setRoute] = useState("Quảng Tây → Tân Thanh → Bắc Ninh");
  const [costs, setCosts] = useState({ tq: 32000000, xk: 3500000, ck: 6800000, thue: 0, vn: 9800000, dv: 6200000, ut: 4500000, other: 0 });
  const [price, setPrice] = useState(118000000);
  const totalCost = useMemo(() => Object.values(costs).reduce((a, b) => a + b, 0), [costs]);
  const profit = price - totalCost;
  const margin = price ? ((profit / price) * 100).toFixed(1) : "0";
  const setC = (k: keyof typeof costs, v: string) => setCosts((c) => ({ ...c, [k]: Number(v) || 0 }));

  const stTone = (s: string) => s === "ACCEPTED" ? "green" : s === "SENT" ? "blue" : s === "REJECTED" ? "red" : "gray";
  const stLabel = (s: string) => s === "ACCEPTED" ? "ĐÃ CHỐT" : s === "SENT" ? "ĐÃ GỬI" : s === "REJECTED" ? "TỪ CHỐI" : "NHÁP";

  return (
    <div className="space-y-4 max-w-[1200px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle title="Kinh Doanh & Báo Giá" sub="Lập dự toán → gửi khách → khách chốt → tạo thỏa thuận. Mọi số đều ghi rõ BÁO GIÁ / DỰ KIẾN." right={<button onClick={() => setShowBuilder((v) => !v)} className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]"><Plus size={17} /> Tạo báo giá</button>} />
        <div className="grid gap-2.5 md:grid-cols-2 xl:grid-cols-4">
          {QUOTES.map((q) => (
            <div key={q.id} className="rounded-2xl border-2 border-slate-200 p-4 lift">
              <div className="flex items-center gap-2"><span className="font-extrabold text-[15px] text-[#0f2a4a]">{q.id}</span><ToneBadge tone={stTone(q.status) as any} size="sm">{stLabel(q.status)}</ToneBadge></div>
              <p className="font-semibold text-[14px] mt-1">{q.customer}</p>
              <p className="text-[12.5px] text-slate-500">{q.route} · {q.goods}</p>
              <div className="grid grid-cols-3 gap-1.5 mt-2.5 text-center text-[12px]">
                <div className="rounded-lg bg-slate-50 border p-1.5"><p className="text-slate-500">Chi phí</p><b>{(q.cost / 1e6).toFixed(1)}tr</b></div>
                <div className="rounded-lg bg-blue-50 border border-blue-200 p-1.5"><p className="text-slate-500">Giá bán</p><b>{(q.price / 1e6).toFixed(1)}tr</b></div>
                <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-1.5"><p className="text-slate-500">Margin</p><b className="text-emerald-700">{q.margin}</b></div>
              </div>
              <div className="grid grid-cols-2 gap-1.5 mt-2.5">
                {q.status === "DRAFT" && <button onClick={() => toast("Đã gửi " + q.id + " cho khách", "Báo giá chuyển sang ĐÃ GỬI — chờ khách chốt.", "green")} className="touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold min-h-[44px]">GỬI KHÁCH</button>}
                {q.status === "SENT" && <button onClick={() => toast("Khách đã chốt " + q.id, "Tiếp theo: lập Thỏa thuận & bàn giao Support.", "green")} className="touch-target rounded-lg bg-emerald-600 text-white text-[13px] font-bold min-h-[44px]">KHÁCH ĐÃ CHỐT</button>}
                {(q.status === "ACCEPTED") && <Link to="/thoa-thuan-ban-giao" className="touch-target flex items-center justify-center rounded-lg bg-emerald-600 text-white text-[13px] font-bold min-h-[44px]">Lập thỏa thuận</Link>}
                <button onClick={() => toast("Xem chi tiết " + q.id, "Bảng dự toán chi tiết hiển thị tại đây.", "blue")} className="touch-target rounded-lg border-2 border-slate-200 text-[13px] font-bold min-h-[44px]">Chi tiết</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {showBuilder && (
        <section className="rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-6 anim-slide-up">
          <h3 className="font-extrabold text-[17px] text-[#0f2a4a] flex items-center gap-2"><Calculator size={20} /> Dự toán báo giá mới <span className="text-[12px] font-extrabold bg-violet-100 text-violet-800 rounded-md px-2 py-0.5">BÁO GIÁ / DỰ KIẾN</span></h3>
          <div className="grid md:grid-cols-2 gap-3.5 mt-3">
            <Field label="Khách hàng" required><select value={customer} onChange={(e) => setCustomer(e.target.value)} className={inputCls()}><option>Công ty CP Công Nghệ Sao Việt</option><option>Công ty TNHH Cơ Khí An Phát</option><option>Công ty TNHH Thiết Bị Minh Đức</option><option>Công ty TNHH Phụ Kiện Hồng Hà</option></select></Field>
            <Field label="Tuyến" required><select value={route} onChange={(e) => setRoute(e.target.value)} className={inputCls()}><option>Quảng Tây → Tân Thanh → Bắc Ninh</option><option>Quảng Đông → Hữu Nghị → Hà Nội</option><option>Quảng Đông → Hữu Nghị → Hải Phòng</option></select></Field>
            <Field label="Incoterm"><select className={inputCls()}><option>DAP — Giao tại kho khách</option><option>DDP — Đã gồm thuế</option><option>EXW — Tại xưởng TQ</option></select></Field>
            <Field label="Hàng / trọng lượng / CBM"><input placeholder="VD: Linh kiện — 3.800 kg / 16 CBM" className={inputCls()} /></Field>
          </div>
          <h4 className="font-bold text-[15px] mt-4 mb-2">Các dòng chi phí (VND) — thiếu dòng nào cứ để 0</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[["tq", "Vận tải TQ"], ["xk", "Khai xuất khẩu"], ["ck", "Cửa khẩu"], ["thue", "Thuế dự kiến"], ["vn", "Vận tải VN"], ["dv", "Dịch vụ"], ["ut", "Ủy thác"], ["other", "Khác"]].map(([k, l]) => (
              <Field key={k} label={l as string}><input type="number" value={(costs as any)[k] || ""} onChange={(e) => setC(k as any, e.target.value)} placeholder="0" className={inputCls()} /></Field>
            ))}
          </div>
          <div className="grid sm:grid-cols-2 gap-3 mt-3">
            <Field label="Giá bán cho khách (VND)" required><input type="number" value={price || ""} onChange={(e) => setPrice(Number(e.target.value) || 0)} className={inputCls()} /></Field>
            <div className="rounded-xl bg-[#0f2a4a] text-white p-3.5 grid grid-cols-3 gap-2 text-center items-center">
              <div><p className="text-[11.5px] text-blue-200">Chi phí</p><p className="font-extrabold text-[14px]">{fmtVND(totalCost)}</p></div>
              <div><p className="text-[11.5px] text-blue-200">Lợi nhuận</p><p className={cx("font-extrabold text-[14px]", profit < 0 ? "text-red-300" : "text-emerald-300")}>{fmtVND(profit)}</p></div>
              <div><p className="text-[11.5px] text-blue-200">Margin</p><p className="font-extrabold text-[16px] text-amber-300">{margin}%</p></div>
            </div>
          </div>
          {profit < 0 && <p className="mt-2 text-[13.5px] font-semibold text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">⚠ Giá bán đang thấp hơn chi phí {fmtVND(-profit)} — tăng giá hoặc giảm chi phí trước khi gửi khách.</p>}
          <div className="grid sm:grid-cols-2 gap-2.5 mt-3">
            <button onClick={() => toast("Đã lưu nháp BG-2026-217", "Báo giá DRAFT cho " + customer + " — gửi khách khi sẵn sàng.", "green")} className="btn-press touch-target rounded-xl border-2 border-slate-200 font-bold min-h-[52px]">Lưu nháp</button>
            <SuccessBtn onClick={() => toast("Đã gửi báo giá cho khách", customer + " — " + route + " — giá " + fmtVND(price) + ".", "green")}>GỬI KHÁCH HÀNG</SuccessBtn>
          </div>
        </section>
      )}
    </div>
  );
}

export function Agreements() {
  const { toast } = useStore();
  const tone = (s: string) => s === "AGREED" ? "green" : s === "REVIEWING" ? "amber" : s === "VOID" ? "red" : "blue";
  return (
    <div className="space-y-4 max-w-[1100px]">
      <SectionTitle title="Thỏa Thuận & Bàn Giao" sub="Báo giá chốt → thỏa thuận điều khoản → bàn giao Support kèm bằng chứng" />
      <div className="rounded-2xl bg-white border border-slate-200 p-4 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        {["1 · Báo giá", "2 · Khách chốt", "3 · Thỏa thuận", "4 · Bàn giao Support"].map((s, i) => (
          <div key={s} className="flex items-center gap-1.5 shrink-0">
            <span className={cx("rounded-xl px-3.5 py-2.5 text-[13.5px] font-extrabold whitespace-nowrap", i < 3 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-500")}>{i < 3 ? "✓ " : ""}{s}</span>
            {i < 3 && <ArrowRight size={15} className="text-slate-300" />}
          </div>
        ))}
      </div>
      <div className="grid gap-3">
        {AGREEMENTS.map((a) => (
          <section key={a.id} className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-extrabold text-[16px] text-[#0f2a4a]">{a.id}</span>
              <ToneBadge tone={tone(a.status) as any} size="sm">{a.status}</ToneBadge>
              <span className="text-[13px] text-slate-500">Báo giá {a.quote} · {a.customer}</span>
            </div>
            <div className="grid md:grid-cols-2 gap-x-6 mt-2.5 text-[14px]">
              <p><span className="text-slate-500">Incoterm:</span> <b>{a.incoterm}</b></p>
              <p><span className="text-slate-500">Thanh toán:</span> <b>{a.payment}</b></p>
              <p className="md:col-span-2"><span className="text-slate-500">Phạm vi:</span> {a.scope}</p>
              <p className="md:col-span-2"><span className="text-slate-500">Bàn giao:</span> <b>{a.handover}</b></p>
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              {a.status !== "AGREED" && <button onClick={() => toast("Đã chốt " + a.id, "Thỏa thuận chuyển sang AGREED — sẵn sàng bàn giao Support.", "green")} className="btn-press touch-target rounded-xl bg-emerald-600 text-white text-[14px] font-bold px-5 min-h-[48px]">KHÁCH ĐÃ CHỐT ĐIỀU KHOẢN</button>}
              <button onClick={() => toast("Đã bàn giao cho Support", "Biên bản bàn giao + checklist chứng từ đã gửi Thu Hằng.", "green")} className="btn-press touch-target rounded-xl bg-[#0f2a4a] text-white text-[14px] font-bold px-5 min-h-[48px]">BÀN GIAO SUPPORT</button>
              <Link to="/hop-dong/moi" className="btn-press touch-target inline-flex items-center rounded-xl border-2 border-slate-200 text-[14px] font-bold px-5 min-h-[48px]">Lập hợp đồng →</Link>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
