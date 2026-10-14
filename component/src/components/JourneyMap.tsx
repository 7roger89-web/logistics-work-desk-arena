import { useCallback, useEffect, useRef, useState } from 'react';
import { CheckCircle2, Circle, Clock, CircleAlert, MapPin } from 'lucide-react';
import type { JourneyNode, Shipment } from '../lib/viewmodel';
import { cx } from '../lib/format';

// Approved prototype B, original ZIP cfe20232…: the canvas geometry, branch,
// edge routing and fit/pan/zoom interaction are retained. Only IDs/data access
// adapt to the app's canonical projection (sivgm → si-vgm, onboard → on-board).
const W = 164, H = 136, PITCH = 212, PX = 48;
const col = (c: number) => PX + c * PITCH;
export interface JourneyPosition { x: number; y: number; w: number; h: number }
export const DEMO_POS: Record<string, JourneyPosition> = {
  start: { x: col(0), y: 30, w: W, h: 44 },
  booking: { x: col(0), y: 140, w: W, h: H },
  pickup: { x: col(1), y: 140, w: W, h: H },
  'customs-export': { x: col(2), y: 140, w: W, h: H },
  'si-vgm': { x: col(3), y: 56, w: W, h: H },
  'gate-in': { x: col(3), y: 224, w: W, h: H },
  etd: { x: col(4), y: 140, w: W, h: H },
  'on-board': { x: col(4), y: 400, w: W, h: H },
  transit: { x: col(3), y: 400, w: W, h: H },
  arrival: { x: col(2), y: 400, w: W, h: H },
  'customs-import': { x: col(1), y: 400, w: W, h: H },
  delivery: { x: col(0), y: 400, w: W, h: H },
  completed: { x: col(0), y: 590, w: W, h: 44 },
};
const CW = col(4) + W + PX, CH = 690;
export const JOURNEY_META = {
  COMPLETED: { label: 'Hoàn thành', icon: CheckCircle2, cls: 'border-emerald-500 bg-emerald-50 border-2', text: 'text-emerald-700' },
  CURRENT: { label: 'Hiện tại', icon: MapPin, cls: 'border-blue-600 bg-white border-[3px] ring-4 ring-blue-100 shadow-lg shadow-blue-200/60', text: 'text-blue-700' },
  WAITING: { label: 'Đang chờ', icon: Clock, cls: 'border-amber-500 bg-amber-50 border-2 border-dashed', text: 'text-amber-800' },
  PROBLEM: { label: 'Cần xử lý', icon: CircleAlert, cls: 'border-red-600 bg-red-50 border-[3px] journey-problem-pulse', text: 'text-red-700' },
  UPCOMING: { label: 'Chưa xác định / sắp tới', icon: Circle, cls: 'border-slate-300 bg-slate-50/80 border-2 border-dashed', text: 'text-slate-500' },
};
export function JourneyStatus({ node, solid = false }: { node: JourneyNode; solid?: boolean }) {
  const m = JOURNEY_META[node.state], Icon = m.icon;
  return <span className={cx('inline-flex items-center gap-1.5 text-xs font-bold', m.text, solid && 'rounded-md border bg-white px-2 py-1')}><Icon size={15} aria-hidden="true" />{m.label}</span>;
}
export function journeyEdgePath(a: JourneyPosition, b: JourneyPosition) {
  if (a.x === b.x && b.y > a.y) return `M${a.x + a.w / 2},${a.y + a.h} L${b.x + b.w / 2},${b.y}`;
  if (b.x < a.x && a.y === b.y) return `M${a.x},${a.y + a.h / 2} L${b.x + b.w},${b.y + b.h / 2}`;
  if (b.x > a.x) {
    const x1 = a.x + a.w, y1 = a.y + a.h / 2, x2 = b.x, y2 = b.y + b.h / 2, dx = (x2 - x1) / 2;
    return `M${x1},${y1} C${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`;
  }
  // Scoped journeys can omit intermediate nodes; route around, never through,
  // remaining cards. This is geometry only: edges still come from the backend.
  const x = Math.min(a.x, b.x) - 24;
  return `M${a.x},${a.y + a.h / 2} H${x} V${b.y + b.h / 2} H${b.x}`;
}
const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));

