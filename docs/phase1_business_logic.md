# Tài Liệu Logic Nghiệp Vụ: Phase 1 (Idea Factory & Idea Bank)

## 1. Luồng Khởi tạo (Brainstorming)
Khi người dùng nhập Chủ đề (Theme) và bấm Brainstorm:
1. **Khởi tạo Project**: Hệ thống kiểm tra Chủ đề. Nếu chưa có, tạo `project` mới. Nếu có, dùng lại `project_id`.
2. **Ép LLM Sinh Ý tưởng**:
   - Nếu check chọn **Rabbit Hole**: Máy sinh ra ĐÚNG 3 ý tưởng nối tiếp nhau, set cờ `rabbit_hole_series = True`, đánh số `part_number` (1,2,3), và gán chung một mã `series_id` (UUID).
   - Nếu không check: Máy sinh ra 5 ý tưởng rời rạc độc lập.
3. **Phân tích Chống Trùng Lặp (Dedup)**:
   - Hệ thống lôi TẤT CẢ ý tưởng cũ trong DB (kể cả đã làm, đang nháp, hay đã bị ném sọt rác).
   - Tách mảng `topics` và chạy thuật toán **Cosine/Jaccard Similarity** nội bộ (tại Python, không tốn token LLM).
   - > 85%: `drop` (Cực kỳ nguy hiểm, trùng lặp cao).
   - 60% - 85%: `warn` (Cảnh báo).
   - < 60%: `pass` (Ý tưởng xanh, mới lạ).
4. **Lưu trữ Bắt buộc**: Lưu TOÀN BỘ kết quả (cả `drop`) vào Database để AI học không lặp lại lỗi.

## 2. Quản lý Kho Ý Tưởng (Idea Bank & Graveyard)
Phase 1 không chỉ là sinh ý tưởng mới mà còn là **Trạm Quản lý Kho**:
- Chỉ những ý tưởng `pass`/`warn` và **chưa từng được tạo kịch bản** mới hiện lên giao diện Kho Ý Tưởng.
- Ý tưởng `drop` bị làm mờ, chặn nút tạo kịch bản.
- Tính năng **Vứt Bỏ (Reject)**: Chuyển ý tưởng nháp thành rác (trạng thái `rejected`). Ý tưởng này biến mất khỏi mắt user nhưng VẪN TỒN TẠI ngầm dưới DB để làm bia đỡ đạn cho bộ lọc Dedup, chặn AI không bao giờ đẻ lại ý tưởng mà user đã ghét.

## 3. Ngõ Cụt (Dead-end Fallback)
Nếu user tạo Theme nhưng chưa làm video nào, Theme đó trên Dashboard sẽ hiện nút màu vàng báo hiệu `Vào Kho Ý Tưởng`. Đây là đường lui an toàn để tiếp tục quy trình mà không cần tốn API đẻ thêm ý tưởng.
