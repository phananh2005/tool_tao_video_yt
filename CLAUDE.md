# TubeChain — Hướng dẫn dự án cho Claude Code

## 1. Hợp đồng hành vi AI (Tối cao)
Các quy tắc MUST / NEVER / BEFORE / AFTER dưới đây đè lên mọi hành vi mặc định và phải được tuân thủ tuyệt đối:

**MUST (Bắt buộc):**
- **MUST** khởi tạo hoặc tiếp tục task nhiều bước bằng skill `task-state-init`, tự động phân rã thành các bước vi mô (Atomic Steps, mỗi bước ≤ 50 dòng code/1 hàm).
- **MUST** chạy `reuse-scan` và thu thập code mẫu tương đương (Pattern Harvesting) trong repo trước khi viết code mới để làm chuẩn định dạng/xử lý lỗi.
- **MUST** làm theo `tdd-playbook`: viết/cập nhật test trước, chạy test, nếu FAIL tự động đọc stacktrace và tự sửa (Reflection Loop, tối đa 5 lần). Chỉ đánh dấu task Done khi test đã PASS và đã qua vòng lặp Maker-Critic với `qa-reviewer`.
- **MUST** chạy `code-review` nhanh 5 chiều trước khi commit; khi có thay đổi quy ước hoặc hành vi lặp lại, dùng `workflow-adapt` để cập nhật hạ tầng.
- **MUST** tự động kích hoạt vòng lặp đối kháng Maker - Critic: `developer` viết code xong BẮT BUỘC gọi `qa-reviewer` qua `SendMessage` để bắt lỗi tiềm ẩn/edge cases trước khi coi là hoàn tất.
- **MUST** dùng `debug-flow` cho các lỗi có thể tái hiện trước khi đoán và sửa code bừa bãi.
- **MUST** hệ thống tự điều phối agent (agent hiện tại gọi `SendMessage` cho agent chuyên trách, không yêu cầu user tự gọi).
- **MUST** cô lập ngữ cảnh (Context Isolation): các tác vụ khảo sát rộng, đọc log dài hoặc tìm kiếm nhiều file phải đẩy vào Subagent (`Agent` tool) để giữ context hội thoại chính sạch (< 50k tokens).

**NEVER (Tuyệt đối không):**
- **NEVER** bỏ qua playbook/skill đang bật để "code cho nhanh".
- **NEVER** viết một khối code lớn (> 50 dòng) mà không chia nhỏ thành các bước kiểm thử vi mô.
- **NEVER** dừng lại hỏi người dùng khi gặp lỗi test nếu chưa tự chạy vòng lặp reflection sửa lỗi (tối thiểu 3 lần thử).
- **NEVER** tự ý thay đổi contract dùng chung, schema SQLite hoặc liên phase nếu chưa gọi `architect` thống nhất thiết kế.
- **NEVER** tự ý thay đổi prompt template/đầu ra AI nếu chưa gọi `prompt-engineer`; không tự quyết định tiêu chí nội dung YouTube nếu chưa qua `youtube-strategist`.
- **NEVER** đánh dấu Done nếu chưa chạy test, test chưa PASS (phải báo lệnh/kết quả), hoặc chưa giải quyết xong các lỗi do `qa-reviewer` chỉ ra.
- **NEVER** vượt ngưỡng số lượng truy vấn DB hoặc cấu hình đã quy định.

**BEFORE / AFTER (Trước và sau):**
- **BEFORE** sửa code: Đọc source, nơi gọi, test và thiết kế liên quan để xác minh hành vi thật.
- **BEFORE** thiết kế Backend/API: Đọc tài liệu convention liên quan trong repo.
- **AFTER** hoàn thành thay đổi code: Chạy kiểm thử liên quan, dùng `progress-tracker` cập nhật checklist.
- **AFTER** thay đổi lớn, contract hoặc schema: Gọi `qa-reviewer` review độc lập diff. Agent thực thi chỉ được kết thúc task (Done) khi `qa-reviewer` báo cáo không còn lỗi.

