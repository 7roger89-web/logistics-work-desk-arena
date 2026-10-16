import { useCallback, useMemo, useState, useSyncExternalStore } from "react";
import { Link } from "react-router-dom";
import { useQueryParam } from "../lib/queryParam";
import { ArrowRight, ListFilter, Plus } from "lucide-react";
import { PrimaryBtn, SectionTitle, ToneBadge } from "../components/ui";
import TaskCreateSheet from "../components/TaskCreateSheet";
import { useStore } from "../lib/store";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import { cx } from "../lib/format";

const LEVEL = {
  Khan: { label: "Khẩn", cls: "bg-red-600 text-white" },
  CanXuLy: { label: "Cần xử lý", cls: "bg-amber-400 text-amber-950" },
  BinhThuong: { label: "Bình thường", cls: "bg-slate-200 text-slate-700" },
} as const;

export default function Tasks() {
  const { tasks } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const canCreate = Boolean(vm?.taskAssignment?.canCreate);
  const [createOpen, setCreateOpen] = useState(false);
  const [success, setSuccess] = useState("");
  const onTaskCreated = useCallback(() => setSuccess("Đã giao việc và đọc lại từ danh sách công việc."), []);
  // LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — filter/query survive opening a task
  // target and coming back (route search params, no global store).
  const [levelRaw, setLevelRaw] = useQueryParam("level");
  const filter = (levelRaw || "ALL") as "ALL" | "Khan" | "CanXuLy" | "BinhThuong";
  const setFilter = (f: "ALL" | "Khan" | "CanXuLy" | "BinhThuong") => setLevelRaw(f === "ALL" ? "" : f);
  const [q, setQ] = useQueryParam("q");
  const list = useMemo(() => tasks.filter((t) => (filter === "ALL" || t.level === filter) && (!q || (t.lot + t.customer + t.job + t.assignee).toLowerCase().includes(q.toLowerCase()))), [tasks, filter, q]);
  // Real counts from the view-model task projection — never a hardcoded KPI.
  const counts = useMemo(() => ({
    ALL: tasks.length,
    Khan: tasks.filter((t) => t.level === "Khan").length,
    CanXuLy: tasks.filter((t) => t.level === "CanXuLy").length,
    BinhThuong: tasks.filter((t) => t.level === "BinhThuong").length,
  }), [tasks]);

  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          title="Việc Cần Xử Lý"
          sub="Hiện trạng → việc thiếu → bấm XỬ LÝ NGAY để tới đúng ô cần nhập. Làm mục Khẩn trước 17:00."
          right={canCreate ? <PrimaryBtn testId="task-create-open" onClick={() => { setSuccess(""); setCreateOpen(true); }}><Plus size={17} /> Giao việc</PrimaryBtn> : undefined}
        />
        {!canCreate && <p data-testid="task-create-readonly" className="mb-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-[13px] text-slate-600">Tài khoản hiện tại chỉ xem được công việc; quyền giao việc được kiểm tra lại ở backend.</p>}
        {success && <p role="status" data-testid="task-create-success" className="mb-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-[13.5px] font-semibold text-emerald-800">{success}</p>}
        <div className="flex flex-col md:flex-row gap-2.5">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Lọc theo mã lô, khách hàng, người phụ trách…" className="flex-1 rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] focus:border-[#1e5aa8] outline-none" />
          <div className="flex gap-2 overflow-x-auto no-scrollbar">
            {(["ALL", "Khan", "CanXuLy", "BinhThuong"] as const).map((f) => (
              <button key={f} onClick={() => setFilter(f)} className={cx("touch-target shrink-0 rounded-xl border-2 px-4 min-h-[48px] text-[14.5px] font-bold", filter === f ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{f === "ALL" ? `Tất cả (${counts.ALL})` : f === "Khan" ? `Khẩn (${counts.Khan})` : f === "CanXuLy" ? `Cần xử lý (${counts.CanXuLy})` : `Bình thường (${counts.BinhThuong})`}</button>
            ))}
          </div>
        </div>
      </div>

      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
        <table className="tbl w-full text-[14.5px] min-w-[980px]">
          <thead><tr><th>Ưu tiên</th><th>Mã lô</th><th>Khách hàng</th><th>Việc cần làm</th><th>Người phụ trách</th><th>Hạn</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
          <tbody>
            {list.map((t) => (
              <tr key={t.id} className="hover:bg-slate-50">
                <td><span className={cx("inline-flex items-center gap-1.5 text-[12.5px] font-extrabold rounded-full px-2.5 py-1 whitespace-nowrap", LEVEL[t.level].cls)}>{LEVEL[t.level].label}</span></td>
                <td className="font-extrabold text-[#0f2a4a]"><Link to={t.route} className="hover:underline whitespace-nowrap">{t.lot}</Link></td>
                <td>{t.customer}</td>
                <td className="max-w-[260px]"><span className="font-semibold">{t.job}</span></td>
                <td className="whitespace-nowrap">{t.assignee}</td>
                <td><span className="font-bold text-red-700 whitespace-nowrap">{t.due}</span><span className="block text-[12.5px] text-slate-500">{t.dueNote}</span></td>
                <td><ToneBadge tone={t.statusTone} size="sm">{t.status}</ToneBadge></td>
                <td><Link to={t.route} className="btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-[#0f2a4a] text-white text-[13.5px] font-bold px-3.5 min-h-[44px] whitespace-nowrap">XỬ LÝ NGAY <ArrowRight size={15} /></Link></td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
        {list.length === 0 && <p className="p-8 text-center text-slate-500">Không có việc nào khớp. <button onClick={() => { setFilter("ALL"); setQ(""); }} className="font-bold text-[#1e5aa8]">Xóa lọc</button></p>}
      </div>

      <div className="md:hidden space-y-3">
        {list.map((t) => (
          <div key={t.id} className="rounded-2xl bg-white border border-slate-200 p-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cx("inline-flex items-center text-[12px] font-extrabold rounded-full px-2.5 py-1", LEVEL[t.level].cls)}>{LEVEL[t.level].label}</span>
              <ToneBadge tone={t.statusTone} size="sm">{t.status}</ToneBadge>
              <span className="ml-auto text-[12.5px] font-bold text-red-700">⏰ {t.due}</span>
            </div>
            <p className="font-extrabold text-[16px] text-[#0f2a4a] mt-2">{t.lot} · {t.customer}</p>
            <div className="mt-1.5 rounded-xl bg-slate-50 border border-slate-200 p-3">
              <p className="text-[12px] font-bold uppercase tracking-wide text-slate-400">Việc cần làm</p>
              <p className="text-[15px] font-semibold text-slate-800 mt-0.5">{t.job}</p>
              <p className="text-[13px] text-slate-500 mt-1">👤 {t.assignee} · {t.dueNote}</p>
            </div>
            <Link to={t.route} className="btn-press touch-target mt-3 flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-extrabold text-[15.5px] min-h-[52px]">XỬ LÝ NGAY <ArrowRight size={18} /></Link>
          </div>
        ))}
        {list.length === 0 && <div className="rounded-2xl bg-white border p-8 text-center text-slate-500">Không có việc nào. <button onClick={() => { setFilter("ALL"); setQ(""); }} className="font-bold text-[#1e5aa8]">Xóa lọc</button></div>}
      </div>

      <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-4 flex items-start gap-3 text-[14px] text-slate-500">
        <ListFilter size={19} className="shrink-0 mt-0.5" />
        <p>Mẹo cho người mới: xử lý theo thứ tự <b>Khẩn → Cần xử lý → Bình thường</b>. Mỗi dòng đều có nút XỬ LÝ NGAY dẫn tới đúng ô nhập liệu.</p>
      </div>
      <TaskCreateSheet open={createOpen} onClose={() => setCreateOpen(false)} onSuccess={onTaskCreated} />
    </div>
  );
}
