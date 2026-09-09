export default function Tabs({ tabs, active, onChange }: { tabs: { key: string; label: string }[]; active: string; onChange: (key: string) => void }) {
  return (
    <div className="flex gap-1 overflow-x-auto no-scrollbar border-b border-border">
      {tabs.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={`relative shrink-0 px-4 py-3 text-[14px] font-semibold whitespace-nowrap transition-colors ${active === t.key ? 'text-navy-900' : 'text-ink-400 hover:text-ink-600'}`}
        >
          {t.label}
          {active === t.key && <span className="absolute left-2 right-2 -bottom-px h-[3px] rounded-full bg-accent-500" />}
        </button>
      ))}
    </div>
  );
}
