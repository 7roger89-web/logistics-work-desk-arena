import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ExternalLink, MapPin, PackageCheck, Truck } from "lucide-react";
import { SectionTitle, StatusDot, ToneBadge } from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtText } from "../lib/format";

// Phase B — real Tracking.
// Populated from the shipment's real transport/state facts. There is no live
// GPS feed in the Logistics model, so no current position is invented: only
// the carrier, its tracking reference/URL and the milestones that actually
// happened are shown.

export default function Tracking() {
  const { shipments } = useStore();
  const [selectedId, setSelectedId] = useState("");
  const [q, setQ] = useState("");

  const rows = useMemo(
    () => shipments.filter((s) => !q || (s.id + s.customer + (s.transport?.containerNo ?? "")).toLowerCase().includes(q.toLowerCase())),
    [shipments, q]
  );
  const selected = shipments.find((s) => s.id === selectedId) ?? rows[0] ?? null;
  const tracking = selected?.tracking ?? null;

  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          title="Theo Dõi Vận Chuyển"
          sub="Hiện trạng và mốc vận chuyển có thật từ dữ liệu lô hàng. Không mô phỏng vị trí GPS."
        />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Lọc theo mã lô, khách, biển số / container…"
          className="w-full rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] focus:border-[#1e5aa8] outline-none" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-4">
        <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
          <div className="p-3.5 border-b border-slate-200"><p className="font-extrabold text-[15px] text-[#0f2a4a]">Lô hàng ({rows.length})</p></div>
          <div className="divide-y divide-slate-100 max-h-[620px] overflow-y-auto">
            {rows.length === 0 && <p className="p-6 text-center text-slate-500 text-[14px]">Không có lô nào khớp.</p>}
            {rows.map((s) => (
              <button key={s.id} onClick={() => setSelectedId(s.id)}
                className={cx("touch-target w-full text-left p-3.5 hover:bg-slate-50",
                  selected?.id === s.id ? "bg-blue-50" : "")}>
                <div className="flex items-center gap-2">
                  <StatusDot tone={s.statusTone} />
                  <span className="font-extrabold text-[15px] text-[#0f2a4a]">{s.id}</span>
                  <ToneBadge tone={s.statusTone} size="sm">{s.status}</ToneBadge>
                </div>
                <p className="text-[13.5px] text-slate-600 mt-1">{s.customer}</p>
                <p className="text-[12.5px] text-slate-400 mt-0.5 truncate">{fmtText(s.route)}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {!selected || !tracking ? (
            <div className="rounded-2xl bg-white border p-10 text-center">
              <p className="font-extrabold text-[18px]">Chọn một lô để xem hành trình</p>
              <p className="text-slate-500 mt-1 text-[14.5px]">Dữ liệu theo dõi lấy trực tiếp từ trạng thái vận chuyển của lô.</p>
            </div>
          ) : (
            <>
              <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <Truck size={20} className="text-[#1e5aa8]" />
                  <h2 className="font-extrabold text-[19px] text-[#0f2a4a]">{selected.id} · {selected.customer}</h2>
                  <ToneBadge tone={tracking.statusTone}>{tracking.status}</ToneBadge>
                  <Link to={`/lo-hang/${selected.id}`} className="ml-auto btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[44px]">Mở 360°</Link>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                  <div className="rounded-xl bg-slate-50 border p-3.5">
                    <p className="text-[12.5px] font-semibold text-slate-500">Hãng vận chuyển</p>
                    <p className="font-extrabold text-[15px] text-[#0f2a4a] mt-0.5">{fmtText(tracking.carrier)}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 border p-3.5">
                    <p className="text-[12.5px] font-semibold text-slate-500">Mã vận đơn / xe</p>
                    <p className="font-extrabold text-[15px] text-[#0f2a4a] mt-0.5">{fmtText(tracking.reference)}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 border p-3.5">
                    <p className="text-[12.5px] font-semibold text-slate-500">Tra cứu hãng</p>
                    {tracking.trackingUrl
                      ? <a href={tracking.trackingUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 font-extrabold text-[14.5px] text-[#1e5aa8] mt-0.5">Mở trang hãng <ExternalLink size={15} /></a>
                      : <p className="font-extrabold text-[15px] text-slate-400 mt-0.5">—</p>}
                  </div>
                </div>
                <div className="mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 flex items-start gap-2">
                  <MapPin size={17} className="text-amber-700 mt-0.5 shrink-0" />
                  <p className="text-[13.5px] text-amber-900">{tracking.positionNote}</p>
                </div>
              </div>

              <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
                <div className="flex items-center gap-2 mb-3">
                  <PackageCheck size={19} className="text-[#0f2a4a]" />
                  <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Mốc vận chuyển</h3>
                </div>
                {tracking.milestones.length === 0 && <p className="text-[14px] text-slate-500">Chưa có mốc nào được ghi nhận cho lô này.</p>}
                <div className="relative pl-6">
                  <span className="absolute left-[9px] top-2 bottom-2 w-0.5 bg-slate-200" />
                  <div className="space-y-3">
                    {tracking.milestones.map((m, i) => (
                      <div key={`${m.title}-${i}`} className="relative">
                        <span className={cx("absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-white",
                          m.done ? (m.tone === "green" ? "bg-emerald-500" : m.tone === "amber" ? "bg-amber-500" : "bg-blue-500") : "bg-slate-300")} />
                        <div className="rounded-xl border border-slate-200 p-3.5">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-extrabold text-[15px] text-[#0f2a4a]">{m.title}</p>
                            <span className="text-[13px] font-bold text-slate-500">{fmtText(m.time)}</span>
                            <ToneBadge tone={m.done ? m.tone : "gray"} size="sm">{m.done ? "Đã diễn ra" : "Chưa"}</ToneBadge>
                          </div>
                          {m.desc && <p className="text-[13.5px] text-slate-600 mt-1">{m.desc}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
