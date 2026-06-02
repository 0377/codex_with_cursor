# Codex with Cursor

This is the portable contract for the Codex main thread -> Codex child thread -> Cursor Agent CLI workflow.

## Required Reading
Read this file before using the workflow in this repository. Treat `contract.json` as the machine-readable source for roles, status tokens, report headings, trigger patterns, required spawn metadata, and forbidden legacy arguments.

## Core Contract
1. Any child-agent, subagent, sub-agent, child-thread, subthread, delegation, worker-execution, 子代理, 子线程, 多代理, 委派, 派工, or 执行层 request must use this workflow.
2. Do not replace it with the default Codex subagent flow, host worker shortcuts, direct `agent`, or direct main-thread `delegate_to_cursor.*`.
3. The Codex main thread owns design, task boundaries, acceptance criteria, review decisions, rework decisions, and final delivery.
4. Every Cursor Agent worker run must be carried by a fresh Codex `spawn_agent` child thread using `model: gpt-5.4`, `reasoning_effort: medium`, and `fork_context: false`.
5. The child thread must set `CODEX_CURSOR_CHILD_THREAD=1` before invoking `delegate_to_cursor.*`.
6. Delegate commands must use task-file-only invocation. `-TaskFile`, `-WorkflowId`, `-TaskId`, `-Role`, and `-SessionKey` are required.
7. Legacy inline `-Task`, legacy `-Mode`, missing workflow metadata, and implicit session-key fallback are not supported.
8. `delegate_to_cursor.*` must not pass `--effort`; Cursor Agent uses its configured default effort.
9. Workers must follow the TaskFile contract: Goal, Allowed Scope, Forbidden Actions, Acceptance Criteria, Verification, and Report Requirements.
10. Task files with empty sections, obvious placeholders, or incomplete Report Requirements are invalid; use `validate_delegate_task.*` before dispatch when preparing non-trivial work.
11. Workers must finish with the exact report headings and concrete verification evidence.
12. If Cursor emits progress text before `Status`, or the stream-json `result` field prepends a full-session transcript, the delegate wrapper extracts the last compliant report block from the final text before acceptance. That recovery is not the same as a zero-output run; do not treat `UNSTRUCTURED_SUCCESS_REJECTED` as proof that no work was done when deliverable files exist.
13. Implementer workflows require accepted `spec` and `quality` reviewer runs plus an accepted `final-verifier` run before workflow acceptance.

## Trigger Rule
Any user mention of child-agent, subagent, sub-agent, child-thread, subthread, delegation, worker-execution, or Chinese equivalents such as 子代理、子线程、多代理、委派、派工、执行层 is a workflow trigger. When triggered, the main Codex thread must use this custom delegation workflow and must not satisfy the request with the default Codex subagent flow, a host-provided agent shortcut, direct `agent` execution, or direct main-thread execution of `delegate_to_cursor.*`.

## workflow/task/run Protocol
The protocol models every request as:

- `WorkflowId`: one user-level orchestration.
- `TaskId`: one scoped child-thread assignment inside that workflow.
- `RunId`: one concrete Cursor Agent execution attempt for a task.
- `Role`: one of `planner`, `implementer`, `researcher`, `reviewer`, or `final-verifier`.

Artifacts use the current artifact schema. Each run writes `config_<RunId>.json`, `status_<RunId>.json`, `prompt_<RunId>.md`, `stream_<RunId>.jsonl`, `trace_<RunId>.log`, and `cursor_<RunId>.md`. Each workflow also writes `workflow_<WorkflowId>.json`, which indexes tasks, runs, scope, verification, review metadata, and final acceptance state.

Reviewer runs must pass `-ReviewForTaskId` and `-ReviewKind spec` or `-ReviewKind quality`. Implementer tasks are not workflow-accepted until both spec and quality reviews are accepted. Task dependencies can be recorded with repeated `-DependsOn <task-id>` values.

## Workflow Method
Use this as a controlled delivery pipeline, borrowing the core discipline from Superpowers:

1. Design gate: clarify the goal, success criteria, scope, constraints, and acceptance evidence before dispatch.
2. Plan gate: split work into task-file-sized assignments with explicit allowed scope, forbidden actions, verification commands, and review gates.
3. Dispatch gate: create a fresh child thread per task; do not let workers inherit noisy main-thread context.
4. Implementer gate: implementation workers must use test-first or the smallest equivalent verification-first evidence when the repository has a practical test surface.
5. Review in two passes. First perform spec compliance review; then perform quality review for minimality, maintainability, regression risk, and test sufficiency.
6. Final-verifier gate: use a final verifier to confirm the aggregate workflow, residual risks, declared verification evidence, and accepted review gates.
7. Finish with evidence: run artifact verification, workflow verification, session continuity checks when relevant, and repository regression tests.

If any stage lacks evidence, the main thread must request rework or report the blocker instead of smoothing over the gap.

## TaskFile Contract
Every `-TaskFile` must contain these sections:

- `Goal`: the exact assignment for this worker.
- `Allowed Scope`: files, directories, or behavior the worker may inspect or change.
- `Forbidden Actions`: files, behaviors, and follow-up work the worker must not execute.
- `Acceptance Criteria`: self-checks before reporting.
- `Verification`: exact commands to run, or the smallest meaningful verification expected.
- `Report Requirements`: the required report headings and status rules.

The runtime rejects task files that do not contain these sections, leave required sections empty, retain obvious placeholders, or omit required report headings from `Report Requirements`. This makes worker context explicit and prevents old one-line prompts from acting as hidden orchestration.

Pre-dispatch validation:

```powershell
pwsh -NoProfile -File <installed-workflow-root>\windows_scripts\validate_delegate_task.ps1 `
  -TaskFile .\.codex\codex_with_cursor\tasks\<task-file>.md `
  -Role implementer `
  -Tests "pytest -q"
```

```bash
"<installed-workflow-root>/macos_scripts/validate_delegate_task.sh" \
  -TaskFile ./.codex/codex_with_cursor/tasks/<task-file>.md \
  -Role implementer \
  -Tests "pytest -q"
```

## Platform Hook Gate
The Codex plugin declares `./hooks/hooks.json` as a semi-hard platform gate. When hooks are enabled:

- `SessionStart` injects this full contract.
- `UserPromptSubmit` reinforces the contract for delegation trigger words.
- `PreToolUse` denies visible direct `agent`, direct main-thread `delegate_to_cursor.*`, missing `CODEX_CURSOR_CHILD_THREAD=1`, missing `-TaskFile`, missing workflow metadata, missing `-SessionKey`, legacy `-Task`, legacy `-Mode`, reviewer runs without review metadata, and parallel writable runs without `-Scope`.
- `spawn_agent` messages should stay at the codex-with-cursor orchestration layer: required child-thread marker, `delegate_to_cursor.*`, and workflow metadata. Prose may reference `codex-with-cursor` or explain that the child must not call the CLI directly; do not paste executable `agent ...` examples into the spawn payload. The Standard Worker Command below is for the child thread only.

The hook reads `contract.json` for shared tokens. This is not a kernel boundary; final responsibility remains with the Codex main thread.

## Trusted Local Terminal Fallback
This fallback is an execution-location fallback only. Preserve the same `CODEX_CURSOR_CHILD_THREAD=1` marker, task file, `WorkflowId`, `TaskId`, `Role`, `SessionKey`, session mode, artifact root, scope, and permission flags that the child thread would have used.

Do not replace this with the default Codex subagent flow, a direct `agent` command, or a modified worker command. Report that the trusted terminal fallback was used and include the command outcome in verification.

## Roles
- Codex main thread: clarify intent, approve design, define task files, create child threads, review results, request rework, and decide final acceptance.
- Codex child thread: provide the visible conversation-tree node and invoke the worker script.
- Cursor Agent CLI: execute the delegated task, run verification, and produce a structured report.

Worker roles:

- `planner`: read-only task decomposition and acceptance criteria.
- `implementer`: code or file changes inside assigned scope.
- `researcher`: read-only codebase or architecture investigation.
- `reviewer`: spec compliance or quality review for a target implementer task.
- `final-verifier`: workflow-level acceptance and residual risk summary.

Workers are context consumers, not decision owners. They must not create nested delegate runs, broaden scope, or decide that unassigned follow-up work should be executed. When a worker lacks context, it reports `NEEDS_CONTEXT`.

## Session Modes
- `PrimaryReuse`: default serial mode. Reuses the main Cursor session for continuity.
- `PrimaryAnchor`: parallel-batch anchor. Its result becomes the main reusable context for later serial work.
- `ParallelPool`: independent parallel side work. Uses reusable pool sessions without writing to the main session.

Only use `-AllowParallel` when task scopes are independent. Parallel writable tasks must pass explicit `-Scope` values. After parallel work, return to serial review before accepting implementation changes.

## Worker Output
Cursor Agent must finish with these exact headings:

```text
Status
Role
Summary
Changed Files
Verification
Findings
Final Result
Risks Or Follow-ups
```

Status and Final Result must match exactly. `Status` and `Final Result` must use one of:

```text
DONE
DONE_WITH_CONCERNS
NEEDS_CONTEXT
BLOCKED
FAIL
```

Verification must list commands actually run and their outcomes. A `DONE` report without concrete verification evidence is invalid. If verification is blocked, the report must explain the blocker and whether it is unrelated to the delegated change.

The report is evidence, not a success claim by itself. Reviewers and final verifiers should treat missing commands, vague outcomes, role mismatch, status mismatch, or scope drift as acceptance blockers.

## Artifacts
Delegation artifacts are written under `.codex/codex_with_cursor/cursor-delegate` by default. If that project-local default is not writable, the runtime falls back to a user-level path under `$CODEX_HOME/codex_with_cursor/cursor-delegate/<project-key>`; explicit `-ArtifactRoot` values are still treated as authoritative and fail fast when unusable.

- `workflow_<WorkflowId>.json`
- `cursor_<RunId>.md`
- `status_<RunId>.json`
- `config_<RunId>.json`
- `prompt_<RunId>.md`
- `stream_<RunId>.jsonl`
- `trace_<RunId>.log`
- `session-pools/<SessionKey>.json`

Use `verify_delegate_run.*` or `verify_delegate_artifacts.*` for each run, `verify_delegate_workflow.*` for the workflow aggregate, and `verify_delegate_chain.*` for multi-run session continuity checks. `verify_delegate_workflow.*` enforces review gates, the final-verifier gate, declared `-Tests` evidence for non-dry-run `DONE` reports, and non-overlapping parallel implementer scopes. The shared implementation lives under `scripts/*.py`; platform wrappers stay thin.

`<installed-workflow-root>` means the installed `skills/codex-with-cursor` directory, for example `<codex-home>/plugins/cache/.../codex-with-cursor/<version-or-hash>/skills/codex-with-cursor` after `codex plugin install` from [this repository](https://github.com/0377/codex_with_cursor). Do not use the package root `<version-or-hash>` directory.

## Command-Line Parameter Layers

Do not mix the three parameter systems below. Only the bottom layer is the Cursor Agent CLI (`agent`).

| Layer | Who invokes it | Example parameters | Maps to Cursor CLI? |
|-------|----------------|--------------------|---------------------|
| Codex child thread | Main thread `spawn_agent` | `model: gpt-5.4`, `reasoning_effort: medium`, `fork_context: false` | No |
| Delegate wrapper | Child thread `delegate_to_cursor.*` | `-TaskFile`, `-WorkflowId`, `-TaskId`, `-Role`, `-SessionKey`, optional `-Model`, `-Scope`, `-BypassPermissions` | No (orchestration only) |
| Cursor Agent CLI | `delegate_to_cursor` runtime | `--print`, `--output-format stream-json`, `--model`, `--resume`, `--yolo`, `--trust` | Yes |

Delegate defaults and Cursor mapping:

- `-Model` defaults to `composer-2.5` when omitted. Override with any ID from `agent --list-models`.
- `-Model` becomes `agent --model <id>`. It is not a Codex `spawn_agent` model.
- `-BypassPermissions` adds `--yolo` and `--trust` on the `agent` invocation.
- The worker prompt is sent on stdin, not as positional `agent` arguments.
- Forbidden on the `agent` invocation: `--effort`, legacy `--name`.
- Only the `agent` executable is resolved; the `cursor` shim is not used as a fallback.
- Each run records `cursorCliExecutable`, `lastCursorCliArgv`, and per-attempt `cursorCliArgv` in `config_<RunId>.json` / `status_<RunId>.json`.

## Standard Worker Command
Normally run this inside a Codex child thread. If the Codex sandbox or delegated runner cannot execute it, use the trusted local terminal fallback above.

Windows:

```powershell
$workflowRoot = '<installed-workflow-root>'
$env:CODEX_CURSOR_CHILD_THREAD = '1'
pwsh -NoProfile -File (Join-Path $workflowRoot 'windows_scripts\delegate_to_cursor.ps1') `
  -TaskFile .\.codex\codex_with_cursor\tasks\<yyyyMMdd>\<HHmmssfff>-<short-id>-<task-file>.md `
  -WorkflowId <workflow-id> `
  -TaskId <task-id> `
  -Role implementer `
  -SessionKey <stable-session-key> `
  -Scope <changed-or-inspected-path> `
  -SessionMode PrimaryReuse `
  -BypassPermissions
```

macOS:

```bash
WORKFLOW_ROOT="<installed-workflow-root>"
export CODEX_CURSOR_CHILD_THREAD=1
"$WORKFLOW_ROOT/macos_scripts/delegate_to_cursor.sh" \
  -TaskFile ./.codex/codex_with_cursor/tasks/<yyyyMMdd>/<HHmmssfff>-<short-id>-<task-file>.md \
  -WorkflowId <workflow-id> \
  -TaskId <task-id> \
  -Role implementer \
  -SessionKey <stable-session-key> \
  -Scope <changed-or-inspected-path> \
  -SessionMode PrimaryReuse \
  -BypassPermissions
```

Reviewer runs add `-Role reviewer -ReviewForTaskId <implementer-task-id> -ReviewKind spec` or `-Role reviewer -ReviewForTaskId <implementer-task-id> -ReviewKind quality`.

## Verification
Run local regression tests after installing or changing this workflow.

Windows:

```powershell
$workflowRoot = '<installed-workflow-root>'
pwsh -NoProfile -File (Join-Path $workflowRoot 'windows_scripts\test_delegate_runtime.ps1')
pwsh -NoProfile -File (Join-Path $workflowRoot 'windows_scripts\test_delegate_session_pool.ps1')
```

macOS:

```bash
WORKFLOW_ROOT="<installed-workflow-root>"
"$WORKFLOW_ROOT/macos_scripts/test_delegate_runtime.sh"
"$WORKFLOW_ROOT/macos_scripts/test_delegate_session_pool.sh"
```

Verify a run and workflow with `verify_delegate_run.*` and `verify_delegate_workflow.*`.

Dry-run stdout includes `Cursor Session Id: <uuid>` and `Cursor Session Argument: <new session>|<--resume> <uuid>` (human-readable summary, not raw CLI argv). New pool leases use `<new session>`; resumed leases use `--resume`.
