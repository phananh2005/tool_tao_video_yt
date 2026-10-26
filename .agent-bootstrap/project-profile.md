# Hồ sơ dự án — TubeChain

> **Cách dùng:** nguồn duy nhất cho mọi tham số cấu hình khi dùng mẫu trong `samples/`.
> Mỗi giá trị **MUST** có cột "Bằng chứng". Không xác định được → `[cần xác nhận]`.
> KHÔNG ghi secret, email, URL nội bộ, giá trị `.env`.

## 1. Dự án

| Mục | Giá trị | Bằng chứng |
|---|---|---|
| Tên | `TubeChain` | `README.md` dòng 1 |
| Loại | web-app (local-first) | `README.md`: "local-first tool for managing a YouTube video-production workflow" |
| Ngôn ngữ tài liệu sinh ra | `vi` | Quy tắc ngôn ngữ của prompt + CLAUDE.md hiện có |

## 2. Harness (AI agent đang dùng)

| Mục | Giá trị | Bằng chứng |
|---|---|---|
| Harness chính | Claude Code | `.claude/` đã có agents, skills, hooks, settings.json |
| Harness phụ | không có | |
| File hub chỉ dẫn | `CLAUDE.md` | Cấu trúc thực tế trong repo |
| Hỗ trợ agent/sub-agent | có | `.claude/agents/*.md` đã tồn tại |
| Hỗ trợ skill | có | `.claude/skills/*/SKILL.md` đã tồn tại |
| Hỗ trợ command do user gọi | có | `adapters/harness-matrix.md`: `.claude/commands/*.md` |
| Hỗ trợ hook | có | `.claude/settings.json` cấu hình PreToolUse, PostToolUse |
| Điều kiện nạp cấu hình | Mở tại gốc repo + workspace đã trust | `adapters/harness-matrix.md` |

## 3. Mức áp dụng

| Mục | Giá trị | Lý do |
|---|---|---|
| Mức | `standard` | Đội nhỏ (1–3 người), rủi ro trung bình (có DB SQLite, pipeline AI), đã có hạ tầng agent khá đầy đủ. Người dùng xác nhận. |

## 4. Tầng (layer) — mỗi tầng một dòng

| `id` | Thư mục | Ngôn ngữ | Lệnh build | Lệnh test | Lệnh lint | Tài liệu convention | Bằng chứng |
|---|---|---|---|---|---|---|---|
| (một tầng — không hậu tố) | `app.py`, `core/`, `modules/`, `web/`, `tests/` | Python | `pip install -r requirements.txt` | `python -m pytest` | không có | `CLAUDE.md`, `docs/agent/workflows.md` | `requirements.txt`, `README.md` |

> Repo một tầng (Python + FastAPI + SQLite + web tĩnh) → bỏ hậu tố tầng theo `adaptation-rules.md` §2.1.

## 5. Đường dẫn

| Ký hiệu | Giá trị | Bằng chứng |
|---|---|---|
| AGENT_DIR | `.claude` | Cấu trúc thực tế: `.claude/agents/`, `.claude/skills/` |
| KNOWLEDGE_DIR | `docs/agent/knowledge` | `docs/agent/` đã có — thêm `knowledge/` cho knowledge files |
| STATE_DIR | `.claude/state` | `.claude/state/_template/` đã tồn tại |
| HOOKS_DIR | `.claude/hooks` | `.claude/hooks/pre-tool-use.py` đã tồn tại |

## 6. Quyền sở hữu & đồng bộ

| Mục | Giá trị | Bằng chứng |
|---|---|---|
| File do generator/sync quản lý | không có | Không phát hiện cơ chế sync |
| Kênh tuỳ biến của dự án | `docs/agent/knowledge/` | Mọi tuỳ biến nội dung đi vào đây |
| Submodule | không có | Kiểm tra không có submodule |

## 7. State & bàn giao phiên

| Mục | Giá trị | Bằng chứng |
|---|---|---|
| Dùng state task | có | `.claude/state/_template/` đã tồn tại; CLAUDE.md yêu cầu skill `task-state-init` |
| Cách đặt DEV_ID | `local-dev` (đội nhỏ, một thư mục state) | Đội 1–3 người → gộp state, `adaptation-rules.md` §2.4 |
| State được commit hay gitignore | gitignore | `.gitignore`: `.claude/state/current-task.md`, `.claude/state/progress.md` |
| Tên command lưu / mở lại phiên | không tạo (mức standard, tuỳ) | `adoption-tiers.md`: command handoff/resume là "tuỳ" ở standard |

## 8. Git & review

| Mục | Giá trị | Bằng chứng |
|---|---|---|
| Nhánh mặc định | `main` | Git context: "Main branch: main" |
| Nhánh được bảo vệ | `main` | Người dùng xác nhận (2026-10-26) |
| Quy ước tên nhánh | không có quy ước thành văn | Quan sát: `new_ai_agent-3` |
| Quy ước commit | `type(scope): message` — chỉ commit/push khi người dùng yêu cầu | Người dùng xác nhận (2026-10-26); `git log`: `chore(docs):`, `feat:` |
| Nền tảng review | GitHub [suy luận] | Remote origin |

