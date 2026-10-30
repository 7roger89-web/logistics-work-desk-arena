// ============================================================================
// Issue #236 — Journey Map node discussion, INSIDE the map.
//
// One root-level comment list + ONE level of replies + composer, attached to
// the node the operator clicked. The conversation itself is the existing
// backend thread (`core.journey_notes`); this file is presentation only:
//
//   node click  → typed `journey_focus` intent (already existed in PR #235)
//   data        → vm.journeyDiscussion (exactly one lot + one stage, bounded)
//   write       → `journey_note_create` → same note backend → fresh readback
//   download    → `journey_note_download` → server reads ONE file → bytes on
//                 the bounded download channel (never in the shared payload)
//
// There is no optimistic persistence: the composer clears only when the
// backend's authoritative outcome for its requestId arrives in lastWrites.
// ============================================================================
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { Paperclip, Reply, Send, X } from "lucide-react";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { downloadBinaryFile } from "../lib/format";
import {
  getViewModel,
  subscribeViewModel,
  type JourneyNote,
  type JourneyNoteAttachment,
} from "../lib/viewmodel";

interface PickedFile {
  name: string;
  mime: string;
  size: number;
  base64: string;
}

const handledDownloads: Record<string, number> = {};

function newRequestId(prefix: string): string {
  const random = typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${random}`;
}

function stamp(value: string): string {
  const text = String(value || "").replace("T", " ");
  return text.slice(0, 19) || "—";
}

function AttachmentRow({
  noteId,
  item,
  disabled,
  onDownload,
}: {
  noteId: string;
  item: JourneyNoteAttachment;
  disabled: boolean;
  onDownload: (noteId: string, item: JourneyNoteAttachment) => void;
}) {
  return (
    <li className="flex items-center gap-1.5 text-[11.5px] text-slate-600">
      <Paperclip size={12} className="shrink-0 text-slate-400" aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate">{item.name}</span>
      <span className="shrink-0 text-slate-400">{item.sizeLabel}</span>
      <button
        type="button"
        disabled={disabled}
        data-testid={`journey-discussion-download-${item.id}`}
        onClick={() => onDownload(noteId, item)}
        className="touch-target shrink-0 rounded border border-slate-200 px-2 text-[11px] font-bold text-[#1e5aa8] disabled:opacity-50"
      >
        Tải
      </button>
    </li>
  );
}

function NoteCard({
  note,
  replies,
  canWrite,
  onReply,
  onDownload,
  downloadBusy,
}: {
  note: JourneyNote;
  replies: JourneyNote[];
  canWrite: boolean;
  onReply: (note: JourneyNote) => void;
  onDownload: (noteId: string, item: JourneyNoteAttachment) => void;
  downloadBusy: boolean;
}) {
  const internal = note.visibility === "INTERNAL";
  const card = (row: JourneyNote, reply: boolean) => (
    <div
      key={row.id}
      data-testid={`journey-discussion-note-${row.id}`}
      data-visibility={row.visibility}
      className={
        reply
          ? "mt-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5"
          : "rounded-lg border border-slate-200 bg-white px-2.5 py-2"
      }
    >
      <div className="flex flex-wrap items-baseline gap-x-1.5 text-[11px]">
        <span className="font-extrabold text-slate-800">{row.author_name || "—"}</span>
        <span className="text-slate-400">{row.author_kind === "customer" ? "Khách hàng" : "Trường Thành"}</span>
        <span className="text-slate-400">· {stamp(row.created_at)}</span>
        {internal && (
          <span className="rounded bg-amber-100 px-1 text-[10px] font-bold text-amber-800">🔒 Nội bộ</span>
        )}
      </div>
      {row.body ? (
        <p className="mt-1 whitespace-pre-wrap break-words text-[12.5px] leading-snug text-slate-800">{row.body}</p>
      ) : null}
      {row.attachments.length > 0 && (
        <ul className="mt-1 space-y-1">
          {row.attachments.map((item) => (
            <AttachmentRow
              key={item.id}
              noteId={row.id}
              item={item}
              disabled={downloadBusy}
              onDownload={onDownload}
            />
          ))}
        </ul>
      )}
      {!reply && canWrite && (
        <button
          type="button"
          data-testid={`journey-discussion-reply-${row.id}`}
          onClick={() => onReply(row)}
          className="touch-target mt-1 inline-flex items-center gap-1 rounded px-1 text-[11.5px] font-bold text-[#1e5aa8]"
        >
          <Reply size={12} aria-hidden="true" /> Trả lời
        </button>
      )}
    </div>
  );
  return (
    <li className="space-y-1">
      {card(note, false)}
      {replies.length > 0 && <ul className="ml-3 border-l-2 border-slate-200 pl-2">{replies.map((r) => card(r, true))}</ul>}
    </li>
  );
}

export default function JourneyDiscussionPanel({
  shipmentId,
  nodeId,
  nodeLabel,
  onClose,
  style,
}: {
  shipmentId: string;
  nodeId: string;
  nodeLabel: string;
  onClose: () => void;
  style: React.CSSProperties;
}) {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const discussion = vm?.journeyDiscussion ?? null;
  const matches = Boolean(
    discussion
      && discussion.shipmentId === shipmentId
      && (discussion.nodeId === nodeId || discussion.stageId === nodeId),
  );
  const active = matches ? discussion : null;

  const [body, setBody] = useState("");
  const [replyTo, setReplyTo] = useState<JourneyNote | null>(null);
  const [file, setFile] = useState<PickedFile | null>(null);
  const [fileError, setFileError] = useState("");
  // Fail-safe default: internal until the operator explicitly chooses "Khách xem".
  const [visibility, setVisibility] = useState<"INTERNAL" | "CUSTOMER">("INTERNAL");
  const [sending, setSending] = useState("");
  const [downloadPending, setDownloadPending] = useState("");
  const [error, setError] = useState("");
  const panelRef = useRef<HTMLDivElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  // The map pans on pointerdown and zooms on wheel; neither may fire while the
  // operator is writing/reading inside the panel.
  useEffect(() => {
    const el = panelRef.current;
    if (!el) return;
    const stopWheel = (event: WheelEvent) => event.stopPropagation();
    el.addEventListener("wheel", stopWheel, { passive: true });
    return () => el.removeEventListener("wheel", stopWheel);
  }, []);

  // Authoritative outcome of THIS panel's last write (never transport alone).
  const outcome = sending
    ? (vm?.lastWrites ?? []).find((row) => row.event === "journey_note_create" && row.requestId === sending)
    : undefined;
  useEffect(() => {
    if (!outcome) return;
    if (outcome.ok) {
      setBody("");
      setFile(null);
      setReplyTo(null);
      setError("");
    } else {
      setError(String(outcome.error || "Không gửi được bình luận."));
    }
    setSending("");
  }, [outcome]);

  // One file, delivered once, after the server re-proved read permission.
  const download = active?.download ?? null;
  useEffect(() => {
    if (!download?.base64) return;
    const key = `${download.noteId}:${download.attachmentId}`;
    if (handledDownloads[key] === download.seq) return;
    handledDownloads[key] = download.seq;
    downloadBinaryFile(download.name, download.base64, download.mime);
    setDownloadPending("");
  }, [download]);

  const downloadOutcome = downloadPending
    ? (vm?.lastWrites ?? []).find(
        (row) => row.event === "journey_note_download" && row.requestId === downloadPending,
      )
    : undefined;
  useEffect(() => {
    if (!downloadOutcome) return;
    if (!downloadOutcome.ok) {
      setError(String(downloadOutcome.error || "Không tải được chứng từ."));
    }
    setDownloadPending("");
  }, [downloadOutcome]);

  const onPickFile = (chosen: File | null) => {
    setFileError("");
    setFile(null);
    if (!chosen) return;
    const limit = active?.maxBytes || 20 * 1024 * 1024;
    if (chosen.size > limit) {
      setFileError(`Tệp vượt giới hạn ${Math.floor(limit / (1024 * 1024))} MB.`);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const encoded = String(reader.result || "").split(",")[1] || "";
      if (!encoded) {
        setFileError("Không đọc được tệp đã chọn.");
        return;
      }
      setFile({ name: chosen.name, mime: chosen.type || "", size: chosen.size, base64: encoded });
    };
    reader.onerror = () => setFileError("Không đọc được tệp đã chọn.");
    reader.readAsDataURL(chosen);
  };

  const send = () => {
    if (!active || sending) return;
    const text = body.trim();
    if (!text && !file) {
      setError("Nhập nội dung hoặc đính kèm chứng từ.");
      return;
    }
    setError("");
    const requestId = newRequestId("JRN");
    setSending(requestId);
    const ok = dispatchLogiEvent("journey_note_create", {
      requestId,
      shipmentId,
      nodeId,
      stageId: active.stageId,
      body: text,
      visibility,
      replyToId: replyTo?.id || "",
      files: file ? [{ name: file.name, mime: file.mime, size: file.size, base64: file.base64 }] : [],
    });
    if (!ok) {
      setSending("");
      setError("Chưa kết nối được backend.");
    }
  };

  const downloadFile = (noteId: string, item: JourneyNoteAttachment) => {
    if (downloadPending) return;
    const requestId = newRequestId("JRN-DOWN");
    setDownloadPending(requestId);
    setError("");
    if (!dispatchLogiEvent("journey_note_download", {
      requestId,
      shipmentId,
      nodeId,
      stageId: active?.stageId || nodeId,
      noteId,
      attachmentId: item.id,
    })) {
      setDownloadPending("");
      setError("Chưa kết nối được backend.");
    }
  };

  const roots = active?.notes ?? [];
  return (
    <div
      ref={panelRef}
      data-testid="journey-discussion-panel"
      data-node={nodeId}
      data-shipment={shipmentId}
      role="dialog"
      aria-label={`Trao đổi công đoạn ${active?.stageLabel || nodeLabel}`}
      className="absolute z-40 flex flex-col overflow-hidden rounded-xl border-2 border-slate-300 bg-white shadow-2xl"
      style={style}
      onPointerDown={(event) => event.stopPropagation()}
      onDoubleClick={(event) => event.stopPropagation()}
    >
      <div className="flex items-start justify-between gap-2 border-b bg-[#0f2a4a] px-3 py-2 text-white">
        <div className="min-w-0">
          <p className="truncate text-[11px] font-bold uppercase tracking-wide text-slate-300">
            💬 Trao đổi · {active?.stageLabel || nodeLabel}
          </p>
          <p className="truncate text-[11.5px] text-slate-200">
            Lô {shipmentId}
            {active && active.nodeLabel ? ` · node ${active.nodeLabel}` : ""}
            {active ? ` · ${active.count} trao đổi` : ""}
          </p>
        </div>
        <button
          type="button"
          data-testid="journey-discussion-close"
          onClick={onClose}
          aria-label="Đóng trao đổi"
          className="touch-target shrink-0 rounded border border-white/30 bg-white/10 p-1"
        >
          <X size={15} aria-hidden="true" />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2.5 py-2" data-testid="journey-discussion-thread">
        {!active && !discussion && <p className="py-6 text-center text-[12px] text-slate-500">Đang tải trao đổi…</p>}
        {!matches && discussion && (
          <p className="py-6 text-center text-[12px] text-slate-500">Đang tải trao đổi của công đoạn này…</p>
        )}
        {active?.error && <p role="alert" className="rounded bg-red-50 px-2 py-1 text-[12px] text-red-700">{active.error}</p>}
        {active && roots.length === 0 && !active.error && (
          <p className="py-6 text-center text-[12px] text-slate-500" data-testid="journey-discussion-empty">
            Chưa có trao đổi nào ở công đoạn này. Viết bình luận đầu tiên.
          </p>
        )}
        {roots.length > 0 && (
          <ul className="space-y-2">
            {roots.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                replies={note.replies ?? []}
                canWrite={Boolean(active?.canWrite)}
                onReply={(row) => {
                  setReplyTo(row);
                  setError("");
                }}
                onDownload={downloadFile}
                downloadBusy={Boolean(downloadPending)}
              />
            ))}
          </ul>
        )}
      </div>

      {active && (
        <div className="shrink-0 border-t bg-slate-50 px-2.5 py-2">
          {!active.canWrite ? (
            <p className="text-[11.5px] text-slate-500">Tài khoản này chỉ được xem trao đổi của lô.</p>
          ) : (
            <>
              {replyTo && (
                <div className="mb-1 flex items-center gap-1 rounded bg-blue-50 px-2 py-1 text-[11px] text-blue-800" data-testid="journey-discussion-reply-banner">
                  <Reply size={12} aria-hidden="true" />
                  <span className="min-w-0 flex-1 truncate">Đang trả lời {replyTo.author_name || "bình luận"}</span>
                  <button type="button" onClick={() => setReplyTo(null)} aria-label="Bỏ trả lời" className="shrink-0 font-bold">
                    <X size={12} aria-hidden="true" />
                  </button>
                </div>
              )}
              <textarea
                data-testid="journey-discussion-body"
                value={body}
                onChange={(event) => setBody(event.target.value)}
                rows={2}
                maxLength={4000}
                placeholder={replyTo ? "Viết phản hồi…" : "Viết bình luận…"}
                className="w-full resize-y rounded-lg border border-slate-300 px-2 py-1.5 text-[12.5px]"
              />
              <div className="mt-1 flex flex-wrap items-center gap-1.5">
                <input
                  ref={fileInput}
                  type="file"
                  data-testid="journey-discussion-file"
                  accept="image/*,application/pdf,.doc,.docx,.xls,.xlsx"
                  className="hidden"
                  onChange={(event) => onPickFile(event.currentTarget.files?.[0] ?? null)}
                />
                <button
                  type="button"
                  onClick={() => fileInput.current?.click()}
                  className="touch-target inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-2 text-[11.5px] font-bold text-slate-700"
                >
                  <Paperclip size={12} aria-hidden="true" /> Đính kèm
                </button>
                {file && <span className="max-w-[130px] truncate text-[11px] text-slate-600">{file.name}</span>}
                {active.canSeeInternal && (
                  <label className="inline-flex items-center gap-1 text-[11px] text-slate-600">
                    <span>Ai xem?</span>
                    <select
                      data-testid="journey-discussion-visibility"
                      value={visibility}
                      onChange={(event) => setVisibility(event.currentTarget.value as "INTERNAL" | "CUSTOMER")}
                      className="rounded border border-slate-300 bg-white px-1 py-0.5 text-[11px]"
                    >
                      <option value="INTERNAL">🔒 Nội bộ</option>
                      <option value="CUSTOMER">👁 Khách xem</option>
                    </select>
                  </label>
                )}
                <button
                  type="button"
                  data-testid="journey-discussion-send"
                  disabled={Boolean(sending)}
                  onClick={send}
                  className="touch-target ml-auto inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] px-3 text-[12px] font-extrabold text-white disabled:opacity-50"
                >
                  <Send size={12} aria-hidden="true" /> {sending ? "Đang gửi…" : "Gửi"}
                </button>
              </div>
              {fileError && <p role="alert" className="mt-1 text-[11.5px] text-red-700">{fileError}</p>}
              {error && <p role="alert" data-testid="journey-discussion-error" className="mt-1 text-[11.5px] text-red-700">{error}</p>}
            </>
          )}
        </div>
      )}
    </div>
  );
}
