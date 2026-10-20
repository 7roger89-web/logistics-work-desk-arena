# CONTROL-TOWER-HANDOFF — Logistics Work Desk

Bàn giao ca cho Control Tower. Mọi task có thay đổi file PHẢI cập nhật file này trước khi báo cáo hoàn tất — quy tắc đứng tại `AGENTS.md` mục `## Control Tower handoff — bắt buộc mọi task`.

## ĐỌC TRƯỚC (cho chat Control Tower mới)

Đọc theo đúng thứ tự này, KHÔNG khảo sát lại repo. Link neo theo PR #211 thường là bản mới nhất; raw.githubusercontent có thể bị CDN trả bản CŨ (đã gặp ca này với AGENTS.md ngày 2026-10-20) — khi cần chắc, đối chiếu head.sha qua api.github.com rồi đọc theo SHA đó.
1. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/AGENTS.md
2. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md
3. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/docs/CONTROL-TOWER-PLAYBOOK.md
4. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/docs/ARENA-OPERATING-GUIDE.md
5. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/.p2p/portable/P2P-EXPERIENCE-CAPSULE.json (kinh nghiệm ACTIVE — non-authoritative, 4KB)
6. Bài học đã trả giá: docs/CONTROL-TOWER-PLAYBOOK.md §9 + AGENTS.md §"Bài học tích lũy" — đọc TRƯỚC khi viết prompt giao việc

Notebook portable 139KB — đủ dùng cho Control Tower là §2A + các RULE được trỏ tới trong playbook §0.2; phần còn lại tra khi cần, đừng đọc hết mặc định.

File này là TRẠNG THÁI, không phải luật. Luật ở AGENTS.md + notebook portable — đọc luật trước khi phân tích thật (notebook §2A).

Link 404 → mở https://api.github.com/repos/7roger89-web/logistics-work-desk-arena/pulls/211 lấy `head.ref` rồi thay chuỗi `refs/pull/211/head` bằng tên nhánh đó — không đoán. Sau khi PR #211 merge vào main thì đổi 5 link sang `.../main/...`. Link theo SHA dùng cho bằng chứng, không dùng cho trạng thái sống.

Luật cứng:
- Bạn ĐỌC được, KHÔNG ghi được (không push, không chạy test, không browser). Muốn ghi thì giao cho Arena/Codex/ChatGPT-connector.
- Không khảo sát lại repo từ đầu. Không tự code.
- Mọi con số trong tài liệu là "khai báo" — phải đo lại mới tin.
- Người viết ≠ người nghiệm thu: QA phải là phiên KHÁC.
- Cuối phiên PHẢI để lại MỤC 3: NEXT_ACTION + NEXT_PACKET dán được ngay. Sắp hết quota thì viết packet TRƯỚC, đọc thêm sau.

Chi tiết cách vận hành: docs/CONTROL-TOWER-PLAYBOOK.md. Luật giao việc cho Arena: docs/ARENA-OPERATING-GUIDE.md. Trạng thái sống: file này, MỤC 3.

## MỤC 1 — MỤC ĐÍCH DỰ ÁN

Journey map-first để Support/Sale nhìn biết lô đang ở công đoạn nào và công đoạn đó còn phải
làm gì. Owner là Sale, giao việc cho Support trên app, dùng hằng ngày cho MỌI luồng. Họ không
đọc code, chỉ tin màn hình. Node báo "xong" khi chưa xong là lỗi nặng nhất.

## MỤC 2 — QUYẾT ĐỊNH ĐÃ CHỐT

- Bên liên kết đứng tên nhập khẩu resolve từ `authority_companies`, KHÔNG authority_agents
- Duyệt 2 stage mới CHỈ cho TT_ENTRUSTED_SUB: `entrustment-ready`, `tt-warehouse-handover`
- Lộ trình: (0) 3 bug → (1) diệt false-done → (2) backport #200/#204/#208 vào #210
  → (3) nối commercial-flow + legal parties + 2 stage → (4) nội dung công đoạn
  → (5) E2E + UAT + merge
