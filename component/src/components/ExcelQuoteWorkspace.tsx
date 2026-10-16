import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { ArrowLeft, ArrowRight, Check, FileDown, FileSpreadsheet, LockKeyhole, Plus, Search, Trash2, TriangleAlert } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, SearchPicker, SectionTitle, SuccessBtn, ToneBadge, inputCls } from "./ui";
import CostIntelligencePanel from "./CostIntelligence";
import { useStore } from "../lib/store";
import { getViewModel, subscribeViewModel, type Quote } from "../lib/viewmodel";
import { cx, downloadBinaryFile, fmtMoney } from "../lib/format";
import { costReferenceIssue, findComparableCosts, loose, type CostCriteria, type CostMatch, type CostMatchLine } from "../lib/costHistory";
import { emptyExcelService, quoteRequestId, type CustomerQuotePreview, type DraftNumber, type ExcelGoods, type ExcelQuoteDraft, type ExcelService, type OptionKey } from "../lib/excelQuote";
import type { LogiEventName } from "../lib/dispatcher";
import "./excelQuote.css";

const STEPS = ["Thông tin khách gửi", "Tính giá nội bộ", "Báo giá gửi khách"];
const money = (value: number | null | undefined, currency = "") => value == null ? "Chưa xác định" : `${fmtMoney(value)} ${currency === "CNY" ? "RMB" : currency}`;
const valueText = (value: DraftNumber | undefined) => value == null ? "" : String(value);

// Exclude server-derived numbers from subsequent preview inputs. This is
// serialization, not a browser calculation/total authority.
function editableDetails(d: ExcelQuoteDraft) {
  const { calculation: _calc, ...base } = d;
  return { ...base, goods: d.goods.map(({ line_total: _amount, ...g }) => g),
    options: Object.fromEntries((['A', 'B'] as const).map((key) => [key, {
      scope: d.options[key].scope,
      service_lines: d.options[key].service_lines.map(({ sell_total: _sell, tax_total: _tax, ...line }) => line),
    }])),
    customs: { confirmed: d.customs.confirmed, basis_vnd: d.customs.basis_vnd, basis_note: d.customs.basis_note,
      duty_pct: d.customs.duty_pct, vat_pct: d.customs.vat_pct, hs_code: d.customs.hs_code },
  };
}

interface Pending { event: LogiEventName; id: string; fingerprint?: string }

