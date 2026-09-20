# Architecture Principles — Logistics

Status: OWNER-SELECTED DIRECTION
Policy ID: POLYGLOT_BY_EVIDENCE_V1
Applies from: 2026-09-20

## Rule

Giữ stack hiện tại là mặc định. Chỉ thêm một ngôn ngữ/runtime mới khi có bằng chứng rằng nó giải quyết một nhu cầu kỹ thuật thật tốt hơn đáng kể so với đường đơn giản hơn.

AI có thể giúp giảm chi phí viết và bảo trì nhiều ngôn ngữ, nhưng đó không phải lý do tự thân để tăng số ngôn ngữ trong hệ thống.

## Current project interpretation

- Python/Streamlit và các module nghiệp vụ hiện có vẫn là baseline của Logistics.
- Không rewrite sang Rust, Next.js hoặc stack khác chỉ vì benchmark tổng quát hay xu hướng công nghệ.
- Không coi Python là bottleneck nếu chưa đo. Kiểm tra database, network, document I/O, external API và thuật toán trước.
- Next.js/TypeScript chỉ được cân nhắc nếu có mục tiêu UI/web cụ thể mà kiến trúc hiện tại không đáp ứng đủ, kèm bằng chứng sản phẩm/UX và migration scope rõ.
- Rust chỉ được cân nhắc cho hot path đã đo được như batch processing, parsing/indexing lớn, CPU-heavy computation hoặc low-latency component.
- Nếu Rust được thêm, ưu tiên một component nhỏ có interface ổn định thay vì rewrite backend.
- Database/storage hiện có không bị thay đổi bởi policy này.

## Admission gate for a new language

Trước khi thêm ngôn ngữ/runtime mới, phải trả lời được:

1. Bottleneck/need cụ thể là gì và bằng chứng đo ở đâu?
2. Tại sao stack hiện tại không giải quyết đủ tốt?
3. Boundary tích hợp nhỏ nhất là gì?
4. Benchmark/acceptance trước-sau là gì?
5. Chi phí build, deploy, observability, security và maintenance tăng bao nhiêu?
6. Có đường rollback hoặc loại bỏ component mới không?

Thiếu câu trả lời vật chất cho các điểm trên => DEFER.

## Anti-overengineering

Một ngôn ngữ đủ thì dùng một. Hai ngôn ngữ chỉ khi lợi ích đã chứng minh lớn hơn complexity. Không tạo microservice, queue, daemon, runtime hoặc framework mới chỉ để hợp thức hóa polyglot.

Policy này không tự cấp quyền migration, deploy, database change, infrastructure change hoặc rewrite.
