---
name: code-review
description: Review nhanh code TubeChain theo 5 chiều (Security, Performance, Correctness, Style, Reuse) trong phiên, TRƯỚC khi commit. Kích hoạt khi implement xong, hoặc khi nghe "review", "check code", "kiểm tra code". Review toàn diện trước PR/MR → agent qa-reviewer.
---

# Code Review — TubeChain (nhanh, trước commit)

Review diff nhanh trước khi commit mã nguồn vào Git. Đảm bảo chất lượng và phát hiện sớm các lỗi cơ bản.

## MUST trigger
- Implement xong bất kỳ thay đổi nào — **trước khi commit**.
- **NEVER** commit khi chưa chạy đủ 5 chiều review.

## Quy trình

### 1. Xác định phạm vi
- Kiểm tra `git diff` và danh sách file đã thay đổi.

### 2. Đánh giá 5 chiều

1. **Security (Bảo mật):**
   - SQLite: Có dùng parameterized query (`?`) không? Tuyệt đối không format string vào SQL query.
   - Filesystem: Kiểm tra path traversal khi thao tác file trong `data/` hoặc `data/projects/`.
   - Secret: Không hardcode API key, token, credential. Không in secret ra log.

2. **Performance (Hiệu năng):**
   - Tuân thủ `docs/agent/knowledge/non-functional-standards.md`.
   - SQLite: Không gọi query trong vòng lặp (`for`).
   - Tác vụ dài (FFmpeg render, TTS synthesize): Không block event loop chính nếu không cần thiết; dùng streaming response hoặc async.

3. **Correctness (Tính đúng đắn):**
   - Khớp contract trong `core/contracts.py`.
   - Xử lý ngoại lệ, null, giá trị biên.
   - Toàn bộ test liên quan đã chạy và **PASS 100%**.

4. **Style & Convention (Quy ước):**
   - Tuân thủ cấu trúc module: `app.py` cho routing, `core/` cho logic nền tảng, `modules/` cho pipeline engines.
   - Code rõ ràng, đặt tên biến/hàm nhất quán bằng tiếng Anh theo chuẩn Python (snake_case).

5. **Reuse (Tái sử dụng):**
   - Có kiểm tra trùng lặp chưa (Reuse Report)?
   - Có hàm helper nào lặp lại logic đã có trong `core/` hoặc module khác không?

### 3. Chuỗi tự kiểm điểm đối kháng (Multi-Pass Audit)
Trước khi đưa ra kết luận, reviewer BẮT BUỘC tự kiểm tra thêm:
- Đã cố gắng tưởng tượng ít nhất 1 tình huống dữ liệu "dị" có thể bẻ gãy code này chưa?
- Test đi kèm có test case nào cho giá trị rỗng/lỗi không? Nếu chưa có → đánh dấu MAJOR để bổ sung.

### 4. Phân loại findings
- **CRITICAL:** Lỗ hổng bảo mật, nguy cơ mất dữ liệu/xóa nhầm database, sai logic nghiệp vụ nghiêm trọng. Phải sửa ngay.
- **MAJOR:** Vi phạm hiệu năng (query trong vòng lặp), thiếu test case biên, lệch contract. Phải sửa trước khi hoàn thành task.
- **MINOR:** Format code, đặt tên chưa tối ưu. Có thể sửa hoặc ghi chú.

### 5. Báo cáo & Khắc phục
- Mỗi finding cần chỉ rõ `file_path:line_number`, kịch bản lỗi, và code đề xuất sửa.
