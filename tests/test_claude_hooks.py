"""Tests for the narrowly scoped Claude Code command hooks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRE_HOOK = ROOT / ".claude" / "hooks" / "pre-tool-use.py"
POST_HOOK = ROOT / ".claude" / "hooks" / "post-tool-use-tdd-guard.py"


def run_hook(path: Path, payload: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )


def output_json(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0
    return json.loads(result.stdout)


def test_pre_tool_use_allows_safe_bash_command() -> None:
    result = run_hook(
        PRE_HOOK,
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "pytest -q"}},
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_pre_tool_use_denies_force_push() -> None:
    result = run_hook(
        PRE_HOOK,
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push origin main --force"}},
    )

    output = output_json(result)
    decision = output["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert "force-pushing" in decision["permissionDecisionReason"]


def test_pre_tool_use_denies_force_with_lease() -> None:
    result = run_hook(
        PRE_HOOK,
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push --force-with-lease"}},
    )

    assert output_json(result)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pre_tool_use_denies_root_recursive_delete() -> None:
    result = run_hook(
        PRE_HOOK,
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf /"}},
    )

    output = output_json(result)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pre_tool_use_denies_direct_tubechain_database_delete() -> None:
    result = run_hook(
        PRE_HOOK,
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm data/tubechain.db"}},
    )

    reason = output_json(result)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "SQLite database" in reason


def test_pre_tool_use_ignores_non_bash_tools() -> None:
    result = run_hook(
        PRE_HOOK,
        {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "notes.txt"}},
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_pre_tool_use_ignores_malformed_payload() -> None:
    result = subprocess.run(
        [sys.executable, str(PRE_HOOK)],
        input="not-json",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_post_tool_use_adds_advisory_for_application_python_edit() -> None:
    result = run_hook(
        POST_HOOK,
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(ROOT / "modules" / "idea_engine" / "engine.py")},
        },
    )

    output = output_json(result)
    context = output["hookSpecificOutput"]
    assert context["hookEventName"] == "PostToolUse"
    assert "TDD reminder" in context["additionalContext"]
    assert "cannot block or undo" in context["additionalContext"]


def test_post_tool_use_does_not_warn_for_tests_or_claude_config() -> None:
    for file_path in (
        str(ROOT / "tests" / "test_engine.py"),
        str(ROOT / ".claude" / "hooks" / "pre-tool-use.py"),
    ):
        result = run_hook(
            POST_HOOK,
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": file_path},
            },
        )
        assert result.returncode == 0
        assert result.stdout == ""


def test_post_tool_use_ignores_other_tool_names() -> None:
    result = run_hook(
        POST_HOOK,
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python app.py"},
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
