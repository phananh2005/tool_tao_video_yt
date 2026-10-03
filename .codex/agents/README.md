# TubeChain — Sub-Agent README

## Mục đích

Bộ 7 agent này chỉ dùng để **phát triển code** cho TubeChain. Chúng **KHÔNG** tham gia vào quá trình runtime tạo video. Khi tool chạy, pipeline thực thi như code Python bình thường.

## Danh sách Agent

| # | Agent | Vùng sở hữu | Quyền hạn | Khi nào dùng |
|---|-------|-------------|-----------|--------------|
| 1 | **planner** | `plans/` | Chỉ đọc code + ghi plan .md | **Luôn chạy đầu tiên** — phân tích yêu cầu, xuất kế hoạch cho các agent khác |
| 2 | **db-architect** | `db.py`, `embeddings.py`, `config.json`, `providers/` (contract) | Đọc/ghi contract + schema; sqlite3 chỉ SELECT | Thiết kế schema, data contract, provider contract, state machine |
| 3 | **idea-engine-coder** | `modules/idea_engine/` | Ghi code + chạy test Phase 1 | Code brainstorm, dedup, Rabbit Hole, playlist, graveyard |
| 4 | **content-coder** | `modules/script_gen/`, `modules/voiceover/`, `modules/seo_optimizer/`, `prompts/` | Ghi code + chạy test Phase 2/3/6 | Code script, voiceover text (không TTS), SEO, prompt templates |
| 5 | **media-coder** | `modules/scene_illustrator/`, `modules/video_assembler/` | Ghi code + chạy test + FFmpeg/ffprobe an toàn | Code scene breakdown, image prompts, video assembly |
| 6 | **web-coder** | `app.py`, `web/` | Ghi code + chạy dev server + test API | Backend endpoints + frontend 7 màn hình |
| 7 | **qa-test-engineer** | `tests/` | Ghi test + chạy pytest + ffprobe verify | Test toàn bộ: unit, integration, golden, E2E |

## Workflow đề xuất

```
Bước 0: planner (LUÔN CHẠY ĐẦU TIÊN)
  → Phân tích yêu cầu user, xuất file kế hoạch .md trong plans/.
  → User duyệt kế hoạch trước khi tiếp tục.

Bước 1: db-architect
  → Thiết kế schema SQLite, data contract (6 JSON), provider adapter contract,
    embeddings format, state machine, config schema — theo kế hoạch.

Bước 2: idea-engine-coder + content-coder + media-coder (SONG SONG)
  → Mỗi agent implement modules trong phạm vi sở hữu.
  → Đều dùng contract từ db-architect.

Bước 3: web-coder
  → Tích hợp backend API + frontend cho toàn bộ modules.
  → Gọi modules qua contract, không chứa logic pipeline.

Bước 4: qa-test-engineer (XUYÊN SUỐT)
  → Chạy sau mỗi milestone.
  → Test ràng buộc cứng, golden test, E2E.
```

## Stack target

| Component | Technology |
|-----------|-----------|
| Backend | Python (Flask hoặc FastAPI) |
| Frontend | HTML/CSS/JS thuần hoặc framework nhẹ (Vue/Svelte) |
| Database | SQLite (`data/tubechain.db`) |
| Vector search | `data/embeddings.json` + cosine similarity in-memory |
| Video | FFmpeg (ghép ảnh tuần tự, 1080p H.264) |
| AI Text | Qua provider adapter — MODE_API hoặc MODE_MANUAL |
| AI Image | Qua provider adapter — MODE_API hoặc MODE_MANUAL |
| Test | pytest |

## Ràng buộc cứng

1. **100% local** — không cloud, không deploy, không database ngoài SQLite.
2. **Video cũ chỉ lưu dữ liệu** — title, transcript, topics, embeddings; không lưu/xử lý media.
3. **Chuỗi Rabbit Hole đúng 3 video**; nhóm liên quan **tối đa 3 video**.
4. **Không TTS** — Phase 3 chỉ xuất text; audio luôn từ user import.
5. **Dựng video đơn giản** — ghép ảnh tuần tự; không Ken Burns, transitions, animation, nhạc nền.
6. **Provider adapter 2 chế độ** — MODE_API + MODE_MANUAL; đổi qua config.
7. **Ngưỡng dedup**: >85% chặn, 60-85% cảnh báo, <60% cho phép (config).

## Quy tắc an toàn

- **Không chạy lệnh nguy hiểm**: rm -rf, ghi đè ngoài phạm vi.
- **Không bypass sandbox/approval** của Codex.
- **Không xóa dữ liệu**: tubechain.db, embeddings.json, projects/.
- **Không sửa secret/env thật** nếu không được yêu cầu.
- **Không DROP TABLE** hoặc xóa bảng quan trọng.
- **Không cài dependency** chưa được duyệt.
- **Không thay đổi kiến trúc lớn** (đổi DB, thêm phase, thêm TTS, thêm hiệu ứng).
- **Không ghi ngoài vùng sở hữu** — xung đột escalate cho db-architect.

## Sandbox/Approval khuyến nghị

| Agent | Codex Mode | Lý do |
|-------|-----------|-------|
| db-architect | `suggest` hoặc `auto-edit` | Chỉ ghi contract/schema, an toàn |
| idea-engine-coder | `auto-edit` | Phạm vi ghi hẹp, chỉ 1 module |
| content-coder | `auto-edit` | Phạm vi ghi hẹp, 3 module + prompts |
| media-coder | `suggest` | Chạy FFmpeg — nên review lệnh trước |
| web-coder | `auto-edit` | Phạm vi ghi rõ ràng |
| qa-test-engineer | `auto-edit` | Chỉ ghi test, chạy pytest + ffprobe |

## Cách chỉnh quyền/scope

1. Mở file `.codex/agents/<agent-name>.md`.
2. Sửa phần **File-write scope** để thêm/bớt thư mục.
3. Sửa phần **Safe command allowlist** để thêm/bớt lệnh.
4. Mọi thay đổi phải đảm bảo agent không giẫm chân agent khác.

## Gợi ý prompt sử dụng

```bash
# LUÔN bắt đầu bằng planner
codex "Dùng agent planner: tôi muốn implement toàn bộ Phase 1 Idea Engine"
# → Planner xuất kế hoạch .md → user duyệt → chạy từng agent theo plan

# Khởi tạo schema/contract (theo kế hoạch)
codex "Dùng agent db-architect: thiết kế schema SQLite cho tất cả bảng, tạo data contract JSON cho 6 phase, và định nghĩa provider adapter contract"

# Implement Phase 1
codex "Dùng agent idea-engine-coder: implement Topic Cross-Pollination với 6 content pillars"

# Implement Phase 2
codex "Dùng agent content-coder: implement Script Generator với timing chuẩn Hook/Intro/Body/Climax/CTA"

# Implement Phase 4+5
codex "Dùng agent media-coder: implement Scene Breakdown chia kịch bản thành scenes 10-30 giây"

# Tích hợp
codex "Dùng agent web-coder: tạo backend endpoint POST /api/phase1/brainstorm và GET /api/phase1/ideas"

# Test
codex "Dùng agent qa-test-engineer: viết test cho Angle Deduplication Filter phủ 3 ngưỡng + edge case embeddings rỗng"

# E2E
codex "Dùng agent qa-test-engineer: viết E2E golden test từ chủ đề thô đến MP4 + MetadataJSON dùng mock provider"
```
