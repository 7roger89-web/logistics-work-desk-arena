import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, FileText, PenLine, Plus } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, SectionTitle, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { fmtVND, cx } from "../lib/format";

export default function NewContract() {
  const { toast } = useStore();
  const [step, setStep] = useState(1);
  const [agent, setAgent] = useState("Phú An Logistics Việt Nam");
  const [company, setCompany] = useState("");
  const [mst, setMst] = useState("");
  const [addr, setAddr] = useState("");
  const [created, setCreated] = useState<string | null>(null);

  const next1 = () => {
    if (!company.trim()) { toast("Thiếu tên công ty bên mua", "Nhập tên công ty — VD: Công ty TNHH Thiết Bị Minh Đức.", "red"); return; }
    if (!mst.trim()) { toast("Thiếu mã số thuế", "Nhập MST 10 số của bên mua để tra cứu pháp lý.", "amber"); return; }
    setStep(2);
  };
  const finish = () => {
    const no = "HDMB-PA-2026-033";
    setCreated(no);
    toast("Đã tạo " + no, "Hợp đồng nháp đã lưu — sang bước nhập hàng hóa để xuất chứng từ.", "green");
  };

  return (
    <div className="space-y-4 max-w-[860px]">
      <SectionTitle title="Tạo Hợp Đồng Mới" sub="3 bước: Bên mua → Hàng hóa → Xuất chứng từ. Mỗi bước đều báo rõ còn thiếu gì." />
      <div className="flex items-center gap-1.5">
        {["1 · Bên mua", "2 · Hàng hóa", "3 · Xuất"].map((s, i) => (
          <div key={s} className="flex items-center gap-1.5 flex-1">
            <span className={cx("flex-1 text-center rounded-xl py-2.5 text-[13.5px] font-extrabold", step > i + 1 || created ? "bg-emerald-600 text-white" : step === i + 1 ? "bg-[#0f2a4a] text-white" : "bg-white border text-slate-400")}>{created && i < 2 ? "✓ " : ""}{s}</span>
            {i < 2 && <ArrowRight size={15} className="text-slate-300 shrink-0" />}
          </div>
        ))}
      </div>

      {step === 1 && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-6 space-y-3.5">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Bước 1 — Chọn đại lý & bên mua</h3>
          <Field label="Đại lý (bên bán)"><select value={agent} onChange={(e) => setAgent(e.target.value)} className={inputCls()}><option>Phú Anh Logistics Việt Nam</option><option>Trường Thành — CN Lạng Sơn</option></select></Field>
          <div className="grid sm:grid-cols-2 gap-3.5">
            <Field label="Công ty bên mua" required error={!company.trim() ? "Nhập tên công ty — không để trống" : undefined}><input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="VD: Công ty TNHH Thiết Bị Minh Đức" className={inputCls(!company.trim() ? "missing" : "ok")} /></Field>
            <Field label="Mã số thuế" required error={!mst.trim() ? "Nhập MST để tra cứu & in hợp đồng" : undefined}><input value={mst} onChange={(e) => setMst(e.target.value)} inputMode="numeric" placeholder="VD: 0201884452" className={inputCls(!mst.trim() ? "missing" : "ok")} /></Field>
          </div>
          <Field label="Địa chỉ bên mua"><input value={addr} onChange={(e) => setAddr(e.target.value)} placeholder="VD: KCN Tràng Duệ, Hải Phòng" className={inputCls()} /></Field>
          {!company.trim() && <p className="text-[13.5px] text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3">⚠ Thiếu tên công ty — nhập tên thì nút “Tiếp tục” mới đi tiếp được.</p>}
          <PrimaryBtn onClick={next1} className="w-full">TIẾP TỤC → NHẬP HÀNG HÓA <ArrowRight size={17} /></PrimaryBtn>
        </section>
      )}

      {step === 2 && !created && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-6 space-y-3.5">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Bước 2 — Xác nhận & tạo nháp</h3>
          <div className="rounded-xl bg-slate-50 border p-4 text-[14.5px] space-y-1">
            <p>Đại lý: <b>{agent}</b></p>
            <p>Bên mua: <b>{company}</b> · MST {mst}</p>
            {addr && <p>Địa chỉ: {addr}</p>}
          </div>
          <p className="text-[13.5px] text-slate-500">Bấm “Tạo nháp” để sinh số HDMB-033, sau đó nhập từng dòng hàng hóa ở màn hình chi tiết (máy tự tính VAT 8% & gợi ý HDMB/HDNT).</p>
          <div className="grid grid-cols-2 gap-2.5">
            <GhostBtn onClick={() => setStep(1)}>← Sửa bên mua</GhostBtn>
            <PrimaryBtn onClick={finish}>➕ TẠO NHÁP HỢP ĐỒNG</PrimaryBtn>
          </div>
        </section>
      )}

      {created && (
        <section className="rounded-2xl bg-white border-2 border-emerald-300 p-5 md:p-6 text-center">
          <span className="w-14 h-14 rounded-full bg-emerald-600 text-white grid place-items-center mx-auto"><CheckCircle2 size={28} /></span>
          <h3 className="font-extrabold text-[19px] text-[#0f2a4a] mt-3">✅ ĐÃ TẠO NHÁP {created}</h3>
          <p className="text-[14.5px] text-slate-600 mt-1">Bên mua: <b>{company}</b> · Tiếp theo: nhập hàng hóa → máy gợi ý phương án chứng từ → xuất file.</p>
          <div className="grid sm:grid-cols-2 gap-2.5 mt-4">
            <Link to={"/hop-dong/HDMB-PA-2026-032"} className="btn-press touch-target flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]"><PenLine size={17} /> NHẬP HÀNG HÓA NGAY</Link>
            <Link to="/hop-dong" className="btn-press touch-target flex items-center justify-center gap-2 rounded-xl border-2 border-slate-200 font-bold min-h-[52px]"><FileText size={17} /> Về danh sách</Link>
          </div>
        </section>
      )}
    </div>
  );
}
