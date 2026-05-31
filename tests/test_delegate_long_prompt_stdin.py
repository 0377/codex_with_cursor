#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from tests.task_helpers import FAKE_AGENT_LIST_MODELS_SH, compliant_task


repo = Path(__file__).resolve().parents[1]
delegate = repo / "skills" / "codex-with-cursor" / "scripts" / "delegate_to_cursor.py"


def make_fake_agent_bin(root: Path, stdin_capture: Path) -> Path:
    fake_bin = root / "fake-agent-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    assistant = json.dumps(
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Status\nDONE\n\nRole\nimplementer\n\nSummary\nok\n\nChanged Files\nNone\n\nVerification\n- fake\n\nFindings\n- fake long prompt run\n\nFinal Result\nDONE\n\nRisks Or Follow-ups\nNone",
                    }
                ],
            },
        },
        separators=(",", ":"),
    )
    result = json.dumps({"type": "result", "subtype": "success"}, separators=(",", ":"))
    if os.name == "nt":
        (fake_bin / "agent.cmd").write_text(
            "@echo off\n"
            f"more > \"{stdin_capture}\"\n"
            f"echo {assistant}\n"
            f"echo {result}\n"
            "exit /b 0\n",
            encoding="utf-8",
        )
    else:
        script = fake_bin / "agent"
        script.write_text(
            "#!/bin/sh\n"
            f"{FAKE_AGENT_LIST_MODELS_SH}"
            f"cat > \"{stdin_capture}\"\n"
            f"printf '%s\\n' '{assistant}'\n"
            f"printf '%s\\n' '{result}'\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
    return fake_bin


def test_delegate_sends_long_prompt_via_stdin() -> None:
    with tempfile.TemporaryDirectory(prefix="codex_with_cc_long_prompt_") as tmp:
        root = Path(tmp)
        artifact_root = root / "artifacts"
        stdin_capture = root / "stdin.txt"
        fake_bin = make_fake_agent_bin(root, stdin_capture)
        long_task = "audit long prompt\n" + ("0123456789abcdef" * 2000)
        task_file = root / "long-task.md"
        task_file.write_text(compliant_task(long_task), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(delegate),
                "-TaskFile",
                str(task_file),
                "-WorkflowId",
                "wf-long-prompt",
                "-TaskId",
                "task-long-prompt",
                "-Role",
                "implementer",
                "-ArtifactRoot",
                str(artifact_root),
                "-SessionKey",
                "long-prompt-session",
                "-BypassPermissions",
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
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)

        run_id = next(line.split(":", 1)[1].strip() for line in result.stdout.splitlines() if line.startswith("RunId:"))
        status = json.loads((artifact_root / f"status_{run_id}.json").read_text(encoding="utf-8"))
        assert status["status"] == "completed"
        captured = stdin_capture.read_text(encoding="utf-8")
        assert "audit long prompt" in captured
        assert len(captured) > 10000
