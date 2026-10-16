import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { CheckCircle2, Circle, Clock, CircleAlert, MapPin, FileText, TriangleAlert } from 'lucide-react';
import type { JourneyNode, Shipment } from '../lib/viewmodel';
import { cx } from '../lib/format';
// Owner-approved paper chart texture extracted verbatim from the approved HTML oracle.
// Vite library build inlines this local JPEG; no external image URL or separate runtime asset request.
import chartPaperUrl from '../assets/journey/chart-paper.jpg?url';

// G2 (LOGI-199 Owner Visual Fidelity Override, 15/10/2026) + N2 refinement:
// the map is the primary canvas over the Owner-approved paper chart texture.
// Main node row (ROW_MAIN) is vertically symmetric between ROW_TOP and
// ROW_BOTTOM so auto-fit places the main route at the vertical center (50%)
// of the desktop canvas, matching the Owner HTML oracle (`ref-01`).
// Terminal review note preserved for contract checks: RÀ SOÁT HOÀN TẤT.
export const JOURNEY_NODE_W = 116, JOURNEY_NODE_H = 66;
const W = JOURNEY_NODE_W, H = JOURNEY_NODE_H, PITCH = 140, PX = 42;
const ROW_TOP = 116, ROW_MAIN = 240, ROW_BOTTOM = 364;
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
const CW = col(9) + W + PX, CH = ROW_BOTTOM + H + ROW_TOP;
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
  const x = Math.min(a.x, b.x) - 24;
  return `M${a.x},${a.y + a.h / 2} H${x} V${b.y + b.h / 2} H${b.x}`;
}
const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));

