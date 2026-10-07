# Bộ hướng dẫn Agent của TubeChain — Bản đồ repository

**Trạng thái:** khảo sát repository chỉ-đọc, 2026-10-07
**Phạm vi:** hướng dẫn Claude Code phục vụ phát triển và cấu trúc ứng dụng quan sát được. Tài liệu này ghi nhận bằng chứng trong repo, không chứng nhận hạ tầng bên ngoài hoặc hành vi runtime ngoài các nguồn đã dẫn.

## Bản đồ repository

| Khu vực | Bằng chứng | Vai trò quan sát được |
|---|---|---|
| Entrypoint ứng dụng/API | `app.py` | Ứng dụng FastAPI; chạy trực tiếp thì bind `127.0.0.1:8000`. Mount giao diện tĩnh `web/` và thư mục `data/`. |
| Contract | `core/contracts.py` | Dataclass Python và interface provider cho idea, script, voiceover, scene asset và thao tác AI provider. |
| Lưu trữ | `core/database.py` | Schema SQLite và truy cập dữ liệu. `DB_PATH` trỏ tới `data/tubechain.db`. |
| Module pipeline | `modules/idea_engine/`, `modules/script_gen/`, `modules/voiceover/`, `modules/scene_illustrator/`, `modules/video_assembler/`, `modules/seo_optimizer/` | Logic sinh nội dung và lắp ráp theo từng phase. |
| Frontend | `web/` | Asset web tĩnh được FastAPI phục vụ. |
| Test | `tests/` | Test pytest cho logic, database, frontend tĩnh và golden path. `tests/test_claude_hooks.py` kiểm thử hook. |
| Tài liệu sản phẩm | `README.md`, `system-description.md`, `docs/phase1_business_logic.md`, `plans/` | Tổng quan người dùng, thiết kế và kế hoạch tính năng/lịch sử. Coi `plans/` là tài liệu lịch sử cho tới khi đối chiếu với code hiện tại. |

## Stack và bằng chứng xác minh

| Hạng mục | Kết quả | Trạng thái bằng chứng |
|---|---|---|
| Ngôn ngữ/runtime | Python | Quan sát trong `app.py`, `core/`, `modules/`, `tests/`. |
| Web framework | FastAPI với model request Pydantic | Quan sát import và `FastAPI(...)` trong `app.py`; phần chạy trực tiếp dùng Uvicorn. |
| Lưu trữ | SQLite và filesystem cục bộ | Quan sát trong `core/database.py`, `app.py`, `.gitignore`. |
| Giao diện | HTML/CSS/JavaScript tĩnh | Quan sát từ `web/` và README; inventory gốc không có package frontend riêng. |
| Lắp ráp media | Gọi subprocess FFmpeg | Quan sát trong `modules/video_assembler/engine.py`; voice synthesis cũng dùng subprocess. |
| Tương tác AI | Tự động hóa Gemini web UI qua Playwright | Quan sát trong `modules/idea_engine/adapter.py`: mở Chrome profile lâu dài và truy cập Gemini website. UI/storage cục bộ **không có nghĩa** toàn bộ xử lý AI offline/cục bộ. |
| Kiểm thử | pytest | Quan sát file test và lệnh đã ghi `python -m pytest` trong README. |
| Manifest dependency | Chưa tìm thấy ở root | Inventory đã kiểm tra không có `requirements.txt`, `pyproject.toml` hoặc `package.json` tại root. Không suy đoán lệnh cài đặt từ sự vắng mặt này. |
| Lint/type-check/build | Chưa xác minh | Không thấy cấu hình/lệnh gốc phù hợp trong inventory. |
| Cấu hình CI | Không tìm thấy trong phần repository đã khảo sát | Không thấy thư mục `.github/`. Điều này không chứng minh không có CI phía hosting. |
| Migration DB | Có logic migration trong `core/database.py` | Có đường cập nhật schema cho cờ tổng hợp voiceover; chưa nhận diện framework migration tổng quát. |

## Ràng buộc sản phẩm liên quan đến công việc agent

`CLAUDE.md` ở root ghi các ràng buộc và định tuyến hiện tại. Tóm tắt:

- FastAPI UI/API, SQLite và file cục bộ; không thêm cloud DB/triển khai từ xa nếu chưa được duyệt.
- Lịch sử video cũ chỉ gồm văn bản/metadata/topics/embeddings, không lưu media cũ.
- Rabbit Hole tối đa ba video; dedup `>0.85` chặn, `0.60–0.85` cảnh báo, `<0.60` cho qua.
- Phase 3 tạo văn bản voiceover. Repo còn Phase 3.5 tổng hợp giọng nói cũ (`modules/voiceover/synthesizer.py`, route trong `app.py`); giữ riêng hai giai đoạn này.
- Video render đơn giản bằng cách ghép ảnh tĩnh tuần tự, theo hỗ trợ audio hiện có.
- Ranh giới adapter được biểu diễn bởi `AIProviderContract` trong `core/contracts.py`; không khẳng định có chế độ API/thủ công nếu chưa thấy implementation.

