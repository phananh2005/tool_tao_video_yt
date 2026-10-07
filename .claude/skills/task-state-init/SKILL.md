---
name: task-state-init
description: Start or resume a substantial TubeChain task by preparing a concise checklist and handoff state without overwriting active work.
argument-hint: [task-title]
---

# Initialize task state

Use for substantial features, multi-step fixes, cross-phase changes, or when the user asks to track work. Skip for trivial questions and one-line changes.

1. Read `.claude/state/current-task.md` and `.claude/state/progress.md` if present. If a task is active, do not overwrite it: determine whether this request resumes it; otherwise ask whether to close it or start a separate task.
2. Use `.claude/state/_template/current-task.md` for structure. Create `.claude/state/current-task.md` with a concise goal, scope, applicable constraints, acceptance criteria and checkboxes. Do not invent implementation facts.
3. Initialize `.claude/state/progress.md` from its template only if absent. If it exists, append a dated start/resume entry and preserve history.
4. Record consequential architecture decisions in `.claude/state/decisions-log.md` only if that active log exists or the user asks for a decision record. Never overwrite past entries.
5. Keep state concise and factual; link paths instead of copying long source text.
