# Kế hoạch Triển khai Phase 4: Scene Illustrator (Sử dụng Gemini Web Sinh Ảnh)

## Mục tiêu
Tận dụng trực tiếp model tạo ảnh (Imagen 3) tích hợp sẵn bên trong Gemini Web để sinh hình ảnh cho từng phân cảnh. Thay vì dùng API bên thứ 3, tool sẽ tự động yêu cầu Gemini vẽ ảnh và trích xuất ảnh đó thẳng từ khung chat tải về máy.

## Cấu trúc dữ liệu (Contracts)
**AssetJSON** bao gồm:
- `script_id`: ID của kịch bản gốc.
- `assets`: Danh sách các tài sản của từng phân cảnh.
  - `scene_number`: Số thứ tự cảnh.
  - `image_prompt`: Câu lệnh (được đưa cho Gemini).
  - `image_path`: Đường dẫn file ảnh đã lưu cục bộ (VD: `data/projects/1/scene_1.jpg`).

## Phương pháp tải ảnh trực tiếp từ Gemini (Web Automation)
1. **Lệnh tạo ảnh:** Playwright sẽ gửi câu lệnh cho Gemini: *"Hãy tạo một bức ảnh tả thực tỷ lệ 16:9 về: [Nội dung của scene]"*.
2. **Trích xuất DOM:** Khác với việc trích xuất văn bản (Text), Playwright sẽ đợi đến khi Gemini load xong hình ảnh (thường nằm trong các thẻ `img` đặc biệt hoặc vùng chứa Media của phản hồi).
3. **Lưu trữ:** Lấy đường dẫn (URL) của bức ảnh sinh ra từ thuộc tính `src` (hoặc thông qua công cụ bắt Network của Playwright) và tải nó xuống ổ cứng.

## 1. db-architect (Bước 1)
- **Cập nhật `core/contracts.py`:** Thêm `AssetSceneJSON` và `AssetJSON`.
- **Cập nhật `core/database.py`:** Tạo bảng `assets` và các hàm lưu trữ (Tương tự kế hoạch cũ).

## 2. media-coder (Bước 2)
- **Cập nhật `GeminiWebAdapter`:** Viết thêm hàm `generate_image(prompt)` chuyên biệt:
  - Gửi yêu cầu sinh ảnh vào ô chat.
  - Chờ selector chứa hình ảnh (Ví dụ: `img[src*='googleusercontent.com']`).
  - Lấy link URL của bức ảnh đầu tiên (vì Gemini thường trả về nhiều phương án) và download về máy.
- **Viết `modules/scene_illustrator/engine.py`:** 
  - Đọc `ScriptJSON`, lấy `visual_concept` của từng phân cảnh.
  - Vòng lặp: Truyền `visual_concept` vào hàm `generate_image()` của Adapter.
  - Lưu file `.jpg` tương ứng.
- **Viết kịch bản CLI `run_phase4.py`:** Giao diện chọn kịch bản và chạy thanh tiến trình tải ảnh.

## 3. qa-test-engineer (Bước 3)
- Đảm bảo Playwright xử lý tốt các trường hợp Gemini từ chối sinh ảnh (do chính sách an toàn/bạo lực).
- Kiểm tra tính ổn định của cơ chế Resume (bỏ qua những cảnh đã có ảnh trên ổ cứng).
