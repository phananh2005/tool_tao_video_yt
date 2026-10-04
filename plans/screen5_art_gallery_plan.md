# Kế hoạch Hoàn thiện Màn hình 5: Art Gallery (Phase 4)

## 1. Hiện trạng & Vấn đề tồn đọng
- **Lỗi gọi hàm Backend:** API `/api/phase4/generate/{script_id}` trong `app.py` đang gọi `engine.generate_prompts_and_images(...)` nhưng class `SceneIllustratorEngine` lại chỉ định nghĩa hàm `generate_assets(...)`. Điều này gây lỗi crash hệ thống khi bắt đầu Phase 4.
- **Tính năng UI chưa hoàn thiện:** Khung hiển thị giao diện Phase 4 (trong `web/index.html`) hoàn toàn chưa có thẻ `<img>` để xem trước hình ảnh, khối `<div v-if="scene.image_path"></div>` đang bị bỏ trống.
- **Thiếu tính năng vẽ lại ảnh lẻ:** Quá trình sinh ảnh AI thường xuyên bị lỗi (sai tỷ lệ, dị dạng khuôn mặt, sai chi tiết). Theo mô tả hệ thống, người dùng cần một nút `[Vẽ lại ảnh này]` cho riêng từng phân cảnh thay vì phải chạy lại toàn bộ từ đầu. Tuy nhiên, Backend hiện tại chưa hỗ trợ API sinh lại một ảnh cụ thể và hàm sinh ảnh cũ đang tự động *Bỏ qua (Skip)* nếu file ảnh đã tồn tại.

## 2. Yêu cầu Nâng cấp (Các Agent cần tham gia)

### 2.1. Sửa lỗi API và Thêm API vẽ ảnh lẻ (web-coder)
- Sửa hàm API `@app.post("/api/phase4/generate/{script_id}")` trong `app.py`: Đổi `engine.generate_prompts_and_images` thành `engine.generate_assets`.
- Viết thêm API `POST /api/phase4/generate/{script_id}/{scene_number}` nhận body chứa `image_prompt`. Hàm này sẽ gọi engine để bắt buộc vẽ lại ảnh của Scene được chọn và ghi đè lên file cũ.

### 2.2. Nâng cấp tính năng Sinh ảnh (media-coder)
- Cập nhật `modules/scene_illustrator/engine.py`: Thêm hàm `generate_single_image(script_id, scene_number, prompt)`. Hàm này sẽ gọi trực tiếp `adapter.generate_image` để vẽ ảnh, lưu vào thư mục dự án và trả về đường dẫn. (Không kiểm tra bỏ qua nếu file đã tồn tại).

### 2.3. Hoàn thiện Giao diện Màn hình 5 (web-coder)
- **Hình ảnh xem trước:** Trong `web/index.html`, chèn thẻ `<img :src="'/' + scene.image_path + '?v=' + imageCacheVersion">` vào vị trí khối div đang trống để hiển thị ảnh ngay lập tức.
- **Nút "Vẽ lại ảnh này":** 
  - Bên dưới phần nhập text "Image Prompt", thêm nút `[🎨 Vẽ lại ảnh này]`.
  - Thêm phương thức `regenerateImage(scene)` vào VueJS, gọi API sinh ảnh đơn và tăng biến `imageCacheVersion` để trình duyệt load lại ảnh mới không bị kẹt cache.
  - Tích hợp thêm UI đánh dấu cảnh báo (isAssetDirty) nếu người dùng gõ sửa Prompt nhưng chưa lưu.

## 3. Luồng Triển khai Đề xuất

1. **Gọi agent `media-coder`:** Thêm hàm sinh lẻ ảnh trong `SceneIllustratorEngine` để hỗ trợ ghi đè file ảnh hỏng.
2. **Gọi agent `web-coder`:** Sửa lỗi Crash trong API của `app.py`, thêm API sinh ảnh đơn lẻ, và cập nhật toàn bộ HTML/JS của Phase 4 trong `web/index.html`.
3. **Kiểm tra luồng (QA):** Sau khi hoàn tất, giao diện Màn hình 5 phải hiển thị được Grid các ảnh. Nhấn thử nút *Vẽ lại ảnh này* và kiểm tra trên UI ảnh có tự reload bằng ảnh mới không.
