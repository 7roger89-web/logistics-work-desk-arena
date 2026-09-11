// ============================================================================
// LOGI_NOTEBOOK_WORKSPACE_01 — /so-tay: a READ-ONLY handbook & work-notes page.
//
// The backend already assembled `handbook` from reference material this repo
// owns (core.config constants, the locked docgen rules, the official
// trade-compliance source registry, the RBAC matrix) plus the team's own notes
// read through the existing knowledge_base reader. This page renders it and
// filters it in the browser.
//
// Deliberately absent: an editor, a publish/approval flow, a search service, a
// second content store. A missing note corpus renders as an honest empty state
// — never as a sample article.
// ============================================================================

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  ExternalLink,
  Info,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import { ICONS, SectionTitle, ToneBadge } from "../components/ui";
import { cx } from "../lib/format";
import { useStore } from "../lib/store";
import type {
  HandbookEntry,
  HandbookProvenance,
  HandbookSection,
  NotebookHandbook,
} from "../lib/viewmodel";

// ----------------------------------------------------------------------------
// search — a plain text filter over the delivered rows (§8: proportional, no
// index, no service). Matching is substring + case-insensitive, on every
// visible field of an article.
// ----------------------------------------------------------------------------

function haystackOf(section: HandbookSection, entry: HandbookEntry): string {
  const cells = entry.table ? entry.table.rows.flat().join(" ") : "";
  return [
    section.label,
    entry.title,
    entry.summary,
    entry.bullets.join(" "),
    entry.tags.join(" "),
    cells,
  ]
    .join(" ")
    .toLowerCase();
}

function isUrl(value: string): boolean {
  return /^https:\/\//i.test(value.trim());
}

function ProvenanceBox({ provenance }: { provenance: HandbookProvenance }) {
  return (
    <div
      data-testid="handbook-provenance"
      className="rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5 text-[12.5px] leading-relaxed text-slate-600"
    >
      <p className="font-bold uppercase tracking-wide text-slate-500">Nguồn</p>
      <p className="mt-1 break-words font-mono text-[12px] text-[#0f2a4a]">
        {provenance.source}
      </p>
      <ul className="mt-1 space-y-0.5">
        <li>
          Phiên bản:{" "}
          <span className="font-semibold">
            {provenance.version ?? "không có trong nguồn"}
          </span>
        </li>
        <li>
          Cập nhật:{" "}
          <span className="font-semibold">
            {provenance.updated ?? "không có trong nguồn"}
          </span>
        </li>
        <li>
          Phụ trách:{" "}
          <span className="font-semibold">
            {provenance.owner ?? "không có trong nguồn"}
          </span>
        </li>
      </ul>
      {provenance.note ? (
        <p className="mt-1.5 border-t border-slate-200 pt-1.5 text-slate-500">
          {provenance.note}
        </p>
      ) : null}
    </div>
  );
}

