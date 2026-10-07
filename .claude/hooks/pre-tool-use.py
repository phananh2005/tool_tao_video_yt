"""PreToolUse safety guard for clearly destructive shell commands.

Claude Code provides a JSON object on stdin with `tool_name` and `tool_input`.
This is a narrow defense-in-depth check, not a shell parser or sandbox.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any


def _payload() -> dict[str, Any] | None:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def _command_is_dangerous(command: str) -> str | None:
    normalized = command.strip().lower()
    if not normalized:
        return None

    # Protect common force-push spellings, including --force-with-lease.
    if re.search(r"\bgit\s+push\b", normalized) and re.search(
        r"(?:^|\s)(?:--force(?:-with-lease)?|-f)(?:\s|$)", normalized
    ):
        return "Blocked: force-pushing is not allowed by the TubeChain project policy."

    # Catch direct common attempts to recursively remove a filesystem root.
    if re.search(
        r"\brm\s+(?:(?:-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\s+)+/(?:\s|$)",
        normalized,
    ):
        return "Blocked: recursive deletion of a filesystem root is not allowed."

    # Catch direct rm/del/rmdir of the project's primary database by path/name.
    db_target = r"(?:^|[\s\"'])((?:[^\s\"']*[\\/])?data[\\/]tubechain\.db|tubechain\.db)(?=$|[\s\"'])"
    destructive_delete = re.search(r"\b(?:rm|del|erase|rmdir)\b", normalized)
    if destructive_delete and re.search(db_target, normalized):
        return "Blocked: direct deletion of the TubeChain SQLite database is not allowed."

    return None


def main() -> int:
    payload = _payload()
    if payload is None:
        # Do not block unrelated tools just because an event payload could not be parsed.
        return 0

    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if tool_name != "Bash" or not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    reason = _command_is_dangerous(command)
    if reason is None:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
