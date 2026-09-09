import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, Languages, Search } from "lucide-react";
import { Field, PrimaryBtn, SectionTitle, ToneBadge, inputCls } from "../components/ui";
import { HS_DATA, USERS } from "../lib/data";
import type { Role } from "../lib/data";
import { cx } from "../lib/format";
import { useStore } from "../lib/store";

export function Tracking() {
  const { shipments } = useStore();
  return (
    <div className="space-y-4 max-w-[1100px]">
      <SectionTitle title="Theo Dõi Vận Chuyển" sub="Vị trí & mốc thời gian từng lô — xe TQ tới đâu, hàng đang ở đâu" />
      <div className="grid gap-3">
        {shipments.map((s) => (
          <section key={s.id} className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-extrabold text-[16.5px] text-[#0f2a4a]">{s.id}</span>
              <ToneBadge tone={s.statusTone} size="sm">{s.status}</ToneBadge>
              <Link to={"/lo-hang/" + s.id} className="ml-auto text-[13.5px] font-bold text-[#1e5aa8] inline-flex items-center gap-1">Mở workspace <ArrowRight size={15} /></Link>
            </div>
            <div className="mt-3 flex items-center gap-1 overflow-x-auto no-scrollbar">
              {["Lấy hàng", "Xuất khẩu", "Cửa khẩu", "Thông quan", "Giao hàng"].map((st, i) => {
                const doneIdx = s.id === "LO-0295" ? 5 : s.id === "LO-0299" ? 4 : s.id === "LO-0306" ? 3 : s.id === "LO-0307" ? 2 : 1;
                const done = i < doneIdx;
                return (
                  <div key={st} className="flex items-center gap-1 shrink-0">
                    <div className="flex flex-col items-center">
                      <span className={cx("w-9 h-9 rounded-full grid place-items-center text-[14px] font-extrabold", done ? "bg-emerald-600 text-white" : i === doneIdx ? "bg-amber-500 text-white pulse-dot" : "bg-slate-100 text-slate-400")}>{done ? "✓" : i + 1}</span>
                      <span className={cx("text-[11.5px] font-bold mt-1 whitespace-nowrap", done || i === doneIdx ? "text-[#0f2a4a]" : "text-slate-400")}>{st}</span>
                    </div>
                    {i < 4 && <span className={cx("w-8 md:w-14 h-1 rounded-full mb-5", i < doneIdx - 0.5 ? "bg-emerald-500" : "bg-slate-200")} />}
                  </div>
                );
              })}
            </div>
            <p className="text-[13.5px] text-slate-600 mt-2">📍 {s.timeline[s.timeline.length - 1]?.title} — {s.timeline[s.timeline.length - 1]?.time}</p>
          </section>
        ))}
      </div>
    </div>
  );
}

export function NewLot() {
  const { toast } = useStore();
  const [quote, setQuote] = useState("BG-2026-214 (Minh Đức — ĐÃ CHỐT)");
  const [customer, setCustomer] = useState("Công ty TNHH Thiết Bị Minh Đức");
  const [routeV, setRouteV] = useState("Quảng Đông → Hữu Nghị → Hải Phòng");
  const [done, setDone] = useState(false);
  return (
    <div className="space-y-4 max-w-[860px]">
      <SectionTitle title="Tạo Lô Mới" sub="Tạo từ báo giá đã chốt — thông tin tự điền, chỉ bổ sung phần thiếu" />
      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-6 space-y-3.5">
        <Field label="Tạo từ báo giá đã chốt" hint="Chọn báo giá ACCEPTED — khách, tuyến, hàng tự điền"><select value={quote} onChange={(e) => setQuote(e.target.value)} className={inputCls()}><option>BG-2026-214 (Minh Đức — ĐÃ CHỐT)</option><option>BG-2026-212 (An Phát — ĐÃ CHỐT)</option><option>Nhập tay (không từ báo giá)</option></select></Field>
        <div className="grid sm:grid-cols-2 gap-3.5">
          <Field label="Khách hàng" required><input value={customer} onChange={(e) => setCustomer(e.target.value)} className={inputCls()} /></Field>
          <Field label="Tuyến" required><select value={routeV} onChange={(e) => setRouteV(e.target.value)} className={inputCls()}><option>Quảng Đông → Hữu Nghị → Hải Phòng</option><option>Quảng Đông → Hữu Nghị → Hà Nội</option><option>Quảng Tây → Tân Thanh → Bắc Ninh</option></select></Field>
          <Field label="Cửa khẩu TQ"><select className={inputCls()}><option>Hữu Nghị (TQ)</option><option>Tân Thanh (TQ)</option></select></Field>
          <Field label="Ngày dự kiến lấy hàng" required error={undefined}><input placeholder="VD: 12/09/2026 09:00" className={inputCls("missing")} /></Field>
        </div>
        <Field label="Hàng hóa"><input placeholder="VD: Máy CNC — 2 máy — 18.500 kg" className={inputCls()} /></Field>
        {!done ? (
          <PrimaryBtn onClick={() => { setDone(true); toast("Đã tạo lô LO-0309 (nháp)", "Tiếp theo: chốt xe TQ & giờ lấy ở tab Lấy hàng.", "green"); }} className="w-full">➕ TẠO LÔ HÀNG</PrimaryBtn>
        ) : (
          <div className="rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center">
            <p className="font-extrabold text-emerald-800 text-[16px]">✅ ĐÃ TẠO LO-0309 (NHÁP)</p>
            <p className="text-[13.5px] text-emerald-700">Tiếp theo: chốt xe TQ + giờ lấy hàng.</p>
            <div className="grid sm:grid-cols-2 gap-2 mt-3">
              <Link to="/lo-hang/LO-0308?tab=lay-hang" className="btn-press touch-target flex items-center justify-center rounded-xl bg-emerald-600 text-white font-bold min-h-[48px]">MỞ TAB LẤY HÀNG MẪU →</Link>
              <Link to="/lo-hang" className="btn-press touch-target flex items-center justify-center rounded-xl border-2 border-slate-200 font-bold min-h-[48px]">Về danh sách lô</Link>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

export function HSLookup() {
  const [q, setQ] = useState("");
  const { toast } = useStore();
  const list = useMemo(() => HS_DATA.filter((h) => !q || (h.hs + h.desc).toLowerCase().includes(q.toLowerCase())), [q]);
  return (
    <div className="space-y-4 max-w-[1100px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle title="Tra Cứu Thuế / HS" sub="Nhập mã HS hoặc tên hàng — xem thuế NK, VAT, chính sách" />
        <div className="flex items-center rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
          <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="VD: 8457 (máy CNC) hoặc 'board mạch'… " className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {list.map((h) => (
          <section key={h.hs} className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <div className="flex items-center gap-2 flex-wrap"><span className="font-extrabold text-[17px] text-[#0f2a4a]">HS {h.hs}</span><span className="text-[12.5px] font-bold bg-blue-100 text-blue-800 rounded-md px-2 py-1">NK {h.nk}</span><span className="text-[12.5px] font-bold bg-emerald-100 text-emerald-800 rounded-md px-2 py-1">VAT {h.vat}</span></div>
            <p className="font-semibold text-[14.5px] mt-1.5">{h.desc}</p>
            <p className="text-[13.5px] text-slate-600 mt-1">📌 Chính sách: {h.policy}</p>
            <p className="text-[13px] text-slate-500">📝 {h.note}</p>
            <button onClick={() => toast("Đã gắn HS " + h.hs + " cho lô", "Mở lô hàng → tab Nhập khẩu để áp thuế " + h.nk + " + VAT " + h.vat + ".", "green")} className="btn-press touch-target mt-3 w-full rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] min-h-[48px]">DÙNG CHO LÔ HÀNG</button>
          </section>
        ))}
        {list.length === 0 && <div className="rounded-2xl bg-white border-2 border-dashed p-8 text-center text-slate-500 md:col-span-2">Không tìm thấy mã HS. Thử “8457”, “máy”, “mạch” hoặc “phụ kiện”.</div>}
      </div>
    </div>
  );
}

export function Handbook() {
  const items = [
    ["Sale mới: từ báo giá tới hợp đồng", "1. Lập báo giá → 2. Gửi khách → 3. Khách chốt → 4. Lập thỏa thuận → 5. Tạo hợp đồng → 6. Gắn lô. Mỗi bước đều có nút dẫn tiếp.", "5 phút"],
    ["Support: xử lý lô từ lấy hàng tới giao", "Chốt xe TQ → theo dõi xuất khẩu → khai nhập (số TK 12 số) → nộp thuế → đặt xe VN → giao & xác nhận → xuất PXK → thu tiền.", "7 phút"],
    ["Khi thiếu chứng từ phải làm gì?", "Không bỏ qua cảnh báo: bấm BỔ SUNG ngay tại chỗ, tải file hoặc ghi lý do + hạn. Mọi cảnh báo đều kèm nút hành động.", "3 phút"],
    ["Ngưỡng 50 triệu: HDNT+PL hay HDMB?", "Tổng sau VAT dưới 50tr → HDNT + PL. Từ đúng 50tr trở lên → HDMB. Máy tự gợi ý, bạn chỉ nhập ngày ký.", "2 phút"],
  ];
  return (
    <div className="space-y-4 max-w-[900px]">
      <SectionTitle title="Sổ Tay Kinh Nghiệm" sub="Hướng dẫn từng bước bằng tiếng Việt đơn giản — cho người mới & cô chú lớn tuổi" />
      {items.map(([t, d, time]) => (
        <section key={t as string} className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 flex gap-3.5">
          <span className="w-11 h-11 rounded-xl bg-[#0f2a4a] text-white grid place-items-center shrink-0"><BookOpen size={20} /></span>
          <div><p className="font-extrabold text-[15.5px] text-[#0f2a4a]">{t} <span className="text-[12px] font-semibold text-slate-400">· {time} đọc</span></p><p className="text-[14px] text-slate-600 mt-1">{d}</p></div>
        </section>
      ))}
    </div>
  );
}

export function Translate() {
  const { toast } = useStore();
  const [src, setSrc] = useState("装箱单 — 42件, 毛重12800KG");
  const out = src.includes("装箱") ? "Phiếu đóng gói — 42 kiện, trọng lượng cả bì 12.800 KG" : src.includes("发票") ? "Hóa đơn thương mại" : "Nhập câu tiếng Trung để xem bản dịch Việt (bản mẫu: 装箱单 / 发票 / 提单 / 原产地证).";
  return (
    <div className="space-y-4 max-w-[900px]">
      <SectionTitle title="Dịch Thuật" sub="Dịch nhanh chứng từ Trung ↔ Việt cho Support" />
      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-3">
        <Field label="Tiếng Trung (dán nội dung chứng từ)"><textarea value={src} onChange={(e) => setSrc(e.target.value)} rows={3} className={inputCls()} /></Field>
        <div className="flex gap-2 flex-wrap">
          {["装箱单", "商业发票", "提单", "原产地证"].map((w) => (<button key={w} onClick={() => setSrc(w + " — mẫu")} className="touch-target rounded-lg border-2 border-slate-200 px-3 min-h-[44px] text-[14px] font-bold">{w}</button>))}
        </div>
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4"><p className="text-[12.5px] font-bold uppercase tracking-wide text-emerald-700">Tiếng Việt</p><p className="font-bold text-[16px] mt-1">{out}</p></div>
        <button onClick={() => toast("Đã chép bản dịch", "Dán vào ghi chú lô hàng hoặc gửi khách.", "green")} className="btn-press touch-target rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] inline-flex items-center gap-2"><Languages size={17} /> CHÉP BẢN DỊCH</button>
      </section>
    </div>
  );
}

export function Users() {
  const { role, toast } = useStore();
  const [users, setUsers] = useState(USERS);
  if (role !== "ADMIN") return (
    <div className="rounded-2xl bg-white border-2 border-red-200 p-8 text-center max-w-[560px] mx-auto">
      <p className="font-extrabold text-[19px] text-red-800">⛔ Khu vực Admin</p>
      <p className="text-[14.5px] text-slate-600 mt-1.5">Vì sao bị chặn: vai trò hiện tại là <b>{role}</b> — chỉ ADMIN được xem & đổi quyền người dùng.</p>
      <p className="text-[14px] text-slate-500 mt-1">Tiếp theo: chuyển vai trò sang ADMIN ở góc phải header để xem mẫu.</p>
    </div>
  );
  const cycle = (u: string) => setUsers((arr) => arr.map((x) => x.username === u ? { ...x, role: (x.role === "ADMIN" ? "SUPPORT" : x.role === "SUPPORT" ? "SALE" : "ADMIN") as Role } : x));
  const lock = (u: string) => { setUsers((arr) => arr.map((x) => x.username === u ? { ...x, status: x.status === "Tạm khóa" ? "Đang hoạt động" : "Tạm khóa" } : x)); toast("Đã cập nhật trạng thái", "Tài khoản " + u, "blue"); };
  return (
    <div className="space-y-4 max-w-[1100px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle title="Người Dùng (Admin)" sub="Tên · tài khoản · vai trò · trạng thái · đăng nhập cuối" right={<button onClick={() => toast("Mở form tạo người dùng", "Nhập tên + chọn vai trò — tài khoản mẫu: ten.sale.", "blue")} className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14px] px-4 min-h-[48px]">＋ Tạo người dùng</button>} />
        <div className="hidden md:block overflow-x-auto"><table className="tbl w-full text-[14px] min-w-[820px]">
          <thead><tr><th>Tên</th><th>Tài khoản</th><th>Vai trò</th><th>Trạng thái</th><th>Đăng nhập cuối</th><th>Hành động</th></tr></thead>
          <tbody>{users.map((u) => (
            <tr key={u.username}><td className="font-bold">{u.name}</td><td className="text-slate-500">{u.username}</td>
              <td><button onClick={() => cycle(u.username)} title="Bấm để đổi role" className={cx("text-[12.5px] font-extrabold rounded-full px-3 py-1", u.role === "ADMIN" ? "bg-violet-100 text-violet-800" : u.role === "SUPPORT" ? "bg-blue-100 text-blue-800" : "bg-emerald-100 text-emerald-800")}>{u.role} ⇄</button></td>
              <td>{u.status === "Tạm khóa" ? <span className="text-red-700 font-bold">🔒 Tạm khóa</span> : <span className="text-emerald-700 font-bold">● Đang hoạt động</span>}</td>
              <td className="text-[13px] text-slate-500">{u.last}</td>
              <td><button onClick={() => lock(u.username)} className="touch-target text-[13px] font-bold border-2 rounded-lg px-3 min-h-[40px] border-slate-200">{u.status === "Tạm khóa" ? "Mở khóa" : "Khóa TK"}</button></td>
            </tr>))}</tbody>
        </table></div>
        <div className="md:hidden space-y-2.5">
          {users.map((u) => (
            <div key={u.username} className="rounded-xl border p-3.5">
              <p className="font-extrabold">{u.name}</p><p className="text-[13px] text-slate-500">{u.username} · {u.last}</p>
              <div className="flex gap-2 mt-2"><button onClick={() => cycle(u.username)} className="touch-target flex-1 rounded-lg bg-slate-100 font-bold text-[13.5px] min-h-[44px]">{u.role} ⇄ đổi</button><button onClick={() => lock(u.username)} className="touch-target flex-1 rounded-lg border-2 border-slate-200 font-bold text-[13.5px] min-h-[44px]">{u.status === "Tạm khóa" ? "Mở khóa" : "Khóa"}</button></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
