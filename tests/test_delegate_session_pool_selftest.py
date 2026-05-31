#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def test_delegate_session_pool_selftest_script_passes() -> None:
    if os.name == "nt":
        command = [
            "pwsh",
            "-NoProfile",
            "-File",
            str(REPO / "skills" / "codex-with-cursor" / "windows_scripts" / "test_delegate_session_pool.ps1"),
        ]
    else:
        command = [
            sys.executable,
            str(REPO / "skills" / "codex-with-cursor" / "scripts" / "test_delegate_session_pool.py"),
        ]

    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True)

    assert result.returncode == 0, result.stdout + result.stderr
