# TubeChain — Hướng dẫn dự án cho Claude Code

## 1. Hợp đồng hành vi AI (Tối cao)
Các quy tắc MUST / NEVER / BEFORE / AFTER dưới đây đè lên mọi hành vi mặc định và phải được tuân thủ tuyệt đối:

**MUST (Bắt buộc):**
- **MUST** khởi tạo hoặc tiếp tục task nhiều bước bằng skill `task-state-init` (cập nhật checklist và state).
- **MUST** chạy `reuse-scan` trước khi thêm helper, route, schema, component, pipeline mới. Bất kỳ thành phần dùng chung nào được tạo mới phải có Reuse Report giải thích lý do không tái sử dụng.
- **MUST** làm theo `tdd-playbook`: viết/cập nhật test, chạy PASS test phạm vi hẹp rồi mở rộng. Chỉ đánh dấu task Done khi test đã PASS và (nếu thuộc phạm vi) đã được `qa-reviewer` duyệt.
- **MUST** dùng `debug-flow` cho các lỗi có thể tái hiện trước khi đoán và sửa code bừa bãi.
- **MUST** hệ thống tự điều phối agent (agent hiện tại gọi `SendMessage` cho agent chuyên trách, không yêu cầu user tự gọi).

**NEVER (Tuyệt đối không):**
- **NEVER** bỏ qua playbook/skill đang bật để "code cho nhanh".
- **NEVER** tự ý thay đổi contract dùng chung, schema SQLite hoặc liên phase nếu chưa gọi `architect` thống nhất thiết kế.
- **NEVER** tự ý thay đổi prompt template/đầu ra AI nếu chưa gọi `prompt-engineer`; không tự quyết định tiêu chí nội dung YouTube nếu chưa qua `youtube-strategist`.
- **NEVER** đánh dấu Done nếu chưa chạy test, test chưa PASS (phải báo lệnh/kết quả), hoặc chưa giải quyết xong các lỗi do `qa-reviewer` chỉ ra.
- **NEVER** vượt ngưỡng số lượng truy vấn DB hoặc cấu hình đã quy định.

**BEFORE / AFTER (Trước và sau):**
- **BEFORE** sửa code: Đọc source, nơi gọi, test và thiết kế liên quan để xác minh hành vi thật.
- **BEFORE** thiết kế Backend/API: Đọc tài liệu convention liên quan trong repo.
- **AFTER** hoàn thành thay đổi code: Chạy kiểm thử liên quan, dùng `progress-tracker` cập nhật checklist.
- **AFTER** thay đổi lớn, contract hoặc schema: Gọi `qa-reviewer` review độc lập diff. Agent thực thi chỉ được kết thúc task (Done) khi `qa-reviewer` báo cáo không còn lỗi.

## 2. Tổng quan dự án
TubeChain là công cụ sản xuất video YouTube theo hướng ưu tiên chạy tại máy người dùng. Mã nguồn dùng Python + FastAPI (`app.py`), SQLite (`core/database.py`), giao diện tĩnh (`web/`), module pipeline (`modules/`) và pytest (`tests/`). FFmpeg dùng ghép video cơ bản. Trước khi giả định dependency, hãy xác minh từ file.

**Pipeline sản phẩm:** (1) Idea Engine, (2) Script Generator, (3) Voiceover Writer (chỉ tạo text), (4) Scene Illustrator, (5) Video Assembler, (6) SEO Optimizer. *Lưu ý: Luồng tổng hợp giọng nói Phase 3.5 hiện có là giai đoạn cũ, không lẫn lộn với Phase 3.*

## 3. Ràng buộc sản phẩm bắt buộc
- **Local first:** Giao diện/API cục bộ và SQLite; tuyệt đối không tự thêm cloud DB hay lưu trữ từ xa.
- **Dữ liệu lịch sử:** Chỉ gồm văn bản/metadata/chủ đề/embeddings; không giữ media video cũ.
- **Giới hạn:** Mỗi chuỗi Rabbit Hole tối đa **3 video**. Ngưỡng dedup: độ tương đồng `> 0.85` (chặn); `0.60–0.85` (cảnh báo); `< 0.60` (cho qua). Không tự ý sửa ngưỡng.
- **Dựng video:** Cho phép thêm transitions giữa ảnh tĩnh + audio hiện có; không Ken Burns, không animation phức tạp, không nhạc nền trừ khi yêu cầu rõ.
- **AI Provider:** Mọi thao tác AI chạy qua provider adapter hiện có. Không ghi cứng thông tin xác thực. Subagent chỉ hỗ trợ phát triển mã, không tham gia runtime tạo video.

## 4. Phân quyền Agent (Định tuyến)
Chỉ dùng subagent khi tạo giá trị; không ép thay đổi nhỏ qua nhiều agent. Trong runtime user, alias `opus` = Gemini 3.1 Pro, `sonnet` = Gemini 3.8 Flash (giữ nguyên alias trong frontmatter, không ghi đè provider ID).

| Agent | Bí danh | Trách nhiệm (Gọi qua SendMessage) |
|---|---|---|
| `youtube-strategist` | `opus` | Chiến lược nội dung, góc tiếp cận, hook, SEO, tiêu chí đánh giá. Không thiết kế contract/code. |
| `prompt-engineer` | `sonnet` | Thiết kế/đánh giá prompt template và cách kiểm thử đầu ra. Không gọi provider trực tiếp. |
| `architect` | `opus` | Thiết kế không tầm thường, data contract, schema/migration SQLite, quyết định liên phase. Không implement code. |
| `developer` | `sonnet` | Thực thi yêu cầu rõ ràng, làm TDD, tái sử dụng code, chạy test. |
| `qa-reviewer` | `opus` | Review độc lập diff, bảo mật, regression; báo lỗi thay vì sửa. |

## 5. An toàn và xử lý dữ liệu
- **KHÔNG** xóa/khởi tạo lại `data/tubechain.db` hay media người dùng để làm test pass. Dùng DB/media fixture tạm cho test.
- Thao tác phá hủy chỉ làm trong đúng phạm vi người dùng yêu cầu và sau khi kiểm tra target.
- **KHÔNG** commit, force-push, triển khai nếu người dùng chưa yêu cầu rõ.
- Hook trong `.claude/settings.json` là lớp phòng vệ hẹp, không thay thế sandbox. PreToolUse chặn lệnh phá hủy, PostToolUse nhắc nhở. Không tự sửa settings.local.json trừ khi có yêu cầu.

## 6. File của framework
- Subagent riêng dự án: `.claude/agents/`
- Skill có thể nạp: `.claude/skills/<skill-name>/SKILL.md`
- Cấu hình và script hook: `.claude/settings.json`, `.claude/hooks/`
- Template state dùng lại: `.claude/state/_template/`
- Tổng quan sản phẩm: `README.md`; mô tả chi tiết: `system-description.md`
- Bản đồ harness: `docs/agent/README.md`, `docs/agent/workflows.md`
