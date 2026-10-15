import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { CheckCircle2, Circle, Clock, CircleAlert, MapPin, FileText, TriangleAlert } from 'lucide-react';
import type { JourneyNode, Shipment } from '../lib/viewmodel';
import { cx } from '../lib/format';
import chartPaperUrl from '../assets/journey/chart-paper.jpg?url';

// G2 (LOGI-199 Owner Visual Fidelity Override, 15/10/2026): the map is the
// primary canvas. Geometry follows the Owner-approved HTML (node 102×58,
// 137px column pitch, main route on one row, SI/VGM above and GATE-IN below
// the branch column, paper chart background). Business state and node ids are
// unchanged; only the presentation and placement of the cards changed.
export const JOURNEY_NODE_W = 102, JOURNEY_NODE_H = 58;
const W = JOURNEY_NODE_W, H = JOURNEY_NODE_H, PITCH = 137, PX = 53;
const ROW_MAIN = 300, ROW_TOP = 176, ROW_BOTTOM = 424;
const col = (c: number) => PX + c * PITCH;
export interface JourneyPosition { x: number; y: number; w: number; h: number }
export const DEMO_POS: Record<string, JourneyPosition> = {
  booking: { x: col(0), y: ROW_MAIN, w: W, h: H },
  pickup: { x: col(1), y: ROW_MAIN, w: W, h: H },
  'customs-export': { x: col(2), y: ROW_MAIN, w: W, h: H },
  'si-vgm': { x: col(3), y: ROW_TOP, w: W, h: H },
  'gate-in': { x: col(3), y: ROW_BOTTOM, w: W, h: H },
  // LOGI-199 T2 — LCL CFS/consolidation occupies the FCL gate-in slot (never both).
  'cfs-receipt': { x: col(3), y: ROW_BOTTOM, w: W, h: H },
  etd: { x: col(4), y: ROW_MAIN, w: W, h: H },
  'on-board': { x: col(5), y: ROW_MAIN, w: W, h: H },
  transit: { x: col(6), y: ROW_MAIN, w: W, h: H },
  arrival: { x: col(7), y: ROW_MAIN, w: W, h: H },
  'customs-import': { x: col(8), y: ROW_MAIN, w: W, h: H },
  delivery: { x: col(9), y: ROW_MAIN, w: W, h: H },
};
const CW = col(9) + W + PX, CH = ROW_BOTTOM + H + 60;
export const JOURNEY_META = {
  COMPLETED: { label: 'Hoàn thành', icon: CheckCircle2, cls: 'border-emerald-500 bg-emerald-50 border-2', text: 'text-emerald-700' },
  CURRENT: { label: 'Hiện tại', icon: MapPin, cls: 'border-blue-600 bg-white border-[3px] ring-4 ring-blue-100 shadow-lg shadow-blue-200/60', text: 'text-blue-700' },
  WAITING: { label: 'Đang chờ', icon: Clock, cls: 'border-amber-500 bg-amber-50 border-2 border-dashed', text: 'text-amber-800' },
  PROBLEM: { label: 'Cần xử lý', icon: CircleAlert, cls: 'border-red-600 bg-red-50 border-[3px] journey-problem-pulse', text: 'text-red-700' },
  UPCOMING: { label: 'Chưa xác định / sắp tới', icon: Circle, cls: 'border-slate-300 bg-slate-50/80 border-2 border-dashed', text: 'text-slate-500' },
};
// Owner HTML node status vocabulary (compact chip on the card).
export const JOURNEY_NODE_STATUS: Record<JourneyNode['state'], string> = {
  PROBLEM: 'CẦN XỬ LÝ',
  CURRENT: 'ĐANG XỬ LÝ',
  WAITING: 'CHỜ THÔNG TIN',
  COMPLETED: 'CÓ BẰNG CHỨNG',
  UPCOMING: 'CHƯA BẮT ĐẦU',
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

export default function JourneyMap({ shipment: s, nodes, selectedId, onPick, collapsed, onExpand, renderBubble, bubbleNodeId = '' }: {
  shipment: Shipment; nodes: JourneyNode[]; selectedId: string; onPick: (id: string) => void;
  collapsed: boolean; onExpand: () => void;
  /** G2 — node-attached task bubble, rendered INSIDE the pan/zoom layer so it moves with its node. */
  renderBubble?: (node: JourneyNode, p: JourneyPosition, canvas: { w: number; h: number }, placeBelow: boolean) => ReactNode;
  bubbleNodeId?: string;
}) {
  const [tf, setTf] = useState({ x: 0, y: 0, k: 1 });
  const tfRef = useRef(tf); tfRef.current = tf;
  const vp = useRef<HTMLDivElement>(null), viewMode = useRef<'auto' | 'fit' | 'readable' | 'manual'>('auto'), moved = useRef(false);
  const cleanupDrag = useRef<(() => void) | undefined>(undefined);
  const [dragging, setDragging] = useState(false);
  const sea = nodes.some(n => n.id === 'booking');
  // Non-sea (AIR/ROAD/scoped) grids size the canvas to the nodes they really
  // have; rows are spaced for the compact card and the bubble above it.
  const gridCols = Math.max(1, Math.min(5, nodes.length)), gridRows = Math.max(1, Math.ceil(nodes.length / 5));
  const positions = new Map(nodes.map((n, i) => [n.id, sea && DEMO_POS[n.id] ? DEMO_POS[n.id] : { x: col(i % 5), y: 120 + Math.floor(i / 5) * 170, w: W, h: H }]));
  const canvasWidth = sea ? CW : col(gridCols - 1) + W + PX;
  const canvasHeight = sea ? CH : 120 + (gridRows - 1) * 170 + H + 80;
  const fit = useCallback(() => {
    const el = vp.current; if (!el?.clientWidth || !el.clientHeight) return;
    const w = el.clientWidth, h = el.clientHeight;
    // Explicit overview: the whole canvas, never larger than 1:1.
    const k = clamp(Math.min((w - 24) / canvasWidth, (h - 24) / canvasHeight), 0.1, 1);
    setTf({ k, x: (w - canvasWidth * k) / 2, y: Math.max(12, (h - canvasHeight * k) / 2) });
  }, [canvasHeight, canvasWidth]);
  // Focus only on a real selected/problem/current node; never manufacture a state.
  const focusId = selectedId || nodes.find(n => n.state === 'PROBLEM')?.id || nodes.find(n => n.current)?.id || nodes[0]?.id;
  const focus = positions.get(focusId);
  const readable = useCallback(() => {
    const el = vp.current; if (!el?.clientWidth || !focus) return;
    setTf({ k: 1, x: el.clientWidth / 2 - focus.x - focus.w / 2, y: el.clientHeight * 0.4 - focus.y - focus.h / 2 });
  }, [focus?.x, focus?.y, focus?.w, focus?.h]);
  // Initial view (auto): a desktop-width canvas fits at ≤1:1 so the whole
  // route is visible like the reference; a phone-width canvas opens at 1:1 on
  // the focused node so text stays readable, pan/zoom reveals the rest.
  const auto = useCallback(() => {
    const el = vp.current; if (!el?.clientWidth) return;
    if (el.clientWidth < 720) readable(); else fit();
  }, [fit, readable]);
  useEffect(() => {
    const el = vp.current; if (!el) return;
    const layout = () => {
      if (viewMode.current === 'auto') auto();
      else if (viewMode.current === 'fit') fit();
      else if (viewMode.current === 'readable') readable();
    };
    if (typeof ResizeObserver === 'undefined') { layout(); return; }
    const ro = new ResizeObserver(layout);
    ro.observe(el); layout(); return () => ro.disconnect();
  }, [auto, fit, readable, collapsed]);
  const zoomAt = useCallback((f: number, px: number, py: number) => {
    viewMode.current = 'manual';
    setTf(t => { const k = clamp(t.k * f, 0.1, 2), r = k / t.k; return { k, x: px - (px - t.x) * r, y: py - (py - t.y) * r }; });
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
      moved.current = true; viewMode.current = 'manual'; setDragging(true);
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
  const edges = (s.journey?.edges ?? []).filter(e => positions.has(e.from) && positions.has(e.to));
  const pick = (id: string, e: React.MouseEvent) => { if (e.detail === 0 || !moved.current) onPick(id); };
  const bubbleNode = bubbleNodeId ? nodes.find(n => n.id === bubbleNodeId) : undefined;
  const bubblePos = bubbleNode ? positions.get(bubbleNode.id) : undefined;
  // Place the bubble below the node when the node sits near the TOP of the
  // visible viewport (screen space), otherwise it is clipped by the canvas edge.
  const bubblePlaceBelow = bubblePos ? tf.y + bubblePos.y * tf.k < 300 : false;
  return <div ref={vp} className={cx('journey-canvas relative min-w-0 flex-1 select-none overflow-hidden', dragging ? 'cursor-grabbing' : 'cursor-grab')} onPointerDown={pan} data-testid="journey-map-viewport" aria-label="Journey Map, kéo để di chuyển, cuộn để zoom" style={{ backgroundImage: `url(${chartPaperUrl})` }}>
    <div className="absolute left-0 top-0 origin-top-left" style={{ width: canvasWidth, height: canvasHeight, transform: `translate(${tf.x}px, ${tf.y}px) scale(${tf.k})` }} data-testid="journey-map-transform">
      {positions.has('si-vgm') && positions.has('gate-in') && <div className="journey-branch-band" style={{ left: DEMO_POS['si-vgm'].x - 12, top: DEMO_POS['si-vgm'].y - 24, width: W + 24, height: DEMO_POS['gate-in'].y + H - DEMO_POS['si-vgm'].y + 48 }} data-testid="journey-parallel-branch"><span className="journey-branch-label">NHÁNH SONG SONG</span></div>}
      <svg width={canvasWidth} height={canvasHeight} className="pointer-events-none absolute left-0 top-0 z-[1]" aria-hidden="true">
        {edges.map(e => { const n = nodes.find(n => n.id === e.from)!; const k = n.state === 'PROBLEM' ? 'r' : n.completed ? 'g' : 's'; return <path key={e.from + e.to} data-from={e.from} data-to={e.to} d={journeyEdgePath(positions.get(e.from)!, positions.get(e.to)!)} fill="none" className={cx('journey-edge', k === 'g' && 'journey-edge-done', k === 'r' && 'journey-edge-problem')} />; })}
      </svg>
      {nodes.map((n, i) => { const p = positions.get(n.id)!; const docs = n.documentIds.length, blockers = n.blockers.length; return <button key={n.id} type="button" data-testid={`journey-node-${n.id}`} data-state={n.state} aria-pressed={selectedId === n.id} aria-label={`${n.label}: ${JOURNEY_NODE_STATUS[n.state]}`} onClick={e => pick(n.id, e)} style={{ left: p.x, top: p.y, width: p.w, height: p.h }} className={cx('journey-node absolute z-10 flex flex-col text-left', n.current && 'journey-node-here', selectedId === n.id && 'journey-node-selected')}>
        <span className="journey-node-top"><span className="journey-node-idx">{String(i + 1).padStart(2, '0')}</span>{n.state === 'PROBLEM' && <CircleAlert size={11} className="journey-node-alert" aria-hidden="true" />}</span>
        <span className="journey-node-title">{n.label}</span>
        <span className="journey-node-foot"><span className="journey-node-status">{JOURNEY_NODE_STATUS[n.state]}</span>
          {docs > 0 && <span className="journey-node-count" title="Số chứng từ đã ghi nhận"><FileText size={9} aria-hidden="true" />{docs}</span>}
          {blockers > 0 && <span className="journey-node-count journey-node-count-warn" title="Việc đang chặn"><TriangleAlert size={9} aria-hidden="true" />{blockers}</span>}
        </span>
      </button>; })}
      {bubbleNode && bubblePos && renderBubble?.(bubbleNode, bubblePos, { w: canvasWidth, h: canvasHeight }, bubblePlaceBelow)}
    </div>
    <div className="journey-zoom-bar absolute bottom-3 left-1/2 z-20 flex -translate-x-1/2 flex-wrap items-center justify-center gap-1" onPointerDown={e => e.stopPropagation()}>
      <button type="button" onClick={() => center(1.2)} aria-label="Zoom In" className="journey-zoom-btn">+</button><button type="button" onClick={() => center(1 / 1.2)} aria-label="Zoom Out" className="journey-zoom-btn">−</button><span className="journey-zoom-level" data-testid="journey-zoom-level">{Math.round(tf.k * 100)}%</span>
      <button type="button" onClick={() => { viewMode.current = 'fit'; fit(); }} className="journey-zoom-text">⤢ Fit Journey</button><button type="button" onClick={() => { viewMode.current = 'readable'; readable(); }} className="journey-zoom-text">↺ Đọc rõ</button>
    </div>
    <div className="journey-map-hint pointer-events-none absolute left-3 top-3 z-20 rounded bg-white/90 px-2 py-1 text-[11px] text-slate-600">Kéo để xem · Cuộn để zoom</div>
  </div>;
}
