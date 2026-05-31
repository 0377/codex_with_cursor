from __future__ import annotations

import os
import sys
from pathlib import Path

FAKE_AGENT_LIST_MODELS_PY = """
if '--list-models' in sys.argv:
    print('composer-2.5')
    raise SystemExit(0)
"""

FAKE_AGENT_LIST_MODELS_SH = """
for arg in "$@"; do
  if [ "$arg" = "--list-models" ]; then
    printf '%s\\n' 'composer-2.5'
    exit 0
  fi
done
"""

FAKE_AGENT_LIST_MODELS_CMD = (
    '@echo off\n'
    'if "%1"=="--list-models" (\n'
    '  echo composer-2.5\n'
    '  exit /b 0\n'
    ')\n'
)


def write_fake_agent_python_shim(fake_bin: Path, script: Path) -> Path:
    """Install a fake ``agent`` on PATH that forwards to ``script``; return the resolved shim path."""
    fake_bin.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        shim = fake_bin / "agent.cmd"
        shim.write_text(
            FAKE_AGENT_LIST_MODELS_CMD + f'"{sys.executable}" "{script}" %*\n',
            encoding="utf-8",
        )
        return shim
    shim = fake_bin / "agent"
    shim.write_text(
        "#!/bin/sh\n"
        f"{FAKE_AGENT_LIST_MODELS_SH}"
        f"exec '{sys.executable}' '{script}' \"$@\"\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return shim


def compliant_task(text: str, verification: str = "dry-run artifact generation completed") -> str:
    return f"""# Delegated Task

Goal
{text}

Allowed Scope
- skills/codex-with-cursor

Forbidden Actions
- Do not edit README.md.
- Do not invoke nested delegate runs.

Acceptance Criteria
- The task stays inside the assigned scope.
- The worker report contains concrete verification evidence.

Verification
- {verification}

Report Requirements
- Status / Role / Summary / Changed Files / Verification / Findings / Final Result / Risks Or Follow-ups
"""
