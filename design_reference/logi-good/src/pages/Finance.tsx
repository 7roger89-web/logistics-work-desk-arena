import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, Plus, Scale, Wallet } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, SectionTitle, StateRow, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { fmtMoney, fmtVND, cx } from "../lib/format";

const DEBTS = [
  { customer: "Cơ Khí An Phát", lot: "LO-0306", contract: "HDMB-PA-2026-031", must: 486500000, got: 150000000, due: "09/09/2026", status: "Hạn hôm nay", tone: "red" as const },
  { customer: "Phụ Kiện Hồng Hà", lot: "LO-0299", contract: "HDMB-PA-2026-027", must: 214600000, got: 100000000, due: "12/09/2026", status: "Còn 3 ngày", tone: "amber" as const },
  { customer: "Cơ Khí An Phát", lot: "LO-0295", contract: "HDMB-PA-2026-031", must: 386500000, got: 300000000, due: "12/09/2026", status: "Còn 3 ngày", tone: "blue" as const },
];

export function Collect() {
  const { toast, shipments } = useStore();
  const [show, setShow] = useState(false);
  const [amt, setAmt] = useState("");
  const [lot, setLot] = useState("LO-0306");
  const rest = (d: typeof DEBTS[0]) => d.must - d.got;
  return (
    <div className="space-y-4 max-w-[1200px]">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          ["Tổng phải thu", "1.087,6 tr", "bg-white border", "text-[#0f2a4a]"],
          ["Đã thu", "550,0 tr", "bg-emerald-600 text-white", "text-white"],
          ["Còn phải thu", "537,6 tr", "bg-white border-2 border-red-300", "text-red-700"],
          ["Quá hạn / hạn nay", "1 khoản", "bg-red-600 text-white", "text-white"],
          ["Phải trả đối tác", "73,8 tr", "bg-white border-2 border-amber-300", "text-[#0f2a4a]"],
        ].map(([l, v, bg, tc]) => (
          <div key={l as string} className={cx("rounded-2xl border border-slate-200 p-3.5", bg as string)}>
            <p className="text-[12.5px] font-semibold opacity-70">{l}</p>
            <p className={cx("text-[20px] md:text-[22px] font-extrabold", tc as string)}>{v}</p>
          </div>
        ))}
      </div>

      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle title="Thu Tiền & Công Nợ" sub="Hiện trạng từng khoản → còn thiếu bao nhiêu → bấm thu ngay" right={<button onClick={() => setShow(true)} className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold text-[14.5px] px-4 min-h-[48px]"><Plus size={17} /> GHI NHẬN THANH TOÁN</button>} />
        <div className="hidden md:block overflow-x-auto"><table className="tbl w-full text-[14px] min-w-[940px]">
          <thead><tr><th>Khách hàng</th><th>Lô · Hợp đồng</th><th>Phải thu</th><th>Đã thu</th><th>Còn lại</th><th>Hạn</th><th>Trạng thái</th><th></th></tr></thead>
          <tbody>{DEBTS.map((d) => (
            <tr key={d.lot} className="hover:bg-slate-50">
              <td className="font-bold">{d.customer}</td>
              <td className="text-[13px]"><Link to={"/lo-hang/" + d.lot} className="font-bold text-[#1e5aa8]">{d.lot}</Link><span className="block text-slate-500">{d.contract}</span></td>
              <td className="whitespace-nowrap">{fmtVND(d.must)}</td><td className="whitespace-nowrap text-emerald-700 font-semibold">{fmtVND(d.got)}</td>
              <td className="font-extrabold text-red-700 whitespace-nowrap">{fmtVND(rest(d))}</td>
              <td className="whitespace-nowrap font-semibold">{d.due}</td>
              <td><ToneBadge tone={d.tone} size="sm">{d.status}</ToneBadge></td>
              <td><button onClick={() => { setLot(d.lot); setAmt(String(rest(d))); setShow(true); }} className="btn-press touch-target rounded-lg bg-emerald-600 text-white text-[13px] font-bold px-3.5 min-h-[44px] whitespace-nowrap">THU NGAY</button></td>
            </tr>))}</tbody>
        </table></div>
        <div className="md:hidden space-y-3">
          {DEBTS.map((d) => (
            <div key={d.lot} className="rounded-2xl border-2 border-slate-200 p-4">
              <div className="flex items-center gap-2"><span className="font-extrabold text-[16px]">{d.lot}</span><ToneBadge tone={d.tone} size="sm">{d.status}</ToneBadge></div>
              <p className="text-[14px] text-slate-600">{d.customer} · Hạn {d.due}</p>
              <div className="grid grid-cols-3 gap-1.5 mt-2 text-center text-[12.5px]">
                <div className="rounded-lg bg-slate-50 border p-2"><p className="text-slate-500">Phải thu</p><b>{(d.must / 1e6).toFixed(0)}tr</b></div>
                <div className="rounded-lg bg-emerald-50 border p-2"><p className="text-slate-500">Đã thu</p><b>{(d.got / 1e6).toFixed(0)}tr</b></div>
                <div className="rounded-lg bg-red-50 border border-red-200 p-2"><p className="text-slate-500">Còn lại</p><b className="text-red-700">{(rest(d) / 1e6).toFixed(1)}tr</b></div>
              </div>
              <button onClick={() => { setLot(d.lot); setAmt(String(rest(d))); setShow(true); }} className="btn-press touch-target mt-2.5 w-full rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">THU {fmtVND(rest(d))}</button>
            </div>
          ))}
        </div>
      </section>

      {show && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55" onClick={() => setShow(false)} />
          <div className="relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up">
            <h3 className="font-extrabold text-[18px]">Ghi nhận thanh toán</h3>
            <div className="grid gap-3 mt-3">
              <Field label="Lô hàng"><select value={lot} onChange={(e) => setLot(e.target.value)} className={inputCls()}><option>LO-0306</option><option>LO-0299</option><option>LO-0295</option></select></Field>
              <Field label="Số tiền (VND)" required><input value={amt} onChange={(e) => setAmt(e.target.value)} inputMode="numeric" placeholder="VD: 150000000" className={inputCls()} /></Field>
              <Field label="Hình thức"><select className={inputCls()}><option>Chuyển khoản Vietcombank</option><option>Chuyển khoản Techcombank</option><option>Tiền mặt</option></select></Field>
            </div>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setShow(false)}>Hủy</GhostBtn>
              <SuccessBtn onClick={() => { if (!amt) { toast("Chưa nhập số tiền", "Nhập số tiền rồi bấm Lưu.", "red"); return; } setShow(false); toast("Đã ghi nhận " + fmtVND(Number(amt.replace(/\D/g, "")) || 0), "Lô " + lot + " — biên lai đã lưu vào lịch sử.", "green"); }}>💾 LƯU KHOẢN THU</SuccessBtn>
            </div>
          </div>
        </div>
      )}
      <div className="md:hidden sticky-action -mx-3 px-3 py-3"><button onClick={() => setShow(true)} className="btn-press touch-target w-full rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">＋ GHI NHẬN THANH TOÁN</button></div>
    </div>
  );
}

