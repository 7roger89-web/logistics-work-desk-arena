import { BookOpen } from "lucide-react";

const NOTEBOOK_URL =
  "https://notebook.google.com/notebook/f5c90bb9-9244-4027-a9ae-84f6ab023a09/preview";

function openNotebookLM() {
  const availWidth = window.screen.availWidth || window.innerWidth;
  const availHeight = window.screen.availHeight || window.innerHeight;
  const width = Math.min(availWidth, Math.max(960, Math.floor(availWidth * 0.82)));
  const height = Math.min(availHeight, Math.max(720, Math.floor(availHeight * 0.86)));
  const left = Math.max(0, Math.floor((availWidth - width) / 2));
  const top = Math.max(0, Math.floor((availHeight - height) / 2));

  const popup = window.open(
    NOTEBOOK_URL,
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
  return (
    <button
      type="button"
      onClick={openNotebookLM}
      className="no-print fixed bottom-24 right-4 z-30 inline-flex min-h-[48px] items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-[14px] font-extrabold text-[#0f2a4a] shadow-lg hover:bg-slate-50 md:bottom-6 md:right-6"
      aria-label="Mở NotebookLM trong cửa sổ riêng"
      title="Mở NotebookLM"
      data-testid="notebooklm-launcher"
    >
      <BookOpen size={19} />
      NotebookLM
    </button>
  );
}
