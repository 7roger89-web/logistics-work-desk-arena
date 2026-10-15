import { ChevronRight, FileText, X } from 'lucide-react';
import type { JourneyNode, Shipment, WorkModuleRollup } from '../lib/viewmodel';
import { cx } from '../lib/format';
import { JOURNEY_NODE_STATUS, JOURNEY_NODE_W, type JourneyPosition } from './JourneyMap';
import { stageAction } from './JourneyQuickPanel';

// G2 — node-attached task bubble (Owner HTML: node → bubble → task popup).
// Every row is a REAL task of this node, derived from the projection: the
// stage action/blocker, extra blockers, its document requirement and the Work
// Modules anchored at this node. Nothing is invented from the HTML demo.

export interface BubbleTask {
  key: string;
  title: string;
  meta: string;
  tone: 'PROBLEM' | 'CURRENT' | 'WAITING' | 'COMPLETED' | 'UPCOMING';
  onOpen?: () => void;
  disabled?: boolean;
}

export function bubbleTasksFor(
  node: JourneyNode,
  s: Shipment,
  modules: WorkModuleRollup[],
  onTask: (node: JourneyNode, work: string) => void,
  onModule: (stepId: string) => void,
  nodes: JourneyNode[],
): BubbleTask[] {
  const tasks: BubbleTask[] = [];
  const docs = node.documentIds.length;
  const attached = (s.attachments ?? []).filter(f => node.documentIds.includes(f.id)).length;
  // 1. The stage's own work item — the same text the popup opens with.
  tasks.push({
    key: 'stage',
    title: stageAction(node),
    meta: `${node.deadline ? `HẠN ${node.deadline}` : 'CHƯA GHI NHẬN HẠN'} · ${docs} CHỨNG TỪ`,
    tone: node.state,
    onOpen: () => onTask(node, 'info'),
  });
  // 2. Each additional blocker is its own task (never merged).
  node.blockers.slice(1).forEach((b, i) => tasks.push({
    key: `blocker-${i}`, title: b, meta: 'VIỆC ĐANG CHẶN', tone: 'PROBLEM', onOpen: () => onTask(node, 'info'),
  }));
  // 3. Documents required at this stage.
  if (node.documentCategories.length > 0 || docs > 0) tasks.push({
    key: 'docs',
    title: 'Chứng từ đính kèm công đoạn',
    meta: `${attached} TỆP ĐÃ GHI NHẬN${node.documentCategories.length ? ` · ${node.documentCategories.length} LOẠI YÊU CẦU` : ''}`,
    tone: attached > 0 ? 'COMPLETED' : 'WAITING',
    onOpen: () => onTask(node, 'docs'),
  });
  // 4. Work Modules anchored at this node (their next step opens in the popup).
  modules.filter(m => m.anchorStage === node.id).forEach(m => {
    const stepId = m.nextStepId ? `wm-${m.instanceId}-${m.nextStepId}` : '';
    const reachable = Boolean(stepId && nodes.some(n => n.id === stepId));
    tasks.push({
      key: `module-${m.instanceId}`,
      title: m.name,
      meta: `${m.summary || 'QUY TRÌNH PHÁT SINH'}${m.nextStep ? ` · TIẾP: ${m.nextStep}` : ''}`,
      tone: m.status === 'DONE' ? 'COMPLETED' : m.status === 'BLOCKING' ? 'PROBLEM' : m.status === 'WAITING' ? 'WAITING' : 'UPCOMING',
      onOpen: reachable ? () => onModule(stepId) : undefined,
      disabled: !reachable,
    });
  });
  return tasks;
}

const TONE_DOT: Record<BubbleTask['tone'], string> = {
  PROBLEM: 'bg-[#C0392B]',
  CURRENT: 'bg-[#1D6FA8]',
  WAITING: 'bg-[#D97706]',
  COMPLETED: 'bg-[#2E7D32]',
  UPCOMING: 'bg-[#94A3B8]',
};

export default function JourneyBubble({ node, pos, canvas, tasks, onClose, onQuick, placeBelow }: {
  node: JourneyNode; pos: JourneyPosition; canvas: { w: number; h: number };
  tasks: BubbleTask[]; onClose: () => void; onQuick: () => void; placeBelow: boolean;
}) {
  const BUBBLE_W = 304;
  // Above the node by default; below it for the top branch so it never leaves the canvas.
  const above = !placeBelow;
  const left = Math.max(8, Math.min(canvas.w - BUBBLE_W - 8, pos.x + JOURNEY_NODE_W / 2 - BUBBLE_W / 2));
  const place = above ? { bottom: canvas.h - pos.y + 16 } : { top: pos.y + pos.h + 16 };
  const headerTone = node.state === 'PROBLEM' ? 'text-[#C0392B]' : node.state === 'COMPLETED' ? 'text-[#2E7D32]' : 'text-[#1D6FA8]';
  return <div className="journey-bubble absolute z-30" style={{ left, width: BUBBLE_W, ...place }} data-testid="journey-bubble" data-node={node.id} role="dialog" aria-label={`Công việc của ${node.label}`}
    onPointerDown={e => e.stopPropagation()} onClick={e => e.stopPropagation()}>
    <div className="journey-bubble-head">
      <div className="min-w-0">
        <div className="journey-bubble-kicker">{node.label.toUpperCase()}</div>
        <div className={cx('journey-bubble-state', headerTone)}>{JOURNEY_NODE_STATUS[node.state]}</div>
      </div>
      <button type="button" onClick={onClose} aria-label="Đóng bong bóng công việc" className="journey-bubble-close"><X size={14} aria-hidden="true" /></button>
    </div>
    <ul className="journey-bubble-list" data-testid="journey-bubble-tasks">
      {tasks.map(t => <li key={t.key}>
        <button type="button" onClick={t.onOpen} disabled={t.disabled || !t.onOpen} data-testid={`journey-bubble-task-${t.key}`}
          className={cx('journey-bubble-task', t.disabled && 'opacity-60')}>
          <span className={cx('journey-bubble-dot', TONE_DOT[t.tone])} aria-hidden="true" />
          <span className="min-w-0 flex-1">
            <span className="journey-bubble-title">{t.title}</span>
            <span className="journey-bubble-meta">{t.meta}</span>
          </span>
          <ChevronRight size={14} className="shrink-0 text-[#94A3B8]" aria-hidden="true" />
        </button>
      </li>)}
    </ul>
    <button type="button" onClick={onQuick} className="journey-bubble-foot" data-testid="journey-bubble-overview">
      <FileText size={13} aria-hidden="true" /> Xem thông tin công đoạn
    </button>
  </div>;
}