- Support/Sale dùng cho MỌI luồng → Luồng B KHÔNG được hoãn
- Journey là lớp trình bày từ facts, không phải kho trạng thái
- Merge main = deploy production. Không đụng app `tienthanhlog`.
- **PR #211 head sync — VIỆC CỐ ĐỊNH sau mỗi phiên Arena**: kiểm ancestry rồi fast-forward `arena/a3117943-logistics-work-desk-arena` lên head nhánh session, kèm expected SHA. Nếu divergent: DỪNG, không force-push; kiểm lại diff PR và handoff. GitHub Edit chỉ đổi base, không đổi head; không merge/deploy.
- **Batch 2 semantics (LCL si-vgm) — CHỐT ĐÚNG (Owner, 2026-10-19)**: LCL CÓ node
  `si-vgm` SI-only (label 'SI', done theo `si_status=='ACCEPTED'`, không VGM).
  Rule đợt 1 "LCL không có node si-vgm" là SAI và đã bỏ.
- **Playbook vận hành Control Tower (2026-10-20)**: `docs/CONTROL-TOWER-PLAYBOOK.md` —
  opener §0 cho chat mới, làn/năng lực, cold start, mẫu prompt W1–W4 + hợp đồng prompt
  bắt buộc, luật khai thác Arena, đường đọc rẻ `api.github.com`, thang failover 5 tầng,
  bất biến liên tục, bài học đã trả giá. Hồ sơ vận hành, KHÔNG phải luật thứ hai
  (luật gốc: `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`).

## MỤC 3 — TRẠNG THÁI
MỤC 3 chỉ giữ CURRENT + ĐANG CHỜ + NEXT_ACTION/NEXT_PACKET; lịch sử cũ ở docs/CONTROL-TOWER-ARCHIVE.md (archive, không phải luật).

