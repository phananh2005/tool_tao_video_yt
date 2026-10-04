# Kế hoạch Hoàn chỉnh Màn hình 1: Dashboard (Quản lý Dự án) - Đã Cập Nhật

## 1. Hiện trạng & Lỗ hổng còn tồn đọng
Sau khi đã triển khai thành công hệ thống **Kho Ý Tưởng (Idea Bank)** để giải quyết vấn đề "Ngõ cụt Phase 1", Màn hình Dashboard hiện tại vẫn còn 2 khuyết điểm cực lớn cần giải quyết:
1. **Lỗi "Nuốt" Video**: Dashboard hiện tại vẫn đang dùng logic cũ `idea_id = p_ideas[-1][0]` (chỉ hiển thị video cuối cùng của Theme). Các video khác đang sản xuất trong cùng Theme bị ẩn đi, không có cách nào bấm "Tiếp tục".
2. **Thiếu cơ sở hạ tầng cho Rabbit Hole (Ràng buộc cứng #3)**: UI chưa có tùy chọn ép AI sinh chuỗi 3 video. Database thiếu cột `series_id` để phân biệt chuỗi A và chuỗi B trong cùng một Theme.

Mục tiêu nâng cấp:
- Đổi UI sang dạng **Expandable Tree** (Cây thư mục xổ xuống) để quản lý nhiều video cùng lúc trong 1 Theme.
- Bổ sung luồng tạo và hiển thị Rabbit Hole hoàn chỉnh từ Prompt AI đến Database và UI.

## 2. Kiến trúc Giao diện (UI/UX)
Chia thành 3 khu vực chính:

### Khu vực A: Thống kê tổng quan (Overview Stats)
- Tổng Themes, Tổng Video Đang sản xuất, Tổng Video Hoàn thành.

### Khu vực B: Trạm Khởi tạo (Idea Factory Launcher)
- Form tạo nhanh Theme:
  - **Dropdown (Đã có)**: Chọn 1 trong 6 Content Pillars.
  - **Checkbox (Mới)**: `[ ] Yêu cầu tạo chuỗi Rabbit Hole (3 phần liên kết)`
  - Button: `[🚀 Khởi tạo & Brainstorm]`

### Khu vực C: Bảng Quản lý Tiến độ (Expandable Tree)
- **Cấp độ 1 (Theme/Project)**: Cột Tên Chủ đề. 
  - Nút `[💡 Kho Ý Tưởng (N)]` (Đã có).
  - Nút `[Dọn Media Toàn bộ Theme]`.
- **Cấp độ 2 (Các Video đang sản xuất - Mở rộng khi bấm vào Theme)**:
  - Chỉ hiển thị những Ideas đã được user bấm "Tạo Kịch Bản".
  - **Rabbit Hole Grouping**: UI quét các Idea có chung `series_id`. Nếu có, vẽ một khung viền (border) nét đứt bao quanh 3 video, đổi màu nền để báo hiệu đây là một chuỗi, gắn nhãn `[Phần 1/3]`, `[Phần 2/3]`, `[Phần 3/3]`.
  - Cột Tiến độ: Progress bar 6 Phase.
  - Cột Hành động: `[Tiếp tục Phase X]` và `[Xóa Media Video này]`.

## 3. Nâng cấp Core & Database (Xử lý Rabbit Hole)
- **Sửa Schema**: Chạy lệnh `ALTER TABLE ideas ADD COLUMN series_id TEXT;` để thêm cột gom nhóm.
- **API `GET /api/dashboard`**: Trả về dữ liệu lồng nhau (Project -> Mảng các Active Scripts). Kèm theo `series_id` để UI nhóm lại.

## 4. Nâng cấp Khâu Prompting (Idea Engine)
- Hàm `generate_ideas` nhận thêm tham số `is_rabbit_hole: bool = False`.
- Nếu `True`: Prompt ép LLM trả về đúng 3 ý tưởng nối tiếp nhau, đánh số `part_number` 1,2,3. Sau khi LLM trả về, Python tự động generate một UUID chung gắn vào `series_id` của cả 3 ideas trước khi lưu vào DB.

## 5. Phân công Thực thi (Workflow)
Cần huy động **3 Agent** để vá toàn bộ hệ thống:
1. **`db-architect`**: Cập nhật lại schema bảng `ideas` (thêm `series_id`), sửa API `/api/dashboard` trong `app.py` để trả về nested list thay vì chỉ 1 video cuối cùng.
2. **`idea-engine-coder`**: Cập nhật `modules/idea_engine/engine.py`. Nâng cấp prompt và hàm `generate_ideas` để hỗ trợ cờ `is_rabbit_hole`, tự động gắn UUID.
3. **`web-coder`**: Nâng cấp UI Màn hình Dashboard: Thêm Checkbox Rabbit Hole. Chuyển bảng hiển thị thành Expandable Table, xử lý logic CSS gộp UI cho Rabbit Hole.
