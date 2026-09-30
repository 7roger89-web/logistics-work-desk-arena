import { useState } from "react";
import { BookOpen } from "lucide-react";

const NOTEBOOKS = [
  {
    label: "Notebook hiện tại",
    url: "https://notebook.google.com/notebook/f5c90bb9-9244-4027-a9ae-84f6ab023a09/preview",
  },
  {
    label: "Bộ Thông Tin Truyền Thông",
    url: "https://notebook.google.com/notebook/242b2eed-2a6d-4bb8-a0b2-c347d79e1047/preview",
  },
  {
    label: "Bộ Y Tế",
    url: "https://notebook.google.com/notebook/5a5d2a90-9881-49fc-9c65-e820b9497088/preview",
  },
  {
    label: "Hóa Chất",
    url: "https://notebook.google.com/notebook/50716c0b-7da6-4984-9f05-be0b19be4b95/preview",
  },
  {
    label: "Bộ KHCN",
    url: "https://notebook.google.com/notebook/6afaf293-e6d1-42f4-beaa-208f2d417f92/preview",
  },
] as const;

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
  const [open, setOpen] = useState(false);

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
            width: "min(360px, calc(100vw - 32px))",
          }}
          data-testid="notebooklm-menu"
        >
          <div className="px-3 pb-2 pt-1">
            <p className="text-[13px] font-extrabold text-[#0f2a4a]">NotebookLM</p>
            <p className="text-[12px] text-slate-500">Chọn bộ tài liệu cần mở</p>
          </div>
          <div className="space-y-1">
            {NOTEBOOKS.map((notebook) => (
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
            ))}
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
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
