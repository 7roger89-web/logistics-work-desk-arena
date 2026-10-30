// HEXA customer portal — interaction layer.
//
// Ported from the Owner reference HEXA_LucGiac_DEMO.html (826,336 bytes,
// SHA-256 b91c878e44256e741c533f75e62fdcc89507413d609b0b3d365af85810fbb40a).
// The layout maths, node geometry, edge paths, zoom/pan/fit behaviour and
// bubble placement are the reference implementation. Everything that FABRICATED
// customer evidence was removed: the embedded demo dataset object, the
// canvas/PDF voucher generator, the fake download buttons and the demo
// comment/upload form.
// All data now arrives as server-built props (component.data); this file never
// invents a stage state, an amount, an ETA or a document.

const JOURNEY_NODE_W = 116;
const JOURNEY_NODE_H = 74;
const JOURNEY_MOBILE_BREAKPOINT = 720;
const MOBILE_NODE_W = 110;
const MOBILE_NODE_H = 74;
const MOBILE_PITCH = 116;
const MOBILE_X0 = 8;
const MOBILE_ROW_Y = [120, 220, 320];
const mobileCol = (c) => MOBILE_X0 + c * MOBILE_PITCH;

const DESKTOP_PITCH = 148;
const DESKTOP_X0 = 24;
const desktopCol = (c) => DESKTOP_X0 + c * DESKTOP_PITCH;

// One slot per canonical stage 00..06. Ids are mode-neutral so ROAD and SEA
// share the reference geometry; only the labels differ per mode.
const STAGE_IDS = ['plan', 'pickup', 'consolidate', 'transit', 'customs', 'delivery', 'finance'];

const NODE_POS_DESKTOP = {
  plan: { x: desktopCol(0), y: 205 },
  pickup: { x: desktopCol(1), y: 205 },
  consolidate: { x: desktopCol(2), y: 205 },
  transit: { x: desktopCol(3), y: 205 },
  customs: { x: desktopCol(4), y: 205 },
  delivery: { x: desktopCol(5), y: 205 },
  finance: { x: desktopCol(6), y: 205 },
};
const NODE_POS_MOBILE = {
  plan: { x: mobileCol(0), y: MOBILE_ROW_Y[0] },
  pickup: { x: mobileCol(1), y: MOBILE_ROW_Y[0] },
  consolidate: { x: mobileCol(2), y: MOBILE_ROW_Y[0] },
  transit: { x: mobileCol(2), y: MOBILE_ROW_Y[1] },
  customs: { x: mobileCol(1), y: MOBILE_ROW_Y[1] },
  delivery: { x: mobileCol(0), y: MOBILE_ROW_Y[1] },
  finance: { x: mobileCol(0), y: MOBILE_ROW_Y[2] },
};

// UNKNOWN is a first-class state: it means "no approved evidence", never "not started".
const JOURNEY_NODE_STATUS = {
  COMPLETED: 'CÓ BẰNG CHỨNG',
  CURRENT: 'ĐANG XỬ LÝ',
  WAITING: 'CHỜ THÔNG TIN',
  PROBLEM: 'CẦN XỬ LÝ',
  UPCOMING: 'CHƯA BẮT ĐẦU',
  UNKNOWN: 'CHƯA ĐỐI SOÁT',
};
const STATE_STRIPE = {
  COMPLETED: '#16a34a',
  CURRENT: '#2563eb',
  WAITING: '#eab308',
  PROBLEM: '#dc2626',
  UPCOMING: '#94a3b8',
  UNKNOWN: '#94a3b8',
};

const state = {
  root: null,
  seaChart: '',
  model: null,
  lot: null,
  selectedNodeId: null,
  lastModalNodeId: null,
  currentScale: 1,
  currentPan: { x: 0, y: 0 },
  activeBubblePos: null,
  mobile: false,
  nodeW: JOURNEY_NODE_W,
  nodeH: JOURNEY_NODE_H,
  bound: false,
  // Components v2 transport (setTriggerValue). Everything this UI sends back
  // to Python is an INTENT: open this node's thread, append ONE comment/reply
  // to it, or read ONE attachment. It never sends a customer id, a role or a
  // permission — the server re-derives all of them.
  transport: null,
  triggerSeq: 0,
  // Issue #236 — the ONE node conversation the server delivered, plus the
  // local draft per lot|node. Drafts are keyed so text typed at one stage can
  // never be submitted to another one after switching nodes.
  discussion: null,
  journeyOpen: false,
  discussionPendingKey: '',
  drafts: {},
  sendingRequestId: '',
  sendTimer: null,
  downloadPendingId: '',
  handledDownloadKey: '',
};

const FOCUS_EVENT = 'journey_focus';
const NOTE_CREATE_EVENT = 'journey_note_create';
const NOTE_DOWNLOAD_EVENT = 'journey_note_download';

function q(id) {
  return state.root ? state.root.querySelector('#' + id) : null;
}
function clearChildren(el) {
  if (!el) return;
  while (el.firstChild) el.removeChild(el.firstChild);
  el.textContent = '';
}
function formatMoney(amount, currency) {
  if (typeof amount !== 'number' || Number.isNaN(amount)) return 'UNKNOWN / Chưa đối soát';
  const cur = String(currency || 'VND');
  return new Intl.NumberFormat('vi-VN').format(amount) + ' ' + cur;
}
function formatVnd(amount) {
  if (typeof amount !== 'number') return 'Chưa công bố';
  return new Intl.NumberFormat('vi-VN').format(amount) + ' VND';
}
function nodeStatusLabel(nodeState) {
  return JOURNEY_NODE_STATUS[nodeState] || JOURNEY_NODE_STATUS.UNKNOWN;
}

/* ---------------------------------------------------------------- geometry */

function getNodePos(id, idx) {
  const table = state.mobile ? NODE_POS_MOBILE : NODE_POS_DESKTOP;
  if (table[id]) return table[id];
  const fallback = state.mobile
    ? { x: mobileCol(idx % 3), y: MOBILE_ROW_Y[Math.min(2, Math.floor(idx / 3))] }
    : { x: DESKTOP_X0 + idx * DESKTOP_PITCH, y: 205 };
  return fallback;
}
function getJourneyViewportMetrics() {
  const vp = q('journey-map-viewport');
  const width = Number(vp && vp.clientWidth) || Number(window.innerWidth || 0);
  const height = Number(vp && vp.clientHeight) || Number(window.innerHeight || 0);
  return { width, height };
}
function applyJourneyLayoutMode(forceMobile) {
  const metrics = getJourneyViewportMetrics();
  state.mobile = typeof forceMobile === 'boolean'
    ? forceMobile
    : (metrics.width > 0 && metrics.width <= JOURNEY_MOBILE_BREAKPOINT);
  state.nodeW = state.mobile ? MOBILE_NODE_W : JOURNEY_NODE_W;
  state.nodeH = state.mobile ? MOBILE_NODE_H : JOURNEY_NODE_H;
  return state.mobile;
}
function journeyEdgePath(a, b) {
  const hw = state.nodeW;
  const hh = state.nodeH;
  if (b.x < a.x - 0.5) {
    const x1 = a.x, y1 = a.y + hh / 2, x2 = b.x + hw, y2 = b.y + hh / 2;
    const dx = Math.max(28, Math.abs(x1 - x2) * 0.42);
    return `M ${x1} ${y1} C ${x1 - dx} ${y1}, ${x2 + dx} ${y2}, ${x2} ${y2}`;
  }
  if (Math.abs(b.x - a.x) <= 0.5 && b.y > a.y) {
    const x = a.x + hw / 2, y1 = a.y + hh, y2 = b.y;
    const dy = Math.max(20, Math.abs(y2 - y1) * 0.45);
    return `M ${x} ${y1} C ${x} ${y1 + dy}, ${x} ${y2 - dy}, ${x} ${y2}`;
  }
  const x1 = a.x + hw, y1 = a.y + hh / 2, x2 = b.x, y2 = b.y + hh / 2;
  const dx = Math.max(40, Math.abs(x2 - x1) * 0.42);
  return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
}
function getRealRect(el, vpW, vpH) {
  if (!el || typeof el.getBoundingClientRect !== 'function') return null;
  const r = el.getBoundingClientRect();
  if (!r || !(r.width > 0) || !(r.height > 0)) return null;
  if (r.width >= vpW && r.height >= vpH) return null;
  return {
    left: r.left,
    top: r.top,
    right: typeof r.right === 'number' ? r.right : r.left + r.width,
    bottom: typeof r.bottom === 'number' ? r.bottom : r.top + r.height,
    width: r.width,
    height: r.height,
  };
}

/* ------------------------------------------------------------ map painters */