function TableBlock({ table }: { table: NonNullable<HandbookEntry["table"]> }) {
  const linkable = table.columns.length <= 2 || table.columns.some((c) => /url|link/i.test(c));
  const render = (value: string) =>
    linkable && isUrl(value) ? (
      <a
        href={value}
        target="_blank"
        rel="noreferrer"
        className="inline-flex max-w-full items-start gap-1 break-all font-semibold text-blue-800 underline decoration-blue-300 underline-offset-2"
      >
        <ExternalLink size={13} className="mt-0.5 shrink-0" />
        <span className="break-all">{value}</span>
      </a>
    ) : (
      <span className="break-words">{value}</span>
    );

  return (
    <div className="mt-3">
      {/* Phone: stacked rows so a wide table never forces horizontal scrolling. */}
      <div className="space-y-2 md:hidden">
        {table.rows.map((row, rowIndex) => (
          <div
            key={`m-${rowIndex}`}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2.5"
            data-testid="handbook-row-mobile"
          >
            {row.map((cell, cellIndex) => (
              <div key={`c-${cellIndex}`} className="py-0.5 text-[13.5px] leading-relaxed">
                <span className="mr-1.5 text-[11.5px] font-bold uppercase tracking-wide text-slate-500">
                  {table.columns[cellIndex] ?? ""}
                </span>
                {render(cell)}
              </div>
            ))}
          </div>
        ))}
      </div>
      {/* Tablet/desktop: a real table, cells wrapping instead of scrolling. */}
      <table className="hidden w-full border-collapse md:table">
        <thead>
          <tr className="bg-slate-50">
            {table.columns.map((col, index) => (
              <th
                key={`h-${index}`}
                scope="col"
                className="border-b border-slate-200 px-2.5 py-2 text-left text-[11.5px] font-extrabold uppercase tracking-wide text-slate-500"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, rowIndex) => (
            <tr key={`r-${rowIndex}`} className="align-top odd:bg-white even:bg-slate-50/50">
              {row.map((cell, cellIndex) => (
                <td
                  key={`d-${cellIndex}`}
                  className="border-b border-slate-100 px-2.5 py-2 text-[13.5px] leading-relaxed text-slate-700"
                >
                  {render(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1.5 text-[12px] text-slate-400">
        {table.rows.length} dòng · đọc từ nguồn, không phải dữ liệu mẫu
      </p>
    </div>
  );
}

function ArticleView({
  section,
  entry,
  onBack,
}: {
  section: HandbookSection;
  entry: HandbookEntry;
  onBack: () => void;
}) {
  const Icon = ICONS[section.icon] ?? BookOpen;
  return (
    <article className="space-y-3" data-testid="handbook-article" data-article-id={entry.id}>
      <button
        type="button"
        onClick={onBack}
        className="btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 bg-white px-3.5 py-2 text-[13.5px] font-bold text-[#0f2a4a]"
        data-testid="handbook-back"
      >
        <ArrowLeft size={17} /> Về danh mục
      </button>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5">
        <p className="flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500">
          <Icon size={15} className="shrink-0" /> {section.label}
        </p>
        <h3 className="mt-2 break-words text-[19px] leading-snug font-extrabold text-[#0f2a4a] md:text-[21px]">
          {entry.title}
        </h3>
        <p className="mt-1.5 text-[14px] leading-relaxed text-slate-600">{entry.summary}</p>

        {entry.bullets.length > 0 ? (
          <ul className="mt-3 space-y-1.5">
            {entry.bullets.map((bullet, index) => (
              <li
                key={index}
                className="flex gap-2 rounded-xl bg-slate-50 px-3 py-2 text-[13.5px] leading-relaxed text-slate-700"
              >
                <span className="mt-0.5 text-slate-400">•</span>
                <span className="min-w-0 break-words">{bullet}</span>
              </li>
            ))}
          </ul>
        ) : null}

        {entry.table ? <TableBlock table={entry.table} /> : null}

        {entry.tags.length > 0 ? (
          <p className="mt-3 flex flex-wrap gap-1.5">
            {entry.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-semibold text-slate-600"
              >
                #{tag}
              </span>
            ))}
          </p>
        ) : null}

        {entry.links.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3">
            {entry.links.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] px-3.5 py-2 text-[13.5px] font-bold text-white"
              >
                {link.label} <ArrowRight size={15} />
              </Link>
            ))}
          </div>
        ) : null}
      </div>

      <ProvenanceBox provenance={entry.provenance ?? section.provenance} />
    </article>
  );
}

function EntryCard({
  section,
  entry,
  onOpen,
}: {
  section: HandbookSection;
  entry: HandbookEntry;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onOpen}
      data-testid="handbook-entry"
      data-entry-id={entry.id}
      className="btn-press w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-blue-300"
    >
      <div className="flex items-start justify-between gap-3">
        <h4 className="min-w-0 break-words text-[15.5px] leading-snug font-extrabold text-[#0f2a4a]">
          {entry.title}
        </h4>
        <ArrowRight size={18} className="mt-0.5 shrink-0 text-slate-400" />
      </div>
      <p className="mt-1.5 text-[13.5px] leading-relaxed text-slate-600">{entry.summary}</p>
      {entry.table && entry.table.rows.length > 0 ? (
        <div className="mt-2 space-y-1" data-testid="handbook-preview">
          {entry.table.rows.slice(0, 2).map((row, index) => (
            <p
              key={index}
              className="break-words rounded-lg bg-slate-50 px-2 py-1 font-mono text-[12px] text-slate-600"
            >
              {row.filter((cell) => cell.trim() !== "").join(" · ")}
            </p>
          ))}
          {entry.table.rows.length > 2 ? (
            <p className="text-[12px] font-semibold text-slate-400">
              +{entry.table.rows.length - 2} dòng nữa trong bài
            </p>
          ) : null}
        </div>
      ) : null}
      <div className="mt-2.5 flex flex-wrap items-center gap-2">
        <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11.5px] font-bold text-slate-600">
          {section.label}
        </span>
        {entry.table ? (
          <span className="rounded-md bg-blue-50 px-2 py-0.5 text-[11.5px] font-bold text-blue-800">
            {entry.table.rows.length} dòng
          </span>
        ) : null}
        <span className="text-[11.5px] font-semibold text-slate-400">
          {entry.tags.slice(0, 3).map((tag) => `#${tag}`).join(" ")}
        </span>
      </div>
    </button>
  );
}

