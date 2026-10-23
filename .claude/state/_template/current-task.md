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
- [ ] Chạy `python -m pytest` liên quan và đảm bảo PASS 100%.
- [ ] Chạy `code-review` 5 chiều đạt chuẩn trước khi hoàn thành.

## Các bước thực hiện (tổng quan)
_Khung do `task-state-init` điền:_
- [ ] 1. Khảo sát & phân tích ảnh hưởng (contract, database schema, caller liên quan).
- [ ] 2. Quét tái sử dụng (`reuse-scan`) và lập kế hoạch chi tiết.
- [ ] 3. Triển khai theo TDD (`tdd-playbook`): viết test trước, implement code tối thiểu.
- [ ] 4. Chạy test xác minh và ghi nhận kết quả.
- [ ] 5. Review code nội bộ (`code-review`).

## Tái sử dụng (Reuse Report)
_Trống — skill `reuse-scan` điền: DÙNG LẠI / MỞ RỘNG / VIẾT MỚI + nguồn đã quét + từ khoá đã tra._

## Kế hoạch chi tiết
_Trống — agent `developer` điền (danh sách file cần tạo/sửa + các bước con) rồi trình người dùng duyệt._

## Blockers / Ghi chú
_chưa có_
