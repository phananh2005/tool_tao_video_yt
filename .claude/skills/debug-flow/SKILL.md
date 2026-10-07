---
name: debug-flow
description: Diagnose a reproducible TubeChain bug or failing test systematically before changing implementation code.
argument-hint: [failure-or-test]
---

# Debug flow: reproduce, isolate, diagnose, fix

1. **Reproduce:** Capture the exact error, input, state and command. Create or identify a focused regression test. Use temporary SQLite databases and fixtures; do not risk the real database or user media.
2. **Isolate:** Narrow the failure to a route, contract, SQLite operation, phase module, frontend behavior, provider adapter, or FFmpeg invocation. Run the smallest failing test.
3. **Diagnose:** Trace callers and data; establish the root cause from evidence. Check edge cases and possible implementation/documentation/schema drift.
4. **Fix:** Make the smallest root-cause fix and add/update regression coverage. Follow `tdd-playbook` where applicable.
5. **Verify:** Re-run the reproducer, affected test module and broader tests as appropriate. Report exact results and remaining uncertainty.
