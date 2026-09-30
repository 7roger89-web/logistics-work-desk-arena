const NOTEBOOK_URL =
  "https://notebook.google.com/notebook/f5c90bb9-9244-4027-a9ae-84f6ab023a09/preview";

export default function NotebookLMEmbed() {
  return (
    <section className="flex min-h-[calc(100vh-112px)] flex-col gap-3" data-testid="notebooklm-embed">
      <div>
        <h1 className="text-[20px] font-extrabold text-[#0f2a4a] md:text-[22px]">NotebookLM</h1>
        <p className="mt-0.5 text-[13px] text-slate-500">
          Dùng trực tiếp tài khoản Google đang đăng nhập trên trình duyệt này.
        </p>
      </div>
      <div className="min-h-[720px] flex-1 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <iframe
          src={NOTEBOOK_URL}
          title="NotebookLM Logistics"
          className="h-full min-h-[720px] w-full border-0"
          referrerPolicy="strict-origin-when-cross-origin"
        />
      </div>
    </section>
  );
}
