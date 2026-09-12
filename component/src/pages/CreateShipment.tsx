import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, FileCheck2, Package, Sparkles } from "lucide-react";
import { Field, PrimaryBtn, SectionTitle, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtMoney, fmtText } from "../lib/format";

// Phase B — real Create Shipment workflow.
// The donor "Thêm mới nhanh → Tạo lô hàng mới" destination now runs the
// existing Logistics creation logic: accepted quote → prefill known values →
// ask only what is missing → real validation → existing save writer → audit →
// fresh read. Duplicate shipment codes are rejected by the backend.

export default function CreateShipment() {
  const { customers, quotes, contracts, dispatch, toast } = useStore();
  const nav = useNavigate();

  const [quoteId, setQuoteId] = useState("");
  const [code, setCode] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [contractId, setContractId] = useState("");
  const [mode, setMode] = useState("Truck");
  const [incoterm, setIncoterm] = useState("DAP");
  const [pol, setPol] = useState("");
  const [pod, setPod] = useState("");
  const [etd, setEtd] = useState("");
  const [addr, setAddr] = useState("");
  const [phone, setPhone] = useState("");

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
    if (!code.trim()) { toast("Thiếu mã lô", "Nhập mã lô (ví dụ LO-0470) rồi bấm Tạo lô hàng.", "red"); return; }
    if (!customerId.trim()) { toast("Thiếu khách hàng", "Chọn khách hàng — backend từ chối lô không có khách.", "red"); return; }
    const sent = dispatch("shipment_create", {
      shipmentId: code.trim().toUpperCase(),
      // `customerId` is the canonical customer key the backend joins on
      // (quotes / receivables / partner context); the name travels separately.
      customerId: customers.find((c) => c.id === customerId)?.id ?? "",
      customer: customers.find((c) => c.id === customerId)?.name ?? "",
      contractId: contractId.trim(),
      currency: "VND",
      transport: { mode, incoterm, pol: pol.trim(), pod: pod.trim(), etd: etd.trim() },
      delivery: { addr: addr.trim(), phone_receiver: phone.trim() },
    });
    if (sent) {
      toast("Đã gửi yêu cầu tạo " + code.trim().toUpperCase(),
        "Backend validate + ghi + audit. Mã trùng sẽ bị từ chối.", "green");
      nav("/lo-hang");
    } else {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
    }
  };

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
              <Field label="Mode / Incoterm">
                <div className="flex gap-2">
                  <select value={mode} onChange={(e) => setMode(e.target.value)} className={inputCls()}>
                    {["Truck", "Sea", "Air", "Rail"].map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                  <select value={incoterm} onChange={(e) => setIncoterm(e.target.value)} className={inputCls()}>
                    {["EXW", "FCA", "FOB", "CIF", "DAP", "DDP"].map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              </Field>
              <Field label="Nơi lấy hàng (POL)"><input value={pol} onChange={(e) => setPol(e.target.value)} placeholder="Bằng Tường (Quảng Tây)" className={inputCls()} /></Field>
              <Field label="Điểm đến (POD)"><input value={pod} onChange={(e) => setPod(e.target.value)} placeholder="Hữu Nghị (Lạng Sơn)" className={inputCls()} /></Field>
              <Field label="Ngày khởi hành (ETD)"><input value={etd} onChange={(e) => setEtd(e.target.value)} placeholder="DD/MM/YYYY" className={inputCls()} /></Field>
              <Field label="SĐT người nhận"><input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="0912…" className={inputCls()} /></Field>
              <div className="md:col-span-2">
                <Field label="Địa chỉ giao hàng"><input value={addr} onChange={(e) => setAddr(e.target.value)} placeholder="Kho khách — KCN…" className={inputCls()} /></Field>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-2.5 mt-4">
              <PrimaryBtn onClick={submit} className="flex-1">TẠO LÔ HÀNG <ArrowRight size={17} /></PrimaryBtn>
              <Link to="/lo-hang" className="btn-press touch-target inline-flex items-center justify-center rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-5 min-h-[48px]">Hủy</Link>
            </div>
            <p className="text-[13px] text-slate-500 mt-3">
              Lô được ghi qua writer hiện có của Logistics, có audit. Mã lô trùng sẽ bị từ chối. Các trường để trống được giữ là <b>không xác định</b>, không bị ép về 0.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
