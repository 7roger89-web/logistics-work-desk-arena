import { useState } from 'react';
import { ArrowRight, CheckCircle2, Circle, Info } from 'lucide-react';
import type { JourneyNode, Shipment, WorkModuleGuidance } from '../lib/viewmodel';
import { cx } from '../lib/format';
import { JOURNEY_META, JourneyStatus } from './JourneyMap';

const GUIDANCE_ROWS: { key: keyof WorkModuleGuidance; label: string }[] = [
  { key: 'why', label: 'WHY — vì sao' },
  { key: 'what_to_do', label: 'WHAT TO DO — cần làm gì' },
  { key: 'who', label: 'WHO — ai làm' },
  { key: 'when', label: 'WHEN — khi nào' },
  { key: 'needs', label: 'NEEDS — cần gì' },
  { key: 'done_when', label: 'DONE WHEN — xong khi nào' },
  { key: 'impact', label: 'IMPACT if incomplete — nếu chưa xong' },
];
const ACTION_STYLE = {
  PROBLEM: { box: 'border-red-700 bg-red-600 text-white', label: 'CẦN LÀM NGAY' },
  CURRENT: { box: 'border-blue-700 bg-blue-600 text-white', label: 'CẦN LÀM' },
  WAITING: { box: 'border-amber-500 bg-amber-100 text-amber-950', label: 'ĐANG CHỜ' },
  COMPLETED: { box: 'border-emerald-300 bg-emerald-50 text-emerald-900', label: 'BẰNG CHỨNG HOÀN THÀNH' },
  UPCOMING: { box: 'border-slate-300 bg-slate-100 text-slate-700', label: 'CHƯA XÁC ĐỊNH / SẮP TỚI' },
};
function Label({ children }: { children: React.ReactNode }) { return <div className="mb-1 text-[10.5px] font-bold uppercase tracking-widest text-slate-500">{children}</div>; }
export function stageAction(node: JourneyNode) {
  return node.blockers.join(' · ') || (node.completed ? 'Mốc hoàn thành đã được ghi nhận; kiểm tra thông tin liên quan khi cần.' : node.owned ? 'Kiểm tra bằng chứng và cập nhật tại bàn làm việc công đoạn.' : 'Theo dõi thông tin tham chiếu; chưa xác nhận Trường Thành phụ trách.');
}
export default function JourneyQuickPanel({ shipment: s, selected: n, onOpen, runPrimary, onClose }: {
  shipment: Shipment; selected: JourneyNode; onOpen: (node: JourneyNode, work: string) => void;
  runPrimary: () => void; onClose: () => void;
}) {
  const [copyState, setCopyState] = useState('');
  const a = ACTION_STYLE[n.state], m = JOURNEY_META[n.state], nodes = s.journey!.nodes;
  // Honest customer wording from projected facts only. No mock owner, cutoff,
  // missing-file status, or prototype next-action engine is imported.
  const update = n.evidence ? `${n.label}: ${n.evidence}.${n.deadline ? ` Mốc dự kiến: ${n.deadline}.` : ''}` : 'Chưa có bằng chứng để xác nhận tiến độ với khách.';
  const files = s.attachments?.filter(f => n.documentIds.includes(f.id)) ?? [];
  const copy = async () => { try { await navigator.clipboard.writeText(update); setCopyState('Đã sao chép'); } catch { setCopyState('Không sao chép được; chọn đoạn trên để copy.'); } };
  return <div className="flex h-full min-h-0 flex-col bg-white" data-testid="journey-quick-panel">
    <div className={cx('border-b-4 px-4 pb-3 pt-3', n.state === 'PROBLEM' ? 'border-red-600 bg-red-50' : 'border-slate-300 bg-white')}>
      <div className="flex items-start justify-between"><div className="text-[10.5px] font-bold uppercase tracking-widest text-slate-500">Quick panel · {s.id}</div><button type="button" onClick={onClose} aria-label="Đóng Quick Panel" className="touch-target -mr-1 -mt-1 rounded text-lg text-slate-400">✕</button></div>
      <div className="flex flex-wrap items-center gap-3"><h3 className="text-2xl font-black tracking-tight text-slate-900">{n.label}</h3><JourneyStatus node={n} solid /></div>
      <div className={cx('mt-0.5 text-sm font-bold', m.text)}>{n.evidence || 'Chưa có bằng chứng thực tế'}</div>
    </div>
    <div className="min-h-0 flex-1 space-y-3.5 overflow-auto px-4 py-3">
      <section><Label>Support Sale cần làm</Label><div className={cx('rounded-lg border-2 p-3', a.box)}><div className="text-[11px] font-extrabold tracking-[0.12em] opacity-90">{a.label}</div><div className="mt-0.5 text-[19px] font-extrabold leading-snug">{stageAction(n)}</div></div></section>
      {n.moduleId && <section className="rounded-lg border border-slate-300 bg-slate-50 p-3" data-testid="journey-module-context"><Label>Quy trình · V{n.moduleTemplateVersion}</Label><div className="font-bold">{n.moduleName}</div><p className="text-xs text-slate-600">{n.moduleStatus === 'DONE' ? 'Đã xong' : n.moduleStatus === 'BLOCKING' ? 'Đang chặn' : n.moduleStatus === 'UNKNOWN' ? 'Chưa xác định' : 'Đang chờ'} · {n.moduleProvenance === 'COMPANY_STANDARD' ? 'Chuẩn công ty' : 'Thêm thủ công'}</p>{n.moduleGateText && <p className="mt-1 text-sm font-semibold text-red-900">{n.moduleGateText}</p>}{n.moduleSteps && <ol className="mt-2 space-y-0.5 text-sm">{n.moduleSteps.map(step => <li key={step.id} className="flex items-center gap-1">{step.completed ? <CheckCircle2 size={13} className="text-emerald-700" /> : <Circle size={13} className="text-slate-400" />}<span className={step.completed ? 'text-slate-600 line-through' : 'font-semibold'}>{step.label}</span></li>)}</ol>}</section>}
      {n.guidance && <section className="rounded-lg border border-slate-300 p-3" data-testid="journey-module-guidance"><Label><Info size={13} className="inline" /> Hướng dẫn bước</Label><dl className="space-y-1 text-sm">{GUIDANCE_ROWS.filter(row => n.guidance?.[row.key]).map(row => <div key={row.key}><dt className="text-xs text-slate-500">{row.label}</dt><dd className="font-medium">{n.guidance?.[row.key]}</dd></div>)}</dl></section>}
      <div className="grid grid-cols-2 gap-3"><section><Label>Owner lô hàng</Label><div className="text-sm font-bold">{s.journey!.owner || 'Chưa phân công'}</div></section><section><Label>Deadline / mốc dự kiến</Label><div className="text-sm font-bold">{n.deadline || 'Chưa ghi nhận'}</div></section></div>
      <section><Label>Dependency</Label><div className="inline-flex rounded-md border border-slate-300 bg-slate-50 px-2.5 py-1 text-sm font-bold">{n.dependencies.map(id => nodes.find(x => x.id === id)?.label).filter(Boolean).join(' + ') || 'Không có công đoạn trước trong phạm vi này'}</div></section>
      <section><Label>Next Action — toàn lô</Label><p className="text-sm font-bold">{s.journey!.primaryAction.text}</p><button type="button" onClick={runPrimary} className="touch-target text-sm font-bold text-blue-700 underline">{s.nextLabel || 'Xử lý ngay'}</button></section>
      <section><Label>Document status</Label><div className="flex flex-wrap gap-1.5">{files.length ? files.map(f => <button key={f.id} type="button" onClick={() => onOpen(n, 'docs')} className="touch-target max-w-full rounded-md border border-slate-300 bg-slate-50 px-2 py-1 text-[13px] font-bold text-slate-700"><span className="break-all">{f.name}</span> · Đã có tệp</button>) : <span className="text-sm text-slate-500">Chưa ghi nhận tệp liên quan</span>}</div><button type="button" onClick={() => onOpen(n, 'docs')} className="touch-target text-xs font-bold text-blue-700">Quản lý chứng từ →</button></section>
      <section><Label>Impact</Label><div className={cx('rounded-md border-l-4 px-3 py-2 text-[13px] leading-snug', n.blockers.length ? 'border-red-600 bg-red-50 text-red-900' : 'border-slate-300 bg-slate-50 text-slate-700')}>{n.blockers.join(' · ') || 'Chưa có blocker được ghi nhận cho công đoạn này.'}</div></section>
      <section><Label>Customer update</Label><div className="rounded-md border border-slate-300 bg-slate-50 p-2.5"><p className="text-[13px] italic leading-snug">“{update}”</p><button type="button" onClick={copy} className="touch-target mt-2 rounded border bg-white px-2 text-xs font-bold">COPY UPDATE</button>{copyState && <p role="status" className="text-xs text-slate-600">{copyState}</p>}</div></section>
    </div>
    <div className="border-t border-slate-300 bg-white p-3"><button type="button" onClick={() => onOpen(n, 'overview')} data-testid="journey-open-workspace" className="touch-target inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 py-3 text-[15px] font-extrabold tracking-wider text-white shadow">MỞ CÔNG ĐOẠN <ArrowRight size={16} /></button><div className="mt-1 text-center text-[11px] text-slate-500">Thông tin · Chứng từ · Chi phí · Lịch sử của {n.label}</div></div>
  </div>;
}
