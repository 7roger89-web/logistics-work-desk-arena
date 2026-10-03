import { useMemo } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Building2,
  CircleAlert,
  Clock3,
  FileText,
  Layers3,
  ListTodo,
  LockKeyhole,
  MapPin,
  Package,
  PenLine,
} from "lucide-react";
import { SectionTitle, ToneBadge } from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtText } from "../lib/format";
import type { AttentionItem } from "../lib/viewmodel";
import {
  buildCustomerPlaybook,
  customerIdFromPath,
} from "../lib/customerPlaybook";

const BAND_META: Record<
  AttentionItem["band"],
  { label: string; cls: string; icon: typeof CircleAlert }
> = {
  BLOCKING: {
    label: "Chặn",
    cls: "border-red-200 bg-red-50 text-red-800",
    icon: LockKeyhole,
  },
  OVERDUE: {
    label: "Quá hạn",
    cls: "border-red-200 bg-red-50 text-red-800",
    icon: Clock3,
  },
  DUE_SOON: {
    label: "Sắp hạn",
    cls: "border-amber-200 bg-amber-50 text-amber-900",
    icon: Clock3,
  },
  ACTION: {
    label: "Cần làm",
    cls: "border-blue-200 bg-blue-50 text-blue-800",
    icon: ListTodo,
  },
  INFO: {
    label: "Thông tin",
    cls: "border-slate-200 bg-slate-50 text-slate-700",
    icon: CircleAlert,
  },
};

function attentionActionLabel(item: AttentionItem): string {
  if (item.sourceType === "WORK_MODULE") return "Mở quy trình";
  if (item.sourceType === "TASK") return "Mở việc";
  return "Mở xử lý";
}

