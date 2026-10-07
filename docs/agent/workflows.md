# TubeChain AI Development Workflows

Use this guide with the project constraints in [`CLAUDE.md`](../../CLAUDE.md) and the repository evidence in [`README.md`](README.md). These are development-time workflows; subagents do not participate in the runtime video pipeline.

## Agent roles and boundaries

| Role | Best fit | Boundary / handoff |
|---|---|---|
| `youtube-strategist` | Audience/content goals, idea differentiation, hooks, retention, video-series sequencing and YouTube packaging requirements. | Provides editorial recommendations and acceptance criteria; does not define technical schemas or promise algorithmic outcomes. |
| `prompt-engineer` | Prompt templates, prompt construction and deterministic tests/evals for generated content. | Inspects the current engine, adapter, parser and contract. Does not make live provider calls or silently change contracts. |
| `architect` | Non-trivial technical design, API/data contracts, SQLite schema/migration and cross-phase changes. | Reports verified behavior, risks and acceptance criteria; hands off a design for implementation. Skip for trivial localized changes. |
| `developer` | Python/FastAPI, SQLite, frontend, pipeline and FFmpeg implementation. | Reuses existing code, tests behavior changes, runs focused checks and reports actual outcomes. |
| `qa-reviewer` | Independent diff review for correctness, security, invariants, regression and test quality. | Reports actionable evidence; normally does not modify production code. |

The checked-in agent files declare `model: opus` or `model: sonnet`. The root guide documents the user's runtime mapping (`opus` → Gemini 3.1 Pro; `sonnet` → Gemini 3.8 Flash); do not replace aliases with guessed provider-specific IDs.

## Route work by task type

### Research / repo understanding

1. Use read-only search and read the closest source, callers and tests.
2. Record `path:line` evidence; distinguish observed behavior, documentation claims, inference and unknowns.
3. Do not inspect local settings, secrets, browser profiles, databases, user media or unrelated logs.
4. If the user wants a research deliverable, summarize findings, gaps, confidence and safe next steps before suggesting edits.

### Content/product design

For features affecting ideas, scripts, voiceover language, scenes, thumbnails, SEO or publishing metadata:

1. `youtube-strategist` defines the creator/audience goal and measurable editorial acceptance criteria.
2. `architect` translates approved content requirements into technical scope/contracts if phase boundaries or persisted/API data are affected.
3. `prompt-engineer` proposes prompt changes against the existing parser/output shape and creates deterministic mock-based test cases.
4. `developer` implements only after the contract is clear; `qa-reviewer` verifies the diff and tests.

For a prompt-only change with a stable contract, skip `architect` unless code inspection reveals a contract/schema change. Editorial guidance is not evidence of guaranteed views, CTR, retention or ranking. Require fact-checking/human approval where the content warrants it.

### Technical design / implementation

- **Small isolated change:** `developer` may implement directly with focused tests.
- **New feature limited to one module:** developer inspects module and tests, runs `reuse-scan`, and follows the current local contract.
- **Cross-phase, API, contract, schema or migration change:** `architect` first; developer implements the reviewed handoff; QA reviews the result.
- **Frontend-only:** inspect static assets in `web/`, API route/response in `app.py`, and `tests/test_frontend_static.py` where relevant.
- **Persistence:** inspect `core/database.py`, `core/contracts.py`, and `tests/test_contracts_db.py`. Use isolated test databases; never reset `data/tubechain.db`.
- **Media/FFmpeg:** inspect `modules/video_assembler/` or `modules/scene_illustrator/` and use temporary fixtures. Do not overwrite or delete user media.

### Debugging

Use skill `debug-flow`:

1. Reproduce with a focused test or safe fixture.
2. Isolate the route/module/data boundary.
3. Diagnose from code and evidence, not guesses.
4. Make the smallest root-cause fix and add regression coverage.
5. Re-run the reproducer and relevant wider checks; report failures and unknowns.

Do not run database migrations or destructive cleanup to reproduce a bug.

### Tests and quality review

- Behavior changes: follow `tdd-playbook` (Red → Green → Refactor) and do not claim a Red was observed unless the failing test was actually run.
- Existing documented test command: `python -m pytest` (from `README.md`). No repository-wide lint/type-check/build command was confirmed during this assessment.
- Run the narrowest relevant test first; expand to affected suites when practical. Report command, result, skipped tests and reason.
- `qa-reviewer` reviews changed code, direct callers/contracts and tests; checks SQLite parameterization, path/deletion scope, secret handling, phase invariants, subprocess/resource handling and unnecessary duplication.
- A hook reminder is not proof of TDD, and tests do not replace diff review.

### Documentation

- Keep factual claims aligned with current source. `system-description.md` contains broader and partly aspirational/legacy context; verify it against code.
- For docs-only changes, validate links and referenced paths; do not invent dependencies or install commands when manifests are absent.
- Keep development harness docs separate from user instructions for running TubeChain.

### DevOps / CI / release

The inspected repository inventory did not include a CI configuration or root dependency manifest. Do not invent a pipeline or add one implicitly. Any future request to add CI, change permissions, install dependencies, modify runtime/production settings, deploy, release, commit, tag or push requires explicit scope/approval. Begin read-only and state expected side effects before acting.

## Clarification and approval gates

**Ask the user before proceeding** when an unresolved choice can materially change scope, user-visible behavior, durable data/schema, API compatibility, security/privacy, external cost/network usage, permissions, or cause an irreversible action. Also ask before editing root instructions, active settings/hooks/CI, or user/local configuration unless the user explicitly authorized that exact change.

**Proceed with a safe assumption** when the missing detail is low-impact, reversible and compatible with existing behavior. State the assumption in the handoff/report; do not ask questions whose answers would not change the implementation.

Examples:
- Ask: an ambiguous requirement may imply deleting persisted records or changing phase output shape.
- Ask: choosing a live AI provider, sending repository data externally, or spending API credits.
- Ask: modifying `.claude/settings.json`, `CLAUDE.md`, permissions, hooks or CI outside an already approved plan.
- Assume and state: use the existing UI style for a small non-breaking UI control when there is one clear precedent.

## State, handoff and completion

Use `.claude/skills/task-state-init` and `.claude/skills/progress-tracker` for substantial, multi-step work; skip state files for trivial edits. Never overwrite active task history without checking it first.

A useful handoff includes:

- User goal and accepted scope; out-of-scope items.
- Decisions, assumptions and links to relevant design/contracts.
- Files/modules changed or proposed.
- Tests/checks run with exact results; skipped checks and why.
- Risks, unresolved questions, blockers and next owner/action.

Before saying work is complete, inspect the diff/status for scope, preserve pre-existing changes, verify applicable acceptance criteria, and report any check not run. Never commit/push/deploy unless explicitly requested.

## Current hook limitations (documentation, not configuration changes)

- `.claude/settings.json` currently registers the pre-tool safety hook for `Bash` only. Do not imply it protects PowerShell or every shell command.
- The pre-tool hook recognizes selected literal destructive command patterns. It is not a full shell parser or sandbox; command chaining, aliases, scripts, alternate shells and path variants may evade string checks.
- The post-tool TDD hook is an advisory after `Write|Edit`; it cannot prevent or undo a completed edit.
- Hook scripts use relative paths in the current configuration; verify execution from a worktree or alternate CWD before relying on it.
- These observations are recorded for future review. This workflow does not change active hooks, settings or permissions.