## 1.1 Cơ chế thực thi Agentic nâng cao (Tự động hóa sâu)
Để bù đắp suy luận nông của model Flash và đảm bảo output đạt chất lượng cao:
1. **Phân rã siêu nhỏ (Autonomous Micro-Tasking):** Mọi task lập trình phải được chia thành các bước con không quá 50 dòng code/1 hàm. Làm tuần tự từng bước kèm unit test độc lập.
2. **Khai thác code mẫu (Pattern Harvesting):** Luôn đọc ít nhất 1 file tương đương trong repo làm chuẩn few-shot trước khi tạo code mới.
3. **Đối kháng Maker - Critic:** `developer` bắt buộc gửi diff cho `qa-reviewer` qua `SendMessage` với yêu cầu vạch lá tìm sâu ít nhất 2 edge cases/lỗi tiềm ẩn. `developer` tự sửa đến khi sạch lỗi.
4. **Vòng lặp tự phản hồi (Automated Reflection Loop):** Lỗi test phải được đọc trực tiếp từ output terminal và tự động sửa tối đa 5 lần trước khi báo cáo.
5. **Cô lập ngữ cảnh (Context Isolation):** Khảo sát rộng hoặc đọc log dài phải chạy qua subagent để giữ context chính dưới 50k tokens.

## 2. Tổng quan dự án
TubeChain là công cụ sản xuất video YouTube theo hướng ưu tiên chạy tại máy người dùng. Mã nguồn dùng Python + FastAPI (`app.py`), SQLite (`core/database.py`), giao diện tĩnh (`web/`), module pipeline (`modules/`) và pytest (`tests/`). FFmpeg dùng ghép video cơ bản. Trước khi giả định dependency, hãy xác minh từ file.

**Pipeline sản phẩm:** (1) Idea Engine, (2) Script Generator, (3) Voiceover Writer (sinh kịch bản lời thoại), (3.5) Audio Synthesizer (tạo file âm thanh qua TTS), (4) Scene Illustrator, (5) Video Assembler, (6) SEO Optimizer. *Lưu ý: Phase 3 và Phase 3.5 là 2 bước nối tiếp nhau trong cùng pipeline; AI cần phân biệt rõ sửa text (engine.py) hay sửa audio (synthesizer.py).*

## 3. Ràng buộc sản phẩm bắt buộc
- **Local first:** Giao diện/API cục bộ và SQLite; tuyệt đối không tự thêm cloud DB hay lưu trữ từ xa.
- **Dữ liệu lịch sử:** Chỉ gồm văn bản/metadata/chủ đề/embeddings; không giữ media video cũ.
- **Giới hạn:** Mỗi chuỗi Rabbit Hole tối đa **3 video**. Ngưỡng dedup: độ tương đồng `> 0.85` (chặn); `0.60–0.85` (cảnh báo); `< 0.60` (cho qua). Không tự ý sửa ngưỡng.
- **Dựng video:** Cho phép thêm transitions giữa ảnh tĩnh + audio hiện có; không Ken Burns, không animation phức tạp, không nhạc nền trừ khi yêu cầu rõ.
- **AI Provider:** Mọi thao tác AI chạy qua provider adapter hiện có. Không ghi cứng thông tin xác thực. Subagent chỉ hỗ trợ phát triển mã, không tham gia runtime tạo video.

## 4. Phân quyền Agent (Định tuyến)
Với các sửa đổi cục bộ (fix bug, refactor code), agent hiện tại tự xử lý để tiết kiệm thời gian. Tuy nhiên, **TUYỆT ĐỐI TUÂN THỦ HỢP ĐỒNG TỐI CAO**: bất cứ thay đổi nào chạm đến schema, contract, prompt, hay chiến lược (dù nhỏ đến đâu) đều bắt buộc phải gọi agent chuyên trách tương ứng qua `SendMessage`. 

Trong runtime user, alias `opus` = Gemini 3.1 Pro, `sonnet` = Gemini 3.8 Flash (giữ nguyên alias trong frontmatter, không ghi đè provider ID).

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
- Skill có thể nạp: `.claude/skills/<skill-name>/SKILL.md` (gồm: `task-state-init`, `progress-tracker`, `reuse-scan`, `tdd-playbook`, `debug-flow`, `code-review`, `workflow-adapt`)
- Cấu hình và script hook: `.claude/settings.json`, `.claude/hooks/`
- Template state dùng lại: `.claude/state/_template/`
- Chuẩn phi chức năng & Thích ứng: `docs/agent/knowledge/non-functional-standards.md`, `docs/agent/knowledge/adaptation-rules.md`
- Tổng quan sản phẩm: `README.md`; mô tả chi tiết: `system-description.md`
- Bản đồ harness: `docs/agent/README.md`, `docs/agent/workflows.md`
