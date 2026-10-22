import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { ArrowLeft } from "lucide-react";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import { inputCls, PrimaryBtn } from "./ui";

const SOURCES: { id: string; label: string }[] = [
  { id: "", label: "Không ghi nguồn" },
  { id: "zalo", label: "Zalo" },
  { id: "wechat", label: "WeChat" },
  { id: "bank", label: "Ngân hàng" },
  { id: "other", label: "Khác" },
];

function newRequestId(): string {
  return `INBOX-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

export default function InboxComposer({
  onCancel,
  onSaved,
  onPendingChange,
}: {
  onCancel: () => void;
  onSaved: (keepOpen: boolean) => void;
  onPendingChange?: (pending: boolean) => void;
}) {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [rawText, setRawText] = useState("");
  const [source, setSource] = useState("");
  const [title, setTitle] = useState("");
  const [sourceRef, setSourceRef] = useState("");
  const [occurredAt, setOccurredAt] = useState("");
  const [pending, setPending] = useState("");
  const [keepOpen, setKeepOpen] = useState(false);
  const [error, setError] = useState("");
  const lock = useRef(false);

  useEffect(() => {
    onPendingChange?.(Boolean(pending));
  }, [pending, onPendingChange]);

  useEffect(() => {
    if (!pending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (row) => row.event === "inbox_snippet_create" && row.requestId === pending
    );
    if (!outcome) return;
    lock.current = false;
    setPending("");
    onPendingChange?.(false);
    if (!outcome.ok) {
      setError(outcome.error || "Không lưu được mẩu tin.");
      return;
    }
    setRawText("");
    setTitle("");
    setSourceRef("");
    setOccurredAt("");
    setError("");
    onSaved(keepOpen);
  }, [vm?.lastWrites, pending, keepOpen, onSaved]);

  const save = (continueAfter: boolean) => {
    if (lock.current) return;
    const text = rawText.trim();
    if (!text) {
      setError("Nội dung là trường bắt buộc duy nhất.");
      return;
    }
    lock.current = true;
    const requestId = newRequestId();
    setError("");
    setKeepOpen(continueAfter);
    setPending(requestId);
    const ok = dispatchLogiEvent("inbox_snippet_create", {
      requestId,
      rawText: text,
      source,
      title: title.trim(),
      sourceRef: sourceRef.trim(),
      occurredAt: occurredAt.trim(),
    });
    if (!ok) {
      lock.current = false;
      setPending("");
      setError("Component chưa kết nối backend.");
    }
  };

  return (
    <div data-testid="inbox-composer" className="space-y-3">
      <button
        type="button"
        onClick={onCancel}
        className="touch-target inline-flex items-center gap-1.5 text-[13.5px] font-semibold text-slate-600 hover:text-[#0f2a4a]"
      >
        <ArrowLeft size={16} /> Về danh sách thêm
      </button>
      <div>
        <p className="font-extrabold text-[18px] text-[#0f2a4a]">Ghi chú nhanh</p>
        <p className="text-[13.5px] text-slate-500 mt-1">
          Dán nội dung Zalo / WeChat / ngân hàng ngay. Chưa cần chọn hợp đồng.
          Mẩu tin gốc được giữ nguyên — đây chưa phải giao dịch đã thanh toán.
        </p>
      </div>
      <label className="block">
        <span className="block text-[13px] font-bold text-slate-600 mb-1">Nội dung <span className="text-red-600">*</span></span>
        <textarea
          data-testid="inbox-composer-text"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          rows={7}
          autoFocus
          placeholder="Dán tin nhắn, số tiền, số hợp đồng… tiếng Việt hoặc tiếng Trung."
          className="w-full rounded-xl border-2 border-slate-200 focus:border-[#1e5aa8] bg-white px-3.5 py-3 text-[15px] min-h-[160px] placeholder:text-slate-400"
        />
      </label>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="block text-[13px] font-bold text-slate-600 mb-1">Nguồn (không bắt buộc)</span>
          <select
            data-testid="inbox-composer-source"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className={inputCls()}
          >
            {SOURCES.map((row) => (
              <option key={row.id || "none"} value={row.id}>{row.label}</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="block text-[13px] font-bold text-slate-600 mb-1">Ngày trên tin (không bắt buộc)</span>
          <input
            data-testid="inbox-composer-date"
            value={occurredAt}
            onChange={(e) => setOccurredAt(e.target.value)}
            placeholder="YYYY-MM-DD — để trống = chưa biết"
            className={inputCls()}
          />
        </label>
        <label className="block">
          <span className="block text-[13px] font-bold text-slate-600 mb-1">Tiêu đề / tag (không bắt buộc)</span>
          <input
            data-testid="inbox-composer-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ví dụ: chuyển USD, nhà máy trả RMB"
            className={inputCls()}
          />
        </label>
        <label className="block">
          <span className="block text-[13px] font-bold text-slate-600 mb-1">Mã tham chiếu nguồn (không bắt buộc)</span>
          <input
            data-testid="inbox-composer-ref"
            value={sourceRef}
            onChange={(e) => setSourceRef(e.target.value)}
            placeholder="Số tin, mã giao dịch giả lập…"
            className={inputCls()}
          />
        </label>
      </div>
      {error && <p className="text-[13.5px] font-medium text-red-700" role="alert">{error}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
        <PrimaryBtn
          testId="inbox-composer-save"
          disabled={Boolean(pending)}
          onClick={() => save(false)}
        >
          {pending && !keepOpen ? "Đang lưu…" : "Lưu"}
        </PrimaryBtn>
        <button
          type="button"
          data-testid="inbox-composer-save-next"
          disabled={Boolean(pending)}
          onClick={() => save(true)}
          className="btn-press touch-target inline-flex items-center justify-center rounded-xl border-2 border-[#0f2a4a] text-[#0f2a4a] font-bold text-[15.5px] px-5 min-h-[48px] disabled:opacity-50"
        >
          {pending && keepOpen ? "Đang lưu…" : "Lưu & ghi tiếp"}
        </button>
      </div>
    </div>
  );
}
