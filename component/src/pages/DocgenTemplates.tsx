// ============================================================================
// LOGI-193 — /bieu-mau: the Admin Office-template lifecycle.
//
// ONE bounded Admin surface over capability the backend already owns:
//
//   UPLOAD an ordinary .docx/.xlsx  →  backend validates + stores + DETECTS
//   CONFIRM/REFINE the mapping ONCE →  backend re-validates against its own
//                                      canonical field whitelist
//   PUBLISH                         →  backend freezes an IMMUTABLE version
//
// The published template then shows up in the SAME shipment document picker
// (ShipmentDocumentPicker) — this page owns only the template lifecycle, never
// a second document system, storage plane or generator.
//
// The browser owns NO mapping logic and NO field list:
//   * `fields`    is the backend's canonical whitelist, verbatim;
//   * `detected`  is the backend's detection, shown as a review aid;
//   * a suggestion is NEVER an assignment — the Admin confirms every row;
//   * only {position, mode, value} triples are sent back, and the backend
//     re-validates them and re-checks Admin RBAC on every write.
//
// `canManage` is a DISPLAY hint. A non-Admin session sees the same list with no
// controls, exactly like /nguoi-dung.
// ============================================================================

import { useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  CircleAlert,
  Eye,
  FileSpreadsheet,
  FileText,
  Info,
  Lock,
  Plus,
  ShieldCheck,
  Upload,
} from "lucide-react";
import {
  Field,
  GhostBtn,
  PrimaryBtn,
  SectionTitle,
  ToneBadge,
  inputCls,
} from "../components/ui";
import { cx, downloadBinaryFile } from "../lib/format";
import { dispatchLogiEvent, type LogiEventName } from "../lib/dispatcher";
import { docgenTemplateWorkspace, getViewModel, subscribeViewModel } from "../lib/viewmodel";
import type {
  LastWriteOutcome,
  UploadedTemplateMapping,
  UploadedTemplateRow,
} from "../lib/viewmodel";

const TEMPLATE_EVENTS = new Set([
  "docgen_template_upload",
  "docgen_template_mapping_save",
  "docgen_template_publish",
  "docgen_template_status_set",
  "docgen_template_preview",
]);

const STATUS_TONE: Record<string, "green" | "amber" | "gray"> = {
  ACTIVE: "green",
  DRAFT: "amber",
  RETIRED: "gray",
};

const STATUS_LABEL: Record<string, string> = {
  ACTIVE: "Đang dùng",
  DRAFT: "Bản nháp",
  RETIRED: "Đã ngừng",
};

function TemplateIcon({ kind }: { kind: string }) {
  return kind === "XLSX"
    ? <FileSpreadsheet size={18} aria-hidden="true" />
    : <FileText size={18} aria-hidden="true" />;
}

