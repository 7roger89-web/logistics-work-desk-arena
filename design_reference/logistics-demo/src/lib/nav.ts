import {
  LayoutDashboard, ListChecks, Package, PackagePlus, Truck,
  Users, Building2, Calculator, Handshake, FileText,
  Wallet, Scale, HandCoins, BarChart3,
  Search, BookOpen, Languages, ShieldCheck,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
}
export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    title: 'VẬN HÀNH',
    items: [
      { label: 'Tổng Quan Công Việc', path: '/', icon: LayoutDashboard },
      { label: 'Việc Cần Xử Lý', path: '/viec-can-xu-ly', icon: ListChecks },
      { label: 'Lô Hàng', path: '/lo-hang', icon: Package },
      { label: 'Tạo Lô Mới', path: '/tao-lo-moi', icon: PackagePlus },
      { label: 'Theo Dõi Vận Chuyển', path: '/theo-doi-van-chuyen', icon: Truck },
    ],
  },
  {
    title: 'KINH DOANH & ĐỐI TÁC',
    items: [
      { label: 'Khách Hàng', path: '/khach-hang', icon: Users },
      { label: 'Ngữ Cảnh Đối Tác', path: '/ngu-canh-doi-tac', icon: Building2 },
      { label: 'Kinh Doanh & Báo Giá', path: '/kinh-doanh-bao-gia', icon: Calculator },
      { label: 'Thỏa Thuận & Bàn Giao', path: '/thoa-thuan-ban-giao', icon: Handshake },
      { label: 'Hợp Đồng', path: '/hop-dong', icon: FileText },
    ],
  },
  {
    title: 'TÀI CHÍNH & ĐỐI SOÁT',
    items: [
      { label: 'Thu Tiền & Công Nợ', path: '/thu-tien-cong-no', icon: Wallet },
      { label: 'Đối Soát Tài Chính', path: '/doi-soat-tai-chinh', icon: Scale },
      { label: 'Công Nợ Đối Tác', path: '/cong-no-doi-tac', icon: HandCoins },
      { label: 'Báo Cáo CEO', path: '/bao-cao-ceo', icon: BarChart3 },
    ],
  },
  {
    title: 'CÔNG CỤ',
    items: [
      { label: 'Tra Cứu Thuế/HS', path: '/tra-cuu-thue-hs', icon: Search },
      { label: 'Sổ Tay Kinh Nghiệm', path: '/so-tay-kinh-nghiem', icon: BookOpen },
      { label: 'Dịch Thuật', path: '/dich-thuat', icon: Languages },
    ],
  },
  {
    title: 'QUẢN TRỊ',
    items: [
      { label: 'Người Dùng', path: '/nguoi-dung', icon: ShieldCheck },
    ],
  },
];

export const MOBILE_NAV = [
  { label: 'Tổng quan', path: '/', icon: LayoutDashboard },
  { label: 'Lô hàng', path: '/lo-hang', icon: Package },
  { label: 'Hợp đồng', path: '/hop-dong', icon: FileText },
  { label: 'Tài chính', path: '/thu-tien-cong-no', icon: Wallet },
];
