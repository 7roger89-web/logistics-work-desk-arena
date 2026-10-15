import { ChevronRight, FileText, Wrench, X } from 'lucide-react';
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

const TONE_BADGE: Record<BubbleTask['tone'], { text: string; cls: string }> = {
  PROBLEM:   { text: '! Cần xử lý',     cls: 'border-[#E0A197] bg-[#F6DFDB] text-[#8E2F22]' },
  CURRENT:   { text: '◐ Đang xử lý',    cls: 'border-[#8EC0E8] bg-[#DCEBFA] text-[#154C79]' },
  WAITING:   { text: '◷ Chờ thông tin', cls: 'border-[#E8BE7B] bg-[#FBEBD3] text-[#8A5209]' },
  COMPLETED: { text: '✓ Có bằng chứng', cls: 'border-[#96C7AF] bg-[#DCEDE4] text-[#22614A]' },
  UPCOMING:  { text: '· Chưa bắt đầu',  cls: 'border-[#C8D3DF] bg-[#E7ECF2] text-[#5B6875]' },
};

export default function JourneyBubble({ node, pos, canvas, tasks, onClose, onQuick, placeBelow }: {
  node: JourneyNode; pos: JourneyPosition; canvas: { w: number; h: number };
  tasks: BubbleTask[]; onClose: () => void; onQuick: () => void; placeBelow: boolean;
}) {
  const BUBBLE_W = 328;
  // Above the node by default; below it when the node is in the upper half of the viewport.
  const above = !placeBelow;
  const left = Math.max(8, Math.min(canvas.w - BUBBLE_W - 8, pos.x + JOURNEY_NODE_W / 2 - BUBBLE_W / 2));
  const place = above ? { bottom: canvas.h - pos.y + 14 } : { top: pos.y + pos.h + 14 };
  const primaryStageTask = tasks.find(t => t.key === 'stage');
  return (
    <div
      className="journey-bubble absolute z-30"
      style={{ left, width: BUBBLE_W, ...place }}
      data-testid="journey-bubble"
      data-node={node.id}
      role="dialog"
      aria-label={`Công việc của ${node.label}`}
      onPointerDown={e => e.stopPropagation()}
      onClick={e => e.stopPropagation()}
    >
      <div data-testid="journey-side-panel">
        <div data-testid="journey-quick-panel">
          <div className="journey-bubble-head">
            <div className="min-w-0">
              <div className="journey-bubble-kicker">{node.label.toUpperCase()}</div>
              <div className="journey-bubble-state">{JOURNEY_NODE_STATUS[node.state]}</div>
            </div>
            <button type="button" onClick={onClose} aria-label="Đóng bong bóng công việc" className="journey-bubble-close">
              <X size={14} aria-hidden="true" />
            </button>
          </div>
          <ul className="journey-bubble-list" data-testid="journey-bubble-tasks">
            {tasks.map(t => {
              const b = TONE_BADGE[t.tone];
              return (
                <li key={t.key}>
                  <button
                    type="button"
                    onClick={t.onOpen}
                    disabled={t.disabled || !t.onOpen}
                    data-testid={`journey-bubble-task-${t.key}`}
                    className={cx('journey-bubble-task', t.disabled && 'opacity-60')}
                  >
                    <span className={cx('journey-bubble-dot', TONE_DOT[t.tone])} aria-hidden="true" />
                    <span className="min-w-0 flex-1">
                      <span className="journey-bubble-title">{t.title}</span>
                      <span className="journey-bubble-meta">{t.meta}</span>
                    </span>
                    <span className={cx('shrink-0 rounded-md border px-2 py-0.5 text-[12px] font-semibold', b.cls)}>
                      {b.text}
                    </span>
                    <ChevronRight size={14} className="mt-1 shrink-0 text-[#94A3B8]" aria-hidden="true" />
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="journey-bubble-foot">
            <button
              type="button"
              onClick={() => primaryStageTask?.onOpen ? primaryStageTask.onOpen() : onQuick()}
              data-testid="journey-open-workspace"
              className="inline-flex items-center gap-1.5 text-[12px] font-bold text-[#123A5E] hover:text-[#1D6FA8]"
            >
              <Wrench size={13} aria-hidden="true" /> MỞ CÔNG ĐOẠN →
            </button>
            <button
              type="button"
              onClick={onQuick}
              data-testid="journey-bubble-overview"
              className="inline-flex items-center gap-1 text-[12px] font-semibold text-[#5B6875] hover:text-[#123A5E]"
            >
              <FileText size={13} aria-hidden="true" /> Xem thông tin công đoạn
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