export function Reconcile() {
  const { toast } = useStore();
  const [done, setDone] = useState(false);
  return (
    <div className="space-y-4 max-w-[1000px]">
      <SectionTitle title="Đối Soát Tài Chính" sub="Chốt số với đại lý Bằng Tường — tiền Việt và tiền Trung tách riêng, không gộp" />
      <div className="grid md:grid-cols-2 gap-4">
        <section className="rounded-2xl bg-white border-2 border-amber-300 p-5">
          <p className="text-[13px] font-extrabold text-amber-700">SỔ VND — ĐẠI LÝ BẰNG TƯỜNG</p>
          <div className="mt-2">
            <StateRow label="Số dư đầu kỳ" value={fmtVND(120000000)} />
            <StateRow label="Phát sinh tăng (cước 9 lô)" value={"+ " + fmtVND(96500000)} />
            <StateRow label="Phát sinh giảm (đã thanh toán)" value={"− " + fmtVND(142700000)} />
            <StateRow label="Số dư còn lại phải trả" value={<span className="font-extrabold text-[19px] text-amber-800">{fmtVND(73800000)}</span>} big />
          </div>
        </section>
        <section className="rounded-2xl bg-white border-2 border-blue-300 p-5">
          <p className="text-[13px] font-extrabold text-blue-700">SỔ CNY — ĐẠI LÝ BẰNG TƯỜNG (¥)</p>
          <div className="mt-2">
            <StateRow label="Số dư đầu kỳ" value="¥45.200" />
            <StateRow label="Phát sinh tăng (xe TQ T9)" value="+ ¥27.700" />
            <StateRow label="Đã thanh toán" value="− ¥45.200" />
            <StateRow label="Số dư còn lại phải trả" value={<span className="font-extrabold text-[19px] text-blue-800">¥27.700</span>} big />
          </div>
          <p className="text-[12.5px] text-slate-400 mt-2">Tuyệt đối không quy đổi gộp 2 sổ — mỗi đồng tiền đối soát riêng.</p>
        </section>
      </div>
      <section className="rounded-2xl bg-white border border-slate-200 p-5">
        <h3 className="font-extrabold text-[15.5px] mb-2">Checklist trước khi chốt</h3>
        {[["Đủ biên lai 9 lô tháng 9", true], ["Cước xe TQ LO-0307 (9.200 CNY) đã khớp", false], ["Thuế + VAT LO-0306 đã có biên lai", false]].map(([t, ok]) => (
          <div key={t as string} className="flex items-center gap-2.5 py-2 border-b last:border-0 text-[14.5px]">
            <span className={cx("w-6 h-6 rounded-full grid place-items-center text-[13px] font-bold", ok ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-500")}>{ok ? "✓" : "·"}</span>
            <span className={ok ? "" : "font-semibold"}>{t}</span>
            {!ok && <button onClick={() => toast("Mở chứng từ liên quan", "Bổ sung biên lai rồi quay lại chốt.", "blue")} className="ml-auto text-[13px] font-bold text-[#1e5aa8] border rounded-lg px-2.5 py-1.5">Bổ sung →</button>}
          </div>
        ))}
        <button onClick={() => { setDone(true); toast("Đã chốt đối soát tháng 9", "Biên bản đã lưu — 2 sổ VND + CNY đều cân.", "green"); }} className="btn-press touch-target mt-3 w-full sm:w-auto rounded-xl bg-[#0f2a4a] text-white font-extrabold px-8 min-h-[52px] inline-flex items-center justify-center gap-2"><Scale size={18} /> CHỐT ĐỐI SOÁT THÁNG 9</button>
        {done && <p className="mt-2 text-[14px] text-emerald-700 font-bold flex items-center gap-1.5"><CheckCircle2 size={17} /> Đã chốt lúc 09/09/2026 — xem biên bản ở Lịch sử.</p>}
      </section>
    </div>
  );
}

export function PartnerDebt() {
  return (
    <div className="space-y-4 max-w-[1100px]">
      <SectionTitle title="Công Nợ Đối Tác" sub="Mỗi đối tác 1 sổ riêng — dư đầu, tăng, giảm, đã trả, còn lại" />
      <div className="hidden md:block rounded-2xl bg-white border overflow-hidden"><div className="overflow-x-auto"><table className="tbl w-full text-[14px] min-w-[860px]">
        <thead><tr><th>Đối tác</th><th>Số dư đầu</th><th>Phát sinh tăng</th><th>Phát sinh giảm</th><th>Đã thanh toán</th><th>Còn lại</th><th></th></tr></thead>
        <tbody>
          <tr><td className="font-bold">Bằng Tường (VND)</td><td>120,0 tr</td><td className="text-red-700 font-semibold">+96,5 tr</td><td>−142,7 tr</td><td>142,7 tr</td><td className="font-extrabold text-amber-800">73,8 tr</td><td><Link to="/tai-chinh/doi-soat" className="font-bold text-[#1e5aa8]">Đối soát →</Link></td></tr>
          <tr><td className="font-bold">Bằng Tường (CNY)</td><td>¥45.200</td><td className="font-semibold">+¥27.700</td><td>−¥45.200</td><td>¥45.200</td><td className="font-extrabold">¥27.700</td><td><Link to="/tai-chinh/doi-soat" className="font-bold text-[#1e5aa8]">Đối soát →</Link></td></tr>
          <tr><td className="font-bold">Nhà xe Hải Phòng (VND)</td><td>0</td><td>+22,0 tr</td><td>−22,0 tr</td><td>22,0 tr</td><td className="font-bold text-emerald-700">0 ✓</td><td><span className="text-slate-400 text-[13px]">Đã xong</span></td></tr>
        </tbody>
      </table></div></div>
      <div className="md:hidden space-y-3">
        {[["Bằng Tường (VND)", "Còn lại 73,8 tr ₫ — cần đối soát"], ["Bằng Tường (CNY)", "Còn lại ¥27.700"], ["Nhà xe Hải Phòng", "Đã xong ✓ — còn 0"]].map(([t, d]) => (
          <div key={t as string} className="rounded-2xl bg-white border p-4"><p className="font-extrabold">{t}</p><p className="text-[14px] text-slate-600 mt-0.5">{d}</p><Link to="/tai-chinh/doi-soat" className="btn-press touch-target mt-2.5 flex items-center justify-center gap-1 rounded-xl bg-[#0f2a4a] text-white font-bold min-h-[48px]">MỞ ĐỐI SOÁT <ArrowRight size={16} /></Link></div>
        ))}
      </div>
    </div>
  );
}
