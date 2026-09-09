import type { ShipmentStatus, DocStatus, QuoteStatus, AgreementStatus, ContractStatus } from './types';

export const SHIPMENT_STATUS_LABEL: Record<ShipmentStatus, string> = {
  CHO_LAY_HANG: 'Chờ lấy hàng',
  DANG_VAN_CHUYEN: 'Đang vận chuyển',
  CHO_THONG_QUAN: 'Chờ thông quan',
  CHO_GIAO: 'Chờ giao',
  DA_GIAO: 'Đã giao',
};

export const SHIPMENT_STATUS_VARIANT: Record<ShipmentStatus, 'info' | 'warning' | 'success' | 'neutral'> = {
  CHO_LAY_HANG: 'neutral',
  DANG_VAN_CHUYEN: 'info',
  CHO_THONG_QUAN: 'warning',
  CHO_GIAO: 'warning',
  DA_GIAO: 'success',
};

export const DOC_STATUS_LABEL: Record<DocStatus, string> = {
  DU: 'Đủ',
  THIEU: 'Thiếu',
  CHAN: 'Bị chặn',
};

export const DOC_STATUS_VARIANT: Record<DocStatus, 'success' | 'warning' | 'danger'> = {
  DU: 'success',
  THIEU: 'warning',
  CHAN: 'danger',
};

export const QUOTE_STATUS_LABEL: Record<QuoteStatus, string> = {
  DRAFT: 'Nháp',
  SENT: 'Đã gửi khách',
  ACCEPTED: 'Khách đã chốt',
  REJECTED: 'Khách từ chối',
};

export const QUOTE_STATUS_VARIANT: Record<QuoteStatus, 'neutral' | 'info' | 'success' | 'danger'> = {
  DRAFT: 'neutral',
  SENT: 'info',
  ACCEPTED: 'success',
  REJECTED: 'danger',
};

export const AGREEMENT_STATUS_LABEL: Record<AgreementStatus, string> = {
  DRAFT: 'Nháp',
  REVIEWING: 'Đang xem xét',
  AGREED: 'Đã thống nhất',
  REVISED: 'Đã điều chỉnh',
  VOID: 'Đã huỷ',
};

export const AGREEMENT_STATUS_VARIANT: Record<AgreementStatus, 'neutral' | 'info' | 'success' | 'warning' | 'danger'> = {
  DRAFT: 'neutral',
  REVIEWING: 'info',
  AGREED: 'success',
  REVISED: 'warning',
  VOID: 'danger',
};

export const CONTRACT_STATUS_LABEL: Record<ContractStatus, string> = {
  DRAFT: 'Nháp',
  DA_PHAT_HANH: 'Đã phát hành',
  HET_HIEU_LUC: 'Hết hiệu lực',
};

export const CONTRACT_STATUS_VARIANT: Record<ContractStatus, 'neutral' | 'success' | 'danger'> = {
  DRAFT: 'neutral',
  DA_PHAT_HANH: 'success',
  HET_HIEU_LUC: 'danger',
};

export const PRIORITY_LABEL: Record<string, string> = {
  KHAN: 'Khẩn',
  CAN_XU_LY: 'Cần xử lý',
  BINH_THUONG: 'Bình thường',
};

export const PRIORITY_VARIANT: Record<string, 'danger' | 'warning' | 'neutral'> = {
  KHAN: 'danger',
  CAN_XU_LY: 'warning',
  BINH_THUONG: 'neutral',
};
