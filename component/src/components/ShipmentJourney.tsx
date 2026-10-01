import { useEffect, useState, useSyncExternalStore } from 'react';
import { ArrowRight, CheckCircle2, Circle, Clock, CircleAlert, MapPin } from 'lucide-react';
import type { JourneyNode, Shipment } from '../lib/viewmodel';
import { getViewModel, subscribeViewModel } from '../lib/viewmodel';
import { useStore } from '../lib/store';
import { cx } from '../lib/format';
import { Field, inputCls } from './ui';

export const JOURNEY_WORK = [
  { id: 'overview', label: 'Tổng quan' }, { id: 'info', label: 'Thông tin' },
  { id: 'docs', label: 'Chứng từ' }, { id: 'costs', label: 'Chi phí' }, { id: 'history', label: 'Lịch sử' },
];
const META = {
  COMPLETED: { label: 'Hoàn thành', icon: CheckCircle2, cls: 'border-emerald-300 bg-emerald-50 text-emerald-900' },
  CURRENT: { label: 'Hiện tại', icon: MapPin, cls: 'border-blue-500 bg-blue-50 text-blue-950' },
  UPCOMING: { label: 'Chưa xác định / sắp tới', icon: Circle, cls: 'border-dashed border-slate-300 bg-slate-50 text-slate-700' },
  WAITING: { label: 'Đang chờ', icon: Clock, cls: 'border-dashed border-amber-400 bg-amber-50 text-amber-950' },
  PROBLEM: { label: 'Cần xử lý', icon: CircleAlert, cls: 'border-red-400 bg-red-50 text-red-900' },
};
const SEA_POS: Record<string, [number, number]> = {
  booking: [0, 0], pickup: [1, 0], 'customs-export': [2, 0], 'si-vgm': [3, 0],
  'gate-in': [3, 1], etd: [2, 1], 'on-board': [1, 1], transit: [0, 1],
  arrival: [0, 2], 'customs-import': [1, 2], delivery: [2, 2],
};
function Status({ node }: { node: JourneyNode }) {
  const m = META[node.state]; const Icon = m.icon;
  return <span className="inline-flex items-center gap-1 text-xs font-bold"><Icon size={14} aria-hidden="true" />{m.label}</span>;
}

