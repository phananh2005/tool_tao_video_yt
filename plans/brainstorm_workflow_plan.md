# Kế hoạch Tích hợp Workflow Brainstorm & Chống trùng lặp (Phase 1)

## Cơ sở dữ liệu (SQLite: data/tubechain.db)
Hệ thống sử dụng 2 bảng chính do db-architect quản lý:
1. **Bảng projects**: Lưu thông tin dự án/chủ đề lớn (Themes).
   - **Các cột**: id (PK), 
ame (Tên dự án/chủ đề), created_at (Thời gian tạo).
2. **Bảng ideas**: Lưu các ý tưởng video (topics) chi tiết đã được tạo.
   - **Các cột**: id (PK), project_id (FK nối với projects), 	itle (Tiêu đề video), 	opics (Từ khóa/Chủ đề con dạng JSON string), 
abbit_hole_series (Boolean: Có thuộc chuỗi 3 video không), part_number (Tập số mấy), summary (Tóm tắt kịch bản), similarity_score (Điểm trùng lặp với video cũ), status (Trạng thái: pending, pass, warn, dropped).

## 1. db-architect (Bước 1)
- **Nhiệm vụ:** Bổ sung các helper tương tác với SQLite trong core/database.py.
- **Chi tiết:**
  - get_or_create_project(name): Tìm project (chủ đề lớn), nếu chưa có thì tạo mới trong bảng projects.
  - get_project_ideas(project_id): Kéo lịch sử các ý tưởng cũ từ bảng ideas ra để phục vụ bộ lọc Dedup.
  - save_idea(project_id, idea_json, similarity_score, status): Ghi kết quả ý tưởng mới vào bảng ideas.

## 2. idea-engine-coder (Bước 2)
- **Nhiệm vụ:** Viết kịch bản tương tác CLI 
un_phase1.py.
- **Luồng hoạt động (Workflow Mới):**
  1. **Hiển thị Menu & Chọn chủ đề:** CLI in ra màn hình 6 chủ đề lớn:
     [1] Công nghệ & AI
     [2] Bí ẩn Vũ trụ
     [3] Lịch sử chưa kể
     [4] Tâm lý học hành vi
     [5] Quản lý Tài chính
     [6] Phát triển bản thân
     *Người dùng nhập số (1-6) để chọn chủ đề ưu thích.*
  2. **Gợi ý Topic qua AI (Brainstorm):** Lưu lựa chọn vào DB (bảng projects). Khởi tạo GeminiWebAdapter (mở Chrome) và truyền chủ đề đã chọn vào prompt cho IdeaEngine.
  3. **Hiển thị Gợi ý cho User:** Nhận về danh sách ý tưởng (Topic Video) chi tiết từ Gemini. In các Topic gợi ý này ra màn hình cho người dùng xem trước.
  4. **Kiểm tra trùng lặp (Dedup):** Tự động kéo danh sách ý tưởng cũ của Project này trong DB. Cho từng ý tưởng mới chạy qua dedup_filter (chống trùng >85% drop, 60-85% warn, <60% pass).
  5. **Giới hạn Rabbit Hole:** Chạy qua hàm enforce_rabbit_hole để đảm bảo không chuỗi nào vượt quá 3 video.
  6. **Lưu trữ:** Tự động lưu các ý tưởng (đã qua màng lọc) vào bảng ideas.

## 3. qa-test-engineer (Bước 3)
- **Nhiệm vụ:** Nghiệm thu toàn bộ Phase 1 bằng cách chạy thực tế.
- **Hành động:** Chạy python run_phase1.py, chọn 1 trong 6 chủ đề trên menu, xem Chrome tự mở và lấy gợi ý, kiểm tra log hiển thị topic, và check 	ubechain.db.
