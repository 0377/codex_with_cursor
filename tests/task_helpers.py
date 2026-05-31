from __future__ import annotations

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
