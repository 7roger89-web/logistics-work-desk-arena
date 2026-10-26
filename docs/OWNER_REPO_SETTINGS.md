# Cấu hình repository cần quyền Owner (token CI bị chặn)

Ghi nhận ngày 2026-10-26. Token tích hợp đang chạy cho phiên làm việc có quyền
`contents:write` (push/xóa branch được) nhưng **bị từ chối 403 "Resource not
accessible by integration"** ở mọi endpoint cài đặt cấp repository:

- `PATCH /repos/{owner}/{repo}` (description)
- `PUT /repos/{owner}/{repo}/topics`
- `GET|PUT /repos/{owner}/{repo}/branches/main/protection`
- `GET /repos/{owner}/{repo}/actions/permissions`

Các thay đổi dưới đây cần Owner tự thực hiện bằng tài khoản có quyền admin.
Lệnh và payload đã được chuẩn bị sẵn; không cần PAT/secret mới — chỉ cần đăng
nhập GitHub trên trình duyệt hoặc một token có quyền administration.

## 1. Repo description + topics (Settings → General)

Description đề xuất:

```text
Logistics Work Desk — Streamlit operations desk for shipments, tariffs, finance and document workflows
```

Topics đề xuất:

```text
streamlit, logistics, mongodb, python, shipments, finance, documents
```

Lệnh Owner (máy local đã đăng nhập `gh` đủ quyền):

```bash
gh repo edit 7roger89-web/logistics-work-desk-arena \
  --description "Logistics Work Desk — Streamlit operations desk for shipments, tariffs, finance and document workflows"

gh api -X PUT repos/7roger89-web/logistics-work-desk-arena/topics \
  -f 'names[]=streamlit' -f 'names[]=logistics' -f 'names[]=mongodb' \
  -f 'names[]=python' -f 'names[]=shipments' -f 'names[]=finance' -f 'names[]=documents'
```

## 2. Branch protection cho `main`

Quy tắc đề xuất (mức tối thiểu, đúng hợp đồng task: require PR + CI xanh):

- Require a pull request before merging — bật; không cho push thẳng vào `main`.
- Require status checks to pass before merging:
  - check context: **`known-red-gate`** (job trong `.github/workflows/tests.yml`).
  - Require branches to be up to date before merging — bật.
- Require conversation resolution before merging — tùy Owner.
- Không bật "Require signed commits" nếu máy Owner chưa cấu hình signing key.
- Không bật ruleset làm tắt quyền xóa branch task đã merge (cần cho vệ sinh định kỳ).

Lệnh Owner (payload tương đương cấu hình trên):

```bash
gh api -X PUT repos/7roger89-web/logistics-work-desk-arena/branches/main/protection \
  -F required_pull_request_reviews.required_approving_review_count=0 \
  -F required_pull_request_reviews.dismiss_stale_reviews=false \
  -F required_status_checks.strict=true \
  -F 'required_status_checks.contexts[]=known-red-gate' \
  -F enforce_admins=false \
  -F restrictions= \
  -F allow_force_pushes=false \
  -F allow_deletions=false
```

Hoặc qua UI: **Settings → Branches → Add branch ruleset / rule → Branch name
pattern `main`** rồi tick các mục trên.

Sau khi rule hoạt động, mọi thay đổi `main` bắt buộc đi qua PR và chỉ merge khi
job `known-red-gate` xanh (không có FAILED/ERROR mới ngoài `tests/known_red.txt`).