- **CURRENT — 2026-10-20 (sau QA độc lập)**: lát mode-copy `afbc18d` đã được QA ĐỘC LẬP nghiệm thu tại [comment 6285586667](https://github.com/7roger89-web/logistics-work-desk-arena/pull/211#issuecomment-6285586667) — **VERDICT=PROVEN** cho đúng 4 tiêu chí acceptance (Sale desktop 4/4, Support mobile 4/4, 0 business write); bằng chứng 18 ảnh + 2 ZIP ở comment. QA tự khai phần CHƯA đo: Sale mobile, Support desktop, màn đăng nhập, `BASELINE_PARITY`. Lịch sử repro: FAIL @ `8aba473` (comment #6281985539) → fix `afbc18d` → browser smoke 8/8 desktop+mobile. Focused 107 PASS. **SỰ CỐ KHOÁ**: ZIP thô đầu tiên chứa `AGENTROUTER_API_KEY`; đã gỡ link và thay bằng ZIP redacted nhưng attachment GitHub gốc không xoá được → **coi như khoá đã lộ, CHỜ Owner rotate**. `OWNER_UAT=INCOMPLETE, NO_MAIN_MERGE=YES, NO_DEPLOY=YES`.

### MỤC 3 — ĐANG CHỜ

- **Task schema chưa có stage binding** (`core/database.py:1813-1835` chỉ lưu content/assignee/deadline): Home/task list mở đúng lô nhưng chưa thể deep-link đúng công đoạn cho task thủ công. Đây là khoảng trống nghiệp vụ của giai đoạn sau; phiên #208-integration KHÔNG thêm schema/migration.
- **Browser QA — đọc đúng 2026-10-20**: **sandbox Arena vẫn không có Chromium** (Playwright CDN + apt mirror bị chặn outbound) nên mọi phiên Arena tiếp tục `BROWSER_NOT_VERIFIED`; làn browser duy nhất hiện có là **Windows/Codex**. Ngày 2026-10-20: QA @ `8aba473` **FAIL** 1 lỗi câu chữ AIR/ROAD (repro 4/4 ở comment PR #6281985539) → **FIX=DONE** @ `afbc18d`, browser smoke **8/8 PASS** desktop+mobile (`BROWSER_MODE_COPY=PASS`); **OWNER_UAT=INCOMPLETE**, chưa nâng thành full-app/Owner UAT PASS. Ảnh #207/HEAD cũ không dùng làm bằng chứng; packet smoke ban đầu ở local, nhưng QA độc lập đã công khai 18 ảnh + 2 ZIP ở comment #6285586667 và PROVEN Sale desktop/Support mobile 4/4; Sale mobile, Support desktop, màn đăng nhập, `BASELINE_PARITY` vẫn chưa đo (xem NEXT_ACTION).
- ~~scope-guard 2 fact `booking_status`/`on_board_at` trong `views/logi_view_model.py`~~ — **ĐÃ CÓ từ chuỗi T1–T5** (`views/logi_view_model.py:2979`, gate `MAIN_CARRIAGE`), Owner không còn phải duyệt việc "đụng file"; nếu muốn gỡ thì Owner nói riêng.
- **Owner quyết định** hướng xử lý 10 failure xung đột test-main × code-#210 (mục riêng hay bỏ qua) — xem số liệu Suite ở trên (sau tích hợp còn 40, gồm 188×3/186/190×4 + main-baseline).
- **Owner**: giữ gate pháp nhân thật và chiều bàn giao tại MỤC 5. Guidance/mode-copy có focused tests 107 PASS và browser slice 8/8; bước kế tiếp là đóng các assurance gaps của mode-copy theo NEXT_ACTION, rồi mới tới Owner UAT đúng dữ liệu thật; không mở lại code nghiệp vụ (3B).

### NEXT_ACTION

Đóng các khoảng trống assurance mà QA độc lập đã tự khai cho lát mode-copy (`BASELINE_PARITY` chưa đo trong đúng môi trường QA; 2 test DOM fail ở full suite nhưng PASS khi chạy riêng — chưa chẩn đoán; 3 khoảng trống vai trò browser: Sale mobile, Support desktop, màn đăng nhập). Sau đó mới tới Owner UAT đúng dữ liệu thật (MỤC 5). Packet dán-ngay:

### NEXT_PACKET (dán được ngay)

```text
LOGI — đóng khoảng trống assurance của lát mode-copy PR #211 (đọc/đo, không sửa code)
GỬI CHO: Codex desktop (Windows) — có checkout thật + Chromium
CHAT_MODE=NEW_CHAT · ROLE=QA độc lập (phiên KHÁC phiên đã sửa) · PROJECT=LOGISTICS-WORK-DESK · REPO=7roger89-web/logistics-work-desk-arena · PR=#211
EXACT_BASE_HEAD=<head PR hiện tại — đối chiếu https://api.github.com/repos/7roger89-web/logistics-work-desk-arena/pulls/211 trước khi làm, không đoán; lần ghi packet này là a366beeaebf9f0c4dbf011de42c13a94d93aeaab>
TASK_AUTHORITY=Control Tower + comment #6285586667 (QA đã PROVEN lát mode-copy, tự khai 3 khoảng trống) + handoff MỤC 3
KHÔNG push code, KHÔNG sửa source (task đọc/đo); bằng chứng chỉ đính qua comment PR #211
P2P_LAW_PREFLIGHT theo AGENTS.md (đọc AGENTS.md → portable law; báo P2P_LAW_SOURCE + LAW_CHECK kèm SOURCE_SHA256; EXPERIENCE_CHECK; LEARNING_RECONCILIATION cuối task) · OE_GATE: "Không bị over engineering chứ?" + SIMPLER_PATH/MATERIAL_PROGRESS/NECESSITY/CORE_BEFORE_SUPPORT/SMALLER_VERIFIABLE_SLICE + OE_VERDICT + 1 lý do
REQUIRED_SKILLS=scope-reality-check (path + SHA256 thật lấy từ .p2p/portable/P2P-SKILL-PROJECTION.json; trả 1 p2p-skill-consumption-receipt/1)
VIỆC 1 — đo BASELINE_PARITY trong ĐÚNG môi trường này: chạy full suite tại EXACT_BASE_HEAD và tại commit ngay trước fix mode-copy, cùng Python/Node/deps/`npm --prefix component ci`. So TẬP FAILED/ERROR → NEW=∅ / GONE=∅. Con số tuyệt đối không quan trọng, tập hợp mới quan trọng. Ghi rõ phiên bản pytest/node.
VIỆC 2 — chẩn đoán 2 test DOM fail khi chạy full suite nhưng PASS khi chạy riêng: nêu tên test + nguyên nhân CÓ BẰNG CHỨNG (thứ tự test / state dùng chung / thiếu node_modules / jsdom). Nếu flaky thì chứng minh bằng re-run, không đoán.
VIỆC 3 — đóng 3 khoảng trống vai trò browser của lát mode-copy: (a) Sale mobile 390×844, (b) Support desktop 1440×900, (c) màn đăng nhập. Cùng 4 fixture FIX-AIR/FIX-ROAD/FIX-FCL/FIX-LCL và ĐÚNG acceptance của comment #6285586667 (AIR/ROAD không còn "hãng tàu"/"trả rỗng"; SEA FCL/LCL giữ nguyên; fields không đổi; 0 business write = versions+audit before=after).
BẰNG CHỨNG BẮT BUỘC: VERDICT=PROVEN|INCOMPLETE|FAILED riêng cho TỪNG việc + ảnh/console/versions/audit ở comment PR (nơi Control Tower đọc được), không chỉ ổ đĩa local.
CẤM: sửa code, merge main, deploy, force-push, PR mới, đụng tienthanhlog, production write, mở scope.
HANDOFF_UPDATE=yes: ghi 1 dòng kết quả vào docs/CONTROL-TOWER-HANDOFF.md MỤC 3/4 + để lại NEXT_ACTION/NEXT_PACKET mới.
DỪNG KHI: 3 việc có verdict rõ + bằng chứng ở comment PR.
```

## MỤC 4 — BẰNG CHỨNG & KIỂM CHỨNG

- **QA độc lập lát mode-copy (2026-10-20, Codex/Windows, Chromium thật)** — **VERDICT=PROVEN** cho 4 tiêu chí acceptance tại `afbc18d`; bằng chứng ở comment #6285586667. QA khai rõ `NOT_RUN`: Sale mobile, Support desktop, màn đăng nhập, `BASELINE_PARITY`. **Sự cố khoá**: `AGENTROUTER_API_KEY` từng nằm trong ZIP thô đính lên comment; attachment gốc còn nguyên trên GitHub → chờ Owner rotate.

- **Browser QA lát mode-copy (2026-10-20, đường Windows/Codex, Chromium thật)** — **FAIL @ `8aba473` rồi PASS sau fix**: repro 4/4 desktop/mobile ở comment PR #6281985539 (editor facts công đoạn Giao hàng của FIX-AIR/FIX-ROAD hiện heading SEA `Đầu nhận — D/O, POD, trả rỗng` + "hãng tàu"; fields đã đúng theo mode) → fix `afbc18d` (copy theo mode: 2 dòng production + DOM test + rebuild dist cùng commit), browser smoke **8/8 PASS** (FIX-AIR/FIX-ROAD/FIX-FCL/FIX-LCL × 1440×900/390×844, 0 business write), focused **107 PASS**, full suite Windows NEW=∅ (1 GONE flaky, recheck PASS) — chi tiết MỤC 6 "2026-10-20 — PR #211: sửa đúng mode cho câu chữ editor công đoạn". **Hạn chế tại thời điểm trước QA độc lập**: evidence packet của smoke ban đầu (REPORT/ảnh/DOM/suite comparison) khi đó chỉ ở `D:/logi-pr211-current/.tmp/logi211-mode-copy/` nên Control Tower chưa đọc được; smoke ban đầu chưa ghi vai trò Sale/Support. QA độc lập đã công khai kết quả tại comment #6285586667; các phạm vi chưa đo được nêu ở NEXT_ACTION MỤC 3. `OWNER_UAT=INCOMPLETE`.
- **QA commit `a811580` + `aba8dcc` (2026-10-19)** — **SOURCE_DIFF_VERIFIED, QA_PASS=NO**. GitHub GET: PR #211 head và nhánh session cùng `aba8dcc` trước sửa, branch không merge; tạo code fix candidate `29bfecd7f431b111dd7b4d35d3ba4675c3b02f6f` và đọc lại từng hunk: helper `core/customs_truth.py` chỉ `True` hoặc `"true"` xác nhận; các reader Journey/VM/checklist/tracking/dashboard dùng chung helper; Streamlit checkbox ép giá trị cũ về boolean trước khi hiển thị; writer chặn `"1"`/giá trị lạ và báo lỗi. `tests/test_journey_stage_guidance.py` thêm ca dương/âm, tracking và kiểm legacy. **Chưa chạy test nào trong phiên QA này**: lệnh CI chuẩn `python -m pytest tests -q --ignore=tests/test_partner_reconciliation_desk_write_oracle.py` NOT_RUN; so baseline `6f9d156` worktree riêng NOT_RUN (`NEW=UNKNOWN, GONE=UNKNOWN`); không có local checkout, không xác minh worktree sạch; trạng thái `component/node_modules` của checkout không xác định; `npm ci`/`npm run typecheck`/`npm run build`/browser/saving checkbox NOT_RUN. Dữ liệu production KHÔNG truy cập/sửa. Các kết quả test/build cũ ở MỤC 3 không phải chứng cứ cho commit QA này. Giữ PR #211 OPEN, **KHÔNG merge main/deploy**.

## MỤC 5 — CẦN OWNER

- **Owner: thu hồi + cấp lại `AGENTROUTER_API_KEY`** (đã lộ qua attachment ZIP công khai trên repo public), cập nhật env/secrets, chạy lại smoke, quét lịch sử git tìm khoá.
- Danh sách pháp nhân thật trong `authority_companies` (tên + vai trò)
- **Bước (3B) — chiều bàn giao kho**: repo KHÔNG định nghĩa bên nào là bên giao / bên nhận
  cho từng trường hợp thật, nên UI chỉ cho CHỌN trong 3 pháp nhân của chuỗi ủy thác và
  không tự suy từ tên công đoạn. Cần Owner chốt: với lô ủy thác tiếp, bàn giao tại kho là
  Trường Thành → đối tác nhận ủy thác, hay pháp nhân đứng nhập khẩu → Trường Thành, và có
  trường hợp nào cả hai chiều đều hợp lệ. Chưa chốt thì không có auto-DONE, không suy chiều.

## MỤC 6 — NHẬT KÝ PHIÊN
Lịch sử cũ đã chuyển nguyên văn sang docs/CONTROL-TOWER-ARCHIVE.md; archive không phải luật hay trạng thái sống.

### 2026-10-20 — LOGI-DOCS-HYGIENE-01 (phần 2/2)

- **Commit SHA**: `4845704880ad2012b0d3c5647cbfe89a2428976b` (hoàn tất việc 0–5); SHA commit cuối có trong receipt `HANDOFF_UPDATE`.
- **Đã làm**: cập nhật cold-start/caveat nguồn, prompt và lesson; rút gọn phần P2P trùng managed trong AGENTS.md nhưng giữ nguyên managed block cùng 4 bullet skill-routing; thu lịch sử MỤC 3/4/MỤC 6 cũ về `docs/CONTROL-TOWER-ARCHIVE.md`. Docs-only.
- **Kiểm chứng**: archive đối chiếu dòng trước/sau, `LOST_LINES=0`; không chạy suite vì chỉ sửa tài liệu.
- **Còn lại / Owner**: Owner rotate `AGENTROUTER_API_KEY`; `OWNER_UAT=INCOMPLETE`; `NO_MAIN_MERGE=YES`, `NO_DEPLOY=YES`.

### 2026-10-20 — Neo ba nguồn thủy tổ + phục hồi guide Arena (docs-only, GitHub connector)

- **Đồng bộ head**: PR #211 `arena/a3117943-logistics-work-desk-arena` đã fast-forward `8f4d15ff` → `89e40625` (compare ahead 1, behind 0; expected SHA match; `force=false`). Không merge main, không deploy.
- **Giữ lại tài sản đã làm**: nhánh Arena `arena/b153ecaf@706f785` phân kỳ với PR (không thể FF); lấy **nội dung** `docs/ARENA-OPERATING-GUIDE.md` và phần cập nhật `docs/CONTROL-TOWER-PLAYBOOK.md` để tích hợp, không chuyển cả commit main-based đè lên lịch sử PR. Guide đã ghi `580b34f`; playbook đã ghi `826f232`.
- **Neo nguồn U1/U2/U3**: thủy tổ `7roger89-web/P2P-upgrade-github-1` @ `db9d3979`; U1 SHA-256 `11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`, U2 `9315f603ab80dc45e46fc6c2dabb98e7f5e0a212108ff3504fd8515f4bb900c3`, U3 `d5e45cea2e75ac0b9c10110423165c2f42b0f40436b3267a55ef08db9de9c443`. Đã đọc và tính lại từ GitHub, cả ba khớp bản `main` tại thời điểm kiểm. Link pin là provenance; Arena đọc LOCAL_PORTABLE, không bị giao việc cross-repo.
- **Phạm vi/kiểm chứng**: chỉ `docs/CONTROL-TOWER-HANDOFF.md`, `docs/CONTROL-TOWER-PLAYBOOK.md`, `docs/ARENA-OPERATING-GUIDE.md`. MỤC 1/2/5 và NEXT_ACTION/NEXT_PACKET nghiệp vụ cũ giữ nguyên. Static contract/source-link checks có, **pytest/full-suite=NOT_RUN; NEW/GONE=UNKNOWN** (GitHub connector không chạy test). Không ghi `.p2p/portable/*`, block P2P managed, code, `component/dist`, `tienthanhlog`, production.
- **Còn lại**: QA độc lập phần docs/provenance nếu cần; NEXT_ACTION chính vẫn là public bằng chứng browser và QA vai trò Sale/Support trước Owner UAT tại MỤC 3; Owner Gate MỤC 5 chưa thay đổi.

### 2026-10-20 — Playbook Control Tower + sửa 3 chỗ hướng dẫn stale (docs-only)

- **Commit docs**: trên nhánh session `arena/5b67d6ed-logistics-work-desk-arena`. **Head PR #211 đổi giữa phiên**: vào phiên ở `8aba473b5208a590590e4949c589aacafbe5c01b`; trong lúc soạn docs, làn Codex/Windows land `afbc18d` (fix mode-copy AIR/ROAD — đúng lỗi ở comment #6281985539) + `8f4d15f` (ghi handoff). Đã reset re-base lên head mới `8f4d15ff581c1fa3daf12626ae5d02d7b734d649` (hậu duệ của `8aba473`, không divergent) và viết lại 3 file docs theo sự thật mới — KHÔNG ghi đè entry handoff của làn Codex. Session rule cấm switch/push nhánh khác → Control Tower kiểm ancestry rồi fast-forward `arena/a3117943-logistics-work-desk-arena` theo luật MỤC 2; expected SHA nằm trong báo cáo task. Không merge main, không deploy, không đụng `tienthanhlog`, không production write, không rebuild dist.
- **AGENTS.md — đúng 3 sửa, đều ngoài mọi block `<!-- BEGIN P2P -->`**: (A) `## Baseline hiện tại`: bỏ trỏ chuỗi C13/C14/C15 @ `e518cae` → trạng thái sống ở file handoff này (đọc trước khi làm) + công việc hiện tại là chuỗi LOGI-199 trên PR #211 (head `arena/a3117943-logistics-work-desk-arena`, base `ct/logi199-journey-main-integration-20261017`); C13/14/15 = lịch sử; giữ nguyên "KHÔNG merge main / KHÔNG deploy cho tới khi Owner xác nhận". (B) `## Testing`: bỏ "kỳ vọng 200 passed, 28 skipped" → số đo thật 2026-10-20 tại `8f4d15f` (**37 failed / 2110 passed / 44 skipped / 0 errors**) + cách đọc đúng (tập failure = 31 lỗi có sẵn trên main + 6 xung đột test-main × code-#210 còn lại, tên đã biết; ĐỎ = hồi quy so baseline; baseline mã hoá trong `.github/workflows/ci.yml`; test cần Mongo/Streamlit thật tự skip theo thiết kế; flaky ±1). (C) thêm `## Definition of Done tối thiểu cho task đụng UI` — 4 gạch: (1) đổi source React ⇒ rebuild `component/dist` CÙNG commit + marker parity; (2) browser QA trên bundle của đúng commit, ≥1 ca Sale + ≥1 ca Support; (3) bằng chứng QA ở nơi Control Tower đọc được; (4) task chỉ-đọc có kết quả nghiệm thu ⇒ ghi 1 dòng vào mục 3/4 — kèm dòng trỏ playbook.
- **`docs/CONTROL-TOWER-PLAYBOOK.md` (mới)**: §0 opener nguyên văn (4 link raw trỏ đúng nhánh `arena/a3117943-...`; link tới chính file playbook có hiệu lực sau khi PR head sync lên commit này), §1 làn/năng lực 5 làn (Venice không ghi được, Arena không có browser, chỉ Owner chốt Owner Gate), §2 cold start (link 404 → lấy tên nhánh từ PR đang mở, không đoán; mọi số trong handoff là "khai báo" phải đo lại; cấm khảo sát lại repo từ đầu), §3 mẫu prompt W1–W4, §4 hợp đồng prompt bắt buộc (thiếu field ⇒ viết lại trước khi gửi), §5 khai thác Arena (deterministic-only, một phiên một mục tiêu, RED/GREEN, kiểm nhánh mồ côi, canary, danh sách cấm), §6 đường đọc rẻ `api.github.com` (mở trang PR đầy đủ ≤1 lần/phiên), §7 failover 5 tầng (Venice → ChatGPT+connector → Codex → Owner tay → dán NEXT_PACKET vào Arena), §8 bất biến liên tục, §9 5 bài học đã trả giá.
- **Handoff (4 sửa, đã điều chỉnh theo sự thật sau `8f4d15f`)**: MỤC 2 +1 dòng trỏ playbook; MỤC 3 ĐANG CHỜ nói rõ 2 sự thật (sandbox Arena vẫn không Chromium; làn browser = Windows/Codex: QA @ `8aba473` FAIL 1 lỗi AIR/ROAD → FIX=DONE @ `afbc18d`, smoke 8/8 PASS; `OWNER_UAT=INCOMPLETE`; bằng chứng smoke chỉ ở file local Windows) + MỤC 3 kết thúc bằng NEXT_ACTION/NEXT_PACKET mới — **không còn là packet sửa AIR/ROAD** (fix đã land) mà là packet public-hoá bằng chứng smoke lên comment PR + QA độc lập có ca vai trò Sale/Support; MỤC 4 +1 dòng bằng chứng QA mode-copy (FAIL history + 8/8 PASS + hạn chế evidence-local); mục này lên trên. MỤC 1/5 và entry handoff của làn Codex giữ nguyên.
- **Kiểm chứng**: docs-only — diff cuối chỉ 3 file markdown (`AGENTS.md`, `docs/CONTROL-TOWER-PLAYBOOK.md`, file này). Full suite `python -m pytest tests -q --ignore=tests/test_partner_reconciliation_desk_write_oracle.py` trong CÙNG môi trường (python 3.11.2, pytest 9.1.1, node v22.22.3, `npm --prefix component ci` để DOM lane chạy cả hai bên): baseline worktree @ `8f4d15f` **37 failed / 2110 passed / 44 skipped / 0 errors** vs code-final **37 / 2110 / 44 / 0**; `comm` trên tập FAILED/ERROR → **NEW=∅ GONE=∅** (giống hệt; đúng 6 xung đột còn lại `186×1 / 190×4 / visual_shipment_workspace×1` + 31 main). Thước đối chiếu trong ngày: `8aba473` đo 37/2109/44/0 — cùng tập failure, +1 pass từ DOM test mode-copy mới. Không có pin nào trong `tests/` phong ấn số liệu suite ("200 passed, 28 skipped" chỉ còn ở tài liệu lịch sử C15 — đúng vai trò lịch sử) → không phải sửa pin. **Ghi nhận cho Control Tower**: `BASELINE_FAILED='41'` trong `.github/workflows/ci.yml` gắn ngày đo 2026-10-19 (hôm đó 41 là thật), hiện thực tế 37 (4 ca 188 đã sửa ở `c5e904d`); chính ci.yml hướng dẫn siết xuống — phiên docs-only này không đụng CI, đề nghị CT cân nhắc siết ở phiên có thẩm quyền sửa workflow. Không đụng: code Python/React, `component/dist`, mọi block `<!-- BEGIN P2P -->`, `.p2p/portable/*`.
- **Còn lại / Cần Owner**: NEXT_ACTION/NEXT_PACKET ở MỤC 3 (public-hoá bằng chứng smoke + QA vai trò Sale/Support); `OWNER_UAT=INCOMPLETE`; 2 gate MỤC 5 giữ nguyên.

### 2026-10-20 — PR #211: sửa đúng mode cho câu chữ editor công đoạn

- **Authority / base / code commit**: [browser reproduction 6281985539](https://github.com/7roger89-web/logistics-work-desk-arena/pull/211#issuecomment-6281985539), vào từ checkout sạch `8aba473b5208a590590e4949c589aacafbe5c01b`; code/test/dist commit `afbc18d7cbbbfd9c8b26df0ed9f578752af4cf5c`. Nhánh `arena/a3117943-logistics-work-desk-arena`; không merge/deploy/PR mới/production write; gói (3B) không mở lại.
- **TASK 0 / phạm vi**: `ShipmentJourney.tsx` chỉ đổi 2 dòng production: `TITLES.delivery` và đoạn giải thích trong `SeaExportFacts`. AIR: “Giao hàng sân bay — D/O, POD”; ROAD: “Giao hàng — biên bản giao nhận, POD”; hai mode dùng “bên vận chuyển”. SEA FCL/LCL giữ nguyên heading và nguyên câu hãng tàu. Không đổi field, renderer/editor, event, writer, RBAC, completion hay backend/schema.
- **Đính chính giả định mode từ bằng chứng thật**: fixture AIR/SEA có pickup Truck ở chặng đầu khiến `s.mode=Truck` (`core/shipment_operations.py:400`, `views/logi_real_data.py:1627`), trong khi Journey dựa trên `executionProfile.mode`. Lượt browser đầu bắt được AIR nhận heading ROAD nếu dùng riêng `s.mode`. Hai biểu thức nay ưu tiên `s.executionProfile?.mode`, fallback `s.mode`; không sửa nguồn dữ liệu. Test mới dùng cả bốn ca `shipment.mode=Truck` + execution profile SEA/AIR/ROAD, nên bắt được lỗi này.
- **RED → GREEN / build**: thêm đúng một test DOM `tests/test_journey_stage_guidance.py::test_delivery_editor_dom_copy_matches_mode_and_preserves_sea_variants`; render actual shipped bundle và fields từ backend. RED trên bundle cũ ở AIR “trả rỗng”; RED riêng cho sai giả định mixed-mode; GREEN sau fix. `npm --prefix component run typecheck`, `run build`, `py -3.12 scripts/scan_process.py component/dist`: thành công, **FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0**. Commit cả JS/CSS từ source mới; rebuild lặp lại cho cùng hash. JS `8fab6a88ac6d0b4fbc126a028bc43597d6c260edf970ee87b124ccf930df1a2d`, CSS `671e675c8a1830174a272ed789de9939edfd45c49d65a725114259ca79455638`.
- **Focused / full suite thật**: `PYTHONUTF8=1 py -3.12 -m pytest tests/test_journey_stage_guidance.py tests/test_journey_node_done_facts.py tests/test_journey_v3_customs_import_184.py tests/test_entrusted_sub_stages_199.py -q` → **107 passed**. Full tại cả hai cây dùng `tests -q --continue-on-collection-errors`, cùng Python/Node/dependencies: baseline `61 failed, 2048 passed, 23 skipped, 5 errors, 16 subtests passed`; bản sửa `60 failed, 2050 passed, 23 skipped, 5 errors, 16 subtests passed`. **Raw NEW=∅ / GONE={test_edit_second_line_note_preserves_first_line_note_and_money}**: baseline chỉ khác `calculated_at` `03:09:13` ↔ `03:09:14` UTC; recheck test này baseline **1 passed**, bản sửa **1 passed**. Giữ nguyên lỗi/flaky ngoài scope, không sửa pin hoặc gọi full suite PASS; tập lỗi ổn định không có hồi quy mới.
- **Browser / nguồn dữ liệu / cleanup**: actual `views.web_app.main` + bundle mới, loopback `127.0.0.1:9503`, sandbox mongomock, fixture factory có sẵn + canonical seed writers, không inject ViewModel vào browser. **8/8 desktop/mobile PASS**: FIX-AIR/FIX-ROAD/FIX-FCL/FIX-LCL → Giao hàng → MỞ CÔNG ĐOẠN → Công việc. Ảnh 1440×900 và 390×844 đúng kích thước; fields AIR 2, ROAD 2, FCL 3, LCL 3 giữ nguyên; nút lưu hiện nhưng không submit. DB/audit before=after, versions cả 4 lô vẫn 1, **0 business write, console=[]**. Đã đóng tab/reset viewport và dừng staging; production 8501/8510 không thao tác.
- **Evidence / limitations / handoff**: local packet `D:/logi-pr211-current/.tmp/logi211-mode-copy/REPORT.md`; ảnh/DOM/results trong `browser-final/`, raw logs và `full-suite-comparison.json`, `skill-consumption-receipt.json` cùng thư mục. Evidence không commit vào source. Anvien launcher thiếu executable, đã ghi log; scope/impact được đọc trực tiếp tại source và đường mount. **HANDOFF_UPDATE=yes**; MỤC 1/2/5 nguyên vẹn. **BROWSER_MODE_COPY=PASS**, **OWNER_UAT=INCOMPLETE**; tiếp theo Supervisor/Control Tower kiểm lát copy này, không mở scope khác.
- **Preflight / skill / OE / learning**: `P2P_LAW_SOURCE=LOCAL_PORTABLE`, canonical body SHA `11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`, `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE` (`shared-exp-b2611df4c9393f0017f07dcb`). Required p2p-uiux/scope-reality-check đọc từ manifest và khớp hai hash Owner ghi. “Không bị over engineering chứ?” → `SIMPLER_PATH=YES, MATERIAL_PROGRESS=YES, NECESSITY=YES, CORE_BEFORE_SUPPORT=YES, SMALLER_VERIFIABLE_SLICE=YES`, `OE_VERDICT=DO_IT`: hai biểu thức + test hẹp, không editor/helper mới. `LEARNING_RECONCILIATION=CANDIDATE`: flat shipment mode có thể là chặng đầu, phải đối chiếu với nguồn mode của Journey; bằng chứng là source + browser và mixed-mode RED/GREEN, chưa promote thành luật/skill.