function applyTransform() {
  const tf = q('journey-map-transform');
  if (tf && tf.style) {
    tf.style.transform = `translate(${state.currentPan.x}px, ${state.currentPan.y}px) scale(${state.currentScale})`;
  }
  const pct = `${Math.round(state.currentScale * 100)}%`;
  const zl = q('journey-zoom-level');
  if (zl) zl.textContent = pct;
  const zp = q('journey-zoom-pct');
  if (zp) zp.textContent = pct;
  repositionOpenBubble();
}
function zoomIn() {
  state.currentScale = Math.min(1.85, Math.round((state.currentScale + 0.15) * 100) / 100);
  applyTransform();
}
function zoomOut() {
  state.currentScale = Math.max(0.55, Math.round((state.currentScale - 0.15) * 100) / 100);
  applyTransform();
}
function resetReadable() {
  applyJourneyLayoutMode();
  state.currentScale = 1;
  state.currentPan = { x: 0, y: 0 };
  applyTransform();
}
function fitJourney() {
  const vp = q('journey-map-viewport');
  const nodes = (state.lot && state.lot.journey && state.lot.journey.nodes) || [];
  if (!vp || nodes.length === 0) { resetReadable(); return; }
  applyJourneyLayoutMode();
  const positions = nodes.map((n, i) => getNodePos(n.id, i));
  const minX = Math.min(...positions.map((p) => p.x));
  const maxX = Math.max(...positions.map((p) => p.x + state.nodeW));
  const minY = Math.min(...positions.map((p) => p.y));
  const maxY = Math.max(...positions.map((p) => p.y + state.nodeH));
  const pad = state.mobile ? 8 : 48;
  const minBoxW = state.mobile ? 120 : 240;
  const minBoxH = state.mobile ? 120 : 180;
  const boxW = Math.max(minBoxW, maxX - minX + pad * 2);
  const boxH = Math.max(minBoxH, maxY - minY + pad * 2);
  const vw = vp.clientWidth || 960;
  const vh = vp.clientHeight || 520;
  const minScale = state.mobile ? 0.5 : 0.65;
  const nextScale = Math.max(minScale, Math.min(1.25, Math.min(vw / boxW, vh / boxH)));
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  state.currentScale = Math.round(nextScale * 100) / 100;
  state.currentPan = {
    x: Math.round(vw / 2 - cx * state.currentScale),
    y: Math.round(vh / 2 - cy * state.currentScale),
  };
  applyTransform();
}

/* --------------------------------------------------------- bubble placement */

// Journey discussion is a readable dock inside the SAME map, not a tiny
// tooltip squeezed into whichever gap happens to exist above a node.
// Dock opposite the selected node on desktop; mobile uses a contained sheet.
function positionBubbleElement(wrap, pos) {
  if (!wrap || !pos) return;
  const vp = q('journey-map-viewport');
  const vpW = (vp && vp.clientWidth) ? vp.clientWidth : (state.mobile ? 356 : 960);
  const vpH = (vp && vp.clientHeight) ? vp.clientHeight : (state.mobile ? 560 : 540);
  const pad = state.mobile ? 8 : 12;
  const bubbleW = Math.min(540, Math.max(0, vpW - pad * 2));
  const bubbleH = Math.min(state.mobile ? 520 : 540, Math.max(0, vpH - pad * 2));
  const nodeCenterX = state.currentPan.x + (pos.x + state.nodeW / 2) * state.currentScale;
  const dockLeft = !state.mobile && nodeCenterX >= vpW / 2;
  wrap.style.width = `${bubbleW}px`;
  wrap.style.height = `${bubbleH}px`;
  wrap.style.maxHeight = `${bubbleH}px`;
  wrap.style.left = `${dockLeft ? pad : Math.max(pad, vpW - pad - bubbleW)}px`;
  wrap.style.top = `${pad}px`;
  wrap.style.right = '';
  wrap.style.bottom = '';
  wrap.classList.remove('journey-bubble-above');
  wrap.classList.add('journey-bubble-below');
}
function repositionOpenBubble() {
  const slot = q('journey-bubble-slot');
  const wrap = slot && slot.firstChild;
  if (wrap && state.activeBubblePos) positionBubbleElement(wrap, state.activeBubblePos);
}

/* -------------------------------------------------------------- dashboard */

function buildDebtLinesDom(debtSummary) {
  const wrap = document.createElement('div');
  wrap.style.fontSize = '11.5px';
  wrap.style.lineHeight = '1.38';
  const debt = debtSummary || {};
  const confirmed = debt.status === 'CONFIRMED' && typeof debt.total_payable === 'number';
  const cur = String(debt.currency || 'VND');
  const l1 = document.createElement('div');
  l1.textContent = confirmed ? `Tổng phải thanh toán: ${formatMoney(debt.total_payable, cur)}` : 'Tổng phải thanh toán: UNKNOWN / Chưa đối soát';
  const l2 = document.createElement('div');
  l2.style.color = confirmed ? '#15803d' : '#64748b';
  l2.textContent = confirmed ? `Đã thanh toán: ${formatMoney(debt.total_paid, cur)}` : 'Đã thanh toán: UNKNOWN / Chưa đối soát';
  const l3 = document.createElement('div');
  l3.style.fontWeight = '700';
  l3.style.color = confirmed ? (debt.remaining_balance > 0 ? '#b45309' : '#0f766e') : '#64748b';
  l3.textContent = confirmed ? `Còn phải thanh toán: ${formatMoney(debt.remaining_balance, cur)}` : 'Còn phải thanh toán: UNKNOWN / Chưa đối soát';
  wrap.appendChild(l1);
  wrap.appendChild(l2);
  wrap.appendChild(l3);
  return wrap;
}
function secondaryLine(parts) {
  const text = parts.filter((p) => String(p || '').trim()).join(' · ');
  return text || '';
}

