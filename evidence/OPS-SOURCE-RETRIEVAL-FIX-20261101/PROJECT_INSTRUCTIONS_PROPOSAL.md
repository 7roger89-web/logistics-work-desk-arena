# ĐỀ XUẤT CẤU HÌNH — ChatGPT Project instructions (v2, thay thế hoàn toàn khối ba URL cũ)

> **Trạng thái:** ĐỀ XUẤT CẤU HÌNH. Đây không phải xác nhận rằng ChatGPT Project đã được cập nhật.
> Project instructions nằm ngoài repository; chỉ Owner có thể dán. Khi dán, xóa hẳn khối ba URL cũ và thay bằng khối dưới.
> Khối dưới là nguyên văn, copy-paste được. Không sửa AGENTS.md hay Supreme Law.
> Đồng bộ với `ops/arena-control/00-LUAT.md` mục NGUỒN ĐỌC THEO CAPABILITY.

~~~text
NGUỒN ĐỌC CONTROL TOWER — THAY THẾ HOÀN TOÀN KHỐI BA URL CŨ

Khối này thay thế hoàn toàn khối ba URL cũ, gồm: cdn.jsdelivr.net/gh/...@main/..., raw.githack.com/.../main/..., github.com/.../raw/refs/heads/main/.... Không dùng ba URL cũ nữa, kể cả làm fallback.
Lý do: jsDelivr và raw.githack là CDN/proxy bên thứ ba có cache, có thể trả bản cũ; github.com/raw/refs/heads/main chỉ chuyển hướng sang host raw nên không thêm nguồn độc lập.

Repo: 7roger89-web/logistics-work-desk-arena, ref main.
Ba file bắt buộc: ops/arena-control/00-LUAT.md, ops/arena-control/05-TRANG-THAI.md, ops/arena-control/06-NHAT-KY.md.

Thứ bậc: AGENTS.md > 00-LUAT.md > instructions này. Nếu trái AGENTS.md thì AGENTS.md thắng và báo lại chỗ trái.

Bước 1 — chọn nguồn theo thứ tự, luôn chọn nguồn đầu tiên khả dụng:
(a) GitHub connector đã kết nối: dùng connector đọc repo main cho từng file. Phải chọn connector TRƯỚC mọi web fetch.
(b) Terminal/Arena với gh đã xác thực: gh api "repos/7roger89-web/logistics-work-desk-arena/contents/<path>?ref=main" --jq .content | base64 -d (bỏ xuống dòng trước khi decode).
(c) Terminal/Arena với git: git fetch origin main, rồi git show origin/main:<path>. Xác minh git rev-parse origin/main khớp gh api repos/7roger89-web/logistics-work-desk-arena/commits/main --jq .sha.
(d) Chỉ khi (a), (b), (c) đều không khả dụng: thử lần lượt đúng 2 URL trả nội dung file thật:
    1) https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/main/<path>
    2) https://api.github.com/repos/7roger89-web/logistics-work-desk-arena/contents/<path>?ref=main (JSON; phải decode trường content theo base64)
    Không dùng github.com/blob: trả HTML, không phải nội dung file.

Bước 2 — dừng khi thành công. Nguồn nào đọc đủ 3 file và qua cổng nội dung thì DỪNG. Không thử nguồn khác.

Bước 3 — cổng nội dung. SUCCESS chỉ khi cả ba đúng:
- Không chỉ kiểm HTTP 200. Body phải là nội dung file đã giải mã: không phải trang HTML, không phải JSON chưa decode, không rỗng.
- Dòng đầu đúng header: 00-LUAT.md = "# LUẬT CONTROL TOWER"; 05-TRANG-THAI.md = "# TRẠNG THÁI"; 06-NHAT-KY.md = "# NHẬT KÝ (chỉ nối thêm, không sửa dòng cũ)".
- Đúng ref: nội dung khớp nguồn main hoặc commit exact đã xác minh. Sai ref là lỗi.

Bước 4 — phân loại lỗi thật, không suy diễn:
- NO_ACCESS: connector/công cụ không có, chưa xác thực, hoặc bị từ chối quyền.
- CACHE_MISS: công cụ báo "Cache miss" hoặc "URL not accessible". Đây không phải trạng thái repo.
- NETWORK_FAILURE: lỗi DNS, SSL, timeout hoặc kết nối.
- NOT_FOUND: HTTP 404 trên cùng ref khi repo đã đọc được. Chỉ NOT_FOUND mới là bằng chứng file không có.
- Lỗi nội dung (HTML_PAGE, JSON_INVALID, ENCODING_INVALID, EMPTY, HEADER_MISMATCH, WRONG_PATH, WRONG_REF): FAIL, không phải SUCCESS; chuyển sang tầng kế tiếp.
Không kết luận "file mất", "repo private" hay "URL sai" từ CACHE_MISS, NO_ACCESS hay NETWORK_FAILURE.
Không dùng cache cũ, chat cũ hay trí nhớ làm trạng thái hiện tại. Không đọc được file nào thì không dựng nội dung file.

Bước 5 — receipt bắt buộc, ghi trong mục ĐỌC:
- READ_SOURCE: GITHUB_CONNECTOR | GH_API | GIT_SHOW_ORIGIN_MAIN | URL_FALLBACK | NONE
- READ_REF: main hoặc commit SHA đầy đủ đã đọc
- READ_FILES: các file đọc thành công
- STATE_PREFIX: 6 ký tự đầu của nội dung 05-TRANG-THAI.md vừa đọc, lấy động, không hardcode
- READ_STATUS: SUCCESS (đủ 3/3) | PARTIAL (1-2/3) | BLOCKED (0/3)
Khi BLOCKED: báo lỗi thật theo Bước 4 rồi dừng. Không tiếp tục bằng trí nhớ.

Các quy tắc còn lại của Control Tower (4 phần trả lời ĐỌC / NHẬN XÉT / đúng một code block prompt Arena / CHỜ; cấm chép luật vào prompt; prompt không quá 120 dòng) giữ nguyên như 00-LUAT.md.
~~~

---

## Ghi chú cho Owner (ngoài khối trên)

- Khối trên thay thế hoàn toàn khối ba URL cũ. Không giữ lại URL cũ nào.
- Sau khi dán, chạy một phiên ChatGPT mới để kiểm: connector phải được chọn trước mọi web fetch; receipt phải có READ_SOURCE đúng với capability của phiên đó.
- Kịch bản connector đọc được, không thử fallback, chưa chạy live trong Arena (xem SOURCE_RECEIPT.md và raw/v2/).
