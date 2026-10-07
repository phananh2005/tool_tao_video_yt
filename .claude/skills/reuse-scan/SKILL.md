---
name: reuse-scan
description: Search TubeChain code, contracts, tests, and UI for existing behavior before introducing a helper, route, schema, component, or pipeline implementation.
---

# Reuse scan

Before adding a function, class, route, data contract, utility, UI component, or repeated behavior:

1. Identify the responsibility and likely owning module. Search relevant paths with `Grep`/`Glob` (or `rg` via Bash where appropriate); exclude `.git/`, `data/`, caches, generated files, and virtual environments.
2. Search both exact names and equivalent behavior. Check `core/contracts.py` for types, `core/database.py` for persistence, `modules/` for phase logic, `app.py` for routes, `web/` for UI conventions, and `tests/` for expected behavior.
3. Read matching implementations, callers and tests. A name match alone does not establish reuse suitability.
4. Extend existing behavior where it fits. For shared contract/schema changes, obtain an Architect handoff rather than silently changing formats.
5. If no suitable implementation exists, add the smallest abstraction in its owning module and test it. Avoid generic utilities with one opaque caller.
6. In the implementation summary, identify reused code or briefly state that no suitable implementation was found.
