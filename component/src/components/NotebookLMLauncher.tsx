import { BookOpen } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";

export default function NotebookLMLauncher() {
  const loc = useLocation();
  const active = loc.pathname.startsWith("/notebooklm");

  return (
    <NavLink
      to="/notebooklm"
      className={
        "no-print fixed bottom-24 right-4 z-30 inline-flex min-h-[48px] items-center gap-2 rounded-2xl px-4 py-3 text-[14px] font-extrabold shadow-lg md:bottom-6 md:right-6 " +
        (active
          ? "bg-[#0f2a4a] text-white"
          : "border border-slate-200 bg-white text-[#0f2a4a] hover:bg-slate-50")
      }
      aria-label="Mở NotebookLM"
      data-testid="notebooklm-launcher"
    >
      <BookOpen size={19} />
      NotebookLM
    </NavLink>
  );
}
