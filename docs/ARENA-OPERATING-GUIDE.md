# ARENA-OPERATING-GUIDE — Logistics Work Desk

> **Đây là hướng dẫn vận hành Arena cho dự án này; không phải luật thứ hai.** Luật gốc vẫn là
> `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`; hợp đồng prompt bắt buộc nằm ở
> `docs/CONTROL-TOWER-PLAYBOOK.md` §4. File này chỉ nói CÁCH giao việc cho làn Arena và CÁCH
> đọc kết quả Arena trả về — không mở quyền, không đổi acceptance, không tạo làn thứ hai.

Cập nhật: 2026-10-20. Phạm vi: mọi prompt giao cho executor Arena (Arena Agent Mode) của repo
`7roger89-web/logistics-work-desk-arena`, chuỗi LOGI-199 / PR #211.

## §1 — ARENA LÀ LÀN GÌ

- Arena chạy trên **bản clone tạm** trong sandbox, **không có Chromium** → mọi claim giao diện
  của Arena là `BROWSER_NOT_VERIFIED`; làn browser duy nhất hiện có là **Windows/Codex**.
- Arena **được**: sửa code/docs trên **nhánh session của chính nó**, chạy `pytest`/`node`, push
  **đúng nhánh session**, trả SHA cuối + danh sách file đổi + số đo test.
- Arena **không được**: merge, deploy, force-push, push nhánh khác, mở PR mới, đụng `main`,
  đụng app `tienthanhlog`, ghi production.
- Vì vậy **fast-forward head PR là việc của Control Tower/Owner**, không phải của Arena: Arena
  chỉ báo nhánh + SHA, Control Tower kiểm ancestry rồi mới fast-forward.

## §2 — LUẬT GIAO VIỆC

1. **Chỉ giao việc có test deterministic.** Acceptance phải kiểm được bằng `pytest`/`node`
   ngay trong sandbox, không phụ thuộc máy Owner hay dữ liệu thật.
2. **Không đặt acceptance cần browser.** Ca cần nhìn màn hình → chuyển làn Windows/Codex;
   Arena chỉ được ghi `BROWSER_NOT_VERIFIED`.
3. **Một phiên một mục tiêu.** Nhồi đủ yêu cầu ngay prompt đầu; micro-fix dùng "keep working";
   không mở mục tiêu thứ hai giữa phiên.
4. **RED-before / GREEN-after bắt buộc** với mọi task sửa hành vi: chạy lại test/module trên
   cây CŨ cho fail đúng phản ví dụ, rồi mới chứng minh xanh trên cây mới.
5. **Full suite so baseline cùng môi trường**: `NEW=∅` / `GONE=∅` trên tập FAILED/ERROR; không
   chạy được thì ghi `NOT_RUN` + lý do, **cấm gọi PASS**. Một test xanh chỉ chứng minh đúng
   ranh giới nó chạy, không chứng minh cả app đúng.
6. **Arena báo tên nhánh + SHA cuối**; Control Tower kiểm ancestry (`compare`, xem playbook §6)
   rồi mới cho fast-forward. **Arena không merge.**
7. **Kiểm nhánh mồ côi sau mỗi phiên** (`branches?per_page=100`, xem playbook §6): đã từng mất
   một commit vì push vào nhánh không ai theo dõi (`f51710b` → phải truy vết + cherry-pick
   `162036f`).
8. **Canary đầu phiên** cho việc medium/high risk (một lệnh đọc hoặc một test nhỏ chứng minh
   môi trường sống) trước khi giao lát lớn. **Arena không tự chấm điểm** việc mình làm; người
   viết ≠ người QA.
9. **Task docs-only** phải ghi rõ `DOCS_ONLY=yes` + danh sách CẤM: code Python/React,
   `component/dist`, `.p2p/portable/*`, mọi block `<!-- BEGIN P2P -->`.
10. **Cuối phiên phải để lại** `NEXT_ACTION` + `NEXT_PACKET` ở handoff MỤC 3. Sắp hết quota thì
    viết packet trước, đọc thêm sau.

## §3 — BẰNG CHỨNG ARENA PHẢI TRẢ

Khối tối thiểu, dán được vào báo cáo hoặc comment PR:

```text
LAW_CHECK=PASS | SOURCE=<nguồn luật thật đã đọc> | SOURCE_SHA256=<sha thật>
EXPERIENCE_CHECK=<USE_ACTIVE_EXPERIENCE | NO_MATCH | UNAVAILABLE>
LEARNING_RECONCILIATION=<NONE | CANDIDATE>
BRANCH=<nhánh session> | HEAD=<sha cuối>
FILES=<danh sách file đổi>
FOCUSED=<số test + tên file test>
FULL_SUITE=<số mới> vs <baseline cùng môi trường> | NEW=∅|GONE=∅ | hoặc NOT_RUN + lý do
BROWSER_NOT_VERIFIED            # bắt buộc khi task đụng UI
HANDOFF_UPDATE=YES | PATH=docs/CONTROL-TOWER-HANDOFF.md | COMMIT=<sha>
```

Thiếu số đo thì câu "xong" không có giá trị. Đỏ (fail) không tự động là hồi quy — phải so
**tập** FAILED/ERROR với baseline cùng môi trường.

## §4 — ĐỌC KẾT QUẢ ARENA (dành cho Control Tower)

Bốn dấu hiệu phải dừng lại và hỏi lại, không nghiệm thu:

1. Báo "PASS" mà không kèm **số test + tên file test**.
2. Báo "full suite xanh" thay vì `NEW=∅/GONE=∅` so baseline cùng môi trường.
3. Báo browser/ảnh chụp từ Arena — Arena không có Chromium, đó là claim không thể đúng.
4. Bằng chứng chỉ nằm trên ổ đĩa máy trạm, Control Tower không đọc được → coi như không có.

## §5 — BÀI HỌC ĐÃ TRẢ GIÁ (phía Arena)

- Sửa source React mà không rebuild `component/dist` trong **cùng commit** → màn hình chạy
  bundle cũ, QA nhìn hành vi không còn tồn tại trong source (đã mất một vòng "fix" ma).
- Bằng chứng để ở local → Control Tower không đọc được → phải đăng lại qua comment PR.
- Push xong không báo nhánh + SHA → commit rơi vào nhánh mồ côi, mất một lượt truy vết.
- Prompt thiếu law preflight / OE gate → làm lệch chuẩn, mất cả phiên.
- Hướng dẫn stale trong tài liệu làm người đọc sau hiểu sai trạng thái → mọi con số trong
  tài liệu là "khai báo", phải đo lại trước khi dùng.

## §6 — CHECKLIST CUỐI PHIÊN ARENA

- [ ] `git status` sạch sau commit; đúng nhánh session, không có file lạ ngoài phạm vi.
- [ ] Diff chỉ chạm file được giao (docs-only thì chỉ `.md`; không `dist`, không block P2P).
- [ ] Focused test + full suite đã đo và so baseline cùng môi trường (hoặc `NOT_RUN` + lý do).
- [ ] Handoff đã cập nhật (MỤC 3 trạng thái + MỤC 6 nhật ký) và có `NEXT_ACTION`/`NEXT_PACKET`.
- [ ] Đã push nhánh session và báo SHA cuối cho Control Tower.
- [ ] Không merge, không deploy, không force-push, không PR mới.
