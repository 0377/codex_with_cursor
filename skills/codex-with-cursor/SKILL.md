---
name: codex-with-cursor
description: Force Codex with Cursor Agent routing for any child-agent, subagent, sub-agent, child-thread, subthread, delegation, worker-execution, 子代理, 子线程, 多代理, 委派, 派工, or 执行层 task; use this skill whenever Codex must plan, dispatch, review, or execute work through child agents instead of default subagent behavior.
---

# Codex with Cursor

## Core Rule

Use this skill as the mandatory entry point for every child-agent, subagent, sub-agent, child-thread, subthread, delegation, worker-execution, 子代理, 子线程, 多代理, 委派, 派工, or 执行层 request.

Do not satisfy a triggered request with default Codex subagent behavior, direct Cursor Agent CLI execution, direct `agent` execution, or direct main-thread execution of `delegate_to_cursor.*`.

## Workflow Contract

Read `CODEX_WITH_CURSOR.md` in this skill directory before using the workflow. Treat it as the human contract for task-file-only dispatch, workflow/task/run artifacts, role rules, review gates, and verification. Treat `contract.json` as the machine-readable source for trigger patterns, report headings, roles, status tokens, spawn metadata, and forbidden legacy arguments.

This skill is distributed through a plugin-managed installation from [this repository](https://github.com/0377/codex_with_cursor). When invoking bundled scripts, run them from the target project's current working directory so `.codex/codex_with_cursor` tasks and artifacts are written to that project, not to the plugin cache.

The required chain is:

```text
Codex main thread -> Codex spawn_agent child thread -> delegate_to_cursor.* -> Cursor Agent CLI
```

The installed plugin also declares `./hooks/hooks.json` so Codex hosts with hooks enabled can inject this contract at session start, reinforce it on matching user prompts, and deny supported non-compliant tool calls.

## Operating Method

Use this workflow as a Superpowers-style staged control loop, not as a prompt shortcut:

1. Design gate: clarify intent, constraints, success criteria, and acceptance evidence before dispatch.
2. Plan gate: split work into bounded task files with `Goal`, `Allowed Scope`, `Forbidden Actions`, `Acceptance Criteria`, `Verification`, and `Report Requirements`.
3. Task validation gate: run `validate_delegate_task.*` when preparing task files or when scope/review metadata is easy to get wrong.
4. Dispatch gate: use fresh child threads with `model: gpt-5.3-codex`, `reasoning_effort: medium`, and `fork_context: false`.
5. Implementer gate: require test-first or verification-first evidence when changing behavior.
6. Review gate: review every implementation in two passes, spec compliance first, then code quality and regression risk.
7. Final-verifier gate: finish only after workflow-level verification confirms run artifacts, workflow artifacts, accepted review gates, final-verifier evidence, parallel scope safety, session continuity when relevant, and repository tests support acceptance.

Workers are context consumers, not decision owners. Codex main thread owns architecture, task boundaries, acceptance, rework decisions, and final delivery.

The Codex child thread must:

- Set `CODEX_CURSOR_CHILD_THREAD=1` before invoking `delegate_to_cursor.*`.
- Pass task instructions through `.codex/codex_with_cursor/tasks/<yyyyMMdd>/<HHmmssfff>-<short-id>-<task-name>.md` with `-TaskFile`.
- Pass `-WorkflowId`, `-TaskId`, `-Role`, and `-SessionKey`.
- Avoid legacy inline `-Task`, legacy `-Mode`, and implicit session-key fallback.
- Keep changes inside the delegated scope and pass `-Scope` for any parallel writable work.
- Run the requested verification.
- Ensure any command passed through `-Tests` appears with an outcome in the worker's `Verification` report.

Task files that omit required sections, leave sections empty, keep obvious placeholders, or omit required report headings are rejected before Cursor Agent starts. This keeps worker context explicit and removes the old one-line prompt path.

## Multi-Skill Chain

Use these sibling skills when the work has enough surface area to need staged control:

- `$codex-with-cursor-planning`: turn the request into task files, acceptance criteria, dependencies, and review gates.
- `$codex-with-cursor-dispatching`: choose serial or parallel delegation and assign WorkflowId/TaskId/Role/SessionKey values.
- `$codex-with-cursor-worker`: define the worker task file and scope for Cursor Agent execution.
- `$codex-with-cursor-reviewing`: review worker reports, findings, verification, changed files, and review gate state.
- `$codex-with-cursor-finishing`: verify the whole workflow and prepare final delivery.

## Main Thread Duties

In the main Codex thread:

- Understand the user request, define scope, choose serial or parallel delegation, and review all worker results.
- Prefer serial execution when write scopes overlap or acceptance criteria are still unstable.
- Use parallel execution only for independent read-only tasks or writable tasks with explicit non-overlapping `-Scope` values.
- Do not run `agent` directly.
- Do not run `delegate_to_cursor.*` directly except when `CODEX_WITH_CURSOR.md` explicitly allows the trusted local terminal fallback.
- Verify each run with `verify_delegate_run.*` or `verify_delegate_artifacts.*`.
- Verify the whole workflow with `verify_delegate_workflow.*`; use `verify_delegate_chain.*` when validating primary/parallel session continuity.
- Reject implementer work until both `spec` and `quality` reviewer runs are accepted.
- Reject implementer workflows without an accepted `final-verifier` task.
- Reject parallel implementer runs whose writable scopes overlap.
- Do not summarize a worker as successful until the artifacts and the worker's verification evidence both support that claim.

## Worker Report Contract

Every Cursor Agent worker must finish with these exact headings:

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

`Status` and `Final Result` must use the same token:

```text
DONE
DONE_WITH_CONCERNS
NEEDS_CONTEXT
BLOCKED
FAIL
```

`Role` must use one of:

```text
planner
implementer
researcher
reviewer
final-verifier
```

Verification must list commands actually run and their outcomes. A `DONE` report without concrete verification evidence is invalid. If verification is blocked, the worker must explain the blocker and whether it is unrelated to the delegated change.
