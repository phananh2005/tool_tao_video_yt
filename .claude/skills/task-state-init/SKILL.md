---
name: task-state-init
description: Bắt đầu hoặc tiếp tục task TubeChain có nhiều bước bằng checklist và state bàn giao ngắn gọn, không ghi đè task đang chạy.
argument-hint: [task-title]
---

# Khởi tạo state cho task

Dùng với tính năng lớn, sửa lỗi nhiều bước, thay đổi liên phase hoặc khi người dùng muốn theo dõi tiến độ. Bỏ qua với câu hỏi nhỏ hay thay đổi một dòng.

1. Nếu có, đọc `.claude/state/current-task.md` và `.claude/state/progress.md`. Nếu task đang chạy, không ghi đè: xác định yêu cầu mới có tiếp tục task đó không; nếu không thì hỏi người dùng muốn đóng task cũ hay tạo task khác.
2. Dùng `.claude/state/_template/current-task.md` làm cấu trúc. Tạo `.claude/state/current-task.md` với mục tiêu, phạm vi, ràng buộc, tiêu chí nghiệm thu và checklist ngắn. Không bịa thông tin implementation.
3. Chỉ khởi tạo `.claude/state/progress.md` từ template nếu file chưa có. Nếu đã có, nối thêm dòng bắt đầu/tiếp tục có ngày giờ và giữ nguyên lịch sử.
4. Chỉ ghi quyết định kiến trúc quan trọng vào `.claude/state/decisions-log.md` khi log đó đã tồn tại hoặc người dùng yêu cầu. Không ghi đè quyết định cũ.
5. Giữ state ngắn và đúng sự thật; dẫn link/path thay vì chép nội dung source dài.
