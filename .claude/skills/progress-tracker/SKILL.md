---
name: progress-tracker
description: Cập nhật checklist task TubeChain và nối ghi chú tiến độ/xác minh ngắn gọn, giữ nguyên lịch sử state.
---

# Theo dõi tiến độ task

1. Đọc `.claude/state/current-task.md` và `.claude/state/progress.md` trước khi sửa.
2. Chỉ đánh dấu hoàn tất sau khi bước đó đã làm và xác minh. Không đánh dấu test, review hoặc bàn giao xong chỉ vì dự định sẽ làm.
3. Nối một dòng có ngày giờ vào `progress.md`, nêu việc hoàn tất và kết quả xác minh. Ghi rõ lỗi, blocker và phần bỏ qua.
4. Nếu scope thay đổi, cập nhật minh bạch mục tiêu/checklist; không lặng lẽ xóa mục chưa xong.
5. Giữ log theo thứ tự thời gian, ngắn, đúng sự thật, không chứa secret hoặc output lệnh nguyên văn. Không tạo state file cho việc nhỏ nếu không được yêu cầu.