export default function ShipmentJourney({ shipment: s, activeStage, work, onOpen, onGlobal, runPrimary }: {
  shipment: Shipment; activeStage: string; work: string;
  onOpen: (node: JourneyNode, work: string) => void; onGlobal: () => void; runPrimary: () => void;
}) {
  const [picked, setPicked] = useState('');
  useEffect(() => { setPicked(activeStage || ''); }, [activeStage]);
  const journey = s.journey;
  if (!journey?.nodes.length) return <section className="rounded-2xl border bg-white p-4"><h2 className="font-bold">Hành trình lô hàng</h2><p className="mt-1 text-sm text-slate-500">Chưa có công đoạn phù hợp. Bổ sung phạm vi dịch vụ trong thông tin vận chuyển.</p></section>;
  const nodes = journey.nodes;
  const selected = nodes.find(n => n.id === picked) ?? nodes.find(n => n.id === activeStage) ?? nodes.find(n => n.current) ?? nodes[0];
  const stage = nodes.find(n => n.id === activeStage);
  const sea = nodes.some(n => n.id === 'booking');
  const pos = new Map(nodes.map((n, i) => [n.id, sea ? SEA_POS[n.id] ?? [i % 4, Math.floor(i / 4)] : [i % 4, Math.floor(i / 4)]]));
  const maxRow = Math.max(...[...pos.values()].map(p => p[1]));
  const primary = journey.primaryAction;
  return <section className="rounded-2xl border border-slate-200 bg-white overflow-hidden" data-testid="shipment-journey">
    <div className="flex flex-wrap items-center gap-3 border-b p-4">
      <div className="min-w-0 flex-1"><h2 className="font-extrabold text-lg text-[#0f2a4a]">Hành trình lô hàng</h2>
        <p className="text-sm text-slate-500">{journey.currentStageId ? `Vị trí theo mốc thực tế: ${nodes.find(n => n.current)?.label}` : journey.positionNote}</p></div>
      <button type="button" onClick={onGlobal} className="touch-target rounded-lg border px-3 py-2 text-sm font-bold">Toàn bộ lô hàng</button>
    </div>
    <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_300px]">
      <div className="min-w-0 p-3">
        <div className="overflow-x-auto rounded-xl bg-slate-50 p-2" aria-label="Bản đồ công đoạn, có thể cuộn ngang">
          <div className="relative min-w-[740px]" style={{ height: (maxRow + 1) * 145 }}>
            <svg className="absolute inset-0 h-full w-full pointer-events-none" viewBox={`0 0 740 ${(maxRow + 1) * 145}`} preserveAspectRatio="none" aria-hidden="true">
              <defs><marker id="journey-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" /></marker></defs>
              {journey.edges.map(e => { const a = pos.get(e.from), b = pos.get(e.to); if (!a || !b) return null;
                const ax = a[0] * 185 + 84, ay = a[1] * 145 + 58, bx = b[0] * 185 + 84, by = b[1] * 145 + 58;
                const horizontal = a[1] === b[1]; const startX = horizontal ? ax + (bx > ax ? 82 : -82) : ax;
                const endX = horizontal ? bx + (bx > ax ? -82 : 82) : bx;
                const startY = horizontal ? ay : ay + 57, endY = horizontal ? by : by - 57;
                return <path key={`${e.from}-${e.to}`} d={`M ${startX} ${startY} L ${endX} ${endY}`} fill="none" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#journey-arrow)" />; })}
            </svg>
            {nodes.map(n => { const [x, y] = pos.get(n.id)!;
              return <button key={n.id} type="button" data-testid={`journey-node-${n.id}`} data-state={n.state}
                aria-pressed={selected.id === n.id} onClick={() => setPicked(n.id)}
                className={cx('absolute flex flex-col text-left rounded-xl border-2 p-2.5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700', META[n.state].cls, selected.id === n.id && 'ring-2 ring-[#0f2a4a] ring-offset-2')}
                style={{ left: `${x * 25}%`, top: y * 145, width: '22.5%', height: 116 }}>
                <Status node={n} /><span className="mt-1 font-extrabold text-sm">{n.label}</span>
                <span className="text-xs line-clamp-2 mt-1">{n.evidence || 'Chưa có bằng chứng thực tế'}</span>
                <span className="mt-auto text-[11px] font-medium">{n.current ? '● Vị trí hiện tại · ' : ''}{n.documentIds.length} tệp · {n.owned ? 'TT phụ trách' : 'Tham chiếu phạm vi'}</span>
              </button>; })}
          </div>
        </div>
        {sea && nodes.some(n => n.id === 'si-vgm') && nodes.some(n => n.id === 'gate-in') && <p className="mt-2 text-xs text-slate-500">SI/VGM và Gate-in là hai nhánh song song. Lịch ETD không xác nhận hai nhánh đã hoàn tất; ATD ghi nhận được vẫn hiển thị độc lập.</p>}
      </div>
      <aside className="border-t xl:border-t-0 xl:border-l p-4 space-y-3" data-testid="journey-quick-panel">
        <div><span className="text-xs font-bold text-slate-500">XEM NHANH</span><h3 className="text-xl font-extrabold text-[#0f2a4a]">{selected.label}</h3><Status node={selected} /></div>
        <div className="rounded-lg bg-slate-50 border p-3"><p className="text-xs font-bold text-slate-500">Support Sale cần làm gì</p>
          <p className="font-semibold mt-1 text-sm">{selected.blockers.join(' · ') || (selected.owned ? 'Kiểm tra bằng chứng và cập nhật tại bàn làm việc công đoạn.' : 'Theo dõi thông tin tham chiếu; chưa xác nhận Trường Thành phụ trách.')} </p></div>
        <dl className="grid grid-cols-2 gap-3 text-sm"><div><dt className="text-xs text-slate-500">Owner lô hàng</dt><dd className="font-semibold">{journey.owner || 'Chưa phân công'}</dd></div><div><dt className="text-xs text-slate-500">Mốc dự kiến / cutoff</dt><dd className="font-semibold">{selected.deadline || 'Chưa ghi nhận'}</dd></div></dl>
        <div className="text-sm"><p className="text-xs font-bold text-slate-500">Phụ thuộc</p><p>{selected.dependencies.map(id => nodes.find(n => n.id === id)?.label).join(' + ') || 'Không có công đoạn trước trong phạm vi này'}</p></div>
        <div className="text-sm"><p className="text-xs font-bold text-slate-500">Next Action — toàn lô</p><p className="font-semibold">{primary.text}</p><button type="button" onClick={runPrimary} className="touch-target mt-1 text-blue-800 font-bold underline">{s.nextLabel || 'Xử lý ngay'}</button></div>
        <div className="text-sm"><p className="text-xs font-bold text-slate-500">Chứng từ / ảnh hưởng</p><p>{selected.documentIds.length} tệp liên quan. {selected.blockers.length ? selected.blockers.join(' · ') : 'Chưa có blocker được ghi nhận cho công đoạn này.'}</p></div>
        <div className="text-sm"><p className="text-xs font-bold text-slate-500">Thông tin có thể báo khách</p><p>{selected.evidence ? `${selected.label}: ${selected.evidence}.` : 'Chưa có bằng chứng để xác nhận tiến độ với khách.'}{selected.deadline ? ` Mốc dự kiến: ${selected.deadline}.` : ''}</p></div>
        <button type="button" onClick={() => onOpen(selected, 'overview')} data-testid="journey-open-workspace" className="touch-target w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold px-3 py-3">Mở bàn làm việc <ArrowRight size={16} /></button>
      </aside>
    </div>
    {stage && <div className="border-t p-4" data-testid="journey-stage-workspace"><div className="flex flex-wrap gap-2 items-center"><h3 className="font-extrabold text-lg">{stage.label} · bàn làm việc</h3><span className="text-sm text-slate-500">{s.id}</span></div>
      <div className="flex gap-2 mt-3 overflow-x-auto" aria-label="Nội dung công đoạn">{JOURNEY_WORK.map(w => <button type="button" key={w.id} aria-pressed={work === w.id} onClick={() => onOpen(stage, w.id)} className={cx('touch-target whitespace-nowrap rounded-lg border px-3 py-2 text-sm font-bold', work === w.id && 'bg-[#0f2a4a] text-white')}>{w.label}</button>)}</div>
      {work === 'overview' && <div className="mt-4 text-sm space-y-2"><p>{stage.evidence || 'Chưa có bằng chứng hoàn thành. UNKNOWN được giữ nguyên.'}</p><p>{stage.blockers.join(' · ') || 'Không có blocker riêng được ghi nhận.'}</p><p>{stage.owned ? 'Công đoạn thuộc phạm vi đã xác nhận của Trường Thành.' : 'Thông tin tham chiếu, chưa phải công việc đã giao cho Trường Thành.'}</p></div>}
    </div>}
  </section>;
}

export function SeaExportFacts({ shipment: s, stageId }: { shipment: Shipment; stageId: string }) {
  const { dispatch } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(''); const [error, setError] = useState('');
  const [expectedVersion] = useState(s.version ?? 0);
  const access = vm?.userAccess?.currentUser;
  const canEdit = Boolean(access?.wildcard || access?.permissions.includes('shipment_edit'));
  const node = s.journey?.nodes.find(n => n.id === stageId);
  const outcome = vm?.lastWrites?.find(w => w.event === 'shipment_sea_facts_save' && w.requestId === pending);
  const loading = Boolean(pending && !outcome);
  const saved = Boolean(outcome?.ok);
  const fields = stageId === 'customs-export' ? [{ key: 'export_declaration_no', label: 'Số tờ khai xuất (đã đăng ký)' }] : stageId === 'gate-in' ? [{ key: 'gate_in_at', label: 'Gate-in thực tế' }] : [
    { key: 'si_status', label: 'Trạng thái SI' }, { key: 'vgm_status', label: 'Trạng thái VGM' },
    { key: 'si_cutoff', label: 'SI cutoff' }, { key: 'vgm_cutoff', label: 'VGM cutoff' },
  ];
  const save = () => {
    if (!Object.keys(draft).length) { setError('Chưa thay đổi trường nào.'); return; }
    const requestId = `SEA-${crypto.randomUUID()}`;
    setError(''); setPending(requestId);
    if (!dispatch('shipment_sea_facts_save', { shipmentId: s.id, fields: draft, requestId, expectedVersion })) {
      setPending(''); setError('Chưa kết nối backend.');
    }
  };
  return <section className="rounded-2xl border bg-white p-4 space-y-3" data-testid="sea-export-facts">
    <h3 className="font-extrabold text-[#0f2a4a]">{stageId === 'customs-export' ? 'Tờ khai xuất — dữ liệu hiện có' : stageId === 'gate-in' ? 'Mốc vào bãi container' : 'SI / VGM — ghi nhận bằng chứng'}</h3>
    <p className="text-sm text-slate-500">Tệp đã tải lên không tự xác nhận hãng tàu đã nhận hoặc chấp nhận. Chỉ ghi trạng thái có bằng chứng.</p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{fields.map(f => <Field key={f.key} label={f.label}>
      {f.key.endsWith('_status') ? <select aria-label={f.label} disabled={!canEdit || loading || !node?.owned} className={inputCls()} value={draft[f.key] ?? s.journey?.seaFacts[f.key] ?? 'UNKNOWN'} onChange={e => setDraft(d => ({ ...d, [f.key]: e.target.value }))}>
        {['UNKNOWN', 'RECEIVED', 'SUBMITTED', 'ACCEPTED'].map((k, i) => <option key={k} value={k}>{['Chưa biết', 'Đã nhận hồ sơ', 'Đã gửi hãng tàu', 'Hãng tàu đã chấp nhận'][i]}</option>)}</select> :
        <input aria-label={f.label} type="text" placeholder={f.key === 'export_declaration_no' ? 'Số tờ khai' : 'YYYY-MM-DD hoặc YYYY-MM-DDTHH:mm'} disabled={!canEdit || loading || !node?.owned} className={inputCls()} value={draft[f.key] ?? s.journey?.seaFacts[f.key] ?? ''} onChange={e => setDraft(d => ({ ...d, [f.key]: e.target.value }))} />}
    </Field>)}</div>
    <button type="button" disabled={!canEdit || loading || !node?.owned || saved} onClick={save} className="touch-target rounded-lg bg-[#0f2a4a] px-4 py-2 font-bold text-white disabled:opacity-50">{loading ? 'Đang chờ đọc lại…' : saved ? 'Đã xác nhận từ backend' : 'Lưu mốc có bằng chứng'}</button>
    {!canEdit && <p className="text-sm text-slate-500">Tài khoản hiện tại chỉ đọc thông tin này.</p>}
    {(error || outcome?.error) && <p role="alert" className="text-sm text-red-700">{error || outcome?.error}</p>}
  </section>;
}
