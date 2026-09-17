import { contractPath } from "../lib/contractRoute";
// ============================================================================
// Hợp đồng — Phase C1 list, donor Logi-good visual shell.
//
// Real contracts from core.database.load_contracts (projected by logi_c1).
// Rows link to the detail work desk (/hop-dong/:id); creation is a real write
// through the ONE bounded dispatcher (contract_create).
// ============================================================================

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Plus, Eye, ArrowRight, FileText } from "lucide-react";
import { SectionTitle, ToneBadge } from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtMoney } from "../lib/format";

export default function Contracts() {
  const { contracts } = useStore();
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("ALL");

  const list = useMemo(
    () =>
      contracts.filter(
        (c) =>
          (kind === "ALL" || c.kind === kind) &&
          (!q || (c.id + c.contractNo + c.client + c.company + c.agent).toLowerCase().includes(q.toLowerCase()))
      ),
    [contracts, q, kind]
  );
  const kinds = ["ALL", ...Array.from(new Set(contracts.map((c) => c.kind).filter(Boolean)))];

  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<FileText size={18} />}
          title="Hợp đồng"
          sub="HDMB · HDNT · PL — tìm theo số hợp đồng, khách, công ty, đại lý"
          right={<Link to="/hop-dong/moi" className="btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]"><Plus size={18} /> Tạo hợp đồng</Link>}
        />
        <div className="flex gap-2">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nhập số hợp đồng (HDMB-0306), khách (An Phát)…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
        </div>
        <div className="flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1">
          {kinds.map((k) => (
            <button key={k} onClick={() => setKind(k)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", kind === k ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>
              {k === "ALL" ? "Tất cả" : k}
            </button>
          ))}
        </div>
        <p className="text-[13.5px] text-slate-500 mt-1.5">Tìm thấy <b className="text-[#0f2a4a]">{list.length} hợp đồng</b> · Mở để xem hàng hóa, sinh chứng từ và liên kết lô.</p>
      </div>

      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="tbl w-full text-[14px] min-w-[880px]">
            <thead>
              <tr><th>Số hợp đồng</th><th>Loại</th><th>Khách hàng</th><th>Công ty · Đại lý</th><th>Giá trị</th><th>Hành động</th></tr>
            </thead>
            <tbody>
              {list.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50">
                  <td><Link to={contractPath(c.id)} className="font-extrabold text-[#1e5aa8] hover:underline text-[15px]">{c.id}</Link></td>
                  <td><ToneBadge tone="blue" size="sm">{c.kind || "—"}</ToneBadge></td>
                  <td className="font-semibold max-w-[180px]">{c.client || "—"}</td>
                  <td className="text-[13px] text-slate-600"><span className="block">{c.company || "—"}</span><span className="block text-slate-400">{c.agent || "—"}</span></td>
                  <td className="font-bold">{fmtMoney(c.value, c.currency)}</td>
                  <td><div className="flex gap-1.5"><Link to={contractPath(c.id)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px]"><Eye size={15} /> MỞ</Link></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {list.length === 0 && (
          <div className="p-8 text-center">
            <p className="font-bold text-[16px]">Không tìm thấy hợp đồng nào</p>
            <p className="text-[14px] text-slate-500 mt-1">Thử từ khóa khác hoặc tạo hợp đồng mới.</p>
            <Link to="/hop-dong/moi" className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5"><Plus size={17} /> Tạo hợp đồng</Link>
          </div>
        )}
      </div>

      <div className="md:hidden space-y-3">
        {list.map((c) => (
          <div key={c.id} className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-extrabold text-[17px] text-[#0f2a4a]">{c.id}</span>
                <ToneBadge tone="blue" size="sm">{c.kind || "—"}</ToneBadge>
              </div>
              <p className="font-semibold text-[14.5px] mt-1">{c.client || "—"}</p>
              <p className="text-[13px] text-slate-500">{c.company || "—"} · {c.agent || "—"}</p>
              <p className="font-extrabold text-[16px] mt-1.5">{fmtMoney(c.value, c.currency)}</p>
            </div>
            <div className="border-t">
              <Link to={contractPath(c.id)} className="touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]">MỞ HỢP ĐỒNG <ArrowRight size={17} /></Link>
            </div>
          </div>
        ))}
        {list.length === 0 && (
          <div className="rounded-2xl bg-white border p-8 text-center">
            <p className="font-bold text-[16px]">Không tìm thấy hợp đồng nào</p>
            <Link to="/hop-dong/moi" className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center"><Plus size={17} /> Tạo hợp đồng</Link>
          </div>
        )}
      </div>
    </div>
  );
}