export default function DocgenTemplates() {
  const vm = getViewModel();
  const workspace = docgenTemplateWorkspace();
  const [, force] = useState(0);
  useEffect(() => subscribeViewModel(() => force((n) => n + 1)), []);

  const [label, setLabel] = useState("");
  const [category, setCategory] = useState("Biểu mẫu tải lên");
  const [fileName, setFileName] = useState("");
  const [fileBody, setFileBody] = useState("");
  const [fileTooBig, setFileTooBig] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);

  /** The template whose mapping the Admin is confirming. */
  const [editing, setEditing] = useState<UploadedTemplateRow | null>(null);
  const [draftMapping, setDraftMapping] = useState<UploadedTemplateMapping[]>([]);
  const [pending, setPending] = useState<string>("");
  const [notice, setNotice] = useState<{ tone: "green" | "amber" | "red"; text: string } | null>(null);

  const canManage = workspace?.canManage === true;
  const templates = useMemo(() => workspace?.templates ?? [], [workspace?.templates]);
  const fields = useMemo(() => workspace?.fields ?? [], [workspace?.fields]);
  const fieldsByKey = useMemo(
    () => new Map(fields.map((field) => [field.key, field])),
    [fields]
  );
  const groups = useMemo(() => {
    const seen: string[] = [];
    for (const field of fields) if (!seen.includes(field.group)) seen.push(field.group);
    return seen;
  }, [fields]);

  // Match the authoritative outcome by requestId — transport success is never
  // treated as write success.
  const outcomes: LastWriteOutcome[] = vm?.lastWrites ?? [];
  useEffect(() => {
    if (!pending) return;
    const outcome = outcomes.find(
      (row) => row.requestId === pending && TEMPLATE_EVENTS.has(String(row.event ?? ""))
    );
    if (!outcome) return;
    setPending("");
    if (outcome.ok) {
      if (outcome.event === "docgen_template_preview") {
        // The trial file is the whole point of the review step: hand it to the
        // browser and name any position the Admin still has to resolve.  Nothing
        // was persisted, so there is no history to refresh.
        const preview = (outcome.readback ?? {}) as {
          fileName?: string;
          mime?: string;
          bytesBase64?: string;
          marker?: string;
          missing?: string[];
        };
        downloadBinaryFile(
          preview.fileName ?? "XEM-THU.docx",
          preview.bytesBase64 ?? null,
          preview.mime ?? "application/octet-stream"
        );
        const gaps = (preview.missing ?? []).filter(Boolean);
        setNotice({
          tone: gaps.length ? "amber" : "green",
          text: gaps.length
            ? `Bản xem thử đã tải (dữ liệu giả ${preview.marker ?? ""}). Còn thiếu: ${gaps.join("; ")}`
            : `Bản xem thử đã tải bằng dữ liệu giả ${preview.marker ?? ""}; chưa lưu hồ sơ nào.`,
        });
      } else {
        setNotice({ tone: "green", text: String(outcome.message ?? "Đã lưu.") });
        if (outcome.event === "docgen_template_mapping_save" || outcome.event === "docgen_template_publish") {
          setEditing(null);
        }
      }
    } else {
      setNotice({ tone: "red", text: String(outcome.error ?? "Backend từ chối thao tác.") });
    }
  }, [outcomes, pending]);

  const send = (event: LogiEventName, payload: Record<string, unknown>) => {
    const requestId = `${event}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setNotice(null);
    const sent = dispatchLogiEvent(event, { ...payload, requestId });
    if (!sent) {
      setNotice({ tone: "red", text: "Component chưa kết nối backend — chưa có gì được gửi." });
      return false;
    }
    setPending(requestId);
    return true;
  };

  const onPickFile = (file: File | null) => {
    setNotice(null);
    if (!file) {
      setFileName("");
      setFileBody("");
      setFileTooBig(false);
      return;
    }
    const limit = workspace?.maxUploadBytes ?? 5 * 1024 * 1024;
    if (file.size > limit) {
      setFileName(file.name);
      setFileBody("");
      setFileTooBig(true);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const raw = String(reader.result ?? "");
      // strip the data-URL prefix; the server re-validates everything anyway
      setFileBody(raw.includes(",") ? raw.slice(raw.indexOf(",") + 1) : raw);
      setFileName(file.name);
      setFileTooBig(false);
      if (!label.trim()) setLabel(file.name.replace(/\.(docx|xlsx)$/i, ""));
    };
    reader.readAsDataURL(file);
  };

  const submitUpload = () => {
    if (!label.trim() || !fileBody) return;
    if (send("docgen_template_upload", { label: label.trim(), category: category.trim(), fileName, base64: fileBody })) {
      setFileBody("");
      setFileName("");
      setLabel("");
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const openMapping = (row: UploadedTemplateRow) => {
    const detected = row.detected ?? [];
    const existing = row.mapping ?? [];
    const byPosition = new Map(existing.map((entry) => [entry.position, entry]));
    setDraftMapping(
      detected.map((position) => {
        const kept = byPosition.get(position.id);
        const suggestion = position.suggestion && fieldsByKey.has(position.suggestion)
          ? position.suggestion
          : "";
        return kept ?? {
          position: position.id,
          mode: suggestion ? "field" : "static",
          value: suggestion || "",
        };
      })
    );
    setEditing(row);
    setNotice(null);
  };

  const setRow = (index: number, patch: Partial<UploadedTemplateMapping>) => {
    setDraftMapping((rows) => rows.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  };

  const boundCount = draftMapping.filter(
    (row) => (row.mode === "field" && row.value) || (row.mode !== "field" && row.value.trim())
  ).length;

  const submitMapping = (row: UploadedTemplateRow) => {
    // Only rows the Admin actually bound are sent; an unbound position is left
    // untouched in the file rather than cleared.
    const mapping = draftMapping
      .filter((entry) => entry.value.trim().length > 0)
      .map((entry) => ({ position: entry.position, mode: entry.mode, value: entry.value.trim() }));
    if (!mapping.length) {
      setNotice({ tone: "red", text: "Chưa có vị trí nào được gắn — chọn ít nhất một trường hoặc một nội dung cố định." });
      return;
    }
    send("docgen_template_mapping_save", { templateId: row.id, mapping });
  };

  return (
    <div className="mx-auto max-w-[1180px] px-3 md:px-6 py-5 md:py-8 space-y-5">
      <header className="rounded-2xl bg-white border border-slate-200 p-4 md:p-6">
        <SectionTitle
          icon={<FileText size={19} aria-hidden="true" />}
          title="Biểu mẫu Office do Admin tải lên"
          sub="Tải một tệp .docx/.xlsx thông thường, xác nhận vị trí cần điền MỘT lần, rồi phát hành. Biểu mẫu đã phát hành xuất hiện trong bộ chọn “Biểu mẫu & chứng từ” của từng lô hàng."
        />
        {!canManage && (
          <p
            role="status"
            data-testid="docgen-templates-read-only"
            className="mt-3 flex items-start gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] text-slate-700"
          >
            <Lock size={15} className="mt-0.5 shrink-0" aria-hidden="true" />
            Chỉ Admin được tải lên, xác nhận mapping và phát hành biểu mẫu. Bạn đang xem danh sách ở chế độ chỉ đọc.
          </p>
        )}
        {notice && (
          <p
            role={notice.tone === "red" ? "alert" : "status"}
            data-testid="docgen-templates-notice"
            className={cx(
              "mt-3 rounded-lg border px-3 py-2 text-[13px] font-semibold",
              notice.tone === "red"
                ? "border-red-200 bg-red-50 text-red-800"
                : notice.tone === "amber"
                  ? "border-amber-200 bg-amber-50 text-amber-900"
                  : "border-emerald-200 bg-emerald-50 text-emerald-800"
            )}
          >
            {notice.text}
          </p>
        )}
      </header>

      {canManage && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5" data-testid="docgen-template-upload">
          <h2 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2">
            <Upload size={17} aria-hidden="true" /> Tải biểu mẫu mới
          </h2>
          <p className="text-[13px] text-slate-500 mt-1">
            Giới hạn {workspace?.maxUploadLabel ?? "5 MB"}. Tệp .doc/.xls cũ và tệp có macro bị từ chối; nội dung tải lên không bao giờ được chạy như macro/Jinja.
          </p>
          <div className="grid sm:grid-cols-2 gap-3 mt-3">
            <Field label="Tên biểu mẫu" required hint="Hiện trong bộ chọn chứng từ của lô hàng.">
              <input
                id="docgen-template-label"
                value={label}
                onChange={(event) => setLabel(event.target.value)}
                placeholder="VD: Bảng kê lô hàng"
                className={inputCls(label.trim() ? "ok" : "missing")}
              />
            </Field>
            <Field label="Nhóm" hint="Chỉ để phân loại trong danh mục.">
              <input
                id="docgen-template-category"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
                className={inputCls("ok")}
              />
            </Field>
          </div>
          <div className="mt-3">
            <label
              htmlFor="docgen-template-file"
              className="flex min-h-[76px] cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-center hover:border-[#1e5aa8]"
            >
              <Upload size={18} className="text-slate-500" aria-hidden="true" />
              <span className="text-[13.5px] font-semibold text-[#0f2a4a]">
                {fileName || "Chọn tệp .docx hoặc .xlsx"}
              </span>
              <span className="text-[12px] text-slate-500">
                {fileTooBig
                  ? `Tệp vượt ${workspace?.maxUploadLabel ?? "5 MB"} — chưa có gì được gửi.`
                  : "Backend kiểm tra định dạng, kích thước và an toàn OOXML trước khi lưu."}
              </span>
            </label>
            <input
              id="docgen-template-file"
              ref={fileInput}
              type="file"
              accept={workspace?.accept ?? ".docx,.xlsx"}
              onChange={(event) => onPickFile(event.currentTarget.files?.[0] ?? null)}
              className="sr-only"
              data-testid="docgen-template-file-input"
            />
          </div>
          <PrimaryBtn
            onClick={submitUpload}
            disabled={!label.trim() || !fileBody || Boolean(pending)}
            testId="docgen-template-upload-submit"
            className="mt-3 w-full sm:w-auto"
          >
            <Plus size={16} aria-hidden="true" />
            {pending ? "Đang xử lý…" : "Tải lên và nhận diện vị trí"}
          </PrimaryBtn>
        </section>
      )}

      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <h2 className="font-extrabold text-[16.5px] text-[#0f2a4a]">
          Danh mục biểu mẫu ({templates.length})
        </h2>
        <p className="text-[13px] text-slate-500 mt-1">
          {workspace?.activeCount ?? 0} biểu mẫu đang hoạt động. Bản đã phát hành là bất biến — sửa mapping cần một phiên bản mới.
        </p>

        {templates.length === 0 ? (
          <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center" data-testid="docgen-templates-empty">
            <FileText size={22} className="mx-auto text-slate-400" aria-hidden="true" />
            <p className="text-[14px] font-semibold text-slate-700 mt-2">Chưa có biểu mẫu nào.</p>
            <p className="text-[13px] text-slate-500 mt-1">
              {canManage ? "Tải lên một tệp .docx hoặc .xlsx để bắt đầu." : "Admin chưa tải biểu mẫu nào lên."}
            </p>
          </div>
        ) : (
          <ul className="mt-4 space-y-3" data-testid="docgen-template-list">
            {templates.map((row) => (
              <li
                key={row.id}
                data-testid="docgen-template-row"
                data-template-id={row.id}
                data-status={row.status}
                className="rounded-xl border border-slate-200 p-3.5"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0 flex items-start gap-2.5">
                    <span className="mt-0.5 text-[#0f2a4a]"><TemplateIcon kind={row.kind} /></span>
                    <div className="min-w-0">
                      <p className="font-extrabold text-[14.5px] text-[#0f2a4a] break-words">{row.label}</p>
                      <p className="text-[12px] text-slate-500 mt-0.5 break-words">
                        {row.category} · {row.kind}
                        {row.activeVersion ? ` · v${row.activeVersion}/${row.versionCount}` : " · chưa phát hành"}
                        {row.publishedMappingCount ? ` · ${row.publishedMappingCount} vị trí` : ""}
                      </p>
                      <p className="text-[12px] text-slate-400 mt-0.5 break-words">
                        {row.uploadedBy ? `Tải bởi ${row.uploadedBy}` : ""}
                        {row.publishedBy ? ` · Phát hành bởi ${row.publishedBy}` : ""}
                      </p>
                    </div>
                  </div>
                  <ToneBadge tone={STATUS_TONE[row.status] ?? "gray"} size="sm">
                    {STATUS_LABEL[row.status] ?? row.status}
                  </ToneBadge>
                </div>

                {canManage && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {row.status === "DRAFT" && (
                      <>
                        <GhostBtn onClick={() => openMapping(row)} testId={`docgen-template-map-${row.id}`}>
                          Xác nhận vị trí điền ({row.detected?.length ?? 0} vị trí nhận diện)
                        </GhostBtn>
                        <GhostBtn
                          onClick={() => send("docgen_template_preview", { templateId: row.id })}
                          disabled={Boolean(pending) || row.mappingCount === 0}
                          testId={`docgen-template-preview-${row.id}`}
                        >
                          <Eye size={15} aria-hidden="true" /> Xem thử (dữ liệu giả)
                        </GhostBtn>
                        <PrimaryBtn
                          onClick={() => send("docgen_template_publish", { templateId: row.id })}
                          disabled={Boolean(pending) || row.mappingCount === 0}
                          testId={`docgen-template-publish-${row.id}`}
                        >
                          <CheckCircle2 size={15} aria-hidden="true" /> Phát hành
                        </PrimaryBtn>
                      </>
                    )}
                    {row.status === "ACTIVE" && (
                      <GhostBtn
                        onClick={() => send("docgen_template_preview", { templateId: row.id })}
                        disabled={Boolean(pending)}
                        testId={`docgen-template-preview-${row.id}`}
                      >
                        <Eye size={15} aria-hidden="true" /> Xem thử (dữ liệu giả)
                      </GhostBtn>
                    )}
                    {row.status === "ACTIVE" && (
                      <GhostBtn
                        onClick={() => send("docgen_template_status_set", { templateId: row.id, active: false })}
                        disabled={Boolean(pending)}
                        testId={`docgen-template-retire-${row.id}`}
                      >
                        Ngừng dùng (không xóa lịch sử)
                      </GhostBtn>
                    )}
                    {row.status === "RETIRED" && (
                      <GhostBtn
                        onClick={() => send("docgen_template_status_set", { templateId: row.id, active: true })}
                        disabled={Boolean(pending)}
                        testId={`docgen-template-activate-${row.id}`}
                      >
                        Kích hoạt lại
                      </GhostBtn>
                    )}
                  </div>
                )}
                {row.status === "DRAFT" && row.mappingCount === 0 && (
                  <p className="text-[12.5px] text-amber-800 mt-2">
                    Cần xác nhận ít nhất một vị trí trước khi phát hành.
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {(workspace?.notes ?? []).length > 0 && (
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <h2 className="font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-2">
            <ShieldCheck size={16} aria-hidden="true" /> Ranh giới an toàn của luồng này
          </h2>
          <ul className="mt-2 space-y-1.5">
            {(workspace?.notes ?? []).map((note) => (
              <li key={note} className="flex items-start gap-2 text-[13px] text-slate-600">
                <Info size={14} className="mt-0.5 shrink-0 text-slate-400" aria-hidden="true" />
                <span className="text-pretty">{note}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {editing && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="docgen-mapping-title"
          data-testid="docgen-template-mapping-dialog"
          className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 p-0 sm:items-center sm:p-4"
        >
          <div className="max-h-[92vh] w-full max-w-[860px] overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl sm:rounded-2xl md:p-6">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 id="docgen-mapping-title" className="text-[17px] font-extrabold text-[#0f2a4a] break-words">
                  Xác nhận vị trí điền — {editing.label}
                </h3>
                <p className="text-pretty text-[13px] text-slate-500 mt-1">
                  {editing.detected?.length ?? 0} vị trí nhận diện · {boundCount} đã gắn. Vị trí nhận diện chỉ là gợi ý: hãy kiểm tra từng dòng trước khi phát hành.
                </p>
              </div>
              <button
                type="button"
                aria-label="Đóng xác nhận vị trí"
                onClick={() => setEditing(null)}
                className="btn-press touch-target grid size-10 shrink-0 place-items-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
              >
                <span aria-hidden="true">×</span>
              </button>
            </div>

            <p className="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[12.5px] text-amber-900">
              <CircleAlert size={15} className="mt-0.5 shrink-0" aria-hidden="true" />
              Chỉ các trường trong danh mục dữ liệu đã xác nhận mới tự điền được. Tiền, giá, VAT, điều khoản thanh toán và tài khoản ngân hàng KHÔNG có trong danh mục — nếu biểu mẫu cần in, hãy để nhân viên nhập tay ở lô hàng.
            </p>

            <ol className="mt-4 space-y-2.5" data-testid="docgen-mapping-rows">
              {(editing.detected ?? []).map((position, index) => {
                const row = draftMapping[index];
                if (!row) return null;
                const bound = row.mode === "field" ? fieldsByKey.get(row.value) : null;
                return (
                  <li
                    key={position.id}
                    data-testid="docgen-mapping-row"
                    data-position-id={position.id}
                    className="rounded-xl border border-slate-200 p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[12px] font-semibold text-slate-700">
                        {position.id}
                      </code>
                      <span className="text-[12px] text-slate-400">{position.detectedBy}</span>
                    </div>
                    <p className="mt-1.5 text-[13px] font-semibold text-[#0f2a4a] break-words">
                      {position.label || "(không có nhãn)"}
                    </p>
                    {position.text && (
                      <p className="text-[12px] text-slate-500 break-words">Nội dung hiện tại: {position.text}</p>
                    )}
                    <div className="mt-2 grid gap-2 sm:grid-cols-[150px_1fr]">
                      <select
                        aria-label={`Cách điền ${position.id}`}
                        value={row.mode}
                        onChange={(event) => setRow(index, { mode: event.currentTarget.value as UploadedTemplateMapping["mode"], value: "" })}
                        className={inputCls("ok")}
                      >
                        <option value="static">Không tự điền</option>
                        <option value="field">Tự điền từ dữ liệu lô</option>
                        <option value="manual">Nhân viên nhập tay</option>
                      </select>
                      {row.mode === "field" ? (
                        <select
                          aria-label={`Trường dữ liệu cho ${position.id}`}
                          value={row.value}
                          onChange={(event) => setRow(index, { value: event.currentTarget.value })}
                          className={inputCls(row.value ? "ok" : "missing")}
                        >
                          <option value="">— Chọn trường —</option>
                          {groups.map((group) => (
                            <optgroup key={group} label={group}>
                              {fields
                                .filter((field) => field.group === group)
                                .map((field) => (
                                  <option key={field.key} value={field.key}>
                                    {field.label}
                                    {field.conditional ? " (cần 1 nguồn duy nhất)" : ""}
                                  </option>
                                ))}
                            </optgroup>
                          ))}
                        </select>
                      ) : (
                        <input
                          aria-label={row.mode === "manual" ? `Nhãn ô nhập tay ${position.id}` : `Nội dung cố định ${position.id}`}
                          value={row.value}
                          onChange={(event) => setRow(index, { value: event.currentTarget.value })}
                          placeholder={row.mode === "manual" ? "VD: Số biên bản" : "Để trống = giữ nguyên ô này"}
                          className={inputCls(row.value.trim() ? "ok" : "missing")}
                        />
                      )}
                    </div>
                    {bound && (
                      <p className="text-[12px] text-slate-500 mt-1.5">
                        Sẽ in: {bound.label}
                        {bound.conditional ? " — chỉ điền khi lô có đúng một nguồn duy nhất, ngược lại báo thiếu." : ""}
                      </p>
                    )}
                  </li>
                );
              })}
            </ol>

            <div className="mt-4 flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-3">
              <GhostBtn onClick={() => setEditing(null)} disabled={Boolean(pending)}>Hủy</GhostBtn>
              <PrimaryBtn
                onClick={() => submitMapping(editing)}
                disabled={Boolean(pending) || boundCount === 0}
                testId="docgen-mapping-save"
              >
                {pending ? "Đang lưu…" : `Lưu ${boundCount} vị trí đã xác nhận`}
              </PrimaryBtn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
