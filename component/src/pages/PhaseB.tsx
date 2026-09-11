// Explicit deferred state for the destinations that do NOT yet have an
// authoritative component capability. The donor shell/navigation stays
// identical; these screens are honestly marked "Sắp có" in the sidebar and
// are never faked with mock business data. Every other destination in the
// shell already runs on the real Logistics backend:
//   Tổng Quan, Việc Cần Xử Lý, Lô Hàng, Chi tiết lô, Tạo Lô Mới, Theo Dõi,
//   Khách Hàng, Kinh doanh · Báo giá, Thỏa thuận mua bán, Hợp đồng,
//   Thu tiền (phải thu), Công nợ đối tác (phải trả), Tra cứu thuế / HS,
//   Dịch thuật, Ngữ cảnh Đối tác.

import { Link, useLocation } from "react-router-dom";
import { Construction, ArrowRight } from "lucide-react";

const PATH_NAMES: Record<string, string> = {
  "/tai-chinh/doi-soat": "Đối soát",
  "/bao-cao-ceo": "Báo cáo CEO",
  "/so-tay": "Sổ tay",
  "/nguoi-dung": "Người dùng & Vai trò",
};

export function PhaseBPlaceholder() {
  const { pathname } = useLocation();
  const name = PATH_NAMES[pathname] ?? "Màn hình phụ";
  return (
    <div className="max-w-[680px] mx-auto mt-8">
      <div className="rounded-3xl bg-white border border-slate-200 p-8 text-center anim-slide-up">
        <span className="mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center">
          <Construction size={26} />
        </span>
        <h2 className="text-[20px] font-extrabold text-[#0f2a4a] mt-4">{name}</h2>
        <p className="text-[13px] font-extrabold uppercase tracking-wide text-amber-700 mt-2">
          Sắp có — chưa triển khai
        </p>
        <p className="text-[14.5px] text-slate-500 mt-2 leading-relaxed">
          Màn hình này chưa có nguồn dữ liệu nghiệp vụ chuẩn trong phiên bản
          hiện tại nên chưa được dựng — hệ thống không hiển thị dữ liệu mẫu
          thay thế. Toàn bộ phần vận hành, kinh doanh và tài chính cốt lõi —
          Tổng Quan, Việc Cần Xử Lý, Lô Hàng, Chi tiết lô, Tạo Lô Mới, Theo Dõi,
          Khách Hàng, Báo giá, Thỏa thuận, Hợp đồng, Thu tiền và Công nợ đối
          tác — đã chạy trên dữ liệu Logistics thật.
        </p>
        <div className="flex flex-wrap justify-center gap-2.5 mt-5">
          <Link
            to="/"
            className="btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-5 min-h-[48px]"
          >
            Về Tổng Quan <ArrowRight size={17} />
          </Link>
          <Link
            to="/lo-hang"
            className="btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-5 min-h-[48px]"
          >
            Xem Lô Hàng
          </Link>
        </div>
      </div>
    </div>
  );
}