function EmptyHandbook({ reason }: { reason: "pending" | "no-source" }) {
  return (
    <div className="max-w-[760px]">
      <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600">
        {reason === "pending"
          ? "Chưa nhận được dữ liệu Sổ tay từ backend. Trang không hiển thị nội dung mẫu thay thế."
          : "Nguồn tham chiếu chưa trả về mục nào có nội dung. Sổ tay hiển thị đúng trạng thái này thay vì tự soạn bài."}
      </div>
    </div>
  );
}

export default function Notebook() {
  const { handbook } = useStore();
  const [sectionId, setSectionId] = useState<string | null>(null);
  const [articleId, setArticleId] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const q = query.trim().toLowerCase();

  const flat = useMemo(() => {
    const out: { section: HandbookSection; entry: HandbookEntry; hay: string }[] = [];
    for (const section of handbook?.sections ?? []) {
      for (const entry of section.entries) {
        out.push({ section, entry, hay: haystackOf(section, entry) });
      }
    }
    return out;
  }, [handbook]);

  const visible = useMemo(() => {
    const scoped = q.length === 0 && sectionId
      ? flat.filter((row) => row.section.id === sectionId)
      : flat;
    if (!q) return scoped;
    return scoped.filter((row) => row.hay.includes(q));
  }, [flat, q, sectionId]);

  const opened = useMemo(() => {
    if (!articleId) return null;
    return flat.find((row) => row.entry.id === articleId) ?? null;
  }, [flat, articleId]);

  if (!handbook) return <EmptyHandbook reason="pending" />;
  const data: NotebookHandbook = handbook;
  if (data.counts.entryCount === 0 && !q) return <EmptyHandbook reason="no-source" />;

  const selectedSection = data.sections.find((section) => section.id === sectionId) ?? null;
  const emptySections = data.sections.filter((section) => section.state && section.entries.length === 0);

  const openArticle = (id: string) => {
    setArticleId(id);
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "auto" });
  };
  const closeArticle = () => setArticleId(null);
  const pickSection = (id: string) => {
    setSectionId(id === sectionId ? null : id);
    setArticleId(null);
    setQuery("");
  };

  return (
    <div className="max-w-[1240px] space-y-4 pb-3">
      {/* Header — read-only by design, and it says so. */}
      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="handbook-header">
        <SectionTitle
          icon={<BookOpen size={20} />}
          title="Sổ tay vận hành"
          sub="Tra cứu quy trình, chứng từ, mã dịch vụ và phân quyền — đúng theo tài liệu hệ thống đang dùng."
          right={<ToneBadge tone="blue" size="sm">CHỈ ĐỌC</ToneBadge>}
        />
        <div className="mt-3 flex flex-wrap items-center gap-2 text-[12.5px] font-semibold text-slate-600">
          <span className="rounded-lg bg-slate-100 px-2 py-1">
            {data.counts.availableSectionCount}/{data.counts.sectionCount} mục có nội dung
          </span>
          <span className="rounded-lg bg-slate-100 px-2 py-1">{data.counts.entryCount} bài tham chiếu</span>
          <span className="rounded-lg bg-slate-100 px-2 py-1" data-testid="handbook-note-count">
            {data.counts.noteTotal ?? data.counts.noteCount} ghi chú đội ngũ
          </span>
          <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 text-emerald-800">
            <ShieldCheck size={13} /> {data.readOnly ? "không sửa từ trang này" : "có chỉnh sửa"}
          </span>
        </div>

        {/* Search: one input, plain substring filtering of already-delivered text. */}
        <div className="relative mt-3">
          <Search size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setArticleId(null);
            }}
            placeholder="Tìm theo tiêu đề, nội dung, mã hoặc từ khóa…"
            aria-label="Tìm trong sổ tay"
            data-testid="handbook-search"
            className="min-h-[48px] w-full rounded-xl border-2 border-slate-200 bg-white pl-10 pr-10 text-[15px] font-medium text-slate-800 outline-none focus:border-blue-400"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Xóa từ khóa"
              className="touch-target absolute right-1 top-1/2 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-xl text-slate-400 hover:bg-slate-100"
            >
              <X size={17} />
            </button>
          ) : null}
        </div>

        {/* Category controls — chips on phone, always ≥44px touch targets. */}
        <div className="mt-3 flex flex-wrap gap-2" data-testid="handbook-categories">
          <button
            type="button"
            onClick={() => {
              setSectionId(null);
              setArticleId(null);
              setQuery("");
            }}
            className={cx(
              "min-h-[44px] rounded-xl border px-3 py-2 text-[13px] font-bold transition-colors",
              sectionId === null
                ? "border-[#0f2a4a] bg-[#0f2a4a] text-white"
                : "border-slate-200 bg-white text-[#0f2a4a] hover:border-blue-300"
            )}
            data-testid="handbook-category-all"
          >
            Tất cả
          </button>
          {data.sections.map((section) => (
            <button
              key={section.id}
              type="button"
              onClick={() => pickSection(section.id)}
              className={cx(
                "min-h-[44px] rounded-xl border px-3 py-2 text-[13px] font-bold transition-colors",
                section.id === sectionId
                  ? "border-[#0f2a4a] bg-[#0f2a4a] text-white"
                  : "border-slate-200 bg-white text-[#0f2a4a] hover:border-blue-300"
              )}
              data-testid={`handbook-category-${section.id}`}
            >
              {section.label}
              <span className="ml-1.5 text-[11.5px] font-extrabold opacity-70">
                {section.entries.length}
              </span>
            </button>
          ))}
        </div>
      </section>

      {opened ? (
        <ArticleView section={opened.section} entry={opened.entry} onBack={closeArticle} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-w-0 space-y-2.5">
            {selectedSection && !q ? (
              <p className="text-[13px] leading-relaxed text-slate-500" data-testid="handbook-section-lead">
                <span className="font-extrabold text-[#0f2a4a]">{selectedSection.label}:</span>{" "}
                {selectedSection.lead}
              </p>
            ) : null}

            {visible.length === 0 ? (
              <div
                className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600"
                data-testid="handbook-no-result"
              >
                Không có bài nào khớp “{query}”. Sổ tay chỉ tìm trong nội dung đã có
                trong nguồn và không tạo bài mới.
              </div>
            ) : (
              visible.map(({ section, entry }) => (
                <EntryCard
                  key={`${section.id}-${entry.id}`}
                  section={section}
                  entry={entry}
                  onOpen={() => openArticle(entry.id)}
                />
              ))
            )}
          </div>

          {/* Side rail: source honesty + what this page does NOT contain. */}
          <aside className="min-w-0 space-y-3">
            {selectedSection && !q ? (
              <ProvenanceBox provenance={selectedSection.provenance} />
            ) : null}

            {emptySections.length > 0 ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5" data-testid="handbook-empty-sections">
                <p className="text-[12px] font-extrabold uppercase tracking-wide text-amber-800">
                  Mục chưa có nguồn
                </p>
                <ul className="mt-1 space-y-1 text-[13px] leading-relaxed text-amber-900">
                  {emptySections.map((section) => (
                    <li key={section.id}>
                      <span className="font-bold">{section.label}</span> — {section.state?.text}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5">
              <p className="flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500">
                <Info size={14} /> Trang này không có
              </p>
              <ul className="mt-1 space-y-1 text-[12.5px] leading-relaxed text-slate-600">
                {data.unavailable.map((line) => (
                  <li key={line} className="break-words">
                    {line}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
