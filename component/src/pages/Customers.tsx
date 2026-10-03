// ============================================================================
// Khách Hàng — Phase C1 business-contracts slice, donor Logi-good visual shell.
//
// Every write goes: typed event → the ONE bounded Python dispatcher → RBAC →
// existing writer (core.database.save_customer_to_cloud / delete_customer) →
// audit → fresh backend read → refreshed view-model. No frontend-only truth.
// ============================================================================

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { Link } from "react-router-dom";
import { useQueryParam } from "../lib/queryParam";
import { Search, Plus, PenLine, Archive, Upload, Users, ArrowRight, CircleAlert } from "lucide-react";
import {
  Field,
  GhostBtn,
  PrimaryBtn,
  SectionTitle,
  SuccessBtn,
  ToneBadge,
  inputCls,
} from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtText, matchLoose } from "../lib/format";
import { getViewModel, subscribeViewModel, type Customer } from "../lib/viewmodel";

const EMPTY_FORM = {
  id: "",
  name: "",
  phone: "",
  email: "",
  contactPerson: "",
  taxCode: "",
  address: "",
  note: "",
};

export default function Customers() {
  const { customers, dispatch, toast, role } = useStore();
  // The authoritative outcome of a customer write comes back in the NEXT fresh
  // view-model (`lastWrites`), matched by the requestId this page sent — never
  // from the transport (LOGI_UAT_REAL_USE_REPAIR_02).
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  // LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — the search box is route-backed: the
  // global search lands here with ?q=<entity> so the exact customer is already
  // filtered/highlighted, and the operator's own search survives navigation.
  const [q, setQ] = useQueryParam("q");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [archiving, setArchiving] = useState<Customer | null>(null);
  const [importing, setImporting] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [archiveReason, setArchiveReason] = useState("");
  const [importText, setImportText] = useState("");
  /** The in-flight customer write: the modal stays open until it is answered. */
  const [pending, setPending] = useState<{ event: "customer_create" | "customer_edit"; id: string; requestId: string } | null>(null);
  const [backendError, setBackendError] = useState("");

  // LOGI_INTERNAL_UX_SIMPLIFY_01 — real runtime fix: the match is
  // diacritic-insensitive ("An Phat" finds "An Phát") and undefined-safe, so
  // toneless typing and partial records filter the visible list correctly.
  const list = useMemo(
    () =>
      customers.filter(
        (c) =>
          !q ||
          matchLoose(
            [c.id, c.name, c.short, c.mst, c.taxCode, c.phone, c.email].join(" "),
            q
          )
      ),
    [customers, q]
  );

  const set = (k: keyof typeof EMPTY_FORM, v: string) =>
    setForm((f) => ({ ...f, [k]: v }));

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setBackendError("");
    setCreating(true);
  };
  const openEdit = (c: Customer) => {
    setBackendError("");
    setForm({
      id: c.id,
      name: c.name,
      phone: c.phone,
      email: c.email,
      contactPerson: c.contactPerson,
      taxCode: c.taxCode,
      address: c.address,
      note: c.note,
    });
    setEditing(c);
  };

  // ONE customer write per click. Transport success is NOT persistence: the
  // modal keeps the entered data, nothing is cleared and nothing claims
  // success until the backend's own outcome (lastWrites, matched by
  // requestId) arrives AND the fresh view-model genuinely carries the
  // customer.
  const submit = () => {
    if (pending) return; // outcome in flight — a second click must not double-send
    const id = form.id.trim().toUpperCase();
    if (!id || !form.name.trim()) {
      toast("Thiếu thông tin", "Mã và tên khách hàng là bắt buộc.", "red");
      return;
    }
    const event = editing ? "customer_edit" : "customer_create";
    const requestId = `cust-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const sent = editing
      // customer_edit writes canonical snake_case fields on the existing doc.
      ? dispatch("customer_edit", {
          id,
          name: form.name.trim(),
          phone: form.phone.trim(),
          email: form.email.trim(),
          contact_person: form.contactPerson.trim(),
          tax_code: form.taxCode.trim(),
          address: form.address.trim(),
          note: form.note.trim(),
          requestId,
        })
      : dispatch("customer_create", {
          id,
          name: form.name.trim(),
          phone: form.phone.trim(),
          email: form.email.trim(),
          contactPerson: form.contactPerson.trim(),
          taxCode: form.taxCode.trim(),
          address: form.address.trim(),
          note: form.note.trim(),
          requestId,
        });
    if (!sent) {
      // The transport itself refused: the form keeps everything the operator
      // typed and says so. No "Đã gửi", no close, no clear.
      setBackendError("Không gửi được yêu cầu — component chưa kết nối backend. Dữ liệu bạn nhập vẫn được giữ nguyên.");
      toast("Không gửi được", "Component chưa kết nối backend; chưa có gì được lưu.", "red");
      return;
    }
    setBackendError("");
    setPending({ event, id, requestId });
    toast(editing ? "Đã gửi cập nhật " + id : "Đã gửi yêu cầu tạo " + id,
      "Đang chờ backend xác nhận…", "blue");
  };

  // Consume the authoritative backend outcome. Success requires BOTH the
  // matching outcome (event + requestId + ok) AND the customer genuinely
  // present in the fresh view-model. Anything else keeps the form open with
  // the operator's data intact.
  useEffect(() => {
    if (!pending || !vm) return;
    const outcome = (vm.lastWrites ?? []).find(
      (w) => w.event === pending.event && w.requestId === pending.requestId
    );
    if (!outcome) return; // still waiting for the authoritative backend answer
    if (outcome.ok) {
      const exists = (vm.customers ?? []).some((c) => c.id === pending.id);
      if (exists) {
        setPending(null);
        setCreating(false);
        setEditing(null);
        setForm(EMPTY_FORM);
        setBackendError("");
        toast(pending.event === "customer_create" ? "Đã tạo khách hàng " + pending.id : "Đã lưu khách hàng " + pending.id,
          "Backend ghi + audit thành công; khách hàng đã có trong dữ liệu mới.", "green");
      } else {
        setPending(null);
        setBackendError("Backend báo thành công nhưng khách hàng chưa xuất hiện trong dữ liệu mới — biểu mẫu được giữ nguyên.");
      }
    } else {
      setPending(null);
      setBackendError(outcome.error || "Backend từ chối yêu cầu.");
      toast("Không lưu được khách hàng", outcome.error || "Backend từ chối.", "red");
    }
  }, [vm, pending, toast]);

  const doArchive = () => {
    if (!archiving) return;
    if (!archiveReason.trim()) {
      toast("Cần lý do lưu trữ", "Nhập lý do trước khi lưu trữ khách hàng.", "red");
      return;
    }
    dispatch("customer_archive", { id: archiving.id, reason: archiveReason.trim() });
    toast("Đã gửi lưu trữ " + archiving.id, "Chỉ Admin có quyền; backend kiểm tra RBAC.", "blue");
    setArchiving(null);
    setArchiveReason("");
  };

  const doImport = () => {
    const rows = importText
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [id, name, taxCode, phone, email, address] = line.split(/[;,|\t]/).map((s) => s.trim());
        return { id, name, taxCode, phone, email, address };
      })
      .filter((r) => r.id && r.name);
    if (rows.length === 0) {
      toast("Không có dòng để import", "Mỗi dòng: Mã;Tên;MST;SĐT;Email;Địa chỉ", "red");
      return;
    }
    dispatch("customer_import", { rows });
    toast("Đã gửi import " + rows.length + " khách hàng", "Backend bỏ qua mã đã tồn tại.", "blue");
    setImporting(false);
    setImportText("");
  };

  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Users size={18} />}
          title="Khách Hàng"
          sub="Tìm theo mã · tên · MST · SĐT · email — tạo, sửa, lưu trữ và import qua backend Logistics thật"
          right={
            <div className="flex gap-2">
              <button onClick={() => setImporting(true)} className="btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] px-4 min-h-[48px]">
                <Upload size={17} /> Import
              </button>
              <button onClick={openCreate} className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]">
                <Plus size={18} /> Khách mới
              </button>
            </div>
          }
        />
        <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
          <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nhập mã (CUST-ANPHAT), tên (An Phát), MST…" aria-label="Tìm khách hàng theo mã, tên, MST, SĐT, email" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
        </div>
        <p className="text-[13.5px] text-slate-500 mt-2.5">
          Tìm thấy <b className="text-[#0f2a4a]">{list.length} khách hàng</b>
          {q ? <> cho “{q}”</> : null} · Mỗi khách hiển thị: mã · MST · liên hệ · địa chỉ.
        </p>
      </div>

      {/* Desktop table */}
      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="tbl w-full text-[14px] min-w-[880px]">
            <thead>
              <tr>
                <th>Mã KH</th>
                <th>Tên khách hàng</th>
                <th>MST</th>
                <th>Liên hệ</th>
                <th>Địa chỉ</th>
                <th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {list.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50">
                  <td><span className="font-extrabold text-[#1e5aa8] text-[15px]">{c.id}</span></td>
                  <td className="font-semibold max-w-[220px]">{c.name}</td>
                  <td>{fmtText(c.taxCode)}</td>
                  <td className="text-[13px]">
                    <span className="block">{fmtText(c.contactPerson)}</span>
                    <span className="block text-slate-500">{fmtText(c.phone)}</span>
                  </td>
                  <td className="max-w-[240px] text-[13px] text-slate-600">{fmtText(c.address)}</td>
                  <td>
                    <div className="flex flex-wrap gap-1.5">
                      <Link to={`/khach-hang/${encodeURIComponent(c.id)}`} data-testid="customer-open-playbook" className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-blue-200 text-[13px] font-bold px-3 min-h-[44px] text-[#1e5aa8]"><ArrowRight size={15} /> Mở hồ sơ</Link>
                      <button onClick={() => openEdit(c)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]"><PenLine size={15} /> Sửa</button>
                      {role === "ADMIN" && (
                        <button onClick={() => setArchiving(c)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-red-200 text-red-700 text-[13px] font-bold px-3 min-h-[44px]"><Archive size={15} /> Lưu trữ</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {list.length === 0 && (
          <div className="p-8 text-center">
            <p className="font-bold text-[16px]">Không tìm thấy khách hàng nào</p>
            <p className="text-[14px] text-slate-500 mt-1">Thử từ khóa khác hoặc tạo khách mới.</p>
            <button onClick={openCreate} className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5"><Plus size={17} /> Khách mới</button>
          </div>
        )}
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {list.map((c) => (
          <div key={c.id} className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-extrabold text-[17px] text-[#0f2a4a]">{c.id}</span>
                <ToneBadge tone="blue" size="sm">MST {fmtText(c.taxCode)}</ToneBadge>
              </div>
              <p className="font-semibold text-[14.5px] mt-1">{c.name}</p>
              <p className="text-[13px] text-slate-500">{fmtText(c.address)}</p>
              <p className="text-[12.5px] text-slate-400 mt-1">{fmtText(c.contactPerson)} · {fmtText(c.phone)}</p>
            </div>
            <div className="px-4 pb-3">
              <Link to={`/khach-hang/${encodeURIComponent(c.id)}`} data-testid="customer-open-playbook" className="touch-target flex w-full items-center justify-center gap-1.5 rounded-lg border border-blue-200 text-[14px] font-bold text-[#1e5aa8]">
                Mở hồ sơ <ArrowRight size={16} aria-hidden="true" />
              </Link>
            </div>
            <div className="grid grid-cols-2 border-t">
              <button onClick={() => openEdit(c)} className="touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]"><PenLine size={17} /> SỬA</button>
              {role === "ADMIN" ? (
                <button onClick={() => setArchiving(c)} className="touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-red-700 min-h-[52px]"><Archive size={17} /> LƯU TRỮ</button>
              ) : (
                <Link to="/kinh-doanh-bao-gia" className="touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]">BÁO GIÁ <ArrowRight size={17} /></Link>
              )}
            </div>
          </div>
        ))}
        {list.length === 0 && (
          <div className="rounded-2xl bg-white border p-8 text-center">
            <p className="font-bold text-[16px]">Không tìm thấy khách hàng nào</p>
            <button onClick={openCreate} className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center"><Plus size={17} /> Khách mới</button>
          </div>
        )}
      </div>

      {/* MODAL: create / edit */}
      {(creating || editing) && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => { if (!pending) { setCreating(false); setEditing(null); setBackendError(""); } }} />
          <div className="relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[90vh] overflow-auto" style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" }}>
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">{editing ? "Sửa khách hàng " + editing.id : "Tạo khách hàng mới"}</h3>
            <p className="text-[13.5px] text-slate-500">Mọi thay đổi đi qua backend Logistics (RBAC + audit).</p>
            <div className="grid sm:grid-cols-2 gap-3 mt-4">
              <Field label="Mã khách hàng" required><input value={form.id} disabled={!!editing} onChange={(e) => set("id", e.target.value)} placeholder="VD: CUST-ABC" className={inputCls(!form.id ? "missing" : "ok")} /></Field>
              <Field label="Tên khách hàng" required><input value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="Công ty / cá nhân" className={inputCls(!form.name ? "missing" : "ok")} /></Field>
              <Field label="Mã số thuế"><input value={form.taxCode} onChange={(e) => set("taxCode", e.target.value)} placeholder="MST" className={inputCls()} /></Field>
              <Field label="Người liên hệ"><input value={form.contactPerson} onChange={(e) => set("contactPerson", e.target.value)} placeholder="Tên người liên hệ" className={inputCls()} /></Field>
              <Field label="Số điện thoại"><input value={form.phone} onChange={(e) => set("phone", e.target.value)} placeholder="SĐT" className={inputCls()} /></Field>
              <Field label="Email"><input value={form.email} onChange={(e) => set("email", e.target.value)} placeholder="email" className={inputCls()} /></Field>
            </div>
            <div className="grid gap-3 mt-3">
              <Field label="Địa chỉ"><input value={form.address} onChange={(e) => set("address", e.target.value)} placeholder="Địa chỉ kho / văn phòng" className={inputCls()} /></Field>
              <Field label="Ghi chú"><input value={form.note} onChange={(e) => set("note", e.target.value)} placeholder="Ghi chú nội bộ" className={inputCls()} /></Field>
            </div>

            {/* The REAL backend/transport refusal — shown verbatim; the modal
                deliberately stayed open with everything the operator typed. */}
            {backendError && (
              <div className="mt-4 rounded-xl border-2 border-red-200 bg-red-50 p-3.5 flex items-start gap-2.5" role="alert">
                <CircleAlert size={18} className="text-red-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-extrabold text-[14.5px] text-red-800">Chưa lưu được — dữ liệu vẫn được giữ</p>
                  <p className="text-[13.5px] text-red-700 mt-0.5 break-words">{backendError}</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2.5 mt-5">
              <GhostBtn onClick={() => { if (!pending) { setCreating(false); setEditing(null); setBackendError(""); } }} disabled={!!pending}>Hủy</GhostBtn>
              <SuccessBtn onClick={submit} disabled={!!pending}>
                {pending ? "ĐANG CHỜ BACKEND XÁC NHẬN…" : <>💾 {editing ? "LƯU THAY ĐỔI" : "TẠO KHÁCH HÀNG"}</>}
              </SuccessBtn>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: archive */}
      {archiving && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => setArchiving(null)} />
          <div className="relative bg-white w-full sm:max-w-[460px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up">
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">Lưu trữ {archiving.id}?</h3>
            <p className="text-[14.5px] text-slate-600 mt-1.5">Khách <b>{archiving.name}</b> sẽ bị soft-delete (không xóa vật lý). Chỉ Admin có quyền.</p>
            <div className="grid gap-3 mt-4">
              <Field label="Lý do lưu trữ" required error={!archiveReason ? "Nhập lý do trước khi lưu trữ" : undefined}>
                <input value={archiveReason} onChange={(e) => setArchiveReason(e.target.value)} placeholder="VD: ngừng hợp tác" className={inputCls(!archiveReason ? "missing" : "ok")} />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setArchiving(null)}>Hủy</GhostBtn>
              <button onClick={doArchive} className="btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-[15.5px] px-5 min-h-[48px]">LƯU TRỮ</button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: import */}
      {importing && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => setImporting(false)} />
          <div className="relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up" style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" }}>
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">Import khách hàng</h3>
            <p className="text-[13.5px] text-slate-500">Mỗi dòng một khách: <b>Mã;Tên;MST;SĐT;Email;Địa chỉ</b></p>
            <div className="grid gap-3 mt-4">
              <Field label="Dữ liệu (mỗi dòng 1 khách)">
                <textarea value={importText} onChange={(e) => setImportText(e.target.value)} rows={6} placeholder={"CUST-XYZ;Khách XYZ;0109999000;0988111222;xyz@example.com;KCN Test"} className={cx(inputCls(), "font-mono text-[13.5px]")} />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setImporting(false)}>Hủy</GhostBtn>
              <PrimaryBtn onClick={doImport}>IMPORT</PrimaryBtn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
