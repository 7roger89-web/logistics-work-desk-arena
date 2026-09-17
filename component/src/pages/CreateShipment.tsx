import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, CircleAlert, FileCheck2, Package, Sparkles } from "lucide-react";
import { Field, PrimaryBtn, SectionTitle, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtMoney, fmtText } from "../lib/format";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";

// Phase B — real Create Shipment workflow.
// The donor "Thêm mới nhanh → Tạo lô hàng mới" destination now runs the
// existing Logistics creation logic: accepted quote → prefill known values →
// ask only what is missing → real validation → existing save writer → audit →
// fresh read. Duplicate shipment codes are rejected by the backend.
//
// LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — the page no longer navigates
// when the event was merely TRANSPORTED. It waits for the authoritative
// backend outcome delivered in the next fresh view-model (`lastWrites`,
// matched by the requestId this click sent):
//   SUCCESS requires BOTH a matching backend outcome
//   (event == "shipment_create" && requestId == pending.requestId && ok)
//   AND the fresh view-model containing the shipment — only then navigate to
//   /lo-hang/<id> (the detail really exists). CONTROL_TOWER_REPAIR_01: there
//   is deliberately NO fallback — transport success, a version change, or the
//   shipment id merely existing (it may pre-date this click) can NEVER count
//   as proof that THIS create request succeeded.
//   FAILURE → stay on the form and show the real backend error (duplicate id,
//   RBAC, validation). One click can never create two shipments: the backend
//   seq guard + duplicate-id check stay intact and the button is disabled
//   while the outcome is in flight.

