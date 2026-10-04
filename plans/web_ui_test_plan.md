# Kế hoạch Kiểm thử & Hoàn thiện Giao diện Web (QA & Test Plan) — v2

## 1. Mục tiêu

Đảm bảo **toàn bộ luồng** Phase 1 → Phase 6 hoạt động đúng, giao tiếp giữa
các engine/module thông suốt, dữ liệu SQLite nhất quán, và **frontend không có
lỗi cú pháp** khiến UI crash.

## 2. Ràng buộc môi trường

| Yếu tố | Thực tế |
|---------|--------|
| Network | **Offline** — không pip install được |
| `httpx` / `httpx2` | **Chưa cài** → `TestClient` của FastAPI/Starlette không dùng được |
| `pytest-mock` | **Chưa cài** → dùng `unittest.mock` thay thế |
| Có sẵn | `pytest`, `sqlite3`, `unittest.mock`, `dataclasses`, `json` |

> **Hệ quả:** Không viết test gọi trực tiếp API qua TestClient. Thay vào đó
> test ở **tầng Engine + Database + Contract** (nơi chứa toàn bộ business logic).

## 3. Chiến lược Kiểm thử

### 3.1. Layer 1 — Unit Test Contracts & Database

File: `tests/test_contracts_db.py`

- Tạo / đọc / ghi tất cả bảng: `projects`, `ideas`, `scripts`, `voiceovers`, `assets`, `seo_metadata`.
- Kiểm tra ràng buộc UNIQUE (`scripts.idea_id`, `voiceovers.script_id`, …).
- Kiểm tra `get_or_create_project` idempotent.
- Kiểm tra `get_project_ideas` trả đúng format `IdeaJSON`.
- Kiểm tra `get_ready_to_render_projects_with_audio` chỉ trả project có `audio_path`.
- Kiểm tra `delete_project_media` xóa folder nhưng **giữ nguyên DB**.

### 3.2. Layer 2 — Unit Test từng Engine (Mock Adapter)

File: `tests/test_idea_engine.py` (đã có — giữ nguyên)

File: `tests/test_engines_unit.py` (mới)

- **IdeaEngine**: `generate_ideas`, `dedup_filter` 3 ngưỡng, `enforce_rabbit_hole` max 3.
- **ScriptGeneratorEngine**: `generate_full_script` trả đúng `ScriptJSON` contract.
- **VoiceoverEngine**: `generate_full_voiceover` trả `VoiceoverJSON`.
- **VoiceSynthesizer**: mock `asyncio.run` + `get_audio_duration`, verify output paths.
- **SceneIllustratorEngine**: `generate_assets` trả `AssetJSON`.
- **VideoAssemblerEngine**: `render_video_stream` yield SSE messages, kết thúc `[DONE]`.
- **SEOOptimizerEngine**: `format_upload_info` trả dict có key `title`, `description`, `tags`, `thumbnail_concept`.

### 3.3. Layer 3 — Integration Test (Golden Path qua Engine)

File: `tests/test_golden_path.py`

Luồng xuyên suốt **không** qua HTTP, chạy trực tiếp engine → database:

1. `IdeaEngine.generate_ideas` → `save_idea` → DB.
2. `ScriptGeneratorEngine.generate_full_script` → `save_script` → DB.
3. `VoiceoverEngine.generate_full_voiceover` → `save_voiceover` → DB.
4. `SceneIllustratorEngine.generate_assets` → `save_asset` → DB.
5. `VideoAssemblerEngine.render_video_stream` → verify SSE output.
6. `SEOOptimizerEngine.format_upload_info` → `save_seo_metadata` → DB.
7. Verify DB cuối cùng có đủ 1 row mỗi bảng, dữ liệu parse lại đúng contract.

### 3.4. Layer 4 — Frontend Static Analysis

File: `tests/test_frontend_static.py`

- Đọc `web/index.html`, kiểm tra:
  - Tất cả thẻ HTML mở/đóng khớp nhau (dùng `html.parser`).
  - Các Vue directive `v-if`, `v-for`, `v-model`, `@click` xuất hiện ít nhất 1 lần (smoke check).
  - Mọi `fetch(` hoặc `apiCall(` đều nằm trong block `try` hoặc `.catch`.

## 4. Ma trận file test

| File | Layer | Số test ước tính |
|------|-------|------------------|
| `tests/test_contracts_db.py` | 1 | 8-10 |
| `tests/test_idea_engine.py` | 2 | 5 (đã có) |
| `tests/test_engines_unit.py` | 2 | 7-10 |
| `tests/test_golden_path.py` | 3 | 1-2 (big integration) |
| `tests/test_frontend_static.py` | 4 | 3-5 |

## 5. Lệnh chạy

```bash
# Chạy toàn bộ
python -m pytest tests/ -v --tb=short

# Chạy từng layer
python -m pytest tests/test_contracts_db.py -v
python -m pytest tests/test_engines_unit.py -v
python -m pytest tests/test_golden_path.py -v
python -m pytest tests/test_frontend_static.py -v
```

## 6. Xử lý file test cũ

- `tests/test_api_integration.py` — **xóa** vì phụ thuộc `httpx2` + `pytest-mock` chưa cài.
- `tests/test_engine_integration.py` — **thay thế** bằng `test_golden_path.py` mới (gọn hơn, đúng contract hơn).
- `tests/test_idea_engine.py` — **giữ nguyên**.

## 7. Checklist triển khai

- [x] Viết `tests/test_contracts_db.py`
- [x] Viết `tests/test_engines_unit.py`
- [x] Viết `tests/test_golden_path.py`
- [x] Viết `tests/test_frontend_static.py`
- [x] Xóa `tests/test_api_integration.py` và `tests/test_engine_integration.py`
- [x] Chạy `pytest tests/ -v` — tất cả PASS (30/30)

