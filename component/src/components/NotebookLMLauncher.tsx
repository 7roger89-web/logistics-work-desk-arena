import { useEffect, useState, useSyncExternalStore } from "react";
import { BookOpen, Plus, Settings, Trash2 } from "lucide-react";
import { dispatchLogiEvent } from "../lib/dispatcher";
import {
  getViewModel,
  subscribeViewModel,
  type NotebookLMItem,
} from "../lib/viewmodel";

function newRequestId(): string {
  return `NOTEBOOKLM-${Date.now().toString(36).toUpperCase()}-${Math.random()
    .toString(36)
    .slice(2, 8)
    .toUpperCase()}`;
}

function openNotebookLM(url: string) {
  const availWidth = window.screen.availWidth || window.innerWidth;
  const availHeight = window.screen.availHeight || window.innerHeight;
  const width = Math.min(availWidth, Math.max(960, Math.floor(availWidth * 0.82)));
  const height = Math.min(availHeight, Math.max(720, Math.floor(availHeight * 0.86)));
  const left = Math.max(0, Math.floor((availWidth - width) / 2));
  const top = Math.max(0, Math.floor((availHeight - height) / 2));

  const popup = window.open(
    url,
    "logistics-notebooklm",
    [
      "popup=yes",
      `width=${width}`,
      `height=${height}`,
      `left=${left}`,
      `top=${top}`,
      "resizable=yes",
      "scrollbars=yes",
    ].join(","),
  );
  popup?.focus();
}

