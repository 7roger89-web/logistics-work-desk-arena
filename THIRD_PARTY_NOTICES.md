# Third-Party Notices

Cập nhật ngày 2026-10-27. **Bản thân repository này giữ trạng thái All rights
reserved** (quyết định Owner ngày 2026-10-26; repo không kèm file LICENSE). File
này chỉ kê khai phần mềm bên thứ ba mà dự án phụ thuộc hoặc tái phân phối; nó
không cấp thêm quyền nào cho mã nguồn nội bộ.

Nguồn xác minh license: trường `License`/classifier trong `*.dist-info/METADATA`
của bản cài từ `requirements.lock` (Python 3.11.2), bổ sung từ trường
`license_expression`/classifier trên PyPI khi METADATA để trống; giấy phép JS lấy
từ `registry.npmjs.org`. Không suy đoán khi metadata không nói rõ.

## 1. Python — dependency trực tiếp (nguồn range: `requirements.txt`)

Version là bản ghim trong `requirements.lock`. License SPDX ghi theo metadata.

| Package | Version ghim | License | Ghi chú |
|---|---|---|---|
| streamlit | 1.66.1 | Apache-2.0 | SPDX từ PyPI (METADATA để trống) |
| pymongo | 4.19.0 | Apache-2.0 | extras `srv`; SPDX từ PyPI |
| pandas | 2.3.3 | BSD-3-Clause | |
| openpyxl | 3.1.5 | MIT | |
| python-calamine | 0.9.0 | MIT | SPDX từ PyPI |
| xlrd | 2.0.2 | BSD-3-Clause | classifier BSD |
| pypdf | 6.21.2 | BSD-3-Clause | SPDX từ PyPI |
| plotly | 6.9.0 | MIT | |
| requests | 2.34.2 | Apache-2.0 | |
| google-genai | 1.75.0 | Apache-2.0 | SPDX từ PyPI |
| docxtpl | 0.20.2 | LGPL-2.1-only | dùng như thư viện, không sửa mã |
| num2words | 0.5.14 | LGPL (classifier không gắn version cụ thể) | dùng như thư viện, không sửa mã |
| pydantic | 2.14.1 | MIT | |
| pyTelegramBotAPI | 4.37.1 | GPL-2.0 (field `GPL2`) | dùng như thư viện ngoài, không sửa mã |
| google-auth | 2.62.0 | Apache-2.0 | |
| Pillow | 12.3.0 | MIT-CMU (giấy phép kiểu PIL/HPND) | SPDX từ PyPI |
| mongomock | 4.3.0 | ISC | chỉ dùng cho transport staging/preview |
| tomli | 2.5.0 | MIT | chỉ áp dụng Python < 3.11; không cài trên 3.11 |

Lưu ý tuân thủ: `pyTelegramBotAPI` (GPL-2.0), `docxtpl` (LGPL-2.1) và
`num2words` (LGPL) là các giấy phép copyleft. Dự án chỉ import/dùng như thư viện
không sửa đổi và không nhúng mã nguồn của chúng vào artifact nội bộ; nếu sau này
sửa mã các gói này hoặc phân phối kèm binary, cần rà lại nghĩa lệ copyleft với
Owner. Các dependency gián tiếp (transitive) được ghim đầy đủ trong
`requirements.lock` và giữ nguyên giấy phép đi kèm từng gói.

## 2. Python — công cụ test (chỉ trong lock, không phải runtime deploy)

| Package | Version | License |
|---|---|---|
| pytest | 9.1.1 | MIT |

## 3. JavaScript — mã tái phân phối trong `component/dist/`

`component/dist/logi-shell.js` và `component/dist/logi-shell.css` là output build
được commit vào repo; chúng bundle mã của các gói khai báo trong
`component/package.json`:

| Package | Dải version khai báo | License |
|---|---|---|
| react | ^19.2.8 (React 19) | MIT |
| react-dom | ^19.2.8 (React 19) | MIT |
| react-router-dom | ^7.18.3 | MIT |
| lucide-react | ^1.43.0 | ISC |

Toàn bộ bốn gói là giấy phép permissive (MIT/ISC); bản build vẫn phải giữ nguyên
thông báo bản quyền gốc khi phân phối. DevDependencies (vite, typescript,
tailwindcss, jsdom...) chỉ phục vụ build/kiểm thử, không nằm trong artifact
`component/dist/`.

## 4. Giới hạn của file này

- Chỉ liệt kê dependency **trực tiếp**; danh sách đầy đủ và version ghim của mọi
  dependency gián tiếp nằm ở `requirements.lock` (Python).
- Số liệu rà tại phiên làm việc ngày 2026-10-27 trên các version ghim; khi nâng
  version phải rà lại license (đặc biệt nếu đổi nhà phát hành hoặc đổi giấy phép).
- File này không thay thế văn bản license gốc; văn bản đầy đủ nằm trong từng
  distribution của gói tương ứng.
