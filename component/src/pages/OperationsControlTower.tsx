import { Link, useSearchParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  CalendarClock,
  CircleAlert,
  Crosshair,
  Layers3,
  ShieldCheck,
  Users,
} from "lucide-react";
import { SectionTitle, ToneBadge } from "../components/ui";
import { useStore } from "../lib/store";
import type {
  OperationsControlConcentrationRow,
  OperationsControlQueueItem,
  OperationsControlWorkloadRow,
} from "../lib/viewmodel";
import { cx } from "../lib/format";

type BandFilter = "ALL" | "BLOCKING" | "OVERDUE" | "DUE_SOON" | "ACTION" | "UNKNOWN";

const BAND_LABEL: Record<string, string> = {
  BLOCKING: "Chặn",
  OVERDUE: "Quá hạn",
  DUE_SOON: "Sắp hạn",
  ACTION: "Cần làm",
  INFO: "Thông tin",
};

function bandMeta(item: OperationsControlQueueItem) {
  if (item.unknown) {
    return { label: "Chưa rõ", cls: "border-slate-300 bg-slate-100 text-slate-700" };
  }
  if (item.sourcePriority === "Khan" && item.band === "ACTION") {
    return { label: "Gấp", cls: "border-red-200 bg-red-50 text-red-800" };
  }
  if (item.band === "BLOCKING" || item.band === "OVERDUE") {
    return { label: BAND_LABEL[item.band], cls: "border-red-200 bg-red-50 text-red-800" };
  }
  if (item.band === "DUE_SOON") {
    return { label: "Sắp hạn", cls: "border-amber-200 bg-amber-50 text-amber-900" };
  }
  return { label: BAND_LABEL[item.band] ?? item.band, cls: "border-blue-200 bg-blue-50 text-blue-800" };
}

function InterventionRow({ item }: { item: OperationsControlQueueItem }) {
  const meta = bandMeta(item);
  return (
    <Link
      to={item.route}
      data-testid="control-intervention-row"
      data-control-band={item.band}
      data-control-shipment={item.shipmentId}
      className="btn-press block rounded-xl border-2 border-slate-200 bg-white p-3 hover:border-[#1e5aa8]"
    >
      <div className="flex flex-wrap items-start gap-2.5">
        <span className={cx("shrink-0 rounded-lg border px-2 py-1 text-[11.5px] font-extrabold", meta.cls)}>
          {meta.label}
        </span>
        <div className="min-w-[220px] flex-1">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <b className="text-[14.5px] text-[#0f2a4a]">{item.action}</b>
            <span className="text-[12.5px] font-semibold text-slate-500">
              {item.shipmentId} · {item.customer}
            </span>
          </div>
          {item.reason ? <p className="mt-0.5 text-[12.5px] text-slate-600">{item.reason}</p> : null}
          <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-slate-500">
            <span>Vị trí: <b className="text-slate-700">{item.shipmentStatus}</b></span>
            {item.owner ? <span>Phụ trách: <b className="text-slate-700">{item.owner}</b></span> : <span>Phụ trách: <b className="text-slate-700">Chưa xác định</b></span>}
            {item.deadline ? <span>Hạn: <b className="text-slate-700">{item.deadline}</b></span> : null}
            {item.blockedGate ? <span>Chặn: <b className="text-red-700">{item.blockedGate}</b></span> : null}
            <span>Nguồn: <b className="text-slate-700">{item.sourceType}</b></span>
          </div>
        </div>
        <span className="inline-flex min-h-[40px] shrink-0 items-center gap-1.5 rounded-lg bg-[#0f2a4a] px-3 text-[13px] font-bold text-white">
          Mở đúng việc <ArrowRight size={14} />
        </span>
      </div>
    </Link>
  );
}

