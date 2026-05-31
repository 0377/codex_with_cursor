#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from tests.task_helpers import compliant_task, write_fake_agent_python_shim

repo = Path(__file__).resolve().parents[1]
delegate = repo / "skills" / "codex-with-cursor" / "scripts" / "delegate_to_cursor.py"
scripts = repo / "skills" / "codex-with-cursor" / "scripts"
sys.path.insert(0, str(scripts))

from codex_with_cursor_runtime.cursor_cli import new_cursor_cli_args, resolve_agent_executable


@pytest.mark.skipif(shutil.which("agent") is None, reason="Cursor Agent CLI (agent) is not installed")
def test_agent_cli_supports_headless_flags() -> None:
    result = subprocess.run(
        ["agent", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    for flag in ("--print", "--output-format", "stream-json", "--model", "--resume", "--yolo", "--trust"):
        assert flag in output, f"missing {flag!r} in agent --help"


@pytest.mark.skipif(shutil.which("agent") is None, reason="Cursor Agent CLI (agent) is not installed")
def test_agent_list_models_includes_default_delegate_model() -> None:
    result = subprocess.run(
        ["agent", "--list-models"],
        text=True,
        capture_output=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "composer-2.5" in output


def test_delegate_default_model_and_cursor_cli_argv_in_dry_run() -> None:
    with tempfile.TemporaryDirectory(prefix="codex_with_cc_default_model_") as tmp:
        artifact_root = Path(tmp) / "artifacts"
        task_file = Path(tmp) / "default-model-task.md"
        task_file.write_text(compliant_task("default model dry run"), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(delegate),
                "-TaskFile",
                str(task_file),
                "-WorkflowId",
                "wf-default-model",
                "-TaskId",
                "task-default-model",
                "-Role",
                "researcher",
                "-ArtifactRoot",
                str(artifact_root),
                "-SessionKey",
                "default-model-session",
                "-DryRun",
            ],
            cwd=repo,
            text=True,
            capture_output=True,
            env={**os.environ, "CODEX_CURSOR_CHILD_THREAD": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        assert result.returncode == 0, result.stdout + result.stderr
        run_id = next(line.split(":", 1)[1].strip() for line in result.stdout.splitlines() if line.startswith("RunId:"))
        config = json.loads((artifact_root / f"config_{run_id}.json").read_text(encoding="utf-8"))
        assert config["model"] == "composer-2.5"


def test_new_cursor_cli_args_match_headless_contract() -> None:
    args = new_cursor_cli_args(
        "composer-2.5",
        "chat-123",
        resume=True,
        bypass_permissions=True,
        workspace="/tmp/repo",
    )
    assert args == [
        "--print",
        "--output-format",
        "stream-json",
        "--model",
        "composer-2.5",
        "--workspace",
        "/tmp/repo",
        "--resume",
        "chat-123",
        "--yolo",
        "--trust",
    ]


def test_resolve_agent_executable_prefers_agent_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if os.name == "nt":
        (tmp_path / "agent.cmd").write_text("@echo off\nexit /b 0\n", encoding="utf-8")
        (tmp_path / "cursor.cmd").write_text("@echo off\nexit /b 0\n", encoding="utf-8")
    else:
        agent_bin = tmp_path / "agent"
        cursor_bin = tmp_path / "cursor"
        agent_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        cursor_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        agent_bin.chmod(0o755)
        cursor_bin.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    resolved = resolve_agent_executable()
    assert resolved is not None
    assert Path(resolved).stem.lower() == "agent"


def test_delegate_records_cursor_cli_argv_with_fake_agent() -> None:
    report = "\n".join(
        (
            "Status",
            "DONE",
            "",
            "Role",
            "researcher",
            "",
            "Summary",
            "argv capture ok",
            "",
            "Changed Files",
            "None",
            "",
            "Verification",
            "- fake",
            "",
            "Findings",
            "- none",
            "",
            "Final Result",
            "DONE",
            "",
            "Risks Or Follow-ups",
            "None",
        )
    )
    with tempfile.TemporaryDirectory(prefix="codex_with_cc_cursor_argv_") as tmp:
        root = Path(tmp)
        artifact_root = root / "artifacts"
        argv_capture = root / "argv.json"
        fake_bin = root / "fake-agent-bin"
        fake_bin.mkdir(parents=True)
        script = root / "capture_argv_agent.py"
        script.write_text(
            "\n".join(
                (
                "import json",
                "import sys",
                "",
                "if '--list-models' in sys.argv:",
                "    print('composer-2.5')",
                "    raise SystemExit(0)",
                "sys.stdin.read()",
                    f"with open({str(argv_capture)!r}, 'w', encoding='utf-8') as handle:",
                    "    json.dump(sys.argv, handle)",
                    f"assistant = {{'type': 'assistant', 'message': {{'role': 'assistant', 'content': [{{'type': 'text', 'text': {report!r}}}]}}}}",
                    "print(json.dumps(assistant, separators=(',', ':')))",
                    "print(json.dumps({'type': 'result', 'subtype': 'success'}, separators=(',', ':')))",
                )
            ),
            encoding="utf-8",
        )
        shim = write_fake_agent_python_shim(fake_bin, script)

        task_file = Path(tmp) / "argv-task.md"
        task_file.write_text(compliant_task("record cursor argv"), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(delegate),
                "-TaskFile",
                str(task_file),
                "-WorkflowId",
                "wf-argv",
                "-TaskId",
                "task-argv",
                "-Role",
                "researcher",
                "-ArtifactRoot",
                str(artifact_root),
                "-SessionKey",
                "argv-session",
                "-BypassPermissions",
                "-MaxRetryCount",
                "0",
            ],
            cwd=repo,
            text=True,
            capture_output=True,
            env={
                **os.environ,
                "CODEX_CURSOR_CHILD_THREAD": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
            },
        )
        assert result.returncode == 0, result.stdout + result.stderr
        run_id = next(line.split(":", 1)[1].strip() for line in result.stdout.splitlines() if line.startswith("RunId:"))
        config = json.loads((artifact_root / f"config_{run_id}.json").read_text(encoding="utf-8"))
        captured_argv = json.loads(argv_capture.read_text(encoding="utf-8"))
        assert "--model" in captured_argv
        model_index = captured_argv.index("--model")
        assert captured_argv[model_index + 1] == "composer-2.5"
        assert "--name" not in captured_argv
        assert config["lastCursorCliArgv"][1:] == captured_argv[1:]
        assert Path(config["cursorCliExecutable"]).resolve() == shim.resolve()