function renderDashboard(model) {
  // Issue #236 — remember the open lot + node so a data refresh (for example
  // after sending a comment) does NOT throw the customer back to the dashboard
  // or lose the node they were reading. Restore happens at the end of this
  // function and only when that lot is still in the freshly delivered payload.
  const keepLotId = state.lot ? String(state.lot.shipment_id || '') : '';
  const keepNodeId = state.selectedNodeId ? String(state.selectedNodeId) : '';
  // A Streamlit rerun can reuse this shadow root for a different principal or
  // a revoked publication. Remove the previous lot, not just the table rows:
  // an open modal, bubble, toolbar and JS state otherwise survive the rerun.
  state.lot = null;
  state.selectedNodeId = null;
  state.lastModalNodeId = null;
  state.activeBubblePos = null;
  applyDiscussionModel(model);
  closeStageModal(true);
  toggleUtilityBubble(false);
  ['journey-bubble-slot', 'journey-modal-body', 'modal-kicker', 'modal-title',
    'modal-sub', 'modal-badge'].forEach((id) => clearChildren(q(id)));
  ['utility-doc-count', 'utility-docs-sub'].forEach((id) => {
    const el = q(id); if (el) el.textContent = '0 tệp';
  });
  const quoteSub = q('utility-quote-sub');
  if (quoteSub) quoteSub.textContent = 'Chưa công bố';
  showUnpublishedState();
  const tbody = q('dash-shipments-tbody');
  const cardsBox = q('dash-shipments-cards');
  const selectorBox = q('customer-shipment-selector');
  const journeyView = q('shipment-journey-view');
  const backBtn = q('btn-back-to-dashboard');
  if (tbody) clearChildren(tbody);
  if (cardsBox) clearChildren(cardsBox);

  const lots = Array.isArray(model.lots) ? model.lots : [];
  const heading = q('dashboard-heading');
  if (heading) heading.textContent = `Dashboard tổng quan — ${lots.length} lô đã công bố (chọn một lô để mở hải đồ Journey Map 00–06):`;
  const note = q('dashboard-note');
  if (note) {
    note.textContent = 'Nhấn vào hàng/thẻ lô để mở Journey Map. Cột Công nợ chỉ hiển thị số liệu đã đối soát; '
      + 'UNKNOWN / Chưa đối soát nghĩa là Trường Thành chưa duyệt công bố tài chính cho lô đó. '
      + '“Chưa xác minh” nghĩa là chưa có chứng cứ công đoạn nào được duyệt công bố.';
  }

  lots.forEach((row) => {
    const sid = String(row.shipment_id || '');
    const modeText = String(row.transport_mode || 'Chưa xác định');
    const cargoText = String(row.cargo_summary || 'Chưa công bố');
    const routeText = String(row.route_summary || 'Chưa công bố');
    const stageLabel = String(row.verified_stage_label || 'Chưa xác minh');
    const stageTitle = String(row.verified_stage_title || '');
    const etaLabel = String(row.verified_warehouse_eta_label || 'Chưa xác minh');
    const updatedLabel = String(row.last_updated_label || 'Chưa có cập nhật được duyệt');
    const nextStepText = String(row.next_step || '');
    const contactText = String(row.contact_point || '');

    const tr = document.createElement('tr');
    tr.dataset.testid = `shipment-row-${sid}`;
    tr.addEventListener('click', () => selectShipmentForJourney(sid));
    const tdId = document.createElement('td');
    const strongId = document.createElement('strong');
    strongId.textContent = sid;
    tdId.appendChild(strongId);
    const tdCargo = document.createElement('td');
    const divCargo = document.createElement('div');
    divCargo.style.fontWeight = '700';
    divCargo.textContent = cargoText;
    const divRoute = document.createElement('div');
    divRoute.style.fontSize = '11.5px';
    divRoute.style.color = '#64748b';
    divRoute.textContent = routeText;
    tdCargo.appendChild(divCargo);
    tdCargo.appendChild(divRoute);
    const tdMode = document.createElement('td');
    const spanMode = document.createElement('span');
    spanMode.className = 'journey-toolbar-chip';
    spanMode.textContent = modeText;
    tdMode.appendChild(spanMode);
    const tdStage = document.createElement('td');
    const spanStage = document.createElement('span');
    spanStage.style.fontWeight = '700';
    spanStage.textContent = stageLabel;
    const divStageTitle = document.createElement('div');
    divStageTitle.style.fontSize = '11.5px';
    divStageTitle.style.color = '#475569';
    divStageTitle.textContent = stageTitle;
    tdStage.appendChild(spanStage);
    tdStage.appendChild(divStageTitle);
    const tdEta = document.createElement('td');
    tdEta.textContent = etaLabel;
    const tdDebt = document.createElement('td');
    tdDebt.dataset.testid = `shipment-debt-${sid}`;
    tdDebt.appendChild(buildDebtLinesDom(row.debt_summary));
    const tdUpdated = document.createElement('td');
    const divUpdated = document.createElement('div');
    divUpdated.textContent = updatedLabel;
    const divNext = document.createElement('div');
    divNext.style.fontSize = '11px';
    divNext.style.color = '#64748b';
    divNext.textContent = secondaryLine([nextStepText, contactText ? `Đầu mối: ${contactText}` : '']);
    tdUpdated.appendChild(divUpdated);
    if (divNext.textContent) tdUpdated.appendChild(divNext);
    const tdBtn = document.createElement('td');
    const btnOpen = document.createElement('button');
    btnOpen.type = 'button';
    btnOpen.className = 'journey-toolbar-btn';
    btnOpen.dataset.testid = `btn-open-journey-${sid}`;
    btnOpen.textContent = 'Xem hành trình';
    btnOpen.addEventListener('click', (ev) => {
      if (ev && ev.stopPropagation) ev.stopPropagation();
      selectShipmentForJourney(sid);
    });
    tdBtn.appendChild(btnOpen);
    tr.appendChild(tdId);
    tr.appendChild(tdCargo);
    tr.appendChild(tdMode);
    tr.appendChild(tdStage);
    tr.appendChild(tdEta);
    tr.appendChild(tdDebt);
    tr.appendChild(tdUpdated);
    tr.appendChild(tdBtn);
    if (tbody) tbody.appendChild(tr);

    const card = document.createElement('article');
    card.className = 'shipment-card-mobile';
    card.dataset.testid = `shipment-card-${sid}`;
    card.addEventListener('click', () => selectShipmentForJourney(sid));
    const cardTop = document.createElement('div');
    cardTop.className = 'shipment-card-top';
    const cardId = document.createElement('strong');
    cardId.style.fontFamily = 'var(--mono)';
    cardId.style.fontSize = '13.5px';
    cardId.textContent = sid;
    const cardBadges = document.createElement('div');
    cardBadges.style.display = 'flex';
    cardBadges.style.gap = '6px';
    const badgeMode = document.createElement('span');
    badgeMode.className = 'journey-toolbar-chip';
    badgeMode.textContent = modeText;
    const badgeStage = document.createElement('span');
    badgeStage.className = 'journey-toolbar-chip journey-toolbar-here';
    badgeStage.textContent = stageLabel;
    cardBadges.appendChild(badgeMode);
    cardBadges.appendChild(badgeStage);
    cardTop.appendChild(cardId);
    cardTop.appendChild(cardBadges);
    const cardCargo = document.createElement('div');
    cardCargo.style.fontSize = '12.5px';
    cardCargo.style.fontWeight = '700';
    cardCargo.textContent = cargoText;
    const cardRoute = document.createElement('div');
    cardRoute.style.fontSize = '11.5px';
    cardRoute.style.color = '#475569';
    cardRoute.textContent = routeText;
    const cardMeta = document.createElement('div');
    cardMeta.className = 'shipment-card-meta';
    const metaEta = document.createElement('div');
    metaEta.textContent = `ETA xác minh: ${etaLabel}`;
    const metaUpdated = document.createElement('div');
    metaUpdated.textContent = `Cập nhật: ${updatedLabel}`;
    cardMeta.appendChild(metaEta);
    cardMeta.appendChild(metaUpdated);
    const cardDebt = document.createElement('div');
    cardDebt.style.background = '#f8fafc';
    cardDebt.style.padding = '7px 9px';
    cardDebt.style.borderRadius = '6px';
    cardDebt.style.border = '1px solid #e2e8f0';
    cardDebt.appendChild(buildDebtLinesDom(row.debt_summary));
    const cardBtn = document.createElement('button');
    cardBtn.type = 'button';
    cardBtn.className = 'btn-primary';
    cardBtn.style.width = '100%';
    cardBtn.textContent = 'Xem hành trình →';
    cardBtn.addEventListener('click', (ev) => {
      if (ev && ev.stopPropagation) ev.stopPropagation();
      selectShipmentForJourney(sid);
    });
    card.appendChild(cardTop);
    card.appendChild(cardCargo);
    card.appendChild(cardRoute);
    card.appendChild(cardMeta);
    card.appendChild(cardDebt);
    card.appendChild(cardBtn);
    if (cardsBox) cardsBox.appendChild(card);
  });

  if (lots.length === 0) {
    if (selectorBox) selectorBox.classList.add('hidden');
    if (backBtn) backBtn.classList.add('hidden');
    if (journeyView) journeyView.classList.remove('hidden');
    showUnpublishedState();
    return;
  }
  // Issue #236 — a refresh (comment sent, attachment read, unrelated rerun)
  // keeps the SAME lot and node open, without re-emitting the intent when the
  // thread is already delivered/pending (so no rerun loop) and without
  // resetting the customer's pan/zoom.
  const canRestore = Boolean(keepLotId) && state.journeyOpen
    && lots.some((row) => String(row.shipment_id || '') === keepLotId);
  if (canRestore) {
    selectShipmentForJourney(keepLotId, { fit: false });
    if (keepNodeId) {
      const row = lots.find((r) => String(r.shipment_id || '') === keepLotId);
      const nodes = (row && row.journey && Array.isArray(row.journey.nodes)) ? row.journey.nodes : [];
      if (nodes.some((n) => String(n.id) === keepNodeId)) selectJourneyNode(keepNodeId);
    }
    return;
  }
  if (lots.length === 1) {
    if (selectorBox) selectorBox.classList.add('hidden');
    if (backBtn) backBtn.classList.add('hidden');
    if (journeyView) journeyView.classList.remove('hidden');
    selectShipmentForJourney(String(lots[0].shipment_id || ''));
    return;
  }
  if (selectorBox) selectorBox.classList.remove('hidden');
  if (journeyView) journeyView.classList.add('hidden');
  if (backBtn) backBtn.classList.remove('hidden');
}

function showUnpublishedState() {
  const zeroEl = q('journey-zero-notice');
  if (zeroEl) zeroEl.classList.remove('hidden');
  const nodesLayer = q('journey-nodes-layer');
  if (nodesLayer) clearChildren(nodesLayer);
  const edgesSvg = q('journey-edges-svg');
  if (edgesSvg) clearChildren(edgesSvg);
  const toolbarIds = ['toolbar-id', 'toolbar-mode', 'toolbar-customer', 'toolbar-route', 'toolbar-here', 'toolbar-eta', 'toolbar-next'];
  toolbarIds.forEach((id) => { const el = q(id); if (el) el.textContent = '—'; });
}

function backToDashboard() {
  closeStageModal(true);
  state.journeyOpen = false;
  const selectorBox = q('customer-shipment-selector');
  const journeyView = q('shipment-journey-view');
  if (journeyView) journeyView.classList.add('hidden');
  if (selectorBox) selectorBox.classList.remove('hidden');
  state.selectedNodeId = null;
  state.activeBubblePos = null;
}
function selectShipmentForJourney(shipmentId, options) {
  const opts = options || {};
  const sid = String(shipmentId || '').trim();
  if (!sid) return;
  const lots = (state.model && state.model.lots) || [];
  const matched = lots.find((r) => String(r.shipment_id) === sid) || null;
  if (!matched) return;
  state.journeyOpen = true;
  const selectorBox = q('customer-shipment-selector');
  const journeyView = q('shipment-journey-view');
  const backBtn = q('btn-back-to-dashboard');
  if (selectorBox) selectorBox.classList.add('hidden');
  if (journeyView) journeyView.classList.remove('hidden');
  if (backBtn) {
    if (lots.length >= 2) backBtn.classList.remove('hidden');
    else backBtn.classList.add('hidden');
  }
  state.lot = matched;
  state.selectedNodeId = null;
  state.activeBubblePos = null;
  renderJourneyMapForShipment(matched);
  // A data refresh keeps the customer's own pan/zoom; only a real lot switch
  // re-fits the map.
  if (opts.fit === false) applyTransform(); else fitJourney();
}

/* ---------------------------------------------------------------- journey */

