# Lịch Sử Làm Việc (Progress Tracker)

*Ghi log lại từng mốc thời gian để giữ context cho các phiên tiếp theo.*

---
- **[2026-10-07]**: Bắt đầu task “Ground Phase 4 images in narration”. Đã xác nhận Phase 4 hiện lấy `visual_concept` từ script và bỏ qua voiceover đã lưu.
- **[2026-10-07]**: TDD Red: `python -m pytest tests/test_engines_unit.py -k "scene_illustrator_grounds_prompts or scene_illustrator_falls_back or scene_illustrator_stores_composed or scene_illustrator_rejects_duplicate" -q` → 4 failed do `generate_assets` chưa nhận tham số voiceover như dự kiến.
- **[2026-10-07]**: Implemented: Phase 4 passes saved voiceover after existing Phase 3.5 gate; image prompt composition uses matching `scene_number`, falls back for missing/blank speech, rejects duplicate voiceover scene IDs, saves composed prompt even on skip-existing-image path.
- **[2026-10-07]**: Focused test `python -m pytest tests/test_engines_unit.py -k "scene_illustrator" -q` → 5 passed, 7 deselected.
- **[2026-10-07]**: Affected engine checks: `python -m pytest tests/test_engines_unit.py -k "not seo_engine_format_upload_info" -q` → 11 passed, 1 deselected. Full engine unit suite not rerun at root; prior implementation-worktree run was 10 passed, 1 known unrelated SEO failure.
- **[2026-10-07]**: Broader checks: `python -m pytest tests/test_golden_path.py tests/test_frontend_static.py -q` → 1 failed (golden path SEO title expected `Golden SEO`, got `Golden Idea`), 4 passed; `python -m pytest tests/test_contracts_db.py -q` → 9 passed, 3 failures in unrelated DB invariants (`test_script_unique_idea_id`, `test_ready_to_render_needs_audio`, `test_delete_project_media_removes_folder_keeps_db`).
- **[2026-10-07]**: `git diff --check` returned no whitespace errors. Route-level test was not run because importing `app.py` initializes real `data/tubechain.db`; no route tests currently exist. Independent reviewer was launched but its isolated worktree was clean, so it did not review the root diff.
