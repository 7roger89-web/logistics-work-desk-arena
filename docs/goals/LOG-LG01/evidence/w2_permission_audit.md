# LG01-T04: W2 Permission-Policy Audit

Goal: LOG-LG01. Task LG01-T04 (W2). Branch log-lg01-multi-user-internal-rc. Date: 2026-08-17.

## 1. Pham vi audit

Cau truc quyen duy nhat: ROLE_PERMISSIONS (core/auth.py) + Route guards (views/web_app.py) + content guards
has_permission/has_write_permission trong tung view. Khong co logic quyen phan tan noi khac.

## 2. Ma tran role thuc te (7 keys, trong do 4 legacy)

| Role | Trang thai | Quyen write dac biet | Ghi chu |
|---|---|---|---|
| admin | Chinh thuc | {*} toan quyen | Mot nguoi dung admin |
| sale | Chinh thuc | sales_write, commercial_write, shipment_create/edit | Khong cham finance/admin |
| support | Chinh thuc | operations_write | Read-only tren finance va admin |
| accounting | Legacy | KHONG *_write (receivables, entrustment, proxy_payment, finance_view) | Ghi doc finance |
| operations | Legacy | operations_write, shipment_create/edit | Khong cham finance/admin |
| sales | Legacy | sales_write, shipment_create/edit | Trung lap voi sale (cu) |
| viewer | Chinh thuc (fallback) | KHONG CO write | Chi read |

SUPPORTED_ROLES = (admin, sale, support): dung 3 role ky vong. 4 legacy keys giu tuong thich nguoc.
Role khong biet: has_permission fall back ve viewer (read-only).
## 3. Material write actions (delete/elevate)

| Action | Guard | Role nao duoc |
|---|---|---|
| shipment_delete | has_permission + confirm UI | chi admin ({*}); khong role non-admin co key |
| customer_delete | has_permission + ly do bat buoc | chi admin |
| knowledge_delete, proxy_payment_delete | has_permission | chi admin || user mgmt (role change/deactivate/hard-delete) | Route permission=admin + _assert_route_access | chi admin; soft-delete truoc, hard-delete ke do, _audit ca 2 buoc |
| tao admin (elevation) | user_management (chi admin) | chi admin tu da co; khong co 4-eyes |
| delete_user actor fallback admin khi username rong | route-level guard | khong dat duoc thuc te |
## 4. Khe ho anonymous (thiet ke C15, khong material cho mode da nguoi dung)

has_permission() co nhanh anonymous: username rong => permission in viewer set (dashboard, reports,
tracking, knowledge, commercial_view, finance_view). Tuy nhien main() goi require_login():
khi AUTH_REQUIRED bat (mode multi-user), moi request chua login bi chuyen huong form dang nhap,
st.stop() truoc khi bat ky route nao render. Nhanh anonymous chi kich hoat khi AUTH_REQUIRED tat
(mode don nguoi dung legacy). Khong co route nao permission finance_view/commercial_view; 2 key nay
chi la content guards trong views. => Khong lo lo bi mat du lieu qua anonymous path trong mode da nguoi dung.
## 5. Ket luan audit

a. 7 role keys khong phai 7 quyen doc lap: chi 3 role chinh thuc (admin, sale, support) + 1 fallback
(viewer) + 4 legacy keys (accounting, operations, sales) giu tuong thich nguoc. Ma tran duoc C15 chung nhan:
test_support_is_read_only_on_finance_and_admin, test_sale_cannot_touch_finance_writes_or_admin,
test_viewer_is_read_only, test_unknown_role_falls_back_to_viewer PASS (27/27 C15 suite).
b. Khong ton tai permission gap de sale/support ghi finance, xoa shipment/customer, hay len admin.
c. Delete operations gioi han o admin + audit trail (soft-delete -> hard-delete, _audit).
## 6. Residual va khuy nghi (khong block release candidate)

R1. Khong co 4-eyes cho elevation thanh admin hoac xoa user: quyet dinh nghiep vu cua Owner (K1).
R2. actor fallback admin trong delete_user: route guard chan truong hop nay thuc te (K2).
R3. 4 legacy role keys ton tai nhieu hon ma tran nghiep vu: de nghi Owner quyet dinh giu hay thu gon (K3).
K1. Owner quyet dinh: ban hay giu 4 legacy roles (accounting, operations, sales, viewer) sau migrate?
K2. Owner quyet dinh: co can 4-eyes cho elevation thanh admin khong?
K3. Sau release: xem xet xoa nhanh anonymous trong has_permission khi AUTH_REQUIRED bat.