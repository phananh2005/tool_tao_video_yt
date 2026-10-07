"""Advisory PostToolUse reminder for application Python edits.

PostToolUse runs after an operation and cannot block or revert it. This hook
only adds a reminder to context; it does not enforce or verify TDD.
"""

from __future__ import annotations

import json
import sys
from pathlib import PurePath
from typing import Any


def _is_application_python(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    if not normalized.endswith(".py"):
        return False
    parts = PurePath(normalized).parts
    if ".claude" in parts:
        return False
    if any(part in {"tests", "test"} or part.startswith("test_") for part in parts):
        return False
    return True


def main() -> int:
    try:
        payload: Any = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    if not isinstance(payload, dict):
        return 0
    if payload.get("tool_name") not in {"Write", "Edit"}:
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not _is_application_python(file_path):
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"TDD reminder: `{file_path}` was changed. Add or update a focused "
                        "pytest test, run it (and relevant broader tests), and report actual "
                        "results. This is advisory; this post-tool hook cannot block or undo edits."
                    ),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
