---
name: tdd-playbook
description: Áp dụng vòng lặp Red-Green-Refactor cho thay đổi hành vi TubeChain và xác minh bằng pytest phù hợp.
---

# Quy trình TDD — Red, Green, Refactor

Dùng cho thay đổi hành vi, sửa lỗi và logic mới. Thay đổi chỉ gồm tài liệu/cấu hình có thể dùng kiểm tra format/schema thay cho unit test ứng dụng.

1. **Red:** Đọc test và contract hiện có. Thêm/sửa test nhỏ nhất mô tả hành vi mong đợi. Chạy test, xác nhận lỗi đúng do hành vi còn thiếu/sai. Nếu không thể chạy trước khi implement, nêu lý do; không được nói đã quan sát Red nếu chưa chạy.
2. **Green:** Viết thay đổi nhỏ nhất, nhất quán để test pass; giữ public contract trừ khi có bàn giao thiết kế duyệt đổi.
3. **Refactor:** Xóa trùng lặp, làm rõ code mà không đổi hành vi; giữ test pass.
4. **Xác minh:** Chạy lại test tập trung rồi test module/suite liên quan. Báo lệnh và kết quả thật, kể cả thất bại.

Lưu ý riêng TubeChain:
- Dùng fixture cô lập và SQLite tạm. Không xóa hoặc thay `data/tubechain.db` để làm test pass.
- Khi sửa dedup, kiểm tra `>0.85`, đúng `0.85`, `0.60` và dưới `0.60`; khi sửa Rabbit Hole, kiểm tra giới hạn ba video.
- Test văn bản voiceover Phase 3 riêng với tổng hợp giọng nói Phase 3.5 hiện có.
- Hook `PostToolUse` chỉ đưa lời nhắc: không thể hoàn tác edit hoặc chứng minh đã thực hiện Red-Green-Refactor. Developer chịu trách nhiệm quy trình TDD.
