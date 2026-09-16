import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { CheckCircle2, CircleAlert, FileSpreadsheet, LoaderCircle, Upload, X } from "lucide-react";
import { GhostBtn, PrimaryBtn, SectionTitle, ToneBadge, inputCls } from "./ui";
import { useStore } from "../lib/store";
import { fmtMoney, fmtNum, fmtText, cx } from "../lib/format";
import { getViewModel, subscribeViewModel, type GetFlyOrderPreview, type GetFlyPreview, type LastWriteOutcome } from "../lib/viewmodel";

const GETFLY_MODE_SHIPMENT_ONLY = "SHIPMENT_ONLY";
const GETFLY_MODE_SHIPMENT_AND_FINANCE = "SHIPMENT_AND_FINANCE";
const MAX_FILE_BYTES = 10 * 1024 * 1024;

function intentId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

function statusLabel(status: string): string {
  return status === "CREATED"
    ? "CREATED"
    : status === "SKIPPED_ALREADY_EXISTS"
      ? "SKIPPED_ALREADY_EXISTS"
      : status === "REFUSED_VALIDATION"
        ? "REFUSED_VALIDATION"
        : "FAILED_WRITE";
}

function orderNeedsFinance(order: GetFlyOrderPreview): boolean {
  return !order.existing;
}

