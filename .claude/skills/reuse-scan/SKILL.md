---
description: >
  Quét tìm thành phần ĐÃ CÓ trong repo TRƯỚC khi viết code mới, để không viết lại thứ đã tồn tại.
  Kích hoạt trước khi tạo util/helper/mapper/converter/formatter/validator/constant/hàm xử lý chung,
  hoặc khi nghe "có sẵn chưa", "đã có hàm nào", "tránh trùng", "viết lại hay dùng lại".
  Xuất Reuse Report 3 nhóm và ghi vào current-task.md.
---

# Reuse Scan

## MUST trigger
- Sắp **tạo mới** thành phần mang tính dùng chung (util, helper, mapper, converter, formatter, validator, constant, enum, hàm xử lý lặp lại được).
- Agent `developer` ở bước lập kế hoạch — luôn chạy, kể cả khi "cảm giác" là chưa có.

**NEVER** viết thành phần dùng chung mới khi chưa có Reuse Report.
**NEVER** kết luận "không có sẵn" mà không ghi **đã quét ở đâu, bằng cách nào**.

## Quy trình

### Bước 1 — Lập bộ từ khoá
- Khái niệm nghiệp vụ (tiếng Việt + tiếng Anh).
- Động từ kỹ thuật: validate, format, parse, convert, map, resolve, retry, mask, export…
- Biến thể tên theo convention Python: `xxx_util`, `xxx_helper`, `format_xxx`, `parse_xxx`…

### Bước 2 — Tra cứu
Dùng Grep/Glob tìm trong `core/`, `modules/`, `tests/`:
1. Phủ mọi nguồn trước, rồi đào vào ứng viên.
2. Ghi lại cách tra để reviewer đối chiếu.

### Bước 3 — Phân loại

| Nhóm | Nghĩa | Ghi kèm |
|---|---|---|
| **DÙNG LẠI** | Đã có thứ đáp ứng đúng | `path#symbol` + cách gọi |
| **MỞ RỘNG** | Có thứ gần đúng — bổ sung thay vì viết bản song song | Vị trí + thay đổi dự kiến |
| **VIẾT MỚI** | Thật sự chưa có | Lý do + nguồn đã quét + từ khoá đã dùng |

> **Không thấy ≠ không tồn tại.** Nghi có tương đương nhưng nằm trong vùng mù → **DỪNG, hỏi người dùng**.

### Bước 4 — Ghi Reuse Report
Ghi vào mục `## Tái sử dụng` của `.claude/state/current-task.md`.

**NEVER** để Reuse Report chỉ trong chat — `qa-reviewer` (chiều 5) đối chiếu bảng này.

## Liên kết
- Gọi từ `developer` (bước quét tái sử dụng) · đối chiếu ở `qa-reviewer` / `code-review`.