export default function JourneyMap({ shipment: s, nodes, selectedId, onPick, collapsed, onExpand }: {
  shipment: Shipment; nodes: JourneyNode[]; selectedId: string; onPick: (id: string) => void;
  collapsed: boolean; onExpand: () => void;
}) {
  const [tf, setTf] = useState({ x: 0, y: 0, k: 1 });
  const tfRef = useRef(tf); tfRef.current = tf;
  const vp = useRef<HTMLDivElement>(null), autoFit = useRef(true), moved = useRef(false);
  const cleanupDrag = useRef<(() => void) | undefined>(undefined);
  const [dragging, setDragging] = useState(false);
  const sea = nodes.some(n => n.id === 'booking');
  const positions = new Map(nodes.map((n, i) => [n.id, sea && DEMO_POS[n.id] ? DEMO_POS[n.id] : { x: col(i % 5), y: 140 + Math.floor(i / 5) * 212, w: W, h: H }]));
  const canvasHeight = sea ? CH : Math.max(CH, 140 + Math.ceil(nodes.length / 5) * 212);
  const fit = useCallback(() => {
    const el = vp.current; if (!el?.clientWidth || !el.clientHeight) return;
    const w = el.clientWidth, h = el.clientHeight;
    // Owner 2026-10-13: the 340px left-column map must fit the complete
    // Journey (logical canvas 1108px wide needs ~0.278). Allow zooming out
    // to 0.25 so the small persistent map shows the whole journey at once.
    const k = clamp(Math.min((w - 32) / CW, (h - 32) / canvasHeight), 0.25, 1.15);
    setTf({ k, x: (w - CW * k) / 2, y: Math.max(12, (h - canvasHeight * k) / 2) });
  }, [canvasHeight]);
  useEffect(() => {
    const el = vp.current; if (!el) return;
    if (typeof ResizeObserver === 'undefined') { fit(); return; }
    const ro = new ResizeObserver(() => { if (autoFit.current) fit(); });
    ro.observe(el); fit(); return () => ro.disconnect();
  }, [fit, collapsed]);
  const zoomAt = useCallback((f: number, px: number, py: number) => {
    autoFit.current = false;
    setTf(t => { const k = clamp(t.k * f, 0.3, 2), r = k / t.k; return { k, x: px - (px - t.x) * r, y: py - (py - t.y) * r }; });
  }, []);
  useEffect(() => {
    const el = vp.current; if (!el) return;
    const wheel = (e: WheelEvent) => { e.preventDefault(); const r = el.getBoundingClientRect(); zoomAt(e.deltaY < 0 ? 1.1 : 1 / 1.1, e.clientX - r.left, e.clientY - r.top); };
    el.addEventListener('wheel', wheel, { passive: false });
    return () => el.removeEventListener('wheel', wheel);
  }, [zoomAt, collapsed]);
  useEffect(() => () => cleanupDrag.current?.(), []);
  const pan = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    cleanupDrag.current?.();
    const sx = e.clientX, sy = e.clientY, origin = tfRef.current; moved.current = false;
    const move = (ev: PointerEvent) => {
      const dx = ev.clientX - sx, dy = ev.clientY - sy;
      if (!moved.current && Math.hypot(dx, dy) < 4) return;
      moved.current = true; autoFit.current = false; setDragging(true);
      setTf({ ...origin, x: origin.x + dx, y: origin.y + dy });
    };
    const stop = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', stop); window.removeEventListener('pointercancel', stop); setDragging(false); };
    cleanupDrag.current = stop;
    window.addEventListener('pointermove', move); window.addEventListener('pointerup', stop); window.addEventListener('pointercancel', stop);
  };
  const center = (f: number) => { const el = vp.current; if (el) zoomAt(f, el.clientWidth / 2, el.clientHeight / 2); };
  if (collapsed) return <nav className="journey-rail" aria-label="Danh sách công đoạn" data-testid="journey-map-rail">
    <button type="button" onClick={onExpand} className="touch-target w-full border-b px-3 py-2 text-left text-xs font-bold">⇥ Mở lại Journey Map</button>
    {nodes.map(n => <button key={n.id} type="button" onClick={() => onPick(n.id)} className={cx('touch-target flex w-full items-center gap-2 border-l-4 px-3 py-2 text-left text-xs font-semibold', selectedId === n.id ? 'border-slate-900 bg-slate-100' : 'border-transparent', n.state === 'PROBLEM' && 'bg-red-50 text-red-700')}><JourneyStatus node={n} /><span>{n.label}</span></button>)}
  </nav>;
  const first = nodes[0], last = nodes[nodes.length - 1];
  const edges = (s.journey?.edges ?? []).filter(e => positions.has(e.from) && positions.has(e.to));
  // End-of-map marker only. Journey occurrence + Work Module completion is NOT
  // whole-shipment closure: documents/finance may still be open or UNKNOWN.
  const pick = (id: string, e: React.MouseEvent) => { if (e.detail === 0 || !moved.current) onPick(id); };
  return <div ref={vp} className={cx('journey-canvas relative min-w-0 flex-1 select-none overflow-hidden', dragging ? 'cursor-grabbing' : 'cursor-grab')} onPointerDown={pan} data-testid="journey-map-viewport" aria-label="Journey Map, kéo để di chuyển, cuộn để zoom">
    <div className="absolute left-0 top-0 origin-top-left" style={{ width: CW, height: canvasHeight, transform: `translate(${tf.x}px, ${tf.y}px) scale(${tf.k})` }} data-testid="journey-map-transform">
      {positions.has('si-vgm') && positions.has('gate-in') && <div className="absolute rounded-2xl border-2 border-dashed border-slate-400/70 bg-slate-200/30" style={{ left: DEMO_POS['si-vgm'].x - 14, top: DEMO_POS['si-vgm'].y - 36, width: W + 28, height: DEMO_POS['gate-in'].y + H - DEMO_POS['si-vgm'].y + 50 }} data-testid="journey-parallel-branch"><span className="absolute -top-2.5 left-3 rounded bg-slate-200 px-1.5 text-[10px] font-extrabold tracking-wider text-slate-600">NHÁNH SONG SONG</span></div>}
      {positions.has('si-vgm') && positions.has('gate-in') && <div className="pointer-events-none absolute rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-bold text-slate-600" style={{ left: DEMO_POS.etd.x - 4, top: DEMO_POS.etd.y - 30, width: W + 8 }}>⛓ Phụ thuộc SI/VGM + Gate-in</div>}
      <svg width={CW} height={canvasHeight} className="pointer-events-none absolute left-0 top-0 z-[1]" aria-hidden="true">
        <defs>{[['g', '#059669'], ['s', '#94a3b8'], ['r', '#dc2626']].map(([k, c]) => <marker key={k} id={`journey-arr-${k}`} markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0.5 L10,5 L0,9.5 z" fill={c} /></marker>)}</defs>
        {edges.map(e => { const n = nodes.find(n => n.id === e.from)!; const k = n.state === 'PROBLEM' ? 'r' : n.completed ? 'g' : 's'; return <path key={e.from + e.to} data-from={e.from} data-to={e.to} d={journeyEdgePath(positions.get(e.from)!, positions.get(e.to)!)} fill="none" stroke={k === 'g' ? '#059669' : k === 'r' ? '#dc2626' : '#94a3b8'} strokeWidth={k === 'g' ? 3 : 2.5} strokeDasharray={k === 'g' ? undefined : '7 5'} markerEnd={`url(#journey-arr-${k})`} />; })}
        {sea && first && <path d={journeyEdgePath(DEMO_POS.start, positions.get(first.id)!)} fill="none" stroke="#94a3b8" strokeWidth="2.5" markerEnd="url(#journey-arr-s)" />}
        {sea && last && <path d={journeyEdgePath(positions.get(last.id)!, DEMO_POS.completed)} fill="none" stroke="#94a3b8" strokeWidth="2.5" markerEnd="url(#journey-arr-s)" />}
      </svg>
      {sea && <><span className="absolute z-10 flex items-center justify-center gap-2 rounded-full border-2 border-slate-400 bg-white text-xs font-bold tracking-wide text-slate-600" style={{ left: DEMO_POS.start.x, top: DEMO_POS.start.y, width: W, height: 44 }}>START</span><span className="absolute z-10 flex items-center justify-center gap-2 rounded-full border-2 border-dashed border-slate-400 bg-white text-xs font-bold tracking-wide text-slate-500" style={{ left: DEMO_POS.completed.x, top: DEMO_POS.completed.y, width: W, height: 44 }}>RÀ SOÁT HOÀN TẤT</span></>}
      {nodes.map((n, i) => { const p = positions.get(n.id)!, m = JOURNEY_META[n.state]; return <button key={n.id} type="button" data-testid={`journey-node-${n.id}`} data-state={n.state} aria-pressed={selectedId === n.id} onClick={e => pick(n.id, e)} style={{ left: p.x, top: p.y, width: p.w, height: p.h }} className={cx('absolute z-10 flex flex-col rounded-xl p-2.5 text-left transition-shadow hover:shadow-lg', m.cls, selectedId === n.id && 'outline outline-[3px] outline-offset-4 outline-slate-900')}>
        {n.current && <span className="absolute -top-3 left-3 rounded-full bg-blue-600 px-2 py-0.5 text-[10px] font-bold tracking-wide text-white shadow">📍 LÔ ĐANG Ở ĐÂY</span>}
        {n.state === 'PROBLEM' && <span className={cx('absolute left-3 rounded-full bg-red-600 px-2 py-0.5 text-[10px] font-bold tracking-wide text-white shadow', n.current ? '-top-7' : '-top-3')}>⚠ VẤN ĐỀ</span>}
        <div className="flex items-center justify-between gap-1"><JourneyStatus node={n} /><span className="rounded bg-slate-900/10 px-1 text-[10px] font-bold text-slate-600">{i + 1}</span></div>
        <div className="mt-1 text-[14px] font-extrabold leading-tight tracking-tight text-slate-900">{n.label}</div>
        <div className={cx('mt-0.5 line-clamp-2 text-[12px] leading-snug', n.state === 'PROBLEM' ? 'font-bold text-red-700' : 'font-medium text-slate-700')}>{n.blockers[0] || n.evidence || 'Chưa có bằng chứng thực tế'}</div>
        <div className="text-[11.5px] font-semibold text-slate-500">{n.deadline ? `⏱ ${n.deadline}` : ''}</div>
        <div className="mt-auto flex items-center gap-1 text-[10.5px] font-bold"><span className="rounded bg-slate-900/[0.07] px-1 py-px">📄 {n.documentIds.length}</span>{n.blockers.length > 0 && <span className="rounded bg-red-600 px-1 py-px text-white">⚠ {n.blockers.length}</span>}{s.finance.actual?.filter(l => l.journeyStage === n.id).length ? <span className="rounded bg-slate-900/[0.07] px-1 py-px">₫ {s.finance.actual.filter(l => l.journeyStage === n.id).length}</span> : null}</div>
      </button>; })}
    </div>
    <div className="absolute bottom-3 left-3 z-20 flex items-center gap-1 rounded-lg border border-slate-300 bg-white p-1 shadow-md" onPointerDown={e => e.stopPropagation()}>
      <button type="button" onClick={() => center(1.2)} aria-label="Zoom In" className="touch-target rounded text-lg font-bold text-slate-700">+</button><button type="button" onClick={() => center(1 / 1.2)} aria-label="Zoom Out" className="touch-target rounded text-lg font-bold text-slate-700">−</button><span className="w-11 text-center text-[11px] font-semibold tabular-nums text-slate-500">{Math.round(tf.k * 100)}%</span>
      <button type="button" onClick={() => { autoFit.current = true; fit(); }} className="touch-target rounded px-2.5 text-xs font-bold">⤢ Fit Journey</button><button type="button" onClick={() => { autoFit.current = false; setTf({ k: 1, x: 24, y: 20 }); }} className="touch-target rounded px-2.5 text-xs font-semibold">↺ Reset View</button>
    </div>
    <div className="pointer-events-none absolute bottom-16 right-3 z-20 flex flex-col gap-1 rounded-lg border border-slate-300 bg-white/95 px-2.5 py-2 text-[11px] font-semibold text-slate-600 shadow">{Object.entries(JOURNEY_META).map(([state, m]) => { const Icon = m.icon; return <span key={state} className="flex items-center gap-1.5"><Icon size={12} className={m.text} />{m.label}</span>; })}</div>
    <div className="pointer-events-none absolute right-3 top-3 z-20 rounded bg-white/80 px-2 py-1 text-[10.5px] text-slate-500">Kéo để di chuyển · Cuộn để zoom · Click node để xem</div>
  </div>;
}