function ConcentrationColumn({
  title,
  rows,
  onSelect,
  testId,
}: {
  title: string;
  rows: OperationsControlConcentrationRow[];
  onSelect: (row: OperationsControlConcentrationRow) => void;
  testId: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3" data-testid={testId}>
      <h3 className="text-[13.5px] font-extrabold text-[#0f2a4a]">{title}</h3>
      <div className="mt-2 space-y-1.5">
        {rows.length === 0 ? (
          <p className="text-[12.5px] text-slate-500">Chưa có cụm từ các mục cần quản lý chú ý.</p>
        ) : rows.slice(0, 5).map((row) => (
          <button
            key={row.key}
            type="button"
            onClick={() => onSelect(row)}
            className="touch-target w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-left hover:border-[#1e5aa8]"
          >
            <span className="flex items-center justify-between gap-2">
              <b className="min-w-0 truncate text-[12.5px] text-slate-700">{row.label}</b>
              <span className="shrink-0 text-[12px] font-extrabold text-[#1e5aa8]">{row.count}</span>
            </span>
            <span className="mt-0.5 block text-[11.5px] text-slate-500">
              {row.blocking ? `${row.blocking} chặn` : "0 chặn"}
              {row.overdue ? ` · ${row.overdue} quá hạn` : ""}
              {row.dueSoon ? ` · ${row.dueSoon} sắp hạn` : ""}
              {row.unknown ? ` · ${row.unknown} chưa rõ` : ""}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

function WorkloadRow({
  row,
  selectOwner,
  selectBand,
}: {
  row: OperationsControlWorkloadRow;
  selectOwner: (ownerKey: string) => void;
  selectBand: (ownerKey: string, band: BandFilter) => void;
}) {
  const stat = [
    ["BLOCKING", "Chặn", row.blocking],
    ["OVERDUE", "Quá hạn", row.overdue],
    ["DUE_SOON", "Sắp hạn", row.dueSoon],
    ["ACTION", "Khác cần chú ý", row.action],
    ["UNKNOWN", "Chưa rõ", row.unknown],
  ] as const;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3" data-testid="control-workload-row">
      <button type="button" onClick={() => selectOwner(row.ownerKey)} className="text-left">
        <b className="text-[13.5px] text-[#0f2a4a]">{row.owner}</b>
      </button>
      <div className="mt-2 grid grid-cols-2 gap-1.5 sm:grid-cols-5">
        {stat.map(([band, label, value]) => (
          <button
            key={band}
            type="button"
            onClick={() => selectBand(row.ownerKey, band)}
            className="touch-target rounded-lg bg-slate-50 px-2 py-1.5 text-left hover:bg-blue-50"
          >
            <span className="block text-[11px] font-semibold text-slate-500">{label}</span>
            <span className="text-[16px] font-extrabold text-[#0f2a4a]">{value}</span>
          </button>
        ))}
      </div>
      <p className="mt-1.5 text-[11.5px] text-slate-400">Các cột có thể chồng lấn; không cộng thành “điểm tải”.</p>
    </div>
  );
}

export default function OperationsControlTower() {
  const { operationsControl } = useStore();
  const [sp, setSp] = useSearchParams();

  if (!operationsControl) {
    return (
      <div className="max-w-[1000px] rounded-2xl border border-slate-200 bg-white p-5">
        <h1 className="text-[19px] font-extrabold text-[#0f2a4a]">Điều hành vận hành</h1>
        <p className="mt-1 text-[14px] text-slate-500">Chưa nhận được projection điều hành từ nguồn Logistics. Không hiển thị số liệu thay thế.</p>
      </div>
    );
  }

  const filter = (sp.get("band") || "ALL") as BandFilter;
  const owner = sp.get("owner") || "";
  const customer = sp.get("customer") || "";
  const gate = sp.get("gate") || "";
  const moduleId = sp.get("module") || "";

  const queue = operationsControl.interventionQueue.filter((item) => {
    if (filter === "BLOCKING" && item.band !== "BLOCKING") return false;
    if (filter === "OVERDUE" && item.band !== "OVERDUE") return false;
    if (filter === "DUE_SOON" && item.band !== "DUE_SOON") return false;
    if (filter === "ACTION" && item.band !== "ACTION") return false;
    if (filter === "UNKNOWN" && !item.unknown) return false;
    if (owner && (item.owner || "UNASSIGNED") !== owner) return false;
    if (customer && item.customer !== customer) return false;
    if (gate && item.blockedGate !== gate) return false;
    if (moduleId && item.moduleTemplateId !== moduleId) return false;
    return true;
  });

  const setFilters = (next: Record<string, string>) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(next)) if (value) params.set(key, value);
    setSp(params);
  };

  const selectOwner = (ownerKey: string) => setFilters({ owner: ownerKey });
  const selectBand = (ownerKey: string, band: BandFilter) => setFilters({ owner: ownerKey, band });
  const hasFilter = filter !== "ALL" || owner || customer || gate || moduleId;

  const scope = operationsControl.scope;

  return (
    <div className="max-w-[1280px] space-y-4 pb-4" data-testid="operations-control-tower">
      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="control-header">
        <SectionTitle
          icon={<Crosshair size={20} />}
          title="Điều hành vận hành"
          sub="Chọn chỗ cần can thiệp từ cùng Attention truth của Support. Chỉ đọc; không có điểm rủi ro hay chấm điểm nhân viên."
          right={<ToneBadge tone="blue" size="sm">CHỈ ĐỌC</ToneBadge>}
        />
        <div className="flex flex-wrap gap-2 text-[12.5px] text-slate-600">
          <span className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5">Deadline: theo <b>ngày có nguồn</b>, không giả đồng hồ &lt;24h</span>
          <Link to="/bao-cao-ceo" className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 font-bold text-[#1e5aa8]">Mở Báo cáo CEO →</Link>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-4" data-testid="control-scope">
        <SectionTitle
          icon={<ShieldCheck size={18} />}
          title="Phạm vi & độ phủ dữ liệu"
          sub="“Chưa có tín hiệu” chỉ nói về nguồn hiện có — không có nghĩa lô khỏe hay an toàn."
        />
        <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-5">
          {[
            ["Lô trong phạm vi", scope.shipmentCount, "bg-slate-50 border-slate-200"],
            ["Có Attention", scope.attentionShipmentCount, "bg-blue-50 border-blue-200"],
            ["Cần quản lý chú ý", scope.managerItemCount, "bg-amber-50 border-amber-200"],
            ["Chưa có tín hiệu", scope.noSignalShipmentCount, "bg-slate-50 border-slate-200"],
            ["Chưa rõ", scope.unknownShipmentCount, "bg-violet-50 border-violet-200"],
          ].map(([label, value, cls]) => (
            <div key={String(label)} className={cx("rounded-xl border p-3", String(cls))}>
              <p className="text-[11.5px] font-bold text-slate-500">{label}</p>
              <p className="mt-0.5 text-[24px] font-extrabold text-[#0f2a4a]">{value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border-2 border-[#0f2a4a] bg-white p-4 md:p-5" data-testid="control-intervention-queue">
        <SectionTitle
          icon={<AlertTriangle size={19} />}
          title={`Cần quản lý chú ý (${queue.length})`}
          sub="Chặn · quá hạn · sắp hạn · dữ liệu chưa rõ · primary action thật sự khẩn. Không phải toàn bộ việc của Support."
          right={hasFilter ? (
            <button type="button" onClick={() => setSp(new URLSearchParams())} className="touch-target rounded-lg border border-slate-300 bg-white px-3 text-[12.5px] font-bold text-slate-600">
              Xóa lọc
            </button>
          ) : undefined}
        />
        <div className="mb-3 flex flex-wrap gap-1.5">
          {([
            ["ALL", "Tất cả"],
            ["BLOCKING", "Chặn"],
            ["OVERDUE", "Quá hạn"],
            ["DUE_SOON", "Sắp hạn"],
            ["ACTION", "Khác cần chú ý"],
            ["UNKNOWN", "Chưa rõ"],
          ] as const).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setFilters({ band: id === "ALL" ? "" : id })}
              className={cx(
                "touch-target rounded-lg border px-3 text-[12.5px] font-bold",
                filter === id && !owner && !customer && !gate && !moduleId
                  ? "border-[#0f2a4a] bg-[#0f2a4a] text-white"
                  : "border-slate-200 bg-white text-slate-600 hover:border-[#1e5aa8]"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="space-y-2">
          {queue.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-[13.5px] text-slate-500">
              Không có mục phù hợp với bộ lọc hiện tại. Đây không phải chứng nhận “mọi lô đều ổn”.
            </div>
          ) : queue.slice(0, 12).map((item) => <InterventionRow key={item.id} item={item} />)}
        </div>
        {queue.length > 12 ? <p className="mt-2 text-[12px] text-slate-500">Đang hiện 12/{queue.length} mục; dùng bộ lọc để thu hẹp đúng nhóm cần xem.</p> : null}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="control-horizon">
        <SectionTitle
          icon={<CalendarClock size={19} />}
          title="Hạn theo dữ liệu hiện có"
          sub={`Mốc ngày ${operationsControl.horizon.asOf} · chỉ task có deadline cấu trúc; không suy diễn ETA/ETD hay guidance text.`}
        />
        <div className="grid gap-3 md:grid-cols-3">
          {operationsControl.horizon.buckets.map((bucket) => (
            <div key={bucket.id} className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
              <div className="flex items-center justify-between">
                <b className="text-[13.5px] text-[#0f2a4a]">{bucket.label}</b>
                <span className="rounded-full bg-white px-2 py-0.5 text-[12px] font-extrabold text-[#1e5aa8]">{bucket.count}</span>
              </div>
              <div className="mt-2 space-y-1.5">
                {bucket.items.length === 0 ? <p className="text-[12px] text-slate-500">Không có mốc đủ authority.</p> : bucket.items.slice(0, 4).map((item) => (
                  <Link key={item.id} to={item.route} className="block rounded-lg bg-white px-2.5 py-2 text-[12px] hover:ring-1 hover:ring-[#1e5aa8]">
                    <b className="text-slate-700">{item.shipmentId}</b>
                    <span className="ml-1.5 text-slate-500">{item.action}</span>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="control-workload">
        <SectionTitle
          icon={<Users size={19} />}
          title="Phân bố việc theo trách nhiệm"
          sub="Đếm sự thật theo loại việc; không có điểm tải, leaderboard hay kết luận ai “quá tải”."
        />
        {operationsControl.workload.length === 0 ? (
          <p className="text-[13px] text-slate-500">Chưa có manager-grade Attention để nhóm theo trách nhiệm.</p>
        ) : (
          <div className="grid gap-2.5 lg:grid-cols-2">
            {operationsControl.workload.map((row) => (
              <WorkloadRow key={row.ownerKey} row={row} selectOwner={selectOwner} selectBand={selectBand} />
            ))}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="control-concentration">
        <SectionTitle
          icon={<Layers3 size={19} />}
          title="Điểm tập trung"
          sub="Cụm công việc để điều phối chung; số lượng lớn không tự động được gọi là bottleneck hay rủi ro."
        />
        <div className="grid gap-3 lg:grid-cols-3">
          <ConcentrationColumn
            title="Theo khách hàng"
            rows={operationsControl.concentration.customers}
            testId="control-concentration-customers"
            onSelect={(row) => setFilters({ customer: row.key })}
          />
          <ConcentrationColumn
            title="Theo cổng đang chặn"
            rows={operationsControl.concentration.gates}
            testId="control-concentration-gates"
            onSelect={(row) => setFilters({ gate: row.key })}
          />
          <ConcentrationColumn
            title="Theo Work Module"
            rows={operationsControl.concentration.modules}
            testId="control-concentration-modules"
            onSelect={(row) => setFilters({ module: row.key })}
          />
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-3" data-testid="control-unavailable">
        <div className="flex items-start gap-2">
          <CircleAlert size={17} className="mt-0.5 shrink-0 text-slate-500" />
          <div>
            <p className="text-[12.5px] font-extrabold text-slate-700">Những gì V1 cố ý chưa kết luận</p>
            <ul className="mt-1 list-disc pl-4 text-[12px] text-slate-500">
              {operationsControl.unavailable.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
