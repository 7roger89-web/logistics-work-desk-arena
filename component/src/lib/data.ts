// ============================================================================
// Donor contract `lib/data` — reconstructed for the component runtime.
//
// The donor reference snapshot does not ship lib/data; per the recovery spec
// the missing supporting contract is provided here:
//   * NAV / ROLE_LABEL — static UI structure, identical to the donor shell.
//   * SHIPMENTS / CONTRACTS / CUSTOMERS / QUOTES / TASKS / NOTIFS — live
//     arrays fed by the Python view-model (sandbox seed in Phase A) via
//     `applyViewModel`. The same array references are kept stable and are
//     mutated in place so donor pages keep reading them exactly as designed.
// ============================================================================

import { applyViewModel, getViewModel, subscribeViewModel } from "./viewmodel";
import type {
  Agreement,
  AuthorityParty,
  Contract,
  Customer,
  Notif,
  Quote,
  Role,
  Shipment,
  Task,
} from "./viewmodel";

export type { Role } from "./viewmodel";

export const ROLE_LABEL: Record<Role, string> = {
  ADMIN: "Quản trị",
  SUPPORT: "Điều phối",
  SALE: "Kinh doanh",
};

export const NAV: {
  group: string;
  // `soon` marks a destination that has no authoritative component capability
  // yet: it renders the explicit deferred placeholder, never a faked page.
  items: { to: string; label: string; icon: string; soon?: boolean }[];
}[] = [
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — Owner UAT simplification for the small
  // Sale/Support team: "Việc Cần Xử Lý", "Theo Dõi Vận Chuyển" and
  // "Thỏa thuận mua bán" left the normal navigation (their routes stay as
  // compatibility redirects in App.tsx; no backend data was touched).
  {
    group: "VẬN HÀNH",
    items: [
      { to: "/", label: "Tổng Quan Công Việc", icon: "layout" },
      { to: "/lo-hang", label: "Lô Hàng", icon: "box" },
      { to: "/tao-lo-moi", label: "Tạo Lô Mới", icon: "plus" },
    ],
  },
  {
    group: "KINH DOANH & ĐỐI TÁC",
    items: [
      { to: "/khach-hang", label: "Khách Hàng", icon: "users" },
      // LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — visible label renamed
      // to the agent master workspace; the route itself stays /ngu-canh-doi-tac.
      { to: "/ngu-canh-doi-tac", label: "Đại Lý Trường Thành", icon: "handshake" },
      { to: "/kinh-doanh-bao-gia", label: "Báo Giá", icon: "calc" },
      { to: "/hop-dong", label: "Hợp đồng", icon: "filetext" },
    ],
  },
  {
    group: "TÀI CHÍNH & ĐỐI SOÁT",
    items: [
      { to: "/tai-chinh/thu-tien", label: "Thu tiền", icon: "wallet" },
      { to: "/tai-chinh/doi-soat", label: "Đối soát", icon: "scale" },
      { to: "/tai-chinh/cong-no-doi-tac", label: "Công nợ đối tác", icon: "building" },
      { to: "/bao-cao-ceo", label: "Báo cáo CEO", icon: "chart" },
    ],
  },
  {
    group: "CÔNG CỤ",
    items: [
      { to: "/tra-cuu-thue", label: "BIỂU THUẾ", icon: "search" },
      { to: "/tra-cuu-chinh-sach", label: "Tra cứu chính sách", icon: "book" },
      { to: "/so-tay", label: "Sổ tay", icon: "book" },
      { to: "/dich-thuat", label: "Dịch thuật", icon: "lang" },
      // LOGI_INTL_PAYMENT_STANDALONE_TOOL_01 — standalone calculator (moved
      // out of the contract detail tabs; no contract coupling, no writes).
      { to: "/thanh-toan-quoc-te", label: "Thanh toán quốc tế", icon: "banknote" },
    ],
  },
  {
    group: "QUẢN TRỊ",
    // LOGI_USER_ACCESS_WORKSPACE_01 — /nguoi-dung is a real read-only
    // user/access workspace now, so the deferred marker goes. It remains the
    // only route in this group; no second user-admin route was added.
    items: [
      { to: "/nguoi-dung", label: "Người dùng & Vai trò", icon: "shield" },
      // Issue #162 — the Work Module template library (list/version/activate/retire).
      { to: "/quy-trinh", label: "Thư viện quy trình", icon: "layers" },
    ],
  },
];

// ----------------------------------------------------------------------------
// Live arrays (stable references, refreshed in place from the view-model).
// ----------------------------------------------------------------------------

const live = {
  shipments: [] as Shipment[],
  contracts: [] as Contract[],
  customers: [] as Customer[],
  quotes: [] as Quote[],
  tasks: [] as Task[],
  notifs: [] as Notif[],
};

function refill<T>(target: T[], items: T[] | undefined): void {
  target.length = 0;
  if (Array.isArray(items)) target.push(...items);
}

// Keep the live arrays in sync whenever Python delivers a new view-model.
subscribeViewModel(() => {
  const vm = getViewModel();
  if (!vm) return;
  refill(live.shipments, vm.shipments);
  refill(live.contracts, vm.contracts);
  refill(live.customers, vm.customers);
  refill(live.quotes, vm.quotes);
  refill(live.tasks, vm.tasks);
  refill(live.notifs, vm.notifications);
});

// Eager sync (no-op until the first view-model arrives).
{
  const vm = getViewModel();
  if (vm) {
    refill(live.shipments, vm.shipments);
    refill(live.contracts, vm.contracts);
    refill(live.customers, vm.customers);
    refill(live.quotes, vm.quotes);
    refill(live.tasks, vm.tasks);
    refill(live.notifs, vm.notifications);
  }
}

export const SHIPMENTS: Shipment[] = live.shipments;
export const CONTRACTS: Contract[] = live.contracts;
export const CUSTOMERS: Customer[] = live.customers;
export const QUOTES: Quote[] = live.quotes;
export const TASKS: Task[] = live.tasks;
export const NOTIFS: Notif[] = live.notifs;

// Re-exported for tooling/tests that need to force-feed a view-model.
export const __applyViewModelForTests = applyViewModel;
