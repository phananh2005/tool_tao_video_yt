---
name: progress-tracker
description: Update TubeChain task checklists and append concise progress or verification notes while preserving existing state history.
---

# Track task progress

1. Read `.claude/state/current-task.md` and `.claude/state/progress.md` before updating them.
2. Tick a checklist item only after completing and verifying it. Do not mark tests, reviews, or handoffs complete based on intention.
3. Append a dated entry to `progress.md` with the completed work and its verification result. Record failures, blockers and skipped checks plainly.
4. If scope changes, update the goal/checklist transparently; do not silently remove incomplete items.
5. Keep the log chronological, brief, factual, and free of secrets or copied command output. Do not create state files for trivial work unless requested.