function renderJourneyMapForShipment(row) {
  const zeroEl = q('journey-zero-notice');
  if (zeroEl) zeroEl.classList.add('hidden');
  applyJourneyLayoutMode();
  const setText = (id, text) => { const el = q(id); if (el) el.textContent = text; };
  setText('toolbar-id', String(row.shipment_id || ''));
  setText('toolbar-mode', String(row.transport_mode || 'Chưa xác định'));
  setText('toolbar-customer', String((state.model && state.model.customer && state.model.customer.name) || ''));
  const cargoRoute = row.has_cargo_route
    ? secondaryLine([row.route_summary, row.cargo_summary])
    : '';
  const routeEl = q('toolbar-route');
  if (routeEl) {
    routeEl.textContent = cargoRoute;
    routeEl.style.display = cargoRoute ? '' : 'none';
  }
  setText('toolbar-here', `Đang ở: ${String(row.verified_stage_label || 'Chưa xác minh')}`);
  setText('toolbar-eta', `ETA kho: ${String(row.verified_warehouse_eta_label || 'Chưa xác minh')}`);
  setText('toolbar-next', secondaryLine([row.next_step, row.contact_point ? `Đầu mối: ${row.contact_point}` : '']));

  const docs = Array.isArray(row.documents) ? row.documents : [];
  const quoteDocs = docs.filter((doc) => doc && doc.kind === 'CUSTOMER_QUOTE');
  setText('utility-doc-count', `${docs.length} tệp`);
  setText('utility-docs-sub', `${docs.length} tệp`);
  setText('utility-quote-sub', quoteDocs.length ? `${quoteDocs.length} tài liệu` : 'Chưa công bố');

  const journey = row.journey || { nodes: [], edges: [] };
  const nodes = Array.isArray(journey.nodes) ? journey.nodes : [];
  const edges = (Array.isArray(journey.edges) && journey.edges.length > 0)
    ? journey.edges
    : nodes.slice(0, -1).map((n, idx) => ({ from: n.id, to: nodes[idx + 1].id }));
  const posById = {};
  const nodeById = {};
  nodes.forEach((n, idx) => {
    posById[n.id] = getNodePos(n.id, idx);
    nodeById[n.id] = n;
  });

  const edgesSvg = q('journey-edges-svg');
  if (edgesSvg) {
    clearChildren(edgesSvg);
    edges.forEach((e) => {
      const a = posById[e.from];
      const b = posById[e.to];
      if (!a || !b) return;
      const fromNode = nodeById[e.from] || {};
      const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      pathEl.setAttribute('class', ['journey-edge', fromNode.completed ? 'journey-edge-done' : ''].filter(Boolean).join(' '));
      pathEl.setAttribute('d', journeyEdgePath(a, b));
      pathEl.style.stroke = fromNode.completed ? '#1a4b75' : '#94a3b8';
      pathEl.style.strokeWidth = '2';
      pathEl.style.fill = 'none';
      pathEl.style.opacity = '0.9';
      edgesSvg.appendChild(pathEl);
    });
  }

  const nodesLayer = q('journey-nodes-layer');
  if (nodesLayer) {
    clearChildren(nodesLayer);
    nodes.forEach((n, idx) => {
      const p = posById[n.id];
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.dataset.testid = `journey-node-${n.id}`;
      btn.setAttribute('data-state', String(n.state || 'UNKNOWN'));
      const classes = ['journey-node'];
      if (n.current) classes.push('journey-node-here');
      if (state.selectedNodeId === n.id) classes.push('journey-node-selected');
      btn.className = classes.join(' ');
      btn.style.left = `${p.x}px`;
      btn.style.top = `${p.y}px`;
      btn.style.width = `${state.nodeW}px`;
      btn.style.height = `${state.nodeH}px`;
      btn.style.setProperty('--stripe', STATE_STRIPE[n.state] || STATE_STRIPE.UNKNOWN);
      btn.style.borderLeft = '4px solid var(--stripe)';

      const topDiv = document.createElement('div');
      topDiv.className = 'journey-node-top';
      const idxSpan = document.createElement('span');
      idxSpan.className = 'journey-node-idx';
      idxSpan.textContent = String(n.index !== undefined ? n.index : idx).padStart(2, '0');
      topDiv.appendChild(idxSpan);
      const titleDiv = document.createElement('div');
      titleDiv.className = 'journey-node-title';
      titleDiv.textContent = String(n.label || '').toUpperCase();
      const footDiv = document.createElement('div');
      footDiv.className = 'journey-node-foot';
      const stSpan = document.createElement('span');
      stSpan.className = 'journey-node-status';
      stSpan.textContent = nodeStatusLabel(n.state);
      footDiv.appendChild(stSpan);

      const stageDocs = Array.isArray(n.stage_documents) ? n.stage_documents : [];
      const stageCmts = Array.isArray(n.stage_comments) ? n.stage_comments : [];
      if (stageDocs.length > 0 || stageCmts.length > 0) {
        const cntSpan = document.createElement('span');
        cntSpan.className = 'journey-node-count';
        cntSpan.style.marginLeft = 'auto';
        cntSpan.textContent = `▤${stageDocs.length} · ${stageCmts.length} BL`;
        topDiv.appendChild(cntSpan);
      }
      btn.appendChild(topDiv);
      btn.appendChild(titleDiv);
      btn.appendChild(footDiv);
      btn.addEventListener('click', () => selectJourneyNode(String(n.id)));
      nodesLayer.appendChild(btn);
    });
  }

  if (state.selectedNodeId && nodeById[state.selectedNodeId]) {
    renderNodeBubble(nodeById[state.selectedNodeId], posById[state.selectedNodeId], docs);
  } else {
    state.activeBubblePos = null;
    const bubbleSlot = q('journey-bubble-slot');
    if (bubbleSlot) clearChildren(bubbleSlot);
  }
}

function selectJourneyNode(nodeId, options) {
  if (!state.lot || !state.lot.journey) return;
  const opts = options || {};
  const utilDrop = q('journey-utility-bubble');
  if (utilDrop) utilDrop.classList.add('hidden');
  state.selectedNodeId = String(nodeId);
  if (opts.load !== false) requestDiscussion(String(nodeId));
  renderJourneyMapForShipment(state.lot);
}

// ---------------------------------------------------------------------------
// Issue #236 — inline node conversation
//
// Clicking a node asks Python for THAT lot + stage thread (`journey_focus`,
// unchanged contract). The thread arrives in `model.discussion` and is rendered
// INSIDE the node bubble: comments, one level of replies, the composer and its
// attachments. Nothing here decides tenancy, visibility or permission.
// ---------------------------------------------------------------------------

function discussionKey(lotId, nodeId) {
  return `${String(lotId || '')}|${String(nodeId || '')}`;
}

function requestDiscussion(nodeId) {
  if (!state.transport || !state.lot) return false;
  const lot = String(state.lot.shipment_id || '');
  const stage = String(nodeId || '');
  if (!lot || !stage) return false;
  const key = discussionKey(lot, stage);
  if (state.discussionPendingKey === key) return true;
  const disc = state.discussion;
  if (disc && String(disc.shipmentId) === lot
    && (String(disc.stageId) === stage || String(disc.nodeId) === stage)) {
    return true;
  }
  state.discussionPendingKey = key;
  state.triggerSeq += 1;
  state.transport(FOCUS_EVENT, {
    seq: state.triggerSeq,
    event: FOCUS_EVENT,
    payload: { shipment_id: lot, stage_id: stage },
  });
  return true;
}

function discussionFor(node) {
  const disc = state.discussion;
  if (!disc || !state.lot || !node) return null;
  if (String(disc.shipmentId) !== String(state.lot.shipment_id)) return null;
  if (String(disc.stageId) !== String(node.id) && String(disc.nodeId) !== String(node.id)) return null;
  return disc;
}

function ensureDraft(key) {
  if (!state.drafts[key]) {
    state.drafts[key] = { text: '', replyTo: '', replyName: '', file: null, notice: '', fileNotice: '' };
  }
  return state.drafts[key];
}

function formatStamp(value) {
  const text = String(value || '').replace('T', ' ');
  return text ? text.slice(0, 19) : '—';
}

function downloadBase64(name, base64, mime) {
  try {
    const binary = atob(String(base64 || ''));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    const blob = new Blob([bytes], { type: mime || 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = String(name || 'chung-tu');
    anchor.rel = 'noopener';
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    return true;
  } catch (_) {
    return false;
  }
}

// Fold the delivered slice into local state. The server is authoritative: the
// draft is cleared only for the requestId the backend actually answered, and a
// file is saved only from the server's one-shot download channel.
function applyDiscussionModel(model) {
  const disc = model && model.discussion;
  if (!disc || !disc.shipmentId || !disc.stageId) {
    state.discussion = null;
    return;
  }
  state.discussion = disc;
  const key = discussionKey(disc.shipmentId, disc.stageId);
  if (state.discussionPendingKey === key) state.discussionPendingKey = '';
  const draft = state.drafts[key];
  const outcome = disc.outcome;
  if (outcome && outcome.requestId && outcome.requestId === state.sendingRequestId) {
    state.sendingRequestId = '';
    if (state.sendTimer) { clearTimeout(state.sendTimer); state.sendTimer = null; }
    if (draft) {
      draft.notice = outcome.ok
        ? (outcome.duplicate ? 'Bình luận này đã được ghi trước đó.' : '')
        : String(outcome.error || 'Không gửi được bình luận.');
      if (outcome.ok) {
        draft.text = '';
        draft.file = null;
        draft.replyTo = '';
        draft.replyName = '';
        draft.fileNotice = '';
      }
    }
  }
  const downloadOutcome = disc.downloadOutcome;
  if (downloadOutcome && downloadOutcome.requestId === state.downloadPendingId) {
    state.downloadPendingId = '';
    if (!downloadOutcome.ok && draft) draft.notice = String(downloadOutcome.error || 'Không tải được chứng từ.');
  }
  const dl = disc.download;
  if (dl && dl.base64) {
    const dkey = `${dl.noteId}:${dl.attachmentId}:${dl.seq}`;
    if (dkey !== state.handledDownloadKey) {
      state.handledDownloadKey = dkey;
      const saved = downloadBase64(dl.name, dl.base64, dl.mime);
      if (draft) draft.notice = saved ? '' : 'Trình duyệt không mở được tệp vừa tải.';
      state.downloadPendingId = '';
    }
  }
}


/* ------------------------------------------------- inline node discussion */

function buildAttachmentList(note, draft) {
  const rows = Array.isArray(note.attachments) ? note.attachments : [];
  if (!rows.length) return null;
  const list = document.createElement('ul');
  list.className = 'journey-discussion-files';
  rows.forEach((item) => {
    const li = document.createElement('li');
    const icon = document.createElement('span');
    icon.className = 'journey-discussion-file-icon';
    icon.textContent = '📎';
    const nameSpan = document.createElement('span');
    nameSpan.className = 'journey-discussion-file-name';
    nameSpan.textContent = String(item.name || 'Chứng từ');
    const sizeSpan = document.createElement('span');
    sizeSpan.className = 'journey-discussion-file-size';
    sizeSpan.textContent = String(item.sizeLabel || '');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'journey-discussion-file-download';
    btn.dataset.testid = `journey-discussion-download-${item.id}`;
    btn.textContent = 'Tải';
    btn.disabled = !state.transport || Boolean(state.downloadPendingId);
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      requestDownload(note.id, item.id);
    });
    li.appendChild(icon);
    li.appendChild(nameSpan);
    li.appendChild(sizeSpan);
    li.appendChild(btn);
    list.appendChild(li);
  });
  return list;
}