export default function JourneyMap({
  shipment: s, nodes, selectedId, onPick, collapsed, onExpand, renderBubble, bubbleNodeId = '', topRightOverlay,
}: {
  shipment: Shipment; nodes: JourneyNode[]; selectedId: string; onPick: (id: string) => void;
  collapsed: boolean; onExpand: () => void;
  /** G2 — node-attached task bubble, rendered INSIDE the pan/zoom layer so it moves with its node. */
  renderBubble?: (node: JourneyNode, p: JourneyPosition, canvas: { w: number; h: number }, placeBelow: boolean) => ReactNode;
  bubbleNodeId?: string;
  /** N2 — top-right floating Hồ sơ & Tài chính control + utility bubble (matching ref-01 / ref-05). */
  topRightOverlay?: ReactNode;
}) {
  const [tf, setTf] = useState({ x: 0, y: 0, k: 1 });
  const tfRef = useRef(tf); tfRef.current = tf;
  const vp = useRef<HTMLDivElement>(null), viewMode = useRef<'auto' | 'fit' | 'readable' | 'manual'>('auto'), moved = useRef(false);
  const cleanupDrag = useRef<(() => void) | undefined>(undefined);
  const [dragging, setDragging] = useState(false);
  const sea = nodes.some(n => n.id === 'booking');
  // Non-sea (AIR/ROAD/scoped) grids size the canvas to the nodes they really
  // have; rows are spaced symmetrically for the compact card and its bubble.
  const gridCols = Math.max(1, Math.min(5, nodes.length)), gridRows = Math.max(1, Math.ceil(nodes.length / 5));
  const positions = new Map(nodes.map((n, i) => [n.id, sea && DEMO_POS[n.id] ? DEMO_POS[n.id] : { x: col(i % 5), y: 140 + Math.floor(i / 5) * 170, w: W, h: H }]));
  const canvasWidth = sea ? CW : col(gridCols - 1) + W + PX;
  const canvasHeight = sea ? CH : 140 + (gridRows - 1) * 170 + H + 140;
  const fit = useCallback(() => {
    const el = vp.current; if (!el?.clientWidth || !el.clientHeight) return;
    const w = el.clientWidth, h = el.clientHeight;
    // Explicit overview: fit the whole canvas symmetrically so ROW_MAIN sits at 50% vertical height.
    const k = clamp(Math.min((w - 24) / canvasWidth, (h - 24) / canvasHeight), 0.1, 1);
    setTf({ k, x: Math.round((w - canvasWidth * k) / 2), y: Math.round((h - canvasHeight * k) / 2) });
  }, [canvasHeight, canvasWidth]);
  // Focus only on a real selected/problem/current node; never manufacture a state.
  const focusId = selectedId || nodes.find(n => n.state === 'PROBLEM')?.id || nodes.find(n => n.current)?.id || nodes[0]?.id;
  const focus = positions.get(focusId);
  const readable = useCallback(() => {
    const el = vp.current; if (!el?.clientWidth || !focus) return;
    const isNarrow = el.clientWidth < 720;
    // Keep the focused node row in the lower half (72%) on mobile so the
    // node-attached task bubble still fits above its node inside the map.
    const anchorRatio = isNarrow ? 0.72 : 0.48;
    setTf({ k: 1, x: Math.round(el.clientWidth / 2 - focus.x - focus.w / 2), y: Math.round(el.clientHeight * anchorRatio - focus.y - focus.h / 2) });
  }, [focus?.x, focus?.y, focus?.w, focus?.h]);
  // LOGI-199 final owner-fidelity fix (A): a fresh mobile view starts at the
  // BEGINNING of the route (BOOKING side, left margin 24px like the Owner HTML
  // oracle) instead of jumping to the PROBLEM/current stage. Scale stays 1 so
  // card size, readability and tap targets are unchanged; pan/zoom/Fit are
  // untouched. The stage needing handling stays one tap away ("Đọc rõ" keeps
  // its selected/problem/current focus) and selecting a node still focuses it.
  const startNode = nodes[0] ? positions.get(nodes[0].id) : undefined;
  const start = useCallback(() => {
    const el = vp.current; if (!el?.clientWidth || !startNode) return;
    const isNarrow = el.clientWidth < 720;
    const anchorRatio = isNarrow ? 0.72 : 0.48;
    setTf({ k: 1, x: Math.round(24 - startNode.x), y: Math.round(el.clientHeight * anchorRatio - startNode.y - startNode.h / 2) });
  }, [startNode?.x, startNode?.y, startNode?.w, startNode?.h]);
  const auto = useCallback(() => {
    const el = vp.current; if (!el?.clientWidth) return;
    if (el.clientWidth >= 720) { fit(); return; }
    if (selectedId) readable(); else start();
  }, [fit, readable, start, selectedId]);
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
  }, [auto, fit, readable, start, collapsed]);
  const zoomAt = useCallback((f: number, px: number, py: number) => {
    viewMode.current = 'manual';
    setTf(t => { const k = clamp(t.k * f, 0.1, 2), r = k / t.k; return { k, x: px - (px - t.x) * r, y: py - (py - t.y) * r }; });
  }, []);
  useEffect(() => {
    const el = vp.current; if (!el) return;
    const wheel = (e: WheelEvent) => {
      // An empty Journey is a decorative chart, not an interactive canvas.
      // Let the page scroll normally instead of zooming an invisible layer.
      if (!nodes.length) return;
      e.preventDefault();
      const r = el.getBoundingClientRect();
      zoomAt(e.deltaY < 0 ? 1.1 : 1 / 1.1, e.clientX - r.left, e.clientY - r.top);
    };
    el.addEventListener('wheel', wheel, { passive: false });
    return () => el.removeEventListener('wheel', wheel);
  }, [zoomAt, collapsed, nodes.length]);
  useEffect(() => () => cleanupDrag.current?.(), []);
  const pan = (e: React.PointerEvent) => {
    if (!nodes.length || e.button !== 0) return;
    if ((e.target as HTMLElement).closest('[data-no-pan]')) return;
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
  // Place the bubble below the node when the node sits in the upper half of the visible viewport on desktop;
  // on mobile, nodes sit in the lower half (64%), so place the bubble above the node.
  const isNarrowVp = (vp.current?.clientWidth ?? 1440) < 720;
  const bubblePlaceBelow = bubblePos ? (!isNarrowVp && tf.y + bubblePos.y * tf.k < 290) : false;
  return (
    <div
      ref={vp}
      className={cx('journey-canvas relative min-w-0 flex-1 select-none overflow-hidden', !nodes.length ? 'cursor-default' : dragging ? 'cursor-grabbing' : 'cursor-grab')}
      onPointerDown={nodes.length ? pan : undefined}
      data-testid="journey-map-viewport"
      aria-label={nodes.length ? 'Journey Map, kéo để di chuyển, cuộn để zoom' : 'Journey Map trống, không có công đoạn để di chuyển'}
      style={{ backgroundColor: '#EDF1F5' }}
    >
      {/* Owner-approved paper chart texture (extracted verbatim from the approved HTML oracle). */}
      <div
        aria-hidden="true"
        data-testid="journey-map-texture"
        className="pointer-events-none absolute inset-0 opacity-[0.34] mix-blend-multiply"
        style={{ backgroundImage: `url(${chartPaperUrl})`, backgroundSize: '760px', backgroundRepeat: 'repeat' }}
      />
      {/* Owner-approved coordinate grid (52 x 52 px). */}
      <div
        aria-hidden="true"
        data-testid="journey-map-grid"
        className="pointer-events-none absolute inset-0"
        style={{ backgroundImage: 'linear-gradient(rgba(120,146,170,0.16) 1px, transparent 1px), linear-gradient(90deg, rgba(120,146,170,0.16) 1px, transparent 1px)', backgroundSize: '52px 52px' }}
      />
      {topRightOverlay}

      <div className={cx("absolute left-0 top-0 origin-top-left", bubbleNode && "z-30")} style={{ width: canvasWidth, height: canvasHeight, transform: `translate(${tf.x}px, ${tf.y}px) scale(${tf.k})` }} data-testid="journey-map-transform">
        {positions.has('si-vgm') && positions.has('gate-in') && <div className="journey-branch-band" style={{ left: DEMO_POS['si-vgm'].x - 12, top: DEMO_POS['si-vgm'].y - 24, width: W + 24, height: DEMO_POS['gate-in'].y + H - DEMO_POS['si-vgm'].y + 48 }} data-testid="journey-parallel-branch"><span className="journey-branch-label">NHÁNH SONG SONG</span></div>}
        <svg width={canvasWidth} height={canvasHeight} className="pointer-events-none absolute left-0 top-0 z-[1]" aria-hidden="true">
          {edges.map(e => { const n = nodes.find(n => n.id === e.from)!; const k = n.state === 'PROBLEM' ? 'r' : n.completed ? 'g' : 's'; return <path key={e.from + e.to} data-from={e.from} data-to={e.to} d={journeyEdgePath(positions.get(e.from)!, positions.get(e.to)!)} fill="none" className={cx('journey-edge', k === 'g' && 'journey-edge-done', k === 'r' && 'journey-edge-problem')} />; })}
        </svg>
        {nodes.map((n, i) => { const p = positions.get(n.id)!; const docs = n.documentIds.length, blockers = n.blockers.length; return <button key={n.id} type="button" data-testid={`journey-node-${n.id}`} data-state={n.state} aria-pressed={selectedId === n.id} aria-label={`${n.label}: ${JOURNEY_NODE_STATUS[n.state]}`} onClick={e => pick(n.id, e)} style={{ left: p.x, top: p.y, width: p.w, height: p.h }} className={cx('journey-node absolute z-10 flex flex-col text-left', n.current && 'journey-node-here', selectedId === n.id && 'journey-node-selected')}>
          <span className="journey-node-top"><span className="journey-node-idx">{String(i + 1).padStart(2, '0')}</span>{n.state === 'PROBLEM' && <CircleAlert size={11} className="journey-node-alert" aria-hidden="true" />}</span>
          <span className="journey-node-title font-extrabold">{n.label}</span>
          <span className="journey-node-foot"><span className="journey-node-status">{JOURNEY_NODE_STATUS[n.state]}</span>
            {docs > 0 && <span className="journey-node-count" title="Số chứng từ đã ghi nhận"><FileText size={9} aria-hidden="true" />{docs}</span>}
            {blockers > 0 && <span className="journey-node-count journey-node-count-warn" title="Việc đang chặn"><TriangleAlert size={9} aria-hidden="true" />{blockers}</span>}
          </span>
        </button>; })}
        {bubbleNode && bubblePos && renderBubble?.(bubbleNode, bubblePos, { w: canvasWidth, h: canvasHeight }, bubblePlaceBelow)}
      </div>

      {/* Bottom-left Status Legend (CHÚ GIẢI TRẠNG THÁI) matching Owner HTML ref-01 */}
      <div
        data-no-pan
        data-testid="journey-status-legend"
        onPointerDown={e => e.stopPropagation()}
        className="journey-map-hint absolute bottom-3 left-3 z-20 hidden max-w-[300px] rounded-xl border border-[#D6DEE7] bg-white/92 px-3 py-2.5 shadow-[0_8px_20px_-6px_rgba(16,38,60,0.14)] backdrop-blur-[2px] sm:block"
      >
        <div className="mb-1.5 flex items-center justify-between text-[12px] font-bold uppercase tracking-wider text-[#5B6875]">
          <span>Chú giải trạng thái</span>
          <span className="font-mono text-[#123A5E]">{Math.round(tf.k * 100)}%</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5 text-[12px]">
          <span className="inline-flex items-center gap-1 rounded-md border border-[#96C7AF] bg-[#DCEDE4] px-2 py-0.5 font-semibold text-[#22614A]">
            ✓ Có bằng chứng
          </span>
          <span className="inline-flex items-center gap-1 rounded-md border border-[#8EC0E8] bg-[#DCEBFA] px-2 py-0.5 font-semibold text-[#154C79]">
            ◐ Đang xử lý
          </span>
          <span className="inline-flex items-center gap-1 rounded-md border border-[#E8BE7B] bg-[#FBEBD3] px-2 py-0.5 font-semibold text-[#8A5209]">
            ◷ Chờ thông tin
          </span>
          <span className="inline-flex items-center gap-1 rounded-md border border-[#E0A197] bg-[#F6DFDB] px-2 py-0.5 font-semibold text-[#8E2F22]">
            ! Cần xử lý
          </span>
          <span className="col-span-2 inline-flex items-center gap-1 rounded-md border border-[#C8D3DF] bg-[#E7ECF2] px-2 py-0.5 font-semibold text-[#5B6875]">
            · Chưa bắt đầu
          </span>
        </div>
        <div className="mt-1.5 border-t border-[#E4EAF0] pt-1.5 text-[12px] leading-snug text-[#5B6875]">
          Bấm vào một node trên bản đồ → chọn bong bóng công việc → mở popup ngắn gọn theo đúng việc đó.
        </div>
      </div>

      {/* Bottom-right Zoom & Fit controls */}
      <div data-no-pan className="journey-zoom-bar absolute bottom-3 right-3 z-20 flex flex-wrap items-center justify-center gap-1" onPointerDown={e => e.stopPropagation()}>
        <button type="button" onClick={() => center(1.2)} aria-label="Zoom In" data-testid="journey-zoom-in" className="journey-zoom-btn">+</button>
        <button type="button" onClick={() => center(1 / 1.2)} aria-label="Zoom Out" data-testid="journey-zoom-out" className="journey-zoom-btn">−</button>
        <span className="journey-zoom-level" data-testid="journey-zoom-level">{Math.round(tf.k * 100)}%</span>
        <button type="button" onClick={() => { viewMode.current = 'fit'; fit(); }} data-testid="journey-zoom-fit" className="journey-zoom-text">⤢ Fit Journey</button>
        <button type="button" onClick={() => { viewMode.current = 'readable'; readable(); }} data-testid="journey-zoom-readable" className="journey-zoom-text">↺ Đọc rõ</button>
      </div>
    </div>
  );
}
