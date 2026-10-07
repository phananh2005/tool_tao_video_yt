---
name: tdd-playbook
description: Apply a focused Red-Green-Refactor test-first loop to TubeChain behavior changes and verify relevant pytest coverage.
---

# TDD Playbook — Red, Green, Refactor

Use for behavior changes, bug fixes and new logic. Documentation/configuration-only changes can use format/schema validation instead of application unit tests.

1. **Red:** Read existing tests and contracts. Add or adjust the smallest test expressing expected behavior. Run it and confirm failure is relevant to missing/incorrect behavior. If it cannot run before implementation, state why; never claim an observed Red that did not happen.
2. **Green:** Implement the smallest coherent change that satisfies the test while preserving public contracts unless a design handoff approves a change.
3. **Refactor:** Remove duplication and improve clarity without changing behavior. Keep tests green.
4. **Verify:** Run the focused test again, then relevant module/suite tests. Report commands and actual outcomes, including failures.

TubeChain test guidance:
- Use isolated fixtures and temporary SQLite databases. Never clear or replace `data/tubechain.db` to make tests pass.
- When changing dedup, cover `>0.85`, exactly `0.85`, `0.60`, and below `0.60`; when changing Rabbit Hole behavior, cover the three-video cap.
- Test Phase 3 voiceover text separately from existing Phase 3.5 synthesis.
- A `PostToolUse` hook is advisory: it cannot undo edits or prove Red-Green-Refactor occurred. The developer remains responsible for the TDD process.
