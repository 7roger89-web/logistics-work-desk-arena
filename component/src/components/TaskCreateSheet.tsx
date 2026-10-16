import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { X } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, SheetDialog, inputCls } from "./ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";

const STAGE_TABS = new Set(["lay-hang", "van-tai", "nhap"]);

type TaskCreateReadback = {
  taskId?: string;
  shipmentId?: string;
  taskScope?: string;
  stageId?: string;
  assignee?: string;
  deadline?: string;
};

function todayLocalIso(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export default function TaskCreateSheet({
  open,
  onClose,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  onSuccess?: (readback: TaskCreateReadback) => void;
}) {
  // The same live model carries the permission-scoped assignee choices and
  // the correlated backend write outcome after a Streamlit rerun.
  const liveVm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const policy = liveVm?.taskAssignment;
  const shipments = useMemo(
    () => [...(liveVm?.shipments ?? [])].sort((a, b) => a.id.localeCompare(b.id, "vi")),
    [liveVm?.shipments]
  );
  const [content, setContent] = useState("");
  const [assigneeUserId, setAssigneeUserId] = useState("");
  const [deadline, setDeadline] = useState(todayLocalIso);
  const [shipmentId, setShipmentId] = useState("");
  const [taskScope, setTaskScope] = useState("");
  const [stageId, setStageId] = useState("");
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");

  const selectedShipment = shipments.find((shipment) => shipment.id === shipmentId);
  const stageOptions = useMemo(
    () => (selectedShipment?.journey?.nodes ?? []).filter(
      (node) => !node.moduleId && STAGE_TABS.has(node.targetTab)
    ),
    [selectedShipment]
  );
  const outcome = liveVm?.lastWrites?.find(
    (write) => write.event === "task_create" && write.requestId === pending
  );
  const loading = Boolean(pending && !outcome);

  useEffect(() => {
    if (!open) return;
    setContent("");
    setAssigneeUserId("");
    setDeadline(todayLocalIso());
    setShipmentId("");
    setTaskScope("");
    setStageId("");
    setPending("");
    setError("");
  }, [open]);

  useEffect(() => {
    if (taskScope === "STAGE" && !stageOptions.some((node) => node.id === stageId)) {
      setStageId(stageOptions[0]?.id ?? "");
    }
  }, [taskScope, stageOptions, stageId]);

  useEffect(() => {
    if (!pending || !outcome) return;
    setPending("");
    if (!outcome.ok) {
      setError(String(outcome.error || "Chưa lưu được công việc."));
      return;
    }
    const readback = outcome.readback as TaskCreateReadback | undefined;
    if (!readback?.taskId) {
      setError("Máy chủ chưa trả lại bản ghi công việc vừa lưu.");
      return;
    }
    setError("");
    onSuccess?.(readback);
    onClose();
  }, [outcome, pending, onClose, onSuccess]);

  if (!open) return null;

  const submit = () => {
    if (pending) return;
    const cleanContent = content.trim();
    if (!cleanContent) { setError("Nhập nội dung công việc."); return; }
    if (cleanContent.length > 500) { setError("Nội dung tối đa 500 ký tự."); return; }
    if (!deadline) { setError("Chọn deadline."); return; }
    if (taskScope === "STAGE" && (!shipmentId || !stageOptions.some((node) => node.id === stageId))) {
      setError("Chọn một công đoạn hiện có trong Journey của lô."); return;
    }

    const requestId = `TASK-CREATE-${crypto.randomUUID()}`;
    setError("");
    setPending(requestId);
    const sent = dispatchLogiEvent("task_create", {
      requestId,
      content: cleanContent,
      assigneeUserId,
      deadline,
      shipmentId,
      taskScope: shipmentId ? taskScope : "",
      stageId: shipmentId && taskScope === "STAGE" ? stageId : "",
    });
    if (!sent) {
      setPending("");
      setError("Chưa kết nối được trình ghi công việc — yêu cầu chưa được gửi.");
    }
  };

  const assignees = policy?.assignees ?? [{ userId: "", label: "Tất cả (Team)" }];

  return (
    <SheetDialog
      id="task-create-sheet"
      testId="task-create-sheet"
      labelledBy="task-create-title"
      width={600}
      pending={loading}
      onClose={() => { if (!loading) onClose(); }}
    >
      <div className="p-4 md:p-5" data-testid="task-create-form">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id="task-create-title" className="text-[18px] font-extrabold text-[#0f2a4a]">Giao việc nhanh</h2>
            <p className="mt-1 text-[13.5px] text-slate-500">Chọn lô và đích đến rõ ràng; nội dung việc không được dùng để đoán công đoạn.</p>
          </div>
          <button type="button" onClick={() => !loading && onClose()} disabled={loading} aria-label="Đóng giao việc" className="touch-target -mr-1 -mt-1 grid h-11 w-11 shrink-0 place-items-center rounded-xl text-slate-500 hover:bg-slate-100 disabled:opacity-50"><X size={20} /></button>
        </div>

        <div className="mt-4 space-y-3">
          <Field label="Nội dung công việc" required hint="Tối đa 500 ký tự.">
            <textarea aria-label="Nội dung công việc" className={inputCls()} rows={3} maxLength={500} value={content} onChange={(event) => setContent(event.target.value)} placeholder="Ví dụ: Xác nhận SI với khách hàng" required />
          </Field>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Field label="Giao cho ai?">
              <select aria-label="Giao cho ai?" className={inputCls()} value={assigneeUserId} onChange={(event) => setAssigneeUserId(event.target.value)}>
                {assignees.map((assignee) => <option key={assignee.userId || "team"} value={assignee.userId}>{assignee.label}</option>)}
              </select>
            </Field>
            <Field label="Deadline (Hạn chót)" required>
              <input aria-label="Deadline (Hạn chót)" type="date" className={inputCls()} value={deadline} onChange={(event) => setDeadline(event.target.value)} required />
            </Field>
          </div>

          <Field label="Gắn với lô (tùy chọn)" hint="Việc chung không gắn lô vẫn giữ nguyên, không tạo lô giả.">
            <select aria-label="Gắn với lô (tùy chọn)" className={inputCls()} value={shipmentId} onChange={(event) => { setShipmentId(event.target.value); setTaskScope(""); setStageId(""); }}>
              <option value="">Việc chung — không gắn lô</option>
              {shipments.map((shipment) => <option key={shipment.id} value={shipment.id}>{shipment.id} · {shipment.customer || "Khách hàng chưa xác định"}</option>)}
            </select>
          </Field>

          {shipmentId && <Field label="Nơi xử lý khi mở từ Home">
            <select aria-label="Nơi xử lý khi mở từ Home" className={inputCls()} value={taskScope} onChange={(event) => { const next = event.target.value; setTaskScope(next); setStageId(next === "STAGE" ? (stageOptions[0]?.id ?? "") : ""); }}>
              <option value="">Chưa gắn công đoạn — mở workspace lô</option>
              <option value="SHIPMENT">Toàn lô</option>
              <option value="STAGE" disabled={stageOptions.length === 0}>Công đoạn cụ thể trong Journey</option>
              <option value="FINANCE">Tài chính toàn lô</option>
            </select>
          </Field>}

          {shipmentId && taskScope === "STAGE" && stageOptions.length > 0 && <Field label="Công đoạn trong Journey" required hint="Danh sách lấy từ Journey hiện tại của đúng lô và phương thức vận chuyển.">
            <select aria-label="Công đoạn trong Journey" className={inputCls()} value={stageId} onChange={(event) => setStageId(event.target.value)} required>
              {stageOptions.map((node) => <option key={node.id} value={node.id}>{node.label} · {node.id}</option>)}
            </select>
          </Field>}

          {shipmentId && taskScope === "STAGE" && stageOptions.length === 0 && <p role="status" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-[13.5px] text-amber-900">Lô chưa có công đoạn Journey hợp lệ để gắn. Hãy chọn Toàn lô, Tài chính hoặc để công đoạn chưa xác định.</p>}
          {shipmentId && !taskScope && <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-[13.5px] text-amber-900">Chưa gắn công đoạn; Home sẽ mở workspace của lô để Sale/Support tự xác định nơi xử lý. Nội dung việc không được dùng để đoán.</p>}
          {shipmentId && taskScope === "FINANCE" && <p className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-[13.5px] text-blue-900">Home mở khu vực Tài chính của chính lô này, không ép vào node xuất khẩu.</p>}
          {shipmentId && taskScope === "SHIPMENT" && <p className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[13.5px] text-slate-700">Home mở workspace toàn lô, không gắn vào một công đoạn.</p>}
          {!shipmentId && <p className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[13.5px] text-slate-700">Việc chung được lưu không kèm lô; không có liên kết lô giả.</p>}

          {error && <p role="alert" data-testid="task-create-error" className="rounded-xl border border-red-200 bg-red-50 p-3 text-[13.5px] font-semibold text-red-800">{error}</p>}
          <div className="flex flex-col-reverse gap-2 border-t border-slate-200 pt-3 sm:flex-row sm:justify-end">
            <GhostBtn onClick={() => !loading && onClose()} disabled={loading} className="min-w-[104px]">Hủy</GhostBtn>
            <PrimaryBtn onClick={submit} disabled={loading || !policy?.canCreate} testId="task-create-submit" className="min-w-[168px]">
              {loading ? "ĐANG LƯU…" : "XÁC NHẬN GIAO VIỆC"}
            </PrimaryBtn>
          </div>
        </div>
      </div>
    </SheetDialog>
  );
}
