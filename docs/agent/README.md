# TubeChain Agent Harness — Repository Map

**Status:** read-only repository assessment, 2026-10-07  
**Scope:** development-time Claude Code guidance and visible application structure. This document describes repository evidence; it does not certify external infrastructure or runtime behavior beyond the cited code.

## Repository map

| Area | Evidence | Observed role |
|---|---|---|
| App/API entrypoint | `app.py` | FastAPI application; direct execution binds to `127.0.0.1:8000`. It mounts the `web/` static UI and the `data/` directory. |
| Contracts | `core/contracts.py` | Python dataclasses and provider interface for idea, script, voiceover, scene assets and AI provider operations. |
| Persistence | `core/database.py` | SQLite schema and data access. `DB_PATH` points to `data/tubechain.db`. |
| Pipeline modules | `modules/idea_engine/`, `modules/script_gen/`, `modules/voiceover/`, `modules/scene_illustrator/`, `modules/video_assembler/`, `modules/seo_optimizer/` | Per-phase generation and assembly logic. |
| Frontend | `web/` | Static web assets served by FastAPI. |
| Tests | `tests/` | Pytest unit, database, frontend-static and golden-path tests. `tests/test_claude_hooks.py` covers hook behavior. |
| Product documentation | `README.md`, `system-description.md`, `docs/phase1_business_logic.md`, `plans/` | User-facing overview, design context and historical/feature plans. Treat plans as historical unless checked against current code. |

## Stack and verification evidence

| Concern | Finding | Evidence status |
|---|---|---|
| Language/runtime | Python | Observed in `app.py`, `core/`, `modules/` and `tests/`. |
| Web framework | FastAPI with Pydantic request models | Observed imports and `FastAPI(...)` in `app.py`; the app's direct-run block uses Uvicorn. |
| Storage | SQLite plus local filesystem | Observed in `core/database.py`, `app.py`, and `.gitignore`. |
| UI | Static HTML/CSS/JavaScript | Observed from `web/` and README; not a separately managed frontend package in the root inventory. |
| Media assembly | FFmpeg subprocess use | Observed in `modules/video_assembler/engine.py`; voice synthesis also has subprocess use. |
| AI interaction | Gemini web UI automation using Playwright | Observed in `modules/idea_engine/adapter.py`, which launches a persistent Chrome context and navigates to the Gemini website. Local storage/UI does **not** mean all AI processing is offline or local. |
| Tests | pytest | Observed test files and documented command `python -m pytest` in README. |
| Dependency manifest | Not found at repository root | No root `requirements.txt`, `pyproject.toml`, or `package.json` was found in the inspected inventory. Do not infer an install command from this absence. |
| Lint/type-check/build commands | Not verified | No applicable root configuration/command was found in the inventory. |
| CI configuration | Not found in inspected repository | No `.github/` directory was found. This does not establish whether hosting-side CI exists. |
| Database migrations | Migration logic exists in `core/database.py` | Code includes a schema update path for the voiceover synthesis flag; no general migration framework was identified. |

## Product constraints relevant to agent work

The current root [`CLAUDE.md`](../../CLAUDE.md) records the project constraints and routing rules. In brief:

- Local-first FastAPI UI/API, SQLite, and local files; do not add cloud DB/deployment without explicit product authorization.
- Historical video context is text/metadata/topics/embeddings, not retained historical media.
- Rabbit Hole series are capped at three videos; dedup thresholds are `>0.85` block, `0.60–0.85` warn, `<0.60` pass.
- Phase 3 creates voiceover text. The repository also has a legacy Phase 3.5 voice-synthesis path (`modules/voiceover/synthesizer.py`, route in `app.py`); treat these as separate stages.
- Video rendering is intentionally simple: sequential static images, with current audio support as implemented.
- The current adapter boundary is represented by `AIProviderContract` in `core/contracts.py`; do not claim API/manual modes exist unless implementation verifies them.

## Existing Claude Code harness inventory

| Capability | Status | Evidence / notes |
|---|---|---|
| Project instruction hub | Present | `CLAUDE.md` gives project constraints, skill links, task routing and workflow. |
| Subagents | Present (5) | `.claude/agents/`: `youtube-strategist`, `prompt-engineer`, `architect`, `developer`, `qa-reviewer`. Frontmatter uses `opus`/`sonnet` aliases; repo documentation states the user's runtime maps those aliases to Gemini 3.1 Pro and Gemini 3.8 Flash. |
| Skills | Present (5) | `.claude/skills/<name>/SKILL.md`: task-state-init, progress-tracker, reuse-scan, debug-flow, tdd-playbook. |
| Task state templates | Present | `.claude/state/_template/`: current-task, progress and decisions-log. No active state file was part of the inspected inventory. |
| Hooks | Present and active in project settings | `.claude/settings.json` registers PreToolUse for `Bash` and PostToolUse for `Write|Edit`; scripts are under `.claude/hooks/`. These are narrow checks, not a sandbox. |
| Hook tests | Present | `tests/test_claude_hooks.py` covers common force-push/root-delete/DB-delete cases, safe commands, payload handling and advisory behavior. |
| User-level/local settings | Exists but not assessed | `.claude/settings.local.json` is excluded from this review; do not inspect or reproduce its values. |
| Slash commands / custom workflows / MCP | Not found in inspected project inventory | No `.claude/commands/`, `.claude/workflows/`, or MCP config was observed. No need to add these absent a repeated use case and explicit scope. |

### Current harness caveats to keep visible

These are review findings only; this bootstrap did not change active configuration:

1. **Shell coverage:** the destructive-command hook is registered for `Bash`. A `PowerShell` tool invocation would not match this event registration. Do not imply it protects every shell or indirect command form.
2. **Working-directory assumptions:** hook commands use project-relative script paths. Validate behavior before relying on them from a worktree or another CWD; no path/config changes were made here.
3. **Staged-state/worktree visibility:** the repository already had substantial staged and untracked work during this assessment. A separate worktree based on an earlier commit may not contain these uncommitted agents/hooks/docs. Confirm the active checkout before assuming a harness feature is available.
4. **Language consistency:** agent/skill documentation is largely English while the task-state templates are Vietnamese. This is a usability inconsistency, not a runtime defect; no template was rewritten.
5. **Historical plans:** `plans/` and helper files may refer to the older seven-agent setup. Treat them as historical unless a task explicitly updates plans; this review did not edit them.
6. **Policy vs enforcement:** Markdown rules are instructions, not a hard security boundary. PostToolUse can remind after an edit but cannot undo or prevent it. PreToolUse matching covers only its configured event/tool and recognizable command strings.

## Source-of-truth precedence

For development work, use this practical order:

1. Explicit user request and approval boundaries.
2. Current root `CLAUDE.md` and applicable security/privacy requirements.
3. Current implementation and tests for actual behavior.
4. Current product/design documents and plans, checked against code.
5. Agent/skill guidance and general tool defaults.

If documentation and implementation disagree, report the mismatch and avoid changing product behavior without approval.

## Ownership and non-goals

- This assessment only adds agent documentation; it does not change application code, database/data, dependencies, active hooks/settings, CI, permissions, or runtime configuration.
- Do not commit, stage, push, publish, or deploy as part of this bootstrap.
- Do not read or copy `.env`, local settings, browser profile, databases, logs, credentials, or other runtime/user data into agent documentation.
