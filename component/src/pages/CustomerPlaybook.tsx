import { useEffect, useMemo, useRef, useSyncExternalStore } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, Layers3, Users } from "lucide-react";
import AttentionNow from "../components/AttentionNow";
import { ToneBadge } from "../components/ui";
import { composeCustomerPlaybook } from "../lib/customerPlaybook";
import { fmtNum, fmtText } from "../lib/format";
import { shipmentPath } from "../lib/shipmentRoute";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import type { Shipment } from "../lib/viewmodel";

function journeyPosition(shipment: Shipment): string {
  const journey = shipment.journey;
  if (!journey) return "";
  const current = journey.nodes.find((node) => node.current)
    ?? journey.nodes.find((node) => node.id === journey.currentStageId);
  if (current?.label) return current.label;
  if (journey.currentStageId) return journey.currentStageId;
  return journey.positionNote?.trim() ? journey.positionNote : "";
}

function primaryAction(shipment: Shipment) {
  const journeyAction = shipment.journey?.primaryAction;
  const label = journeyAction?.text || shipment.nextAction || shipment.nextLabel || "";
  if (!label) return null;
  return {
    label,
    detail: journeyAction?.detail || shipment.nextActionDetail || "",
    route: journeyAction?.route || shipment.nextRoute || "",
  };
}

