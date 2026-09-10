// ============================================================================
// Tạo hợp đồng mới — Phase C1, donor Logi-good visual shell.
//
// contract_create → the ONE bounded dispatcher → RBAC (can_edit_contract /
// sales_write) → save_contract_to_cloud → audit → fresh read. Kind/identity/
// goods/docgen are completed on the detail work desk afterwards.
// ============================================================================

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, FileText } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, SectionTitle, inputCls } from "../components/ui";
import { useStore } from "../lib/store";

export default function NewContract() {
  const { customers, dispatch, toast } = useStore();
  const nav = useNavigate();
  const [id, setId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [kind, setKind] = useState("HDMB");
  const [note, setNote] = useState("");

  const submit = () => {
    const cid = id.trim().toUpperCase();
    if (!cid) {
      toast("Thiếu số hợp đồng", "Nhập số hợp đồng (VD: HDMB-0310).", "red");
      return;
    }
    if (!customerId) {
      toast("Chưa chọn khách hàng", "Chọn khách hàng / đối tác cho hợp đồng.", "red");
      return;
    }
    const sent = dispatch("contract_create", { id: cid, customerId, kind, note: note.trim() });
    if (sent) {
      toast("Đã gửi tạo hợp đồng " + cid, "Backend ghi + audit; tiếp tục nhập hàng hóa & sinh chứng từ.", "green");
      nav("/hop-dong/" + cid);
    } else {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
    }
  };

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
          <Field label="Khách hàng / đối tác" required error={!customerId ? "Chọn khách hàng" : undefined}>
            <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} className={inputCls(!customerId ? "missing" : "ok")}>
              <option value="">-- Chọn khách --</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.id})</option>)}
            </select>
          </Field>
          <Field label="Ghi chú"><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi chú nội bộ" className={inputCls()} /></Field>
        </div>
        <div className="grid grid-cols-2 gap-2.5 mt-5">
          <GhostBtn onClick={() => nav(-1)}>Hủy</GhostBtn>
          <PrimaryBtn onClick={submit}>💾 TẠO HỢP ĐỒNG</PrimaryBtn>
        </div>
      </div>
    </div>
  );
}
