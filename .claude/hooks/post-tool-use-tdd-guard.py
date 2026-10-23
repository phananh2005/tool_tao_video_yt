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

    lines_count = 0
    if "content" in tool_input and isinstance(tool_input["content"], str):
        lines_count = len(tool_input["content"].splitlines())
    elif "new_string" in tool_input and isinstance(tool_input["new_string"], str):
        lines_count = len(tool_input["new_string"].splitlines())

    warning_micro = ""
    if lines_count > 60:
        warning_micro = (
            f" [CẢNH BÁO MICRO-TASKING: Thao tác này sửa/ghi {lines_count} dòng code (> 60 dòng). "
            "Hãy chia nhỏ thành các bước vi mô (≤ 50 dòng/1 hàm) và viết unit test cho từng hàm nhỏ trước!]"
        )

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"TDD reminder: `{file_path}` đã được sửa. Thêm hoặc cập nhật test pytest "
                        "tập trung, chạy test liên quan, và báo cáo kết quả thật. "
                        "Đây chỉ là lời nhắc; hook này cannot block or undo edits."
                        + warning_micro
                    ),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
