---
name: tdd-playbook
description: Áp dụng vòng lặp Red-Green-Refactor cho thay đổi hành vi TubeChain và xác minh bằng pytest. Kích hoạt khi thêm tính năng mới, sửa bug hoặc thay đổi logic nghiệp vụ.
---

# Quy trình TDD — Red, Green, Refactor

Dùng cho thay đổi hành vi, sửa lỗi và logic mới trong TubeChain. Thay đổi chỉ gồm tài liệu/cấu hình có thể dùng kiểm tra format/schema thay cho unit test ứng dụng.

## MUST trigger
- Nhận yêu cầu thêm logic nghiệp vụ, sửa lỗi, hoặc thay đổi hành vi API/pipeline.
- **NEVER** viết code trước khi có test mô tả hành vi mong đợi.
- **NEVER** nói đã thấy Red nếu chưa thực sự chạy test và thấy thất bại đúng lý do.

## Vòng lặp TDD

### Bước 1 — Red (Kiểm thử thất bại)
1. Đọc test và contract hiện có (`core/contracts.py`, `tests/`).
2. Thêm hoặc sửa test nhỏ nhất mô tả đúng hành vi mong đợi.
3. Chạy test: `python -m pytest tests/test_xxx.py -k test_name -v`.
4. Xác nhận test FAIL đúng do hành vi còn thiếu hoặc sai logic (không phải do lỗi cú pháp test).
5. Nếu không thể chạy trước khi implement (ví dụ phụ thuộc môi trường ngoài), ghi rõ lý do.

### Bước 2 — Green (Triển khai tối thiểu)
1. Viết lượng code tối thiểu, đơn giản nhất để test chuyển sang PASS.
2. Giữ nguyên ranh giới contract giữa các phase trừ khi đã được `architect` thống nhất.
3. Chạy lại test: `python -m pytest tests/test_xxx.py -k test_name -v` và kiểm tra PASS.

### Bước 3 — Refactor (Tối ưu mã nguồn)
1. Dọn dẹp mã nguồn, loại bỏ trùng lặp, tối ưu cấu trúc mà không thay đổi hành vi bên ngoài.
2. Đảm bảo tuân thủ `docs/agent/knowledge/non-functional-standards.md` (không query DB trong vòng lặp, phân trang rõ ràng).
3. Chạy lại toàn bộ test suite liên quan để đảm bảo không bị hồi quy.

## Ràng buộc & Lưu ý đặc thù TubeChain
- **Dữ liệu test:** Dùng SQLite tạm (in-memory hoặc file tạm qua fixture) và media fixture giả lập. **TUYỆT ĐỐI KHÔNG** xóa hoặc ghi đè `data/tubechain.db` hay thư mục `data/projects/` của người dùng.
- **Ngưỡng dedup:** Khi sửa logic deduplication, phải test đủ 3 mốc: `> 0.85` (drop), `0.60–0.85` (warn), `< 0.60` (pass), và mốc biên đúng `0.85`, `0.60`.
- **Rabbit Hole:** Phải kiểm thử giới hạn chuỗi tối đa 3 video (`enforce_rabbit_hole`).
- **Phase 3 vs 3.5:** Tách bạch test sinh văn bản lời thoại (`modules/voiceover/engine.py`) và test tổng hợp âm thanh qua TTS (`modules/voiceover/synthesizer.py`).
- **Hook PostToolUse:** Chỉ đóng vai trò cảnh báo/nhắc nhở ngữ cảnh, không thay thế cho kỷ luật tự giác thực hiện TDD của lập trình viên.
