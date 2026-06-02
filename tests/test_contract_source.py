#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / "skills" / "codex-with-cursor"
CONTRACT = WORKFLOW / "contract.json"
HOOK_SCRIPT = REPO / "hooks" / "subagent-gate-hook.mjs"
SCRIPTS = WORKFLOW / "scripts"
DELEGATE = SCRIPTS / "delegate_to_cursor.py"
sys.path.insert(0, str(SCRIPTS))

from codex_with_cursor_runtime.cli import add_delegate_args
from codex_with_cursor_runtime.common import REPORT_HEADINGS, REPORT_STATUS_VALUES, WORKER_ROLES
from codex_with_cursor_runtime.contract import default_cursor_model


def compliant_task(text: str = "Inspect the contract-driven task file gate.") -> str:
    return f"""# Contract Driven Task

Goal
{text}

Allowed Scope
- skills/codex-with-cursor

Forbidden Actions
- Do not edit README.md.
- Do not invoke nested delegate runs.

Acceptance Criteria
- The task stays inside the assigned scope.
- The report contains concrete verification evidence.

Verification
- dry-run artifact generation completed

Report Requirements
- Status / Role / Summary / Changed Files / Verification / Findings / Final Result / Risks Or Follow-ups
"""


def run_hook(payload: dict, env: dict[str, str] | None = None) -> dict:
    result = subprocess.run(
        ["node", str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO,
        encoding="utf-8",
        env={**os.environ, **(env or {})},
        check=False,
    )
    assert result.returncode == 0, result.stderr
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def run_delegate(task_file: Path, artifact_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(DELEGATE),
            "-TaskFile",
            str(task_file),
            "-WorkflowId",
            "wf-task-contract",
            "-TaskId",
            task_file.stem,
            "-Role",
            "researcher",
            "-SessionKey",
            "task-contract",
            "-ArtifactRoot",
            str(artifact_root),
            "-DryRun",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        env={**os.environ, "CODEX_CURSOR_CHILD_THREAD": "1", "PYTHONDONTWRITEBYTECODE": "1"},
    )


def test_contract_json_is_single_source_for_runtime_constants() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["workerRoles"] == list(WORKER_ROLES)
    assert contract["reportStatusValues"] == list(REPORT_STATUS_VALUES)
    assert contract["reportHeadings"] == list(REPORT_HEADINGS)
    assert contract["childThread"]["markerName"] == "CODEX_CURSOR_CHILD_THREAD"
    assert contract["childThread"]["markerValue"] == "1"
    assert contract["spawn"]["model"] == "gpt-5.4"
    assert contract["spawn"]["reasoningEffort"] == "medium"
    assert contract["spawn"]["forkContext"] is False
    assert "-Task" in contract["legacy"]["forbiddenArgs"]
    assert "-Mode" in contract["legacy"]["forbiddenArgs"]
    assert contract["cursorAgent"]["executable"] == "agent"
    assert contract["cursorAgent"]["defaultModel"] == "composer-2.5"
    assert contract["cursorAgent"]["defaultModel"] == default_cursor_model()
    delegate_parser = argparse.ArgumentParser()
    add_delegate_args(delegate_parser)
    model_default = next(action.default for action in delegate_parser._actions if action.dest == "model")
    assert model_default == contract["cursorAgent"]["defaultModel"]


def test_hook_gate_reads_spawn_requirements_from_contract_json() -> None:
    with tempfile.TemporaryDirectory(prefix="codex_with_cc_contract_hook_") as tmp:
        plugin_root = Path(tmp)
        workflow_root = plugin_root / "skills" / "codex-with-cursor"
        workflow_root.mkdir(parents=True)
        (workflow_root / "SKILL.md").write_text("# codex-with-cursor\n", encoding="utf-8")
        (workflow_root / "CODEX_WITH_CURSOR.md").write_text("# Codex with Cursor\n", encoding="utf-8")
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        contract["spawn"]["model"] = "contract-model"
        (workflow_root / "contract.json").write_text(json.dumps(contract), encoding="utf-8")

        denied = run_hook(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "spawn_agent",
                "tool_input": {
                    "message": (
                        "Set CODEX_CURSOR_CHILD_THREAD=1 and run delegate_to_cursor.ps1 "
                        "-TaskFile task.md -WorkflowId wf -TaskId task -Role researcher -SessionKey wf"
                    ),
                    "model": "gpt-5.3-codex",
                    "reasoning_effort": "medium",
                    "fork_context": False,
                },
            },
            env={"CODEX_PLUGIN_ROOT": str(plugin_root)},
        )

    reason = denied["hookSpecificOutput"]["permissionDecisionReason"]
    assert "contract-model" in reason


def test_delegate_rejects_task_files_without_required_sections() -> None:
    with tempfile.TemporaryDirectory(prefix="codex_with_cc_task_contract_") as tmp:
        root = Path(tmp)
        artifact_root = root / "artifacts"
        incomplete = root / "incomplete.md"
        incomplete.write_text("just do the thing", encoding="utf-8")

        rejected = run_delegate(incomplete, artifact_root)

        assert rejected.returncode != 0
        assert "Task file contract" in (rejected.stdout + rejected.stderr)

        complete = root / "complete.md"
        complete.write_text(compliant_task(), encoding="utf-8")
        accepted = run_delegate(complete, artifact_root)

        assert accepted.returncode == 0, accepted.stdout + accepted.stderr
