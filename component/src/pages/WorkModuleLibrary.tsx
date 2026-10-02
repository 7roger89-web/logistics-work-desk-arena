// ============================================================================
// Issue #162 — Work Module Library (/quy-trinh).
//
// The SMALLEST bounded management surface the task asks for: list every stored
// template version with its status, create a new version (structured form),
// activate a DRAFT, and retire an ACTIVE version. There is deliberately NO
// BPMN canvas, no drag/drop graph editor, no arbitrary edge drawing and no
// recursive workflow designer — steps are an ordered list with a bounded
// dependency vocabulary (INFORMATIONAL | PARALLEL_REQUIRED | BLOCKING).
//
// Every mutation goes through the ONE dispatcher (work_module_template_save):
//   typed event → bounded dispatcher → server-side RBAC (operations authority,
//   re-checked in core.database) → immutable-version writer → audit → the
//   authoritative outcome, correlated by requestId in the next fresh view-model.
// A version that already exists can never be rewritten: the form always
// publishes a NEW version, and the server refuses anything else.
//
// Attach to a shipment is NOT here: it stays on the shipment Journey
// ("+ Thêm quy trình phát sinh"), because that is where the operator's context is.
// ============================================================================

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { CircleAlert, CircleCheck, CircleSlash, Info, Layers, Plus, Trash2 } from "lucide-react";
import { Field, PrimaryBtn, SectionTitle, ToneBadge, inputCls } from "../components/ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import type { WorkModuleGuidance } from "../lib/viewmodel";
import { cx } from "../lib/format";

const STATUS_TONE: Record<string, "green" | "amber" | "gray"> = {
  ACTIVE: "green",
  DRAFT: "amber",
  RETIRED: "gray",
};
const STATUS_LABEL: Record<string, string> = {
  ACTIVE: "Đang dùng",
  DRAFT: "Bản nháp",
  RETIRED: "Ngừng dùng",
};
const DEPENDENCY_TYPES = ["BLOCKING", "PARALLEL_REQUIRED", "INFORMATIONAL"] as const;
const DEPENDENCY_LABEL: Record<string, string> = {
  BLOCKING: "Bắt buộc trước (chặn)",
  PARALLEL_REQUIRED: "Bắt buộc, có thể song song",
  INFORMATIONAL: "Chỉ tham khảo",
};
const GUIDANCE_FIELDS: { key: keyof WorkModuleGuidance; label: string; placeholder: string }[] = [
  { key: "why", label: "WHY — vì sao phải làm", placeholder: "Vì sao quy trình này tồn tại" },
  { key: "what_to_do", label: "WHAT TO DO — cần làm gì", placeholder: "Việc cụ thể" },
  { key: "who", label: "WHO — ai làm (khi đã xác định rõ)", placeholder: "Để trống nếu chưa xác định" },
  { key: "when", label: "WHEN — khi nào (chỉ khi đã rõ)", placeholder: "Để trống nếu chưa có mốc rõ ràng" },
  { key: "needs", label: "NEEDS — cần gì", placeholder: "Hồ sơ / thông tin cần có" },
  { key: "done_when", label: "DONE WHEN — xong khi nào", placeholder: "Điều kiện hoàn thành" },
  { key: "impact", label: "IMPACT if incomplete — nếu chưa xong", placeholder: "Ảnh hưởng nếu bỏ qua" },
];

type StepDraft = { id: string; label: string; dependsOn: string; dependencyType: string; guidance: Record<string, string> };

const emptyStep = (): StepDraft => ({ id: "", label: "", dependsOn: "", dependencyType: "BLOCKING", guidance: {} });

