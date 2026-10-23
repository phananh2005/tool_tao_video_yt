---
name: task-state-init
description: Bắt đầu hoặc tiếp tục task TubeChain có nhiều bước bằng checklist và state bàn giao ngắn gọn. Kích hoạt khi nghe "implement [X]", "build [X]", "tạo [X]", "viết [X]", "thêm tính năng [X]", "bắt đầu làm [X]", "start task". Không ghi đè task đang chạy.
argument-hint: [task-title]
---

# Khởi tạo state cho task

Dùng với tính năng lớn, sửa lỗi nhiều bước, thay đổi liên phase hoặc khi người dùng muốn theo dõi tiến độ. Bỏ qua với câu hỏi nhỏ hay thay đổi một dòng.

## MUST trigger
**MUST** thực thi khi nhận request implement **VÀ** chưa có `current-task.md` với `status: in_progress`.

**NEVER** bắt đầu viết code khi chưa xong đủ 4 bước dưới.

## Quy trình

### Bước 1 — Kiểm tra task đang có
- Đọc `.claude/state/current-task.md` và `.claude/state/progress.md`.
- `status: in_progress` → hỏi user: tiếp tục task cũ hay tạo mới.
- `status: done` / `idle` / không có file → tạo mới.

### Bước 2 — Thu thập thông tin
- Hỏi nếu chưa rõ: tên task, Definition of Done, ràng buộc kỹ thuật.
- Đánh giá mức nhẹ: loại thay đổi, phạm vi thô, yếu tố đặc biệt (migration, đổi contract, bảo mật).
- KHÔNG đọc sâu kiến trúc — đó là việc của agent `developer`.

### Bước 3 — Ghi file & Phân rã siêu nhỏ (Micro-Tasking)
Ghi `.claude/state/current-task.md` theo template `.claude/state/_template/current-task.md`:
- Điền Mô tả, Thiết kế liên quan, DoD.
- **Bắt buộc phân rã siêu nhỏ (Atomic Steps):** Các bước thực hiện phải được chẻ nhỏ đến mức mỗi bước chỉ can thiệp **tối đa 1 hàm hoặc 1 file (≤ 50 dòng code)**. Tuyệt đối không dùng các bước chung chung như "Viết toàn bộ Phase 4". Mẫu phân rã chuẩn:
  - Bước 1: Thu thập code mẫu tương đương (Pattern Harvesting).
  - Bước 2: Viết/sửa test case đơn lẻ cho hàm mục tiêu.
  - Bước 3: Triển khai code tối thiểu cho hàm đó.
  - Bước 4: Chạy test và tự sửa nếu lỗi (Reflection loop).
  - Bước 5: Gọi `qa-reviewer` đối kháng rà soát trước khi đóng task.
- Để TRỐNG "Tái sử dụng" (do `reuse-scan` điền) và điền các bước con vào "Kế hoạch chi tiết".

### Bước 4 — Xác nhận
Hiển thị task vừa tạo, hỏi "Bắt đầu implement không?".

Nếu có, khởi tạo `.claude/state/progress.md` từ template nếu file chưa có. Nếu đã có, nối thêm dòng bắt đầu/tiếp tục có ngày giờ và giữ nguyên lịch sử.

## Output
- File `.claude/state/current-task.md` với `status: in_progress`.

## Điều kiện dừng
- User chưa xác nhận tiếp tục hay ghi đè task đang dở.
- Không xác định được DoD.

## Liên kết
- Quét tái sử dụng → skill `reuse-scan`
- Kế hoạch chi tiết → agent `developer`
- Cập nhật tiến độ → skill `progress-tracker`