export default function ExcelQuoteWorkspace({ initialQuote, onClose }: { initialQuote?: Quote | null; onClose: () => void }) {
  const { customers, dispatch, toast, userName } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [currentQuote, setCurrentQuote] = useState(initialQuote ?? null);
  const [step, setStep] = useState(1);
  const [details, setDetails] = useState<ExcelQuoteDraft | null>(initialQuote?.excelQuote ?? null);
  const [review, setReview] = useState<ExcelQuoteDraft | null>(null);
  const [header, setHeader] = useState(() => ({
    customerId: initialQuote?.customerId ?? "", salesOwner: initialQuote?.salesOwner || userName,
    goodsDescription: initialQuote?.goodsDescription ?? "", origin: initialQuote?.origin ?? "", destination: initialQuote?.destination ?? "",
    route: initialQuote?.route ?? "", incoterm: initialQuote?.incoterm || "EXW", transportMode: initialQuote?.transportMode || "Sea",
    expectedDeliveryDate: initialQuote?.expectedDeliveryDate ?? "",
  }));
  const [fx, setFx] = useState(() => ({ CNY: valueText(initialQuote?.fxRatesToVnd?.CNY), USD: valueText(initialQuote?.fxRatesToVnd?.USD), CNY_PER_USD: "" }));
  const [preview, setPreview] = useState<{ quote: Quote; customer: CustomerQuotePreview } | null>(null);
  const [previewFor, setPreviewFor] = useState("");
  const [previewPending, setPreviewPending] = useState<Pending | null>(null);
  const [busy, setBusy] = useState<Pending | null>(null);
  const [error, setError] = useState("");
  const [savedMessage, setSavedMessage] = useState("");
  const [managingRates, setManagingRates] = useState(false);
  const [costOpen, setCostOpen] = useState(true);
  const fileInput = useRef<HTMLInputElement>(null);
  const heading = useRef<HTMLDivElement>(null);
  const working = review ?? details;
  const payload = useMemo(() => working ? { ...header, fx, excelQuote: editableDetails(working) } : null, [header, fx, working]);
  const fingerprint = payload ? JSON.stringify(payload) : "";
  const [savedFingerprint, setSavedFingerprint] = useState(() => initialQuote?.excelQuote ? JSON.stringify({ ...header, fx, excelQuote: editableDetails(initialQuote.excelQuote) }) : "");
  const dirty = !!working && fingerprint !== savedFingerprint;
  const fresh = !!preview && previewFor === fingerprint;
  const calculated = fresh ? preview.quote.excelQuote : null;
  const customer = customers.find((c) => c.id === header.customerId);
  const locked = !!busy;
  const canAct = !busy && !previewPending && !managingRates;
  const set = (key: keyof typeof header, value: string) => setHeader((old) => ({ ...old, [key]: value }));
  const patch = (change: Partial<ExcelQuoteDraft>) => {
    if (review) setReview({ ...review, ...change });
    else if (details) setDetails({ ...details, ...change });
  };
  const move = (next: number) => {
    setStep(next);
    heading.current?.scrollIntoView({ block: "start", behavior: "instant" });
  };

  // One in-flight preview on the native Streamlit trigger channel. Stale
  // results never masquerade as the current form's calculations.
  useEffect(() => {
    if (!payload || !header.customerId || busy || previewPending || managingRates || previewFor === fingerprint) return;
    const timer = window.setTimeout(() => {
      const id = quoteRequestId();
      if (dispatch("quote_preview", { ...payload, requestId: id })) {
        setPreviewPending({ event: "quote_preview", id, fingerprint });
      } else setError("Chưa kết nối backend; không tính tổng trong trình duyệt.");
    }, 500);
    return () => window.clearTimeout(timer);
  }, [fingerprint, busy, previewPending, managingRates, previewFor, header.customerId, dispatch, payload]);

  useEffect(() => {
    if (!previewPending) return;
    const outcome = vm?.lastWrites?.find((w) => w.event === "quote_preview" && w.requestId === previewPending.id);
    if (!outcome) return;
    setPreviewPending(null);
    setPreviewFor(previewPending.fingerprint || "");
    if (outcome.ok && outcome.readback) {
      setPreview(outcome.readback as unknown as { quote: Quote; customer: CustomerQuotePreview });
      setError("");
    } else {
      setPreview(null);
      setError(String(outcome.error || "Backend chưa tính được bản xem trước."));
    }
  }, [vm, previewPending]);

  useEffect(() => {
    if (!busy) return;
    const outcome = vm?.lastWrites?.find((w) => w.event === busy.event && w.requestId === busy.id);
    if (!outcome) return;
    setBusy(null);
    if (!outcome.ok) { setError(String(outcome.error || "Backend từ chối thao tác.")); return; }
    setError("");
    if (busy.event === "quote_import_excel") {
      setReview(outcome.readback as unknown as ExcelQuoteDraft);
      setStep(1);
      toast("Đã đọc Excel — chưa áp dụng", "Xem lại từng dòng. File nguồn đã lưu trong kho chứng từ hiện có.", "blue");
    } else if (busy.event === "quote_create" || busy.event === "quote_edit" || busy.event === "quote_transition") {
      const q = outcome.readback as unknown as Quote;
      if (!q?.id || !q.excelQuote) { setError("Backend chưa trả về bản báo giá đã đọc lại; không coi là đã lưu."); return; }
      setCurrentQuote(q);
      if (busy.fingerprint) setSavedFingerprint(busy.fingerprint);
      setSavedMessage(`${q.id} · phiên bản ${q.version} · ${q.statusLabel} — đã đọc lại từ backend.`);
      toast("Backend đã xác nhận", q.statusLabel + " · " + q.id, "green");
    } else {
      const doc = outcome.document as { fileName?: string; mime?: string; downloadBase64?: string } | undefined;
      if (!doc?.downloadBase64) { setError("Backend không trả bytes tệp; chưa có file để tải."); return; }
      downloadBinaryFile(doc.fileName || "bao-gia.xlsx", doc.downloadBase64, doc.mime || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
    }
  }, [vm, busy, toast]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const send = (event: LogiEventName, data: Record<string, unknown>, bindForm = false) => {
    if (!canAct) return;
    const id = quoteRequestId();
    if (dispatch(event, { ...data, requestId: id })) {
      setBusy({ event, id, fingerprint: bindForm ? fingerprint : undefined });
      setError("");
    } else setError("Chưa kết nối backend; không có dữ liệu nào được lưu.");
  };
  const upload = async (file: File | undefined) => {
    if (!file) return;
    if (!header.customerId) { setError("Chọn khách hàng trong danh bạ trước khi nhập Excel."); return; }
    if (file.size > 5 * 1024 * 1024 || !file.name.toLowerCase().endsWith(".xlsx")) { setError("Chỉ nhận .xlsx, tối đa 5 MB."); return; }
    try {
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
      send("quote_import_excel", { customerId: header.customerId, fileName: file.name, base64 });
    } catch { setError("Trình duyệt không đọc được tệp. Chưa gửi lên backend."); }
  };
  const save = () => payload && send(currentQuote ? "quote_edit" : "quote_create", { ...payload, ...(currentQuote ? { id: currentQuote.id, expectedVersion: currentQuote.version } : {}) }, true);
  const exportFile = (sentVersion?: number) => currentQuote && send("quote_export_xlsx", { id: currentQuote.id, ...(sentVersion ? { sentVersion } : {}) });
  const updateGoods = (index: number, key: keyof ExcelGoods, value: DraftNumber) => working && patch({ goods: working.goods.map((g, i) => i === index ? { ...g, [key]: value } : g) });
  const updateLine = (index: number, change: Partial<ExcelService>) => {
    if (!working) return;
    const key = working.active_option;
    patch({ options: { ...working.options, [key]: { ...working.options[key], service_lines: working.options[key].service_lines.map((line, i) => i === index ? { ...line, ...change } : line) } } });
  };
  const appendLine = (line: ExcelService) => working && patch({ options: { ...working.options, [working.active_option]: { ...working.options[working.active_option], service_lines: [...working.options[working.active_option].service_lines, line] } } });
  const pickCost = (match: CostMatch, line: CostMatchLine) => {
    const issue = costReferenceIssue(match, line);
    if (issue) { toast("Không thể dùng làm giá vốn", issue, "blue"); return; }
    appendLine({ ...emptyExcelService(), service_name: line.label, unit: line.unit, qty: line.qty ?? 1,
      cost_unit: line.price, currency: line.ccy, sell_unit: "", sell_confirmed: false, tax_pct: "",
      cost_source: `${match.sourceLabel} · ${match.supplier || match.referenceId} · ${line.priceProvenance} · ${line.ccy}/${line.unit}`,
      internal_note: line.note, valid_until: line.validUntil || "", validity_status: line.validityStatus || "UNKNOWN",
      condition: line.condition || "UNCONFIRMED", rate_snapshot_id: line.rateSnapshotId, rate_row_id: line.rateRowId,
    });
    toast("Chỉ điền giá vốn tham khảo", "Giá bán vẫn trống. Dòng phí chỉ thuộc phương án " + working?.active_option + ".", "blue");
  };
  const active = working?.active_option || "A";
  const option = working?.options[active];
  const priceView = calculated?.options[active];
  const criteria: CostCriteria = { incoterm: header.incoterm, mode: header.transportMode, origin: working?.shipment.pol || header.origin,
    destination: working?.shipment.pod || header.destination, factory: working?.shipment.pickup || "", delivery: working?.shipment.delivery || "",
    loadModel: working?.shipment.load_model || "", equipment: working?.shipment.equipment || "", cbm: null, weightKg: null };

  return (
    <div className="excel-quote-workspace space-y-4 max-w-[1300px]" data-testid="excel-quote-workspace" data-preview-current={fresh} data-saved-id={currentQuote?.id || ""} data-version={currentQuote?.version || 0} ref={heading}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionTitle icon={<FileSpreadsheet size={20} />} title="Báo giá từ Excel" sub="Từ thông tin khách gửi đến bản báo giá đã kiểm tra · Dự toán, không phải công nợ." />
        <GhostBtn onClick={() => { if (!dirty || window.confirm("Có thay đổi chưa lưu. Rời bản nháp này?")) onClose(); }} disabled={locked}><ArrowLeft size={16} /> Danh sách báo giá</GhostBtn>
      </div>
      <nav className="eq-steps" aria-label="Ba bước báo giá">
        {STEPS.map((title, i) => <button key={title} type="button" aria-current={step === i + 1 ? "step" : undefined} disabled={i > 0 && (!details || !!review)} onClick={() => move(i + 1)} data-testid={`excel-step-${i + 1}`} className={cx("eq-step", step === i + 1 && "eq-step-active")}><span className="eq-step-number">{i + 1}</span><span>{title}</span></button>)}
      </nav>
      <div className="flex flex-wrap items-center gap-2 text-[13px]">
        <ToneBadge tone={currentQuote?.status === "SENT" ? "green" : "gray"}>{currentQuote?.statusLabel || "Nháp chưa lưu"}</ToneBadge>
        <span>{currentQuote?.id ? `${currentQuote.id} · v${currentQuote.version}` : "Chưa có mã báo giá"}</span>
        {dirty && <span className="font-semibold text-amber-800">● Có thay đổi chưa lưu</span>}
        {working && !fresh && <span role="status" className="text-slate-500">{previewPending ? "Đang tính từ backend…" : previewFor === fingerprint && error ? "Dữ liệu cần sửa" : "Đang chờ backend tính lại…"}</span>}
      </div>
      {error && <div role="alert" className="eq-alert border-red-300 bg-red-50 text-red-900">⚠ {error}</div>}
      {savedMessage && <div role="status" data-testid="excel-saved" className="eq-alert border-emerald-200 bg-emerald-50 text-emerald-900"><Check size={18} className="inline mr-2" />{savedMessage}</div>}

      {step === 1 && <>
        <section className="eq-card">
          <h3 className="eq-title">Khách hàng & thông tin nguồn</h3>
          {!working && !currentQuote ? <SearchPicker label="Khách hàng" required options={customers.map((c) => ({ id: c.id, label: c.name, sub: [c.id, c.taxCode].filter(Boolean).join(" · ") }))} selectedId={header.customerId} selectedLabel={customer?.name || ""} onSelect={(id) => set("customerId", id)} testId="excel-customer" /> : <p className="font-bold text-[16px]">{customer?.name || currentQuote?.customer || "Khách hàng chưa xác định"}</p>}
          <div className="grid sm:grid-cols-2 gap-3 mt-4">
            <Field label="Hàng hóa"><input className={inputCls()} value={header.goodsDescription} onChange={(e) => set("goodsDescription", e.target.value)} data-testid="excel-goods-description" /></Field>
            <Field label="Sale phụ trách"><input className={inputCls()} value={header.salesOwner} onChange={(e) => set("salesOwner", e.target.value)} /></Field>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <PrimaryBtn testId="excel-upload-button" onClick={() => fileInput.current?.click()} disabled={!header.customerId || !canAct}><FileSpreadsheet size={18} /> {busy?.event === "quote_import_excel" ? "Đang đọc Excel…" : "Nhập Excel khách gửi"}</PrimaryBtn>
            <input type="file" accept=".xlsx" aria-label="Nhập Excel khách gửi" data-testid="excel-upload" ref={fileInput} className="sr-only" onChange={(e) => { void upload(e.target.files?.[0]); e.target.value = ""; }} />
            <span className="text-[13px] text-slate-500">V1 · bố cục Lục Giác · .xlsx tối đa 5 MB</span>
          </div>
          {working && <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 text-[13px] break-words" data-testid="excel-source"><p className="font-semibold">📄 {working.source.file_name} · {working.source.sheet_names.length} sheet · bảng hàng: {working.source.goods_sheet}</p><p className="mt-1 text-slate-500">File gốc giữ nguyên trong kho chứng từ · SHA256 {working.source.sha256.slice(0, 16)}…</p><Field label="Nhà cung cấp tham khảo"><input className={inputCls()} value={working.supplier} onChange={(e) => patch({ supplier: e.target.value })} /></Field>{currentQuote && <GhostBtn className="mt-2" onClick={() => send("quote_source_download", { id: currentQuote.id })} disabled={!canAct}><FileDown size={16} /> Tải file nguồn đã lưu</GhostBtn>}</div>}
        </section>
        {working && <>
          <section className="eq-card" data-testid="excel-review">
            <div className="flex flex-wrap justify-between gap-2 items-center mb-3"><div><h3 className="eq-title">{review ? "Xem lại Excel trước khi áp dụng" : "Bảng hàng hóa"}</h3><p className="eq-muted">Sửa trực tiếp. Không tự điền model / vật liệu sang các dòng trống. Thành tiền do backend tính.</p></div><ToneBadge tone={review ? "amber" : "blue"}>{review ? "Chưa áp dụng" : "Đã áp dụng vào nháp"}</ToneBadge></div>
            <GoodsEditor goods={working.goods} calculated={calculated?.goods} onChange={updateGoods} />
            <div className="eq-totals" data-testid="excel-goods-summary"><span><b>{calculated?.calculation?.row_count ?? working.goods.length}</b> dòng hàng</span><span><b>{fresh ? money(calculated?.calculation?.quantity) : "…"}</b> chiếc</span>{fresh ? calculated?.calculation?.goods_totals.map((t) => <strong key={t.currency}>{money(t.amount, t.currency)}</strong>) : <span>Chờ tính lại thành tiền…</span>}</div>
            {review && <div className="flex flex-wrap gap-2 mt-4"><SuccessBtn testId="excel-apply" disabled={!fresh || !canAct} onClick={() => { setDetails(review); setReview(null); toast("Đã áp dụng vào bản nháp", "Chưa lưu báo giá cho đến khi bấm Lưu nháp.", "blue"); }}>Áp dụng bảng đã xem</SuccessBtn><GhostBtn onClick={() => { setReview(null); setError(""); }} disabled={!canAct}>Bỏ bản vừa đọc</GhostBtn></div>}
          </section>
          <section className="eq-card"><h3 className="eq-title">Điều kiện từ sheet khách gửi</h3><p className="eq-muted">Thông tin nguồn — chưa xác nhận hợp đồng. Chọn nội dung công bố ở bước 3.</p><ul className="mt-2 space-y-1 text-[14px]">{working.disclosures.map((d) => <li key={d.id}>• {d.text}</li>)}</ul></section>
          <Warnings details={working} onChange={patch} />
        </>}
      </>}

      {step === 2 && working && <>
        <section className="eq-card">
          <h3 className="eq-title">Điều kiện & tuyến vận chuyển</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <Field label="Incoterm"><select className={inputCls()} value={header.incoterm} onChange={(e) => set("incoterm", e.target.value)} data-testid="excel-incoterm">{["EXW", "FOB", "CIF", "DAP"].map((v) => <option key={v}>{v}</option>)}</select></Field>
            <Field label="Phương thức"><select className={inputCls()} value={header.transportMode} onChange={(e) => { set("transportMode", e.target.value); patch({ shipment: { ...working.shipment, load_model: "", equipment: "" } }); }} data-testid="excel-mode"><option value="Sea">SEA · Đường biển</option><option value="Air">AIR · Hàng không</option><option value="Road">ROAD · Đường bộ</option></select></Field>
            <Field label="Hình thức tải"><select className={inputCls()} value={working.shipment.load_model} onChange={(e) => patch({ shipment: { ...working.shipment, load_model: e.target.value, equipment: "" } })} data-testid="excel-load-model"><option value="">Chưa xác nhận</option>{(header.transportMode === "Sea" ? ["FCL", "LCL"] : header.transportMode === "Air" ? ["DIRECT", "CONSOLIDATED"] : ["FTL", "LTL"]).map((v) => <option key={v}>{v}</option>)}</select></Field>
            {header.transportMode === "Sea" && working.shipment.load_model === "FCL" && <Field label="Loại container"><select className={inputCls()} value={working.shipment.equipment} onChange={(e) => patch({ shipment: { ...working.shipment, equipment: e.target.value } })} data-testid="excel-equipment"><option value="">Chưa xác nhận</option>{["20GP", "40GP", "40HQ", "OPEN_TOP", "FLAT_RACK"].map((v) => <option key={v}>{v}</option>)}</select></Field>}
            <Field label="Nơi đi / nước đi"><input className={inputCls()} value={header.origin} onChange={(e) => set("origin", e.target.value)} /></Field>
            <Field label="Nơi đến / nước đến"><input className={inputCls()} value={header.destination} onChange={(e) => set("destination", e.target.value)} /></Field>
            {([['pol', header.transportMode === 'Air' ? 'Sân bay đi' : 'Cảng / điểm đi'], ['pod', header.transportMode === 'Air' ? 'Sân bay đến' : 'Cảng / điểm đến'], ['pickup', 'Nơi lấy hàng'], ['delivery', 'Địa điểm giao']] as const).map(([key, label]) => <Field key={key} label={label}><input className={inputCls()} value={working.shipment[key]} onChange={(e) => patch({ shipment: { ...working.shipment, [key]: e.target.value } })} data-testid={`excel-${key}`} /></Field>)}
            <Field label="CBM đã xác nhận"><NumberField value={working.shipment.cbm} onChange={(v) => patch({ shipment: { ...working.shipment, cbm: v } })} label="CBM" /></Field>
            <Field label="Trọng lượng kg đã xác nhận"><NumberField value={working.shipment.weight_kg} onChange={(v) => patch({ shipment: { ...working.shipment, weight_kg: v } })} label="Trọng lượng" /></Field>
            <Field label="Tuyến mô tả"><input className={inputCls()} value={header.route} onChange={(e) => set("route", e.target.value)} /></Field>
            <Field label="Ngày giao dự kiến" hint="YYYY-MM-DD; backend kiểm tra ngày thực."><input className={inputCls()} placeholder="2026-12-20" value={header.expectedDeliveryDate} onChange={(e) => set("expectedDeliveryDate", e.target.value)} data-testid="excel-delivery-date" /></Field>
          </div>
          <p className="eq-alert border-blue-200 bg-blue-50 text-blue-900 mt-4">ⓘ {header.incoterm} chỉ gợi ý phạm vi cần hỏi; không tự xác nhận bên chịu phí. Phạm vi thực tế phải ghi riêng cho từng phương án.</p>
        </section>
        <section className="eq-card">
          <div className="eq-option-tabs" role="group" aria-label="Phương án dịch vụ">{(['A', 'B'] as OptionKey[]).map((key) => <button type="button" key={key} onClick={() => patch({ active_option: key })} aria-pressed={active === key} data-testid={`excel-option-${key}`} className={cx("eq-option", active === key && "eq-option-active")}><b>Phương án {key}</b><span>{key === 'A' ? 'Khách tự đứng tên nhập khẩu' : 'Dịch vụ nhập khẩu ủy thác'}</span><small>{working.options[key].service_lines.length} phí đã chọn · không sao chép từ phương án khác</small></button>)}</div>
          <div className="mt-4"><Field label={`Phạm vi dịch vụ phương án ${active}`} required><textarea className={inputCls()} rows={2} value={option?.scope || ""} onChange={(e) => patch({ options: { ...working.options, [active]: { ...working.options[active], scope: e.target.value } } })} data-testid="excel-scope" placeholder="Ghi rõ việc đã thống nhất thực hiện, phần loại trừ và bên phụ trách…" /></Field></div>
          <div className="flex flex-wrap justify-between gap-2 mt-5 mb-3 items-center"><h3 className="eq-title"><LockKeyhole size={17} className="inline mr-2" />Chi phí nội bộ · phương án {active}</h3><GhostBtn onClick={() => setCostOpen(!costOpen)} testId="excel-cost-toggle"><Search size={16} /> Tìm trong Kho giá vốn</GhostBtn></div>
          <p className="eq-muted mb-3">Chọn từng phí cần dùng. Chỉ điền giá vốn, giá bán để trống. Không tự cộng nâng hạ, phụ phí điều kiện hoặc khoản dự phòng.</p>
          {costOpen && <CostPicker criteria={criteria} onPick={pickCost} onManage={setManagingRates} />}
          {option?.service_lines.length === 0 && <p className="eq-empty">Phương án {active} chưa chọn phí nào. Không có phí không đồng nghĩa với dịch vụ miễn phí.</p>}
          <div className="space-y-3 mt-4">{option?.service_lines.map((line, index) => <ServiceEditor key={line.id || index} line={line} computed={priceView?.service_lines[index]} index={index} onChange={(change) => updateLine(index, change)} onRemove={() => patch({ options: { ...working.options, [active]: { ...working.options[active], service_lines: working.options[active].service_lines.filter((_, i) => i !== index) } } })} />)}</div>
          <GhostBtn className="mt-3" onClick={() => appendLine(emptyExcelService())} testId="excel-add-fee"><Plus size={16} /> Thêm phí thủ công</GhostBtn>
          <div className="eq-totals" data-testid="excel-service-subtotal"><span>Giá bán dịch vụ trước VAT:</span>{fresh ? priceView?.calculation?.totals_by_currency.map((t) => <strong key={t.currency}>{money(t.sell_total, t.currency)}</strong>) : <span>Chờ backend tính lại…</span>}</div>
        </section>
        <section className="eq-card"><h3 className="eq-title">Tỷ giá cho dự toán</h3><p className="eq-muted">Không lấy tỷ giá cũ trong Excel làm tỷ giá hiện hành. Nhập RMB → VND trực tiếp hoặc USD → VND + RMB/USD, không nhập đồng thời hai cách. Để trống thì giữ tổng theo từng đồng tiền, không có tổng VND xác định.</p><div className="grid sm:grid-cols-3 gap-3 mt-3">{([['CNY', 'RMB (CNY) → VND'], ['USD', 'USD → VND'], ['CNY_PER_USD', 'RMB cho 1 USD (nếu dùng chéo)']] as const).map(([key, label]) => <Field key={key} label={label}><NumberField label={label} value={fx[key]} onChange={(v) => setFx((old) => ({ ...old, [key]: valueText(v) }))} testId={`excel-fx-${key}`} /></Field>)}</div></section>
        <section className="eq-card"><h3 className="eq-title">Thuế nhập khẩu dự kiến</h3><p className="eq-muted">HS / thuế suất cũ chỉ tham khảo. Giá bán dịch vụ không làm tăng trị giá hải quan. Không tự cộng mọi phí Trung Quốc vào cơ sở tính thuế.</p><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
          <Field label="HS tham khảo"><input className={inputCls()} value={working.customs.hs_code} onChange={(e) => patch({ customs: { ...working.customs, hs_code: e.target.value, confirmed: false } })} /></Field>
          {([['basis_vnd', 'Trị giá hải quan VND'], ['duty_pct', 'Thuế NK %'], ['vat_pct', 'VAT NK %']] as const).map(([key, label]) => <Field key={key} label={label}><NumberField label={label} value={working.customs[key]} testId={`excel-customs-${key}`} onChange={(v) => patch({ customs: { ...working.customs, [key]: v, confirmed: false } })} /></Field>)}
        </div><div className="mt-3"><Field label="Căn cứ / giả định xác nhận riêng (nội bộ)"><textarea className={inputCls()} rows={2} value={working.customs.basis_note} onChange={(e) => patch({ customs: { ...working.customs, basis_note: e.target.value, confirmed: false } })} data-testid="excel-customs-basis-note" /></Field></div><label className="eq-checkbox mt-3"><input type="checkbox" checked={working.customs.confirmed} onChange={(e) => patch({ customs: { ...working.customs, confirmed: e.target.checked } })} data-testid="excel-customs-confirmed" /><span>Tôi đã xác nhận trị giá hải quan, căn cứ và thuế suất cho dự toán này.</span></label><p className="mt-3 font-semibold" data-testid="excel-customs-result">Thuế NK + VAT NK dự kiến: {fresh ? money(calculated?.customs.total_vnd, "VND") : "Chờ tính lại…"}</p></section>
        <Warnings details={working} onChange={patch} />
      </>}

      {step === 3 && working && <>
        <section className="eq-card"><h3 className="eq-title">Chọn thông tin công bố</h3><p className="eq-muted">Bỏ tích để ẩn khỏi bản khách, không xóa thông tin nguồn. Lưu tại backend cùng báo giá.</p><div className="grid sm:grid-cols-2 gap-2 mt-3">{working.disclosures.map((d) => <label key={d.id} className="eq-checkbox"><input type="checkbox" checked={d.selected} data-testid={`excel-disclose-${d.id}`} onChange={(e) => patch({ disclosures: working.disclosures.map((item) => item.id === d.id ? { ...item, selected: e.target.checked } : item) })} /><span>{d.text}</span></label>)}</div><div className="mt-4"><Field label="Ghi chú công bố thêm" hint="Nội dung này được in nguyên các dòng xuống báo giá khách; không ghi thông tin nội bộ vào đây."><textarea rows={4} className={inputCls()} value={working.additional_public_notes} onChange={(e) => patch({ additional_public_notes: e.target.value })} data-testid="excel-public-notes" placeholder="Nhập những điều kiện / lưu ý muốn công bố thêm…" /></Field></div></section>
        <section className="eq-customer-paper" data-testid="excel-customer-preview" aria-label="Bản báo giá khách"><div className="text-center border-b border-slate-200 pb-5 mb-5"><p className="text-[12px] font-bold tracking-widest text-slate-500">BẢN XEM TRƯỚC · {currentQuote?.status === 'SENT' && !dirty ? 'ĐÃ ĐÁNH DẤU GỬI' : 'DỰ THẢO CHƯA GỬI'}</p><h3 className="text-[24px] font-extrabold text-[#0f2a4a] mt-2">BÁO GIÁ DỊCH VỤ LOGISTICS</h3><p className="mt-1 text-[14px]">{currentQuote?.quoteNo || 'Mã báo giá được cấp khi lưu'}</p></div>{fresh && preview ? <CustomerPreview value={preview.customer} /> : <p role="status">Đang lấy bản khách từ backend; không hiển thị tổng của dữ liệu cũ.</p>}</section>
        <section className="eq-card"><h3 className="eq-title">Lưu & xuất bản khách</h3><p className="eq-muted">Lưu nháp không phải gửi khách. XLSX không có giá vốn, lợi nhuận, nguồn giá, ghi chú nội bộ hoặc lịch sử Sale.</p>{currentQuote?.status === "SENT" && <p className="eq-alert border-amber-200 bg-amber-50 mt-3">Sửa và lưu sẽ tạo phiên bản nháp tiếp theo. Nội dung các phiên bản đã gửi bên dưới không bị đổi.</p>}<div className="flex flex-wrap gap-2 mt-4"><SuccessBtn testId="excel-save-step3" onClick={save} disabled={!fresh || !canAct || !!review}>Lưu bản nháp</SuccessBtn><PrimaryBtn testId="excel-export" onClick={() => exportFile()} disabled={!currentQuote || dirty || !canAct}><FileDown size={17} /> Xuất XLSX bản khách</PrimaryBtn>{currentQuote && !dirty && (currentQuote.status === "DRAFT" || currentQuote.status === "READY_FOR_REVIEW") && <GhostBtn disabled={!canAct} testId="excel-transition" onClick={() => send("quote_transition", { id: currentQuote.id, nextStatus: currentQuote.status === 'DRAFT' ? 'READY_FOR_REVIEW' : 'SENT' })}>{currentQuote.status === "DRAFT" ? "Chuyển chờ review" : "Đánh dấu đã gửi khách"}</GhostBtn>}</div>{dirty && <p className="eq-muted mt-2">Lưu nháp rồi mới xuất để file phản ánh đúng dữ liệu đã lưu.</p>}{!!currentQuote?.sentVersions?.length && <div className="mt-5 border-t border-slate-200 pt-4"><h4 className="font-bold text-[14px]">Phiên bản đã gửi · nội dung cố định</h4><div className="flex flex-wrap gap-2 mt-2">{currentQuote.sentVersions.map((v) => <GhostBtn key={v.version} onClick={() => exportFile(v.version)} disabled={!canAct} testId={`excel-history-${v.version}`}><FileDown size={15} /> v{v.version} · {v.sentAt.slice(0, 10)}</GhostBtn>)}</div></div>}</section>
      </>}
      {working && <div className="eq-footer"><div className="flex flex-wrap gap-2"><GhostBtn onClick={() => move(Math.max(1, step - 1))} disabled={step === 1}><ArrowLeft size={16} /> Quay lại</GhostBtn>{step < 3 && <PrimaryBtn testId="excel-next" onClick={() => move(step + 1)} disabled={!details || !!review}>Tiếp tục <ArrowRight size={16} /></PrimaryBtn>}</div><SuccessBtn testId="excel-save" onClick={save} disabled={!details || !!review || !fresh || !canAct}>{busy?.event === 'quote_create' || busy?.event === 'quote_edit' ? 'Đang lưu…' : 'Lưu nháp lên backend'}</SuccessBtn></div>}
    </div>
  );
}

function NumberField({ value, onChange, label, testId }: { value: DraftNumber; onChange: (v: string) => void; label: string; testId?: string }) {
  return <input className={inputCls()} inputMode="decimal" value={valueText(value)} aria-label={label} onChange={(e) => onChange(e.target.value)} data-testid={testId} placeholder="Chưa biết" />;
}

function GoodsEditor({ goods, calculated, onChange }: { goods: ExcelGoods[]; calculated?: ExcelGoods[]; onChange: (index: number, key: keyof ExcelGoods, value: string) => void }) {
  return <table className="eq-goods-table"><thead><tr><th>Hàng hóa / Model / Vật liệu</th><th>Kích thước mm</th><th>Số lượng</th><th>Đơn giá RMB</th><th>Thành tiền</th><th>Ghi chú</th></tr></thead><tbody>{goods.map((g, i) => <tr key={g.id || i} data-testid={`excel-goods-${i + 1}`}><td data-label={`Hàng ${i + 1}`}><b className="text-slate-500 text-[12px]">{i + 1} · {g.source_sheet} / dòng {g.source_row}</b>{(['description', 'model', 'material'] as const).map((k) => <input key={k} className={inputCls()} aria-label={`${k === 'description' ? 'Tên hàng' : k === 'model' ? 'Model' : 'Vật liệu'} hàng ${i + 1}`} value={g[k] || ''} onChange={(e) => onChange(i, k, e.target.value)} placeholder={k === 'description' ? 'Tên hàng' : 'Chưa xác nhận'} />)}</td><td data-label="Kích thước mm"><div className="eq-dimensions">{(['length_mm', 'width_mm', 'height_mm'] as const).map((k, j) => <NumberField key={k} label={`${['Dài', 'Rộng', 'Cao'][j]} hàng ${i + 1}`} value={g[k]} onChange={(v) => onChange(i, k, v)} testId={`excel-goods-${i + 1}-${k}`} />)}</div></td><td data-label="Số lượng"><NumberField label={`Số lượng hàng ${i + 1}`} value={g.qty} onChange={(v) => onChange(i, 'qty', v)} testId={`excel-goods-${i + 1}-qty`} /></td><td data-label="Đơn giá"><NumberField label={`Đơn giá hàng ${i + 1}`} value={g.unit_price} onChange={(v) => onChange(i, 'unit_price', v)} testId={`excel-goods-${i + 1}-price`} /><span className="text-[12px] text-slate-500">{g.currency === 'CNY' ? 'RMB' : g.currency}</span></td><td data-label="Thành tiền" className="font-bold tabular-nums" data-testid={`excel-goods-${i + 1}-total`}>{calculated ? money(calculated[i]?.line_total, g.currency) : 'Chờ tính…'}</td><td data-label="Ghi chú"><textarea className={inputCls()} rows={3} aria-label={`Ghi chú hàng ${i + 1}`} value={g.note || ''} onChange={(e) => onChange(i, 'note', e.target.value)} /></td></tr>)}</tbody></table>;
}

function Warnings({ details, onChange }: { details: ExcelQuoteDraft; onChange: (patch: Partial<ExcelQuoteDraft>) => void }) {
  return <section className="eq-card border-amber-200" data-testid="excel-warnings"><h3 className="eq-title text-amber-900"><TriangleAlert size={18} className="inline mr-2" />Cảnh báo thông tin bất thường</h3><p className="eq-muted">Giữ nguyên dữ liệu nguồn. Ghi chú xác minh không biến giá cũ thành giá hiện hành.</p><div className="space-y-2 mt-3">{details.source_warnings.map((w) => <details key={w.id} className="eq-warning"><summary>{w.text}<span className="block text-[12px] mt-1 font-normal">{details.warning_notes[w.id]?.status === 'NOTED' ? 'Đã ghi chú xác minh' : details.warning_notes[w.id]?.status === 'NEEDS_INFO' ? 'Cần bổ sung' : 'Chưa xử lý'}</span></summary><div className="grid sm:grid-cols-[210px_1fr] gap-2 mt-3"><Field label="Trạng thái xác minh"><select className={inputCls()} value={details.warning_notes[w.id]?.status || 'UNRESOLVED'} onChange={(e) => onChange({ warning_notes: { ...details.warning_notes, [w.id]: { note: details.warning_notes[w.id]?.note || '', status: e.target.value } } })}><option value="UNRESOLVED">Chưa xử lý</option><option value="NOTED">Đã ghi chú xác minh</option><option value="NEEDS_INFO">Cần bổ sung</option></select></Field><Field label="Ghi chú xác minh (nội bộ)"><textarea className={inputCls()} rows={2} value={details.warning_notes[w.id]?.note || ''} onChange={(e) => onChange({ warning_notes: { ...details.warning_notes, [w.id]: { status: details.warning_notes[w.id]?.status || 'UNRESOLVED', note: e.target.value } } })} /></Field></div></details>)}</div>{details.source_costs.length > 0 && <details className="mt-3"><summary className="cursor-pointer font-bold text-[14px] py-3">Chi phí cũ trong file · chỉ đọc tham khảo, chưa chọn tính</summary><div className="space-y-1 text-[13px]">{details.source_costs.map((c, i) => <p key={i}>{c.label}: {money(c.amount, 'VND')}{c.condition === 'IF_APPLICABLE' ? ' · NẾU PHÁT SINH' : ''}</p>)}<p className="mt-2 font-semibold">Không tự đưa các khoản này vào Kho giá vốn hoặc phương án A/B.</p></div></details>}</section>;
}

function CostPicker({ criteria, onPick, onManage }: { criteria: CostCriteria; onPick: (match: CostMatch, line: CostMatchLine) => void; onManage: (value: boolean) => void }) {
  const { shipments, costIntelligence } = useStore();
  const [query, setQuery] = useState('');
  const matches = useMemo(() => findComparableCosts(shipments, criteria, costIntelligence.rates, costIntelligence.catalog), [shipments, JSON.stringify(criteria), costIntelligence]);
  useEffect(() => () => onManage(false), [onManage]);
  const needle = loose(query);
  const filtered = matches.filter((m) => !needle || loose([m.supplier, m.referenceId, m.origin, m.destination, ...m.lines.map((l) => l.label)].join(' ')).includes(needle)).slice(0, 12);
  return <div className="eq-cost-picker" data-testid="excel-cost-picker">
    <Field label="Tìm trong Kho giá vốn" hint="Cùng dữ liệu rate_cards / cost_catalog và bộ đối chiếu Cost Intelligence của app.">
      <input className={inputCls()} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tên phí, nhà cung cấp, cảng…" data-testid="excel-cost-search" />
    </Field>
    {filtered.length ? <div className="space-y-3 mt-3">{filtered.map((match) => <div key={match.referenceId} className="rounded-xl border border-slate-200 bg-white p-3" data-testid="excel-cost-reference" data-reference-id={match.referenceId} data-source={match.source}>
      <p className="font-bold text-[14px]">{match.sourceLabel} · {match.supplier || match.referenceId}</p>
      <p className="eq-muted">{match.origin} → {match.destination} · {match.equipment || 'Thiết bị chưa rõ'}</p>
      {match.differences?.length ? <p className="text-[13px] text-amber-900 mt-1">⚠ {match.differences.join(' · ')}</p> : null}
      <div className="mt-2 space-y-2">{match.lines.map((line, i) => {
        const issue = costReferenceIssue(match, line);
        return <div key={i} className="eq-cost-result" data-cost-basis={line.priceBasis}>
          <div>
            <b>{line.label} · {money(line.price, line.ccy)}{line.unit ? ` / ${line.unit}` : ''}</b>
            {issue && <p className="text-[13px] font-semibold text-amber-900" data-testid="excel-cost-ineligible">{issue}</p>}
            <p className="eq-muted break-words">{line.priceProvenance}</p>
            <p className="text-[12px] text-amber-900">{line.validityStatus === 'EXPIRED' || match.expired ? '⚠ ĐÃ HẾT HẠN' : line.validityStatus === 'SUPERSEDED' ? '⚠ ĐÃ CÓ GIÁ THAY THẾ' : line.validUntil ? `Hiệu lực nguồn: ${line.validUntil} — cần xác nhận` : '⚠ CHƯA RÕ HIỆU LỰC'}{line.condition === 'IF_APPLICABLE' ? ' · CÓ ĐIỀU KIỆN' : ''}</p>
            {line.note && <p className="eq-muted break-words">{line.note}</p>}
          </div>
          <GhostBtn onClick={() => onPick(match, line)} disabled={!!issue} testId={`excel-pick-cost-${i + 1}`}>Dùng giá vốn</GhostBtn>
        </div>;
      })}</div>
    </div>)}</div> : <p className="eq-empty">Không có giá phù hợp với tiêu chí hiện tại. App không bịa giá; có thể bổ sung bảng giá thật vào Kho hiện có bên dưới.</p>}
    <details className="mt-3" onToggle={(e) => onManage(e.currentTarget.open)}>
      <summary className="cursor-pointer font-bold py-3 text-[14px]">Bổ sung giá vào Kho hiện có</summary>
      <p className="eq-muted mb-3">Đóng khung này sau khi lưu giá để tiếp tục tính báo giá.</p><CostIntelligencePanel />
    </details>
  </div>;
}

function ServiceEditor({ line, computed, index, onChange, onRemove }: { line: ExcelService; computed?: ExcelService; index: number; onChange: (change: Partial<ExcelService>) => void; onRemove: () => void }) {
  const n = index + 1;
  const source = computed || line;
  return <fieldset className="eq-service" data-testid={`excel-fee-${n}`}><legend className="sr-only">Phí {n}</legend><div className="flex justify-between items-start gap-2 mb-3"><b className="text-[14px] text-[#0f2a4a]">{n}. {line.service_name || 'Phí chưa đặt tên'}</b><button type="button" aria-label={`Xóa phí ${n}`} className="touch-target text-red-700 shrink-0" onClick={onRemove}><Trash2 size={17} /></button></div><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3"><Field label="Tên dịch vụ"><input className={inputCls()} value={line.service_name} onChange={(e) => onChange({ service_name: e.target.value })} data-testid={`excel-fee-${n}-name`} /></Field><Field label="Giá vốn tham khảo"><input className={inputCls()} inputMode="decimal" value={valueText(line.cost_unit)} readOnly={!!line.rate_snapshot_id} onChange={(e) => onChange({ cost_unit: e.target.value })} placeholder="Chưa biết" data-testid={`excel-fee-${n}-cost`} /></Field><Field label="Giá bán do Sale nhập"><NumberField value={line.sell_unit} onChange={(v) => onChange({ sell_unit: v, sell_confirmed: false })} label={`Giá bán phí ${n}`} testId={`excel-fee-${n}-sell`} /></Field><Field label="Số lượng"><NumberField value={line.qty} onChange={(v) => onChange({ qty: v, sell_confirmed: false })} label={`Số lượng phí ${n}`} testId={`excel-fee-${n}-qty`} /></Field><Field label="Đơn vị"><input className={inputCls()} value={line.unit} readOnly={!!line.rate_snapshot_id} onChange={(e) => onChange({ unit: e.target.value })} /></Field><Field label="Tiền tệ"><select className={inputCls()} value={line.currency} disabled={!!line.rate_snapshot_id} onChange={(e) => onChange({ currency: e.target.value, sell_confirmed: false })}><option>VND</option><option>USD</option><option>CNY</option></select></Field><Field label="VAT dịch vụ % (nếu biết)"><NumberField value={line.tax_pct} onChange={(v) => onChange({ tax_pct: v })} label={`VAT dịch vụ phí ${n}`} testId={`excel-fee-${n}-vat`} /></Field><Field label="Điều kiện áp dụng"><select className={inputCls()} value={line.condition} onChange={(e) => onChange({ condition: e.target.value })}><option value="UNCONFIRMED">Cần xác nhận phạm vi</option><option value="CONFIRMED">Đã chọn trong phạm vi</option><option value="IF_APPLICABLE">Nếu phát sinh</option></select></Field></div><label className="eq-checkbox mt-3"><input type="checkbox" checked={line.sell_confirmed} disabled={valueText(line.sell_unit).trim() === ''} onChange={(e) => onChange({ sell_confirmed: e.target.checked })} data-testid={`excel-fee-${n}-confirmed`} /><span>Sale xác nhận giá bán dòng này · thành tiền {money(computed?.sell_total, line.currency)}</span></label><div className="rounded-lg bg-amber-50 border border-amber-200 p-3 mt-3 text-[13px]" data-testid={`excel-fee-${n}-source`}><b>Nguồn giá nội bộ:</b> {source.cost_source || 'Chưa ghi'}<p>⚠ {source.validity_status === 'EXPIRED' ? 'ĐÃ HẾT HẠN — không phải giá hiện hành' : source.validity_status === 'SUPERSEDED' ? 'ĐÃ CÓ GIÁ THAY THẾ' : source.validity_status === 'SOURCE_VALID' ? 'Theo hiệu lực nguồn — vẫn cần xác nhận' : 'CHƯA RÕ HIỆU LỰC'}{source.valid_until ? ` · ${source.valid_until}` : ''}{source.condition === 'IF_APPLICABLE' ? ' · PHÍ CÓ ĐIỀU KIỆN' : ''}</p>{source.source_warning && <p>{source.source_warning}</p>}</div><div className="grid sm:grid-cols-2 gap-3 mt-3"><Field label="Ghi chú nội bộ · không xuất"><textarea rows={2} className={inputCls()} value={line.internal_note} onChange={(e) => onChange({ internal_note: e.target.value })} data-testid={`excel-fee-${n}-internal-note`} /></Field><Field label="Ghi chú phí công bố cho khách"><textarea rows={2} className={inputCls()} value={line.public_note} onChange={(e) => onChange({ public_note: e.target.value })} /></Field></div></fieldset>;
}

function CustomerPreview({ value }: { value: CustomerQuotePreview }) {
  const c = value.goods_calculation;
  const shipment = value.shipment;
  return <><p className="text-[16px] font-bold">Kính gửi: {value.customer_name}</p><p className="mt-1">Hàng hóa: {value.goods_description || 'Theo danh mục dưới đây'}</p><p className="mt-1">{value.incoterm} · {value.transport_mode} · {value.route || 'Tuyến theo các điểm đã chọn bên dưới'}</p><p className="mt-1">Cảng / điểm: {shipment.pol || 'Chưa xác nhận'} → {shipment.pod || 'Chưa xác nhận'} · {shipment.load_model || 'Chưa rõ hình thức tải'}{shipment.equipment ? ` / ${shipment.equipment}` : ''}</p>{shipment.pickup && <p>Nơi lấy hàng: {shipment.pickup}</p>}{shipment.delivery && <p>Giao tại: {shipment.delivery}</p>}{(shipment.cbm != null || shipment.weight_kg != null) && <p>Đóng hàng đã xác nhận: {shipment.cbm ?? '—'} CBM · {shipment.weight_kg ?? '—'} kg</p>}{value.expected_delivery_date && <p>Ngày giao dự kiến: {value.expected_delivery_date}</p>}<h4 className="eq-public-heading">Danh mục hàng hóa</h4><div className="space-y-2">{value.goods.map((g, i) => <div className="eq-public-row" key={i}><div><b>{i + 1}. {g.description || 'Hàng hóa'} · {g.length_mm ?? '—'} × {g.width_mm ?? '—'} × {g.height_mm ?? '—'} mm</b><p className="eq-muted">{[g.model, g.material].filter(Boolean).join(' · ')}{g.note ? ` · ${g.note}` : ''}</p><p>{valueText(g.qty)} chiếc × {money(g.unit_price == null || g.unit_price === '' ? null : Number(g.unit_price), g.currency)}</p></div><strong>{money(g.line_total, g.currency)}</strong></div>)}</div><div className="eq-totals"><span>{c.row_count} dòng · {c.quantity ?? '—'} chiếc</span>{c.goods_totals.map((t) => <strong key={t.currency}>{money(t.amount, t.currency)}</strong>)}</div><h4 className="eq-public-heading">Phương án {value.option} · {value.option === 'A' ? 'Khách tự đứng tên nhập khẩu' : 'Dịch vụ nhập khẩu ủy thác'}</h4><p className="whitespace-pre-wrap">{value.scope || 'Phạm vi dịch vụ chưa xác nhận'}</p><div className="mt-3 space-y-2">{value.service_lines.map((line, i) => <div className="eq-public-row" key={i}><div><b>{line.service_name}</b><p>{valueText(line.qty)} {line.unit} × {money(line.sell_unit == null || line.sell_unit === '' ? null : Number(line.sell_unit), line.currency)}</p>{line.condition === 'IF_APPLICABLE' && <p>Nếu phát sinh — chỉ thực hiện sau khi thống nhất.</p>}{line.public_note && <p className="whitespace-pre-wrap">{line.public_note}</p>}</div><strong>{money(line.sell_total, line.currency)}</strong></div>)}{value.service_lines.length === 0 && <p className="eq-muted">Chưa có phí dịch vụ có giá bán được xác nhận để công bố.</p>}</div><h4 className="eq-public-heading">Tổng dự toán</h4><p>{value.customs.calculable ? `Cơ sở riêng đã xác nhận: ${money(value.customs.basis_vnd, 'VND')} · Thuế NK ${value.customs.duty_pct}% · VAT NK ${value.customs.vat_pct}%.` : 'Cơ sở hải quan chưa được xác nhận; không suy ra từ giá bán dịch vụ.'}</p><p>Thuế NK dự kiến: {money(value.customs.duty_vnd, 'VND')} · VAT NK dự kiến: {money(value.customs.vat_vnd, 'VND')}</p><p className="mt-2">Tạm tính hàng + dịch vụ trước mọi thuế: <b>{money(c.before_tax_vnd, 'VND')}</b></p><p className="mt-2 text-[18px] font-extrabold" data-testid="excel-public-total">Tổng dự toán gồm thuế đã xác định: {money(c.estimate_vnd, 'VND')}</p>{c.unknown_reasons.map((reason) => <p key={reason} className="text-[13px] text-amber-900 mt-1">• {reason}</p>)}<p className="eq-muted mt-2">Tỷ giá dự toán đã nhập: {Object.entries(value.fx_snapshot.rates_to_vnd).filter(([code]) => code !== 'VND').map(([code, rate]) => `${code} → VND ${rate}`).join(' · ') || 'Chưa có; không quy đổi ngoại tệ.'}</p><h4 className="eq-public-heading">Điều kiện & ghi chú công bố</h4><div className="space-y-2" data-testid="excel-public-disclosures">{value.customer_notes.map((note, i) => <p key={i} className="whitespace-pre-wrap">• {note}</p>)}</div><p className="eq-muted border-t border-slate-200 pt-4 mt-5">Báo giá là dự toán, chưa phải hóa đơn hoặc nghĩa vụ thanh toán. Thuế dự kiến không thay thế kết luận pháp lý / hải quan.</p></>;
}
