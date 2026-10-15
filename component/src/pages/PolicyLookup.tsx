import { useEffect, useState, useSyncExternalStore } from "react";
import { BookOpen, ExternalLink, Plus, Settings, Trash2 } from "lucide-react";
import { SectionTitle } from "../components/ui";
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
  const target = window.open(url, "logistics-notebooklm");
  target?.focus();
}

export default function PolicyLookup() {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const registry = vm?.notebookLM;
  const notebooks = registry?.items ?? [];
  const canManage = registry?.canManage === true;

  const [manage, setManage] = useState(false);
  const [draft, setDraft] = useState<NotebookLMItem[]>([]);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!manage) setDraft(notebooks.map((item) => ({ ...item })));
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

  const save = () => {
    if (pending) return;
    if (draft.length === 0) {
      setError("Phải giữ ít nhất một nguồn tra cứu chính sách.");
      return;
    }
    if (draft.some((item) => !item.label.trim() || !item.url.trim())) {
      setError("Mỗi nguồn phải có đủ tên và URL.");
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
    <div className="max-w-[1100px] space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <SectionTitle
            icon={<BookOpen size={18} />}
            title="Tra cứu chính sách"
            sub="Các bộ NotebookLM chính sách dùng chung của công ty. Chọn một bộ để mở bằng tài khoản Google đang đăng nhập."
          />
          {canManage && !manage && (
            <button
              type="button"
              onClick={() => {
                setDraft(notebooks.map((item) => ({ ...item })));
                setError("");
                setManage(true);
              }}
              className="inline-flex min-h-[42px] items-center gap-2 rounded-xl border border-slate-200 px-3.5 py-2 text-[13px] font-extrabold text-[#0f2a4a] hover:bg-slate-50"
              data-testid="policy-manage"
            >
              <Settings size={16} /> Quản lý nguồn
            </button>
          )}
        </div>

        {!manage ? (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {notebooks.map((notebook) => (
              <button
                key={notebook.url}
                type="button"
                onClick={() => openNotebookLM(notebook.url)}
                className="group flex w-full min-w-0 min-h-[86px] items-center justify-between gap-3 rounded-2xl border border-slate-200 p-4 text-left hover:border-[#1e5aa8] hover:bg-slate-50"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-slate-100 text-[#1e5aa8]">
                    <BookOpen size={20} />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-[15px] font-extrabold text-[#0f2a4a]">
                      {notebook.label}
                    </span>
                    <span className="mt-0.5 block text-[12.5px] text-slate-500">
                      Mở NotebookLM
                    </span>
                  </span>
                </span>
                <ExternalLink
                  size={17}
                  className="shrink-0 text-slate-400 group-hover:text-[#1e5aa8]"
                />
              </button>
            ))}
          </div>
        ) : (
          <div className="mt-3 space-y-3" data-testid="policy-manager">
            {draft.map((item, index) => (
              <div
                key={`${index}-${item.url}`}
                className="rounded-2xl border border-slate-200 p-3"
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
                      placeholder="Tên nguồn, ví dụ: Bộ Công Thương"
                      className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-[13.5px] outline-none focus:border-[#1e5aa8]"
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
                      className="w-full rounded-xl border border-slate-200 px-3 py-2.5 font-mono text-[12px] outline-none focus:border-[#1e5aa8]"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setDraft((rows) => rows.filter((_, i) => i !== index))
                    }
                    className="self-start rounded-xl border border-red-200 p-2.5 text-red-700 hover:bg-red-50"
                    aria-label="Xóa nguồn"
                  >
                    <Trash2 size={17} />
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
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3.5 py-2.5 text-[13px] font-bold text-[#0f2a4a] hover:bg-slate-50"
            >
              <Plus size={16} /> Thêm nguồn chính sách
            </button>

            {error && (
              <p className="rounded-xl bg-red-50 px-3 py-2.5 text-[13px] font-semibold text-red-700">
                {error}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setManage(false);
                  setError("");
                }}
                disabled={!!pending}
                className="rounded-xl border border-slate-200 px-4 py-2.5 text-[13px] font-bold text-slate-700"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={save}
                disabled={!!pending}
                className="rounded-xl bg-[#0f2a4a] px-4 py-2.5 text-[13px] font-extrabold text-white disabled:opacity-50"
                data-testid="policy-save"
              >
                {pending ? "ĐANG LƯU…" : "LƯU DANH SÁCH"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