function buildNoteCard(note, draft, isReply) {
  const card = document.createElement('div');
  card.className = isReply ? 'journey-discussion-note is-reply' : 'journey-discussion-note';
  card.dataset.testid = `journey-discussion-note-${note.id}`;
  card.dataset.visibility = String(note.visibility || '');
  const head = document.createElement('div');
  head.className = 'journey-discussion-note-head';
  const author = document.createElement('span');
  author.className = 'journey-discussion-author';
  author.textContent = String(note.author_name || '—');
  const kind = document.createElement('span');
  kind.className = 'journey-discussion-kind';
  kind.textContent = String(note.author_kind === 'customer' ? 'Khách hàng' : 'Trường Thành');
  const when = document.createElement('span');
  when.className = 'journey-discussion-time';
  when.textContent = `· ${formatStamp(note.created_at)}`;
  head.appendChild(author);
  head.appendChild(kind);
  head.appendChild(when);
  card.appendChild(head);
  if (note.body) {
    const body = document.createElement('p');
    body.className = 'journey-discussion-body-text';
    body.textContent = String(note.body);
    card.appendChild(body);
  }
  const files = buildAttachmentList(note, draft);
  if (files) card.appendChild(files);
  if (!isReply) {
    const reply = document.createElement('button');
    reply.type = 'button';
    reply.className = 'journey-discussion-reply';
    reply.dataset.testid = `journey-discussion-reply-${note.id}`;
    reply.textContent = '↩ Trả lời';
    reply.addEventListener('click', (ev) => {
      ev.stopPropagation();
      draft.replyTo = String(note.id);
      draft.replyName = String(note.author_name || 'bình luận');
      draft.notice = '';
      renderJourneyMapForShipment(state.lot);
    });
    card.appendChild(reply);
  }
  return card;
}

function buildDiscussionThread(node) {
  const wrap = document.createElement('div');
  wrap.className = 'journey-discussion';
  wrap.dataset.testid = 'journey-discussion';
  wrap.dataset.node = String(node.id);
  const head = document.createElement('div');
  head.className = 'journey-discussion-head';
  head.textContent = '💬 Trao đổi';
  wrap.appendChild(head);
  const disc = discussionFor(node);
  const key = discussionKey(state.lot && state.lot.shipment_id, node.id);
  const draft = ensureDraft(key);
  if (!disc) {
    const stateBox = document.createElement('div');
    stateBox.className = 'journey-discussion-empty';
    if (state.discussionPendingKey === key) {
      stateBox.dataset.testid = 'journey-discussion-loading';
      stateBox.textContent = 'Đang tải trao đổi…';
      wrap.appendChild(stateBox);
    } else {
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'journey-discussion-retry';
      retry.dataset.testid = 'journey-discussion-retry';
      retry.textContent = state.transport ? 'Tải trao đổi của công đoạn này' : 'Trao đổi chưa kết nối';
      retry.disabled = !state.transport;
      retry.addEventListener('click', (ev) => {
        ev.stopPropagation();
        if (requestDiscussion(String(node.id))) renderJourneyMapForShipment(state.lot);
      });
      wrap.appendChild(retry);
    }
    return wrap;
  }
  head.textContent = `💬 Trao đổi (${Number(disc.count) || 0})`;
  if (disc.error) {
    const err = document.createElement('div');
    err.className = 'journey-discussion-error';
    err.setAttribute('role', 'alert');
    err.textContent = String(disc.error);
    wrap.appendChild(err);
  }
  const notes = Array.isArray(disc.notes) ? disc.notes : [];
  if (!notes.length && !disc.error) {
    const empty = document.createElement('div');
    empty.className = 'journey-discussion-empty';
    empty.dataset.testid = 'journey-discussion-empty';
    empty.textContent = 'Chưa có trao đổi nào ở công đoạn này.';
    wrap.appendChild(empty);
  }
  const list = document.createElement('div');
  list.className = 'journey-discussion-list';
  list.dataset.testid = 'journey-discussion-list';
  notes.forEach((note) => {
    const item = document.createElement('div');
    item.className = 'journey-discussion-thread';
    item.appendChild(buildNoteCard(note, draft, false));
    const replies = Array.isArray(note.replies) ? note.replies : [];
    if (replies.length) {
      const replyList = document.createElement('div');
      replyList.className = 'journey-discussion-replies';
      replies.forEach((reply) => replyList.appendChild(buildNoteCard(reply, draft, true)));
      item.appendChild(replyList);
    }
    list.appendChild(item);
  });
  wrap.appendChild(list);
  return wrap;
}

function readPickedFile(file, key) {
  const draft = ensureDraft(key);
  const limit = Number((state.discussion && state.discussion.maxBytes) || 20 * 1024 * 1024);
  draft.fileNotice = '';
  if (!file) { draft.file = null; return; }
  if (file.size > limit) {
    draft.file = null;
    draft.fileNotice = `Tệp vượt giới hạn ${Math.floor(limit / (1024 * 1024))} MB.`;
    renderJourneyMapForShipment(state.lot);
    return;
  }
  const apply = (encoded) => {
    if (!encoded) {
      draft.fileNotice = 'Không đọc được tệp đã chọn.';
    } else {
      draft.file = { name: file.name, mime: file.type || '', size: file.size, base64: encoded };
      draft.fileNotice = `Đã chọn: ${file.name}`;
    }
    if (state.lot) renderJourneyMapForShipment(state.lot);
  };
  if (typeof FileReader === 'undefined') {
    draft.fileNotice = 'Trình duyệt không đọc được tệp.';
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    const raw = String(reader.result || '');
    apply(raw.includes(',') ? raw.split(',')[1] : '');
  };
  reader.onerror = () => apply('');
  reader.readAsDataURL(file);
}

function sendDiscussion(node) {
  if (!state.transport || !state.lot || state.sendingRequestId) return;
  const lot = String(state.lot.shipment_id || '');
  const key = discussionKey(lot, node.id);
  const draft = ensureDraft(key);
  const text = String(draft.text || '').trim();
  if (!text && !draft.file) {
    draft.notice = 'Nhập nội dung hoặc đính kèm chứng từ.';
    renderJourneyMapForShipment(state.lot);
    return;
  }
  draft.notice = '';
  const requestId = `JRN-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
  state.sendingRequestId = requestId;
  state.triggerSeq += 1;
  const files = draft.file
    ? [{ name: draft.file.name, mime: draft.file.mime, size: draft.file.size, base64: draft.file.base64 }]
    : [];
  state.transport(NOTE_CREATE_EVENT, {
    seq: state.triggerSeq,
    event: NOTE_CREATE_EVENT,
    payload: {
      requestId,
      shipmentId: lot,
      nodeId: String(node.id),
      stageId: String(node.id),
      body: text,
      // The portal can only ever publish customer-visible content; the server
      // enforces it again regardless of this value.
      visibility: 'CUSTOMER',
      replyToId: String(draft.replyTo || ''),
      files,
    },
  });
  if (state.sendTimer) clearTimeout(state.sendTimer);
  state.sendTimer = setTimeout(() => {
    if (state.sendingRequestId !== requestId) return;
    state.sendingRequestId = '';
    const current = ensureDraft(key);
    current.notice = 'Chưa nhận được xác nhận từ máy chủ. Vui lòng thử lại.';
    if (state.lot) renderJourneyMapForShipment(state.lot);
  }, 20000);
  renderJourneyMapForShipment(state.lot);
}

function requestDownload(noteId, attachmentId) {
  if (!state.transport || !state.lot || state.downloadPendingId) return;
  const requestId = `JRN-DOWN-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
  state.downloadPendingId = requestId;
  state.triggerSeq += 1;
  state.transport(NOTE_DOWNLOAD_EVENT, {
    seq: state.triggerSeq,
    event: NOTE_DOWNLOAD_EVENT,
    payload: {
      requestId,
      shipmentId: String(state.lot.shipment_id || ''),
      nodeId: String(state.selectedNodeId || ''),
      stageId: String((state.discussion && state.discussion.stageId) || state.selectedNodeId || ''),
      noteId: String(noteId),
      attachmentId: String(attachmentId),
    },
  });
  if (state.lot) renderJourneyMapForShipment(state.lot);
}

