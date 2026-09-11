// ============================================================================
// LOGI_CEO_REPORT_01 — bounded, READ-ONLY current-position management view.
//
// The backend has already assembled `ceoReport` from existing shipment/Home/
// task, C2C receivable, C2D payable and reconciliation projections. This page
// intentionally renders no forecast, target, trend, KPI score, finance writer
// or cross-currency grand total. Every monetary card stays inside one explicit
// currency block.
// ============================================================================

import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, CircleAlert, FileText, Package, Scale, Wallet } from "lucide-react";
import { SectionTitle, ToneBadge } from "../components/ui";
import { fmtCcy, fmtNum } from "../lib/format";
import { useStore } from "../lib/store";
import type { CeoCurrencyPosition } from "../lib/viewmodel";

function CurrencyPositionCard({
  position,
  kind,
}: {
  position: CeoCurrencyPosition;
  kind: "receivable" | "payable";
}) {
  const isReceivable = kind === "receivable";
  const noun = isReceivable ? "phải thu" : "phải trả";
  const amountTone = isReceivable ? "text-red-700" : "text-amber-800";
  const bgTone = isReceivable ? "bg-red-50 border-red-200" : "bg-amber-50 border-amber-200";
  const openLabel = position.incompleteRowCount > 0 ? "dòng còn mở đã xác định" : "dòng còn mở";
  const incompleteLabel = isReceivable
    ? "dòng chưa đủ Finance Actual, không tính là 0"
    : "dòng chưa đủ số dư canonical, không tính là 0";

  return (
    <div
      data-testid={`ceo-${kind}-${position.currency}`}
      data-ceo-currency={position.currency}
      className={`min-w-0 rounded-2xl border p-3.5 md:p-4 ${bgTone}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="rounded-md bg-white/80 border border-slate-200 px-2 py-0.5 text-[12px] font-extrabold tracking-wide text-[#0f2a4a]">
          {position.currency}
        </span>
        <span className="text-right text-[12px] leading-snug font-semibold text-slate-500">
          {fmtNum(position.openCount)} {openLabel}
        </span>
      </div>
      <p className="mt-3 text-[12.5px] font-bold uppercase tracking-wide text-slate-600">Còn {noun}</p>
      <p className={`mt-1 break-words text-[20px] leading-tight font-extrabold md:text-[23px] ${amountTone}`}>
        {fmtCcy(position.outstanding, position.currency)}
      </p>
      <p className="mt-2 text-[12.5px] leading-relaxed text-slate-500">
        {fmtNum(position.rowCount)} dòng nguồn đủ điều kiện · không quy đổi sang tiền tệ khác
      </p>
      {position.incompleteRowCount > 0 ? (
        <p className="mt-1 text-[12.5px] leading-relaxed font-semibold text-amber-800">
          {fmtNum(position.incompleteRowCount)} {incompleteLabel}.
        </p>
      ) : null}
    </div>
  );
}

function StateCount({ label, value, tone = "gray" }: { label: string; value: number | null | undefined; tone?: "green" | "amber" | "red" | "gray" }) {
  const classes = {
    green: "border-emerald-200 bg-emerald-50 text-emerald-800",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
    red: "border-red-200 bg-red-50 text-red-800",
    gray: "border-slate-200 bg-slate-50 text-slate-700",
  } as const;

  return (
    <div className={`min-w-0 rounded-xl border px-3 py-2.5 ${classes[tone]}`}>
      <p className="text-[11.5px] font-bold uppercase tracking-wide opacity-75">{label}</p>
      <p className="mt-0.5 text-[18px] leading-tight font-extrabold">{fmtNum(value)}</p>
    </div>
  );
}

function EmptyPosition({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600">
      {children}
    </div>
  );
}

export default function CeoReport() {
  const { ceoReport } = useStore();

  // A missing payload must not fall back to donor/sample content.
  if (!ceoReport) {
    return (
      <div className="max-w-[1000px]">
        <EmptyPosition>
          Chưa nhận được tóm tắt quản trị từ nguồn Logistics. Hệ thống không hiển thị số liệu thay thế.
        </EmptyPosition>
      </div>
    );
  }

  const { operations, receivables, payables, finance, reconciliation, quickLinks, unavailable } = ceoReport;
  const reconciliationObligations = reconciliation.obligations;
  const reconciliationMoney = reconciliation.money;
  const reconciliationReady = Boolean(
    reconciliation.available && reconciliationObligations && reconciliationMoney
  );

  return (
    <div className="max-w-[1240px] space-y-4 pb-3">
      {/* Header: current position only; no time range is inferred. */}
      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="ceo-header">
        <SectionTitle
          icon={<BarChart3 size={20} />}
          title="Báo cáo CEO"
          sub="Tóm tắt vị thế hiện tại từ dữ liệu Logistics đã có. Chỉ đọc; tiền tệ luôn tách riêng."
          right={<ToneBadge tone="blue" size="sm">CHỈ ĐỌC</ToneBadge>}
        />
        <div className="rounded-xl border border-blue-100 bg-blue-50 px-3.5 py-2.5 text-[13.5px] leading-relaxed text-blue-900">
          Dùng để nhìn nhanh vận hành, phải thu, phải trả và đối soát. Không có biểu đồ xu hướng hay số liệu ước tính.
        </div>
      </section>

      {/* Operations: existing Home + task-projection semantics only. */}
      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="ceo-operations">
        <SectionTitle
          icon={<Package size={20} />}
          title="Vận hành"
          sub="Đếm từ danh sách lô hiện tại và hàng đợi việc hiện có."
        />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" data-testid="ceo-operations-cards">
          <div className="min-w-0 rounded-2xl border border-slate-200 bg-slate-50 p-3.5">
            <p className="text-[12px] font-bold uppercase tracking-wide text-slate-500">Tổng lô hàng</p>
            <p className="mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]">{fmtNum(operations.totalShipmentCount)}</p>
            <p className="mt-1 text-[12.5px] text-slate-500">Danh sách lô hiện tại</p>
          </div>
          <div className="min-w-0 rounded-2xl border border-blue-200 bg-blue-50 p-3.5">
            <p className="text-[12px] font-bold uppercase tracking-wide text-blue-700">Lô đang chạy</p>
            <p className="mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]">{fmtNum(operations.openShipmentCount)}</p>
            <p className="mt-1 text-[12.5px] text-blue-800">Theo định nghĩa Tổng quan</p>
          </div>
          <div className="min-w-0 rounded-2xl border border-amber-200 bg-amber-50 p-3.5">
            <p className="text-[12px] font-bold uppercase tracking-wide text-amber-800">Việc ưu tiên</p>
            <p className="mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]">{fmtNum(operations.actionableTaskCount)}</p>
            <p className="mt-1 text-[12.5px] text-amber-900">Khẩn + Cần xử lý</p>
          </div>
        </div>
        {operations.statusCounts.length > 0 ? (
          <div className="mt-4">
            <p className="text-[12px] font-bold uppercase tracking-wide text-slate-500">Trạng thái lô hiện tại</p>
            <div className="mt-2 flex flex-wrap gap-2" data-testid="ceo-status-counts">
              {operations.statusCounts.map((item) => (
                <span key={item.status} className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[13px] font-semibold text-slate-700">
                  <span className="truncate">{item.status}</span>
                  <b className="text-[#0f2a4a]">{fmtNum(item.count)}</b>
                </span>
              ))}
            </div>
          </div>
        ) : (
          <p className="mt-4 text-[14px] text-slate-500">Chưa có lô hàng trong dữ liệu hiện tại.</p>
        )}
      </section>

      {/* Receivables and payables deliberately have separate currency card groups. */}
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="ceo-receivables">
          <SectionTitle
            icon={<Wallet size={20} className="text-emerald-600" />}
            title="Phải thu khách"
            sub="C2C · chỉ tổng từ lô đã có Finance Actual."
          />
          {receivables.positions.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2" data-testid="ceo-receivable-currency-grid">
              {receivables.positions.map((position) => (
                <CurrencyPositionCard key={position.currency} position={position} kind="receivable" />
              ))}
            </div>
          ) : (
            <EmptyPosition>
              Chưa có tổng phải thu đủ điều kiện từ Finance Actual. Đây là trạng thái <b>chưa xác định</b>, không phải 0.
            </EmptyPosition>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="ceo-payables">
          <SectionTitle
            icon={<FileText size={20} className="text-amber-700" />}
            title="Phải trả đối tác"
            sub="C2D · nghĩa vụ và phân bổ từ ledger canonical."
          />
          {payables.error ? (
            <EmptyPosition>
              Chưa đọc được ledger phải trả canonical: {payables.error}. Hệ thống không hiển thị số 0 thay thế.
            </EmptyPosition>
          ) : !payables.hasCanonicalRecords ? (
            <EmptyPosition>
              Chưa có bản ghi nghĩa vụ hoặc thanh toán canonical. Đây là trạng thái <b>chưa có dữ liệu</b>, không phải phải trả bằng 0.
            </EmptyPosition>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2" data-testid="ceo-payable-currency-grid">
              {payables.positions.map((position) => (
                <CurrencyPositionCard key={position.currency} position={position} kind="payable" />
              ))}
            </div>
          )}
          {payables.status === "REVIEW_REQUIRED" ? (
            <p className="mt-3 inline-flex rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] font-semibold text-amber-900">
              Có bản ghi phải trả cần rà soát trong desk đối soát.
            </p>
          ) : null}
        </section>
      </div>

      {/* Missing finance is evidence, not a zero. Profit/margin are intentionally omitted. */}
      <section
        className="rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50/70 p-4 md:p-5"
        data-testid="ceo-finance-visibility"
      >
        <div className="flex items-start gap-3">
          <CircleAlert size={21} className="mt-0.5 shrink-0 text-amber-700" />
          <div className="min-w-0">
            <h3 className="text-[15px] font-extrabold text-amber-950">Khả năng nhìn thấy tài chính</h3>
            {finance.incompleteShipmentCount > 0 ? (
              <p className="mt-1 text-[13.5px] leading-relaxed text-amber-900">
                {fmtNum(finance.incompleteShipmentCount)} lô chưa đủ Finance Actual. Các tổng phải thu phía trên không tính các lô này và không coi dữ liệu thiếu là 0.
              </p>
            ) : (
              <p className="mt-1 text-[13.5px] leading-relaxed text-amber-900">
                Trang chỉ hiển thị các vị thế có nguồn hiện tại; không tự suy diễn thêm chỉ số tài chính.
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Reconciliation has only known count state; amounts stay on its own per-currency desk. */}
      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="ceo-reconciliation">
        <SectionTitle
          icon={<Scale size={20} className="text-violet-700" />}
          title="Đối soát"
          sub="Số dòng theo trạng thái phân bổ từ ledger canonical; không phải đối soát sao kê hay sổ kế toán."
          right={reconciliation.status === "REVIEW_REQUIRED" ? <ToneBadge tone="amber" size="sm">CẦN RÀ SOÁT</ToneBadge> : undefined}
        />
        {!reconciliation.available || !reconciliationObligations || !reconciliationMoney ? (
          <EmptyPosition>
            {reconciliation.status === "NO_SOURCE"
              ? `Chưa đọc được ledger đối soát${reconciliation.error ? `: ${reconciliation.error}` : ""}. Không hiển thị số 0 thay thế.`
              : "Chưa có bản ghi đối soát canonical. Đây là trạng thái chưa có dữ liệu, không phải công nợ bằng 0."}
          </EmptyPosition>
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5" data-testid="ceo-reconciliation-obligations">
              <p className="text-[13px] font-extrabold text-[#0f2a4a]">Nghĩa vụ</p>
              <p className="mt-0.5 text-[12.5px] text-slate-500">MATCHED / PARTIAL / UNMATCHED theo phân bổ đã có</p>
              <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
                <StateCount label="Đã đối soát" value={reconciliationObligations.MATCHED} tone="green" />
                <StateCount label="Một phần" value={reconciliationObligations.PARTIAL} tone="amber" />
                <StateCount label="Chưa đối soát" value={reconciliationObligations.UNMATCHED} tone="red" />
                <StateCount label="Chưa xác định" value={reconciliationObligations.UNKNOWN} />
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5" data-testid="ceo-reconciliation-money">
              <p className="text-[13px] font-extrabold text-[#0f2a4a]">Giao dịch tiền</p>
              <p className="mt-0.5 text-[12.5px] text-slate-500">ALLOCATED / PARTIAL / UNALLOCATED theo phân bổ đã có</p>
              <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
                <StateCount label="Đã phân bổ" value={reconciliationMoney.ALLOCATED} tone="green" />
                <StateCount label="Một phần" value={reconciliationMoney.PARTIAL} tone="amber" />
                <StateCount label="Chưa phân bổ" value={reconciliationMoney.UNALLOCATED} tone="red" />
                <StateCount label="Chưa xác định" value={reconciliationMoney.UNKNOWN} />
              </div>
            </div>
          </div>
        )}
        {reconciliationReady && reconciliation.reviewCount !== null && reconciliation.reviewCount > 0 ? (
          <p className="mt-3 inline-flex rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] font-semibold text-amber-900">
            {fmtNum(reconciliation.reviewCount)} dòng ledger cần rà soát.
          </p>
        ) : null}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5" data-testid="ceo-quick-navigation">
        <SectionTitle
          icon={<ArrowRight size={20} />}
          title="Đi nhanh tới dữ liệu gốc"
          sub="Mỗi liên kết mở desk đã sở hữu dữ liệu và hành động nghiệp vụ tương ứng."
        />
        <div className="grid gap-2.5 sm:grid-cols-2" data-testid="ceo-quick-links">
          {quickLinks.map((link) => (
            <Link
              key={link.href}
              to={link.href}
              className="btn-press touch-target flex min-h-[52px] min-w-0 items-center justify-between gap-3 rounded-xl border-2 border-slate-200 bg-white px-4 py-2.5 text-left hover:border-[#1e5aa8]"
            >
              <span className="min-w-0">
                <span className="block text-[14px] font-extrabold text-[#0f2a4a]">{link.label}</span>
                <span className="block truncate text-[12.5px] text-slate-500">{link.note}</span>
              </span>
              <ArrowRight size={18} className="shrink-0 text-[#1e5aa8]" />
            </Link>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid="ceo-scope-note">
        <p className="text-[12px] font-extrabold uppercase tracking-wide text-slate-500">Phạm vi dữ liệu</p>
        <ul className="mt-2 space-y-1.5 text-[13.5px] leading-relaxed text-slate-600">
          {unavailable.map((item) => <li key={item}>• {item}</li>)}
        </ul>
      </section>
    </div>
  );
}
