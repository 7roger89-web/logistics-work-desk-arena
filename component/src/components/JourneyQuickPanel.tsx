import { useState } from 'react';
import { ArrowRight, CheckCircle2, ChevronDown, Circle, Info } from 'lucide-react';
import type { JourneyNode, Shipment, WorkModuleGuidance } from '../lib/viewmodel';
import { cx, fmtCcy } from '../lib/format';
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
function Label({ children }: { children: React.ReactNode }) { return <div className="mb-1 text-[12px] font-bold uppercase tracking-widest text-slate-500">{children}</div>; }
export function stageAction(node: JourneyNode) {
  return node.blockers.join(' · ') || (node.completed ? 'Mốc hoàn thành đã được ghi nhận; kiểm tra thông tin liên quan khi cần.' : node.owned ? 'Kiểm tra bằng chứng và cập nhật tại bàn làm việc công đoạn.' : 'Theo dõi thông tin tham chiếu; chưa xác nhận Trường Thành phụ trách.');
}
export default function JourneyQuickPanel({ shipment: s, selected: n, onOpen, runPrimary, onClose }: {
  shipment: Shipment; selected: JourneyNode; onOpen: (node: JourneyNode, work: string) => void;
  runPrimary: () => void; onClose: () => void;
}) {
  const [copyState, setCopyState] = useState('');
  const [moreOpen, setMoreOpen] = useState(false);
  const a = ACTION_STYLE[n.state], m = JOURNEY_META[n.state], nodes = s.journey!.nodes;
  // Honest customer wording from projected facts only. No mock owner, cutoff,
  // missing-file status, or prototype next-action engine is imported.
  const update = n.evidence ? `${n.label}: ${n.evidence}.${n.deadline ? ` Mốc dự kiến: ${n.deadline}.` : ''}` : 'Chưa có bằng chứng để xác nhận tiến độ với khách.';
  const files = s.attachments?.filter(f => n.documentIds.includes(f.id)) ?? [];
  const copy = async () => { try { await navigator.clipboard.writeText(update); setCopyState('Đã sao chép'); } catch { setCopyState('Không sao chép được; chọn đoạn trên để copy.'); } };
  const cny = s.finance?.partner?.partners?.find(g => g.totalsByCurrency?.CNY)?.totalsByCurrency?.CNY
    || (s.finance?.partner?.currency === 'CNY' ? { payable: s.finance.partner.payable, paid: s.finance.partner.paid, remaining: s.finance.partner.remaining } : null);
  const deps = n.dependencies.map(id => nodes.find(x => x.id === id)?.label).filter(Boolean).join(' + ');
  return <div className="flex h-full min-h-0 flex-col bg-white" data-testid="journey-quick-panel">
    <div className={cx('border-b-4 bg-white px-4 pb-3 pt-3', n.state === 'PROBLEM' ? 'border-red-600' : 'border-slate-300')}>
      <div className="flex items-start justify-between"><div className="text-[12px] font-bold uppercase tracking-widest text-slate-500">Quick panel · {s.id}</div><button type="button" onClick={onClose} aria-label="Đóng Quick Panel" className="touch-target -mr-1 -mt-1 rounded text-lg text-slate-400">✕</button></div>
      <div className="flex flex-wrap items-center gap-3"><h3 className="text-2xl font-black tracking-tight text-slate-900">{n.label}</h3><JourneyStatus node={n} solid /></div>
      <div className={cx('mt-0.5 text-sm font-bold', m.text)}>{n.evidence || 'Chưa có bằng chứng thực tế'}</div>
    </div>
    <div className="min-h-0 flex-1 space-y-3 overflow-auto px-4 py-3">
      <section><Label>Support Sale cần làm</Label><div className={cx('rounded-lg border-2 p-3', a.box)}><div className="text-[12px] font-extrabold tracking-[0.12em] opacity-90">{a.label}</div><div className="mt-0.5 text-[19px] font-extrabold leading-snug">{stageAction(n)}</div><button type="button" onClick={() => onOpen(n, 'info')} data-testid="journey-quick-action" className="touch-target mt-2.5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#0f2a4a] px-3 py-2.5 text-[13px] font-extrabold tracking-wide text-white">XỬ LÝ NGAY <ArrowRight size={15} /></button></div></section>
      <section><Label>Thông tin chính</Label></section>
      <dl className="divide-y divide-slate-100 rounded-lg border border-slate-200 text-[13px]" data-testid="journey-quick-facts">
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">NGƯỜI NHẬP KHẨU</dt><dd className="text-right font-bold">{s.importInfo.receiver || s.customer || 'Chưa có thông tin'}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">TỜ KHAI</dt><dd className="text-right font-bold">{s.importInfo.declarationNo ? `${s.importInfo.declarationNo} · đã đăng ký` : 'Chưa có thông tin'}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">THÔNG QUAN</dt><dd className={cx('text-right font-bold', !s.importInfo.customsStatus && 'text-red-700')}>{s.importInfo.customsStatus ? 'Đã xác nhận' : 'Chưa xác nhận'}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">THUẾ NK</dt><dd className={cx('text-right font-bold', s.importInfo.tax == null && 'text-red-700')}>{s.importInfo.tax == null ? 'Chưa có thông tin' : fmtCcy(s.importInfo.tax, 'VND')}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">VAT</dt><dd className={cx('text-right font-bold', s.importInfo.vat == null && 'text-red-700')}>{s.importInfo.vat == null ? 'Chưa có thông tin' : fmtCcy(s.importInfo.vat, 'VND')}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">GNT</dt><dd className={cx('text-right font-bold', !s.importInfo.gnt && 'text-red-700')}>{s.importInfo.gnt ? (s.importInfo.gnt.ready ? 'Sẵn sàng nộp thuế' : 'Đã ghi nhận') : 'Chưa có'}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">CHINA AGENT</dt><dd className={cx('text-right font-bold', !cny && 'text-red-700')}>{cny ? `${fmtCcy(cny.payable, 'CNY')} · ${(cny.paid ?? 0) > 0 ? 'đã thanh toán' : 'chưa thanh toán'}` : 'Chưa có thông tin'}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">NGƯỜI THEO</dt><dd className="text-right font-bold">{s.journey!.owner || 'Chưa phân công'}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">HẠN</dt><dd className="text-right font-bold">{n.deadline || 'Chưa ghi nhận'}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">CHỜ AI / PHỤ THUỘC</dt><dd className="text-right font-bold">{deps || '—'}</dd></div>
        <div className="flex items-center justify-between gap-2 px-3 py-2"><dt className="shrink-0 text-slate-500">Chứng từ</dt><dd className="text-right font-bold">{files.length ? `${files.length} tệp đã ghi nhận` : 'Chưa ghi nhận'}</dd></div>
        {n.blockers.length > 0 && <div className="bg-red-50 px-3 py-2"><dt className="text-xs font-bold text-red-700">BLOCKER / ẢNH HƯỞNG</dt><dd className="mt-0.5 text-[13px] font-bold leading-snug text-red-900">{n.blockers.join(' · ')}</dd></div>}
      </dl>
      {n.moduleId && <section className="rounded-lg border border-slate-300 bg-slate-50 p-3" data-testid="journey-module-context"><Label>Quy trình · V{n.moduleTemplateVersion}</Label><div className="font-bold">{n.moduleName}</div><p className="text-xs text-slate-600">{n.moduleStatus === 'DONE' ? 'Đã xong' : n.moduleStatus === 'BLOCKING' ? 'Đang chặn' : n.moduleStatus === 'UNKNOWN' ? 'Chưa xác định' : 'Đang chờ'} · {n.moduleProvenance === 'COMPANY_STANDARD' ? 'Chuẩn công ty' : 'Thêm thủ công'}</p>{n.moduleGateText && <p className="mt-1 text-sm font-semibold text-red-900">{n.moduleGateText}</p>}</section>}
      <button type="button" onClick={() => setMoreOpen(v => !v)} aria-expanded={moreOpen} data-testid="journey-quick-more"
        className="touch-target flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] font-bold text-slate-600">
        Chi tiết thêm <ChevronDown size={15} className={cx('transition-transform', moreOpen && 'rotate-180')} aria-hidden="true" />
      </button>
      {moreOpen && <div className="space-y-3">
        {n.guidance && <section className="rounded-lg border border-slate-300 p-3" data-testid="journey-module-guidance"><Label><Info size={13} className="inline" /> Hướng dẫn bước</Label><dl className="space-y-1 text-sm">{GUIDANCE_ROWS.filter(row => n.guidance?.[row.key]).map(row => <div key={row.key}><dt className="text-xs text-slate-500">{row.label}</dt><dd className="font-medium">{n.guidance?.[row.key]}</dd></div>)}</dl></section>}
        <section><Label>CẦN CÓ</Label><div className="rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-sm">{n.guidance?.needs || (files.length ? `Đã liên kết ${files.length} tệp; kiểm tra đúng bằng chứng trước khi cập nhật.` : n.evidence ? `Bằng chứng hiện có: ${n.evidence}` : 'Chưa có tiêu chí/tệp cụ thể được lưu; không tự đoán.')}</div></section>
        <section><Label>DONE WHEN / XONG KHI</Label><div className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm">{n.guidance?.done_when || (n.completed && n.evidence ? `Đã có bằng chứng: ${n.evidence}` : 'Khi authority của công đoạn ghi nhận bằng chứng thực tế; không suy completion từ lịch dự kiến hay file upload.')}</div></section>
        <section><Label>Next Action — toàn lô (tham chiếu)</Label><p className="text-sm font-bold">{s.journey!.primaryAction.text}</p><button type="button" onClick={runPrimary} className="touch-target text-xs font-bold text-blue-700 underline">{s.nextLabel || 'Mở việc toàn lô'}</button></section>
        <section><Label>CHỨNG TỪ</Label><div className="flex flex-wrap gap-1.5">{files.length ? files.map(f => <button key={f.id} type="button" onClick={() => onOpen(n, 'docs')} className="touch-target max-w-full rounded-md border border-slate-300 bg-slate-50 px-2 py-1 text-[13px] font-bold text-slate-700"><span className="break-all">{f.name}</span> · Đã có tệp</button>) : <span className="text-sm text-slate-500">Chưa ghi nhận tệp liên quan</span>}</div><button type="button" onClick={() => onOpen(n, 'docs')} className="touch-target text-xs font-bold text-blue-700">Quản lý chứng từ →</button></section>
        <section><Label>Customer update</Label><div className="rounded-md border border-slate-300 bg-slate-50 p-2.5"><p className="text-[13px] italic leading-snug">“{update}”</p><button type="button" onClick={copy} className="touch-target mt-2 rounded border bg-white px-2 text-xs font-bold">COPY UPDATE</button>{copyState && <p role="status" className="text-xs text-slate-600">{copyState}</p>}</div></section>
      </div>}
    </div>
    <div className="border-t border-slate-300 bg-white p-3"><button type="button" onClick={() => onOpen(n, 'overview')} data-testid="journey-open-workspace" className="touch-target inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 py-3 text-[15px] font-extrabold tracking-wider text-white shadow">MỞ CÔNG ĐOẠN <ArrowRight size={16} /></button><div className="mt-1 text-center text-[12px] text-slate-500">Thông tin · Chứng từ · Chi phí · Lịch sử của {n.label}</div></div>
  </div>;
}
