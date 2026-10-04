# Kế hoạch Triển khai Phase 2: Script Generator (Cập nhật Chunking)

## Mục tiêu
Gọi AI (Gemini Web) phát triển ý tưởng thành kịch bản JSON. Vì giới hạn độ dài output của web chat, hệ thống sẽ áp dụng chiến thuật "Chia để trị" (Divide and Conquer) để tránh bị cắt cụt JSON.

## Cấu trúc dữ liệu (Contracts)
**1. OutlineJSON (Cấu trúc tổng quan):**
- `chapters`: Danh sách các chương (Ví dụ: Mở bài, Thân bài 1, Thân bài 2, Kết luận).
  - `chapter_number`: Số thứ tự.
  - `title`: Tên chương.
  - `summary`: Tóm tắt nội dung chương đó.

**2. ScriptJSON (Kịch bản chi tiết):**
- `idea_id`: ID của ý tưởng.
- `scenes`: Danh sách các phân cảnh (được gộp lại từ các chương).
  - `chapter_number`: Thuộc chương nào.
  - `scene_number`: Số thứ tự phân cảnh toàn cục.
  - `visual_concept`: Mô tả hình ảnh khái quát.
  - `duration_seconds`: Thời gian (giây).
  - `narration_outline`: Các gạch đầu dòng nội dung.

## 1. db-architect (Bước 1)
- **Cập nhật `core/contracts.py`:** Thêm `ChapterJSON`, `SceneJSON` và `ScriptJSON`.
- **Cập nhật `core/database.py`:** Thêm bảng `scripts` (`id`, `idea_id`, `content`, `created_at`).

## 2. content-coder (Bước 2)
- **Thiết kế luồng 2 Bước tại `modules/script_gen/engine.py`:** 
  - **Call AI lần 1 (Macro):** Gửi Idea và yêu cầu Gemini lập dàn ý gồm 3-5 Chương (Chapters).
  - **Call AI lần 2 -> N (Micro):** Lặp qua từng Chương, gửi Prompt: "Dựa vào Idea này và dàn ý này, hãy sinh ra chi tiết các Scenes chỉ riêng cho Chương X". 
  - **Gộp kết quả:** Engine sẽ tự động ghép các mảng Scenes của từng Chương lại thành 1 `ScriptJSON` hoàn chỉnh và đánh lại số thứ tự `scene_number`.
- **Viết kịch bản `run_phase2.py`:** Tự động điều phối luồng gọi AI nhiều lần và hiển thị tiến độ (Ví dụ: "Đang gen Chương 1/4..."). Cuối cùng lưu JSON vào DB.

## 3. qa-test-engineer (Bước 3)
- Viết test đảm bảo thuật toán gộp Scenes từ nhiều Chapters hoạt động đúng và mảng `scene_number` được đánh số liên tục.
