import { contractPath } from "../lib/contractRoute";
import { shipmentIdFromPath } from "../lib/shipmentRoute";
import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowRight, Building2, CheckCircle2, ChevronDown, CircleAlert, Download, Eye, FileText, Lock, MapPin, PenLine, Phone, Truck, Wallet, FileDown, FileSpreadsheet } from "lucide-react";
import { Field, GhostBtn, MissingBox, PrimaryBtn, SearchPicker, SectionTitle, SheetDialog, StateRow, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import ShipmentOperations from "../components/ShipmentOperations";
import ShipmentExecutionProfile from "../components/ShipmentExecutionProfile";
import FinanceActualEntry from "../components/FinanceActualEntry";
import ShipmentAttachments from "../components/ShipmentAttachments";
import ShipmentDocumentPicker from "../components/ShipmentDocumentPicker";
import ShipmentJourney, { SeaExportFacts, WorkModuleStepPanel } from "../components/ShipmentJourney";
import AttentionNow from "../components/AttentionNow";
import ShipmentCompletionGoals from "../components/ShipmentCompletionGoals";
import type {
  UploadedTemplateShipmentState, JourneyNode } from "../lib/viewmodel";
import { getViewModel, subscribeViewModel, type Payment } from "../lib/viewmodel";
import {
  projectShipmentDocumentCards,
  type ShipmentDocumentAction,
  type ShipmentDocumentCard,
  type ShipmentDocumentHistoryItem,
} from "../lib/shipmentDocumentPicker";
import { useStore } from "../lib/store";
import { fmtMoney, fmtVND, fmtCcy, fmtMillionsCcy, fmtPct, cx, downloadBinaryFile, parseAmountVN } from "../lib/format";

const TABS = [
  { id: "van-tai", label: "Vận chuyển & Hàng hóa", short: "Vận chuyển" },
  { id: "lay-hang", label: "Xuất khẩu", short: "Xuất khẩu" },
  { id: "nhap", label: "Nhập khẩu & Giao hàng", short: "Nhập & Giao" },
  { id: "tai-chinh", label: "Tài chính / Công nợ", short: "Tài chính" },
  { id: "chung-tu", label: "Quy trình & Chứng từ", short: "Quy trình" },
  { id: "lich-su", label: "Lịch sử", short: "Lịch sử" },
];

const TAB_IDS = new Set(TABS.map((t) => t.id));

/** One fresh request identity per write intent — never derived from content. */
function mintRequestId(prefix: string): string {
  return `${prefix}-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

function workflowStateClass(state: string): string {
  if (state === "COMPLETE") return "bg-emerald-50 border-emerald-200 text-emerald-800";
  if (state === "READY") return "bg-blue-50 border-blue-200 text-blue-800";
  if (state === "NOT_APPLICABLE") return "bg-slate-50 border-slate-200 text-slate-500";
  if (state === "CONDITIONAL") return "bg-violet-50 border-violet-200 text-violet-800";
  if (state === "BLOCKED") return "bg-red-50 border-red-200 text-red-800";
  return "bg-amber-50 border-amber-200 text-amber-900";
}

/**
 * The tab the backend's own `nextRoute` points at.
 *
 * LOGI_UAT_REAL_USE_REPAIR_02 — "XỬ LÝ NGAY" used to read the tab with
 * `/tab=(\w+)/`, and `\w` excludes `-`: every hyphenated tab the backend
 * really emits (`lay-hang`, `tai-chinh`, `van-tai`, `chung-tu`, `lich-su`)
 * was truncated to its first segment (`lay`, `tai`, …), which matches no tab,
 * so the intended work section never opened. The route is parsed with the
 * real URL query parser and validated against the SAME canonical tab list the
 * tab bar renders; an unknown tab falls back to the default view instead of
 * selecting a section that does not exist.
 */
export function nextRouteTab(nextRoute: string): string | null {
  const q = nextRoute.indexOf("?");
  if (q < 0) return null;
  // LOGI_SHIPMENT_PRIMARY_ACTION_UNIFY_01 — the composed primary route may
  // carry a #anchor (fld-tk / shipment-execution-profile). It is not part of
  // the query and must be stripped before parsing, or the tab is lost.
  const query = nextRoute.slice(q + 1).split("#", 1)[0];
  const tab = new URLSearchParams(query).get("tab");
  return tab && TAB_IDS.has(tab) ? tab : null;
}

/**
 * The in-page anchor the backend's composed `nextRoute` points at, if any.
 *
 * LOGI_SHIPMENT_PRIMARY_ACTION_UNIFY_01 — only the EXISTING anchors this page
 * already renders are honoured: the customs declaration input (`fld-tk`) and
 * the execution-profile section (`shipment-execution-profile`). Anything else
 * is ignored (null) and the tab navigation alone applies.
 */
export function nextRouteAnchor(nextRoute: string): string | null {
  const h = nextRoute.indexOf("#");
  if (h < 0) return null;
  const anchor = nextRoute.slice(h + 1).trim();
  return anchor === "fld-tk" || anchor === "shipment-execution-profile" ? anchor : null;
}

/**
 * LOGI_SHIPMENT_PRIMARY_ACTION_UNIFY_01 — scroll (and focus, for the TK input)
 * the existing element an anchor points at. No-op when it is absent.
 */
function revealAnchor(anchor: string | null) {
  // Issue #190 CONTINUE — the permanent tab row is gone; fall back to the
  // Journey section. No-op when it is absent.
  const fallback = () => document.querySelector('[data-testid="shipment-journey"]')?.scrollIntoView({ behavior: "smooth" });
  if (!anchor) {
    fallback();
    return;
  }
  const el = document.getElementById(anchor);
  if (!el) {
    fallback();
    return;
  }
  el.scrollIntoView({ behavior: "smooth", block: anchor === "fld-tk" ? "center" : "start" });
  if (anchor === "fld-tk" && el instanceof HTMLElement) el.focus({ preventScroll: true });
}

export default function ShipmentDetail() {
  // LOGI_SHIPMENT_SLASH_ROUTE_REPAIR_01 (Issue #138) — the identity comes from
  // the RAW location segment decoded exactly ONCE, not from the router param:
  // the params API collapses a literal uppercase "%2F" inside an identity into
  // "/" (verified against this bundle), so a correctly encoded link such as
  // /lo-hang/A%252FB would otherwise open the wrong lot. The router's param
  // stays the fallback for any location that is not this route. The adjacent
  // contract detail has used this same bounded mechanism since Issue #59.
  const { id: paramId } = useParams();
  const { pathname } = useLocation();
  const id = shipmentIdFromPath(pathname, paramId);
  const [sp, setSp] = useSearchParams();
  const tab = sp.get("tab") || "van-tai";
  const { shipments, attention, updateShipment, toast, contracts, customers, dispatch, financeServices, environment } = useStore();
  // The authoritative outcome of a saved actual line comes back in the NEXT
  // fresh view-model (`lastWrites`), never from the transport.
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const nav = useNavigate();
  const s = shipments.find((x) => x.id === id);
  const [showPay, setShowPay] = useState(false);
  const [showDeliver, setShowDeliver] = useState(false);
  // P1.4 — metadata maintenance lives behind an explicit disclosure so the
  // operational tab content sits closer to the next action.
  const [headerEditOpen, setHeaderEditOpen] = useState(false);
  // ---------------------------------------------------------------------------
  // LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 · OWNER_RUNTIME_UAT_REPAIR (#86)
  //
  // The Owner's runtime screenshot showed that the header still stacked FOUR
  // equal-weight blocks between the quick facts and the tabs. These are local
  // view flags only — the SAME information, one click away, no capability
  // deleted, no data re-derived, no persisted state:
  //   moreInfoOpen   → the secondary "Thông tin thêm" identity facts
  //   missingOpen    → the existing missing-fact rows (Issue #84 semantics)
  //   checklistOpen  → the existing scoped import/delivery checklist
  //   exportUnlocked / exportLockNotice → the advisory Xuất khẩu lock (§5)
  //   (Issue #190 CONTINUE removed the "Thông tin thêm" disclosure and the
  //   permanent tab row from the default first screen; those facts live in
  //   the HỒ SƠ & PHẠM VI card and the Global Workspace now.)
  // ---------------------------------------------------------------------------
  // Issue #190 — the reference composition moves the two journey-level
  // controls ("Toàn bộ lô hàng", "+ Quy trình") into this identity bar; the
  // Journey section itself starts at the map+panel split. Presses are
  // forwarded as monotonic counters.
  const [globalReq, setGlobalReq] = useState(0);
  const [attachReq, setAttachReq] = useState(0);
  const [missingOpen, setMissingOpen] = useState(false);
  const [checklistOpen, setChecklistOpen] = useState(false);
  const [exportUnlocked, setExportUnlocked] = useState(false);
  const [exportLockNotice, setExportLockNotice] = useState(false);
  const [payAmt, setPayAmt] = useState("");
  const [payKind, setPayKind] = useState("Thu tiền khách");
  const [partnerAmt, setPartnerAmt] = useState("");
  const [form, setForm] = useState<Record<string, string>>({});
  const [savedTick, setSavedTick] = useState(0);

  // LOGI_SHIPMENT_DOCUMENT_WORKFLOW_01 — local draft only; persistence is the
  // typed backend event below and success is shown only after correlated
  // lastWrites confirmation.
  const [flowModeDraft, setFlowModeDraft] = useState("");
  const [flowAgentDraft, setFlowAgentDraft] = useState("");
  const [flowCompanyDraft, setFlowCompanyDraft] = useState("");
  const [flowPending, setFlowPending] = useState("");
  const [flowError, setFlowError] = useState("");
  const [documentSelectionOpen, setDocumentSelectionOpen] = useState(false);
  const [documentSelectionDraftIds, setDocumentSelectionDraftIds] = useState<string[]>([]);
  const [documentSelectionPending, setDocumentSelectionPending] = useState("");
  const [documentSelectionError, setDocumentSelectionError] = useState("");
  const [documentDownloadPending, setDocumentDownloadPending] = useState("");

  useEffect(() => { setForm({}); setPartnerAmt(""); }, [id, tab]);

  useEffect(() => {
    const flow = s?.commercialFlow;
    setFlowModeDraft(String(flow?.mode || ""));
    setFlowAgentDraft(flow?.subAgentId || "");
    const companies = vm?.authority?.companies ?? [];
    setFlowCompanyDraft(flow?.companyId || (companies.length === 1 ? companies[0].id : ""));
    setFlowError("");
  }, [
    id,
    s?.commercialFlow?.mode,
    s?.commercialFlow?.subAgentId,
    s?.commercialFlow?.companyId,
    vm?.authority?.companies?.length,
  ]);

  useEffect(() => {
    if (!flowPending) return;
    const outcome = vm?.lastWrites?.find(
      (row) => row.event === "shipment_commercial_flow_save" && row.requestId === flowPending
    );
    if (!outcome) return;
    setFlowPending("");
    if (outcome.ok) {
      setFlowError("");
      toast("Đã xác nhận hình thức nhập khẩu", "Workflow chứng từ đã được tính lại từ dữ liệu thật của lô.", "green");
    } else {
      const message = String(outcome.error || "Backend từ chối hình thức nhập khẩu này.");
      setFlowError(message);
      toast("Chưa lưu được hình thức nhập khẩu", message, "red");
    }
  }, [vm?.lastWrites, flowPending, toast]);

  const persistedDocumentIds = s?.selectedDocumentTemplateIds ?? [];
  const persistedDocumentKey = persistedDocumentIds.join("\u0000");
  useEffect(() => {
    setDocumentSelectionDraftIds(persistedDocumentIds);
  }, [id, persistedDocumentKey]);
  useEffect(() => {
    setDocumentSelectionOpen(false);
    setDocumentSelectionPending("");
    setDocumentSelectionError("");
    setDocumentDownloadPending("");
  }, [id]);
  useEffect(() => {
    if (!documentSelectionPending) return;
    const outcome = vm?.lastWrites?.find(
      (row) => row.event === "shipment_document_selection_save" && row.requestId === documentSelectionPending
    );
    if (!outcome) return;
    setDocumentSelectionPending("");
    if (outcome.ok) {
      const readback = outcome.readback && typeof outcome.readback === "object"
        ? outcome.readback as Record<string, unknown>
        : {};
      if (Array.isArray(readback.selectedDocumentTemplateIds)) {
        setDocumentSelectionDraftIds(readback.selectedDocumentTemplateIds.filter((value): value is string => typeof value === "string"));
      }
      setDocumentSelectionError("");
      setDocumentSelectionOpen(false);
      toast("Đã lưu biểu mẫu cho lô", "Danh sách đã được xác nhận bằng readback mới từ backend.", "green");
    } else {
      const message = String(outcome.error || "Backend từ chối lưu lựa chọn biểu mẫu.");
      setDocumentSelectionError(message);
      toast("Chưa lưu được lựa chọn", message, "red");
    }
  }, [vm?.lastWrites, documentSelectionPending, toast]);
  useEffect(() => {
    if (!documentDownloadPending) return;
    const outcome = vm?.lastWrites?.find(
      (row) => row.event === "attachment_download" && row.requestId === documentDownloadPending
    );
    if (!outcome) return;
    setDocumentDownloadPending("");
    if (!outcome.ok) {
      toast("Chưa tải được tệp chứng từ", String(outcome.error || "Backend từ chối yêu cầu đọc tệp."), "red");
    }
  }, [vm?.lastWrites, documentDownloadPending, toast]);
  // LOGI_SHIPMENT_PRIMARY_ACTION_UNIFY_01 — deep links from Home/Tasks carry
  // the composed `nextRoute` (?tab=…#anchor). On mount the tab content is
  // already rendered from the query, so honour the anchor once: scroll the
  // existing section/field into view (plus focus for the TK input).
  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, "");
    if (hash !== "fld-tk" && hash !== "shipment-execution-profile") return;
    const t = setTimeout(() => revealAnchor(hash), 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const val = (k: string, fb: string) => form[k] ?? fb;

  const linkedContract = useMemo(() => contracts.find((c) => c.id === s?.contract), [contracts, s]);
  const pickerLinkedContracts = useMemo(() => {
    const shipmentId = s?.id.toUpperCase();
    const selectedContractId = s?.contract.toUpperCase();
    const matches = contracts.filter((contract) =>
      contract.id.toUpperCase() === selectedContractId || (contract.linkedShipments ?? []).some(
        (shipment) => shipment.id.toUpperCase() === shipmentId
      )
    );
    return Array.from(new Map(matches.map((contract) => [contract.id, contract])).values());
  }, [contracts, s?.contract, s?.id]);
  const pickerContract = linkedContract ?? (pickerLinkedContracts.length === 1 ? pickerLinkedContracts[0] : null);
  const pickerPolicy = vm?.shipmentDocumentPicker;
  const shipmentDocumentCards = useMemo(() => {
    if (!s) return [];
    return projectShipmentDocumentCards({
      catalog: pickerPolicy?.catalog ?? [],
      selectedIds: persistedDocumentIds,
      shipment: s,
      linkedContract: pickerContract,
      linkedContractCount: pickerLinkedContracts.length,
      canGenerate: pickerPolicy?.canGenerate === true,
      storageConfigured: pickerPolicy?.storageConfigured === true,
      pxkDraft: {
        number: val("pxkNo", s.pxk.number ?? ""),
        date: val("pxkDate", s.pxk.date ?? ""),
      },
      form07Draft: {
        number: val("form07No", s.form07?.number ?? ""),
        orderDate: val("form07OrderDate", s.form07?.orderDate ?? ""),
      },
    });
  }, [
    s,
    pickerPolicy,
    persistedDocumentKey,
    pickerContract,
    pickerLinkedContracts.length,
    form.pxkNo,
    form.pxkDate,
    form.form07No,
    form.form07OrderDate,
  ]);
  // LOGI-193 — the Admin-published templates this lot selected, paired with
  // their server-computed readiness. Derived only from what the backend sent.
  const uploadedTemplateRows = useMemo(() => {
    const states = s?.uploadedTemplates ?? {};
    const catalog = vm?.shipmentDocumentPicker?.catalog ?? [];
    return persistedDocumentIds
      .map((templateId) => {
        const state = states[templateId];
        const entry = catalog.find((item) => item.id === templateId);
        if (!state || !entry) return null;
        return { id: templateId, label: entry.label, category: entry.category, state };
      })
      .filter(
        (row): row is {
          id: string;
          label: string;
          category: string;
          state: UploadedTemplateShipmentState;
        } => row !== null
      );
  }, [s?.uploadedTemplates, vm?.shipmentDocumentPicker?.catalog, persistedDocumentIds]);
  const authorityAgents = vm?.authority?.agents ?? [];
  const authorityCompanies = vm?.authority?.companies ?? [];
  const selectedFlowAgent = authorityAgents.find((a) => a.id === flowAgentDraft);
  const selectedFlowCompany = authorityCompanies.find((a) => a.id === flowCompanyDraft);
  const shipmentAttention = useMemo(() => attention.filter((item) => item.shipmentId === id).slice(0, 5), [attention, id]);

  if (!s) return <div className="rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto"><p className="font-extrabold text-[19px]">Không tìm thấy lô {id}</p><p className="text-slate-500 mt-1 text-[15px]">Mã lô có thể sai. Về danh sách để tìm lại.</p><Link to="/lo-hang" className="btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center">Về danh sách lô</Link></div>;

  // The ONE authoritative currency of this shipment (shipments.currency →
  // data["3.4"].currency). The backend has no FX engine, so every amount is
  // labelled with this code and amounts of different currencies are never
  // summed. The "VND" fallback mirrors core.logic's own default.
  const ccy = s.finance.currency || "VND";
  const workspaceNode = s.journey?.nodes.find(n => n.id === sp.get("stage"));
  const workspaceWork = sp.get("work") || "info";
  // Issue #162 — a Work Module step owns its own bounded "Thông tin" panel (like
  // the Sea facts panel above), so the generic work blurbs stay hidden for it.
  const moduleStepNode = workspaceNode?.moduleId ? workspaceNode : undefined;
  const showExistingWork = !workspaceNode || (workspaceWork !== "overview" && !(workspaceWork === "info" && (["si-vgm", "gate-in"].includes(workspaceNode.id) || Boolean(moduleStepNode))));
  const openStageWorkspace = (node: JourneyNode, work: string) => {
    const targetTab = work === "docs" ? "chung-tu" : work === "costs" ? "tai-chinh" : work === "history" ? "lich-su" : node.targetTab;
    // The existing advisory gate still governs origin navigation. Authoritative
    // primary-action/deep links keep their existing bypass.
    if (targetTab === "lay-hang" && exportTabLocked) { setExportLockNotice(true); return false; }
    setSp({ tab: targetTab, stage: node.id, work });
    return true;
  };

  const saveCommercialFlow = () => {
    if (!flowModeDraft) {
      setFlowError("Chọn một hình thức nhập khẩu trước khi lưu.");
      return;
    }
    if (flowModeDraft === "TT_ENTRUSTED_SUB" && !flowAgentDraft) {
      setFlowError("Chọn đơn vị đứng nhập khẩu hộ từ danh mục đối tác.");
      return;
    }
    const companyId =
      flowCompanyDraft || (authorityCompanies.length === 1 ? authorityCompanies[0].id : "");
    if ((flowModeDraft === "TT_ENTRUSTED_DIRECT" || flowModeDraft === "TT_ENTRUSTED_SUB") && !companyId) {
      setFlowError(
        flowModeDraft === "TT_ENTRUSTED_SUB"
          ? "Chọn pháp nhân Trường Thành sẽ ký với đơn vị nhập khẩu hộ."
          : "Chọn pháp nhân Trường Thành sẽ đứng tên nhập khẩu."
      );
      return;
    }
    const requestId = mintRequestId("FLOW");
    setFlowError("");
    setFlowPending(requestId);
    const sent = dispatch("shipment_commercial_flow_save", {
      shipmentId: s.id,
      requestId,
      mode: flowModeDraft,
      companyId,
      subAgentId: flowModeDraft === "TT_ENTRUSTED_SUB" ? flowAgentDraft : "",
    });
    if (!sent) {
      setFlowPending("");
      setFlowError("Component chưa kết nối backend.");
    }
  };

  const openDocumentSelection = () => {
    setDocumentSelectionDraftIds(persistedDocumentIds);
    setDocumentSelectionError("");
    setDocumentSelectionOpen(true);
  };

  const closeDocumentSelection = () => {
    if (documentSelectionPending) return;
    setDocumentSelectionOpen(false);
    setDocumentSelectionError("");
    setDocumentSelectionDraftIds(persistedDocumentIds);
  };

  const saveDocumentSelection = () => {
    if (!s || !pickerPolicy?.canSaveSelection) {
      setDocumentSelectionError("Tài khoản hiện không có quyền lưu lựa chọn biểu mẫu.");
      return;
    }
    const requestId = mintRequestId("SDOC");
    setDocumentSelectionError("");
    setDocumentSelectionPending(requestId);
    const sent = dispatch("shipment_document_selection_save", {
      shipmentId: s.id,
      requestId,
      expectedVersion: Number.isInteger(s.version) ? s.version : 0,
      selectedTemplateIds: documentSelectionDraftIds,
    });
    if (!sent) {
      setDocumentSelectionPending("");
      setDocumentSelectionError("Component chưa kết nối backend.");
    }
  };

  // -----------------------------------------------------------------------
  // Phase B write contract: every save is ONE typed event → the single Python
  // dispatcher → RBAC → existing writer → audit → fresh backend read. The UI
  // is then refreshed from the backend; nothing here mutates business state.
  // -----------------------------------------------------------------------
  /**
   * Keep only the fields the operator actually filled. Keys are the canonical
   * shipment paths; values are already resolved by `val()`. Blank stays absent
   * so an UNKNOWN value is never written as an empty/zero fact.
   */
  const onlyFilled = (resolved: Record<string, string | null | undefined>) => {
    const out: Record<string, string> = {};
    for (const [key, value] of Object.entries(resolved)) {
      const next = (value ?? "").trim();
      if (next.length > 0) out[key] = next;
    }
    return out;
  };

  const afterSave = (label: string, keep: string[] = []) => {
    // Clear what was just written, but keep the keys the operator still needs
    // on screen (the PXK legal identity is typed once and used by both the
    // receiver-facts save and the export that follows).
    setForm((f) => {
      if (keep.length === 0) return {};
      const next: Record<string, string> = {};
      for (const key of keep) if (f[key] != null) next[key] = f[key];
      return next;
    });
    setSavedTick(Date.now());
    toast(label, "Đã gửi tới backend. Dữ liệu sẽ được đọc lại từ Logistics sau khi ghi.", "green");
  };

  const saveImport = () => {
    const tk = val("tk", s.importInfo.declarationNo);
    if (!tk) { toast("Chưa thể lưu thông quan", "Thiếu: Số tờ khai nhập khẩu — nhập số TK (12 số) rồi bấm Lưu.", "red"); return; }
    // LOGI_GNT_CANONICAL_FIELDS_01 — tk_date / import_duty_amount /
    // import_vat_amount are writable canonical facts (Owner-approved
    // 2026-09-12). They are what the operator reads off the real customs
    // notice / GNT: never computed here.
    //
    // CLEAR_FIX — these three must NOT go through onlyFilled(), which drops
    // blanks: an operator clearing a stored 5.000.000 would send nothing, the
    // stale number would stay canonical and the fresh readback would put it
    // back on screen. BLANK = UNKNOWN, so a cleared field has to travel.
    //
    // The React touched-state is the discriminator:
    //   key absent from `form` → untouched → send nothing, so an ordinary save
    //     never copies the legacy `reg_date` read fallback into `tk_date`;
    //   key present in `form`  → the operator actually edited it → send the
    //     trimmed value verbatim, INCLUDING "". The backend `_coerce` preserves
    //     the blank, so the projection returns UNKNOWN and the UI renders "—".
    const edited: Record<string, string> = {};
    if (form.tkDate != null) edited.tk_date = form.tkDate.trim();
    if (form.importDuty != null) edited.import_duty_amount = form.importDuty.trim();
    if (form.importVat != null) edited.import_vat_amount = form.importVat.trim();
    const fields: Record<string, string> = {
      tk_no: tk,
      ...onlyFilled({
        phan_luong: val("inspection", s.importInfo.inspection),
        arrival_date: val("arrivalDate", s.importInfo.arrivalDate ?? ""),
        free_time: val("freeTime", s.importInfo.freeTime != null ? String(s.importInfo.freeTime) : ""),
        delivery_date: val("schedule", s.importInfo.schedule),
      }),
      ...edited,
    };
    dispatch("shipment_field_save", { shipmentId: s.id, fields });
    afterSave("Đã lưu tờ khai " + tk);
  };

  /**
   * LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the two header facts of a lot.
   *
   * A lot in this app has no free-text title: what the team calls the lot's
   * name is its CODE plus its CUSTOMER, and only the customer half is a data
   * field that can be corrected (``core.database.update_shipment_customer``
   * already writes it, audits it and bumps the version for the legacy desk).
   * The code stays read-only here on purpose: the existing rename writer does
   * not re-point ``contracts.shipment_ids``, so exposing it would silently
   * break contract links.
   *
   * Both saves are ONE typed event → the single dispatcher → RBAC → existing
   * writer → audit → fresh backend read. A blank date is only sent when the
   * operator actually edited the field, so an untouched lot never gets a
   * fabricated date and an UNKNOWN one never becomes 0/today.
   */
  const saveHeaderDate = () => {
    const edited = form.createdAt != null ? form.createdAt.trim() : null;
    if (edited === null) {
      toast("Chưa sửa ngày", "Chọn/ghi Ngày tạo rồi bấm Lưu — app không tự điền hôm nay.", "amber");
      return;
    }
    dispatch("shipment_field_save", { shipmentId: s.id, fields: { created_at: edited } });
    afterSave(edited ? "Đã lưu ngày tạo " + edited : "Đã xoá ngày tạo (để trống = chưa biết)");
  };

  const saveHeaderCustomer = () => {
    const picked = (form.lotCustomer ?? "").trim();
    if (!picked || picked === (s.customerId ?? "")) {
      toast("Chưa đổi khách hàng", "Bấm “Tìm / đổi”, chọn khách trong danh bạ rồi bấm Lưu.", "amber");
      return;
    }
    dispatch("shipment_customer_save", { shipmentId: s.id, customerId: picked });
    setForm((f) => ({ ...f, lotCustomer: "" }));
    afterSave("Đã gửi đổi khách hàng của lô");
  };

  const confirmDelivery = () => {
    const sent = dispatch("delivery_confirm", {
      shipmentId: s.id,
      deliveredAt: new Date().toISOString().slice(0, 10),
      receiverName: s.importInfo.receiver,
      receiverTitle: s.importInfo.receiverTitle ?? "",
      receiverPhone: s.importInfo.receiverPhone,
      deliveryLocation: s.importInfo.deliveryLocation || s.importInfo.deliveryAddr,
    });
    setShowDeliver(false);
    if (sent) toast("Đã gửi xác nhận giao hàng " + s.id, "Backend ghi nhận + audit; PXK sẽ mở ở tab Chứng từ.", "green");
    else toast("Không gửi được", "Component chưa kết nối backend.", "red");
  };

  // Stable request identity per PAYMENT INTENT.
  //
  // The identity is minted when the payment sheet is opened and then held for
  // that one intent, so a re-render or a double click replays the SAME id and
  // the backend's request registry treats it as one idempotent request. It is
  // deliberately NOT derived from shipmentId|amount|kind: that made a second
  // genuine receipt of the same amount and kind replay the first request and
  // never post. Idempotency is scoped to the request, not to the amount.
  const payRequestRef = useRef("");
  // -------------------------------------------------------------------
  // CUSTOMER PAYMENT — LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 (P0 payment trust).
  //
  // The old sheet closed and showed a green toast the moment the TRANSPORT
  // accepted the event. TRANSPORT_SUCCESS != PERSISTENCE_SUCCESS, so the
  // operator could believe money was recorded while the backend never
  // confirmed it. This is now the SAME authoritative outcome pattern the
  // codebase already proves in NewContract / CreateShipment /
  // payment_correction:
  //
  //   one click → ONE payment intent (stable requestId, minted at sheet
  //   open, re-minted only when the draft changes → a genuinely new intent)
  //   → submit disabled + "ĐANG CHỜ BACKEND XÁC NHẬN…" → sheet stays open →
  //   the fresh view-model's `lastWrites` is correlated by requestId:
  //     ok    → sheet closes, amount clears, THEN green success;
  //     refused → sheet stays open, amount preserved, inline backend error,
  //               the same open intent replays the SAME requestId (the
  //               writer's action registry absorbs replays; an edited amount
  //               mints a NEW id and stays a distinct intent).
  //
  //   A missing/unrelated `lastWrites` entry can never fake success, and the
  //   pending ref absorbs a synchronous double click before React even
  //   re-renders.
  // -------------------------------------------------------------------
  const [payPending, setPayPending] = useState("");
  const payPendingRef = useRef(""); // synchronous guard: two clicks in one tick
  const [payError, setPayError] = useState("");
  const openPay = () => {
    payRequestRef.current = mintRequestId("PAY");
    payPendingRef.current = "";
    setPayPending("");
    setPayError("");
    setShowPay(true);
  };
  const clearPayPending = () => { payPendingRef.current = ""; setPayPending(""); };
  const recordPay = () => {
    if (payPendingRef.current) return; // outcome in flight: never double-send
    const raw = payAmt.trim();
    const parsed = parseAmountVN(raw);
    if (parsed == null || parsed <= 0) { toast("Chưa nhập số tiền", `Nhập số tiền ${ccy} rồi bấm Lưu — ví dụ 50.000.000.`, "red"); return; }
    const sent = dispatch("payment_record", {
      shipmentId: s.id,
      amount: raw,
      requestId: payRequestRef.current,
      date: new Date().toISOString().slice(0, 10),
      note: payKind,
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    setPayError("");
    payPendingRef.current = payRequestRef.current;
    setPayPending(payRequestRef.current);
  };
  useEffect(() => {
    if (!payPending) return;
    // Correlation is scoped to the PENDING request id: a stale refusal for an
    // OLDER requestId in the same lastWrites array can never settle this retry.
    const outcome = (vm?.lastWrites ?? []).find(
      (w) => w.event === "payment_record" && (w.requestId as string | undefined) === payPending
    );
    if (!outcome) return; // still waiting for the authoritative backend answer
    if (outcome.ok) {
      // Success requires BOTH the correlated ok AND the authoritative finance
      // readback: the SAME fresh view-model must already show the payment
      // (finance.payments[].requestId). ok-without-readback stays pending —
      // it may simply be a not-yet-refreshed readback, never a failure.
      const fresh = (vm?.shipments ?? []).find((x) => x.id === s.id);
      const readbackConfirmed = !!fresh?.finance?.payments?.some(
        (p) => (p.requestId as string | undefined) === payPending
      );
      if (!readbackConfirmed) return; // truthful: still waiting for the fresh readback
      setShowPay(false);
      setPayAmt("");
      setPayError("");
      clearPayPending();
      toast("Đã ghi nhận khoản thu " + s.id,
        "Backend đã xác nhận ghi sổ — khoản thu với mã yêu cầu này đã hiển thị trong sổ tài chính đọc lại.",
        "green");
    } else {
      // Authoritative refusal: the refused request stays historical evidence.
      // The form keeps amount/kind and the NEXT retry is a NEW write attempt
      // with a FRESH requestId — so the stale refusal (old id) in the current
      // lastWrites can never reconsume and instantly "settle" the retry.
      clearPayPending();
      setPayError(outcome.error || "Backend từ chối khoản thu này.");
      payRequestRef.current = mintRequestId("PAY");
      toast("Chưa ghi nhận được", outcome.error || "Backend từ chối khoản thu.", "red");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vm?.lastWrites, payPending]);

  // -------------------------------------------------------------------
  // CUSTOMER PAYMENT CORRECTION — the real canonical reversal workflow.
  //
  // The decorative toast is gone. One sheet → the EXISTING `payment_correction`
  // event → dispatcher → RBAC → `core.database.save_direct_payment_correction`
  // → `financial_corrections` + audit `payment_reversed` + domain event →
  // forced fresh readback. The writer's semantics are the UI's semantics:
  //   * the original payment is NEVER edited in place, replaced or deleted —
  //     it stays in history, marked reversed by the backend itself;
  //   * the optional money/date/note fields are EVIDENCE attached to the
  //     correction (they travel with the correction's fingerprint), never a
  //     replacement amount;
  //   * the derived totals move because the backend recomputes them and the
  //     read model excludes reversed rows — not because this component said so.
  //
  // Request identity: minted when the sheet opens and held for that one intent
  // — a rerender or a double click replays the SAME correctionRequestId and
  // the writer's unique `correction_request_id` index absorbs the replay;
  // closing and reopening is a NEW intent and mints a NEW id. The id is
  // deliberately never derived from paymentId|amount|reason.
  //
  // Authoritative outcome: the fresh view-model's `lastWrites` carries the
  // backend's answer matched by correctionRequestId. Success closes the sheet;
  // a refusal keeps it open with the backend's real message. "Event was
  // transported" is never success.
  const [correctionFor, setCorrectionFor] = useState<Payment | null>(null);
  const [corrReason, setCorrReason] = useState("");
  const [corrAmt, setCorrAmt] = useState("");
  const [corrDate, setCorrDate] = useState("");
  const [corrNote, setCorrNote] = useState("");
  const [corrError, setCorrError] = useState("");
  const [corrPending, setCorrPending] = useState("");
  const corrRequestRef = useRef("");
  const corrPendingRef = useRef(""); // synchronous double-click guard
  const openCorrection = (p: Payment) => {
    corrRequestRef.current = mintRequestId("CORR");
    corrPendingRef.current = "";
    setCorrectionFor(p);
    setCorrReason(""); setCorrAmt(""); setCorrDate(""); setCorrNote("");
    setCorrError(""); setCorrPending("");
  };
  const closeCorrection = () => { setCorrectionFor(null); corrPendingRef.current = ""; setCorrPending(""); };
  const submitCorrection = () => {
    if (!correctionFor || corrPendingRef.current) return; // pending = in flight: never double-send
    const reason = corrReason.trim();
    if (!reason) {
      setCorrError("LÝ DO ĐIỀU CHỈNH là bắt buộc — backend từ chối correction không có lý do.");
      return;
    }
    const amtRaw = corrAmt.trim();
    // Existing canonical VN parser validates; the RAW string still travels —
    // the backend's payment_correction path parses via _financial_amount.
    // Blank stays absent (never 0); garbage is refused here AND yields no
    // evidence amount on the backend (it can silently become nothing, never 0).
    if (amtRaw && parseAmountVN(amtRaw) == null) {
      setCorrError("Số tiền bằng chứng không phải số hợp lệ — sửa lại hoặc để trống (không tự thành 0).");
      return;
    }
    const sent = dispatch("payment_correction", {
      shipmentId: s.id,
      paymentId: correctionFor.id,
      correctionRequestId: corrRequestRef.current,
      reason,
      ...(amtRaw ? { amount: amtRaw } : {}),
      ...(corrDate.trim() ? { date: corrDate.trim() } : {}),
      ...(corrNote.trim() ? { note: corrNote.trim() } : {}),
    });
    if (!sent) { setCorrError("Component chưa kết nối backend — yêu cầu chưa được gửi đi."); return; }
    setCorrError("");
    corrPendingRef.current = corrRequestRef.current;
    setCorrPending(corrRequestRef.current);
  };
  useEffect(() => {
    if (!corrPending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (w) => w.event === "payment_correction"
        && (w.correctionRequestId as string | undefined) === corrPending
    );
    if (!outcome) return; // still waiting for the authoritative backend answer
    if (outcome.ok) {
      closeCorrection();
      toast("Đã ghi bút toán hoàn tác có liên kết",
        "financial_corrections + audit payment_reversed; khoản thu gốc vẫn ở lại lịch sử với trạng thái Đã hoàn tác, số liệu đọc lại từ backend.",
        "green");
    } else {
      corrPendingRef.current = "";
      setCorrPending("");
      setCorrError(outcome.error || "Backend từ chối bút toán điều chỉnh này.");
      // Same retry contract: the refused correction stays historical; the next
      // submit mints a FRESH correctionRequestId so the stale refusal (old id)
      // in the current lastWrites can never instantly settle the retry.
      corrRequestRef.current = mintRequestId("CORR");
      toast("Chưa điều chỉnh được", outcome.error || "Backend từ chối.", "red");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vm?.lastWrites, corrPending]);

  // C2B — partner payable / payment to partner. SAME contract as receipts
  // (and the same authoritative-outcome pattern): one stable request identity
  // per PAYABLE/PAYMENT INTENT, minted with the amount draft and re-minted
  // when the draft changes, so a double click replays the SAME id and the
  // canonical action registry absorbs it. The sheet-free buttons now wait for
  // the backend's correlated `lastWrites` answer before any green success:
  // a refused write stays visible as an inline error, never as success.
  const partnerOblRef = useRef("");
  const partnerPayRef = useRef("");
  const [partnerPending, setPartnerPending] = useState<Record<string, string>>({});
  const partnerPendingRef = useRef<Record<string, string>>({});
  const [partnerError, setPartnerError] = useState<Record<string, string>>({});
  const newPartnerIntent = (prefix: string) => mintRequestId(prefix);
  const mintPartnerObl = () => { partnerOblRef.current = newPartnerIntent("POBL"); };
  const mintPartnerPay = () => { partnerPayRef.current = newPartnerIntent("PPAY"); };
  const setPartnerState = (key: "obl" | "pay", pending: string, error: string) => {
    partnerPendingRef.current = { ...partnerPendingRef.current, [key]: pending };
    setPartnerPending((p) => ({ ...p, [key]: pending }));
    setPartnerError((p) => ({ ...p, [key]: error }));
  };
  const recordPartnerPayable = () => {
    if (partnerPendingRef.current.obl) return; // outcome in flight: never double-send
    const partner = s.finance.partner;
    if (!partner?.partnerId) { toast("Chưa chọn đối tác", "Chưa có đối tác trong danh mục để ghi nhận phải trả.", "red"); return; }
    const raw = partnerAmt.trim();
    const parsed = parseAmountVN(raw);
    if (parsed == null || parsed <= 0) { toast("Chưa nhập số tiền", `Nhập số tiền phải trả ${ccy} — ví dụ 57.000.000.`, "red"); return; }
    if (!partnerOblRef.current) mintPartnerObl();
    const sent = dispatch("partner_payable_record", {
      shipmentId: s.id,
      partnerId: partner.partnerId,
      amount: raw,
      currency: ccy,
      requestId: partnerOblRef.current,
      note: "Phải trả chi phí đối tác theo thực tế lô",
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    setPartnerState("obl", partnerOblRef.current, "");
  };
  const recordPartnerPayment = () => {
    if (partnerPendingRef.current.pay) return; // outcome in flight: never double-send
    const partner = s.finance.partner;
    if (!partner?.partnerId) { toast("Chưa chọn đối tác", "Chưa có đối tác để thanh toán — ghi nhận phải trả trước.", "red"); return; }
    const raw = partnerAmt.trim();
    const parsed = parseAmountVN(raw);
    if (parsed == null || parsed <= 0) { toast("Chưa nhập số tiền", `Nhập số tiền thanh toán ${ccy} — ví dụ 20.000.000.`, "red"); return; }
    if (!partnerPayRef.current) mintPartnerPay();
    const sent = dispatch("partner_payment_record", {
      shipmentId: s.id,
      partnerId: partner.partnerId,
      amount: raw,
      currency: ccy,
      requestId: partnerPayRef.current,
      date: new Date().toISOString().slice(0, 10),
      note: "Chuyển khoản thanh toán đối tác",
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    setPartnerState("pay", partnerPayRef.current, "");
  };
  // Authoritative outcomes for BOTH partner writes, correlated by requestId —
  // the backend echoes each request's id into `lastWrites` (success AND
  // refusal), so transport truth never impersonates persistence truth.
  useEffect(() => {
    const writes = vm?.lastWrites ?? [];
    if (writes.length === 0) return;
    for (const key of ["obl", "pay"] as const) {
      const pendingId = partnerPendingRef.current[key];
      if (!pendingId) continue;
      const event = key === "obl" ? "partner_payable_record" : "partner_payment_record";
      const outcome = writes.find(
        (w) => w.event === event && (w.requestId as string | undefined) === pendingId
      );
      if (!outcome) continue; // still waiting for the authoritative answer
      if (outcome.ok) {
        // Success proof is PER LEDGER, in the backend's own projection shape:
        // • partner PAYABLE is an OBLIGATION, not a payment — the correlated
        //   outcome already carries the canonical fresh obligation result
        //   (position / obligationId / persisted from
        //   _handle_partner_payable_record); no payments list is waited for.
        // • partner PAYMENT success requires the canonical partner-ledger
        //   readback: finance.partner.payments[].requestId (from
        //   _partner_projection) — NEVER the customer receipts list
        //   (finance.payments, shipment data["3.4"].payments), which is a
        //   different ledger. ok-without-proof stays pending; it may simply
        //   be a not-yet-refreshed readback, never a failure.
        const canonicalProof =
          key === "obl"
            ? !!outcome.position
            : !!((vm?.shipments ?? []).find((x) => x.id === ((outcome.shipmentId as string | undefined) || s.id))
                ?.finance?.partner?.payments?.some(
                  (p) => (p.requestId as string | undefined) === pendingId
                ));
        if (!canonicalProof) continue; // truthful: still waiting for the canonical proof
        setPartnerState(key, "", "");
        setPartnerAmt("");
        toast(
          key === "obl" ? "Đã ghi nhận phải trả đối tác" : "Đã ghi nhận thanh toán đối tác",
          "Backend đã xác nhận ghi sổ — bút toán với mã yêu cầu này đã hiển thị trong sổ tài chính đọc lại.",
          "green"
        );
      } else {
        setPartnerState(key, "", outcome.error || "Backend từ chối bút toán này.");
        // Same retry contract as the customer receipts: the refused request
        // stays historical; the next submit is a NEW intent with a FRESH id,
        // so the stale refusal (old id) can never reconsume the retry.
        if (key === "obl") mintPartnerObl();
        else mintPartnerPay();
        toast("Chưa ghi nhận được", outcome.error || "Backend từ chối.", "red");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vm?.lastWrites]);

  // FINANCE ACTUAL — the service lines themselves are entered in the bounded
  // `FinanceActualEntry` section below (canonical catalog + full line fields +
  // edit of the SAME row), all of it saved through the ONE existing
  // `finance_actual_save` event. Quote Estimate is never touched there.

  /**
   * PXK through core.docgen. The service needs the lot's own legal identity
   * (Số PXK / Ngày PXK) — it refuses to invent them, so the shell hands over
   * what the operator typed instead of promising "tự sinh khi xuất".
   */
  const exportPXK = () => {
    const pxkNo = val("pxkNo", s?.pxk.number ?? "").trim();
    const pxkDate = val("pxkDate", s?.pxk.date ?? "").trim();
    if (!s) return;
    if (!pxkNo || !pxkDate) {
      toast("Chưa xuất được PXK",
        "core.docgen từ chối khi thiếu Số PXK hoặc Ngày PXK — nhập 2 ô ở tab Chứng từ rồi bấm lại.",
        "red");
      return;
    }
    // Real docgen path only. Phase B removed the prototype .txt export.
    const sent = dispatch("pxk_generate", { shipmentId: s.id, pxkNo, pxkDate });
    if (sent) toast("Đã gửi yêu cầu xuất PXK " + pxkNo,
      "core.docgen kiểm tra gate giao hàng, sinh file Office thật và lưu metadata chứng từ.", "blue");
    else toast("Không gửi được", "Component chưa kết nối backend.", "red");
  };

  /**
   * Issue #168 — FORM_07 Biên bản giao nhận through core.docgen.form07. The
   * receipt's own legal identity (Số biên bản / Ngày đơn đặt hàng) has no
   * canonical source, so the shell hands over what the operator typed — the
   * service refuses to invent them, exactly like pxkNo/pxkDate for PXK.
   */
  const exportFORM07 = () => {
    const form07No = val("form07No", s?.form07?.number ?? "").trim();
    const orderDate = val("form07OrderDate", s?.form07?.orderDate ?? "").trim();
    if (!s) return;
    if (!form07No || !orderDate) {
      toast("Chưa tạo được biên bản giao nhận",
        "core.docgen.form07 từ chối khi thiếu Số biên bản hoặc Ngày đơn đặt hàng — nhập 2 ô ở tab Chứng từ rồi bấm lại.",
        "red");
      return;
    }
    const sent = dispatch("form07_generate", { shipmentId: s.id, form07No, orderDate });
    if (sent) toast("Đã gửi yêu cầu tạo Biên bản giao nhận " + form07No,
      "Backend kiểm tra gate giao hàng + hợp đồng nguồn, sinh DOCX từ mẫu Owner đã làm sạch và lưu vào kho chứng từ.", "blue");
    else toast("Không gửi được", "Component chưa kết nối backend.", "red");
  };

  /**
   * Download the FORM_07 file the server really produced. Metadata is durable;
   * session bytes are session-scoped — the picker card's history rows download
   * through the EXISTING bounded attachment_download event after a remount.
   */
  const downloadForm07 = () => {
    const doc = s?.form07?.document;
    if (!doc || !doc.downloadBase64) {
      toast("File không còn trong phiên này",
        "Metadata FORM_07 " + (s?.form07?.number || s?.id || "") + " vẫn còn trên backend; tải bản đã lưu qua danh sách lịch sử của thẻ biểu mẫu.", "amber");
      return;
    }
    downloadBinaryFile(
      doc.fileName || "FORM07_" + (s?.form07?.number || s?.id) + ".docx",
      doc.downloadBase64,
      doc.mime || "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    );
  };

  /**
   * LOGI-193 — generate ONE file from an Admin-published uploaded template.
   *
   * The browser sends only the template id plus the operator-typed manual
   * values; the server owns the confirmed mapping, the canonical fact
   * resolution, readiness and the non-destructive render. Nothing here can
   * widen what gets filled: an unmapped or unresolved position is refused
   * server-side, never silently blanked.
   */
  const exportUploadedTemplate = (templateId: string, label: string, manualFields: string[]) => {
    if (!s) return;
    const manualValues: Record<string, string> = {};
    const stillMissing: string[] = [];
    for (const field of manualFields) {
      const typed = val(`up_${templateId}_${field}`, "").trim();
      if (typed) manualValues[field] = typed;
      else stillMissing.push(field);
    }
    if (stillMissing.length) {
      toast("Chưa tạo được " + label,
        "Backend từ chối khi thiếu thông tin nhập tay: " + stillMissing.join(", ") +
        " — nhập đủ ở tab Chứng từ rồi bấm lại. Không có giá trị nào được tự đặt.",
        "red");
      return;
    }
    const sent = dispatch("uploaded_template_generate", {
      shipmentId: s.id, templateId, manualValues,
    });
    if (sent) toast("Đã gửi yêu cầu tạo " + label,
      "Backend kiểm tra mapping đã xác nhận + dữ liệu canonical, điền không phá vỡ bố cục và lưu vào kho chứng từ.",
      "blue");
    else toast("Không gửi được", "Component chưa kết nối backend.", "red");
  };

  /**
   * The four facts core.docgen checks before PXK (delivery location, receiver
   * name, receiver title, delivery date) are canonical 2.7 fields, so they are
   * saved through the SAME typed writer as the rest of the lot — never kept in
   * component state only.
   */
  const savePxFacts = () => {
    const fields = onlyFilled({
      delivery_location: val("pxPlace", s.pxk.place || s.importInfo.deliveryAddr || ""),
      receiver_name: val("pxReceiver", s.pxk.receiver || s.importInfo.receiver || ""),
      receiver_title: val("pxRole", s.pxk.role ?? ""),
      delivery_date: val("pxDate", s.importInfo.schedule ?? ""),
    });
    if (Object.keys(fields).length === 0) {
      toast("Chưa có gì để lưu", "Nhập ít nhất một trường người nhận / địa điểm / ngày giao.", "red");
      return;
    }
    dispatch("shipment_field_save", { shipmentId: s.id, fields });
    afterSave("Đã lưu thông tin giao nhận " + s.id, ["pxkNo", "pxkDate"]);
  };

  /**
   * Download the file core.docgen really produced. Metadata is durable; the
   * bytes live on the session store, so a lot generated in an earlier session
   * says so honestly instead of pretending to download.
   */
  const downloadPxk = () => {
    const doc = s.pxk.document;
    if (!doc || !doc.downloadBase64) {
      toast("File không còn trong phiên này",
        "Metadata PXK " + (s.pxk.number || s.id) + " vẫn còn trên backend; bytes chỉ được giữ trong phiên đã sinh. Bấm sinh lại để có file tải.",
        "amber");
      return;
    }
    downloadBinaryFile(
      doc.fileName || "PXK_" + (s.pxk.number || s.id) + ".xlsx",
      doc.downloadBase64,
      doc.mime || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    );
  };

  const saveGntTaxpayer = () => {
    if (!s) return;
    const currentGnt = s.importInfo.gnt || { payer: "", taxCode: "", address: "" };
    const payerVal = val("gntPayer", currentGnt.payer || "");
    const taxCodeVal = val("gntTaxCode", currentGnt.taxCode || "");
    const addrVal = val("gntAddress", currentGnt.address || "");

    const fields: Record<string, string> = {
      gnt_taxpayer_name: payerVal,
      gnt_taxpayer_tax_code: taxCodeVal,
      gnt_taxpayer_address: addrVal,
    };

    const sent = dispatch("shipment_field_save", {
      shipmentId: s.id,
      fields,
    });
    if (sent) {
      toast("Đã gửi thông tin Người nộp thuế", "Backend ghi nhận vào hồ sơ hải quan của lô.", "blue");
    } else {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
    }
  };

  const generateGNT = () => {
    if (!s) return;
    const sent = dispatch("gnt_generate", { shipmentId: s.id });
    if (sent) {
      toast(
        "Đã gửi yêu cầu tạo Giấy Nộp Thuế",
        "Hệ thống kiểm tra thông tin tờ khai/thuế và sinh file Excel Mẫu C1-02/NS.",
        "blue"
      );
    } else {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
    }
  };

  const downloadGNT = () => {
    const doc = s?.importInfo.gnt?.document;
    if (!doc || !doc.downloadBase64) {
      toast(
        "File không còn trong phiên này",
        "Bytes chỉ được giữ trong phiên đã sinh. Bấm 'Tạo lại XLSX' để sinh và tải file.",
        "amber"
      );
      return;
    }
    downloadBinaryFile(
      doc.fileName || "GNT_" + s.id + ".xlsx",
      doc.downloadBase64,
      doc.mime || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    );
  };

  const openDocumentAnchor = (tabId: string, elementId: string) => {
    setSp({ tab: tabId });
    window.setTimeout(() => {
      const target = document.getElementById(elementId);
      target?.scrollIntoView({ behavior: "smooth", block: "center" });
      if (target instanceof HTMLElement) target.focus({ preventScroll: true });
    }, 160);
  };

  // LOGI-193 — `card` is now used: an uploaded-template card's id IS its
  // server-owned template id, which the generate event needs.
  const handleDocumentAction = (card: ShipmentDocumentCard, action: ShipmentDocumentAction) => {
    switch (action) {
      case "GENERATE_CONTRACT":
      case "OPEN_CONTRACT":
        if (pickerContract) nav(`${contractPath(pickerContract.id)}?tab=chung-tu`);
        else nav("/hop-dong");
        return;
      case "GENERATE_PXK":
        exportPXK();
        return;
      case "GENERATE_GNT":
        generateGNT();
        return;
      case "GENERATE_FORM07":
        exportFORM07();
        return;
      case "OPEN_CONTRACT_LIST":
        nav("/hop-dong");
        return;
      case "OPEN_COMMERCIAL_FLOW":
        openDocumentAnchor("chung-tu", "shipment-commercial-flow");
        return;
      case "OPEN_IMPORT":
        openDocumentAnchor("nhap", "fld-gnt-payer");
        return;
      case "OPEN_DELIVERY":
        setSp({ tab: "nhap" });
        setShowDeliver(true);
        return;
      case "OPEN_PXK":
        openDocumentAnchor("chung-tu", "fld-pxkno");
        return;
      case "OPEN_FORM07":
        openDocumentAnchor("chung-tu", "fld-form07no");
        return;
      // LOGI-193 — the card id IS the template id (server-owned catalog ids).
      case "GENERATE_UPLOADED": {
        const uploaded = s?.uploadedTemplates?.[card.id];
        exportUploadedTemplate(card.id, card.label, uploaded?.manualFields ?? []);
        return;
      }
      case "OPEN_UPLOADED":
        openDocumentAnchor("chung-tu", "shipment-uploaded-templates");
        return;
    }
  };

  const downloadDocumentHistory = (card: ShipmentDocumentCard, history: ShipmentDocumentHistoryItem) => {
    if (history.downloadBase64) {
      downloadBinaryFile(
        history.fileName || `${card.id}_R${history.revision}`,
        history.downloadBase64,
        history.mime || "application/octet-stream"
      );
      toast("Đã tải " + (history.fileName || card.label), "Tệp được mở từ đầu ra hiện có của bộ tạo.", "green");
      return;
    }
    if (!history.attachmentId) {
      toast("Chưa thể tải tệp", "Bản lịch sử chỉ có metadata; không có bytes phiên này hoặc tệp đính kèm đã liên kết.", "amber");
      return;
    }
    if (documentDownloadPending) return;
    const requestId = mintRequestId("DOCDOWN");
    setDocumentDownloadPending(requestId);
    const sent = dispatch("attachment_download", {
      shipmentId: s.id,
      attachmentId: history.attachmentId,
      requestId,
    });
    if (!sent) {
      setDocumentDownloadPending("");
      toast("Chưa tải được tệp chứng từ", "Component chưa kết nối backend.", "red");
    }
  };

  // `missingDocs` is already the not-ok subset of `docs`; counting both
  // double-counted the same facts (chip said 8 while the box listed 4).
  // LOGI_SCOPE_AWARE_MISSING_INFO_01 — the four operational facts
  // (Số tờ khai nhập khẩu, Đã thông quan, Xe giao VN + tài xế, Xác nhận đã giao hàng)
  // are NOT file attachments and must NOT route to chung-tu with "Tải file ... lên".
  // Truthful routing:
  // - Số tờ khai -> nhap#fld-tk
  // - Xe giao VN + tài xế -> van-tai (existing transport editor)
  // - Xác nhận đã giao hàng -> nhap + existing delivery-confirm flow
  // - Đã thông quan -> nhap existing import surface
  const missingTarget = (m: string): string => {
    if (/xe giao/i.test(m)) return "van-tai";
    if (/tờ khai|thông quan|giao hàng/i.test(m)) return "nhap";
    if (/xe TQ|biển số|packing|container|lấy hàng/i.test(m)) return "van-tai";
    if (/chứng từ|PXK|HDMB|PL$/i.test(m)) return "chung-tu";
    return "nhap";
  };

  const missingCount = s.missingDocs.length;

  // ---------------------------------------------------------------------------
  // OWNER ADVISORY LOCK — "Xuất khẩu" for an F / C / D Incoterms family.
  //
  // The Owner's rule (#86 runtime UAT): for the normal internal flow a lot
  // sold under an F-, C- or D-rule does not need the export workspace, so the
  // tab is LOCKED BY DEFAULT and clearly marked. This is a UI ADVISORY ONLY:
  //   * it never touches serviceScope / serviceScopeConfirmed, missingDocs,
  //     Tasks, status, execution-profile stages, the Incoterm value or any
  //     persistence — there is no write and no new field anywhere here;
  //   * the operator can always unlock manually for this session, because a
  //     customer term or the actual handling can change unexpectedly;
  //   * an operator-CONFIRMED service scope that really contains an origin /
  //     export activity removes the lock entirely — the operator is never
  //     trapped behind a misleading padlock;
  //   * a deep link that already points at the tab (the ONE composed primary
  //     action route, ?tab=lay-hang) is never blocked: the gate is only on the
  //     tab control itself, so the primary action's authority is untouched;
  //   * an unknown Incoterm is NOT treated as F/C/D — "we do not know" must not
  //     become "we restrict you".
  // ---------------------------------------------------------------------------
  const EXPORT_ORIGIN_SCOPES = new Set([
    "ORIGIN_PICKUP", "EXPORT_HANDLING", "EXPORT_CUSTOMS", "ORIGIN_TERMINAL_OR_BORDER",
  ]);
  const incotermForLock = (s.executionProfile?.incoterm || s.incoterm || "").trim().toUpperCase();
  const exportScopeRequiresOrigin = Boolean(s.executionProfile?.serviceScopeConfirmed)
    && (s.executionProfile?.serviceScope ?? []).some((code) => EXPORT_ORIGIN_SCOPES.has(code));
  const exportLockedByDefault = /^[FCD]/.test(incotermForLock) && !exportScopeRequiresOrigin;
  // A workspace the operator is ALREADY inside (deep link, or the ONE primary
  // action that names it) is never shown as locked — that would be a lie.
  const exportTabLocked = exportLockedByDefault && !exportUnlocked && tab !== "lay-hang";

  /** Manual unlock for THIS session only — nothing is persisted. */
  const unlockExportTab = () => {
    setExportUnlocked(true);
    setExportLockNotice(false);
    setSp({ tab: "lay-hang" });
  };

  /**
   * The ONE primary action. PR83 stays authoritative: the text and the route are
   * exactly `s.nextAction` / `s.nextRoute` — only the VISUAL WEIGHT changed
   * (the giant banner became a compact one-row strip). The behaviour below is
   * the previous banner handler, moved verbatim.
   */
  const curJourneyNode = s.journey?.nodes?.find((n) => n.current);
  const positionNote = curJourneyNode
    ? `Vị trí theo mốc thực tế: ${curJourneyNode.label}`
    : s.journey?.positionNote || "";

  // Issue #190 CONTINUE — identity-bar facts. Every value comes from the
  // shipment / environment; nothing is invented. The avatar falls back to the
  // company monogram (as in the Owner reference) when no operator is set.
  const brandSub = environment?.displayName ? `${environment.displayName} · Nội bộ` : "Nội bộ";
  const modeLabel = s.commercialFlow?.modeLabel || "";
  const operatorName = (s.journey?.owner || "").trim() || (s.sale || "").trim();
  const operatorKnown = Boolean(operatorName) && operatorName !== "—";
  const operatorInitials = operatorKnown
    ? operatorName.split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase()
    : "TT";
  const operatorTitle = operatorKnown ? `Phụ trách: ${operatorName}` : "Trường Thành";

  const runPrimaryAction = () => {
    if (s.nextRoute.startsWith("/lo-hang")) {
      const t = nextRouteTab(s.nextRoute);
      const anchor = nextRouteAnchor(s.nextRoute);
      const q = s.nextRoute.split("?", 2)[1]?.split("#", 1)[0] || "";
      const params = new URLSearchParams(q);
      if (t) params.set("tab", t);
      setSp(params);
      // Any anchored destination may be mounted only after the query-param tab
      // change re-renders. Reveal it on the next paint window; otherwise a
      // profile action can fall back to workspace-tabs before the editor exists.
      if (!anchor) revealAnchor(null);
      else setTimeout(() => revealAnchor(anchor), 150);
    } else {
      nav(s.nextRoute);
    }
  };

  return (
    <div className="space-y-2.5 min-w-0">
      {/* HEADER — Issue #190 CONTINUE: ONE top white header bar per the Owner
          reference. LEFT: brand identity + shipment title + mode chip +
          customer/route line. RIGHT: Toàn bộ lô hàng + operator avatar.
          The permanent tab row is gone from the default first screen (tabs
          live in Global Workspace); the secondary identity facts moved into
          the HỒ SƠ & PHẠM VI card. Nothing is deleted. */}
      <div className="rounded-2xl bg-white border border-slate-200 px-4 py-2.5 md:px-5" data-testid="shipment-identity-bar">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2.5 shrink-0" aria-label="Về trang chủ">
            <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#1e5aa8] to-[#0a1f3a] grid place-items-center text-white font-extrabold text-[18px] shadow">T</span>
            <span className="leading-tight hidden sm:block">
              <span className="block font-extrabold text-[14.5px] text-[#0f2a4a]">TRƯỜNG THÀNH</span>
              <span className="block text-[11.5px] text-slate-500 font-medium">{brandSub}</span>
            </span>
          </Link>
          <span className="hidden md:block w-px self-stretch bg-slate-200" aria-hidden="true" />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <h1 className="text-[19px] font-extrabold text-[#0f2a4a] whitespace-nowrap" title={positionNote || undefined}>Lô hàng {s.id}</h1>
              {modeLabel && <span className="rounded-md border border-red-200 bg-red-50 px-2 py-0.5 text-[12px] font-bold text-red-700 whitespace-nowrap">{modeLabel}</span>}
            </div>
            <p className="mt-0.5 truncate text-[12.5px] text-slate-600">
              <span className="font-semibold text-slate-800">{s.customer}</span>
              <span className="text-slate-400"> → </span>
              <span>{s.route}</span>
            </p>
          </div>
          <div className="ml-auto flex shrink-0 items-center gap-2.5">
            <button type="button" onClick={() => setGlobalReq((v) => v + 1)} data-testid="journey-global-page" className="touch-target inline-flex items-center rounded-xl border border-slate-200 bg-white px-4 min-h-[44px] text-[14px] font-bold text-[#0f2a4a] hover:border-[#1e5aa8]">Toàn bộ lô hàng</button>
            <span className="grid h-10 w-10 place-items-center rounded-full bg-[#0f2a4a] text-white text-[13px] font-extrabold" title={operatorTitle} aria-label={operatorTitle}>{operatorInitials}</span>
          </div>
        </div>
      </div>
        {/* OWNER_RUNTIME_UAT_REPAIR — the duplicated "HỒ SƠ THỰC HIỆN LÔ ·
            Hồ sơ lô còn thiếu…" yellow band is GONE from the top path: the
            "Hồ sơ thực hiện lô" section below already owns that configuration
            state (its state label, its summary lines, its stage chips) and a
            real CONFIG_CHECK / insurance mismatch is still rendered there in
            red. Two warnings for one fact was the clutter the Owner reported. */}
        {/* Issue #190 CONTINUE — the permanent tab row is gone from the default
            first screen. Tab capabilities stay reachable through Toàn bộ lô
            hàng → Global Workspace (and deep links); nothing is deleted. */}
        {/* OWNER_RUNTIME_UAT_REPAIR §5 — a locked export tab never opens
            silently and never just disappears: clicking it says WHY in one
            compact line and hands the operator the manual unlock. Session-only,
            no persisted override, and it changes no data. */}
        {exportLockNotice && (
          <div
            role="status"
            data-testid="export-lock-notice"
            className="mx-3 md:mx-6 mb-3 flex flex-wrap items-center gap-2 rounded-xl border-2 border-slate-200 bg-slate-50 px-3 py-2"
          >
            <Lock size={15} className="shrink-0 text-slate-500" aria-hidden="true" />
            <p className="text-[13px] font-semibold text-slate-700 min-w-0 flex-1">
              Xuất khẩu đang được khóa theo điều kiện giao hàng {incotermForLock} — ở các điều kiện F/C/D, dòng chảy nội bộ thường không cần bàn làm việc xuất khẩu. Điều kiện khách hoặc cách xử lý thực tế thay đổi? Mở khóa tay để làm việc trực tiếp.
            </p>
            <button
              type="button"
              onClick={unlockExportTab}
              data-testid="export-unlock"
              className="btn-press touch-target shrink-0 inline-flex items-center gap-1.5 rounded-lg border-2 border-[#0f2a4a] bg-white text-[#0f2a4a] text-[13px] font-bold px-3 min-h-[40px]"
            >
              MỞ KHÓA XUẤT KHẨU
            </button>
          </div>
        )}

      <AttentionNow items={shipmentAttention} title="Cần xử lý" compact />

      <ShipmentJourney key={s.id} shipment={s} activeStage={workspaceNode?.id || ""} work={workspaceWork} globalRequest={globalReq} attachRequest={attachReq}
        onOpen={openStageWorkspace} onGlobal={(target = "van-tai") => { if (target === "lay-hang" && exportTabLocked) { setExportLockNotice(true); return false; } setSp({ tab: target }); return true; }} runPrimary={runPrimaryAction}
        globalActive={Boolean(sp.get("tab")) && !workspaceNode} globalTab={tab}>
      {workspaceNode && workspaceWork === "info" && !moduleStepNode && ["si-vgm", "gate-in", "customs-export"].includes(workspaceNode.id) &&
        <SeaExportFacts key={`${s.id}-${workspaceNode.id}-${s.version}`} shipment={s} stageId={workspaceNode.id} />}
      {workspaceNode && moduleStepNode && workspaceWork === "info" &&
        <WorkModuleStepPanel key={`${s.id}-${workspaceNode.id}`} shipment={s} node={workspaceNode} />}
      {workspaceNode && ["docs", "costs", "history"].includes(workspaceWork) && <p className="rounded-xl bg-slate-50 border p-3 text-sm text-slate-600">
        {workspaceWork === "docs" ? "Tệp liên quan được lọc từ kho chứng từ toàn lô; quy trình chứng từ chung vẫn giữ nguyên." : workspaceWork === "costs" ? "Dòng chi phí theo công đoạn. Dòng cũ chưa phân công vẫn xem được trong nhóm chưa phân công; tổng tiền là tổng toàn lô do backend tính." : "Lịch sử toàn lô: dữ liệu cũ không có liên kết công đoạn nên được giữ nguyên, không tự đoán."}
      </p>}

      {/* ============ LOT IDENTITY + MAINTENANCE DISCLOSURE ============
          LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — customer/date maintenance used
          to sit permanently between the header+tabs and the operational tab
          content, pushing daily work below the fold. It is now an explicit
          "Sửa thông tin lô" disclosure: the identity summary STAYS visible on
          the main path, and every edit capability (customer change, creation
          date, save semantics) is one click away — nothing removed. */}
      {!workspaceNode && <section
        className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5"
        data-testid="shipment-header-edit"
      >
        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => setHeaderEditOpen((v) => !v)}
            aria-expanded={headerEditOpen}
            data-testid="shipment-header-edit-toggle"
            className={cx(
              "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 px-3.5 min-h-[44px] text-[14px] font-bold",
              headerEditOpen ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a]"
            )}
          >
            <PenLine size={17} className={headerEditOpen ? "text-white" : "text-[#1e5aa8]"} /> Sửa thông tin lô
            <ChevronDown size={16} className={cx("transition-transform", headerEditOpen && "rotate-180")} />
          </button>
          <span className="text-[12.5px] font-semibold text-slate-500 text-right">
            Tên lô = <b className="text-[#0f2a4a]">{s.id}</b> · {s.customer}
            {!headerEditOpen && <span className="hidden md:inline"> · tạo {s.createdAt || "chưa biết"}</span>}
          </span>
        </div>
        {headerEditOpen && (
        <>
        <div className="grid gap-3 lg:grid-cols-[1fr_300px] items-start mt-3">
          <div className="space-y-2">
            <SearchPicker
              label="Khách hàng của lô"
              testId="shipment-customer-picker"
              options={customers.map((x) => ({
                id: x.id,
                label: x.name || x.id,
                sub: x.mst || x.taxCode ? `MST ${x.mst || x.taxCode} · ${x.id}` : x.id,
              }))}
              selectedId={form.lotCustomer || s.customerId || ""}
              selectedLabel={
                customers.find((x) => x.id === (form.lotCustomer || s.customerId))?.name || s.customer
              }
              placeholder="Gõ tên khách hoặc mã khách để tìm…"
              emptyHint="Danh bạ khách hàng đang trống — thêm khách ở mục Khách Hàng trước."
              onSelect={(idValue) => set("lotCustomer", idValue)}
            />
            <div className="flex flex-wrap items-center gap-2">
              <PrimaryBtn onClick={saveHeaderCustomer} className="min-h-[44px] px-4 text-[13.5px]">
                💾 LƯU KHÁCH HÀNG CỦA LÔ
              </PrimaryBtn>
              {(form.lotCustomer ?? "") !== "" && (form.lotCustomer ?? "") !== (s.customerId ?? "") && (
                <GhostBtn onClick={() => set("lotCustomer", "")} className="min-h-[44px]">Hủy chọn</GhostBtn>
              )}
            </div>
          </div>
          <div className="space-y-2">
            <Field label="Ngày tạo lô" hint="DD/MM/YYYY hoặc YYYY-MM-DD · để trống = chưa biết">
              <input
                id="fld-created-at"
                value={val("createdAt", s.createdAt ?? "")}
                onChange={(e) => set("createdAt", e.target.value)}
                placeholder="VD: 03/09/2026"
                className={inputCls()}
              />
            </Field>
            <div className="flex flex-wrap items-center gap-2">
              <PrimaryBtn onClick={saveHeaderDate} className="min-h-[44px] px-4 text-[13.5px]">
                💾 LƯU NGÀY TẠO
              </PrimaryBtn>
              {form.createdAt != null && form.createdAt.trim() === "" && (
                <span className="text-[12.5px] font-semibold text-amber-700">
                  Đang lưu = để trống (chưa biết)
                </span>
              )}
            </div>
          </div>
        </div>
        <p className="text-[12.5px] text-slate-500 mt-2.5">
          Mã lô <b>{s.id}</b> là định danh và không đổi ở màn này — đổi mã lô sẽ làm lệch các liên
          kết hợp đồng đang trỏ vào mã cũ. Ngày tạo là ngày bộ phận vận hành mở lô, không tự suy ra
          từ ETD/ETA.
        </p>
        </>
        )}
      </section>}

      {/* ============ HỒ SƠ THỰC HIỆN LÔ — COMPACT ENTRY ============
          LOGI_QUOTE_COST_WORKFLOW_UX_01 — the FULL editor no longer occupies a
          permanent top-level block before the working content. It now lives in
          "Vận chuyển & Hàng hóa" (default collapsed). What stays on every tab
          is ONE line: the persisted state + an explicit "Sửa hồ sơ thực hiện"
          entry. Capability, data, shipment_profile_save, nextAction routing,
          Incoterms and insurance-mismatch logic are all unchanged — only the
          composition moved. A real CONFIG_CHECK / insurance mismatch still
          surfaces here in the same red wording so it cannot be missed. */}
      {!workspaceNode && tab !== "van-tai" && (
        <div
          data-testid="shipment-profile-compact"
          data-state={s.executionProfile?.state ?? ""}
          className={cx(
            "flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border-2 px-3 py-2",
            s.executionProfile?.state === "CONFIG_CHECK"
              ? "border-red-300 bg-red-50"
              : s.executionProfile?.state === "PROFILE_INCOMPLETE"
                ? "border-amber-200 bg-amber-50/60"
                : "border-slate-200 bg-white"
          )}
        >
          <span className="text-[11px] font-extrabold uppercase tracking-wide text-slate-500 shrink-0">Hồ sơ thực hiện lô</span>
          <span className="text-[13.5px] font-bold text-[#0f2a4a] min-w-0">
            {s.executionProfile?.stateLabel || "Chưa có dữ liệu hồ sơ"}
          </span>
          <span className="text-[12.5px] text-slate-500 min-w-0 hidden sm:inline">
            {(s.executionProfile?.summaryLines ?? []).slice(0, 1).join("")}
          </span>
          <button
            type="button"
            onClick={() => setSp({ tab: "van-tai" })}
            data-testid="shipment-profile-compact-edit"
            className="btn-press touch-target ml-auto shrink-0 inline-flex items-center gap-1.5 rounded-lg border-2 border-[#0f2a4a] bg-white text-[#0f2a4a] text-[13px] font-bold px-3 min-h-[40px]"
          >
            Sửa hồ sơ thực hiện
          </button>
        </div>
      )}

      {/* OWNER_RUNTIME_UAT_REPAIR §3 — "Đang thiếu N thông tin" used to be a
          full-width block of boxes permanently on the page. It is now ONE
          compact disclosure, collapsed by default: the count is still visible
          (the same `s.missingDocs.length` the header chip reports — no second
          counter), and expanding reveals the EXISTING rows with their EXISTING
          Issue #84 routing, untouched below. */}
      {missingCount > 0 && tab !== "chung-tu" && (
        <div className="rounded-2xl bg-white border-2 border-red-200 p-3 md:p-3.5" data-testid="missing-info">
          <button
            type="button"
            onClick={() => setMissingOpen((v) => !v)}
            aria-expanded={missingOpen}
            data-testid="missing-info-toggle"
            className="btn-press touch-target flex w-full items-center gap-2 text-left"
          >
            <CircleAlert size={16} className="shrink-0 text-red-600" />
            <span className="font-extrabold text-[14px] text-red-800">Thiếu {missingCount} thông tin</span>
            <ChevronDown size={16} className={cx("ml-auto shrink-0 text-red-700 transition-transform", missingOpen && "rotate-180")} />
          </button>
          {missingOpen && (
          <div className="grid gap-2 mt-2.5 md:grid-cols-2">
            {s.missingDocs.map((m) => (
              <MissingBox
                key={m}
                what={m}
                actionLabel="Bổ sung ngay"
                onAction={() => {
                  // LOGI_SCOPE_AWARE_MISSING_INFO_01 — truthful routing per fact
                  if (/xe giao/i.test(m)) {
                    // Xe giao VN + tài xế -> van-tai existing transport editor
                    setSp({ tab: "van-tai" });
                    setTimeout(() => document.getElementById("missing-anchor")?.scrollIntoView({ behavior: "smooth", block: "center" }), 150);
                  } else if (m.includes("tờ khai")) {
                    // Số tờ khai -> nhap#fld-tk
                    setSp({ tab: "nhap" });
                    setTimeout(() => {
                      const el = document.getElementById("fld-tk");
                      if (el) {
                        el.scrollIntoView({ behavior: "smooth", block: "center" });
                        (el as HTMLElement).focus({ preventScroll: true });
                      } else {
                        document.getElementById("missing-anchor")?.scrollIntoView({ behavior: "smooth", block: "center" });
                      }
                    }, 150);
                  } else if (/xác nhận.*giao/i.test(m) || m.toLowerCase().includes("đã giao")) {
                    // Xác nhận đã giao hàng -> existing delivery-confirm flow
                    setSp({ tab: "nhap" });
                    setTimeout(() => {
                      if (!s.importInfo.delivered) {
                        setShowDeliver(true);
                      } else {
                        document.getElementById("missing-anchor")?.scrollIntoView({ behavior: "smooth", block: "center" });
                      }
                    }, 150);
                  } else if (/thông quan/i.test(m)) {
                    // Đã thông quan -> nhap existing import surface, not fld-tk
                    setSp({ tab: "nhap" });
                    setTimeout(() => {
                      const sec = document.getElementById("import-customs-section") || document.getElementById("missing-anchor");
                      sec?.scrollIntoView({ behavior: "smooth", block: "center" });
                    }, 150);
                  } else {
                    const targetTab = missingTarget(m);
                    setSp({ tab: targetTab });
                    setTimeout(() => document.getElementById("missing-anchor")?.scrollIntoView({ behavior: "smooth", block: "center" }), 150);
                  }
                }}
              />
            ))}
          </div>
          )}
        </div>
      )}

      {/* ============ TAB: OPERATIONAL TRANSPORT + CARGO ============
          The full execution-profile editor belongs here: it is the tab that owns
          transport/cargo reality, and the profile decides which stages exist. */}
      {showExistingWork && tab === "van-tai" && (
        <>
          <ShipmentExecutionProfile
            shipment={s}
            dispatch={dispatch}
            toast={toast}
            onOpenTransportTab={() => setSp({ tab: "van-tai" })}
          />
          <ShipmentOperations shipment={s} dispatch={dispatch} toast={toast} />
        </>
      )}

      {/* ============ TAB: PICKUP ============ */}
      {showExistingWork && tab === "lay-hang" && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4" id="missing-anchor">
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><MapPin size={19} className="text-[#1e5aa8]" /> Nhà máy & xuất khẩu</h3>
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-3.5">
              <p className="font-bold text-[15px]">{s.pickup.factory || "Chưa có nhà máy"}</p>
              <p className="text-[13.5px] text-slate-500">{s.pickup.address || "Chưa có địa chỉ lấy hàng"}</p>
              <p className="text-[14px] mt-1.5 flex items-center gap-1.5"><Phone size={15} className="text-slate-400" /> {s.pickup.contact || "Chưa có liên hệ"} · {s.pickup.phone || "—"}</p>
            </div>
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-[13.5px] text-blue-950">
              <p className="font-extrabold">Xe/container và lịch chặng được quản lý tại “Vận chuyển & Hàng hóa”.</p>
              <p className="mt-1">Không nhập biển số TQ và xe giao VN vào cùng một trường.</p>
              <button onClick={() => setSp({ tab: "van-tai" })} className="touch-target mt-3 rounded-xl bg-[#1e5aa8] text-white font-bold px-4 min-h-[44px]">MỞ CÁC CHẶNG VẬN CHUYỂN</button>
            </div>
          </section>

          <div className="space-y-4">
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Xuất khẩu — {s.exportInfo.border}</h3>
              <StateRow label="Đơn vị khai" value={s.exportInfo.declarant} />
              <StateRow label="Ngày dự kiến / thực tế" value={<span>{s.exportInfo.eta || "—"} / {s.exportInfo.ata || "chưa có"}</span>} />
              <StateRow label="Trạng thái" value={<ToneBadge tone={s.exportInfo.state.includes("Đã") ? "green" : "amber"} size="sm">{s.exportInfo.state}</ToneBadge>} />
            </section>

          </div>
        </div>
      )}

      {/* ============ TAB: IMPORT ============ */}
      {showExistingWork && tab === "nhap" && (
        <div className="space-y-4" id="missing-anchor">
          {/* LOGI_SCOPE_AWARE_MISSING_INFO_01 — scope-relevant checklist moved from lay-hang / Xuất khẩu (misleading heading) to the correct existing Nhập khẩu & Giao hàng surface. Only relevant rows per confirmed service scope. Truthful routing per fact. */}
          {s.docs.length > 0 && (
            /* OWNER_RUNTIME_UAT_REPAIR §4 — same section, same rows, same
               truthful per-fact routing; only the DEFAULT state changed. The
               count shown next to the toggle is `s.docs.filter(d => !d.ok)` —
               the SAME scoped rows the section already renders (display only:
               no new checklist engine, no new counter authority, no
               missingDocs/serviceScope change). */
            <section className="rounded-2xl bg-white border border-slate-200 p-3 md:p-3.5" data-testid="import-delivery-checklist" aria-label="Checklist nhập khẩu & giao hàng">
              <button
                type="button"
                onClick={() => setChecklistOpen((v) => !v)}
                aria-expanded={checklistOpen}
                data-testid="import-delivery-checklist-toggle"
                className="btn-press touch-target flex w-full items-center gap-2 text-left"
              >
                <span className="font-extrabold text-[15.5px] text-[#0f2a4a]">Checklist nhập khẩu &amp; giao hàng</span>
                <span className={cx("text-[12.5px] font-bold", s.docs.some((d) => !d.ok) ? "text-amber-700" : "text-emerald-700")}>
                  {s.docs.filter((d) => !d.ok).length}/{s.docs.length} cần bổ sung
                </span>
                <ChevronDown size={16} className={cx("ml-auto shrink-0 text-slate-400 transition-transform", checklistOpen && "rotate-180")} />
              </button>
              {checklistOpen && (<>
              <p className="text-[13px] text-slate-500 mt-1 mb-3">Thông tin vận hành cần bổ sung theo phạm vi Trường Thành đã xác nhận.</p>
              <div className="space-y-2">
                {s.docs.map((d) => (
                  <div key={d.name} className={cx("flex items-center gap-3 rounded-xl border-2 p-3", d.ok ? "border-emerald-200 bg-emerald-50/60" : "border-amber-300 bg-amber-50")}>
                    <span className={cx("w-8 h-8 rounded-full grid place-items-center font-extrabold shrink-0", d.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white")}>{d.ok ? "✓" : "!"}</span>
                    <div className="flex-1 min-w-0"><p className="font-bold text-[14.5px]">{d.name} — {d.ok ? <span className="text-emerald-700">✅ Đủ</span> : <span className="text-amber-800">Thiếu</span>}</p>{d.note && <p className="text-[13px] text-slate-600">{d.note}</p>}</div>
                    {!d.ok && (
                      <button
                        onClick={() => {
                          // Truthful action routing per operational fact
                          if (d.name.includes("tờ khai")) {
                            // Số tờ khai -> nhap#fld-tk
                            document.getElementById("fld-tk")?.focus();
                            document.getElementById("fld-tk")?.scrollIntoView({ behavior: "smooth", block: "center" });
                          } else if (/xe giao/i.test(d.name)) {
                            // Xe giao VN + tài xế -> van-tai existing transport editor
                            setSp({ tab: "van-tai" });
                          } else if (/xác nhận.*giao/i.test(d.name) || d.name.toLowerCase().includes("đã giao")) {
                            // Xác nhận đã giao hàng -> existing delivery-confirm flow
                            if (!s.importInfo.delivered) {
                              setShowDeliver(true);
                            } else {
                              document.getElementById("import-delivery-section")?.scrollIntoView({ behavior: "smooth", block: "center" });
                            }
                          } else if (/thông quan/i.test(d.name)) {
                            // Đã thông quan -> nhap existing import surface, not fld-tk
                            const sec = document.getElementById("import-customs-section") || document.getElementById("missing-anchor");
                            sec?.scrollIntoView({ behavior: "smooth", block: "center" });
                          } else {
                            document.getElementById("missing-anchor")?.scrollIntoView({ behavior: "smooth", block: "center" });
                          }
                        }}
                        className="btn-press touch-target shrink-0 inline-flex items-center gap-1 rounded-lg bg-amber-500 text-white text-[13.5px] font-bold px-3 min-h-[44px]"
                      >
                        <PenLine size={14} /> Bổ sung
                      </button>
                    )}
                  </div>
                ))}
              </div>
              </>)}
            </section>
          )}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="space-y-4">
            <section id="import-customs-section" className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Tờ khai & thuế nhập khẩu — {s.importInfo.borderVN}</h3>
              {!val("tk", s.importInfo.declarationNo) && <MissingBox what="số tờ khai nhập khẩu" where="Hàng đang chờ ở bãi VN — có số TK mới nộp thuế & phân luồng được" actionLabel="Nhập số TK" onAction={() => document.getElementById("fld-tk")?.focus()} />}
              <div className="grid sm:grid-cols-2 gap-3">
                <Field label="Số tờ khai" required={!s.importInfo.declarationNo} error={!val("tk", s.importInfo.declarationNo) ? "Nhập 12 số tờ khai — VD: 105588421330" : undefined}>
                  <input id="fld-tk" value={val("tk", s.importInfo.declarationNo)} onChange={(e) => set("tk", e.target.value)} placeholder="12 số tờ khai…" className={inputCls(!val("tk", s.importInfo.declarationNo) ? "missing" : "ok")} />
                </Field>
                <Field label="Ngày đăng ký" hint="Lưu vào ngày tờ khai (2.4.tk_date)."><input id="fld-tkdate" value={val("tkDate", s.importInfo.regDate)} onChange={(e) => set("tkDate", e.target.value)} placeholder="VD: 15/08/2026" className={inputCls()} /></Field>
                <Field label="Thuế nhập khẩu (VND)" hint="Số thực tế trên thông báo thuế/GNT — app không tự tính."><input id="fld-duty" value={val("importDuty", s.importInfo.tax == null ? "" : String(s.importInfo.tax))} onChange={(e) => set("importDuty", e.target.value)} inputMode="decimal" placeholder="Bỏ trống = chưa biết" className={inputCls()} /></Field>
                <Field label="VAT hàng nhập (VND)" hint="Số thực tế trên thông báo thuế/GNT — app không tự tính."><input id="fld-vat" value={val("importVat", s.importInfo.vat == null ? "" : String(s.importInfo.vat))} onChange={(e) => set("importVat", e.target.value)} inputMode="decimal" placeholder="Bỏ trống = chưa biết" className={inputCls()} /></Field>
                <Field label="Phân luồng / kiểm hóa"><input value={val("inspection", s.importInfo.inspection)} onChange={(e) => set("inspection", e.target.value)} className={inputCls()} /></Field>
                <Field label="Giấy phép chuyên ngành" hint="Chỉ đọc — chưa có trường dữ liệu trong lô."><input value={s.importInfo.license} readOnly placeholder="Chưa có trường dữ liệu" className={inputCls()} /></Field>
              </div>
              <PrimaryBtn onClick={saveImport} className="w-full">💾 LƯU TỜ KHAI & THUẾ</PrimaryBtn>
              {val("tk", s.importInfo.declarationNo) && <div className="rounded-xl bg-blue-50 border border-blue-200 p-3 text-[13.5px] text-blue-900">✅ Đã có số TK <b>{val("tk", s.importInfo.declarationNo)}</b>. Tiếp theo: nộp thuế rồi bấm “Thông quan” khi có kết quả phân luồng.</div>}
            </section>

            {/* GIẤY NỘP THUẾ (GNT) */}
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-extrabold text-[16px] text-[#0f2a4a] flex items-center gap-2">
                  <FileSpreadsheet size={18} className="text-[#1e5aa8]" /> GIẤY NỘP THUẾ (GNT) — Mẫu C1-02/NS
                </h3>
                {s.importInfo.gnt?.done && (
                  <span className="rounded-full bg-emerald-100 text-emerald-800 text-[12px] font-bold px-2.5 py-0.5">
                    ✅ Đã tạo
                  </span>
                )}
              </div>

              {/* Read-only summary of declaration & taxes */}
              <div className="grid sm:grid-cols-2 gap-2 text-[13px]">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block text-[11.5px] font-medium">Số tờ khai</span>
                  <span className="font-bold text-[#0f2a4a]">{s.importInfo.declarationNo || <span className="text-amber-600 italic font-normal">Chưa có</span>}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block text-[11.5px] font-medium">Ngày tờ khai</span>
                  <span className="font-bold text-[#0f2a4a]">{s.importInfo.regDate || <span className="text-amber-600 italic font-normal">Chưa có</span>}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block text-[11.5px] font-medium">Thuế nhập khẩu</span>
                  <span className="font-bold text-[#0f2a4a]">{s.importInfo.tax != null ? fmtVND(s.importInfo.tax) : <span className="text-amber-600 italic font-normal">Chưa có</span>}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block text-[11.5px] font-medium">VAT hàng nhập khẩu</span>
                  <span className="font-bold text-[#0f2a4a]">{s.importInfo.vat != null ? fmtVND(s.importInfo.vat) : <span className="text-amber-600 italic font-normal">Chưa có</span>}</span>
                </div>
              </div>

              {/* Explicit Operator Input for Taxpayer */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[13.5px] text-[#0f2a4a]">Thông tin Người nộp thuế (Pháp nhân chịu thuế)</span>
                  {s.importInfo.gnt?.customerHint && (
                    <span className="text-[11.5px] text-slate-500 italic">Gợi ý khách hàng: <b>{s.importInfo.gnt.customerHint}</b></span>
                  )}
                </div>
                <div className="grid sm:grid-cols-2 gap-2.5">
                  <Field label="Người nộp thuế *" hint="Tên pháp nhân trên tờ khai HQ">
                    <input
                      id="fld-gnt-payer"
                      data-field="gnt-payer"
                      value={val("gntPayer", s.importInfo.gnt?.payer || "")}
                      onChange={(e) => set("gntPayer", e.target.value)}
                      placeholder="VD: CÔNG TY TNHH ABC…"
                      className={inputCls(!val("gntPayer", s.importInfo.gnt?.payer || "") ? "missing" : "ok")}
                    />
                  </Field>
                  <Field label="Mã số thuế (MST) *" hint="MST 10 hoặc 13 số">
                    <input
                      id="fld-gnt-taxcode"
                      data-field="gnt-taxcode"
                      value={val("gntTaxCode", s.importInfo.gnt?.taxCode || "")}
                      onChange={(e) => set("gntTaxCode", e.target.value)}
                      placeholder="VD: 0101234567"
                      className={inputCls(!val("gntTaxCode", s.importInfo.gnt?.taxCode || "") ? "missing" : "ok")}
                    />
                  </Field>
                  <div className="sm:col-span-2">
                    <Field label="Địa chỉ" hint="Địa chỉ trụ sở / đăng ký kinh doanh">
                      <input
                        id="fld-gnt-address"
                        data-field="gnt-address"
                        value={val("gntAddress", s.importInfo.gnt?.address || "")}
                        onChange={(e) => set("gntAddress", e.target.value)}
                        placeholder="Địa chỉ doanh nghiệp nộp thuế…"
                        className={inputCls()}
                      />
                    </Field>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={saveGntTaxpayer}
                  className="btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-[#0f2a4a] text-white font-semibold px-3.5 py-2 text-[13px] hover:bg-[#1e5aa8]"
                >
                  <PenLine size={14} /> LƯU THÔNG TIN NGƯỜI NỘP THUẾ
                </button>
              </div>

              {s.importInfo.gnt?.noPayable && (
                <div className="rounded-xl bg-slate-100 border border-slate-300 p-3 text-[13px] text-slate-700">
                  ℹ️ <b>Không có nghĩa vụ thuế:</b> Thuế NK và VAT đều bằng 0 (không cần nộp qua GNT).
                </div>
              )}

              {s.importInfo.gnt?.missing && s.importInfo.gnt.missing.length > 0 && !s.importInfo.gnt.noPayable && (
                <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13px] text-amber-900">
                  ⚠️ <b>Chưa đủ điều kiện tạo GNT:</b> Thiếu {s.importInfo.gnt.missing.join(", ")}. Vui lòng hoàn thiện và lưu ở trên.
                </div>
              )}

              <div className="rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-[12.5px] text-slate-600">
                ℹ️ <i>Cần kiểm tra/hoàn thiện các trường Kho bạc trước khi sử dụng để nộp.</i>
              </div>

              {s.importInfo.gnt?.done && s.importInfo.gnt.document ? (
                <div className="rounded-xl bg-emerald-50 border border-emerald-300 p-3.5 space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-bold text-emerald-900 text-[14px]">✅ GNT đã tạo: {s.importInfo.gnt.document.fileName}</p>
                      <p className="text-[12px] text-emerald-700">Mẫu C1-02/NS (2 sheet) · {s.importInfo.gnt.document.generatedAt ? new Date(s.importInfo.gnt.document.generatedAt).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) : "Vừa tạo"}</p>
                    </div>
                  </div>
                  <div className="flex gap-2 pt-1">
                    {s.importInfo.gnt.document.downloadAvailable ? (
                      <button
                        onClick={downloadGNT}
                        className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-4 min-h-[44px] text-[13.5px]"
                      >
                        <Download size={16} /> TẢI XLSX
                      </button>
                    ) : (
                      <p className="text-[12.5px] text-emerald-800 self-center">Bytes trong phiên trước. Bấm “Tạo lại” để tải.</p>
                    )}
                    <button
                      onClick={generateGNT}
                      disabled={!s.importInfo.gnt?.ready}
                      className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white font-semibold px-3 min-h-[44px] text-[13px]"
                    >
                      <FileSpreadsheet size={15} /> Tạo lại XLSX
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={generateGNT}
                  disabled={!s.importInfo.gnt?.ready}
                  className={cx(
                    "btn-press touch-target w-full rounded-xl font-bold py-2.5 min-h-[46px] flex items-center justify-center gap-2 text-[14.5px]",
                    s.importInfo.gnt?.ready
                      ? "bg-[#0f2a4a] text-white hover:bg-[#1e5aa8]"
                      : "bg-slate-200 text-slate-400 cursor-not-allowed"
                  )}
                >
                  <FileSpreadsheet size={17} /> TẠO GIẤY NỘP THUẾ XLSX
                </button>
              )}
            </section>
          </div>

          <section id="import-delivery-section" className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><Truck size={19} className="text-[#1e5aa8]" /> Xe Việt Nam & giao hàng</h3>
            {(!s.importInfo.driverVN || !s.importInfo.plateVN) && !s.importInfo.delivered && <MissingBox what="chặng xe giao VN" where="Thêm một chặng Truck riêng; không dùng lại xe lấy hàng TQ" actionLabel="Mở chặng vận chuyển" onAction={() => setSp({ tab: "van-tai" })} />}
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Loại xe VN" hint="Đọc từ xe đầu tiên của chặng Truck giao hàng."><input value={s.importInfo.truckVN} readOnly placeholder="Chưa có chặng xe giao" className={inputCls()} /></Field>
              <Field label="Biển số VN" hint="Đọc từ chặng Truck giao hàng; sửa tại tab Vận chuyển."><input value={s.importInfo.plateVN} readOnly placeholder="Chưa có chặng xe giao" className={inputCls()} /></Field>
              <Field label="Tài xế VN" hint="Đọc từ chặng Truck giao hàng; sửa tại tab Vận chuyển."><input value={s.importInfo.driverVN} readOnly placeholder="Chưa có tài xế" className={inputCls()} /></Field>
              <Field label="Lịch giao" hint="Lưu vào ngày giao (2.7.delivery_date) — PXK cần ngày này."><input id="fld-schedule" value={val("schedule", s.importInfo.schedule)} onChange={(e) => set("schedule", e.target.value)} placeholder="VD: 12/09/2026" className={inputCls()} /></Field>
            </div>
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-3.5">
              <p className="text-[12.5px] font-bold uppercase tracking-wide text-slate-400">Địa chỉ giao</p>
              <p className="font-bold text-[15px] mt-0.5">{s.importInfo.deliveryAddr}</p>
              <p className="text-[14px] text-slate-600 mt-1">Người nhận: <b>{s.importInfo.receiver}</b> · {s.importInfo.receiverPhone}</p>
              {s.importInfo.actualDelivery && <p className="text-[14px] text-emerald-700 font-bold mt-1">✅ Đã giao: {s.importInfo.actualDelivery}</p>}
            </div>
            {s.importInfo.delivered ? (
              <div className="rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center">
                <p className="font-extrabold text-[17px] text-emerald-800">✅ ĐÃ GIAO HÀNG XONG</p>
                <p className="text-[13.5px] text-emerald-700">{s.importInfo.actualDelivery} · Sang tab Chứng từ để xuất PXK →</p>
                <button onClick={() => setSp({ tab: "chung-tu" })} className="btn-press touch-target mt-2.5 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]">SANG XUẤT PHIẾU XUẤT KHO <ArrowRight size={17} /></button>
              </div>
            ) : (
              <SuccessBtn onClick={() => setShowDeliver(true)} className="w-full text-[17px] min-h-[56px]">✅ XÁC NHẬN ĐÃ GIAO HÀNG</SuccessBtn>
            )}
          </section>
          </div>
        </div>
      )}

      {/* ============ TAB: FINANCE ============ */}
      {showExistingWork && tab === "tai-chinh" && (
        <div className="space-y-4" id="missing-anchor">
          {/* 1 — DỊCH VỤ & CHI PHÍ THỰC TẾ: what Sale/Support really enter first. */}
          <FinanceActualEntry
            stageContext={workspaceNode?.id}
            shipment={s}
            services={financeServices}
            ccy={ccy}
            dispatch={dispatch}
            toast={toast}
            lastWrites={vm?.lastWrites}
          />
          {/* LOGI_QUOTE_COST_WORKFLOW_UX_01 — Owner working priority: the
              ACTUAL service/cost entry comes FIRST, then the compact actual
              summary, then receivable/payment/payable, and the quote estimate
              last as a small, clearly-labelled reference. No amount, formula,
              writer or RBAC changed — only the reading order and visual weight. */}
          <section className="rounded-2xl bg-white border-2 border-emerald-300 p-4 md:p-5">
              <p className="text-[12px] font-extrabold uppercase tracking-wider text-emerald-700 bg-emerald-100 inline-block rounded-md px-2 py-0.5">Thực tế — đã phát sinh, có chứng từ</p>
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mt-2 mb-2">Doanh thu &amp; chi phí thực tế ({ccy})</h3>
              {s.finance.actual.length === 0 && (
                <p className="text-[14px] text-slate-500">Chưa ghi nhận dòng thực tế nào — doanh thu / chi phí / lợi nhuận thực tế đang <b>chưa xác định</b>, không phải 0.</p>
              )}
              {s.finance.actual.length > 0 && (
                <p className="text-[13.5px] text-slate-500 mb-1">{s.finance.actual.length} dòng dịch vụ đã ghi nhận · tổng hợp theo {ccy}:</p>
              )}
              <StateRow label="Doanh thu thực tế (chưa VAT)" value={<span className="font-bold">{fmtCcy(s.finance.receivableNet, ccy)}</span>} />
              <StateRow label="Chi phí thực tế" value={<span className="font-bold">{fmtCcy(s.finance.payable, ccy)}</span>} />
              {/* ACTUAL PROFIT — from booked actuals only. Never from the quote. */}
              <div className="mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-3">
                <p className="text-[12px] font-extrabold uppercase tracking-wider text-emerald-700">Lợi nhuận thực tế</p>
                <div className="grid grid-cols-2 gap-2 mt-1.5 text-center">
                  <div><p className="text-[12px] text-slate-500 font-semibold">Lãi / Lỗ thực tế</p>
                    <p className={cx("font-extrabold text-[17px]", s.finance.profit == null ? "text-slate-400" : s.finance.profit < 0 ? "text-red-700" : "text-emerald-700")}>{fmtCcy(s.finance.profit, ccy)}</p></div>
                  <div><p className="text-[12px] text-slate-500 font-semibold">Biên lợi nhuận</p>
                    <p className={cx("font-extrabold text-[17px]", s.finance.profitMargin == null ? "text-slate-400" : s.finance.profitMargin < 0 ? "text-red-700" : "text-emerald-700")}>{fmtPct(s.finance.profitMargin)}</p></div>
                </div>
                <p className="text-[12.5px] text-slate-500 mt-2">
                  = Doanh thu thực tế − chi phí thực tế − hoa hồng. Không gồm VAT đầu ra. Không lấy số báo giá để bù chỗ trống.
                </p>
              </div>
              <p className="text-[12.5px] text-slate-400 mt-2">
                Chi tiết từng dịch vụ (mã phí · SL · đơn vị · giá vốn · giá bán · VAT · ghi chú) và nút SỬA nằm ở mục
                “DỊCH VỤ &amp; CHI PHÍ THỰC TẾ” phía trên.
              </p>
          </section>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-2"><Wallet size={19} className="text-emerald-600" /> Phải thu khách hàng ({ccy})</h3>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl bg-slate-50 border p-3"><p className="text-[12px] text-slate-500 font-semibold">Phải thu</p><p className="font-extrabold text-[16px] md:text-[18px]">{fmtMillionsCcy(s.finance.receivable, ccy)}</p></div>
                <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3"><p className="text-[12px] text-emerald-700 font-semibold">Đã thu</p><p className="font-extrabold text-[16px] md:text-[18px] text-emerald-700">{fmtMillionsCcy(s.finance.received, ccy)}</p></div>
                <div className="rounded-xl bg-red-50 border border-red-200 p-3"><p className="text-[12px] text-red-600 font-semibold">Còn phải thu</p><p className="font-extrabold text-[16px] md:text-[18px] text-red-700">{fmtMillionsCcy(s.finance.outstanding, ccy)}</p></div>
              </div>
              <p className="text-[12.5px] text-slate-400 mt-2">Phải thu = doanh thu thực tế + VAT đầu ra. Còn phải thu = phải thu − đã thu, do backend tính.</p>
              <button onClick={openPay} className="btn-press touch-target mt-3 w-full rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">＋ GHI NHẬN THANH TOÁN</button>
            </section>
            <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-2">Phải trả đối tác ({ccy})</h3>
              {/* C2B — the selected partner + payable/paid/remaining come from the
                  canonical ledger block (finance.partner), never from client math.
                  UNKNOWN stays “—”; a true zero from the ledger stays 0. */}
              {(() => {
                const partner = s.finance.partner;
                const partnerId = partner?.partnerId ?? "";
                const partnerName = partner?.partnerName;
                const suggested = partner?.suggested === true;
                return (
                  <>
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="text-[12px] text-slate-500 font-semibold">Đối tác:</span>
                      {partnerName ? (
                        <span className="inline-flex items-center gap-1.5 text-[13.5px] font-extrabold text-[#0f2a4a]">
                          <Building2 size={15} className="text-[#1e5aa8]" /> {partnerName}
                          <span className="text-[11.5px] font-bold text-slate-400">{partnerId}</span>
                          {suggested && <span className="text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">đề xuất từ danh mục</span>}
                        </span>
                      ) : (
                        <span className="text-[13.5px] font-bold text-slate-400">—</span>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="rounded-xl bg-slate-50 border p-3"><p className="text-[12px] text-slate-500 font-semibold">Phải trả</p><p className="font-extrabold text-[16px] md:text-[18px]">{fmtMillionsCcy(partner?.payable ?? null, ccy)}</p></div>
                      <div className="rounded-xl bg-blue-50 border border-blue-200 p-3"><p className="text-[12px] text-blue-700 font-semibold">Đã trả</p><p className="font-extrabold text-[16px] md:text-[18px] text-blue-700">{fmtMillionsCcy(partner?.paid ?? null, ccy)}</p></div>
                      <div className="rounded-xl bg-amber-50 border border-amber-200 p-3"><p className="text-[12px] text-amber-700 font-semibold">Còn phải trả</p><p className="font-extrabold text-[16px] md:text-[18px] text-amber-800">{fmtMillionsCcy(partner?.remaining ?? null, ccy)}</p></div>
                    </div>
                  </>
                );
              })()}
              {/* UNKNOWN != ZERO: before any canonical payable/payment record the
                  figures above stay an em dash — they are never shown as 0. Once
                  the ledger has rows, mọi số đều do backend đọc ra. */}
              <p className="text-[12.5px] text-slate-400 mt-2">Phải trả / đã trả / còn lại đọc từ sổ tài chính canonical (nghĩa vụ + thanh toán + phân bổ) theo lô này. Chưa có sổ ⇒ “—”, không suy ra 0. Đơn vị: {ccy} — không quy đổi.</p>

              {/* Payment history — canonical transactions bound to this shipment. */}
              {(s.finance.partner?.payments?.length ?? 0) > 0 && (
                <div className="mt-3">
                  <p className="text-[12px] font-extrabold uppercase tracking-wider text-slate-500 mb-1.5">Lịch sử trả đối tác</p>
                  <div className="space-y-1.5">
                    {s.finance.partner!.payments.map((p, i) => (
                      <div key={p.id || i} className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 p-2.5">
                        <span className="text-[12px] font-bold text-slate-400 w-[80px]">{p.date || "—"}</span>
                        <span className="flex-1 min-w-[140px] text-[12.5px] text-slate-600">{p.note || p.kind}{p.requestId ? ` · ${p.requestId}` : ""}</span>
                        <span className="font-extrabold text-[14.5px]">{fmtMoney(p.amount, p.ccy)} <span className="text-[11px] text-slate-400">{p.ccy}</span></span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* C2B write actions — SAME typed-event contract as receipts:
                  typed event → Python dispatcher → RBAC → canonical writer →
                  audit → fresh backend read. Frontend visibility is NOT
                  authorization; a denied role only sees the backend's refusal.
                  The intent id is minted with the amount draft and held for that
                  one intent (re-click replays the SAME id → idempotent). */}
              <div className="mt-3 rounded-xl border border-slate-200 p-3">
                <p className="text-[13px] font-extrabold text-[#0f2a4a] mb-2">Ghi nhận phải trả & thanh toán đối tác</p>
                <Field label={`Số tiền (${ccy})`} hint="Ví dụ: 20.000.000 — để trống là UNKNOWN, không tự thành 0">
                  <input value={partnerAmt} disabled={!!partnerPending.obl || !!partnerPending.pay} onChange={(e) => { setPartnerAmt(e.target.value); mintPartnerObl(); mintPartnerPay(); }} inputMode="numeric" placeholder="VD: 20000000" className={inputCls()} />
                </Field>
                {partnerPending.obl && <p role="status" data-testid="partner-payable-pending" className="mt-2 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13px] font-semibold text-blue-800">⏳ ĐANG CHỜ BACKEND XÁC NHẬN (phải trả)…</p>}
                {partnerPending.pay && <p role="status" data-testid="partner-payment-pending" className="mt-2 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13px] font-semibold text-blue-800">⏳ ĐANG CHỜ BACKEND XÁC NHẬN (thanh toán)…</p>}
                {partnerError.obl && <p role="alert" className="mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700">{partnerError.obl}</p>}
                {partnerError.pay && <p role="alert" className="mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700">{partnerError.pay}</p>}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2.5">
                  <GhostBtn onClick={recordPartnerPayable} disabled={!!partnerPending.obl} testId="partner-payable-submit" className="min-h-[48px]">{partnerPending.obl ? "⏳ ĐANG CHỜ…" : "📌 GHI NHẬN PHẢI TRẢ"}</GhostBtn>
                  <PrimaryBtn onClick={recordPartnerPayment} disabled={!!partnerPending.pay} testId="partner-payment-submit" className="min-h-[48px]">{partnerPending.pay ? "⏳ ĐANG CHỜ…" : "💸 TRẢ ĐỐI TÁC"}</PrimaryBtn>
                </div>
              </div>

              <Link to="/tai-chinh/doi-soat" className="btn-press touch-target mt-3 w-full rounded-xl border-2 border-slate-200 font-bold min-h-[52px] flex items-center justify-center">MỞ ĐỐI SOÁT</Link>
            </section>
          </div>
          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-3">Lịch sử thu / chi — sửa bằng điều chỉnh, không xóa</h3>
            <div className="space-y-2">
              {s.finance.payments.map((p, i) => (
                // "Đã hoàn tác" comes ONLY from the backend projection's
                // `reversed` flag (is_reversed / status on the stored row) —
                // never a client-side guess. The action button stays visible
                // to every role; authorization is enforced in the writer.
                <div key={p.id || i} data-payment-row={p.id || undefined} className={cx("flex flex-wrap items-center gap-2 rounded-xl border p-3", p.reversed ? "border-slate-200 bg-slate-50/80" : "border-slate-200")}>
                  <span className="text-[12.5px] font-bold text-slate-400 w-[92px]">{p.date}</span>
                  <span className="flex-1 min-w-[160px]">
                    <span className="block font-bold text-[14.5px]">{p.kind}{p.reversed && <span className="ml-2 align-middle rounded-full bg-slate-200 text-slate-600 text-[11px] font-extrabold px-2 py-0.5">Đã hoàn tác</span>}</span>
                    <span className="block text-[12.5px] text-slate-500">{p.by}{p.note ? " · " + p.note : ""}{p.id ? " · " + p.id : ""}</span>
                  </span>
                  <span className={cx("font-extrabold text-[15.5px]", p.reversed && "text-slate-400 line-through")}>{fmtMoney(p.amount, p.ccy)} <span className="text-[11.5px] text-slate-400">{p.ccy}</span></span>
                  {p.reversed
                    ? <span className="text-[12.5px] font-semibold text-slate-400 px-3">Đã điều chỉnh — khóa</span>
                    : p.id
                      ? <button onClick={() => openCorrection(p)} className="touch-target text-[13px] font-bold text-[#1e5aa8] border border-slate-200 rounded-lg px-3 min-h-[40px]" data-payment-id={p.id}>Điều chỉnh</button>
                      : <span className="text-[12px] font-semibold text-amber-700 px-2" title="Khoản thu legacy không có mã — backend không có đối tượng để liên kết correction.">chưa có mã khoản thu</span>}
                </div>
              ))}
            </div>
          </section>

          {/* 4 — QUOTE ESTIMATE: a small, subdued, collapsible REFERENCE at the
              bottom. Still clearly labelled ESTIMATE, still per-currency, and
              the numbers/derivations are byte-for-byte the ones the backend
              already projected — only the visual weight and position changed. */}
          <details className="rounded-xl border border-dashed border-violet-300 bg-violet-50/40 px-3.5 py-2.5" data-testid="quote-estimate-compact">
            <summary className="cursor-pointer list-none flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-violet-700 bg-violet-100 rounded-md px-2 py-0.5">
                Báo giá / Dự kiến — chưa phải số thực thu/chi
              </span>
              <span className="text-[12.5px] font-bold text-slate-600">Chi phí dự kiến theo báo giá</span>
              <span className="text-[12.5px] text-slate-500">
                {s.finance.quote.length > 0 ? `${s.finance.quote.length} dòng dự kiến` : "Chưa gắn báo giá"} · bấm để xem
              </span>
            </summary>
            <div className="mt-2">
              {s.finance.quote.length === 0 && (
                <p className="text-[13px] text-slate-500">Chưa gắn báo giá. <Link to="/kinh-doanh-bao-gia" className="font-bold text-[#1e5aa8]">Mở báo giá →</Link></p>
              )}
              {s.finance.quote.map((c) => (
                <StateRow key={c.label} label={c.label} value={<span className="font-bold text-[14px]">{fmtMoney(c.amount, c.ccy)} <span className="text-[11.5px] font-bold text-violet-600">{c.ccy}</span></span>} />
              ))}
              <p className="text-[12px] text-slate-400 mt-1.5">Mỗi đồng tiền ghi rõ VND / USD / CNY — không gộp chung. Đây là ESTIMATE, không phải Finance Actual.</p>
            </div>
          </details>
        </div>
      )}

      {/* ============ TAB: DOCS ============ */}
      {showExistingWork && tab === "chung-tu" && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <section
            className="xl:col-span-2 rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-5"
            data-testid="shipment-commercial-flow"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="font-extrabold text-[17px] text-[#0f2a4a]">Hình thức nhập khẩu</h3>
                <p className="text-[13px] text-slate-500 mt-0.5">
                  Chọn đúng pháp nhân đứng nhập khẩu. Hệ thống dùng lựa chọn này để bật/tắt đúng bộ chứng từ; không tự đoán.
                </p>
              </div>
              {s.commercialFlow?.confirmed && (
                <span className="rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 px-3 py-1 text-[12.5px] font-extrabold">
                  ✓ ĐÃ XÁC NHẬN
                </span>
              )}
            </div>

            <div className="grid md:grid-cols-3 gap-2.5 mt-4">
              {[
                ["CUSTOMER_SELF", "Khách hàng tự nhập", "HĐ vận chuyển · PXK Trường Thành không áp dụng"],
                ["TT_ENTRUSTED_DIRECT", "Trường Thành nhận ủy thác", "Trường Thành trực tiếp đứng tên nhập khẩu"],
                ["TT_ENTRUSTED_SUB", "Ủy thác tiếp qua đối tác", "Ví dụ Phú Anh đứng nhập khẩu hộ Trường Thành"],
              ].map(([mode, title, desc]) => (
                <label
                  key={mode}
                  className={cx(
                    "cursor-pointer rounded-xl border-2 p-3 min-h-[94px] flex gap-2.5",
                    flowModeDraft === mode ? "border-[#1e5aa8] bg-blue-50/60" : "border-slate-200 bg-white"
                  )}
                >
                  <input
                    type="radio"
                    name="commercial-flow"
                    value={mode}
                    checked={flowModeDraft === mode}
                    disabled={!!flowPending}
                    onChange={() => {
                      setFlowModeDraft(mode);
                      setFlowError("");
                      if (mode !== "TT_ENTRUSTED_SUB") setFlowAgentDraft("");
                    }}
                    className="mt-1 h-5 w-5 accent-[#0f2a4a] shrink-0"
                  />
                  <span>
                    <span className="block font-extrabold text-[14.5px] text-[#0f2a4a]">{title}</span>
                    <span className="block text-[12.5px] text-slate-500 mt-1">{desc}</span>
                  </span>
                </label>
              ))}
            </div>

            {flowModeDraft === "TT_ENTRUSTED_SUB" && (
              <div className="mt-3 grid md:grid-cols-2 gap-3">
                <Field label="Đơn vị đứng nhập khẩu hộ" required={!flowAgentDraft}>
                  <select
                    value={flowAgentDraft}
                    disabled={!!flowPending}
                    onChange={(e) => { setFlowAgentDraft(e.target.value); setFlowError(""); }}
                    className={inputCls(!flowAgentDraft ? "missing" : "ok")}
                  >
                    <option value="">— Chọn đối tác —</option>
                    {authorityAgents.map((agent) => (
                      <option key={agent.id} value={agent.id}>{agent.legalName || agent.id}</option>
                    ))}
                  </select>
                </Field>
                <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                  <p className="text-[12px] font-bold uppercase tracking-wide text-slate-400">Pháp nhân dự kiến đứng nhập khẩu</p>
                  <p className="font-extrabold text-[14.5px] text-[#0f2a4a] mt-1">{selectedFlowAgent?.legalName || "Chưa chọn"}</p>
                  <p className="text-[12.5px] text-slate-500">MST: {selectedFlowAgent?.legalCode || "—"}</p>
                </div>
              </div>
            )}

            {(flowModeDraft === "TT_ENTRUSTED_DIRECT" || flowModeDraft === "TT_ENTRUSTED_SUB") && authorityCompanies.length > 1 && (
              <div className="mt-3 max-w-[560px]">
                <Field
                  label={flowModeDraft === "TT_ENTRUSTED_SUB" ? "Pháp nhân Trường Thành ký với đối tác" : "Pháp nhân Trường Thành đứng nhập khẩu"}
                  required={!flowCompanyDraft}
                >
                  <select
                    value={flowCompanyDraft}
                    disabled={!!flowPending}
                    onChange={(e) => { setFlowCompanyDraft(e.target.value); setFlowError(""); }}
                    className={inputCls(!flowCompanyDraft ? "missing" : "ok")}
                  >
                    <option value="">— Chọn pháp nhân —</option>
                    {authorityCompanies.map((company) => (
                      <option key={company.id} value={company.id}>{company.legalName || company.id}</option>
                    ))}
                  </select>
                </Field>
              </div>
            )}

            {s.commercialFlow?.confirmed && (
              <div className="mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-3">
                <p className="text-[12px] font-bold uppercase tracking-wide text-emerald-700">Người đứng tên nhập khẩu hiện tại</p>
                <p className="font-extrabold text-[15px] text-emerald-900 mt-0.5">
                  {s.commercialFlow.legalImporterName || "Thiếu hồ sơ pháp lý"}
                </p>
                <p className="text-[12.5px] text-emerald-800">MST: {s.commercialFlow.legalImporterTaxCode || "—"}</p>
                {(s.commercialFlow.missing ?? []).length > 0 && (
                  <p className="text-[12.5px] font-semibold text-amber-800 mt-1">
                    Cần bổ sung: {(s.commercialFlow.missing ?? []).join(" · ")}
                  </p>
                )}
              </div>
            )}

            {(flowModeDraft === "TT_ENTRUSTED_DIRECT" || flowModeDraft === "TT_ENTRUSTED_SUB") && authorityCompanies.length === 1 && (
              <p className="mt-2 text-[12.5px] text-slate-500">
                Pháp nhân Trường Thành: <b>{selectedFlowCompany?.legalName || authorityCompanies[0]?.legalName}</b>
              </p>
            )}
            {flowError && <p role="alert" className="mt-3 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700">{flowError}</p>}
            <PrimaryBtn onClick={saveCommercialFlow} disabled={!!flowPending} className="mt-3 min-w-[220px]">
              {flowPending ? "ĐANG LƯU…" : "XÁC NHẬN HÌNH THỨC NHẬP KHẨU"}
            </PrimaryBtn>
          </section>

          {pickerPolicy && (
            <ShipmentDocumentPicker
              shipmentId={s.id}
              cards={shipmentDocumentCards}
              selection={{
                catalog: pickerPolicy.catalog ?? [],
                savedIds: persistedDocumentIds,
                draftIds: documentSelectionDraftIds,
                canEdit: pickerPolicy.canSaveSelection === true,
                storageConfigured: pickerPolicy.storageConfigured === true,
                open: documentSelectionOpen,
                pending: Boolean(documentSelectionPending),
                error: documentSelectionError,
                onOpen: openDocumentSelection,
                onClose: closeDocumentSelection,
                onDraftChange: setDocumentSelectionDraftIds,
                onSave: saveDocumentSelection,
              }}
              onAction={handleDocumentAction}
              onDownload={downloadDocumentHistory}
            />
          )}

          <section className="xl:col-span-2 rounded-2xl bg-white border border-slate-200 p-4 md:p-5" data-testid="shipment-document-workflow">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="font-extrabold text-[17px] text-[#0f2a4a]">Vòng đời hồ sơ lô hàng</h3>
                <p className="text-[13px] text-slate-500">
                  Báo giá → hợp đồng → tiền/thuế → giao hàng → kho → quyết toán. Bước không áp dụng vẫn hiện để giải thích, nhưng không tính vào mẫu số tiến độ.
                </p>
              </div>
              {s.documentWorkflow && (
                <div className="flex flex-wrap gap-1.5 text-[12px] font-extrabold">
                  <span className="rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 px-2.5 py-1">
                    {s.documentWorkflow.summary.complete}/{s.documentWorkflow.summary.total} hoàn tất
                  </span>
                  <span className="rounded-full bg-blue-50 border border-blue-200 text-blue-800 px-2.5 py-1">
                    {s.documentWorkflow.summary.ready} sẵn sàng
                  </span>
                  <span className="rounded-full bg-amber-50 border border-amber-200 text-amber-900 px-2.5 py-1">
                    {s.documentWorkflow.summary.attention} cần xử lý
                  </span>
                </div>
              )}
            </div>

            <div className="mt-4 space-y-2">
              {(s.documentWorkflow?.steps ?? []).map((step, index) => (
                <div key={step.id} className="rounded-xl border border-slate-200 p-3 flex flex-col md:flex-row md:items-center gap-2.5">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <span className="w-8 h-8 rounded-full bg-[#0f2a4a] text-white grid place-items-center font-extrabold text-[13px] shrink-0">
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-extrabold text-[14.5px] text-[#0f2a4a]">{step.label}</p>
                        <span className={cx("rounded-full border px-2 py-0.5 text-[11.5px] font-extrabold", workflowStateClass(step.state))}>
                          {step.stateLabel}
                        </span>
                      </div>
                      <p className="text-[12.8px] text-slate-500 mt-0.5">{step.reason}</p>
                    </div>
                  </div>
                  {step.targetRoute && step.actionLabel ? (
                    <Link to={step.targetRoute} className="btn-press touch-target shrink-0 inline-flex items-center justify-center rounded-lg border-2 border-slate-200 px-3 min-h-[44px] text-[13px] font-bold">
                      {step.actionLabel}
                    </Link>
                  ) : step.targetTab && step.actionLabel ? (
                    <button
                      type="button"
                      onClick={() => setSp({ tab: step.targetTab })}
                      className="btn-press touch-target shrink-0 rounded-lg border-2 border-slate-200 px-3 min-h-[44px] text-[13px] font-bold"
                    >
                      {step.actionLabel}
                    </button>
                  ) : null}
                </div>
              ))}
              {!s.documentWorkflow && (
                <p className="text-[13.5px] text-slate-500">Workflow chưa có trong payload hiện tại.</p>
              )}
            </div>
          </section>

          <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3"><FileText size={19} className="text-[#1e5aa8]" /> Hợp đồng / docgen liên kết hiện có</h3>
            {linkedContract ? (
              <div className="rounded-xl border-2 border-slate-200 p-4">
                <div className="flex flex-wrap items-center gap-2"><span className="font-extrabold text-[17px] text-[#0f2a4a]">{linkedContract.id}</span><ToneBadge tone={linkedContract.statusTone} size="sm">{linkedContract.status}</ToneBadge></div>
                <p className="text-[14px] text-slate-600 mt-1">{linkedContract.companyLegal} · Giá trị {fmtVND(linkedContract.value ?? s.finance.receivable)}</p>
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <Link to={contractPath(linkedContract.id)} className="btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] min-h-[48px]"><Eye size={16} /> MỞ HỢP ĐỒNG</Link>
                  {/* P1-B — now COMPLETED, unblocked by PR #52.

                      This used to call setSp({tab:"chung-tu"}), which only
                      re-selected the SHIPMENT's own documents tab the employee
                      already stood on; the contract's HDNT/PL/HDMB workdesk
                      never opened.

                      It now reaches that existing workdesk through PR52's
                      shared contractPath helper — no second encoder, no new
                      router, no new document UI. That helper percent-encodes
                      the contract number as ONE route segment, so slash ids
                      (05/2026/HDMB) reach /hop-dong/:id instead of the "*"
                      wildcard; "?tab=chung-tu" is read by ContractDetail's
                      existing useSearchParams tab mechanism. */}
                  <Link to={contractPath(linkedContract.id) + "?tab=chung-tu"} onClick={() => toast("Chứng từ hợp đồng " + linkedContract.id, "Mở workdesk chứng từ HDNT/PL/HDMB của hợp đồng (core.docgen).", "blue")} className="btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] min-h-[48px]"><FileDown size={16} /> MỞ CHỨNG TỪ</Link>
                </div>
              </div>
            ) : <p className="text-slate-500 text-[14px]">Lô chưa gắn hợp đồng. <Link to="/hop-dong" className="font-bold text-[#1e5aa8]">Chọn hợp đồng →</Link></p>}
            <div className="mt-4">
              <h4 className="font-bold text-[14.5px] mb-2">Chứng từ lô hàng — hiện trạng & bổ sung</h4>
              <div className="space-y-2">
                {s.docs.map((d) => (
                  <div key={d.name} className="flex items-center gap-2.5 rounded-xl border border-slate-200 p-2.5">
                    <span className={cx("w-7 h-7 rounded-full grid place-items-center text-[13px] font-extrabold", d.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white")}>{d.ok ? "✓" : "!"}</span>
                    <span className="flex-1 font-semibold text-[14px]">{d.name} — {d.ok ? <span className="text-emerald-700">Đã đủ</span> : <span className="text-amber-800">Thiếu</span>}</span>
                    {!d.ok && <button onClick={() => { setSp({ tab: missingTarget(d.name) }); toast("Mở tab bổ sung", "Đi tới ô nhập liệu thật cho " + d.name + ".", "blue"); }} className="btn-press touch-target shrink-0 inline-flex items-center gap-1 rounded-lg bg-amber-500 text-white text-[13px] font-bold px-3 min-h-[44px]"><PenLine size={14} /> Bổ sung</button>}
                  </div>
                ))}
              </div>
            </div>
          </section>

          {s.commercialFlow?.mode === "CUSTOMER_SELF" ? (
            <section className={cx(
              "rounded-2xl border-2 p-4 md:p-5",
              s.pxk.done ? "bg-amber-50 border-amber-300" : "bg-slate-50 border-slate-200"
            )}>
              <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-1">Phiếu xuất kho (PXK)</h3>
              {s.pxk.done ? (
                <>
                  <p className="text-[13.5px] text-amber-900">
                    <b>Có PXK lịch sử từ mô hình trước.</b> Hệ thống giữ nguyên để kiểm toán nhưng không cho sinh bản PXK mới khi khách hàng tự đứng tên nhập khẩu.
                  </p>
                  <p className="text-[12.8px] text-amber-800 mt-1">
                    {s.pxk.document?.fileName || s.pxk.number || "PXK"} · bản R{s.pxk.document?.revision ?? 1} · {s.pxk.document?.status || "GENERATED"}
                  </p>
                  {s.pxk.document?.downloadAvailable && (
                    <button onClick={downloadPxk} className="btn-press touch-target mt-2 inline-flex items-center gap-1.5 rounded-xl border-2 border-amber-500 text-amber-900 font-bold px-4 min-h-[46px]">
                      <Download size={16} /> TẢI BẢN LỊCH SỬ
                    </button>
                  )}
                </>
              ) : (
                <p className="text-[13.5px] text-slate-600">
                  <b>Không áp dụng.</b> Khách hàng tự đứng tên nhập khẩu nên workflow không yêu cầu Phiếu xuất kho của Trường Thành cho lô này.
                </p>
              )}
            </section>
          ) : !s.commercialFlow?.confirmed ? (
            <section className="rounded-2xl bg-amber-50 border-2 border-amber-200 p-4 md:p-5">
              <h3 className="font-extrabold text-[16.5px] text-amber-900 mb-1">Phiếu xuất kho (PXK) — đang khóa</h3>
              <p className="text-[13.5px] text-amber-800">
                Xác nhận <b>Hình thức nhập khẩu</b> ở đầu tab trước. Backend cũng từ chối tạo PXK cho tới khi mô hình được xác nhận.
              </p>
              {s.pxk.done && (
                <p className="text-[12.8px] font-semibold text-amber-900 mt-2">
                  PXK lịch sử {s.pxk.document?.fileName || s.pxk.number || ""} vẫn được giữ; xác nhận mô hình để hệ thống đánh giá tính phù hợp, không xóa lịch sử.
                </p>
              )}
            </section>
          ) : (
          <section className="rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-5">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-1">Phiếu xuất kho (PXK) — theo từng lô</h3>
            <p className="text-[13px] text-slate-500 mb-3">PXK gắn với lô đã giao, nguồn từ {s.pxk.source || s.contract}. Mỗi lô 1 PXK riêng.</p>
            {!s.importInfo.delivered && <MissingBox what="xác nhận đã giao hàng" where="Phải giao xong mới được xuất PXK" actionLabel="Sang xác nhận giao" onAction={() => setSp({ tab: "nhap" })} />}
            <div className="grid sm:grid-cols-2 gap-3 mt-3">
              {/* Số PXK / Ngày PXK are the lot's OWN legal identity: core.docgen
                  refuses to invent them, so they are operator inputs here (same
                  as the authoritative docgen desk) and sent with the request. */}
              <Field label="Số PXK" required={!s.pxk.number} hint="Số pháp lý của phiếu — backend không tự đặt.">
                <input id="fld-pxkno" value={val("pxkNo", s.pxk.number ?? "")} onChange={(e) => set("pxkNo", e.target.value)} placeholder="VD: PXK-2026-0308" className={inputCls(!val("pxkNo", s.pxk.number ?? "") ? "missing" : "ok")} />
              </Field>
              <Field label="Ngày PXK" required={!s.pxk.date} hint="DD/MM/YYYY hoặc YYYY-MM-DD.">
                <input id="fld-pxkdate" value={val("pxkDate", s.pxk.date ?? "")} onChange={(e) => set("pxkDate", e.target.value)} placeholder="VD: 11/09/2026" className={inputCls(!val("pxkDate", s.pxk.date ?? "") ? "missing" : "ok")} />
              </Field>
              <Field label="Địa điểm nhận" required={!s.pxk.place} hint="Lưu vào 2.7.delivery_location — PXK bị chặn nếu thiếu.">
                <input id="fld-pxplace" value={val("pxPlace", s.pxk.place || s.importInfo.deliveryAddr || "")} onChange={(e) => set("pxPlace", e.target.value)} placeholder="Kho / địa chỉ nhận thực tế" className={inputCls(!val("pxPlace", s.pxk.place || s.importInfo.deliveryAddr || "") ? "missing" : "ok")} />
              </Field>
              <Field label="Người nhận" required={!s.pxk.receiver} hint="Lưu vào 2.7.receiver_name.">
                <input id="fld-pxreceiver" value={val("pxReceiver", s.pxk.receiver || s.importInfo.receiver || "")} onChange={(e) => set("pxReceiver", e.target.value)} placeholder="Tên người nhận" className={inputCls(!val("pxReceiver", s.pxk.receiver || s.importInfo.receiver || "") ? "missing" : "ok")} />
              </Field>
              <Field label="Chức vụ người nhận" required={!s.pxk.role} hint="Lưu vào 2.7.receiver_title.">
                <input id="fld-pxrole" value={val("pxRole", s.pxk.role ?? "")} onChange={(e) => set("pxRole", e.target.value)} placeholder="Theo giấy giới thiệu" className={inputCls(!val("pxRole", s.pxk.role ?? "") ? "missing" : "ok")} />
              </Field>
              <Field label="Ngày giao" hint="Lưu vào 2.7.delivery_date — PXK cần ngày này.">
                <input id="fld-pxdate" value={val("pxDate", s.importInfo.schedule ?? "")} onChange={(e) => set("pxDate", e.target.value)} placeholder="VD: 12/09/2026" className={inputCls()} />
              </Field>
              <Field label="Nguồn (HDMB/PL)" hint="Từ hợp đồng đã liên kết với lô — liên kết ở màn Hợp đồng.">
                <input value={s.pxk.source || s.contract} readOnly placeholder="Chưa liên kết chứng từ nguồn" className={inputCls()} />
              </Field>
            </div>
            <PrimaryBtn onClick={savePxFacts} className="w-full mt-3">💾 LƯU THÔNG TIN GIAO NHẬN</PrimaryBtn>
            {(s.pxk.missingDeliveryFacts ?? []).length > 0 && (
              <MissingBox what={(s.pxk.missingDeliveryFacts ?? []).join(" · ")} where="core.docgen chặn PXK đến khi đủ thông tin giao nhận" actionLabel="Nhập ở trên" onAction={() => document.getElementById("fld-pxplace")?.focus()} />
            )}
            <div className="mt-3 rounded-xl bg-slate-50 border p-3 text-[13.5px]">
              <p>Đã giao hàng xong: <b className={s.importInfo.delivered ? "text-emerald-700" : "text-red-600"}>{s.importInfo.delivered ? "✅ Rồi — " + s.importInfo.actualDelivery : "❌ Chưa"}</b></p>
              <p>Ngày giao: <b>{s.importInfo.actualDelivery || s.importInfo.schedule}</b></p>
            </div>
            {s.pxk.done ? (
              <div className="mt-3 rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center">
                <p className="font-extrabold text-emerald-800">✅ ĐÃ XUẤT {s.pxk.number}</p>
                {/* Real readback of the generated document: file, revision,
                    status and who generated it — not a decorative checkmark. */}
                <p className="text-[13.5px] text-emerald-700 mt-0.5">
                  {s.pxk.document?.fileName || "PXK"} · bản R{s.pxk.document?.revision ?? 1} · {s.pxk.document?.status || "GENERATED"}
                  {s.pxk.document?.generatedBy ? " · " + s.pxk.document.generatedBy : ""}
                </p>
                {s.pxk.document?.downloadAvailable ? (
                  <button onClick={downloadPxk} className="btn-press touch-target mt-2 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]"><Download size={17} /> TẢI {s.pxk.document?.fileName || "PXK"}</button>
                ) : (
                  <p className="text-[13px] text-emerald-800 mt-2">File sinh ở phiên trước: metadata còn trên backend, bytes chỉ giữ trong phiên đã sinh — bấm “SINH BẢN MỚI” để có file tải.</p>
                )}
                <button onClick={exportPXK} className="btn-press touch-target mt-2 ml-2 inline-flex items-center gap-1.5 rounded-xl border-2 border-emerald-600 text-emerald-800 font-bold px-5 min-h-[48px]"><FileDown size={17} /> SINH BẢN MỚI (R+1)</button>
              </div>
            ) : (
              <SuccessBtn onClick={exportPXK} className="w-full mt-3 text-[16px] min-h-[56px]">🖨 XUẤT PHIẾU XUẤT KHO</SuccessBtn>
            )}
          </section>
          )}
          {/* Issue #168 — FORM_07 Biên bản giao nhận: the SAME chung-tu surface
              pattern PXK uses. Canonical facts (parties, delivery, goods) are
              server-bound and read-only here; the operator types only the two
              values no canonical source owns (Số biên bản, Ngày đơn đặt hàng). */}
          {s.form07 && (
          <section className="rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-5" data-testid="shipment-form07-panel">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-1">Biên bản giao nhận (FORM_07)</h3>
            <p className="text-[13px] text-slate-500 mb-3">
              DOCX sinh từ mẫu Owner đã làm sạch (SHA-256 đã ghim). Nguồn hàng hóa: {s.form07.source || s.contract || "chưa liên kết hợp đồng"}. Hai bên, người nhận và ngày giao lấy từ dữ liệu canonical — không nhập tay.
            </p>
            {!s.form07.delivered && <MissingBox what="xác nhận đã giao hàng" where="Biên bản giao nhận chỉ tạo sau khi lô đã giao thực tế" actionLabel="Sang xác nhận giao" onAction={() => setSp({ tab: "nhap" })} />}
            <div className="grid sm:grid-cols-2 gap-3 mt-3">
              <Field label="Số biên bản" required={!s.form07.number} hint="Số pháp lý của biên bản — backend không tự đặt.">
                <input id="fld-form07no" value={val("form07No", s.form07.number ?? "")} onChange={(e) => set("form07No", e.target.value)} placeholder="VD: BBGN-2026-001" className={inputCls(!val("form07No", s.form07.number ?? "") ? "missing" : "ok")} />
              </Field>
              <Field label="Ngày đơn đặt hàng" required={!s.form07.orderDate} hint="DD/MM/YYYY — in vào 'Căn cứ Đơn đặt hàng ngày…'.">
                <input id="fld-form07orderdate" value={val("form07OrderDate", s.form07.orderDate ?? "")} onChange={(e) => set("form07OrderDate", e.target.value)} placeholder="VD: 25/09/2026" className={inputCls(!val("form07OrderDate", s.form07.orderDate ?? "") ? "missing" : "ok")} />
              </Field>
            </div>
            {(s.form07.readiness?.missing ?? []).length > 0 && (
              <MissingBox what={(s.form07.readiness?.missing ?? []).join(" · ")} where="core.docgen.form07 chặn đến khi đủ thông tin" actionLabel="Nhập ở trên" onAction={() => document.getElementById("fld-form07no")?.focus()} />
            )}
            {s.form07.done ? (
              <div className="mt-3 rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center" data-testid="form07-done">
                <p className="font-extrabold text-emerald-800">✅ ĐÃ TẠO {s.form07.number}</p>
                <p className="text-[13.5px] text-emerald-700 mt-0.5">
                  {s.form07.document?.fileName || "FORM_07"} · bản R{s.form07.document?.revision ?? 1} · {s.form07.document?.status || "GENERATED"}
                  {s.form07.document?.generatedBy ? " · " + s.form07.document.generatedBy : ""}
                </p>
                {s.form07.document?.downloadBase64 ? (
                  <button onClick={downloadForm07} className="btn-press touch-target mt-2 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]"><Download size={17} /> TẢI {s.form07.document?.fileName || "FORM_07"}</button>
                ) : (
                  <p className="text-[13px] text-emerald-800 mt-2">File sinh ở phiên trước: metadata còn trên backend — tải đúng bytes đã lưu qua lịch sử ở thẻ “Biểu mẫu &amp; chứng từ”.</p>
                )}
                <button onClick={exportFORM07} className="btn-press touch-target mt-2 ml-2 inline-flex items-center gap-1.5 rounded-xl border-2 border-emerald-600 text-emerald-800 font-bold px-5 min-h-[48px]"><FileDown size={17} /> SINH BẢN MỚI (R+1)</button>
              </div>
            ) : (
              <SuccessBtn onClick={exportFORM07} className="w-full mt-3 text-[16px] min-h-[56px]">🖨 TẠO BIÊN BẢN GIAO NHẬN</SuccessBtn>
            )}
          </section>
          )}
          {/* LOGI-193 — Admin-published Office templates this lot selected.
              Every filled value is server-bound from verified facts; the ONLY
              thing typed here is a field the Admin explicitly marked as
              operator-input. Nothing is defaulted, so an UNKNOWN fact stays
              visibly missing instead of printing a blank or a zero. */}
          {uploadedTemplateRows.length > 0 && (
          <section
            id="shipment-uploaded-templates"
            className="rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-5"
            data-testid="shipment-uploaded-templates-panel"
          >
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-1">Biểu mẫu Office do Admin phát hành</h3>
            <p className="text-[13px] text-slate-500 mb-3">
              Bố cục gốc của tệp được giữ nguyên; chỉ các vị trí Admin đã xác nhận được điền từ dữ liệu đã xác nhận của lô. Trường tiền tệ/giá/thanh toán không bao giờ tự điền.
            </p>
            <div className="space-y-3">
              {uploadedTemplateRows.map((row) => {
                const state = row.state;
                const ready = state.readiness.state === "READY";
                const missingManual = (state.manualFields ?? []).filter((field) => !val(`up_${row.id}_${field}`, "").trim());
                const missingCanonical = (state.readiness.missing ?? []).filter((item) => !/nhập tay/i.test(item));
                return (
                  <article
                    key={row.id}
                    data-testid="uploaded-template-card"
                    data-template-id={row.id}
                    data-state={state.readiness.state}
                    className="rounded-xl border border-slate-200 p-3.5"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-extrabold text-[14.5px] text-[#0f2a4a] break-words">{row.label}</p>
                        <p className="text-[11.5px] text-slate-500 mt-0.5">
                          {state.kind} · bản v{state.version} · {row.category}
                        </p>
                      </div>
                      <ToneBadge tone={ready ? "blue" : "amber"} size="sm">
                        {ready ? "Sẵn sàng" : "Thiếu thông tin"}
                      </ToneBadge>
                    </div>

                    {missingCanonical.length > 0 && (
                      <MissingBox
                        what={missingCanonical.join(" · ")}
                        where="Backend chặn đến khi dữ liệu canonical của lô được bổ sung — không tự đặt giá trị."
                        actionLabel="Sang thông tin lô"
                        onAction={() => setSp({ tab: "info" })}
                      />
                    )}

                    {(state.manualFields ?? []).length > 0 && (
                      <div className="grid sm:grid-cols-2 gap-3 mt-3">
                        {(state.manualFields ?? []).map((field) => {
                          const fieldId = `fld-up-${row.id}-${field}`;
                          const typed = val(`up_${row.id}_${field}`, "");
                          return (
                            <Field
                              key={field}
                              label={field}
                              required
                              hint="Admin đánh dấu ô này là nhập tay — backend không tự đặt."
                            >
                              <input
                                id={fieldId}
                                value={typed}
                                onChange={(event) => set(`up_${row.id}_${field}`, event.target.value)}
                                placeholder={"Nhập " + field}
                                className={inputCls(typed.trim() ? "ok" : "missing")}
                              />
                            </Field>
                          );
                        })}
                      </div>
                    )}

                    <SuccessBtn
                      onClick={() => exportUploadedTemplate(row.id, row.label, state.manualFields ?? [])}
                      disabled={!ready || missingManual.length > 0}
                      className="w-full mt-3 text-[15px] min-h-[52px]"
                      testId={"uploaded-template-generate-" + row.id}
                    >
                      🖨 TẠO TỆP {state.kind} TỪ BIỂU MẪU
                    </SuccessBtn>
                    {!ready && missingManual.length > 0 && (
                      <p className="text-[12.5px] text-amber-800 mt-2">
                        Còn thiếu thông tin nhập tay: {missingManual.join(", ")}.
                      </p>
                    )}
                  </article>
                );
              })}
            </div>
          </section>
          )}
          {/* LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — real attachments of
              the lot. Metadata comes from the backend projection; the bytes stay
              in the server-side attachment store and are read through the
              bounded attachment_download event, so no Drive id, folder id or
              credential ever reaches the DOM. */}
          <ShipmentAttachments
            contextCategories={workspaceNode?.documentCategories}
            shipmentId={s.id}
            attachments={s.attachments ?? []}
            policy={vm?.attachmentPolicy}
          />
        </div>
      )}

      {/* ============ TAB: HISTORY ============ */}
      {showExistingWork && tab === "lich-su" && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 max-w-[800px]">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] mb-4">Dòng thời gian — {s.id}</h3>
          <div className="relative pl-6 space-y-4 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {s.timeline.map((t, i) => (
              <div key={i} className="relative">
                <span className={cx("absolute -left-6 top-1 w-4 h-4 rounded-full border-[3px] border-white shadow", t.tone === "green" ? "bg-emerald-500" : t.tone === "amber" ? "bg-amber-500" : t.tone === "red" ? "bg-red-500" : "bg-blue-500")} />
                <p className="text-[12.5px] font-bold text-slate-400">{t.time}</p>
                <p className="font-bold text-[15px] text-[#0f2a4a]">{t.title}</p>
                {t.desc && <p className="text-[13.5px] text-slate-600">{t.desc}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* sticky mobile primary */}
      <div className="xl:hidden sticky-action -mx-3 px-3 py-3 flex gap-2">
        {tab === "nhap" && !s.importInfo.delivered && <button onClick={() => setShowDeliver(true)} className="btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">✅ XÁC NHẬN ĐÃ GIAO</button>}
        {tab === "chung-tu" && s.commercialFlow?.confirmed && s.commercialFlow?.mode !== "CUSTOMER_SELF" && <button onClick={exportPXK} className="btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]">🖨 XUẤT PHIẾU XUẤT KHO</button>}
        {tab === "tai-chinh" && <button onClick={openPay} className="btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]">＋ GHI NHẬN THANH TOÁN</button>}
      </div>

      </ShipmentJourney>

      <ShipmentCompletionGoals shipment={s} onOpenTab={(target) => {
        if (target === "lay-hang" && exportTabLocked) { setExportLockNotice(true); return; }
        setSp({ tab: target });
      }} />

      {/* MODAL: deliver */}
      {showDeliver && (
        <SheetDialog id="delivery-confirm-sheet" testId="delivery-confirm-sheet" labelledBy="delivery-sheet-title" width={480} onClose={() => setShowDeliver(false)}>
            <h3 id="delivery-sheet-title" className="font-extrabold text-[18px] text-[#0f2a4a]">Xác nhận đã giao {s.id}?</h3>
            <p className="text-[14.5px] text-slate-600 mt-1.5">
              Khách <b>{s.customer}</b> đã ký nhận đủ <b>{s.cargo.packs} kiện</b> tại <b>{s.importInfo.deliveryAddr}</b>?
              Sau xác nhận, lô chuyển sang “Đã giao”
              {s.commercialFlow?.mode === "CUSTOMER_SELF" ? "." : "; bước PXK sẽ được xét theo workflow đã xác nhận."}
            </p>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setShowDeliver(false)}>Chưa, để sau</GhostBtn>
              <SuccessBtn onClick={confirmDelivery}>✅ ĐÃ GIAO</SuccessBtn>
            </div>
        </SheetDialog>
      )}
      {/* MODAL: pay — authoritative outcome: open while pending, close only on
          the backend's correlated confirmation, refusal stays inline. */}
      {showPay && (
        <SheetDialog id="payment-record-sheet" testId="payment-record-sheet" labelledBy="payment-sheet-title" pending={!!payPending} width={480} onClose={() => setShowPay(false)}>
            <h3 id="payment-sheet-title" className="font-extrabold text-[18px] text-[#0f2a4a]">Ghi nhận thanh toán — {s.id}</h3>
            <p className="text-[13.5px] text-slate-500">Còn phải thu: <b className="text-red-700">{fmtCcy(s.finance.outstanding, ccy)}</b></p>
            <div className="grid gap-3 mt-3">
              <Field label="Loại khoản"><select value={payKind} disabled={!!payPending} onChange={(e) => { setPayKind(e.target.value); payRequestRef.current = mintRequestId("PAY"); }} className={inputCls()}><option>Thu tiền khách</option><option>Thu tạm ứng</option><option>Thu nốt công nợ</option><option>Trả đối tác</option></select></Field>
              <Field label={`Số tiền (${ccy})`} required error={!payAmt ? "Nhập số tiền — VD: 150000000" : undefined}><input value={payAmt} disabled={!!payPending} onChange={(e) => { setPayAmt(e.target.value); payRequestRef.current = mintRequestId("PAY"); }} inputMode="numeric" placeholder="VD: 150000000" className={inputCls(!payAmt ? "missing" : "ok")} /></Field>
            </div>
            {payPending ? (
              <p role="status" data-testid="payment-record-pending" className="mt-2.5 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13.5px] font-semibold text-blue-800">
                ⏳ ĐANG CHỜ BACKEND XÁC NHẬN… Không gửi lại và không đóng trang.
              </p>
            ) : (
              <p className="text-[12.5px] text-slate-400 mt-2">Ghi theo đồng tiền của lô ({ccy}) — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản thu thứ hai.</p>
            )}
            {payError && (
              <p role="alert" id="payment-record-error" className="mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700">{payError}</p>
            )}
            <p className="text-[12.5px] text-slate-400 mt-2">Mã yêu cầu: <b className="font-mono">{payRequestRef.current}</b></p>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setShowPay(false)} disabled={!!payPending}>Hủy</GhostBtn>
              <SuccessBtn onClick={recordPay} disabled={!!payPending} testId="payment-record-submit">
                {payPending ? "⏳ ĐANG CHỜ BACKEND XÁC NHẬN…" : "💾 LƯU KHOẢN THU"}
              </SuccessBtn>
            </div>
        </SheetDialog>
      )}
      {/* ============ SHEET: PAYMENT CORRECTION (canonical reversal) ============
          Read-only original facts + REQUIRED reason + OPTIONAL evidence.
          This sheet never edits the old payment: the backend appends a linked
          correction and marks the row reversed. Submit is disabled while the
          outcome is in flight; the sheet closes ONLY on the authoritative
          backend success and stays open (fields frozen) on refusal. */}
      {correctionFor && (
        <SheetDialog id="payment-correction-sheet" testId="payment-correction-sheet" labelledBy="correction-sheet-title" pending={!!corrPending} width={520} onClose={closeCorrection}>
            <h3 id="correction-sheet-title" className="font-extrabold text-[18px] text-[#0f2a4a]">Điều chỉnh khoản thu — hoàn tác có kiểm toán</h3>
            <p className="text-[13px] text-slate-500 mt-0.5">
              Khoản thu gốc không bị sửa nội dung và không bị xóa: backend ghi một correction liên kết
              (financial_corrections + audit payment_reversed) rồi đánh dấu khoản thu “Đã hoàn tác”.
              Số dư phải thu đọc lại từ backend — không phải từ màn hình này.
            </p>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 mt-3 grid grid-cols-[110px_1fr] gap-x-3 gap-y-1.5 text-[13px]" id="correction-original-facts">
              <span className="text-slate-400 font-bold">Payment ID</span>
              <span className="font-bold text-slate-700 break-all text-right">{correctionFor.id}</span>
              <span className="text-slate-400 font-bold">Ngày</span>
              <span className="font-bold text-slate-700 text-right">{correctionFor.date || "—"}</span>
              <span className="text-slate-400 font-bold">Số tiền</span>
              <span className="font-extrabold text-slate-700 text-right">{fmtMoney(correctionFor.amount, correctionFor.ccy)}</span>
              <span className="text-slate-400 font-bold">Loại</span>
              <span className="font-bold text-slate-700 text-right">{correctionFor.kind}{correctionFor.note && correctionFor.note !== correctionFor.kind ? " · " + correctionFor.note : ""}</span>
              <span className="text-slate-400 font-bold">Đồng tiền</span>
              <span className="font-bold text-slate-700 text-right">{correctionFor.ccy}</span>
            </div>
            <div className="grid gap-3 mt-3">
              <Field label="Lý do điều chỉnh" required
                     error={corrError && !corrReason.trim() ? corrError : undefined}
                     hint="Bắt buộc — backend từ chối correction không có lý do.">
                <textarea value={corrReason} onChange={(e) => setCorrReason(e.target.value)} disabled={!!corrPending}
                  rows={2} placeholder="VD: Khách chuyển khoản sai nội dung — hoàn tác khoản này, khoản ghi lại sẽ nhập riêng."
                  className={inputCls(corrReason.trim() ? "ok" : "missing")} />
              </Field>
              <details className="rounded-xl border border-slate-200 p-3">
                <summary className="cursor-pointer text-[13.5px] font-bold text-slate-600">
                  Bằng chứng kèm theo (không bắt buộc — KHÔNG phải số tiền thay thế)
                </summary>
                <div className="grid gap-3 mt-3">
                  <Field label={`Số tiền liên quan (${correctionFor.ccy || ccy})`}
                         error={corrError && corrAmt.trim() && parseAmountVN(corrAmt) == null ? corrError : undefined}
                         hint="Chỉ lưu kèm correction làm bằng chứng. Để trống = không nhập, không tự thành 0.">
                    <input value={corrAmt} onChange={(e) => setCorrAmt(e.target.value)} disabled={!!corrPending}
                      inputMode="decimal" placeholder="VD: 1.200.000" className={inputCls(corrAmt.trim() ? (parseAmountVN(corrAmt) == null ? "invalid" : "ok") : "ok")} />
                  </Field>
                  <Field label="Ngày liên quan">
                    <input value={corrDate} onChange={(e) => setCorrDate(e.target.value)} disabled={!!corrPending}
                      placeholder="VD: 11/09/2026" className={inputCls("ok")} />
                  </Field>
                  <Field label="Ghi chú">
                    <input value={corrNote} onChange={(e) => setCorrNote(e.target.value)} disabled={!!corrPending}
                      placeholder="Chứng từ, ủy nhiệm chi, email khách…" className={inputCls("ok")} />
                  </Field>
                </div>
              </details>
            </div>
            {corrError && corrReason.trim() && (
              <p className="mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700" role="alert" id="correction-backend-error">{corrError}</p>
            )}
            <p className="text-[12.5px] text-slate-400 mt-2">
              Mã yêu cầu: <b className="font-mono">{corrRequestRef.current}</b> — bấm lặp lại cùng ý định này không tạo
              correction thứ hai; đóng rồi mở lại là ý định mới với mã mới.
            </p>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={closeCorrection}>{corrPending ? "Đang chờ backend…" : "Hủy"}</GhostBtn>
              <PrimaryBtn onClick={submitCorrection} disabled={!!corrPending}>
                {corrPending ? "⏳ ĐANG GHI…" : "✅ XÁC NHẬN ĐIỀU CHỈNH / HOÀN TÁC"}
              </PrimaryBtn>
            </div>
        </SheetDialog>
      )}
      {savedTick > 0 && <span className="hidden" />}
    </div>
  );
}
