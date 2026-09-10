// Bounded "chưa triển khai" state for the remaining Phase C destinations.
// The donor shell/navigation stays identical; only these screens are deferred.
// Phase B already wired the operational core (Tổng Quan, Việc Cần Xử Lý,
// Lô Hàng, Chi tiết lô, Tạo Lô Mới, Theo Dõi) to the real Logistics backend.

import { Link, useLocation } from "react-router-dom";
import { Construction, ArrowRight } from "lucide-react";

const PATH_NAMES: Record<string, string> = {
  "/khach-hang": "Khách Hàng",
  "/ngu-canh-doi-tac": "Ngữ cảnh Đối tác",
  "/kinh-doanh-bao-gia": "Kinh doanh · Báo giá",
  "/thoa-thuan-ban-giao": "Thòa thuận mua bán",
  "/hop-dong": "Hợp đồng",
  "/hop-dong/moi": "Tạo hợp đồng mới",
  "/tai-chinh/thu-tien": "Thu tiền",
  "/tai-chinh/doi-soat": "Đối soát",
  "/tai-chinh/cong-no-doi-tac": "Công nợ đối tác",
  "/bao-cao-ceo": "Báo cáo CEO",
  "/tra-cuu-thue": "Tra cứu thuế / HS",
  "/so-tay": "Sổ tay",
  "/dich-thuat": "Dịch thuật",
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
        <p className="text-[14.5px] text-slate-500 mt-2 leading-relaxed">
          Màn hình này chưa triển khai. Phần vận hành cốt lõi — Tổng Quan,
          Việc Cần Xử Lý, Lô Hàng, Chi tiết lô hàng, Tạo Lô Mới và Theo Dõi —
          đã chạy trên dữ liệu Logistics thật.
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
