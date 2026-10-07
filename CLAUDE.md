# TubeChain — Project Guide for Claude Code

## Project snapshot
TubeChain is a local-first YouTube video-production tool. The checked-in application currently uses Python + FastAPI (`app.py`), SQLite (`core/database.py`), static web assets (`web/`), pipeline modules under `modules/`, and pytest tests under `tests/`. FFmpeg is used for basic video assembly. Confirm dependencies and commands from project files before assuming them; do not invent setup instructions.

The product pipeline is:
1. **Idea Engine** — brainstorm, deduplication, Rabbit Hole planning.
2. **Script Generator** — structured script and timing.
3. **Voiceover Writer** — spoken-text generation only.
4. **Scene Illustrator** — scene breakdown, image prompts/assets.
5. **Video Assembler** — simple sequential static-image assembly.
6. **SEO Optimizer** — title, description, tags, chapters and thumbnail concept.

The current implementation also has a **legacy Phase 3.5 voice synthesis** path. Keep that distinct from Phase 3 text generation; do not silently remove or extend either behavior.

## Hard product constraints
- Keep the app local: local UI/API and SQLite; do not add cloud DB, deployment or remote storage.
- Historical videos are represented by text/metadata/topics/embeddings only; do not retain old video media as history.
- Rabbit Hole groups are capped at **3 videos**.
- Dedup thresholds: similarity `> 0.85` blocks; `0.60–0.85` warns; `< 0.60` passes. Reuse existing configuration/logic rather than duplicating thresholds.
- Phase 3 writes voiceover text; it is not a TTS feature. Treat the existing Phase 3.5 implementation as a separate legacy stage.
- Keep video assembly intentionally simple: sequential static images and the existing supported audio input; no Ken Burns, transitions, animation, or background-music feature.
- Keep AI calls behind the existing provider-adapter boundary. Do not claim API/manual modes exist unless confirmed in code; never hardcode credentials.
- Development subagents assist code work only; they are not runtime actors in the video-production pipeline.

## Routing and handoffs
Use subagents when they add value; do not force a multi-agent chain for trivial edits.

| Agent | Model alias | Responsibility |
|---|---|---|
| `youtube-strategist` | `opus` | YouTube audience/content strategy for ideas, angle, hooks, retention, series, titles, thumbnails and SEO. Provides content requirements and measurable editorial criteria; does not define technical contracts or write code. |
| `prompt-engineer` | `sonnet` | Design/review prompt templates and deterministic prompt-output evaluations for the existing adapter flow. Does not make live provider calls or silently change shared contracts. |
| `architect` | `opus` | Non-trivial requirements/design, shared data contracts, SQLite schema/migrations, cross-phase decisions and acceptance criteria. Does not implement application code. |
| `developer` | `sonnet` | Implement a clear request or approved design, reuse existing code, follow TDD for behavior changes, run relevant checks. |
| `qa-reviewer` | `opus` | Independent diff review, invariant/security/regression checks and test verification; normally reports findings rather than changing production code. |

In this environment, the user-configured runtime maps `opus` to Gemini 3.1 Pro and `sonnet` to Gemini 3.8 Flash. Keep the documented aliases in subagent frontmatter; do not replace them with guessed provider-specific IDs.

Routing by task type:
- **AI-generated content/product behavior:** `youtube-strategist` defines audience/content goals and acceptance criteria → `architect` translates them into technical design/contracts → `prompt-engineer` drafts or evaluates prompt behavior against the approved contract → `developer` implements → `qa-reviewer` independently verifies.
- **Prompt-only change with stable output contract:** `prompt-engineer` → `developer` (tests) → `qa-reviewer` when risk warrants.
- **Technical/schema/cross-phase work:** `architect` (when design is non-trivial) → `developer` → `qa-reviewer`.
- **Small isolated fix:** `developer` may proceed directly with focused tests; involve other agents only where they add value.

`youtube-strategist` owns content strategy, not technical architecture. `prompt-engineer` owns prompt design/evaluation, not database/API contracts. Shared contract changes always return to `architect` before implementation proceeds. The two content-focused agents are development-time specialists, never runtime participants in video creation.

## Engineering workflow
1. Read the relevant source, callers, tests, and any design handoff; identify verified behavior before changing it.
2. Run skill `reuse-scan` before creating a new helper, route, schema, component, or repeated behavior.
3. For behavior changes and bugs, follow `tdd-playbook`: Red (observe the relevant failing test when practical) → Green → Refactor → verification. Do not claim a test was run if it was not.
4. Use `debug-flow` for reproducible failures. Use `task-state-init` and `progress-tracker` for substantial tracked work, not trivial edits.
5. Run focused tests first, then the broader affected suite. Report exact commands, results, and any checks not run.
6. Review the diff for scope creep, contract drift, accidental data/media deletion, credentials, and unrelated changes.

## Safety and data handling
- Never delete or reinitialize `data/tubechain.db` or user media to make a test pass.
- Use temporary databases/media fixtures for tests. Keep destructive operations within the explicitly requested project scope and inspect targets first.
- Do not commit, force-push, deploy, or publish unless the user explicitly asks.
- Hooks in `.claude/settings.json` are narrow defense-in-depth. The PreToolUse guard blocks selected obvious destructive shell commands; it is not a complete shell parser or sandbox. The PostToolUse TDD reminder is advisory and cannot undo or block a completed edit.
- Do not modify `.claude/settings.local.json` or user/global Claude Code configuration unless explicitly requested.

## Framework files
- Project-specific subagents: `.claude/agents/`
- Loadable skills: `.claude/skills/<skill-name>/SKILL.md`
- Hook configuration and scripts: `.claude/settings.json`, `.claude/hooks/`
- Reusable state templates: `.claude/state/_template/`
- Product overview: `README.md`; detailed product/legacy context: `system-description.md` (verify against implementation).
- Agent harness inventory and task workflows: [`docs/agent/README.md`](docs/agent/README.md) and [`docs/agent/workflows.md`](docs/agent/workflows.md).
