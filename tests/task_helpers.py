from __future__ import annotations


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
