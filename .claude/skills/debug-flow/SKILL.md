---
description: >
  Debug có hệ thống theo 4 bước Reproduce → Isolate → Diagnose → Fix. Kích hoạt khi
  "debug", "lỗi", "bug", "exception", "error", "không chạy", "tại sao lại…".
  KHÔNG đề xuất nguyên nhân khi chưa tái hiện.
---

# Debug Flow

## MUST trigger
- Nhận báo lỗi.
- Agent định đoán nguyên nhân khi chưa tái hiện — **dừng, quay về Bước 1**.

**NEVER** đề xuất nguyên nhân khi chưa qua Bước 1.

## Quy trình (đúng thứ tự)

### Bước 1 — Reproduce
- Triệu chứng cụ thể; input gây lỗi; stack trace / log quanh thời điểm lỗi (đã redact).
- Tái hiện ở môi trường nhỏ nhất (ưu tiên một test FAIL).
- Không tái hiện được → không đoán; thu thêm dữ liệu hoặc hỏi người dùng.

### Bước 2 — Isolate
- Khoanh module xảy ra lỗi — chưa cần biết vì sao.
- Checklist theo đặc trưng TubeChain:
  - API/route: ranh giới request, JSON parse, DB connection, timeout gọi adapter
  - Pipeline module: input/output contract, adapter response format, file I/O
  - SQLite: transaction, migration, column mismatch
  - FFmpeg: subprocess exit code, file path, codec
  - Playwright/Adapter: selector, timeout, session state

### Bước 3 — Diagnose
- Tìm **root cause** (5 Whys), không dừng ở triệu chứng.
- So cấu hình ứng dụng với biến môi trường (chỉ so **tên key**, không in giá trị bí mật).

### Bước 4 — Fix
- Fix nhỏ nhất xử lý root cause; viết test chặn tái diễn; chạy `python -m pytest`, dán output.

## Dừng và hỏi
- Lỗi chập chờn không tái hiện được.
- Root cause ở adapter/service bên ngoài (Gemini web).
- Fix cần thay đổi kiến trúc → bàn giao cho `architect`.
