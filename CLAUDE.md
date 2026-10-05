# TubeChain — Agent Registry

## Tóm tắt dự án

TubeChain là tool 100% local (web UI local) tự động hóa sản xuất video YouTube qua pipeline 6 phase tuần tự:

1. **Idea Engine** — brainstorm, chống trùng lặp, Rabbit Hole series
2. **Script Generator** — kịch bản JSON có cấu trúc timing chuẩn
3. **Voiceover Writer** — chuyển outline → spoken text (KHÔNG có TTS)
4. **Scene Illustrator** — chia scene, sinh prompt ảnh, lấy ảnh (API hoặc thủ công)
5. **Video Assembler** — ghép ảnh tuần tự bằng FFmpeg, đơn giản tuyệt đối
6. **SEO Optimizer** — title/description/tags/chapters/thumbnail concept

## Ràng buộc cứng

| # | Ràng buộc |
|---|-----------|
| 1 | 100% local — không cloud, không deploy, không DB ngoài SQLite |
| 2 | Video cũ chỉ lưu **dữ liệu** (title, transcript, topics, embeddings) — không lưu/xử lý media |
| 3 | Chuỗi Rabbit Hole đúng **3 video**; mọi nhóm video liên quan **tối đa 3** |
| 4 | Ngưỡng dedup: >85% chặn, 60-85% cảnh báo, <60% cho phép (hằng số config) |
| 5 | Tool **không có TTS** — Phase 3 chỉ xuất text |
| 6 | Dựng video **đơn giản** — ghép ảnh tuần tự, không Ken Burns/transitions/animation/nhạc nền |
| 7 | Mọi lời gọi AI phải qua **provider adapter** (MODE_API / MODE_MANUAL) |
| 8 | Các agent chỉ dùng để **phát triển code**, không tham gia runtime tạo video |

## Stack

- Backend: Python (Flask/FastAPI)
- Frontend: HTML/CSS/JS thuần hoặc framework nhẹ
- Database: SQLite (`data/tubechain.db`)
- Vector search: `data/embeddings.json` + cosine similarity in-memory
- Video: FFmpeg
- AI Text/Image: qua provider adapter, chưa xác định nguồn cụ thể
- Test: pytest

## Danh sách Agent

| Agent | Sở hữu | Khi nào dùng |
|-------|--------|--------------|
| **planner** | `plans/` | **Luôn chạy đầu tiên** — phân tích yêu cầu, xuất kế hoạch .md cho các agent khác |
| **db-architect** | Data contract, schema SQLite, config, provider contract | Thiết kế schema, contract giữa các phase, state machine |
| **idea-engine-coder** | `modules/idea_engine/` | Code Phase 1: brainstorm, dedup, Rabbit Hole, playlist, graveyard |
| **content-coder** | `modules/script_gen/`, `modules/voiceover/`, `modules/seo_optimizer/`, `prompts/` | Code Phase 2 + 3 + 6: script, voiceover text, SEO metadata |
| **media-coder** | `modules/scene_illustrator/`, `modules/video_assembler/` | Code Phase 4 + 5: chia scene, sinh prompt ảnh, ghép video FFmpeg |
| **web-coder** | `app.py`, `web/` | Backend API + frontend 7 màn hình |
| **qa-test-engineer** | `tests/` | Test toàn bộ: unit, integration, golden test, E2E |

## Quy tắc Handoff

1. **TUYỆT ĐỐI KHÔNG TỰ TRẢ LỜI CODE/FIX TRỰC TIẾP**. Mọi task đều phải chạy qua workflow bắt buộc: `planner` → `db-architect` (nếu có đổi schema/contract) → Coder tương ứng (`media-coder`, `web-coder`...) → `qa-test-engineer`.
2. **Giao tiếp qua data contract** — mọi agent dùng contract do `db-architect` định nghĩa. Không tự chế format riêng.
3. **Contract bao gồm**: IdeaJSON, ScriptJSON, VoiceoverJSON, SceneAssets, AudioTrack, MetadataJSON.
4. **Quy trình**: `planner` phân tích yêu cầu → `db-architect` tạo contract → các coder agent implement theo contract → `qa-test-engineer` test theo contract.
5. **Xung đột contract**: nếu agent cần thay đổi contract → escalate cho `db-architect`, không tự sửa.
6. **Không agent nào ghi file ngoài vùng sở hữu** — vi phạm phải escalate.

## Workflow đề xuất

```
planner (luôn chạy đầu tiên — xuất kế hoạch .md)
    ↓
db-architect (thiết kế contract/schema theo kế hoạch)
    ↓
idea-engine-coder ─┐
content-coder      ├── song song
media-coder        ┘
    ↓
web-coder (tích hợp)
    ↓
qa-test-engineer (xuyên suốt, chạy sau mỗi milestone)
```

## Gọi agent trong Claude Code

```bash
# Luôn bắt đầu bằng planner
claude "Dùng agent planner: tôi muốn implement Phase 1 Idea Engine hoàn chỉnh"
# Sau khi duyệt kế hoạch, chạy từng agent theo plan
claude "Dùng agent db-architect để thiết kế schema SQLite cho bảng projects và ideas"
claude "Dùng agent idea-engine-coder để implement Topic Cross-Pollination"
claude "Dùng agent qa-test-engineer để viết test cho dedup filter 3 ngưỡng"
```
