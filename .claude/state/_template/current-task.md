---
task: (chưa có task)
created:
status: idle
---

# Current Task: [Tên nhiệm vụ]

## Mô tả
_Dùng skill `task-state-init` để khởi tạo task mới._

## Thiết kế & Ràng buộc liên quan
_Trỏ tới tài liệu thiết kế hoặc kế hoạch liên quan (ví dụ trong `docs/` hoặc `plans/`); chưa có → `không`._

## Definition of Done (DoD)
- [ ] Logic nghiệp vụ đáp ứng yêu cầu.
- [ ] Không vi phạm ràng buộc an toàn (không xóa database `tubechain.db`, không xóa media người dùng).
- [ ] Pre-flight kiểm tra cú pháp đã chạy (`python -m py_compile <file>`).
- [ ] Chạy `python -m pytest` liên quan và đảm bảo PASS 100%.
- [ ] Đã qua đối kháng Maker-Critic (`qa-reviewer` xác nhận 0 critical, 0 major kèm bằng chứng).
- [ ] Chạy `code-review` 5 chiều đạt chuẩn trước khi hoàn thành.

## Các bước thực hiện (tổng quan)
_Khung do `task-state-init` điền:_
- [ ] 1. Khảo sát, phân tích ảnh hưởng & trích xuất code mẫu (Pattern Harvesting).
- [ ] 2. Quét tái sử dụng (`reuse-scan`) và lập kế hoạch vi mô (mỗi bước ≤ 50 dòng code).
- [ ] 3. Triển khai theo TDD (`tdd-playbook`): viết test trước, implement code tối thiểu.
- [ ] 4. Chạy pre-flight syntax check (`py_compile`) và pytest xác minh (Reflection loop nếu fail).
- [ ] 5. Gửi diff cho `qa-reviewer` đối kháng rà soát và giải quyết dứt điểm findings.
- [ ] 6. Review code nội bộ (`code-review`).

## Tái sử dụng & Code mẫu (Pattern Harvesting)
_Do `reuse-scan` và `developer` điền bắt buộc 3 mục:_
- **File mẫu đã đọc:** `path:line`
- **Cấu trúc học tập:** _(cách xử lý lỗi, logging UTF-8, typing, regex JSON...)_
- **Bảng Reuse Report:**
  | Thành phần cần | Phân loại (DÙNG LẠI / MỞ RỘNG / VIẾT MỚI) | Vị trí đã có / Lý do viết mới |
  |---|---|---|

## Kế hoạch chi tiết (Phân rã siêu nhỏ — Atomic Steps)
_Trống — agent `developer` điền. Quy tắc vi mô: Mỗi bước chỉ tác động tối đa 1 hàm hoặc 1 file (≤ 50 dòng code)._
- [ ] Bước 1:
- [ ] Bước 2:

## Blockers / Ghi chú
_chưa có_