export default function GetFlyImport() {
  const { dispatch, toast } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const preview: GetFlyPreview = vm?.getfly ?? {
    status: "EMPTY",
    previewId: "",
    filename: "",
    orders: [],
    summary: { orders: 0, revenue: null, profit: null },
    error: "",
  };
  const lastWrites = vm?.lastWrites ?? [];
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [pendingPreview, setPendingPreview] = useState("");
  const [pendingCommit, setPendingCommit] = useState("");
  const [mode, setMode] = useState(GETFLY_MODE_SHIPMENT_ONLY);
  const [vatByLineId, setVatByLineId] = useState<Record<string, string>>({});
  const [localError, setLocalError] = useState("");
  const [transportError, setTransportError] = useState("");
  const [commitResults, setCommitResults] = useState<Array<Record<string, unknown>>>([]);
  const [seenPreviewId, setSeenPreviewId] = useState("");

  useEffect(() => {
    if (!pendingPreview) return;
    const outcome = lastWrites.find(
      (row) => row.event === "getfly_preview" && row.requestId === pendingPreview
    );
    if (!outcome) return;
    setPendingPreview("");
    if (!outcome.ok) {
      setTransportError(String(outcome.error || "Không đọc được DSDH.xlsx."));
    } else {
      setTransportError("");
      setLocalError("");
    }
  }, [lastWrites, pendingPreview]);

  useEffect(() => {
    if (!pendingCommit) return;
    const outcome = lastWrites.find(
      (row) => row.event === "getfly_import" && row.requestId === pendingCommit
    );
    if (!outcome) return;
    setPendingCommit("");
    const rows = Array.isArray(outcome.results)
      ? outcome.results.filter((row): row is Record<string, unknown> => Boolean(row && typeof row === "object"))
      : [];
    setCommitResults(rows);
    if (!outcome.ok) {
      setTransportError(String(outcome.error || "Nhập GetFly bị từ chối."));
    } else {
      setTransportError("");
      setLocalError("");
      toast("GetFly đã được ghi nhận", "Đã đọc lại dữ liệu mới từ backend.", "green");
    }
  }, [lastWrites, pendingCommit, toast]);

  useEffect(() => {
    if (!preview.previewId || preview.previewId === seenPreviewId) return;
    setSeenPreviewId(preview.previewId);
    setVatByLineId({});
    setCommitResults([]);
    setLocalError("");
    setTransportError("");
  }, [preview.previewId, seenPreviewId]);

  const missingOrders = useMemo(
    () => preview.orders.filter(orderNeedsFinance),
    [preview.orders]
  );
  const missingLineCount = useMemo(
    () => missingOrders.reduce((sum, order) => sum + order.serviceLines.length, 0),
    [missingOrders]
  );

  const financeProblems = useMemo(() => {
    if (mode !== GETFLY_MODE_SHIPMENT_AND_FINANCE) return [] as string[];
    const problems: string[] = [];
    for (const order of missingOrders) {
      for (const line of order.serviceLines) {
        const vat = vatByLineId[line.lineId] ?? "";
        if (!vat.trim()) problems.push(`${order.orderId} · ${line.lineId}: VAT chưa nhập`);
        else if (!Number.isFinite(Number(vat)) || Number(vat) < 0 || Number(vat) > 100) {
          problems.push(`${order.orderId} · ${line.lineId}: VAT không hợp lệ`);
        }
        if (line.qty == null || Number(line.qty) <= 0) problems.push(`${order.orderId} · ${line.lineId}: Số lượng UNKNOWN/không hợp lệ`);
        if (line.cost == null) problems.push(`${order.orderId} · ${line.lineId}: Giá vốn UNKNOWN`);
        if (line.price == null) problems.push(`${order.orderId} · ${line.lineId}: Giá bán UNKNOWN`);
        if (!line.name.trim()) problems.push(`${order.orderId} · ${line.lineId}: Tên dịch vụ UNKNOWN`);
      }
    }
    return problems;
  }, [mode, missingOrders, vatByLineId]);

  const selectFile = () => fileInputRef.current?.click();

  const onFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    if (!file) return;
    setCommitResults([]);
    setLocalError("");
    setTransportError("");
    if (!file.name.toLowerCase().endsWith(".xlsx")) {
      setTransportError("Chỉ nhận file DSDH.xlsx / .xlsx.");
      return;
    }
    if (file.size > MAX_FILE_BYTES) {
      setTransportError(`File DSDH vượt giới hạn ${MAX_FILE_BYTES / (1024 * 1024)} MB.`);
      return;
    }
    const requestId = intentId("GF-PREVIEW");
    setPendingPreview(requestId);
    const reader = new FileReader();
    reader.onerror = () => {
      setPendingPreview("");
      setTransportError("Không đọc được bytes từ file đã chọn.");
    };
    reader.onload = () => {
      const dataUrl = typeof reader.result === "string" ? reader.result : "";
      const comma = dataUrl.indexOf(",");
      const contentBase64 = comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl;
      if (!contentBase64) {
        setPendingPreview("");
        setTransportError("File DSDH không có dữ liệu.");
        return;
      }
      const sent = dispatch("getfly_preview", {
        filename: file.name,
        mime: file.type,
        size: file.size,
        contentBase64,
        requestId,
      });
      if (!sent) {
        setPendingPreview("");
        setTransportError("Không gửi được ý định xem trước tới backend.");
      }
    };
    // FileReader is the only browser-side file operation. XLSX parsing remains
    // entirely in core.getfly_reader on the server.
    reader.readAsDataURL(file);
  };

  const setVat = (lineId: string, value: string) => {
    setVatByLineId((current) => ({ ...current, [lineId]: value }));
    setLocalError("");
    setTransportError("");
  };

  const commit = () => {
    if (!preview.previewId) {
      setLocalError("Chưa có preview hợp lệ. Hãy chọn DSDH.xlsx trước.");
      return;
    }
    if (mode === GETFLY_MODE_SHIPMENT_AND_FINANCE && financeProblems.length > 0) {
      setLocalError("Không thể xác nhận: mỗi dòng dịch vụ của lô mới phải có Giá vốn, Giá bán, Số lượng và VAT. VAT trống không phải là 0.");
      return;
    }
    const requestId = intentId("GF-COMMIT");
    const payload: Record<string, unknown> = {
      previewId: preview.previewId,
      mode,
      requestId,
    };
    // Mode A intentionally carries no financial facts. Mode B carries only
    // explicit operator VAT choices; all order/service facts come from the
    // server-side preview, never from client-normalized rows.
    if (mode === GETFLY_MODE_SHIPMENT_AND_FINANCE) payload.vatByLineId = vatByLineId;
    const sent = dispatch("getfly_import", payload);
    if (!sent) {
      setTransportError("Không gửi được xác nhận nhập GetFly tới backend.");
      return;
    }
    setPendingCommit(requestId);
    setTransportError("");
    setLocalError("");
  };

  const hasPreview = preview.status === "READY" && Boolean(preview.previewId);

  return (
    <section className="rounded-2xl bg-white border-2 border-sky-200 p-4 md:p-5 space-y-4" data-testid="getfly-import">
      <SectionTitle
        icon={<FileSpreadsheet size={19} />}
        title="Nhập GetFly DSDH"
        sub="DSDH.xlsx → xem trước trên server → xác nhận tạo các lô còn thiếu"
        right={
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={onFileChange}
              className="hidden"
              data-testid="getfly-file-input"
              aria-label="Chọn DSDH.xlsx"
            />
            <button
              type="button"
              onClick={selectFile}
              disabled={pendingPreview !== ""}
              className="btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14px] px-3.5 min-h-[46px] disabled:opacity-50"
              data-testid="getfly-choose-file"
            >
              {pendingPreview ? <LoaderCircle size={17} className="animate-spin" /> : <Upload size={17} />}
              {pendingPreview ? "ĐANG ĐỌC…" : "NHẬP GETFLY DSDH"}
            </button>
          </>
        }
      />

      {(localError || transportError) && (
        <div className="rounded-xl border-2 border-red-300 bg-red-50 p-3 text-[13.5px] text-red-800 flex items-start gap-2" data-testid="getfly-error">
          <CircleAlert size={17} className="shrink-0 mt-0.5" />
          <span>{localError || transportError}</span>
        </div>
      )}

      {pendingPreview && (
        <div className="rounded-xl border border-sky-200 bg-sky-50 p-3 text-[14px] text-sky-900 flex items-center gap-2" data-testid="getfly-parsing">
          <LoaderCircle size={17} className="animate-spin" /> Đang gửi bytes tới backend để đọc DSDH.xlsx… Chưa có thao tác ghi dữ liệu.
        </div>
      )}

      {!hasPreview && !pendingPreview && !transportError && (
        <div className="rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-4 text-[14px] text-slate-600" data-testid="getfly-empty">
          Chọn đúng file DSDH.xlsx để xem số đơn, doanh thu, lợi nhuận, dịch vụ và trạng thái đã có/chưa có. Chọn file chỉ tạo preview, chưa ghi lô hay Finance Actual.
        </div>
      )}

      {hasPreview && (
        <>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3" data-testid="getfly-preview-meta">
            <div className="flex flex-wrap items-center gap-2 text-[13.5px]">
              <ToneBadge tone="blue" size="sm">PREVIEW · {preview.filename}</ToneBadge>
              <span className="text-slate-500">{preview.orders.length} đơn · previewId {preview.previewId}</span>
              {preview.fingerprint && <span className="text-slate-400 font-mono text-[11px]">SHA-256 {preview.fingerprint.slice(0, 16)}…</span>}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 mt-3">
              <div className="rounded-xl bg-white border border-slate-200 p-3" data-testid="getfly-kpi-revenue">
                <p className="text-[11.5px] font-bold uppercase tracking-wide text-slate-400">Doanh Thu GF</p>
                <p className="font-extrabold text-[20px] text-[#0f2a4a]">{fmtMoney(preview.summary.revenue)}</p>
              </div>
              <div className="rounded-xl bg-white border border-slate-200 p-3" data-testid="getfly-kpi-profit">
                <p className="text-[11.5px] font-bold uppercase tracking-wide text-slate-400">Lợi Nhuận GF</p>
                <p className="font-extrabold text-[20px] text-emerald-700">{fmtMoney(preview.summary.profit)}</p>
              </div>
              <div className="rounded-xl bg-white border border-slate-200 p-3" data-testid="getfly-kpi-orders">
                <p className="text-[11.5px] font-bold uppercase tracking-wide text-slate-400">Số Đơn</p>
                <p className="font-extrabold text-[20px] text-[#0f2a4a]">{fmtNum(preview.summary.orders)}</p>
              </div>
            </div>
          </div>

          <div className="space-y-3" data-testid="getfly-orders">
            {preview.orders.map((order) => (
              <div key={order.orderId} className="rounded-xl border-2 border-slate-200 bg-white overflow-hidden" data-testid={`getfly-order-${order.orderId}`}>
                <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-extrabold text-[16px] text-[#0f2a4a]">{order.orderId}</p>
                    <p className="text-[13.5px] text-slate-700">{fmtText(order.customer)} · Ngày: {fmtText(order.orderDate)}</p>
                    <p className="text-[12.5px] text-slate-500">Trạng thái nguồn: {fmtText(order.sourceStatus)} · Mã KH: {fmtText(order.customerCode)}</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <ToneBadge tone={order.existing ? "green" : "amber"} size="sm">
                      {order.existing ? "Đã có trong hệ thống" : "Lô còn thiếu — sẽ tạo"}
                    </ToneBadge>
                    <ToneBadge tone={order.customerMatch === "UNKNOWN" ? "amber" : "blue"} size="sm">
                      {order.customerMatch === "UNKNOWN" ? "Khách master: UNKNOWN" : `Khách master: ${order.customerMatch === "MATCHED_BY_CODE" ? "đúng mã" : "đúng tên"}`}
                    </ToneBadge>
                  </div>
                </div>
                <div className="p-3.5 overflow-x-auto">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <p className="font-bold text-[14px] text-slate-700">Dịch vụ / sản phẩm ({order.serviceLines.length} dòng)</p>
                    <p className="text-[13px] text-slate-500">Doanh thu: <b>{fmtMoney(order.revenue)}</b> · Lợi nhuận: <b>{fmtMoney(order.profit)}</b></p>
                  </div>
                  <table className="tbl w-full text-[12.5px] min-w-[840px]">
                    <thead><tr><th>Mã</th><th>Tên</th><th>Mô tả</th><th>SL</th><th>Giá vốn</th><th>Giá bán</th><th>Thành tiền</th>{mode === GETFLY_MODE_SHIPMENT_AND_FINANCE && <th>VAT % *</th>}</tr></thead>
                    <tbody>
                      {order.serviceLines.map((line) => (
                        <tr key={line.lineId} data-testid={`getfly-line-${line.lineId}`}>
                          <td className="font-bold">{fmtText(line.code)}</td>
                          <td className="font-semibold">{fmtText(line.name)}</td>
                          <td>{fmtText(line.description)}</td>
                          <td>{fmtNum(line.qty)}</td>
                          <td>{fmtMoney(line.cost)}</td>
                          <td>{fmtMoney(line.price)}</td>
                          <td>{fmtMoney(line.revenue)}</td>
                          {mode === GETFLY_MODE_SHIPMENT_AND_FINANCE && (
                            <td>
                              {orderNeedsFinance(order) ? (
                                <input
                                  value={vatByLineId[line.lineId] ?? ""}
                                  onChange={(event) => setVat(line.lineId, event.target.value)}
                                  inputMode="decimal"
                                  placeholder="Nhập VAT"
                                  className={cx(inputCls(vatByLineId[line.lineId]?.trim() ? "ok" : "missing"), "min-w-[115px]")}
                                  data-testid={`getfly-vat-${line.lineId}`}
                                  aria-label={`VAT ${order.orderId} ${line.lineId}`}
                                />
                              ) : <span className="text-slate-400">— bỏ qua</span>}
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border-2 border-indigo-200 bg-indigo-50/60 p-3.5 space-y-3" data-testid="getfly-commit-panel">
            <p className="font-extrabold text-[15px] text-[#0f2a4a]">Phạm vi nhập</p>
            <label className="flex items-start gap-2.5 rounded-xl border-2 border-white bg-white p-3 cursor-pointer">
              <input type="radio" name="getfly-mode" value={GETFLY_MODE_SHIPMENT_ONLY} checked={mode === GETFLY_MODE_SHIPMENT_ONLY} onChange={() => { setMode(GETFLY_MODE_SHIPMENT_ONLY); setLocalError(""); }} data-testid="getfly-mode-shipment-only" />
              <span><b>CHỈ TẠO LÔ TỪ GETFLY</b><span className="block text-[13px] text-slate-600">Tạo lô thiếu theo mã đơn, khách, ngày, trạng thái. Không ghi giá vốn/giá bán/VAT vào Finance Actual.</span></span>
            </label>
            <label className="flex items-start gap-2.5 rounded-xl border-2 border-white bg-white p-3 cursor-pointer">
              <input type="radio" name="getfly-mode" value={GETFLY_MODE_SHIPMENT_AND_FINANCE} checked={mode === GETFLY_MODE_SHIPMENT_AND_FINANCE} onChange={() => { setMode(GETFLY_MODE_SHIPMENT_AND_FINANCE); setLocalError(""); }} data-testid="getfly-mode-finance" />
              <span><b>TẠO LÔ + GHI DỊCH VỤ THỰC TẾ</b><span className="block text-[13px] text-slate-600">Mỗi lô mới phải có Giá vốn, Giá bán và VAT do operator nhập. VAT trống bị từ chối; VAT 0 là một câu trả lời hợp lệ.</span></span>
            </label>
            {mode === GETFLY_MODE_SHIPMENT_AND_FINANCE && (
              <p className="text-[13px] text-indigo-900">Đang chờ VAT cho {missingLineCount} dòng dịch vụ của {missingOrders.length} lô mới. Các lô đã có sẽ được bỏ qua.</p>
            )}
            {financeProblems.length > 0 && mode === GETFLY_MODE_SHIPMENT_AND_FINANCE && (
              <div className="rounded-lg border border-amber-300 bg-amber-50 p-2.5 text-[13px] text-amber-900" data-testid="getfly-finance-warning">
                VAT / tiền bắt buộc chưa đủ — XÁC NHẬN sẽ bị chặn cho đến khi operator nhập đủ. Ví dụ: {financeProblems[0]}
              </div>
            )}
            {commitResults.length > 0 && (
              <div className="space-y-2" data-testid="getfly-results">
                <p className="font-bold text-[14px]">Kết quả authoritative từ backend</p>
                {commitResults.map((row, index) => {
                  const status = String(row.status || "");
                  const ok = status === "CREATED" || status === "SKIPPED_ALREADY_EXISTS";
                  return <div key={`${String(row.orderId)}-${index}`} className={cx("rounded-lg border p-2.5 text-[13px]", ok ? "border-emerald-300 bg-emerald-50 text-emerald-900" : "border-red-300 bg-red-50 text-red-900")}>
                    <span className="font-extrabold">{String(row.orderId || "UNKNOWN")}</span> · {statusLabel(status)} {row.message ? `· ${String(row.message)}` : ""} {row.error ? `· ${String(row.error)}` : ""} {Array.isArray(row.errors) ? `· ${row.errors.join(" ")}` : ""}
                    {status === "CREATED" && <CheckCircle2 size={15} className="inline ml-1" />}
                  </div>;
                })}
              </div>
            )}
            <div className="flex flex-wrap items-center gap-2">
              <PrimaryBtn onClick={commit} disabled={Boolean(pendingCommit) || !hasPreview}>
                {pendingCommit ? <LoaderCircle size={17} className="animate-spin" /> : <CheckCircle2 size={17} />}
                {pendingCommit ? "ĐANG CHỜ BACKEND…" : "XÁC NHẬN NHẬP"}
              </PrimaryBtn>
              <GhostBtn onClick={() => { setMode(GETFLY_MODE_SHIPMENT_ONLY); setCommitResults([]); setLocalError(""); setTransportError(""); }}>ĐỔI VỀ CHỈ TẠO LÔ</GhostBtn>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
