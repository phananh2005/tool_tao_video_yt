# Kế hoạch Triển khai Phase 5: Video Assembler (Ghép Video)

## Mục tiêu
Tạo ra một video hoàn chỉnh (`.mp4`) bằng cách ghép nối tuần tự toàn bộ các bức ảnh đã được tải về ở Phase 4. Thời gian hiển thị của mỗi bức ảnh sẽ khớp chính xác với `duration_seconds` được AI tính toán ở kịch bản Phase 2.

## Ràng buộc tuân thủ (Theo AGENTS.md)
1. **Không có TTS (Text-to-Speech):** Video xuất ra sẽ là video dạng Slideshow không có âm thanh (Silent Slideshow). Người dùng có thể sử dụng file này để đưa vào các phần mềm (CapCut, Premiere) tự thu âm và lồng tiếng sau.
2. **Đơn giản tuyệt đối:** Ghép ảnh thô tuần tự (Cut to cut). Không dùng các hiệu ứng zoom (Ken Burns), không transition, không chèn nhạc nền.
3. **Công cụ duy nhất:** Sử dụng thư viện `FFmpeg` gốc.

## 1. db-architect (Bước 1)
- **Cập nhật `core/database.py`:** Thêm hàm `get_ready_to_render_projects()`. Hàm này sẽ gộp (`JOIN`) dữ liệu từ 2 bảng `scripts` (lấy thời gian hiển thị) và bảng `assets` (lấy đường dẫn file ảnh) để tạo thành một chuỗi dữ liệu (Timeline) hoàn chỉnh.

## 2. media-coder (Bước 2)
- **Tạo `modules/video_assembler/engine.py`:**
  - Viết hàm đọc cấu trúc Timeline.
  - Tự động sinh ra file `concat.txt` - đây là file cấu hình chuyên dụng của FFmpeg chứa danh sách ảnh và thời gian hiển thị (Ví dụ: `file 'scene_1.jpg'`, `duration 15`).
  - Gọi lệnh `subprocess.run()` để thực thi `ffmpeg`.
  - Cài đặt bộ lọc `scale=1920:1080` của FFmpeg: tự động kéo giãn hoặc thêm viền đen cho ảnh để đảm bảo video luôn chuẩn Full HD, tránh lỗi crash khi FFmpeg ghép các ảnh không đồng nhất về độ phân giải.
- **Tạo kịch bản CLI `run_phase5.py`:**
  - Hiển thị danh sách các Dự án đã đủ điều kiện Render (đã tải xong ảnh).
  - Cho người dùng chọn dự án và hiển thị thanh tiến trình gọi FFmpeg.
  - Lưu video thành phẩm `final_video.mp4` thẳng vào thư mục `data/projects/{id}/`.

## 3. qa-test-engineer (Bước 3)
- Kiểm tra tính hợp lệ của hàm gọi FFmpeg. Đảm bảo tool sẽ báo lỗi thân thiện (mời cài FFmpeg) nếu máy tính người dùng chưa được cài đặt phần mềm này, thay vì văng lỗi sập chương trình.