export default function WorkModuleLibrary() {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const library = vm?.workModules;
  const canAuthor = Boolean(library?.canAuthor);
  const all = useMemo(() => library?.all ?? [], [library]);
  const stageOptions = useMemo(() => {
    const seen = new Map<string, string>();
    for (const shipment of vm?.shipments ?? []) {
      for (const node of shipment.journey?.nodes ?? []) {
        if (!seen.has(node.id)) seen.set(node.id, node.label);
        if (!seen.has(node.family)) seen.set(node.family, node.family);
      }
    }
    for (const stage of library?.stages ?? []) if (!seen.has(stage.id)) seen.set(stage.id, stage.label);
    return [...seen.entries()].map(([id, label]) => ({ id, label })).sort((a, b) => a.label.localeCompare(b.label, "vi"));
  }, [vm?.shipments, library?.stages]);

  const [open, setOpen] = useState(false);
  const [templateId, setTemplateId] = useState("");
  const [name, setName] = useState("");
  const [version, setVersion] = useState("1");
  const [status, setStatus] = useState("DRAFT");
  const [description, setDescription] = useState("");
  const [anchorStage, setAnchorStage] = useState("");
  const [gateStage, setGateStage] = useState("");
  const [steps, setSteps] = useState<StepDraft[]>([emptyStep()]);
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const outcome = vm?.lastWrites?.find((w) => w.event === "work_module_template_save" && w.requestId === pending);
  const loading = Boolean(pending && !outcome);

  useEffect(() => {
    if (!outcome) return;
    if (outcome.ok) { setPending(""); setError(""); setOpen(false); reset(); }
    else { setError(String(outcome.error || "Backend từ chối lưu quy trình.")); setPending(""); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [outcome]);

  const reset = () => {
    setTemplateId(""); setName(""); setVersion("1"); setStatus("DRAFT"); setDescription("");
    setAnchorStage(""); setGateStage(""); setSteps([emptyStep()]);
  };
  const setStep = (index: number, patch: Partial<StepDraft>) =>
    setSteps((rows) => rows.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  const setGuidance = (index: number, key: string, value: string) =>
    setSteps((rows) => rows.map((row, i) => (i === index ? { ...row, guidance: { ...row.guidance, [key]: value } } : row)));

  const submit = () => {
    setError("");
    const payloadSteps = steps
      .filter((step) => step.id.trim())
      .map((step) => ({
        id: step.id.trim(),
        label: step.label.trim() || step.id.trim(),
        dependencies: step.dependsOn ? [{ type: step.dependencyType, nodeId: step.dependsOn }] : [],
        guidance: Object.fromEntries(Object.entries(step.guidance).filter(([, v]) => String(v || "").trim())),
      }));
    if (!templateId.trim() || !name.trim() || payloadSteps.length === 0) {
      setError("Cần mã quy trình, tên quy trình và ít nhất một bước có mã."); return;
    }
    const last = payloadSteps[payloadSteps.length - 1];
    const template: Record<string, unknown> = {
      template_id: templateId.trim().toUpperCase(),
      name: name.trim(),
      version: Number(version) || 1,
      status,
      description: description.trim(),
      anchor_stage: anchorStage,
      gate_stage: gateStage,
      nodes: payloadSteps,
    };
    if (gateStage) template.join = { from: last.id, type: "BLOCKING" };
    const requestId = `WMT-${crypto.randomUUID()}`;
    setPending(requestId);
    if (!dispatchLogiEvent("work_module_template_save", { requestId, template })) {
      setPending(""); setError("Chưa kết nối backend.");
    }
  };

  const changeStatus = (row: (typeof all)[number], next: string) => {
    const requestId = `WMT-${crypto.randomUUID()}`;
    setError(""); setPending(requestId);
    // Only the STATUS may move; the backend keeps the stored version body
    // byte-for-byte and refuses every other rewrite.
    if (!dispatchLogiEvent("work_module_template_save", {
      requestId,
      template: { template_id: row.templateId, name: row.name, version: row.version, status: next, anchor_stage: row.anchorStage },
    })) { setPending(""); setError("Chưa kết nối backend."); }
  };

  const prefillNewVersion = (row: (typeof all)[number]) => {
    setTemplateId(row.templateId); setName(row.name); setVersion(String(row.version + 1)); setStatus("DRAFT");
    setDescription(row.description); setAnchorStage(row.anchorStage); setGateStage(row.gateStage);
    setSteps(row.steps.map((step) => ({
      id: step.id, label: step.label,
      dependsOn: step.dependencies[0]?.nodeId ?? "", dependencyType: step.dependencies[0]?.type ?? "BLOCKING",
      guidance: { ...step.guidance },
    })));
    setOpen(true); setError("");
  };

  return <div className="space-y-4 max-w-[1300px]" data-testid="work-module-library">
    <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
      <SectionTitle
        title="Thư viện quy trình phát sinh"
        sub="Quy trình tái sử dụng để gắn thêm vào một lô hàng. Mỗi phiên bản đã công bố là bất biến: muốn đổi nội dung phải tạo phiên bản mới, lô đã gắn giữ nguyên ý nghĩa cũ."
        right={canAuthor ? <PrimaryBtn testId="wm-library-new" onClick={() => { setOpen((v) => !v); setError(""); }}>{open ? "Đóng biểu mẫu" : "Tạo phiên bản mới"}</PrimaryBtn> : undefined}
      />
      {!canAuthor && <div className="mt-2 flex items-start gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600" data-testid="wm-library-readonly">
        <Info size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
        <p>Tài khoản hiện tại chỉ xem được thư viện. Việc tạo/kích hoạt/ngừng dùng phiên bản cần quyền vận hành (operations) và được kiểm tra lại ở backend.</p>
      </div>}
    </div>

    {open && canAuthor && <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5" data-testid="wm-library-form">
      <h3 className="font-extrabold text-[#0f2a4a]">Phiên bản mới</h3>
      <p className="text-sm text-slate-500">Biểu mẫu có cấu trúc. Không có trình vẽ sơ đồ: các bước là một danh sách có thứ tự với quan hệ phụ thuộc giới hạn.</p>
      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="Mã quy trình" required><input aria-label="Mã quy trình" className={inputCls()} value={templateId} onChange={(e) => setTemplateId(e.target.value.toUpperCase())} placeholder="VD: IMPORT_SPECIAL_HANDLING" /></Field>
        <Field label="Tên hiển thị" required><input aria-label="Tên hiển thị" className={inputCls()} value={name} onChange={(e) => setName(e.target.value)} placeholder="VD: IMPORT SPECIAL HANDLING" /></Field>
        <Field label="Phiên bản" required hint="Bản đã công bố không sửa được — tăng số để tạo bản mới."><input aria-label="Phiên bản" className={inputCls()} inputMode="numeric" value={version} onChange={(e) => setVersion(e.target.value)} /></Field>
        <Field label="Trạng thái"><select aria-label="Trạng thái" className={inputCls()} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="DRAFT">Bản nháp (chưa gắn được)</option>
          <option value="ACTIVE">Đang dùng (gắn được)</option>
        </select></Field>
        <Field label="Công đoạn neo" required hint="Quy trình bắt đầu từ công đoạn hành trình này."><select aria-label="Công đoạn neo" className={inputCls()} value={anchorStage} onChange={(e) => setAnchorStage(e.target.value)}>
          <option value="">--Chọn--</option>
          {stageOptions.map((s) => <option key={s.id} value={s.id}>{s.label} ({s.id})</option>)}
        </select></Field>
        <Field label="Cổng chặn" hint="Bỏ trống nếu quy trình không chặn công đoạn nào."><select aria-label="Cổng chặn" className={inputCls()} value={gateStage} onChange={(e) => setGateStage(e.target.value)}>
          <option value="">Không chặn cổng nào</option>
          {stageOptions.map((s) => <option key={s.id} value={s.id}>{s.label} ({s.id})</option>)}
        </select></Field>
      </div>
      <Field label="Mô tả / lý do"><textarea aria-label="Mô tả" className={cx(inputCls(), "min-h-[72px]")} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Vì sao quy trình này tồn tại — hiện ngay khi người dùng chọn gắn." /></Field>

      <div className="mt-4">
        <div className="flex items-center gap-2"><h4 className="font-bold">Các bước</h4>
          <button type="button" onClick={() => setSteps((rows) => [...rows, emptyStep()])} className="touch-target inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-sm font-bold" data-testid="wm-add-step"><Plus size={14} aria-hidden="true" />Thêm bước</button></div>
        <div className="mt-2 space-y-3">
          {steps.map((step, index) => <div key={index} className="rounded-xl border border-slate-200 p-3" data-testid={`wm-step-${index}`}>
            <div className="flex flex-wrap items-end gap-2">
              <Field label="Mã bước" required><input aria-label={`Mã bước ${index + 1}`} className={inputCls()} value={step.id} onChange={(e) => setStep(index, { id: e.target.value })} placeholder="prepare-file" /></Field>
              <Field label="Tên bước"><input aria-label={`Tên bước ${index + 1}`} className={inputCls()} value={step.label} onChange={(e) => setStep(index, { label: e.target.value })} placeholder="Prepare specialist file" /></Field>
              <Field label="Phụ thuộc bước"><select aria-label={`Phụ thuộc bước ${index + 1}`} className={inputCls()} value={step.dependsOn} onChange={(e) => setStep(index, { dependsOn: e.target.value })}>
                <option value="">Không phụ thuộc</option>
                {steps.filter((_, i) => i !== index && steps[i].id.trim()).map((other) => <option key={other.id} value={other.id}>{other.label || other.id}</option>)}
              </select></Field>
              <Field label="Loại phụ thuộc"><select aria-label={`Loại phụ thuộc ${index + 1}`} className={inputCls()} value={step.dependencyType} onChange={(e) => setStep(index, { dependencyType: e.target.value })} disabled={!step.dependsOn}>
                {DEPENDENCY_TYPES.map((type) => <option key={type} value={type}>{DEPENDENCY_LABEL[type]}</option>)}
              </select></Field>
              {steps.length > 1 && <button type="button" aria-label={`Xóa bước ${index + 1}`} onClick={() => setSteps((rows) => rows.filter((_, i) => i !== index))} className="touch-target inline-flex items-center gap-1 rounded-lg border px-2 py-2 text-sm font-bold text-red-700"><Trash2 size={14} aria-hidden="true" />Xóa</button>}
            </div>
            <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
              {GUIDANCE_FIELDS.map((f) => <label key={String(f.key)} className="text-sm">
                <span className="text-xs font-bold text-slate-500">{f.label}</span>
                <input aria-label={`${f.label} — bước ${index + 1}`} className={inputCls()} value={step.guidance[f.key] ?? ""} placeholder={f.placeholder} onChange={(e) => setGuidance(index, String(f.key), e.target.value)} />
              </label>)}
            </div>
          </div>)}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <PrimaryBtn testId="wm-library-submit" onClick={submit} disabled={loading}>{loading ? "Đang chờ đọc lại…" : "Công bố phiên bản"}</PrimaryBtn>
        <span className="text-sm text-slate-500">Ghi qua backend rồi đọc lại; chưa có xác nhận thì chưa tính là đã lưu.</span>
      </div>
      {(error || (outcome && !outcome.ok)) && <p role="alert" className="mt-2 text-sm text-red-700" data-testid="wm-library-error">{error || outcome?.error}</p>}
    </div>}

    <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="tbl w-full text-[14.5px] min-w-[880px]">
          <thead><tr><th>Quy trình</th><th>Phiên bản</th><th>Trạng thái</th><th>Công đoạn neo</th><th>Cổng chặn</th><th>Bước</th><th>Hành động</th></tr></thead>
          <tbody>
            {all.map((row) => <tr key={row.id} className="hover:bg-slate-50" data-testid={`wm-row-${row.id}`}>
              <td><span className="font-extrabold text-[#0f2a4a]">{row.name}</span><span className="block text-[12.5px] text-slate-500">{row.templateId}</span></td>
              <td className="font-bold">V{row.version}</td>
              <td><ToneBadge tone={STATUS_TONE[row.status] ?? "gray"} size="sm">{STATUS_LABEL[row.status] ?? row.status}</ToneBadge></td>
              <td>{row.anchorStage}</td>
              <td>{row.gateStage || "—"}</td>
              <td>{row.stepCount}</td>
              <td>
                <div className="flex flex-wrap gap-2">
                  {canAuthor && <button type="button" data-testid={`wm-new-version-${row.id}`} onClick={() => prefillNewVersion(row)} className="touch-target rounded-lg border px-2.5 py-1.5 text-[13px] font-bold">Tạo bản mới</button>}
                  {canAuthor && row.status === "DRAFT" && <button type="button" data-testid={`wm-activate-${row.id}`} disabled={loading} onClick={() => changeStatus(row, "ACTIVE")} className="touch-target rounded-lg border px-2.5 py-1.5 text-[13px] font-bold text-emerald-800"><CircleCheck size={13} className="mr-1 inline" aria-hidden="true" />Kích hoạt</button>}
                  {canAuthor && row.status === "ACTIVE" && <button type="button" data-testid={`wm-retire-${row.id}`} disabled={loading} onClick={() => changeStatus(row, "RETIRED")} className="touch-target rounded-lg border px-2.5 py-1.5 text-[13px] font-bold text-slate-700"><CircleSlash size={13} className="mr-1 inline" aria-hidden="true" />Ngừng dùng</button>}
                  {!canAuthor && <span className="text-[13px] text-slate-500">Chỉ xem</span>}
                </div>
              </td>
            </tr>)}
          </tbody>
        </table>
      </div>
      {all.length === 0 && <p className="p-8 text-center text-slate-500" data-testid="wm-library-empty">Chưa có quy trình nào trong thư viện.</p>}
    </div>

    <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-4 flex items-start gap-3 text-[14px] text-slate-500">
      <Layers size={19} className="shrink-0 mt-0.5" aria-hidden="true" />
      <p>Gắn quy trình vào lô hàng được thực hiện ngay trên trang lô hàng (<b>+ Thêm quy trình phát sinh</b>), nơi có đủ ngữ cảnh lô. Phiên bản đã ngừng dùng vẫn hiển thị ở đây để tra cứu nhưng không gắn mới được.</p>
    </div>
    {error && !open && <p role="alert" className="text-sm text-red-700 flex items-center gap-1"><CircleAlert size={14} aria-hidden="true" />{error}</p>}
  </div>;
}