function buildDiscussionComposer(node) {
  const wrap = document.createElement('div');
  wrap.className = 'journey-discussion-composer';
  wrap.dataset.testid = 'journey-discussion-composer';
  const disc = discussionFor(node);
  if (!disc) return wrap;
  const key = discussionKey(state.lot && state.lot.shipment_id, node.id);
  const draft = ensureDraft(key);
  if (!disc.canWrite) {
    const readOnly = document.createElement('div');
    readOnly.className = 'journey-discussion-empty';
    readOnly.textContent = 'Tài khoản này chỉ được xem trao đổi.';
    wrap.appendChild(readOnly);
    return wrap;
  }
  if (draft.replyTo) {
    const banner = document.createElement('div');
    banner.className = 'journey-discussion-reply-banner';
    banner.dataset.testid = 'journey-discussion-reply-banner';
    const text = document.createElement('span');
    text.textContent = `Đang trả lời ${draft.replyName || 'bình luận'}`;
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'journey-discussion-cancel';
    cancel.setAttribute('aria-label', 'Bỏ trả lời');
    cancel.textContent = '×';
    cancel.addEventListener('click', (ev) => {
      ev.stopPropagation();
      draft.replyTo = '';
      draft.replyName = '';
      renderJourneyMapForShipment(state.lot);
    });
    banner.appendChild(text);
    banner.appendChild(cancel);
    wrap.appendChild(banner);
  }
  const body = document.createElement('textarea');
  body.className = 'journey-discussion-input';
  body.dataset.testid = 'journey-discussion-body';
  body.rows = 2;
  body.maxLength = 4000;
  body.placeholder = draft.replyTo ? 'Viết phản hồi…' : 'Viết bình luận…';
  body.value = String(draft.text || '');
  body.addEventListener('input', () => { draft.text = body.value; });
  body.addEventListener('pointerdown', (ev) => ev.stopPropagation());
  body.addEventListener('keydown', (ev) => ev.stopPropagation());
  wrap.appendChild(body);
  const row = document.createElement('div');
  row.className = 'journey-discussion-actions';
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'image/*,application/pdf';
  fileInput.style.display = 'none';
  fileInput.dataset.testid = 'journey-discussion-file';
  fileInput.addEventListener('change', () => {
    readPickedFile(fileInput.files && fileInput.files[0], key);
  });
  const attach = document.createElement('button');
  attach.type = 'button';
  attach.className = 'journey-discussion-attach';
  attach.dataset.testid = 'journey-discussion-attach';
  attach.textContent = '📎 Đính kèm';
  attach.disabled = Boolean(state.sendingRequestId);
  attach.addEventListener('click', (ev) => {
    ev.stopPropagation();
    fileInput.click();
  });
  const send = document.createElement('button');
  send.type = 'button';
  send.className = 'journey-discussion-send';
  send.dataset.testid = 'journey-discussion-send';
  send.textContent = state.sendingRequestId ? 'Đang gửi…' : 'Gửi';
  send.disabled = Boolean(state.sendingRequestId);
  send.addEventListener('click', (ev) => {
    ev.stopPropagation();
    sendDiscussion(node);
  });
  row.appendChild(fileInput);
  row.appendChild(attach);
  if (draft.file) {
    const picked = document.createElement('span');
    picked.className = 'journey-discussion-picked';
    picked.textContent = String(draft.file.name || '');
    row.appendChild(picked);
  }
  row.appendChild(send);
  wrap.appendChild(row);
  const notice = String(draft.notice || draft.fileNotice || '');
  if (notice) {
    const note = document.createElement('div');
    note.className = 'journey-discussion-notice';
    note.dataset.testid = 'journey-discussion-notice';
    note.setAttribute('role', draft.notice ? 'alert' : 'status');
    note.textContent = notice;
    wrap.appendChild(note);
  }
  return wrap;
}

// ---------------------------------------------------------------------------
// Issue #244 — "Hồ sơ Kế hoạch đã công bố" inside node 00.
//
// The rows come ONLY from `lot.plan_documents`, which Python already filtered to
// CUSTOMER_QUOTE / CUSTOMER_CONTRACT / PAYMENT_REQUEST among documents that
// passed the publication allowlist (id + version + PUBLISHED). Nothing here
// decides visibility, and nothing here is downloadable: a published contract is
// metadata, not a signature, and a payment REQUEST is not a payment.
// ---------------------------------------------------------------------------

const PLAN_NODE_ID = 'plan';

function buildPlanPublishedBlock(node) {
  if (!node || String(node.id) !== PLAN_NODE_ID) return null;
  const rows = (state.lot && Array.isArray(state.lot.plan_documents))
    ? state.lot.plan_documents
    : [];
  const section = document.createElement('section');
  section.className = 'journey-bubble-task journey-plan-published';
  section.dataset.testid = 'journey-plan-published';
  section.style.cursor = 'default';
  const body = document.createElement('span');
  body.className = 'journey-bubble-task-body';
  const title = document.createElement('span');
  title.className = 'journey-bubble-title';
  title.textContent = 'Hồ sơ Kế hoạch đã công bố';
  body.appendChild(title);
  if (rows.length === 0) {
    const empty = document.createElement('span');
    empty.className = 'journey-bubble-meta';
    empty.dataset.testid = 'journey-plan-published-empty';
    empty.textContent = String(
      (state.lot && state.lot.plan_documents_empty_label)
      || 'Chưa có hồ sơ Kế hoạch được công bố'
    );
    body.appendChild(empty);
  } else {
    rows.forEach((row) => {
      const line = document.createElement('span');
      line.className = 'journey-bubble-meta';
      line.dataset.testid = `journey-plan-document-${String(row.kind || '')}`;
      const label = String(row.label || '');
      const docTitle = String(row.title || '');
      line.textContent = label && docTitle && docTitle !== label
        ? `${label}: ${docTitle}`
        : (label || docTitle || 'Hồ sơ Kế hoạch');
      body.appendChild(line);
    });
  }
  const note = document.createElement('span');
  note.className = 'journey-bubble-meta';
  note.textContent = 'Hồ sơ đã công bố không chứng minh đã ký hoặc đã thanh toán.';
  body.appendChild(note);
  section.appendChild(body);
  return section;
}

function renderNodeBubble(node, pos, docs) {
  const bubbleSlot = q('journey-bubble-slot');
  if (!bubbleSlot) return;
  clearChildren(bubbleSlot);
  if (!node || !pos) { state.activeBubblePos = null; return; }
  state.activeBubblePos = { x: pos.x, y: pos.y };
  const wrap = document.createElement('div');
  wrap.className = 'journey-bubble journey-bubble-below';
  wrap.dataset.testid = 'journey-bubble';
  wrap.setAttribute('data-node', String(node.id));
  wrap.style.left = '12px';
  wrap.style.top = '12px';
  wrap.style.width = `${state.mobile ? 250 : 290}px`;

  const head = document.createElement('div');
  head.className = 'journey-bubble-head';
  const headTextWrap = document.createElement('div');
  const kicker = document.createElement('span');
  kicker.className = 'journey-bubble-kicker';
  kicker.textContent = String(node.label || '').toUpperCase();
  const stateSpan = document.createElement('span');
  stateSpan.className = 'journey-bubble-state';
  stateSpan.textContent = nodeStatusLabel(node.state);
  headTextWrap.appendChild(kicker);
  headTextWrap.appendChild(document.createElement('br'));
  headTextWrap.appendChild(stateSpan);
  const closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.className = 'journey-bubble-close';
  closeBtn.dataset.testid = 'journey-bubble-close';
  closeBtn.textContent = '×';
  closeBtn.setAttribute('aria-label', 'Đóng bubble');
  closeBtn.style.fontSize = '17px';
  closeBtn.style.lineHeight = '1';
  closeBtn.addEventListener('click', () => closeJourneyBubble());
  head.appendChild(headTextWrap);
  head.appendChild(closeBtn);

  const listDiv = document.createElement('div');
  listDiv.className = 'journey-bubble-list';
  const taskStage = document.createElement('button');
  taskStage.type = 'button';
  taskStage.className = `journey-bubble-task ${node.completed ? 'is-done' : ''}`;
  taskStage.dataset.testid = 'journey-bubble-task-stage';
  const dot1 = document.createElement('span');
  dot1.className = `journey-bubble-dot ${node.completed ? 'dot-done' : (node.current ? 'dot-info' : 'dot-pending')}`;
  dot1.textContent = node.completed ? '✓' : (node.current ? '◐' : '·');
  const body1 = document.createElement('span');
  body1.className = 'journey-bubble-task-body';
  const title1 = document.createElement('span');
  title1.className = 'journey-bubble-title';
  title1.textContent = String(node.evidence || 'Chưa có dữ liệu được duyệt cho công đoạn này');
  const meta1 = document.createElement('span');
  meta1.className = 'journey-bubble-meta';
  meta1.textContent = node.occurred_at ? `Xác minh: ${String(node.occurred_at)}` : 'Chưa có mốc thời gian xác minh được công bố';
  body1.appendChild(title1);
  body1.appendChild(meta1);
  taskStage.appendChild(dot1);
  taskStage.appendChild(body1);
  taskStage.addEventListener('click', () => openStageModal(String(node.id), 'info'));

  const taskDocs = document.createElement('button');
  taskDocs.type = 'button';
  taskDocs.className = `journey-bubble-task ${docs.length > 0 ? 'is-done' : ''}`;
  taskDocs.dataset.testid = 'journey-bubble-task-docs';
  const dot2 = document.createElement('span');
  dot2.className = `journey-bubble-dot ${docs.length > 0 ? 'dot-done' : 'dot-pending'}`;
  dot2.textContent = docs.length > 0 ? '▤' : '·';
  const body2 = document.createElement('span');
  body2.className = 'journey-bubble-task-body';
  const title2 = document.createElement('span');
  title2.className = 'journey-bubble-title';
  title2.textContent = docs.length > 0
    ? `Chứng từ được công bố (${docs.length} tệp)`
    : 'Chứng từ: Không có dữ liệu được duyệt';
  const meta2 = document.createElement('span');
  meta2.className = 'journey-bubble-meta';
  meta2.textContent = docs.length > 0 ? 'Nhấn để xem chi tiết chỉ-đọc' : 'Trường Thành chưa công bố chứng từ nào';
  body2.appendChild(title2);
  body2.appendChild(meta2);
  taskDocs.appendChild(dot2);
  taskDocs.appendChild(body2);
  taskDocs.addEventListener('click', () => openStageModal(String(node.id), 'docs'));

  // The action the user opened this node for is the conversation; keep stage
  // and published-document summaries underneath, still accessible by scrolling.
  listDiv.appendChild(buildDiscussionThread(node));
  listDiv.appendChild(taskStage);
  listDiv.appendChild(taskDocs);
  // Issue #244 — Node 00 KẾ HOẠCH: the plan files Trường Thành already chose to
  // publish (Báo giá / Hợp đồng / Đề nghị thanh toán), metadata only.
  const planBlock = buildPlanPublishedBlock(node);
  if (planBlock) listDiv.appendChild(planBlock);

  const foot = document.createElement('div');
  foot.className = 'journey-bubble-foot';
  foot.style.display = 'flex';
  foot.style.flexDirection = 'column';
  foot.style.gap = '6px';
  const openBtn = document.createElement('button');
  openBtn.type = 'button';
  openBtn.className = 'journey-bubble-open';
  openBtn.dataset.testid = 'journey-open-workspace';
  openBtn.textContent = 'Xem chi tiết chỉ-đọc →';
  openBtn.addEventListener('click', () => openStageModal(String(node.id), 'info'));
  foot.appendChild(openBtn);
  // Issue #236 — the conversation is written/read HERE, in the node's own
  // bubble. No Streamlit form is opened above the map.
  foot.appendChild(buildDiscussionComposer(node));

  wrap.appendChild(head);
  wrap.appendChild(listDiv);
  wrap.appendChild(foot);
  bubbleSlot.appendChild(wrap);
  positionBubbleElement(wrap, pos);
}

