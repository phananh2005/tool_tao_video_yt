# Kế hoạch Thực thi: Quản lý Kho Ý Tưởng (Idea Bank) & Tối ưu Dedup

## 1. Vấn đề cốt lõi & Lỗ hổng cần vá
Sau khi kiểm tra kỹ lưỡng, hệ thống hiện tại đang dính **3 lỗi logic nghiêm trọng**:
1. **Kho Ý Tưởng bị lẫn lộn Video đã làm**: API load danh sách Idea hiện tại không thèm kiểm tra xem Idea đó đã được tạo Kịch bản hay chưa. Nếu lôi Màn hình 1 ra làm Kho, nó sẽ hiển thị cả những video bạn đã up lên YouTube, dẫn đến nguy cơ ấn nhầm "Tạo Kịch Bản" đè mất dữ liệu cũ!
2. **Lãng phí Ý tưởng nháp**: Mỗi lần Brainstorm sinh 5 ideas, user chọn 1, 4 cái còn lại nằm mốc trong DB, không có đường link nào từ Dashboard để vào Màn hình 1 lấy lại chúng.
3. **Lỗ hổng Bộ nhớ AI (Dedup)**: Các ý tưởng bị máy đánh giá trùng lặp (>85%, `drop`) hoặc bị user chủ động vứt sọt rác (`rejected`) đang KHÔNG được làm thước đo cho AI. Dẫn đến việc AI cứ đẻ đi đẻ lại những thứ sếp đã ghét.

## 2. Giải pháp UI/UX (Màn hình 1 & 2)
### Dashboard (Màn hình 1)
- Ở Cấp độ 1 (Theme/Project), bổ sung nút: **`[💡 Kho Ý Tưởng (N)]`**. 
- `N` là số đếm chính xác các ý tưởng **CHƯA ĐƯỢC CHỌN LÀM KỊCH BẢN** và **CHƯA BỊ VỨT BỎ**.

### Idea Factory (Màn hình 2 - Khi bấm vào từ Kho)
- Chỉ hiển thị danh sách các ý tưởng hợp lệ (pass/warn) còn tồn đọng.
- Vô hiệu hóa/Ẩn nút `[Tạo Kịch Bản]` đối với các ý tưởng bị hệ thống chấm `Drop`.
- Thêm nút **`[🗑️ Vứt bỏ]`** bên cạnh các ý tưởng nháp. Bấm vào sẽ đổi status thành `rejected` và làm biến mất khỏi UI.

## 3. Nâng cấp DB & SQL (Bắt buộc độ chính xác 100%)
- **Truy vấn Đếm N & Load Kho Ý Tưởng**: 
  Phải dùng kỹ thuật `LEFT JOIN`: 
  `SELECT ... FROM ideas i LEFT JOIN scripts s ON i.id = s.idea_id WHERE i.project_id = ? AND s.id IS NULL AND i.status IN ('pass', 'warn', 'pending')`
- **Logic Dedup Tuyệt đối**:
  Sửa hàm `get_project_ideas` (dùng để tính toán độ trùng lặp nội bộ). BẮT BUỘC bỏ điều kiện `status != 'dropped'`. AI phải dùng TẤT CẢ lịch sử (đã làm, đang nháp, bị drop, bị reject) làm thước đo. Có như vậy, ý tưởng sếp đã vứt đi mới vĩnh viễn không bị gọi hồn về.
- **Sửa API `POST /api/phase1/brainstorm`**:
  Gỡ bỏ dòng `if status != 'drop':` để cưỡng chế lưu TẤT CẢ sản phẩm AI nghĩ ra vào DB.

## 4. Phân công Thực thi (Workflow)
1. **Gọi `db-architect`**: 
   - Viết lại câu SQL đếm số `N` trong `app.py` cho Dashboard.
   - Sửa SQL API `/api/projects/{id}/ideas` áp dụng `LEFT JOIN scripts` để lọc Idea đã làm.
   - Thêm API `PUT /api/ideas/{id}/reject`.
   - Sửa API Brainstorm để lưu tất cả Idea.
2. **Gọi `web-coder`**: 
   - Thêm nút `[Kho Ý Tưởng (N)]` vào Dashboard. 
   - Nâng cấp màn Idea Factory: Chặn click các idea `drop`, thêm nút `[Vứt bỏ]` gọi API reject.