export default function CustomerPlaybook() {
  const { id = "" } = useParams();
  const pageRef = useRef<HTMLDivElement>(null);
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const customer = vm?.customers.find((row) => row.id === id);
  const playbook = useMemo(
    () => customer && vm
      ? composeCustomerPlaybook(customer, vm.shipments, vm.attention ?? [])
      : null,
    [customer, vm],
  );
  const attentionAvailable = Array.isArray(vm?.attention);

  useEffect(() => {
    pageRef.current?.scrollIntoView?.({ block: "start" });
  }, [id]);

  if (!customer || !playbook) {
    return (
      <section className="w-full max-w-[760px] min-w-0 rounded-2xl border border-slate-200 bg-white p-5 md:p-6" data-testid="customer-playbook-not-found">
        <h1 className="text-balance text-[19px] font-extrabold text-[#0f2a4a]">Không tìm thấy khách hàng</h1>
        <p className="mt-1 text-pretty text-sm text-slate-600">Mã khách hàng trên đường dẫn không có trong danh sách hiện tại.</p>
        <Link to="/khach-hang" className="touch-target mt-4 inline-flex items-center gap-2 rounded-lg bg-[#0f2a4a] px-4 font-bold text-white">
          Về danh sách khách hàng <ArrowRight size={16} aria-hidden="true" />
        </Link>
      </section>
    );
  }

  const hasOperatingNote = Boolean(customer.note?.trim());
  const customerMasterLink = `/khach-hang?q=${encodeURIComponent(customer.id)}`;

  return (
    <div ref={pageRef} className="w-full max-w-[1100px] min-w-0 space-y-4 scroll-mt-16" data-testid="customer-playbook" data-customer-id={customer.id}>
      {/* 1. Existing customer master facts + its one V1 operating note. */}
      <section className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="customer-playbook-identity" aria-labelledby="customer-playbook-title">
        <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#0f2a4a] text-white" aria-hidden="true"><Users size={19} /></span>
            <div className="min-w-0">
              <p className="text-[11px] font-extrabold text-slate-500">HỒ SƠ KHÁCH HÀNG</p>
              <h1 id="customer-playbook-title" className="mt-0.5 break-words text-balance text-[20px] font-extrabold leading-tight text-[#0f2a4a] md:text-[23px]">{customer.name}</h1>
              <p className="mt-1 break-all text-[13px] font-semibold text-slate-600">Mã khách hàng · {customer.id}</p>
            </div>
          </div>
          <Link
            to={customerMasterLink}
            data-testid="customer-playbook-master-link"
            className="touch-target inline-flex w-full shrink-0 items-center justify-center gap-1.5 rounded-lg border border-slate-300 px-3 text-center text-[13px] font-bold text-[#0f2a4a] hover:bg-slate-50 sm:w-auto"
          >
            Mở danh sách để sửa <ArrowRight size={15} aria-hidden="true" />
          </Link>
        </div>

        <dl className="mt-4 grid min-w-0 grid-cols-1 gap-x-5 gap-y-3 border-t border-slate-100 pt-4 sm:grid-cols-2">
          {[
            { label: "Mã số thuế", value: fmtText(customer.taxCode) },
            { label: "Người liên hệ", value: fmtText(customer.contactPerson) },
            { label: "Điện thoại", value: fmtText(customer.phone) },
            { label: "Email", value: fmtText(customer.email), breakAll: true },
            { label: "Địa chỉ", value: fmtText(customer.address) },
          ].map((fact) => (
            <div key={fact.label} className="min-w-0">
              <dt className="text-[11px] font-bold text-slate-500">{fact.label}</dt>
              <dd className={`mt-0.5 text-[13.5px] font-semibold text-slate-800 ${fact.breakAll ? "break-all" : "break-words"}`}>{fact.value}</dd>
            </div>
          ))}
        </dl>

        <div className="mt-4 min-w-0 rounded-xl border border-slate-200 bg-slate-50 p-3" data-testid="customer-operating-note" data-note-empty={!hasOperatingNote}>
          <h2 className="text-[13px] font-extrabold text-[#0f2a4a]">Ghi chú vận hành</h2>
          {hasOperatingNote
            ? <p className="mt-1 break-words whitespace-pre-wrap text-[13.5px] text-slate-700">{customer.note}</p>
            : <p className="mt-1 text-[13.5px] text-slate-500">Chưa ghi nhận ghi chú vận hành.</p>}
        </div>
      </section>

      {/* 2. The shared Attention projection/component, filtered by exact-linked shipment IDs. */}
      <div className="min-w-0" data-testid="customer-playbook-attention" data-attention-source-available={attentionAvailable}>
        <AttentionNow
          items={playbook.attention}
          title="Customer Attention"
          emptyText={attentionAvailable
            ? "Chưa có mục Attention liên kết được ghi nhận cho các lô gắn đúng mã khách hàng."
            : "Chưa nhận được dữ liệu Attention từ projection hiện tại."}
        />
        {playbook.attentionTotalCount > playbook.attention.length && (
          <p className="px-1 pt-1 text-[12px] text-slate-500" data-testid="customer-attention-truncated">
            Đang hiển thị {playbook.attention.length} mục đầu theo thứ tự Attention hiện có; còn {fmtNum(playbook.attentionTotalCount - playbook.attention.length)} mục.
          </p>
        )}
      </div>

      {/* 3. All current ViewModel shipments with exact customerId linkage. */}
      <section className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="customer-linked-shipments" aria-labelledby="customer-linked-shipments-title">
        <div className="flex min-w-0 flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
          <h2 id="customer-linked-shipments-title" className="text-balance text-[16px] font-extrabold text-[#0f2a4a]">Lô hàng liên kết hiện có</h2>
          <span className="shrink-0 text-[12px] font-bold text-slate-500">{fmtNum(playbook.linkedShipments.length)} lô</span>
        </div>
        <p className="mt-1 text-pretty text-[12px] text-slate-500">Chỉ hiển thị lô có customerId khớp chính xác với mã khách hàng này.</p>

        {playbook.linkedShipments.length === 0 ? (
          <p className="mt-3 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-3 text-[13px] text-slate-600" data-testid="customer-linked-shipments-empty">
            Chưa có lô hàng nào được gắn đúng mã khách hàng trong dữ liệu hiện tại.
          </p>
        ) : (
          <ul className="mt-3 grid min-w-0 grid-cols-1 gap-2.5">
            {playbook.linkedShipments.map((shipment) => {
              const position = journeyPosition(shipment);
              const action = primaryAction(shipment);
              return (
                <li
                  key={shipment.id}
                  className="min-w-0 rounded-xl border border-slate-200 bg-white p-3"
                  data-testid="customer-playbook-shipment"
                  data-shipment-id={shipment.id}
                >
                  <div className="flex min-w-0 flex-wrap items-center gap-2">
                    <Link to={shipmentPath(shipment.id)} className="touch-target min-w-0 break-all font-extrabold text-[14px] text-[#1e5aa8] underline-offset-2 hover:underline" data-testid="customer-playbook-shipment-link">
                      {shipment.id}
                    </Link>
                    <ToneBadge tone={shipment.statusTone} size="sm">{fmtText(shipment.status)}</ToneBadge>
                  </div>
                  <dl className="mt-2 grid min-w-0 grid-cols-1 gap-2 sm:grid-cols-2">
                    {position && (
                      <div className="min-w-0">
                        <dt className="text-[11px] font-bold text-slate-500">Vị trí Journey</dt>
                        <dd className="break-words text-[13px] font-semibold text-slate-800" data-testid="customer-playbook-journey-position">{position}</dd>
                      </div>
                    )}
                    {action && (
                      <div className="min-w-0">
                        <dt className="text-[11px] font-bold text-slate-500">Hành động chính hiện có</dt>
                        <dd className="mt-0.5 min-w-0">
                          {action.route
                            ? <Link to={action.route} className="touch-target inline-flex max-w-full items-center gap-1 break-words text-[13px] font-bold text-[#1e5aa8] underline-offset-2 hover:underline" data-testid="customer-playbook-primary-action">{action.label} <ArrowRight size={14} className="shrink-0" aria-hidden="true" /></Link>
                            : <span className="break-words text-[13px] font-semibold text-slate-800" data-testid="customer-playbook-primary-action">{action.label}</span>}
                          {action.detail && <p className="mt-0.5 break-words text-[12px] text-slate-600">{action.detail}</p>}
                        </dd>
                      </div>
                    )}
                  </dl>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* 4. Neutral counts from attached Work Module rollups and canonical blocked gates. */}
      <section className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="customer-playbook-concentration" aria-labelledby="customer-playbook-concentration-title">
        <div className="flex min-w-0 items-start gap-2.5">
          <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-slate-100 text-[#0f2a4a]" aria-hidden="true"><Layers3 size={17} /></span>
          <div className="min-w-0">
            <h2 id="customer-playbook-concentration-title" className="text-balance text-[16px] font-extrabold text-[#0f2a4a]">Tập trung vận hành hiện tại</h2>
            <p className="mt-0.5 text-pretty text-[12px] text-slate-500">Số lượng mô tả dữ liệu đang gắn; không phải đánh giá rủi ro hay điểm nghẽn.</p>
          </div>
        </div>

        {playbook.linkedShipments.length === 0 ? (
          <p className="mt-3 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-3 text-[13px] text-slate-600" data-testid="customer-concentration-empty">
            Chưa có lô liên kết chính xác để tổng hợp Work Module hoặc cổng chặn.
          </p>
        ) : (
          <div className="mt-3 grid min-w-0 grid-cols-1 gap-4 md:grid-cols-2">
            <div className="min-w-0" data-testid="customer-module-concentration">
              <h3 className="text-[13px] font-extrabold text-slate-700">Work Module đã gắn</h3>
              {playbook.moduleGroups.length === 0 ? (
                <p className="mt-1 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-2.5 text-[12.5px] text-slate-600">Chưa ghi nhận Work Module trong dữ liệu Journey hiện tại.</p>
              ) : (
                <ul className="mt-2 space-y-2">
                  {playbook.moduleGroups.map((group) => (
                    <li key={group.key} className="min-w-0 rounded-lg border border-slate-200 bg-slate-50/70 p-2.5" data-testid="customer-playbook-module-group" data-module-template={group.templateId} data-module-unknown-count={group.unknownCount}>
                      <p className="break-words text-[13px] font-bold text-[#0f2a4a]">{group.name}{group.templateVersion > 0 ? ` · V${group.templateVersion}` : ""}</p>
                      <p className="mt-0.5 text-[12px] text-slate-600">{fmtNum(group.moduleCount)} lần gắn · {fmtNum(group.shipmentCount)} lô liên kết</p>
                      {group.unknownCount > 0 && <p className="mt-0.5 break-words text-[12px] font-semibold text-slate-700" data-testid="customer-playbook-module-unknown">UNKNOWN: {fmtNum(group.unknownCount)} mục chưa xác định.</p>}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="min-w-0" data-testid="customer-blocked-gate-concentration">
              <h3 className="text-[13px] font-extrabold text-slate-700">Cổng đang bị chặn theo Work Module</h3>
              {playbook.blockedGates.length === 0 ? (
                <p className="mt-1 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-2.5 text-[12.5px] text-slate-600">Chưa có cổng chặn được ghi nhận trong rollup Work Module hiện tại.</p>
              ) : (
                <ul className="mt-2 space-y-2">
                  {playbook.blockedGates.map((group) => (
                    <li key={group.key} className="min-w-0 rounded-lg border border-slate-200 bg-slate-50/70 p-2.5" data-testid="customer-playbook-blocked-gate" data-gate-label={group.label}>
                      <p className="break-words text-[13px] font-bold text-[#0f2a4a]">{group.label}</p>
                      <p className="mt-0.5 text-[12px] text-slate-600">{fmtNum(group.moduleCount)} quy trình · {fmtNum(group.shipmentCount)} lô liên kết</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