## Inventory Claude Code hiện có

| Khả năng | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Hub chỉ dẫn dự án | Có | `CLAUDE.md` ghi constraint, liên kết skill, định tuyến và workflow. |
| Subagent | Có (5) | `.claude/agents/`: `youtube-strategist`, `prompt-engineer`, `architect`, `developer`, `qa-reviewer`. Frontmatter dùng alias `opus`/`sonnet`; tài liệu repo ghi runtime người dùng ánh xạ chúng sang Gemini 3.1 Pro và Gemini 3.8 Flash. |
| Skill | Có (5) | `.claude/skills/<name>/SKILL.md`: task-state-init, progress-tracker, reuse-scan, debug-flow, tdd-playbook. |
| Template trạng thái task | Có | `.claude/state/_template/`: current-task, progress, decisions-log. Không thấy file state task đang chạy trong inventory khảo sát. |
| Hook | Có, đang bật trong project settings | `.claude/settings.json` đăng ký PreToolUse cho `Bash`, PostToolUse cho `Write|Edit`; script trong `.claude/hooks/`. Đây là kiểm tra hẹp, không phải sandbox. |
| Test hook | Có | `tests/test_claude_hooks.py` bao phủ một số lệnh force-push/root-delete/DB-delete, lệnh an toàn, payload và lời nhắc advisory. |
| Settings cấp local/người dùng | Có nhưng không khảo sát | Bỏ qua `.claude/settings.local.json`; không đọc hoặc chép giá trị bên trong. |
| Slash command / workflow tùy chỉnh / MCP | Chưa tìm thấy trong inventory dự án đã xem | Không thấy `.claude/commands/`, `.claude/workflows/` hay MCP config. Chưa cần thêm khi chưa có nhu cầu lặp lại cụ thể và phạm vi được duyệt. |

### Hạn chế harness cần lưu ý

Đây là phát hiện review; lần bootstrap này không đổi cấu hình đang hoạt động:

1. **Phạm vi shell:** hook lệnh nguy hiểm chỉ đăng ký cho `Bash`. Lệnh qua tool `PowerShell` không khớp đăng ký này. Không khẳng định hook bảo vệ mọi shell hay biến thể lệnh gián tiếp.
2. **Giả định working directory:** hook dùng đường dẫn script tương đối với project. Trước khi tin cậy trong worktree hoặc CWD khác, cần xác minh cách chạy; lần này không đổi path/config.
3. **Trạng thái staged/worktree:** lúc khảo sát repo có nhiều thay đổi staged và untracked. Worktree tạo từ commit cũ có thể không chứa agent/hook/tài liệu chưa commit. Xác nhận checkout hiện tại trước khi giả định harness khả dụng.
4. **Ngôn ngữ:** phần lớn hướng dẫn agent/skill bằng tiếng Anh trong khi template task state bằng tiếng Việt. Đây là điểm chưa thống nhất về trải nghiệm, không phải lỗi runtime; chưa sửa template.
5. **Kế hoạch lịch sử:** `plans/` và helper có thể nhắc hệ agent bảy vai trò cũ. Coi là lịch sử trừ khi task yêu cầu cập nhật; lần khảo sát này không sửa.
6. **Chỉ dẫn và enforcement:** Markdown chỉ hướng dẫn, không phải ranh giới bảo mật cứng. PostToolUse chỉ nhắc sau edit, không hoàn tác/ngăn edit. PreToolUse chỉ xét event/tool đã đăng ký và mẫu lệnh nhận diện được.

## Thứ tự ưu tiên nguồn sự thật

Khi làm việc trong dự án, áp dụng thứ tự thực tế:

1. Yêu cầu rõ ràng và ranh giới phê duyệt của người dùng.
2. `CLAUDE.md` hiện tại cùng yêu cầu bảo mật/quyền riêng tư áp dụng.
3. Mã nguồn và test hiện hành để xác định hành vi thật.
4. Tài liệu sản phẩm/thiết kế và kế hoạch hiện hành, đối chiếu với code.
5. Hướng dẫn agent/skill và mặc định chung của công cụ.

Nếu tài liệu khác implementation, báo điểm lệch và không tự đổi hành vi sản phẩm khi chưa được duyệt.

## Quyền sở hữu và phần không làm

- Đợt khảo sát này chỉ bổ sung tài liệu agent; không đổi code ứng dụng, database/dữ liệu, dependency, hook/settings đang chạy, CI, quyền hoặc runtime config.
- Không commit, stage, push, publish hay deploy trong phạm vi bootstrap.
- Không đọc hoặc chép `.env`, local settings, browser profile, database, log, credential hoặc dữ liệu runtime/người dùng vào tài liệu.
