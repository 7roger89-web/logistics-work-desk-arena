import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { Link } from "react-router-dom";
import { Link2, Paperclip, Search, Unlink } from "lucide-react";
import { contractPath } from "../lib/contractRoute";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { cx, downloadBinaryFile, matchLoose, UNKNOWN } from "../lib/format";
import { shipmentPath } from "../lib/shipmentRoute";
import { getViewModel, subscribeViewModel, type InboxAttachment, type InboxSnippet } from "../lib/viewmodel";
import { PrimaryBtn, SheetDialog, ToneBadge, inputCls } from "../components/ui";

const SOURCE_LABEL: Record<string, string> = {
  zalo: "Zalo",
  wechat: "WeChat",
  bank: "Ngân hàng",
  other: "Khác",
};

function newRequestId(prefix = "INBOX-LINK"): string {
  return `${prefix}-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

function sourceLabel(source: string): string {
  if (!source) return "Không ghi nguồn";
  return SOURCE_LABEL[source] || source;
}

function snippetTitle(row: InboxSnippet): string {
  if (row.title.trim()) return row.title.trim();
  const line = row.rawText.split(/\n/)[0]?.trim() || "";
  if (line) return line.length > 80 ? `${line.slice(0, 80)}…` : line;
  const fileName = row.attachments?.[0]?.name;
  return fileName || row.id;
}

function useInboxDownload() {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const handled = useRef<Record<string, number>>({});
  useEffect(() => {
    const groups = [
      vm?.inbox?.snippets ?? [],
      ...Object.values(vm?.inbox?.byContractId ?? {}),
      ...Object.values(vm?.inbox?.byShipmentId ?? {}),
    ];
    for (const list of groups) {
      for (const row of list) {
        for (const item of row.attachments ?? []) {
          if (!item.downloadAvailable || !item.downloadBase64) continue;
          const seq = item.downloadSeq ?? 0;
          if (handled.current[item.id] === seq) continue;
          handled.current[item.id] = seq;
          downloadBinaryFile(item.name, item.downloadBase64, item.mime || "application/octet-stream");
        }
      }
    }
  }, [vm?.inbox]);
}

function AttachmentList({
  snippet,
  shipmentId,
  contractId,
}: {
  snippet: InboxSnippet;
  shipmentId?: string;
  contractId?: string;
}) {
  const rows = snippet.attachments ?? [];
  if (!rows.length) return null;
  const startDownload = (item: InboxAttachment) => {
    dispatchLogiEvent("inbox_snippet_download", {
      requestId: newRequestId("INBOX-DOWN"),
      snippetId: snippet.id,
      attachmentId: item.id,
      ...(shipmentId ? { shipmentId } : {}),
      ...(contractId ? { contractId } : {}),
    });
  };
  return (
    <ul className="mt-2 space-y-1.5" data-testid="inbox-attachment-list">
      {rows.map((item) => (
        <li key={item.id} className="flex items-center gap-2 text-[13px] text-slate-600">
          <Paperclip size={14} className="shrink-0 text-slate-400" />
          <span className="min-w-0 flex-1 truncate">{item.name}</span>
          <span className="text-slate-400">{item.sizeLabel}</span>
          <button
            type="button"
            data-testid="inbox-attachment-download"
            onClick={() => startDownload(item)}
            className="touch-target rounded-lg border border-slate-200 px-2.5 min-h-[36px] font-bold text-[#1e5aa8]"
          >
            Tải
          </button>
        </li>
      ))}
    </ul>
  );
}

export function ContractLinkedSnippets({ contractId }: { contractId: string }) {
  useInboxDownload();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const fromMap = vm?.inbox?.byContractId?.[contractId];
  const rows = fromMap ?? (vm?.inbox?.snippets ?? []).filter((row) => (row.contractIds ?? []).includes(contractId));
  return (
    <section data-testid="contract-linked-inbox" className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
      <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Thông tin đã ghép</h3>
      <p className="text-[13.5px] text-slate-500 mt-1">
        Mẩu tin gốc, chưa xác minh. Ghép không tạo giao dịch đã thanh toán.
      </p>
      {rows.length === 0 ? (
        <p className="text-[14px] text-slate-500 mt-3">Chưa ghép mẩu tin nào vào hợp đồng này.</p>
      ) : (
        <div className="mt-3 space-y-2">
          {rows.map((row) => (
            <article key={row.id} className="rounded-xl border border-slate-200 p-3.5" data-testid="contract-linked-inbox-card">
              <p className="font-bold text-[14.5px] text-[#0f2a4a]">{snippetTitle(row)}</p>
              <p className="text-[12.5px] text-slate-500 mt-0.5">{sourceLabel(row.source)} · {row.createdBy || UNKNOWN} · {row.createdAt || UNKNOWN}</p>
              <p className="whitespace-pre-wrap text-[14px] text-slate-700 mt-2">{row.rawText || UNKNOWN}</p>
              <AttachmentList snippet={row} contractId={contractId} />
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export function ShipmentInboxSnippets({ shipmentId }: { shipmentId: string }) {
  useInboxDownload();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const fromMap = vm?.inbox?.byShipmentId?.[shipmentId];
  const rows = fromMap ?? (vm?.inbox?.snippets ?? []).filter((row) => (row.shipmentIds ?? []).includes(shipmentId));
  return (
    <section data-testid="shipment-inbox-snippets" className="mt-4 rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
      <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Thông tin từ Bể</h3>
      <p className="text-[13.5px] text-slate-500 mt-1">
        Tệp và mẩu tin đã ghép từ Bể thông tin. Bỏ ghép không xóa file đã lưu.
      </p>
      {rows.length === 0 ? (
        <p className="text-[14px] text-slate-500 mt-3">Chưa ghép mẩu tin nào vào lô này.</p>
      ) : (
        <div className="mt-3 space-y-2">
          {rows.map((row) => (
            <article key={row.id} className="rounded-xl border border-slate-200 p-3.5" data-testid="shipment-inbox-card">
              <p className="font-bold text-[14.5px] text-[#0f2a4a]">{snippetTitle(row)}</p>
              <p className="text-[12.5px] text-slate-500 mt-0.5">{sourceLabel(row.source)} · {row.createdBy || UNKNOWN} · {row.createdAt || UNKNOWN}</p>
              {row.rawText ? <p className="whitespace-pre-wrap text-[14px] text-slate-700 mt-2">{row.rawText}</p> : null}
              <AttachmentList snippet={row} shipmentId={shipmentId} />
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default function Inbox() {
  useInboxDownload();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const snippets = vm?.inbox?.snippets ?? [];
  const contracts = vm?.contracts ?? [];
  const shipments = vm?.shipments ?? [];
  const canRead = vm?.inbox?.canRead !== false;
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "unlinked" | "linked">("all");
  const [selected, setSelected] = useState<string[]>([]);
  const [linkOpen, setLinkOpen] = useState(false);
  const [targetType, setTargetType] = useState<"contract" | "snippet" | "shipment">("contract");
  const [targetId, setTargetId] = useState("");
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const lock = useRef(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      dispatchLogiEvent("inbox_snippet_search", {
        requestId: newRequestId("INBOX-Q"),
        query,
        filter,
      });
    }, 280);
    return () => window.clearTimeout(timer);
  }, [query, filter]);

  const visible = useMemo(() => {
    return snippets.filter((row) => {
      if (filter === "linked" && !row.linked) return false;
      if (filter === "unlinked" && row.linked) return false;
      if (!query.trim()) return true;
      return matchLoose(
        [
          row.rawText,
          row.title,
          row.source,
          row.sourceRef,
          (row.contractIds ?? []).join(" "),
          (row.shipmentIds ?? []).join(" "),
          (row.attachments ?? []).map((item) => item.name).join(" "),
          row.createdBy,
        ].join(" "),
        query
      );
    });
  }, [snippets, filter, query]);

  const toggle = (id: string) => {
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  };

  const sendLink = (action: "link" | "unlink") => {
    if (lock.current) return;
    const ids = selected.length ? selected : [];
    if (!ids.length || !targetId) {
      setError("Chọn mẩu tin và đích ghép.");
      return;
    }
    lock.current = true;
    const requestId = newRequestId();
    setError("");
    setPending(requestId);
    const ok = dispatchLogiEvent("inbox_snippet_link", {
      requestId,
      snippetIds: ids,
      action,
      targetType,
      targetId,
    });
    if (!ok) {
      lock.current = false;
      setPending("");
      setError("Component chưa kết nối backend.");
    }
  };

  useEffect(() => {
    if (!pending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (row) => row.event === "inbox_snippet_link" && row.requestId === pending
    );
    if (!outcome) return;
    lock.current = false;
    setPending("");
    if (!outcome.ok) {
      setError(outcome.error || "Không ghép được.");
      return;
    }
    setLinkOpen(false);
    setSelected([]);
    setTargetId("");
  }, [vm?.lastWrites, pending]);

  if (!canRead) {
    return (
      <div data-testid="inbox-page" className="space-y-4 max-w-[980px]">
        <h1 className="text-[24px] md:text-[28px] font-extrabold text-[#0f2a4a]">Bể thông tin</h1>
        <p className="rounded-2xl border border-slate-200 p-6 text-[14.5px] text-slate-600">
          Bạn không có quyền xem bể thông tin.
        </p>
      </div>
    );
  }

  return (
    <div data-testid="inbox-page" className="space-y-4 max-w-[980px]">
      <div>
        <p className="text-[12.5px] font-bold uppercase tracking-wide text-slate-400">Ghi nhanh · ghép sau</p>
        <h1 className="text-[24px] md:text-[28px] font-extrabold text-[#0f2a4a]">Bể thông tin</h1>
        <p className="text-[14.5px] text-slate-600 mt-1">
          {vm?.inbox?.count ?? snippets.length} mẩu · {vm?.inbox?.unlinkedCount ?? 0} chưa ghép · {vm?.inbox?.linkedCount ?? 0} đã ghép.
          Nội dung gốc không bị ghi đè. Đây chưa phải sổ kế toán.
        </p>
      </div>

      <div className="rounded-2xl bg-amber-50 border border-amber-200 p-3.5 text-[13.5px] text-amber-950">
        Mẩu tin là bằng chứng nguồn chưa xác minh. Ghép với hợp đồng hoặc lô hàng không đánh dấu đã thanh toán, không cộng USD với RMB.
      </div>

      <div className="flex flex-col md:flex-row gap-2.5">
        <label className="flex-1 flex items-center rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-white px-3 min-h-[48px]">
          <Search size={18} className="text-slate-400 shrink-0" />
          <input
            data-testid="inbox-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Tìm nội dung, số hợp đồng, lô hàng, nguồn…"
            className="w-full bg-transparent px-2.5 py-2.5 text-[15px] outline-none"
          />
        </label>
        <div className="flex gap-2" data-testid="inbox-filters">
          {([
            ["all", "Tất cả"],
            ["unlinked", "Chưa ghép"],
            ["linked", "Đã ghép"],
          ] as const).map(([id, label]) => (
            <button
              key={id}
              type="button"
              data-testid={`inbox-filter-${id}`}
              onClick={() => setFilter(id)}
              className={cx(
                "touch-target rounded-xl px-3 min-h-[48px] text-[13.5px] font-bold border-2",
                filter === id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <PrimaryBtn testId="inbox-link-open" disabled={!selected.length} onClick={() => { setLinkOpen(true); setError(""); }}>
          <Link2 size={18} /> Ghép thông tin ({selected.length})
        </PrimaryBtn>
        <Link to="/" className="text-[13.5px] font-semibold text-slate-500">Về tổng quan</Link>
      </div>

      {vm?.inbox?.hasMore ? (
        <p className="text-[13px] text-slate-500">Còn mẩu tin cũ hơn. Dùng ô tìm để gọi đúng mẩu, không cuộn hết 500 dòng.</p>
      ) : null}

      {visible.length === 0 ? (
        <p data-testid="inbox-empty" className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-[14.5px] text-slate-500">
          {snippets.length === 0 ? "Chưa có mẩu tin. Bấm Thêm → Ghi chú nhanh để lưu ngay." : "Không có mẩu tin khớp bộ lọc."}
        </p>
      ) : (
        <div className="space-y-2.5">
          {visible.map((row) => (
            <article
              key={row.id}
              data-testid="inbox-card"
              className={cx("rounded-2xl border bg-white p-4", selected.includes(row.id) ? "border-[#1e5aa8]" : "border-slate-200")}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1.5 w-5 h-5 accent-[#0f2a4a]"
                  checked={selected.includes(row.id)}
                  onChange={() => toggle(row.id)}
                  aria-label={`Chọn ${snippetTitle(row)}`}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-extrabold text-[15.5px] text-[#0f2a4a]">{snippetTitle(row)}</p>
                    <ToneBadge tone={row.linked ? "green" : "amber"} size="sm">{row.linked ? "Đã ghép" : "Chưa ghép"}</ToneBadge>
                    <ToneBadge tone="gray" size="sm">{sourceLabel(row.source)}</ToneBadge>
                  </div>
                  <p className="text-[12.5px] text-slate-500 mt-1">
                    {row.createdBy || UNKNOWN} · {row.createdAt || UNKNOWN}
                    {row.occurredAt ? ` · ngày trên tin ${row.occurredAt}` : ` · ngày trên tin ${UNKNOWN}`}
                    {` · số tiền ${UNKNOWN}`}
                  </p>
                  {row.rawText ? <p className="whitespace-pre-wrap text-[14.5px] text-slate-700 mt-2">{row.rawText}</p> : null}
                  <AttachmentList snippet={row} />
                  {(row.contractIds ?? []).length > 0 && (
                    <p className="text-[13px] mt-2">
                      Hợp đồng:{" "}
                      {(row.contractIds ?? []).map((id) => (
                        <Link key={id} to={contractPath(id)} className="font-bold text-[#1e5aa8] mr-2">{id}</Link>
                      ))}
                    </p>
                  )}
                  {(row.shipmentIds ?? []).length > 0 && (
                    <p className="text-[13px] mt-1">
                      Lô hàng:{" "}
                      {(row.shipmentIds ?? []).map((id) => (
                        <Link key={id} to={shipmentPath(id)} className="font-bold text-[#1e5aa8] mr-2">{id}</Link>
                      ))}
                    </p>
                  )}
                  {(row.linkedSnippetIds ?? []).length > 0 && (
                    <p className="text-[13px] text-slate-600 mt-1">Ghép với mẩu: {row.linkedSnippetIds.join(", ")}</p>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {linkOpen && (
        <SheetDialog id="inbox-link-sheet" testId="inbox-link-sheet" labelledBy="inbox-link-title" width={520} pending={Boolean(pending)} onClose={() => setLinkOpen(false)}>
          <p id="inbox-link-title" className="font-extrabold text-[18px] text-[#0f2a4a]">Ghép thông tin</p>
          <p className="text-[13.5px] text-slate-500 mt-1 mb-4">
            {selected.length} mẩu đã chọn. Có thể ghép nhiều mẩu vào một hợp đồng hoặc một lô; RMB không bắt buộc 1:1 với USD.
          </p>
          <div className="flex flex-wrap gap-2 mb-3">
            <button type="button" className={cx("touch-target rounded-xl px-3 min-h-[44px] font-bold border-2", targetType === "contract" ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200")} onClick={() => { setTargetType("contract"); setTargetId(""); }}>Hợp đồng</button>
            <button type="button" data-testid="inbox-link-type-shipment" className={cx("touch-target rounded-xl px-3 min-h-[44px] font-bold border-2", targetType === "shipment" ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200")} onClick={() => { setTargetType("shipment"); setTargetId(""); }}>Lô hàng</button>
            <button type="button" className={cx("touch-target rounded-xl px-3 min-h-[44px] font-bold border-2", targetType === "snippet" ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200")} onClick={() => { setTargetType("snippet"); setTargetId(""); }}>Mẩu khác</button>
          </div>
          {targetType === "contract" ? (
            <label className="block">
              <span className="block text-[13px] font-bold text-slate-600 mb-1">Hợp đồng hiện có</span>
              <select data-testid="inbox-link-contract" value={targetId} onChange={(e) => setTargetId(e.target.value)} className={inputCls()}>
                <option value="">— Chọn hợp đồng —</option>
                {contracts.map((row) => (
                  <option key={row.id} value={row.id}>{row.id} · {row.client || row.company}</option>
                ))}
              </select>
            </label>
          ) : targetType === "shipment" ? (
            <label className="block">
              <span className="block text-[13px] font-bold text-slate-600 mb-1">Lô hàng hiện có</span>
              <select data-testid="inbox-link-shipment" value={targetId} onChange={(e) => setTargetId(e.target.value)} className={inputCls()}>
                <option value="">— Chọn lô hàng —</option>
                {shipments.map((row) => (
                  <option key={row.id} value={row.id}>{row.id} · {row.customer || ""}</option>
                ))}
              </select>
            </label>
          ) : (
            <label className="block">
              <span className="block text-[13px] font-bold text-slate-600 mb-1">Mẩu tin đích</span>
              <select data-testid="inbox-link-snippet" value={targetId} onChange={(e) => setTargetId(e.target.value)} className={inputCls()}>
                <option value="">— Chọn mẩu —</option>
                {snippets.filter((row) => !selected.includes(row.id)).map((row) => (
                  <option key={row.id} value={row.id}>{snippetTitle(row)}</option>
                ))}
              </select>
            </label>
          )}
          {error && <p className="text-[13.5px] font-medium text-red-700 mt-3" role="alert">{error}</p>}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-4">
            <PrimaryBtn testId="inbox-link-save" disabled={Boolean(pending)} onClick={() => sendLink("link")}>Ghép</PrimaryBtn>
            <button
              type="button"
              data-testid="inbox-unlink-save"
              disabled={Boolean(pending)}
              onClick={() => sendLink("unlink")}
              className="btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl border-2 border-slate-300 font-bold min-h-[48px]"
            >
              <Unlink size={16} /> Bỏ ghép
            </button>
          </div>
        </SheetDialog>
      )}
    </div>
  );
}