export default function CustomerPlaybook() {
  const { id: paramId } = useParams();
  const { pathname } = useLocation();
  const customerId = customerIdFromPath(pathname, paramId);
  const { customers, shipments, attention } = useStore();

  const playbook = useMemo(
    () =>
      buildCustomerPlaybook({
        customerId,
        customers,
        shipments,
        attention,
      }),
    [customerId, customers, shipments, attention]
  );

  if (playbook.status === "NOT_FOUND" || !playbook.customer) {
    return (
      <div
        className="max-w-[1000px] space-y-4 pb-4"
        data-testid="customer-playbook-not-found"
      >
        <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Link
              to="/khach-hang"
              className="touch-target inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13.5px] font-bold text-[#0f2a4a] hover:border-[#1e5aa8]"
            >
              <ArrowLeft size={16} /> Danh bạ khách hàng
            </Link>
            <ToneBadge tone="blue" size="sm">
              CHỈ ĐỌC
            </ToneBadge>
          </div>
          <h1 className="mt-3 text-[19px] font-extrabold text-[#0f2a4a]">
            Không tìm thấy hồ sơ khách hàng {customerId || "—"}
          </h1>
          <p className="mt-1 text-[14px] text-slate-600">
            Mã khách hàng này hiện không có trong danh bạ đang tải. Kiểm tra lại mã hoặc quay về danh bạ khách hàng.
          </p>
        </section>
      </div>
    );
  }

  const c = playbook.customer;

  return (
    <div
      className="max-w-[1280px] space-y-4 pb-4"
      data-testid="customer-playbook"
      data-customer-id={c.id}
    >
      {/* BLOCK 1: CUSTOMER IDENTITY + GHI CHÚ VẬN HÀNH */}
      <section
        className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5"
        data-testid="playbook-identity-note"
      >
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <Link
            to={c.masterListHref}
            data-testid="playbook-back-customers"
            className="touch-target inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] font-bold text-[#0f2a4a] hover:border-[#1e5aa8]"
          >
            <ArrowLeft size={15} /> Danh bạ khách hàng
          </Link>
          <div className="flex flex-wrap items-center gap-2">
            <ToneBadge tone="blue" size="sm">
              CHỈ ĐỌC
            </ToneBadge>
            <Link
              to={c.masterEditHref}
              data-testid="playbook-edit-in-master"
              className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 bg-white px-3 py-2 text-[13px] font-bold text-[#0f2a4a] hover:border-[#1e5aa8]"
            >
              <PenLine size={15} /> Sửa tại Danh bạ khách hàng
            </Link>
          </div>
        </div>

        <SectionTitle
          icon={<Building2 size={20} />}
          title={`${c.name} (${c.id})`}
          sub="Hồ sơ ngữ cảnh vận hành theo dữ liệu danh bạ và các lô đã liên kết chính xác mã khách hàng."
        />

        <dl
          className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3 text-[13.5px]"
          data-testid="playbook-identity-facts"
        >
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
            <dt className="text-[11.5px] font-bold text-slate-500">Mã khách hàng</dt>
            <dd className="mt-0.5 font-extrabold text-[#0f2a4a] break-words">{c.id}</dd>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
            <dt className="text-[11.5px] font-bold text-slate-500">Mã số thuế</dt>
            <dd className="mt-0.5 font-semibold text-slate-800 break-words">{fmtText(c.taxCode)}</dd>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
            <dt className="text-[11.5px] font-bold text-slate-500">Người liên hệ</dt>
            <dd className="mt-0.5 font-semibold text-slate-800 break-words">{fmtText(c.contactPerson)}</dd>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
            <dt className="text-[11.5px] font-bold text-slate-500">Số điện thoại</dt>
            <dd className="mt-0.5 font-semibold text-slate-800 break-words">{fmtText(c.phone)}</dd>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
            <dt className="text-[11.5px] font-bold text-slate-500">Email</dt>
            <dd className="mt-0.5 font-semibold text-slate-800 break-words">{fmtText(c.email)}</dd>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
            <dt className="text-[11.5px] font-bold text-slate-500">Địa chỉ</dt>
            <dd className="mt-0.5 font-semibold text-slate-800 break-words">{fmtText(c.address)}</dd>
          </div>
        </dl>

        <div
          className="mt-3.5 rounded-xl border border-slate-200 bg-amber-50/40 p-3.5"
          data-testid="playbook-operating-note"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="inline-flex items-center gap-1.5 text-[14px] font-extrabold text-[#0f2a4a]">
              <FileText size={16} className="text-[#1e5aa8]" aria-hidden="true" />
              {c.operatingNoteLabel}
            </h3>
            <span className="text-[11.5px] font-semibold text-slate-500">
              Nguồn: trường ghi chú danh bạ khách hàng
            </span>
          </div>
          {c.hasOperatingNote ? (
            <p
              className="mt-1.5 whitespace-pre-line break-words text-[14px] font-medium text-slate-800"
              data-testid="playbook-operating-note-text"
            >
              {c.note}
            </p>
          ) : (
            <p
              className="mt-1.5 text-[13.5px] text-slate-500"
              data-testid="playbook-operating-note-empty"
            >
              {c.operatingNoteEmptyText}
            </p>
          )}
        </div>

        <p
          className="mt-2.5 text-[12px] text-slate-500"
          data-testid="playbook-coverage-note"
        >
          {playbook.coverage.note}
        </p>
      </section>

      {/* BLOCK 2: CUSTOMER ATTENTION — HERO */}
      <section
        className="rounded-2xl border-2 border-[#0f2a4a] bg-white p-4 md:p-5"
        data-testid="playbook-attention-hero"
      >
        <SectionTitle
          icon={<AlertTriangle size={19} />}
          title={`Việc cần chú ý của khách hàng (${playbook.attention.totalCount})`}
          sub={`Từ cùng nguồn Attention chung, lọc theo các lô có customerId = ${c.id}. Giữ nguyên mức độ, thứ tự, lý do và đường dẫn xử lý.`}
        />

        {playbook.attention.visibleItems.length === 0 ? (
          <div
            className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-[13.5px] text-slate-600"
            data-testid="playbook-attention-empty"
          >
            {playbook.attention.emptyText}
          </div>
        ) : (
          <div className="space-y-2.5">
            {playbook.attention.visibleItems.map((item) => {
              const meta =
                item.sourcePriority === "Khan"
                  ? {
                      label: "Gấp",
                      cls: "border-red-200 bg-red-50 text-red-800",
                      icon: CircleAlert,
                    }
                  : BAND_META[item.band] ?? BAND_META.ACTION;
              const Icon = meta.icon;
              return (
                <article
                  key={item.id}
                  className="rounded-xl border border-slate-200 bg-white p-3"
                  data-testid="playbook-attention-item"
                  data-attention-id={item.id}
                  data-attention-band={item.band}
                  data-attention-source={item.sourceType}
                  data-attention-shipment={item.shipmentId}
                  data-attention-unknown={item.unknown ? "true" : "false"}
                >
                  <div className="flex flex-wrap items-start gap-2.5">
                    <span
                      className={cx(
                        "inline-flex shrink-0 items-center gap-1 rounded-lg border px-2 py-1 text-[11.5px] font-extrabold",
                        meta.cls
                      )}
                    >
                      <Icon size={13} aria-hidden="true" /> {meta.label}
                    </span>
                    {item.unknown && (
                      <span
                        className="inline-flex shrink-0 items-center rounded-lg border border-slate-300 bg-slate-100 px-2 py-1 text-[11.5px] font-extrabold text-slate-700"
                        data-testid="playbook-attention-unknown-badge"
                      >
                        UNKNOWN · Chưa xác định
                      </span>
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                        <b className="break-words text-[14.5px] text-[#0f2a4a]">
                          {item.action}
                        </b>
                        <span className="text-[12.5px] font-bold text-[#1e5aa8]">
                          Lô {item.shipmentId}
                        </span>
                      </div>
                      {item.reason && (
                        <p className="mt-0.5 break-words text-[12.5px] text-slate-600">
                          {item.reason}
                        </p>
                      )}
                      <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-slate-500">
                        {item.blockedGate && (
                          <span>
                            Chặn: <b className="text-red-700">{item.blockedGate}</b>
                          </span>
                        )}
                        {item.owner && (
                          <span>
                            Phụ trách: <b className="text-slate-700">{item.owner}</b>
                          </span>
                        )}
                        {item.deadline && (
                          <span>
                            Hạn: <b className="text-slate-700">{item.deadline}</b>
                          </span>
                        )}
                        {item.context && <span>{item.context}</span>}
                        {item.unknown && (
                          <span className="font-semibold text-slate-700">
                            Chưa xác định đủ dữ liệu — không coi là hoàn thành
                          </span>
                        )}
                      </div>
                    </div>
                    <Link
                      to={item.route}
                      data-testid="playbook-attention-link"
                      className="btn-press touch-target inline-flex min-h-[40px] shrink-0 items-center gap-1.5 rounded-lg bg-[#0f2a4a] px-3 text-[13px] font-bold text-white"
                    >
                      {attentionActionLabel(item)} <ArrowRight size={14} />
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
        {playbook.attention.truncated && (
          <p className="mt-2 text-[12px] text-slate-500">
            Đang hiển thị {playbook.attention.visibleItems.length}/
            {playbook.attention.totalCount} mục theo thứ tự của Attention.
          </p>
        )}
      </section>

      {/* BLOCK 3: CURRENT LINKED SHIPMENTS */}
      <section
        className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5"
        data-testid="playbook-linked-shipments"
      >
        <SectionTitle
          icon={<Package size={19} />}
          title={`Lô hàng đang liên kết (${playbook.linkedShipments.length})`}
          sub={`Chỉ hiển thị các lô có customerId = ${c.id}. Trạng thái từng lô lấy trực tiếp từ hành trình và việc chính hiện tại.`}
        />

        {playbook.linkedShipments.length === 0 ? (
          <div
            className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-[13.5px] text-slate-600"
            data-testid="playbook-shipments-empty"
          >
            Chưa có lô hàng nào được liên kết chính xác với mã khách hàng {c.id}. Các lô chỉ trùng tên khách hoặc MST nhưng chưa gắn mã khách hàng sẽ không tự động gán vào đây.
          </div>
        ) : (
          <div className="space-y-2.5">
            {playbook.linkedShipments.map((row) => (
              <article
                key={row.id}
                className="rounded-xl border border-slate-200 bg-slate-50/50 p-3.5"
                data-testid="playbook-shipment-row"
                data-shipment-id={row.id}
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2 min-w-0">
                    <Link
                      to={row.openHref}
                      className="text-[15.5px] font-extrabold text-[#1e5aa8] hover:underline break-all"
                    >
                      {row.id}
                    </Link>
                    <ToneBadge tone={row.statusTone} size="sm">
                      {row.status}
                    </ToneBadge>
                    {row.route && row.route !== "—" && (
                      <span className="text-[12.5px] text-slate-500 break-words">
                        {row.route}
                      </span>
                    )}
                  </div>
                  <Link
                    to={row.openHref}
                    data-testid="playbook-shipment-open"
                    className="btn-press touch-target inline-flex min-h-[40px] shrink-0 items-center gap-1.5 rounded-lg border-2 border-slate-200 bg-white px-3 text-[13px] font-bold text-[#0f2a4a] hover:border-[#1e5aa8]"
                  >
                    Mở lô <ArrowRight size={14} />
                  </Link>
                </div>

                <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2 text-[13px]">
                  <div
                    className="rounded-lg border border-slate-200 bg-white px-3 py-2"
                    data-testid="playbook-shipment-journey"
                  >
                    <span className="inline-flex items-center gap-1 text-[11.5px] font-bold text-slate-500">
                      <MapPin size={13} aria-hidden="true" /> Vị trí hành trình hiện tại
                    </span>
                    <p className="mt-0.5 font-semibold text-slate-800 break-words">
                      {row.journeyPosition
                        ? row.journeyPosition
                        : row.journeyPositionNote}
                    </p>
                    {row.unknownModuleCount > 0 && (
                      <p className="mt-1 text-[12px] font-semibold text-slate-700">
                        Quy trình chưa xác định (UNKNOWN): {row.unknownModuleCount}
                      </p>
                    )}
                  </div>

                  <div
                    className="rounded-lg border border-slate-200 bg-white px-3 py-2"
                    data-testid="playbook-shipment-primary-action"
                  >
                    <span className="block text-[11.5px] font-bold text-slate-500">
                      Việc chính hiện tại
                    </span>
                    {row.primaryAction ? (
                      <div className="mt-0.5">
                        <Link
                          to={row.primaryActionRoute}
                          className="font-bold text-[#0f2a4a] hover:text-[#1e5aa8] hover:underline break-words"
                        >
                          {row.primaryAction}
                        </Link>
                        {row.primaryActionDetail && (
                          <p className="mt-0.5 text-[12px] text-slate-500 break-words">
                            {row.primaryActionDetail}
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="mt-0.5 text-slate-500">Chưa ghi nhận việc chính</p>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* BLOCK 4: CURRENT OPERATIONAL CONCENTRATION */}
      <section
        className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5"
        data-testid="playbook-concentration"
      >
        <SectionTitle
          icon={<Layers3 size={19} />}
          title="Tập trung vận hành hiện tại"
          sub="Nhóm thực tế theo quy trình phát sinh (Work Modules) và cổng đang bị chặn trên các lô liên kết. Chỉ mô tả số lượng hiện có — không đánh giá mức độ hay suy diễn cấu hình mặc định."
        />

        {!playbook.concentration.hasConcentrationFacts ? (
          <div
            className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-[13.5px] text-slate-600"
            data-testid="playbook-concentration-empty"
          >
            {playbook.concentration.emptyText}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <div
              className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5"
              data-testid="playbook-concentration-modules"
            >
              <h3 className="text-[13.5px] font-extrabold text-[#0f2a4a]">
                Quy trình phát sinh đang gắn ({playbook.concentration.modules.length})
              </h3>
              {playbook.concentration.modules.length === 0 ? (
                <p className="mt-2 text-[12.5px] text-slate-500">
                  Chưa có quy trình phát sinh nào trên các lô liên kết.
                </p>
              ) : (
                <div className="mt-2 space-y-2">
                  {playbook.concentration.modules.map((m) => (
                    <div
                      key={m.key}
                      className="rounded-lg border border-slate-200 bg-white p-3"
                      data-testid="playbook-module-group"
                      data-module-template={m.templateId}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="min-w-0">
                          <b className="block break-words text-[13.5px] text-[#0f2a4a]">
                            {m.label}
                          </b>
                          {m.templateId !== m.label && (
                            <span className="text-[11.5px] font-mono text-slate-500">
                              {m.templateId}
                            </span>
                          )}
                        </div>
                        <span className="shrink-0 rounded-lg bg-slate-100 px-2 py-1 text-[12px] font-extrabold text-[#1e5aa8]">
                          {m.shipmentCount} lô · {m.instanceCount} lần gắn
                        </span>
                      </div>
                      <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-slate-600">
                        <span>Đang chặn: <b>{m.blockingCount}</b></span>
                        <span>Đang chờ: <b>{m.waitingCount}</b></span>
                        <span>Hoàn thành: <b>{m.doneCount}</b></span>
                        {m.unknownCount > 0 && (
                          <span
                            className="font-bold text-slate-800"
                            data-testid="playbook-module-unknown-count"
                          >
                            UNKNOWN (Chưa xác định): {m.unknownCount}
                          </span>
                        )}
                      </div>
                      {m.blockedGates.length > 0 && (
                        <p className="mt-1 text-[12px] text-red-700 font-semibold">
                          Cổng đang bị chặn: {m.blockedGates.join(", ")}
                        </p>
                      )}
                      <p className="mt-1 text-[11.5px] text-slate-500 break-words">
                        Lô liên kết: {m.shipmentIds.join(", ")}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div
              className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5"
              data-testid="playbook-concentration-gates"
            >
              <h3 className="text-[13.5px] font-extrabold text-[#0f2a4a]">
                Cổng đang bị chặn ({playbook.concentration.gates.length})
              </h3>
              {playbook.concentration.gates.length === 0 ? (
                <p className="mt-2 text-[12.5px] text-slate-500">
                  Chưa có cổng nào đang bị chặn theo dữ liệu chuẩn hiện tại.
                </p>
              ) : (
                <div className="mt-2 space-y-2">
                  {playbook.concentration.gates.map((g) => (
                    <div
                      key={g.key}
                      className="rounded-lg border border-slate-200 bg-white p-3"
                      data-testid="playbook-gate-group"
                      data-gate-key={g.key}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <b className="break-words text-[13.5px] text-red-800">
                          {g.label}
                        </b>
                        <span className="shrink-0 rounded-lg bg-red-50 border border-red-200 px-2 py-1 text-[12px] font-extrabold text-red-800">
                          {g.shipmentCount} lô · {g.count} mục chặn
                        </span>
                      </div>
                      {g.moduleNames.length > 0 && (
                        <p className="mt-1 text-[12px] text-slate-600 break-words">
                          Quy trình: <b>{g.moduleNames.join(", ")}</b>
                        </p>
                      )}
                      <p className="mt-1 text-[11.5px] text-slate-500 break-words">
                        Lô bị chặn: {g.shipmentIds.join(", ")}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
