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
  {
    group: "VẬN HÀNH",
    items: [
      { to: "/", label: "Tổng Quan Công Việc", icon: "layout" },
      { to: "/viec-can-xu-ly", label: "Việc Cần Xử Lý", icon: "alarm" },
      { to: "/lo-hang", label: "Lô Hàng", icon: "box" },
      { to: "/tao-lo-moi", label: "Tạo Lô Mới", icon: "plus" },
      { to: "/theo-doi", label: "Theo Dõi Vận Chuyển", icon: "truck" },
    ],
  },
  {
    group: "KINH DOANH & ĐỐI TÁC",
    items: [
      { to: "/khach-hang", label: "Khách Hàng", icon: "users" },
      { to: "/ngu-canh-doi-tac", soon: true, label: "Ngữ cảnh Đối tác", icon: "handshake" },
      { to: "/kinh-doanh-bao-gia", label: "Kinh doanh · Báo giá", icon: "calc" },
      { to: "/thoa-thuan-ban-giao", label: "Thỏa thuận mua bán", icon: "filecheck" },
      { to: "/hop-dong", label: "Hợp đồng", icon: "filetext" },
    ],
  },
  {
    group: "TÀI CHÍNH & ĐỐI SOÁT",
    items: [
      { to: "/tai-chinh/thu-tien", label: "Thu tiền", icon: "wallet" },
      { to: "/tai-chinh/doi-soat", soon: true, label: "Đối soát", icon: "scale" },
      { to: "/tai-chinh/cong-no-doi-tac", label: "Công nợ đối tác", icon: "building" },
      { to: "/bao-cao-ceo", soon: true, label: "Báo cáo CEO", icon: "chart" },
    ],
  },
  {
    group: "CÔNG CỤ",
    items: [
      { to: "/tra-cuu-thue", soon: true, label: "Tra cứu thuế / HS", icon: "search" },
      { to: "/so-tay", soon: true, label: "Sổ tay", icon: "book" },
      { to: "/dich-thuat", soon: true, label: "Dịch thuật", icon: "lang" },
    ],
  },
  {
    group: "QUẢN TRỊ",
    items: [{ to: "/nguoi-dung", soon: true, label: "Người dùng & Vai trò", icon: "shield" }],
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