/* ------------------------------------------------------------------ modal */

function openStageModal(nodeId, tab) {
  if (!state.lot) return;
  state.lastModalNodeId = String(nodeId || '') || null;
  state.selectedNodeId = null;
  state.activeBubblePos = null;
  const bubbleSlot = q('journey-bubble-slot');
  if (bubbleSlot) clearChildren(bubbleSlot);
  const nodes = (state.lot.journey && state.lot.journey.nodes) || [];
  const node = nodes.find((n) => String(n.id) === String(nodeId))
    || nodes[0]
    || { id: nodeId, label: nodeId, state: 'UNKNOWN', evidence: 'Chưa có dữ liệu được duyệt cho công đoạn này', occurred_at: '' };
  const modalLayer = q('journey-modal-layer');
  if (modalLayer) modalLayer.classList.remove('hidden');
  const setText = (id, text) => { const el = q(id); if (el) el.textContent = text; };
  setText('modal-kicker', `CHI TIẾT CÔNG ĐOẠN · ${String(state.lot.shipment_id || '')}`);
  setText('modal-title', String(node.label || ''));
  setText('modal-sub', node.occurred_at
    ? `Thời điểm xác minh: ${String(node.occurred_at)}`
    : 'Chưa có thời điểm xác minh được công bố cho công đoạn này');
  setText('modal-badge', nodeStatusLabel(node.state));
  renderReadonlyModalBody(node, tab || 'info');
}
function openGlobalModal(tab) {
  if (!state.lot) return;
  const nodes = (state.lot.journey && state.lot.journey.nodes) || [];
  const currentNode = nodes.find((n) => n.current) || nodes[0] || {
    id: 'overview',
    label: 'Tổng quan Hồ sơ & Chứng từ đã công bố',
    state: 'UNKNOWN',
    evidence: String(state.lot.verified_stage_title || ''),
    occurred_at: '',
  };
  openStageModal(currentNode.id, tab || 'docs');
}
function closeStageModal(skipBubbleRestore) {
  const modalLayer = q('journey-modal-layer');
  if (modalLayer) modalLayer.classList.add('hidden');
  const restoreId = state.lastModalNodeId;
  state.lastModalNodeId = null;
  const journeyView = q('shipment-journey-view');
  if (!skipBubbleRestore && restoreId && state.lot && journeyView && !journeyView.classList.contains('hidden')) {
    selectJourneyNode(restoreId);
    repositionOpenBubble();
  }
}
function closeJourneyBubble() {
  state.selectedNodeId = null;
  state.activeBubblePos = null;
  if (state.lot) renderJourneyMapForShipment(state.lot);
}
function readonlyBox(label, value, extraClass) {
  const box = document.createElement('div');
  box.className = 'readonly-box';
  const lbl = document.createElement('div');
  lbl.className = 'lbl';
  lbl.textContent = label;
  const val = document.createElement('div');
  val.className = 'val' + (extraClass ? ` ${extraClass}` : '');
  val.textContent = value;
  box.appendChild(lbl);
  box.appendChild(val);
  return box;
}
function sectionTitle(text) {
  const h = document.createElement('h4');
  h.className = 'modal-section-title';
  h.textContent = text;
  return h;
}
function emptyBox(text, testid) {
  const box = document.createElement('div');
  box.className = 'modal-empty';
  box.textContent = text;
  if (testid) box.dataset.testid = testid;
  return box;
}

