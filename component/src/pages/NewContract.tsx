import { contractPath } from "../lib/contractRoute";
// ============================================================================
// Tạo hợp đồng mới — Phase C1, donor Logi-good visual shell.
//
// contract_create → the ONE bounded dispatcher → RBAC (can_edit_contract /
// sales_write) → save_contract_to_cloud → audit → fresh read. Kind/identity/
// goods/docgen are completed on the detail work desk afterwards.
//
// LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — three additions on this page:
//   * the counterparty is picked through a real search (`SearchPicker`), not a
//     blind <select> over the whole customer master;
//   * the PL answer is explicit ("Có PL" / "Không cần PL" / chưa chọn) and is
//     stored verbatim — a blank is never recorded as "Không cần PL";
//   * a GetFly DSDH block can be pasted and imported, and its outcome is read
//     from the backend's own `lastWrites` — the page never claims success
//     because the event was transported.
// ============================================================================

import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ClipboardPaste, FileText } from "lucide-react";
import {
  Field, GhostBtn, PlChoice, PrimaryBtn, SearchPicker, SectionTitle, inputCls,
} from "../components/ui";
import { useStore } from "../lib/store";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";

const GETFLY_SAMPLE =
  "Mã ĐH\tNgày đặt hàng\tTên KH\tMã KH\nDH-1001\t05/09/2026\tAn Phát JSC\tCUST-ANPHAT";

