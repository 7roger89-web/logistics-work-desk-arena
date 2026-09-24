// ============================================================================
// LOGI_INTL_PAYMENT_STANDALONE_TOOL_01 (Issue #109) — /thanh-toan-quoc-te.
//
// Thin standalone page under the sidebar group CÔNG CỤ. It needs no contract
// and no contract ID: it hands the EXISTING read-only intlFxRates projection
// (BOC / Agribank / BIDV, fail-closed) to the stateless calculator. No
// dispatch, no write, no persistence — refresh/navigation discards the inputs.
// ============================================================================

import IntlPaymentComparator from "../components/IntlPaymentComparator";
import { useStore } from "../lib/store";

export default function IntlPaymentTool() {
  const { intlFxRates } = useStore();
  return (
    <div className="space-y-4 max-w-[1300px]" data-testid="intl-payment-tool">
      <div>
        <h1 className="text-[20px] md:text-[22px] font-extrabold text-[#0f2a4a] leading-tight">Thanh toán quốc tế</h1>
        <p className="text-[13.5px] text-slate-500 mt-1">
          Công cụ tính tham khảo. Không thực hiện chuyển tiền và không lưu dữ liệu.
        </p>
      </div>
      <IntlPaymentComparator fxRates={intlFxRates} />
    </div>
  );
}