function renderReadonlyModalBody(node, activeTab) {
  const container = q('journey-modal-body');
  if (!container) return;
  clearChildren(container);
  const row = state.lot || {};
  const pub = row.publication || {};
  const docs = Array.isArray(row.documents) ? row.documents : [];
  const timeline = Array.isArray(row.timeline) ? row.timeline : [];
  const quoteDocs = docs.filter((doc) => doc && doc.kind === 'CUSTOMER_QUOTE');
  const fin = row.finance_detail || null;

  const grid = document.createElement('div');
  grid.className = 'readonly-grid';
  grid.appendChild(readonlyBox('Mã lô', String(row.shipment_id || '—')));
  grid.appendChild(readonlyBox('Phương thức', String(row.transport_mode || 'Chưa xác định')));
  grid.appendChild(readonlyBox('Công đoạn', `${String(node.index || '')} ${String(node.label || '')}`.trim()));
  grid.appendChild(readonlyBox('Trạng thái công đoạn', nodeStatusLabel(node.state)));
  grid.appendChild(readonlyBox('Thời điểm xác minh', node.occurred_at ? String(node.occurred_at) : 'Chưa có dữ liệu được duyệt'));
  grid.appendChild(readonlyBox('Phiên bản công bố', String(pub.version || 'Chưa công bố')));
  grid.appendChild(readonlyBox('Duyệt công bố lúc', String(pub.approved_at || 'Chưa công bố')));
  container.appendChild(grid);

  container.appendChild(sectionTitle('HỒ SƠ & CHỨNG TỪ ĐƯỢC CÔNG BỐ'));
  if (docs.length === 0) {
    container.appendChild(emptyBox('Không có dữ liệu được duyệt — Trường Thành chưa công bố chứng từ nào cho lô này.', 'stage-documents-section'));
  } else {
    const table = document.createElement('table');
    table.className = 'doc-list-table';
    table.dataset.testid = 'stage-documents-section';
    const thead = document.createElement('thead');
    const htr = document.createElement('tr');
    ['Mã chứng từ', 'Loại', 'Tên chứng từ', 'Phiên bản', 'Trạng thái công bố'].forEach((h) => {
      const th = document.createElement('th');
      th.textContent = h;
      htr.appendChild(th);
    });
    thead.appendChild(htr);
    table.appendChild(thead);
    const tbody = document.createElement('tbody');
    docs.forEach((doc) => {
      const tr = document.createElement('tr');
      const cells = [
        ['Mã chứng từ', String(doc.id || '')],
        ['Loại', String(doc.kind || '')],
        ['Tên chứng từ', String(doc.title || '')],
        ['Phiên bản', String(doc.version || '')],
        ['Trạng thái công bố', 'Đã duyệt công bố'],
      ];
      cells.forEach(([label, value]) => {
        const td = document.createElement('td');
        td.dataset.label = label;
        td.textContent = value;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    container.appendChild(table);
  }

  container.appendChild(sectionTitle('TÀI LIỆU BÁO GIÁ ĐÃ DUYỆT'));
  if (quoteDocs.length === 0) {
    container.appendChild(emptyBox('Chưa có tài liệu báo giá được duyệt cho lô này.', 'quote-section'));
  } else {
    const quoteList = document.createElement('div');
    quoteList.className = 'readonly-grid';
    quoteList.dataset.testid = 'quote-section';
    quoteDocs.forEach((doc) => {
      quoteList.appendChild(readonlyBox('Mã tài liệu', String(doc.id || '—')));
      quoteList.appendChild(readonlyBox('Phiên bản', String(doc.version || '—')));
      quoteList.appendChild(readonlyBox('Tên báo giá', String(doc.title || '—')));
    });
    container.appendChild(quoteList);
  }

  container.appendChild(sectionTitle('CÔNG NỢ DỊCH VỤ'));
  if (!fin || fin.status !== 'CONFIRMED' || typeof fin.total_payable !== 'number') {
    container.appendChild(emptyBox('UNKNOWN / Chưa đối soát — chưa có bảng công nợ được duyệt công bố.', 'finance-section'));
  } else {
    const finSec = document.createElement('div');
    finSec.dataset.testid = 'finance-section';
    const finGrid = document.createElement('div');
    finGrid.className = 'readonly-grid';
    finGrid.appendChild(readonlyBox('Tổng phải thanh toán', formatMoney(fin.total_payable, fin.currency)));
    finGrid.appendChild(readonlyBox('Đã thanh toán', formatMoney(fin.total_paid, fin.currency)));
    finGrid.appendChild(readonlyBox('Còn phải thanh toán', formatMoney(fin.remaining_balance, fin.currency)));
    finGrid.appendChild(readonlyBox('Đối soát', String(fin.reconciliation_status_label || 'Chưa đối soát')));
    finSec.appendChild(finGrid);
    container.appendChild(finSec);
  }

  container.appendChild(sectionTitle('NHẬT KÝ MỐC TIẾN ĐỘ ĐÃ XÁC MINH & CÔNG BỐ'));
  const tlList = document.createElement('div');
  tlList.style.display = 'grid';
  tlList.style.gap = '6px';
  tlList.dataset.testid = 'timeline-section';
  if (timeline.length === 0) {
    tlList.appendChild(emptyBox('Trường Thành chưa công bố mốc tiến độ nào cho lô này.'));
  } else {
    timeline.forEach((ev) => {
      const item = document.createElement('div');
      item.className = 'readonly-box';
      const top = document.createElement('div');
      top.className = 'lbl';
      top.textContent = `${String(ev.stage || '')} · ${String(ev.occurred_at || '')}`;
      const txt = document.createElement('div');
      txt.className = 'val';
      txt.textContent = String(ev.title || '');
      item.appendChild(top);
      item.appendChild(txt);
      tlList.appendChild(item);
    });
  }
  container.appendChild(tlList);

  const backBtn = document.createElement('button');
  backBtn.type = 'button';
  backBtn.className = 'journey-toolbar-btn';
  backBtn.style.marginTop = '14px';
  backBtn.textContent = '← Quay lại hải đồ';
  backBtn.dataset.testid = 'modal-back-to-map';
  backBtn.addEventListener('click', () => closeStageModal(false));
  container.appendChild(backBtn);
}

/* -------------------------------------------------------------- utilities */

function toggleUtilityBubble(force) {
  const el = q('journey-utility-bubble');
  if (!el) return;
  const nextOpen = (typeof force === 'boolean') ? force : el.classList.contains('hidden');
  el.classList.toggle('hidden', !nextOpen);
  if (nextOpen && state.selectedNodeId) {
    state.selectedNodeId = null;
    state.activeBubblePos = null;
    if (state.lot) renderJourneyMapForShipment(state.lot);
  }
}

/* --------------------------------------------------------------- binding */

function bindOnce() {
  if (state.bound) return;
  state.bound = true;
  const on = (id, event, handler) => {
    const el = q(id);
    if (el) el.addEventListener(event, handler);
  };
  on('btn-back-to-dashboard', 'click', backToDashboard);
  on('journey-utility-trigger', 'click', () => toggleUtilityBubble());
  on('journey-utility-close', 'click', () => toggleUtilityBubble(false));
  on('utility-open-docs', 'click', () => openGlobalModal('docs'));
  on('utility-open-quote', 'click', () => openGlobalModal('quote'));
  on('btn-global-docs', 'click', () => openGlobalModal('docs'));
  on('journey-modal-close', 'click', () => closeStageModal());
  const backdrop = state.root.querySelector('[data-testid="journey-modal-backdrop"]');
  if (backdrop) backdrop.addEventListener('click', () => closeStageModal());
  on('journey-zoom-in', 'click', zoomIn);
  on('journey-zoom-out', 'click', zoomOut);
  on('journey-zoom-fit', 'click', fitJourney);
  on('journey-zoom-readable', 'click', resetReadable);

  const vp = q('journey-map-viewport');
  if (vp && vp.addEventListener) {
    let dragState = null;
    vp.addEventListener('pointerdown', (e) => {
      if (e.pointerType === 'touch') return;
      if (e.target && e.target.closest && e.target.closest('.journey-node, .journey-zoom-bar, .journey-bubble, .journey-utility-anchor')) return;
      dragState = { startX: e.clientX, startY: e.clientY, origX: state.currentPan.x, origY: state.currentPan.y };
      vp.style.cursor = 'grabbing';
      if (vp.setPointerCapture) try { vp.setPointerCapture(e.pointerId); } catch (_) { /* ignore */ }
    });
    vp.addEventListener('pointermove', (e) => {
      if (!dragState) return;
      state.currentPan = {
        x: dragState.origX + (e.clientX - dragState.startX),
        y: dragState.origY + (e.clientY - dragState.startY),
      };
      applyTransform();
    });
    const endDrag = () => { dragState = null; if (vp) vp.style.cursor = 'grab'; };
    vp.addEventListener('pointerup', endDrag);
    vp.addEventListener('pointercancel', endDrag);
    vp.addEventListener('wheel', (e) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.1 : -0.1;
      state.currentScale = Math.max(0.55, Math.min(1.85, Math.round((state.currentScale + delta) * 100) / 100));
      applyTransform();
    }, { passive: false });
  }

  // Keyboard parity with the reference (Esc closes the modal, then the bubble).
  // The listener sits on the host document because keydown targets do not
  // retarget into a shadow root from outside it.
  const doc = state.root.ownerDocument || document;
  doc.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' && e.key !== 'Esc') return;
    if (!state.root || !state.root.querySelector('#journey-workspace-shell')) return;
    const modal = q('journey-modal-layer');
    if (modal && !modal.classList.contains('hidden')) { closeStageModal(); return; }
    if (state.selectedNodeId) closeJourneyBubble();
  });

  window.addEventListener('resize', syncJourneyLayoutMode);
  window.addEventListener('orientationchange', syncJourneyLayoutMode);
}

function syncJourneyLayoutMode() {
  const wasMobile = state.mobile;
  const isMobile = applyJourneyLayoutMode();
  if (wasMobile === isMobile || !state.lot) { repositionOpenBubble(); return; }
  renderJourneyMapForShipment(state.lot);
  fitJourney();
}

function paintHeader(model) {
  const customer = model.customer || {};
  const setText = (id, text) => { const el = q(id); if (el) el.textContent = text; };
  setText('customer-brand-title', String(customer.name || 'Cổng khách hàng'));
  setText('customer-brand-sub', String(model.brand_sub || 'Theo dõi trực quan trên hải đồ theo dữ liệu Trường Thành đã xác minh'));
  setText('customer-brand-badge', String(customer.badge || 'HEXA'));
  const count = Array.isArray(model.lots) ? model.lots.length : 0;
  setText('header-published-count', `${count} lô đã công bố`);
  const account = q('header-account');
  if (account) {
    account.textContent = String(customer.account_label || '');
    account.style.display = customer.account_label ? '' : 'none';
  }
  const strip = q('portal-demo-strip');
  if (strip) {
    if (model.demo_flag) { strip.textContent = String(model.demo_flag); strip.classList.remove('hidden'); }
    else { strip.classList.add('hidden'); strip.textContent = ''; }
  }
  const notice = q('portal-notice');
  if (notice) {
    if (model.notice && model.notice.text) {
      notice.textContent = '';
      const b = document.createElement('span');
      b.style.fontWeight = '800';
      b.textContent = String(model.notice.title || 'LƯU Ý:');
      const t = document.createElement('span');
      t.textContent = ' ' + String(model.notice.text);
      notice.appendChild(b);
      notice.appendChild(t);
      notice.classList.remove('hidden');
    } else {
      notice.classList.add('hidden');
      notice.textContent = '';
    }
  }
  const kpi = model.kpi || {};
  setText('kpi-active-tracking', String(kpi.tracking ?? count));
  setText('kpi-arriving-soon', String(kpi.verified_eta ?? 0));
  setText('kpi-customer-action', String(kpi.customer_action ?? 0));
  setText('kpi-customer-action-sub', String(kpi.customer_action_sub || 'Chưa có yêu cầu được xác nhận'));
  const hint = q('journey-hint-bar');
  if (hint) {
    hint.innerHTML = '';
    const strong = (text) => { const b = document.createElement('b'); b.textContent = text; return b; };
    hint.appendChild(document.createTextNode('Bấm vào '));
    hint.appendChild(strong('node 00–06'));
    hint.appendChild(document.createTextNode(' trên hải đồ → bubble tóm tắt → '));
    hint.appendChild(strong('Xem chi tiết chỉ-đọc'));
    hint.appendChild(document.createTextNode(' hoặc '));
    hint.appendChild(strong('💬 Trao đổi / Chứng từ'));
    hint.appendChild(document.createTextNode(' để mở trao đổi của đúng công đoạn → '));
    hint.appendChild(strong('← Quay lại hải đồ'));
    hint.appendChild(document.createTextNode(' để về hải đồ → '));
    hint.appendChild(strong('← Quay lại Dashboard'));
    hint.appendChild(document.createTextNode(' để xem lại danh sách lô.'));
  }
  const note = q('utility-note');
  if (note) note.textContent = 'Chỉ hiển thị trường nằm trong allowlist công bố đã được duyệt.';
}

export default function mount(component) {
  const root = component.parentElement;
  const first = state.root !== root;
  state.root = root;
  // The v2 transport is (re)bound on every invocation; a static mount (tests,
  // or a renderer without the API) simply leaves the discussion action off.
  state.transport = component && typeof component.setTriggerValue === 'function'
    ? component.setTriggerValue
    : null;
  if (first) {
    state.bound = false;
    state.seaChart = (component.data && component.data.assets && component.data.assets.sea_chart) || '';
  }
  const paint = () => {
    const chart = (component.data && component.data.assets && component.data.assets.sea_chart) || state.seaChart;
    state.seaChart = chart;
    if (chart) {
      const sea = q('journey-sea-chart');
      if (sea) sea.style.backgroundImage = `url('${chart}')`;
      const tex = state.root.querySelector('[data-testid="journey-map-texture"]');
      if (tex) tex.style.backgroundImage = `url('${chart}')`;
    }
    const model = component.data && component.data.model;
    if (model && typeof model === 'object') {
      state.model = model;
      paintHeader(model);
      renderDashboard(model);
    }
  };
  if (!q('journey-workspace-shell') && typeof requestAnimationFrame === 'function') {
    // The shadow-root markup can land a frame after this module runs.
    requestAnimationFrame(() => { bindOnce(); paint(); });
  } else {
    bindOnce();
    paint();
  }
  return () => { /* no teardown needed: Streamlit keeps the same shadow root */ };
}
