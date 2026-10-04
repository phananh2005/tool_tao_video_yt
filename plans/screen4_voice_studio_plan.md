# Kế hoạch Hoàn thiện Màn hình 4: Voice Studio (Phase 3 & 3.5)

## 1. Hiện trạng & Vấn đề tồn đọng
- **Lỗi mất code UI:** File `web/index.html` hiện tại bị mất toàn bộ mã HTML từ Phase 3 trở đi do một lỗi patch trước đó (tuy nhiên bản backup đầy đủ vẫn nằm trong `index_dump.txt`).
- **Lỗi logic Backend:** 
  - API `/api/phase3_5/synthesize/{script_id}` trong `app.py` đang gọi sai hàm (`synth.synthesize_all()` không tồn tại). 
  - Hàm `synthesize_voiceover` trong `modules/voiceover/synthesizer.py` yêu cầu dữ liệu bảng `assets` (của Phase 4) phải tồn tại. Điều này gây lỗi logic chéo vì Pipeline yêu cầu Phase 3.5 (Tạo Voice) chạy TRƯỚC Phase 4 (Sinh Ảnh).
- **Thiếu tính năng UI (Screen 4):** Giao diện chưa có thẻ `<audio>` để người dùng nghe lại giọng đọc sinh ra từ AI. Chưa có chức năng tổng hợp âm thanh (TTS) riêng lẻ cho từng Scene.
- **Lỗi truy cập File:** Thư mục `data/projects/` chứa file mp3 chưa được mount tĩnh (Static Files) trong FastAPI, nên frontend không thể lấy file để play bằng URL.

## 2. Yêu cầu Nâng cấp (Các Agent cần tham gia)

### 2.1. Phục hồi và Cập nhật Giao diện (web-coder)
- **Khôi phục HTML:** Lấy lại đoạn code từ `<!-- PHASE 3: VOICE STUDIO -->` trở đi trong `index_dump.txt` và ghép vào `web/index.html` (đảm bảo giữ nguyên các nâng cấp của Phase 2 hiện tại).
- **UI Màn hình 4:** 
  - Hiển thị danh sách các thẻ (Card) ứng với mỗi Scene.
  - Mỗi thẻ chứa Textarea để sửa `spoken_text`.
  - Bổ sung nút `[🎧 Sinh Âm Thanh (TTS)]` cho **từng Scene** (để dễ dàng test/sửa lại 1 câu bị lỗi thay vì chạy lại toàn bộ).
  - Bổ sung thẻ `<audio controls>` bên dưới mỗi Textarea để phát file mp3 (vd: `/data/projects/{script_id}/voice_{scene_number}.mp3`).
  - Phía trên góc phải giữ một nút `[Tạo Voiceover toàn bộ]` để xử lý hàng loạt.

### 2.2. Sửa lỗi Backend API (web-coder)
- **Mount Static Data:** Bổ sung dòng `app.mount("/data", StaticFiles(directory="data"), name="data")` vào `app.py`.
- **Cập nhật API Phase 3.5 (`app.py`):**
  - `POST /api/phase3_5/synthesize/{script_id}`: Tổng hợp âm thanh cho tất cả Scene.
  - `POST /api/phase3_5/synthesize/{script_id}/{scene_number}`: Tổng hợp âm thanh cho một Scene cụ thể.

### 2.3. Tái cấu trúc Logic Sinh Âm thanh (content-coder)
- Sửa đổi lớp `VoiceSynthesizer` trong `modules/voiceover/synthesizer.py`:
  - Loại bỏ điều kiện bắt buộc phải có bảng `assets` (của Phase 4). 
  - Lưu trực tiếp file MP3 vào thư mục dự án và có thể chủ động tạo/lưu trước duration hoặc tạo record cơ bản cho `assets` nếu cần, nhưng không được để crash nếu chưa chạy Phase 4.
  - Viết thêm hàm `synthesize_single_scene(script_id, scene_number, text)` để hỗ trợ việc tổng hợp TTS lẻ một cảnh.

## 3. Luồng Triển khai Đề xuất

1. **Gọi agent `content-coder`:** Xử lý lỗi kiến trúc của thư mục `modules/voiceover/synthesizer.py`, đảm bảo có thể sinh MP3 mà không crash khi thiếu dữ liệu Phase 4. Thêm hàm sinh lẻ 1 scene.
2. **Gọi agent `web-coder`:** 
   - Khôi phục `web/index.html`.
   - Cập nhật `app.py` (Mount folder data, sửa Endpoint `/api/phase3_5/synthesize/...`).
   - Tích hợp HTML/VueJS cho UI Màn hình 4 theo bản mô tả trên.
3. **Gọi agent `qa-test-engineer`:** Khởi chạy `python app.py` và test thực tế trên Web: Thử sinh TTS cho 1 cảnh, nghe thử audio, sửa chữ rồi sinh lại.