export default function NewContract() {
  const { customers, dispatch, toast } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const nav = useNavigate();
  const pendingRef = useRef<{ id: string; requestId: string } | null>(null);
  const [pending, setPending] = useState<{ id: string; requestId: string } | null>(null);
  const [createError, setCreateError] = useState("");
  useEffect(() => {
    if (!pending || pendingRef.current !== pending) return;
    const outcome = vm?.lastWrites?.find(
      (w) => w.event === "contract_create" && w.requestId === pending.requestId
    );
    if (!outcome) return;
    if (outcome.ok === false) {
      pendingRef.current = null;
      setPending(null);
      setCreateError(String(outcome.error || "Máy chủ từ chối tạo hợp đồng."));
    } else if (outcome.ok === true && vm?.contracts.some((c) => c.id === pending.id)) {
      pendingRef.current = null;
      setPending(null);
      nav(contractPath(pending.id));
    }
  }, [vm, pending, nav]);
  const [id, setId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [kind, setKind] = useState("HDMB");
  const [note, setNote] = useState("");
  const [date, setDate] = useState("");
  const [plRequired, setPlRequired] = useState<"YES" | "NO" | "">("");
  const [getflyOpen, setGetflyOpen] = useState(false);
  const [getflyText, setGetflyText] = useState("");
  const [getflyRequestId, setGetflyRequestId] = useState("");

  const customerOptions = useMemo(
    () => customers.map((c) => ({ id: c.id, label: c.name || c.id, sub: c.mst || c.taxCode ? `MST ${c.mst || c.taxCode} · ${c.id}` : c.id })),
    [customers]
  );
  const picked = customers.find((c) => c.id === customerId) ?? null;

  // The import's outcome is the backend's answer after the canonical writer
  // ran — never the fact that a trigger was transported.
  const getflyOutcome = useMemo(() => {
    if (!getflyRequestId) return null;
    return (vm?.lastWrites ?? []).find(
      (w) => w.event === "customer_getfly_import" && w.requestId === getflyRequestId
    ) ?? null;
  }, [vm?.lastWrites, getflyRequestId]);

  const importFromGetfly = () => {
    const text = getflyText.trim();
    if (!text) {
      toast("Chưa có gì để nhập", "Dán các dòng đơn hàng từ file GetFly (kèm dòng tiêu đề).", "red");
      return;
    }
    const requestId = `GETFLY-${Date.now().toString(36).toUpperCase()}`;
    const sent = dispatch("customer_getfly_import", { text, requestId });
    if (!sent) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    setGetflyRequestId(requestId);
    toast("Đã gửi dữ liệu GetFly", "Máy chủ đọc cột GetFly, ghi khách hàng mới rồi báo lại kết quả.", "blue");
  };

  const submit = () => {
    if (pendingRef.current) return;
    const cid = id.trim().toUpperCase();
    if (!cid) {
      toast("Thiếu số hợp đồng", "Nhập số hợp đồng (VD: HDMB-0310).", "red");
      return;
    }
    if (!customerId) {
      toast("Chưa chọn khách hàng", "Bấm “Tìm / đổi” rồi chọn khách hàng / đối tác.", "red");
      return;
    }
    const request = { id: cid, requestId: crypto.randomUUID() };
    pendingRef.current = request;
    setPending(request);
    setCreateError("");
    const sent = dispatch("contract_create", {
      requestId: request.requestId,
      id: cid,
      customerId,
      kind,
      note: note.trim(),
      date: date.trim(),
      pl_required: plRequired,
    });
    if (!sent) {
      pendingRef.current = null;
      setPending(null);
      setCreateError("Không gửi được. Component chưa kết nối backend.");
    }
  };

  const outcomeCustomers = (getflyOutcome?.customers ?? []) as { id: string; name: string }[];
  const outcomeSkipped = (getflyOutcome?.skippedMissing ?? []) as string[];
  const outcomeOrders = (getflyOutcome?.orders ?? []) as string[];

  return (
    <div className="space-y-4 max-w-[760px]">
      <button onClick={() => nav(-1)} className="touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]"><ArrowLeft size={17} /> Quay lại</button>
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-6">
        <SectionTitle icon={<FileText size={18} />} title="Tạo hợp đồng mới" sub="HDMB / HDNT + Phụ lục — sau khi tạo sẽ nhập hàng hóa, sinh chứng từ và liên kết lô" />
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Số hợp đồng" required error={!id ? "Nhập số hợp đồng" : undefined}>
            <input value={id} onChange={(e) => setId(e.target.value)} placeholder="VD: HDMB-0310" className={inputCls(!id ? "missing" : "ok")} />
          </Field>
          <Field label="Loại hợp đồng" required>
            <select value={kind} onChange={(e) => setKind(e.target.value)} className={inputCls()}>
              <option value="HDMB">HDMB — Hợp đồng mua bán (≥ 50 triệu)</option>
              <option value="HDNT">HDNT — Hợp đồng nguyên tắc (&lt; 50 triệu)</option>
              <option value="PL">PL — Phụ lục hợp đồng</option>
            </select>
          </Field>
        </div>

        <div className="grid gap-3 mt-3">
          <SearchPicker
            label="Khách hàng / đối tác"
            testId="contract-customer-picker"
            required
            options={customerOptions}
            selectedId={customerId}
            selectedLabel={picked ? `${picked.name} (${picked.id})` : ""}
            placeholder="Gõ tên khách hoặc mã khách (VD: An Phát, CUST-ANPHAT)…"
            emptyHint="Danh bạ khách hàng đang trống — nhập từ GetFly bên dưới hoặc tạo mới ở mục Khách Hàng."
            onSelect={setCustomerId}
          />
          <div className="grid sm:grid-cols-2 gap-3">
            <Field label="Ngày hợp đồng" hint="Định dạng 2026-09-05 — để trống nếu chưa có.">
              <input value={date} onChange={(e) => setDate(e.target.value)} placeholder="2026-09-05" className={inputCls()} />
            </Field>
            <Field label="Ghi chú"><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi chú nội bộ" className={inputCls()} /></Field>
          </div>

          <div className="rounded-xl border border-slate-200 p-3">
            <PlChoice testId="contract-pl-choice" value={plRequired} onChange={setPlRequired} />
            <p className="text-[12.5px] text-slate-500 mt-1.5">
              Đây là quyết định của bộ phận vận hành ghi trên hợp đồng; quy tắc 50 triệu của
              chứng từ (HDNT + PL hay HDMB) vẫn do máy chủ tính, không đổi theo ô chọn này.
            </p>
          </div>
        </div>

        {/* GetFly — the only counterparty data that sheet actually carries. */}
        <div className="mt-4 rounded-xl bg-slate-50 border border-slate-200 p-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-[14px] font-extrabold text-[#0f2a4a] flex items-center gap-1.5">
              <ClipboardPaste size={16} /> Nhập khách hàng từ GetFly (DSDH)
            </p>
            <button
              type="button"
              onClick={() => setGetflyOpen((v) => !v)}
              aria-expanded={getflyOpen}
              className="btn-press touch-target rounded-lg border-2 border-slate-200 bg-white px-3 min-h-[36px] text-[13px] font-bold text-slate-600"
              data-testid="contract-getfly-toggle"
            >
              {getflyOpen ? "Đóng" : "Dán dữ liệu GetFly"}
            </button>
          </div>
          {getflyOpen && (
            <div className="mt-2.5 space-y-2" data-testid="contract-getfly-panel">
              <p className="text-[12.5px] text-slate-500">
                Copy nguyên khối trong file GetFly (bao gồm dòng tiêu đề: Mã ĐH · Ngày đặt hàng ·
                Tên KH · Mã KH). GetFly chỉ mang theo khách hàng và đơn hàng — mã hợp đồng, hồ sơ
                pháp lý Công ty (bên mua) và MST không có trong sheet đó nên app không tự đặt.
              </p>
              <textarea
                value={getflyText}
                onChange={(e) => setGetflyText(e.target.value)}
                rows={5}
                placeholder={GETFLY_SAMPLE}
                className={inputCls() + " font-mono text-[13px]"}
                data-testid="contract-getfly-text"
              />
              <div className="flex flex-wrap gap-2">
                <GhostBtn onClick={importFromGetfly} className="flex-1">
                  📥 Nhập khách hàng từ GetFly
                </GhostBtn>
              </div>
            </div>
          )}
        {getflyOutcome && (
          <div
            className={
              "rounded-lg px-2.5 py-2 text-[13px] font-semibold " +
              (getflyOutcome.ok ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800")
            }
            data-testid="contract-getfly-outcome"
          >
            <p>{String(getflyOutcome.error || "Đã nhập khách hàng từ GetFly.")}</p>
            {outcomeCustomers.length > 0 && (
              <p className="mt-1 font-medium text-slate-600">
                Đã có trong danh bạ: {outcomeCustomers.map((c) => `${c.name} (${c.id})`).join(", ")}
                {outcomeOrders.length > 0 ? ` · ${outcomeOrders.length} đơn hàng GetFly` : null}
              </p>
            )}
            {outcomeSkipped.length > 0 && (
              <p className="mt-1 font-medium text-amber-700">
                Bỏ qua (thiếu mã KH hoặc tên KH): {outcomeSkipped.join(", ")}
              </p>
            )}
            {getflyOutcome.ok && outcomeCustomers.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {/* One button per customer the paste really carried — the app never
                    guesses which one this contract belongs to. */}
                {outcomeCustomers.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setCustomerId(c.id)}
                    className="btn-press touch-target rounded-lg border-2 border-emerald-300 bg-white px-2.5 min-h-[34px] text-[12.5px] font-bold text-emerald-800"
                    data-testid={`contract-getfly-use-${c.id}`}
                  >
                    Dùng {c.name} cho hợp đồng này
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        </div>

        {createError && <p role="alert" className="mt-4 text-red-700" data-testid="contract-create-error">{createError}</p>}
        {pending && <p role="status" className="mt-4 text-slate-600" data-testid="contract-create-pending">Đang chờ kết quả và dữ liệu hợp đồng từ máy chủ… Không gửi lại yêu cầu.</p>}
        <div className="grid grid-cols-2 gap-2.5 mt-5">
          <GhostBtn onClick={() => nav(-1)}>Hủy</GhostBtn>
          <PrimaryBtn onClick={submit} disabled={!!pending}>💾 TẠO HỢP ĐỒNG</PrimaryBtn>
        </div>
      </div>
    </div>
  );
}
