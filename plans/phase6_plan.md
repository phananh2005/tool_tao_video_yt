# Kế hoạch Triển khai Phase 6: SEO Optimizer & Xuất bản

## Mục tiêu
Hoàn thiện quy trình sản xuất bằng cách tự động sinh bộ thông tin chuẩn SEO cho video YouTube. Giai đoạn này giúp người dùng tối đa hóa tỷ lệ nhấp chuột (CTR) và tối ưu hóa công cụ tìm kiếm của Youtube, chỉ việc Copy & Paste khi Upload video.

## Thông tin sinh ra (Metadata)
Bộ Metadata bao gồm:
1. **Title (Tiêu đề):** Hấp dẫn, khơi gợi tò mò, chứa từ khóa.
2. **Description (Mô tả):** Đoạn mô tả chi tiết chứa từ khóa phụ và lời kêu gọi hành động (Subscribe/Like).
3. **Tags (Từ khóa):** 15-20 từ khóa liên quan nhất.
4. **Timestamps (Chỉ mục thời gian):** Tự động tính toán số phút:số giây cho từng Chương (Chapter) để tạo tính năng Video Chapters trên Youtube.
5. **Thumbnail Concept:** Gợi ý thiết kế ảnh bìa (chữ gì to, nền gì, màu sắc chủ đạo).

## 1. db-architect (Bước 1)
- **Cập nhật Database:** Tạo thêm bảng `seo_metadata` để lưu thông tin (Cột: `id`, `script_id`, `content`, `created_at`).
- **Hàm hỗ trợ:** `get_rendered_projects_without_seo()` (Lấy dự án đã xong Phase 5 nhưng chưa có SEO) và `save_seo_metadata()`.

## 2. content-coder (Bước 2)
- **Tính toán Timestamps bằng Python:** Không tin tưởng AI làm toán cộng thời gian. Tool sẽ tự động duyệt qua danh sách ảnh và thời lượng (Timeline) của từng Chương, cộng dồn giây và format ra định dạng `MM:SS` chuẩn Youtube.
- **Viết `modules/seo_optimizer/engine.py`:**
  - Gửi Tên chủ đề và Tóm tắt kịch bản cho Gemini để nhờ viết Title, Description, Tags và Thumbnail Concept dưới dạng JSON.
  - Sau khi nhận JSON về, Python sẽ ghép dính mảng Timestamps (đã tính ở trên) vào Description.
- **Viết kịch bản `run_phase6.py`:** 
  - Chọn dự án.
  - Chạy Engine lấy SEO.
  - **Đặc biệt:** Tự động tạo và lưu một file văn bản tên là `YouTube_Upload_Info.txt` ngay trong thư mục `data/projects/{id}/`. Người dùng mở file này lên copy dán vào web Youtube là xong.

## 3. qa-test-engineer (Bước 3)
- Kiểm tra file `YouTube_Upload_Info.txt` có fomat đẹp, rõ ràng. Đảm bảo Timestamps luôn bắt đầu bằng `00:00` (Quy định bắt buộc của YouTube để nhận diện Chapters).
