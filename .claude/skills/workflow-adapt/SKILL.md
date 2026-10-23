---
name: workflow-adapt
description: Tự điều chỉnh cách làm việc của agent cho khớp thực tế của TubeChain. Phát hiện chỗ hạ tầng agent (hub, procedure, skill, hook, lệnh test) lệch với repo hoặc với yêu cầu lặp lại của người dùng, rồi đề xuất sửa ở kênh tuỳ biến. Kích hoạt khi người dùng sửa cùng một hành vi ≥2 lần, khi lệnh test chạy lỗi vì đã đổi, khi quy tắc mâu thuẫn với code, hoặc khi nghe "điều chỉnh cách làm việc", "agent làm sai quy ước repo này", "cập nhật quy tắc agent", "adapt workflow".
---

# Workflow Adapt — Tự điều chỉnh cách làm việc

Bản đồ tín hiệu → điều chỉnh: `docs/agent/knowledge/adaptation-rules.md`.
Skill này **đề xuất và áp dụng sau khi được người dùng duyệt** — không tự nới guardrail, không sửa file bừa bãi.

## MUST trigger
**MUST** thực thi khi một trong các điều kiện sau xảy ra:
- Người dùng sửa cùng một hành vi của agent **≥ 2 lần** trong phiên làm việc.
- Lệnh build/test/lint ghi trong hub hoặc hồ sơ dự án chạy lỗi do lệnh đã thay đổi (không phải do lỗi code).
- Quy tắc trong `CLAUDE.md` hoặc agent definition mâu thuẫn với convention đang dùng thật trong repo.
- Hook chặn nhầm cùng một mẫu lệnh từ lần thứ 2 trở lên.
- Repo đổi hình dạng: thêm/bớt thư viện, đổi cấu trúc module, thay đổi framework test.

**NEVER** tự ý sửa hạ tầng agent giữa chừng một task mà không dừng lại trình đề xuất cho người dùng.

## Quy trình 5 bước

### Bước 1 — Ghi nhận điểm lệch
- Mô tả điểm lệch bằng 1–2 câu: hành vi hiện tại của agent · hành vi mà repo hoặc người dùng thực sự yêu cầu.
- Thu thập bằng chứng cụ thể: `file_path:line_number`, lệnh chạy kèm mã thoát (exit code), trích dẫn ngắn câu nói của người dùng.
- Nếu không có bằng chứng rõ ràng → dừng, hỏi người dùng; không tự điều chỉnh theo phỏng đoán.

### Bước 2 — Định vị nguồn gốc
- Xác định hành vi bắt nguồn từ file nào: `CLAUDE.md`, `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, hay `docs/agent/knowledge/*.md`.

### Bước 3 — Chọn phương án điều chỉnh nhỏ nhất
- Tra bảng tín hiệu trong `docs/agent/knowledge/adaptation-rules.md`.
- Ưu tiên thứ tự: sửa giá trị (lệnh, đường dẫn, ngưỡng) → sửa một quy tắc cụ thể → thêm ngoại lệ có điều kiện → loại bỏ thành phần thừa.
- Kiểm tra không vi phạm guardrail cốt lõi (ranh giới bảo mật, an toàn dữ liệu, không xóa DB/media, chạy test trước khi báo Done).

### Bước 4 — Trình đề xuất cho người dùng duyệt
Trình bày bảng đề xuất:

| Điểm lệch | Bằng chứng | File cần sửa | Nội dung thay đổi | Ảnh hưởng | Cách đảo ngược |
|---|---|---|---|---|---|

Chờ người dùng duyệt trước khi thực hiện ghi file.

### Bước 5 — Áp dụng và ghi dấu vết
- Sửa đúng các file đã được duyệt. Nếu đường dẫn hoặc lệnh xuất hiện ở nhiều file, rà soát lại để cập nhật đồng bộ.
- Ghi nhận 1 dòng vào mục 12 "Quyết định thích ứng" trong `.agent-bootstrap/project-profile.md` và `.claude/state/decisions-log.md`.
- Nếu sửa hook: chạy lại test kiểm chứng hook (`tests/test_claude_hooks.py`) và báo kết quả.
