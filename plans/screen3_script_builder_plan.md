# Kế hoạch Hoàn thiện Màn hình 3: Script Builder (Phase 2)

## 1. Hiện trạng & Vấn đề
- **Hiện trạng:** Đã hiển thị dữ liệu scriptData (các Scene, visual_concept, narration_outline) dưới dạng form cơ bản trong web/index.html. Đã có API PUT /api/scripts/ lưu vào DB thành công.
- **Vấn đề tồn đọng:** 
  - Các Scene đang hiển thị một danh sách phẳng (flat list), chưa phân nhóm theo Chapter (Mở bài, Thân bài...) dù data model (SceneJSON) có thuộc tính chapter_number.
  - Khung nhập 
arration_outline dùng 	extarea gộp dòng bằng \n khá sơ sài, dễ gây lỗi định dạng mảng (Array of strings) nếu người dùng nhập có dòng trống.
  - Chưa có tính năng tự động cập nhật thời lượng (duration) khi người dùng thêm/bớt nội dung văn bản.
  - UI/UX còn thô, khó phân biệt giữa các phân cảnh nếu kịch bản dài.

## 2. Yêu cầu Nâng cấp cho agent web-coder

Agent web-coder cần cập nhật file web/index.html (phần HTML và VueJS instance) để bổ sung các tính năng sau:

### 2.1. Nhóm dữ liệu theo Chapter (Group by Chapter)
- **Logic:** Viết một computed property trong Vue (ví dụ: groupedScenes) để gom nhóm các mảng scene trong scriptData.scenes theo khoá chapter_number.
- **UI:** Render một Header to bản cho mỗi Chapter (Ví dụ: **Chapter 1**), bên trong hiển thị danh sách các thẻ (Cards) của từng Scene.

### 2.2. Trải nghiệm Chỉnh sửa Văn bản Thông minh (Smart Textarea)
- Cải thiện binding Vue trên 	extarea cho 
arration_outline. Loại bỏ các dòng trống dư thừa khi gộp chuỗi.
- Tự động cập nhật scene.narration_outline thành List[str] mỗi khi nhập liệu.

### 2.3. Tự động tính toán lại Thời lượng (Auto-Calculate Duration)
- **Quy tắc tính toán (ước lượng):** Tốc độ đọc khoảng **3 từ / giây**.
- **Hành vi:** Khi người dùng thay đổi 
arration_outline:
  1. Đếm tổng số từ (word count) của toàn bộ phân cảnh.
  2. Cập nhật duration_seconds của Scene = (Số từ / 3) + 2 (giây padding).
  3. Quét toàn bộ scenes và tính lại estimated_total_duration của Script.
- **UI:** Hiện thông số thời gian thay đổi theo thời gian thực (Real-time).

### 2.4. Cải tiến UI/UX (TailwindCSS)
- **Thiết kế Card:** Mỗi Scene nằm trong một vùng g-gray-50 border border-gray-200 rounded-lg p-4 shadow-sm.
- **Trạng thái isDirty:** Thêm cờ để nhận biết Kịch bản đã bị chỉnh sửa nhưng chưa Lưu. Hiển thị nhắc nhở ⚠️ Có thay đổi chưa lưu cạnh nút Lưu Kịch Bản.
- **Visual Concept:** Tạo thêm không gian cho trường isual_concept (Ý tưởng hình ảnh), làm mờ/italic để phân biệt với phần lời bình (narration).

## 3. Luồng Triển khai Đề xuất

1. **Gọi agent web-coder:** Yêu cầu sửa file web/index.html, tập trung vào block HTML <!-- PHASE 2: SCRIPT BUILDER --> và block JS Vue methods/computed.
2. **Kiểm thử (QA):** Khởi chạy python app.py, mở màn hình Phase 2, thử sửa text xem thời lượng (duration) có nảy số tự động không, format JSON khi save API có chuẩn không.