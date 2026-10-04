# Kế hoạch Triển khai Phase 3: Voiceover Writer

## Mục tiêu
Chuyển đổi Dàn ý Kịch bản (Script Outline từ Phase 2) thành Lời thoại chi tiết (Spoken Text). Lời thoại này sẽ dùng để làm kịch bản thu âm (Voiceover) ở giai đoạn dựng video. Phase này hoàn toàn chỉ xuất ra TEXT, KHÔNG làm Text-to-Speech (theo đúng ràng buộc AGENTS.md).

## Cấu trúc dữ liệu mới (Contracts)
**VoiceoverJSON** bao gồm:
- `script_id`: ID của kịch bản gốc.
- `voiceover_scenes`: Danh sách lời thoại tương ứng với từng phân cảnh.
  - `scene_number`: Số thứ tự phân cảnh (Khớp tuyệt đối với Phase 2).
  - `spoken_text`: Câu văn hoàn chỉnh, mượt mà, văn phong YouTube.

## Chiến thuật "Chia để trị" (Chunking)
Vì lời thoại cho video 10-15 phút dài khoảng 1500-2500 chữ, chắc chắn sẽ vượt quá giới hạn output của Gemini Web nếu gọi 1 lần. 
=> **Luồng xử lý:** Code sẽ gom các Scenes lại theo từng Chương (Chapter). Gọi AI viết lời bình cho từng Chương riêng biệt, sau đó tự động ghép lại.

## 1. db-architect (Bước 1)
- **Cập nhật `core/contracts.py`:** Thêm class `VoiceoverSceneJSON` và `VoiceoverJSON`.
- **Cập nhật `core/database.py`:** 
  - Thêm bảng `voiceovers` với các cột: `id` (PK), `script_id` (FK), `content` (lưu JSON Text), `created_at`.
  - Thêm helper: `get_scripts_without_voiceover()` và `save_voiceover(script_id, voiceover_json)`.

## 2. content-coder (Bước 2)
- **Viết `modules/voiceover/engine.py`:** 
  - Class `VoiceoverEngine` tái sử dụng `GeminiWebAdapter`.
  - Hàm `generate_chapter_voiceover(...)`: Gửi toàn bộ outline của video cho AI đọc hiểu mạch truyện, nhưng chỉ yêu cầu viết câu từ chi tiết cho các Scene thuộc 1 Chương cụ thể. Bắt buộc phong cách kể chuyện (storytelling) cuốn hút.
  - Hàm `generate_full_voiceover(...)`: Loop qua các chương và gộp JSON lời thoại lại.
- **Viết kịch bản CLI `run_phase3.py`:**
  - Hiển thị danh sách các Kịch bản (Phase 2) chưa có lời thoại.
  - Người dùng nhập ID để chọn.
  - Chạy Engine tự động lặp qua các chương.
  - Lưu vào bảng `voiceovers`.

## 3. qa-test-engineer (Bước 3)
- Viết `tests/test_voiceover.py`.
- Mock Data để test việc gộp lời thoại từ nhiều lần gọi AI, đảm bảo `scene_number` không bị mất mát hoặc lộn xộn.
