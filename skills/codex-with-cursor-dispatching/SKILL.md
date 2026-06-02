---
name: codex-with-cursor-dispatching
description: Dispatch codex-with-cursor tasks through the required Codex child thread to delegate_to_cursor.* to Cursor Agent CLI chain with WorkflowId, TaskId, Role, and Scope metadata.
---

# Codex with Cursor Dispatching

Read `../codex-with-cursor/CODEX_WITH_CURSOR.md` before dispatching. Use this skill after planning has produced task boundaries.

Dispatch rules:

- Every child thread uses `model: gpt-5.4`, `reasoning_effort: medium`, and `fork_context: false`.
- Every worker command sets `CODEX_CURSOR_CHILD_THREAD=1`.
- Every worker command passes `-TaskFile`, `-WorkflowId`, `-TaskId`, `-Role`, and `-SessionKey`.
- Run `validate_delegate_task.*` before dispatch when the task file was generated, contains reviewer metadata, or carries explicit `-Tests` commands.
- Never dispatch legacy inline `-Task`, legacy `-Mode`, or a command that relies on an implicit session key.
- Reviewer commands must pass `-ReviewForTaskId` and `-ReviewKind spec` or `-ReviewKind quality`.
- Parallel writable tasks require explicit non-overlapping `-Scope` values.
- Use `PrimaryAnchor` for a parallel batch anchor, `ParallelPool` for independent side work, and `PrimaryReuse` for serial follow-up.

Dispatch discipline:

- Dispatch the immediate blocking task locally only when no child-thread delegation is needed; otherwise create the Codex child thread and keep the main thread focused on review.
- Put all worker instructions in a TaskFile with `Goal`, `Allowed Scope`, `Forbidden Actions`, `Acceptance Criteria`, `Verification`, and `Report Requirements`; the runtime rejects old one-line prompts.
- Include the exact verification commands in the task file and pass them with `-Tests` when possible.
- The worker's final `Verification` report must include every command passed with `-Tests` and the observed outcome.
- Dispatch implementer, spec reviewer, and quality reviewer as separate task ids so the workflow artifact can prove acceptance.
- Dispatch a final-verifier task for any workflow with implementer tasks.
- Use parallel dispatch only after scope boundaries are explicit enough to avoid file conflicts.
- After a parallel batch, wait for the anchor and side tasks before serial review or follow-up implementation.

Do not dispatch default Codex workers outside the codex-with-cursor chain.

## spawn_agent message (platform gate)

The PreToolUse gate inspects the serialized `spawn_agent` payload. Keep the message at the orchestration layer:

- Include `CODEX_CURSOR_CHILD_THREAD=1`, `delegate_to_cursor.ps1` or `delegate_to_cursor.sh`, and every required delegate flag: `-TaskFile`, `-WorkflowId`, `-TaskId`, `-Role`, `-SessionKey`.
- Point the child thread at the installed `codex-with-cursor-dispatching` skill and the on-disk TaskFile instead of pasting the Standard Worker Command block from `CODEX_WITH_CURSOR.md`.
- Prose may mention the workflow name `codex-with-cursor` or phrases such as "Cursor Agent CLI" when explaining what the child must not run directly.
- Do not paste executable `agent ...` or `cursor ...` CLI examples into `spawn_agent.message`; those belong only inside the child thread's `delegate_to_cursor.*` runtime, not in the spawn payload.
- Do not embed the full TaskFile body in `spawn_agent.message` when Forbidden Actions mention avoiding direct CLI usage; keep task instructions in `-TaskFile` only.