export default function CreateShipment() {
  const { customers, quotes, contracts, dispatch, toast } = useStore();
  const nav = useNavigate();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);

  const [quoteId, setQuoteId] = useState("");
  const [code, setCode] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [contractId, setContractId] = useState("");
  const [mode, setMode] = useState("");
  const [incoterm, setIncoterm] = useState("DAP");
  const [pol, setPol] = useState("");
  const [pod, setPod] = useState("");

  // The in-flight create intent. While set, the button is disabled (one click
  // = one request) and the page waits for the backend's AUTHORITATIVE outcome
  // in `lastWrites` instead of trusting the transport.
  const [pending, setPending] = useState<{ shipmentId: string; requestId: string } | null>(null);
  const [backendError, setBackendError] = useState("");

  const acceptedQuotes = useMemo(
    () => quotes.filter((q) => (q.status || "").toLowerCase().includes("accept") || (q.status || "").toLowerCase().includes("chốt")),
    [quotes]
  );
  const selectedQuote = quotes.find((q) => q.id === quoteId) ?? null;

  // Prefill from the accepted quote: known values are carried over so the
  // operator is only asked for what is genuinely missing.
  const applyQuote = (id: string) => {
    setQuoteId(id);
    const quote = quotes.find((q) => q.id === id);
    if (!quote) return;
    // Resolve by the canonical ids the quote really carries. Matching on names
    // (and matching a contract by its seller-side legal company) never hit, so
    // the operator was left re-picking both fields after every prefill.
    const customer = customers.find((c) => c.id === quote.customerId)
      ?? customers.find((c) => c.name === quote.customer);
    if (customer) setCustomerId(customer.id);
    setMode(["Truck", "Sea", "Air", "Rail"].includes(quote.transportMode) ? quote.transportMode : "");
    setIncoterm(quote.incoterm || "DAP");
    setPol(quote.origin || "");
    setPod(quote.destination || "");
    const matches = quote.customerId
      ? contracts.filter((c) => c.customerId === quote.customerId)
      : [];
    if (matches.length === 1) {
      setContractId(matches[0].id);
      toast("Đã nạp báo giá " + id, "Khách hàng + hợp đồng " + matches[0].id + " đã điền sẵn từ báo giá đã chốt.", "blue");
      return;
    }
    if (matches.length > 1) {
      setContractId("");
      toast("Đã nạp báo giá " + id,
        `Khách ${quote.customer} có ${matches.length} hợp đồng — chọn đúng hợp đồng ở ô “Hợp đồng liên kết”.`, "amber");
      return;
    }
    toast("Đã nạp báo giá " + id, "Giá trị và khách hàng đã được điền sẵn từ báo giá đã chốt.", "blue");
  };

  const submit = () => {
    if (pending) return; // outcome in flight — a second click must not double-send
    if (!code.trim()) { toast("Thiếu mã lô", "Nhập mã lô (ví dụ LO-0470) rồi bấm Tạo lô hàng.", "red"); return; }
    if (!customerId.trim()) { toast("Thiếu khách hàng", "Chọn khách hàng — backend từ chối lô không có khách.", "red"); return; }
    if (!mode && (pol.trim() || pod.trim())) { toast("Thiếu mode đầu tiên", "Chọn mode hoặc để trống cả nơi đi/đến để bổ sung sau.", "red"); return; }
    const shipmentId = code.trim().toUpperCase();
    const requestId = `create-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const sent = dispatch("shipment_create", {
      shipmentId,
      // `customerId` is the canonical customer key the backend joins on
      // (quotes / receivables / partner context); the name travels separately.
      customerId: customers.find((c) => c.id === customerId)?.id ?? "",
      customer: customers.find((c) => c.id === customerId)?.name ?? "",
      contractId: contractId.trim(),
      currency: "VND",
      transport: { mode, incoterm, pol: pol.trim(), pod: pod.trim() },
      // The backend echoes this id so the outcome in `lastWrites` can be
      // matched to THIS click — never to another request.
      requestId,
    });
    if (sent) {
      setBackendError("");
      setPending({ shipmentId, requestId });
      toast("Đã gửi yêu cầu tạo " + shipmentId,
        "Đang lưu và xác nhận lô hàng…", "blue");
    } else {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
    }
  };

  // Consume the authoritative backend outcome once the fresh view-model
  // delivers it. SUCCESS requires BOTH a matching backend outcome
  // (event == "shipment_create" && requestId == this click's requestId && ok)
  // AND the fresh view-model genuinely containing the shipment. Nothing else
  // may navigate as success: transport success is insufficient, a view-model
  // version change is insufficient, and the shipment id merely existing is
  // insufficient — it may pre-date this click (CONTROL_TOWER_REPAIR_01: the
  // previous fallback that treated those as proof was removed, deliberately
  // with no replacement).
  useEffect(() => {
    if (!pending || !vm) return;
    const outcome = (vm.lastWrites ?? []).find(
      (w) => w.event === "shipment_create" && w.requestId === pending.requestId
    );
    if (!outcome) return; // still waiting for the authoritative backend answer
    if (outcome.ok) {
      const exists = (vm.shipments ?? []).some((s) => s.id === pending.shipmentId);
      if (exists) {
        setPending(null);
        toast("Đã tạo lô " + pending.shipmentId,
          "Backend ghi + audit thành công; lô đã có trong dữ liệu mới.", "green");
        nav(`/lo-hang/${pending.shipmentId}?tab=van-tai`);
      } else {
        setPending(null);
        setBackendError("Backend báo thành công nhưng lô chưa xuất hiện trong dữ liệu mới — chưa chuyển màn hình.");
      }
    } else {
      setPending(null);
      setBackendError(outcome.error || "Backend từ chối yêu cầu tạo lô.");
      toast("Không tạo được lô", outcome.error || "Backend từ chối.", "red");
    }
  }, [vm, pending, nav, toast]);

  return (
    <div className="space-y-4 max-w-[1000px]">
      <Link to="/lo-hang" className="touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]"><ArrowLeft size={17} /> Về danh sách lô</Link>

      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" />
        <div className="p-4 md:p-6">
          <SectionTitle title="Tạo Lô Hàng Mới" sub="Bắt đầu từ báo giá đã chốt để tự điền, rồi chỉ bổ sung phần còn thiếu. Ghi bằng writer hiện có của Logistics." />

          <div className="rounded-2xl bg-blue-50 border border-blue-200 p-4 mb-4">
            <p className="font-extrabold text-[15px] text-blue-900 flex items-center gap-2"><Sparkles size={17} /> 1 · Chọn báo giá đã chốt (không bắt buộc)</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-3">
              {acceptedQuotes.length === 0 && <p className="text-[14px] text-blue-800">Chưa có báo giá đã chốt trong dữ liệu hiện tại — có thể nhập tay bên dưới.</p>}
              {acceptedQuotes.map((q) => (
                <button key={q.id} onClick={() => applyQuote(q.id)}
                  className={cx("touch-target text-left rounded-xl border-2 bg-white p-3.5 lift",
                    quoteId === q.id ? "border-[#1e5aa8]" : "border-slate-200")}>
                  <p className="font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-1.5"><FileCheck2 size={16} className="text-emerald-600" /> {q.id}</p>
                  <p className="text-[13.5px] text-slate-600 mt-0.5">{q.customer} · {fmtText(q.status)}</p>
                  <p className="text-[13.5px] font-bold text-[#1e5aa8] mt-1">{fmtMoney(q.total)} {q.currency ?? "VND"}</p>
                </button>
              ))}
            </div>
            {selectedQuote && (
              <p className="text-[13.5px] text-blue-900 mt-3">
                Đã chọn <b>{selectedQuote.id}</b> — Quote Estimate chỉ dùng để điền trước; Finance Actual sẽ nhập riêng ở tab Tài chính của lô.
              </p>
            )}
          </div>

          <div className="rounded-2xl border-2 border-slate-200 p-4">
            <p className="font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-2"><Package size={17} /> 2 · Thông tin lô</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
              <Field label="Mã lô (bắt buộc)" required>
                <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} placeholder="LO-0470" className={inputCls(code.trim() ? "ok" : "missing")} />
              </Field>
              <Field label="Khách hàng (bắt buộc)" required>
                <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} className={inputCls(customerId ? "ok" : "missing")}>
                  <option value="">-- Chọn khách hàng --</option>
                  {customers.map((c) => <option key={c.id} value={c.id}>{c.name}{c.mst ? ` · MST ${c.mst}` : ""} · {c.id}</option>)}
                </select>
              </Field>
              <Field label="Hợp đồng liên kết" hint="PXK/chứng từ của lô lấy nguồn từ hợp đồng này; sau khi tạo lô thì không đổi được ở màn lô.">
                <select value={contractId} onChange={(e) => setContractId(e.target.value)} className={inputCls()}>
                  <option value="">-- Chưa liên kết --</option>
                  {/* `company` is the seller-side legal entity (the same for every
                      contract), so the customer is what makes a row readable. */}
                  {contracts.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.client || "chưa rõ khách"}{c.customerId ? ` · ${c.customerId}` : ""}</option>)}
                </select>
              </Field>
              <Field label="Mode đầu tiên (không bắt buộc) / Incoterm" hint="Chọn mode để tạo chặng đầu; xe/container bổ sung sau ở chi tiết lô.">
                <div className="flex gap-2">
                  <select value={mode} onChange={(e) => setMode(e.target.value)} className={inputCls()}>
                    <option value="">-- Bổ sung sau --</option>
                    {["Truck", "Sea", "Air", "Rail"].map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                  <select value={incoterm} onChange={(e) => setIncoterm(e.target.value)} className={inputCls()}>
                    {["EXW", "FCA", "FOB", "CIF", "DAP", "DDP"].map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              </Field>
              <Field label="Nơi đi cơ bản"><input value={pol} onChange={(e) => setPol(e.target.value)} placeholder="Bằng Tường (Quảng Tây)" className={inputCls()} /></Field>
              <Field label="Nơi đến cơ bản"><input value={pod} onChange={(e) => setPod(e.target.value)} placeholder="Hữu Nghị (Lạng Sơn)" className={inputCls()} /></Field>
            </div>

            {/* The REAL backend refusal (duplicate id, RBAC, validation…) —
                shown verbatim; the page stayed on the form on purpose. */}
            {backendError && (
              <div className="mt-4 rounded-xl border-2 border-red-200 bg-red-50 p-3.5 flex items-start gap-2.5" role="alert">
                <CircleAlert size={18} className="text-red-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-extrabold text-[14.5px] text-red-800">Backend từ chối — lô chưa được tạo</p>
                  <p className="text-[13.5px] text-red-700 mt-0.5 break-words">{backendError}</p>
                </div>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-2.5 mt-4">
              {/* The waiting label is the SAME canonical wording every other
                  authoritative-outcome surface uses (PartnerContext agent save,
                  Customers create/edit): it states that the backend, not the
                  transport, is being waited on. The create-shipment DOM oracle
                  asserts exactly this string. */}
              <PrimaryBtn onClick={submit} disabled={!!pending} className="flex-1">
                {pending ? "ĐANG CHỜ BACKEND XÁC NHẬN…" : <>TẠO LÔ HÀNG <ArrowRight size={17} /></>}
              </PrimaryBtn>
              <Link to="/lo-hang" className="btn-press touch-target inline-flex items-center justify-center rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-5 min-h-[48px]">Hủy</Link>
            </div>
            {pending && (
              <p className="text-[13px] font-semibold text-blue-700 mt-2.5">
                Đang lưu và xác nhận lô hàng…
              </p>
            )}
            <p className="text-[13px] text-slate-500 mt-3">
              Lô được ghi qua writer hiện có của Logistics, có audit. Mã lô trùng sẽ bị từ chối. Các trường để trống được giữ là <b>không xác định</b>, không bị ép về 0.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
