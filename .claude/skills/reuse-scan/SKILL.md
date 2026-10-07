---
name: reuse-scan
description: Tìm hành vi có sẵn trong code, contract, test và UI của TubeChain trước khi thêm helper, route, schema, component hoặc pipeline mới.
---

# Quét khả năng tái sử dụng

Trước khi thêm function, class, route, data contract, utility, UI component hoặc hành vi lặp lại:

1. Xác định trách nhiệm và module sở hữu phù hợp. Dùng `Grep`/`Glob` (hoặc `rg` qua Bash khi phù hợp) để tìm đúng thư mục; loại `.git/`, `data/`, cache, file sinh tự động và virtual environment khỏi phạm vi.
2. Tìm cả tên chính xác lẫn hành vi tương tự. Kiểm tra `core/contracts.py` về kiểu dữ liệu, `core/database.py` về persistence, `modules/` về logic phase, `app.py` về route, `web/` về quy ước UI và `tests/` về hành vi kỳ vọng.
3. Đọc implementation, nơi gọi và test của kết quả tìm được. Trùng tên không đồng nghĩa có thể dùng lại.
4. Mở rộng code hiện có nếu phù hợp. Với contract/schema dùng chung, xin bàn giao từ Architect thay vì tự đổi format.
5. Nếu không có phần phù hợp, tạo abstraction nhỏ nhất trong module sở hữu và viết test. Tránh utility quá tổng quát chỉ có một nơi gọi khó hiểu.
6. Trong báo cáo implementation, nêu code đã tái sử dụng hoặc nói ngắn gọn rằng không tìm thấy phần phù hợp.
