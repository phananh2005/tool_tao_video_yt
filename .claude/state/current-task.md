# Current Task: Ground Phase 4 images in narration

## Goal
Make generated scene images reflect the saved Phase 3 spoken text for the same scene, rather than relying only on the earlier Phase 2 visual concept.

## Checklist
- [x] Trace current script → voiceover → image flow and reuse existing scene/asset contracts.
- [x] Confirm technical approach with the architect and editorial acceptance criteria.
- [x] Add focused tests and observe relevant Red before implementation.
- [x] Pass saved voiceover into Phase 4 and compose narration-grounded prompts.
- [x] Verify scene-number matching, fallback, duplicate validation, cached prompt metadata and focused tests.
- [ ] Complete independent QA review; review was attempted but targeted the clean QA agent worktree rather than the root working-tree diff.

## Notes & constraints
- Kept Phase 3 text-only and Phase 3.5 synthesis separate; preserved the existing synthesis gate.
- Matches voiceover by `scene_number`, never list position. Missing/blank text falls back to visual concept; duplicate voiceover scene numbers raise `ValueError`.
- Keeps `visual_concept` as primary image direction; quoted speech is treated as scene data and grounds depicted subject/action/consequence without unsupported details.
- Stores composed prompt through existing `AssetSceneJSON.image_prompt`; no schema/provider change. No live provider calls.
- Focused illustrator tests: 5 passed. Engine tests excluding known unrelated SEO test: 11 passed. Full golden-path test fails at existing SEO title expectation; DB contract module has 3 failures outside this change. See progress.md for exact outcomes.
- Route-level test was skipped: importing app initializes root `data/tubechain.db`; avoid risk to user data. No route tests were present.