export default function NotebookLMLauncher() {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const registry = vm?.notebookLM;
  const notebooks = registry?.items ?? [];
  const canManage = registry?.canManage === true;

  const [open, setOpen] = useState(false);
  const [manage, setManage] = useState(false);
  const [draft, setDraft] = useState<NotebookLMItem[]>([]);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!manage) {
      setDraft(notebooks.map((item) => ({ ...item })));
    }
  }, [manage, registry?.items]);

  useEffect(() => {
    if (!pending) return;
    const outcome = vm?.lastWrites?.find(
      (item) =>
        item.event === "notebooklm_registry_save" &&
        item.requestId === pending,
    );
    if (!outcome) return;
    setPending(null);
    if (outcome.ok) {
      setManage(false);
      setError("");
    } else {
      setError(outcome.error || "Backend từ chối lưu danh sách NotebookLM.");
    }
  }, [pending, vm?.lastWrites]);

  const startManage = () => {
    setDraft(notebooks.map((item) => ({ ...item })));
    setError("");
    setManage(true);
  };

  const save = () => {
    if (pending) return;
    if (draft.length === 0) {
      setError("Phải giữ ít nhất một NotebookLM.");
      return;
    }
    const invalid = draft.find(
      (item) => !item.label.trim() || !item.url.trim(),
    );
    if (invalid) {
      setError("Mỗi NotebookLM phải có đủ tên và URL.");
      return;
    }
    const requestId = newRequestId();
    const sent = dispatchLogiEvent("notebooklm_registry_save", {
      items: draft.map((item) => ({
        label: item.label.trim(),
        url: item.url.trim(),
      })),
      requestId,
    });
    if (!sent) {
      setError("Component chưa kết nối backend — chưa lưu được.");
      return;
    }
    setError("");
    setPending(requestId);
  };

  return (
    <>
      {open && (
        <div
          className="no-print rounded-2xl border border-slate-200 bg-white p-2 shadow-2xl"
          style={{
            position: "fixed",
            right: 16,
            bottom: 152,
            zIndex: 31,
            width: manage
              ? "min(620px, calc(100vw - 32px))"
              : "min(380px, calc(100vw - 32px))",
            maxHeight: "70vh",
            overflowY: "auto",
          }}
          data-testid="notebooklm-menu"
        >
          <div className="flex items-center justify-between gap-2 px-3 pb-2 pt-1">
            <div>
              <p className="text-[13px] font-extrabold text-[#0f2a4a]">NotebookLM</p>
              <p className="text-[12px] text-slate-500">
                {manage ? "Quản lý danh sách dùng chung" : "Chọn bộ tài liệu cần mở"}
              </p>
            </div>
            {canManage && !manage && (
              <button
                type="button"
                onClick={startManage}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-[12px] font-bold text-[#0f2a4a] hover:bg-slate-50"
                data-testid="notebooklm-manage"
              >
                <Settings size={14} /> Quản lý
              </button>
            )}
          </div>

          {manage ? (
            <div className="space-y-2 px-1 pb-1">
              {draft.map((item, index) => (
                <div
                  key={`${index}-${item.url}`}
                  className="rounded-xl border border-slate-200 p-2.5"
                >
                  <div className="flex gap-2">
                    <div className="min-w-0 flex-1 space-y-2">
                      <input
                        value={item.label}
                        onChange={(e) =>
                          setDraft((rows) =>
                            rows.map((row, i) =>
                              i === index ? { ...row, label: e.target.value } : row,
                            ),
                          )
                        }
                        placeholder="Tên notebook"
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-[13px]"
                      />
                      <input
                        value={item.url}
                        onChange={(e) =>
                          setDraft((rows) =>
                            rows.map((row, i) =>
                              i === index ? { ...row, url: e.target.value } : row,
                            ),
                          )
                        }
                        placeholder="https://notebook.google.com/notebook/.../preview"
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-[12px]"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        setDraft((rows) => rows.filter((_, i) => i !== index))
                      }
                      className="self-start rounded-lg border border-red-200 p-2 text-red-700 hover:bg-red-50"
                      aria-label="Xóa notebook"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}

              <button
                type="button"
                onClick={() =>
                  setDraft((rows) =>
                    rows.length >= (registry?.maxItems ?? 30)
                      ? rows
                      : [...rows, { label: "", url: "" }],
                  )
                }
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-[12.5px] font-bold text-[#0f2a4a] hover:bg-slate-50"
              >
                <Plus size={15} /> Thêm NotebookLM
              </button>

              {error && (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-[12.5px] font-semibold text-red-700">
                  {error}
                </p>
              )}

              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setManage(false);
                    setError("");
                  }}
                  disabled={!!pending}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-[12.5px] font-bold text-slate-700"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  onClick={save}
                  disabled={!!pending}
                  className="rounded-lg bg-[#0f2a4a] px-3 py-2 text-[12.5px] font-bold text-white disabled:opacity-50"
                  data-testid="notebooklm-save"
                >
                  {pending ? "ĐANG LƯU…" : "LƯU DANH SÁCH"}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              {notebooks.length === 0 ? (
                <p className="px-3 py-3 text-[13px] text-slate-500">
                  Đang tải danh sách NotebookLM…
                </p>
              ) : (
                notebooks.map((notebook) => (
                  <button
                    key={notebook.url}
                    type="button"
                    onClick={() => {
                      openNotebookLM(notebook.url);
                      setOpen(false);
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-[13.5px] font-bold text-slate-700 hover:bg-slate-50"
                  >
                    <BookOpen size={17} className="shrink-0 text-[#1e5aa8]" />
                    <span>{notebook.label}</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      )}

      <button
        type="button"
        onClick={() => {
          setOpen((value) => !value);
          if (open) setManage(false);
        }}
        className="no-print fixed bottom-24 right-4 z-30 inline-flex min-h-[48px] items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-[14px] font-extrabold text-[#0f2a4a] shadow-lg hover:bg-slate-50 md:bottom-6 md:right-6"
        aria-label="Chọn NotebookLM"
        aria-expanded={open}
        title="Chọn NotebookLM"
        data-testid="notebooklm-launcher"
      >
        <BookOpen size={19} />
        NotebookLM
      </button>
    </>
  );
}
