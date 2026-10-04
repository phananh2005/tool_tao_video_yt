# Kế hoạch Bổ sung: Tích hợp Edge TTS (Voiceover Synthesizer)

## Mục tiêu
Tự động hóa hoàn toàn khâu lồng tiếng bằng thư viện `edge-tts`. Khâu này sẽ lấy văn bản tiếng Việt từ Kịch bản (Phase 3) và chuyển thành các tệp âm thanh `.mp3` miễn phí, không giới hạn.

## 1. db-architect
- **Dữ liệu:** Không cần tạo thêm bảng Database mới. Chúng ta sẽ lưu các file `.mp3` trực tiếp vào ổ cứng cùng thư mục với hình ảnh của Phase 4 (`data/projects/{id}/voice_scene_{scene_number}.mp3`).
- Hàm lấy dữ liệu vẫn sử dụng `get_script_by_id()` và `voiceovers`.

## 2. content-coder
- **Viết `modules/voiceover/synthesizer.py`:**
  - Sử dụng lệnh hệ thống (hoặc thư viện) để gọi `edge-tts` (Giọng mặc định: `vi-VN-HoaiMyNeural` - Nữ).
  - Duyệt qua từng `scene_number` trong `VoiceoverJSON`.
  - Sinh file audio tương ứng: `voice_scene_1.mp3`, `voice_scene_2.mp3`...
  - **Khớp thời lượng (Cực kỳ quan trọng):** Dùng công cụ `ffprobe` (đi kèm với ffmpeg) để lấy độ dài thực tế của file MP3 vừa tạo. Sau đó CẬP NHẬT LẠI thời gian (`duration_seconds`) của Scene đó trong bảng `assets` hoặc mảng `timeline` để video ảnh khớp chính xác với độ dài giọng đọc (Không bị chạy ảnh nhanh/chậm hơn tiếng).

## 3. media-coder
- **Sửa lại Phase 5 (FFmpeg):**
  - Thay vì chỉ tạo file `concat.txt` cho hình ảnh, chúng ta sẽ sinh ra 1 danh sách cho ảnh và 1 danh sách cho Audio.
  - Mix 2 luồng lại: Lệnh FFmpeg sẽ lấy input ảnh ghép với input Audio để tạo thành video có tiếng hoàn chỉnh.