## 9. Playbook & hook

| Mục | Giá trị | Bằng chứng |
|---|---|---|
| Playbook đang bật | TDD (advisory via PostToolUse hook) | `.claude/hooks/post-tool-use-tdd-guard.py`, CLAUDE.md yêu cầu `tdd-playbook` |
| Runtime cho hook | Python | Hooks viết bằng Python (`.py`), repo Python |

## 10. CI

| Mục | Giá trị | Bằng chứng |
|---|---|---|
| Có CI trong repo | không thấy trong repo | Không có `.github/workflows/`, `.gitlab-ci.yml` |
| File CI | không có | |

## 11. Thiết kế, ADR, phi chức năng, tra cứu ngoài

| Mục | Giá trị | Bằng chứng |
|---|---|---|
| Có quy trình thiết kế trước khi code | có (qua architect agent) | CLAUDE.md §4: architect agent thiết kế, developer implement |
| Thư mục spec nghiệp vụ / thiết kế | `plans/` (lịch sử), `docs/` | `plans/*.md`, `docs/phase1_business_logic.md` |
| design-standards | không áp dụng (đội nhỏ, thiết kế qua architect agent) | |
| Thư mục ADR | không áp dụng | Đội nhỏ, quyết định ghi trong state/decisions-log |
| Tầng có DB/ORM | có (SQLite trực tiếp, không ORM) | `core/database.py`: `sqlite3.connect()` |
| non-functional-standards | `docs/agent/knowledge/non-functional-standards.md` | Tạo mới theo `adaptation-rules.md` §2.3 |
| Nguồn tra cứu ngoài repo | không có | Không có `.mcp.json`, không có wiki config |
| external-knowledge | không áp dụng | |

## 12. Quyết định thích ứng

> Mỗi lần mẫu được điều chỉnh/bỏ cho khớp repo — ghi 1 dòng.

| Ngày | Tín hiệu | Bằng chứng | Điều chỉnh | Lý do | Đảo ngược bằng |
|---|---|---|---|---|---|
| 2026-10-23 | Một tầng duy nhất | `app.py`, `core/`, `modules/`, `web/` đều Python | Bỏ hậu tố tầng: `developer` thay vì `developer-backend`; bỏ routing theo tầng | Repo chỉ có 1 tầng Python, §2.1 | Thêm hậu tố nếu repo thêm tầng |
| 2026-10-23 | Đội 1–3 người | Người dùng xác nhận | Gộp code-reviewer vào skill `code-review`; một thư mục state (không namespace) | §2.4: đội nhỏ | Tách namespace khi thêm dev |
| 2026-10-23 | Đã có 5 agents chuyên trách riêng TubeChain | CLAUDE.md §4, `.claude/agents/` | Giữ nguyên 5 agents đã có (architect, developer, prompt-engineer, qa-reviewer, youtube-strategist) thay vì gộp | Đã chạy tốt, phù hợp pipeline 6 phase phức tạp | Gộp agents nếu người dùng thấy thừa |
| 2026-10-23 | Có DB (SQLite) nhưng không dùng ORM | `core/database.py`: `sqlite3.connect()` | Tạo non-functional-standards nhưng bỏ phần ORM/lazy-load; giữ phần phân trang, ngưỡng truy vấn, vòng lặp DB | §2.3 | |
| 2026-10-23 | Không có CI trong repo | Không có file CI | Không tạo hook lặp CI; ưu tiên hook harness + checklist | §2.2 | Thêm CI hook khi có CI |
| 2026-10-23 | Không có nguồn tra cứu ngoài | Không có `.mcp.json` | Bỏ `external-knowledge.md`, bỏ hook đầu phiên nhắc nguồn ngoài | §2.5 | Thêm khi có nguồn ngoài |
| 2026-10-23 | Hooks viết Python, repo Python | `.claude/hooks/*.py` | Giữ hook runtime Python; không chuyển sang Node | §4 stack-hints | |
| 2026-10-23 | Không có lint/format/static analysis | Không có config | Không tạo cổng lint "sau sửa" | §2.2 | Thêm khi bật lint |
| 2026-10-23 | Prototype/tool nội bộ | README: "local-first tool" | Mức standard thay vì full; không playbook 4 lớp enforcement | §2.1 | Nâng full khi cần |

## 13. Còn chờ xác nhận

- [x] Manifest dependency: Đã tạo `requirements.txt` chuẩn cho dự án.
- [x] Ngưỡng số truy vấn SQLite: Detail ≤ 3, List ≤ 4, Write ≤ 6 — người dùng xác nhận (2026-10-26)
- [x] Quy ước commit: `type(scope): message` — chỉ commit/push khi người dùng yêu cầu rõ — người dùng xác nhận (2026-10-26)
- [x] Nhánh được bảo vệ: `main` — người dùng xác nhận (2026-10-26)
