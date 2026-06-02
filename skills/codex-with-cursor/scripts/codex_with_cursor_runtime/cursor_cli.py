from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any, Iterable

from .common import DelegateError

from .reports import extract_structured_delegate_report, text_has_required_report_headings


def resolve_agent_executable() -> str | None:
    """Resolve the Cursor Agent CLI binary.

    Only ``agent`` is supported. The legacy ``cursor`` shim is not used because
    headless flags such as ``--print`` and ``--output-format stream-json`` are
    not guaranteed to work on it.
    """
    return shutil.which("agent")


def apply_delegate_report_text(state: dict[str, Any], text: str) -> None:
    trimmed = text.strip()
    if not trimmed:
        return
    state["sawAssistantText"] = True
    state["assistantTexts"].append(trimmed)
    current = str(state.get("finalText") or "").strip()
    if text_has_required_report_headings(trimmed):
        state["capturedFinalResultHeading"] = True
        state["finalText"] = trimmed
        return
    extracted = extract_structured_delegate_report(trimmed)
    if extracted:
        state["capturedFinalResultHeading"] = True
        state["finalText"] = extracted
        return
    if current and text_has_required_report_headings(current):
        return
    if current:
        extracted_current = extract_structured_delegate_report(current)
        if extracted_current:
            state["capturedFinalResultHeading"] = True
            state["finalText"] = extracted_current
            return
    state["finalText"] = trimmed


def text_blocks(content: Any) -> list[str]:
    if content is None:
        return []
    items = content if isinstance(content, list) else [content]
    out: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("type") == "text" and str(item.get("text", "")).strip():
            out.append(str(item["text"]))
    return out


def update_stream_capture(record: dict[str, Any], state: dict[str, Any]) -> list[str]:
    state.setdefault("assistantTexts", [])
    state.setdefault("traceLines", [])
    state.setdefault("finalText", "")
    state.setdefault("sawAssistantText", False)
    state.setdefault("sawResultSuccess", False)
    state.setdefault("capturedFinalResultHeading", False)
    state.setdefault("cursorSessionId", None)

    trace_lines: list[str] = []
    record_type = str(record.get("type", ""))
    if record_type == "system":
        parts = ["[system]"]
        if record.get("subtype"):
            parts.append(str(record["subtype"]))
        if record.get("status"):
            parts.append(str(record["status"]))
        trace_lines.append(" ".join(parts))
        if str(record.get("subtype", "")) == "init" and record.get("session_id"):
            state["cursorSessionId"] = str(record["session_id"])
    elif record_type == "assistant":
        message = record.get("message") if isinstance(record.get("message"), dict) else {}
        message_id = message.get("id")
        trace_lines.append(f"[assistant] message={message_id}" if message_id else "[assistant]")
        texts = text_blocks(message.get("content"))
        if texts:
            text = "\n".join(texts).strip()
            if text:
                apply_delegate_report_text(state, text)
        if record.get("session_id"):
            state["cursorSessionId"] = str(record["session_id"])
    elif record_type == "result":
        subtype = str(record.get("subtype", ""))
        line = "[result]"
        if subtype:
            line += f" {subtype}"
        if record.get("duration_ms") is not None:
            line += f" duration_ms={record['duration_ms']}"
        if subtype == "success":
            state["sawResultSuccess"] = True
        result_text = str(record.get("result", "")).strip()
        if result_text:
            apply_delegate_report_text(state, result_text)
        if record.get("session_id"):
            state["cursorSessionId"] = str(record["session_id"])
        trace_lines.append(line)
    elif record_type == "stream_event":
        event = record.get("event") if isinstance(record.get("event"), dict) else {}
        event_type = str(event.get("type", ""))
        trace_lines.append(f"[stream] {event_type}" if event_type else "[stream]")
    elif record_type:
        trace_lines.append(f"[{record_type}]")
    else:
        trace_lines.append("[unknown-record]")
    state["traceLines"].extend(trace_lines)
    return trace_lines


def new_cursor_cli_args(
    model: str,
    session_id: str,
    resume: bool,
    bypass_permissions: bool,
    workspace: str | None = None,
) -> list[str]:
    args = [
        "--print",
        "--output-format",
        "stream-json",
        "--model",
        model,
    ]
    if workspace:
        args.extend(["--workspace", workspace])
    if resume and session_id:
        args.extend(["--resume", session_id])
    if bypass_permissions:
        args.extend(["--yolo", "--trust"])
    return args


def validate_cursor_model(agent_bin: str, model: str) -> None:
    try:
        result = subprocess.run(
            [agent_bin, "--list-models"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except OSError as exc:
        raise DelegateError(f"Failed to run agent --list-models: {exc}") from exc
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
        raise DelegateError(f"agent --list-models failed with exit code {result.returncode}. {output.strip()}")
    if model not in output:
        raise DelegateError(
            f"Cursor model {model!r} was not found by agent --list-models. "
            "Pass -Model with an ID from agent --list-models or use -SkipModelCheck to bypass."
        )


def non_json_raw_lines(raw_lines: Iterable[str]) -> list[str]:
    out: list[str] = []
    for line in raw_lines:
        if not str(line).strip():
            continue
        try:
            json.loads(str(line))
        except json.JSONDecodeError:
            out.append(str(line).strip())
    return out


def retry_decision(
    raw_lines: Iterable[str],
    resume_attempt: bool,
    exit_code: int,
    saw_assistant_text: bool,
    saw_result_success: bool,
    captured_final_result_heading: bool,
) -> dict[str, Any]:
    joined = "\n".join(non_json_raw_lines(raw_lines))
    saw_stale = re.search(
        r"(No conversation found|session.*not found|invalid.*session|unknown.*session)",
        joined,
        re.IGNORECASE,
    ) is not None
    saw_stream_json = re.search(r"stream-json|output-format", joined, re.IGNORECASE) is not None
    has_structured_success = saw_result_success and captured_final_result_heading
    decision = {
        "shouldRetry": False,
        "retryReason": "",
        "retryWithFreshSession": False,
        "sawStaleSessionText": saw_stale,
        "sawStreamJsonVerboseError": saw_stream_json,
        "hasStructuredSuccess": has_structured_success,
        "exitCode": exit_code,
        "sawAssistantText": saw_assistant_text,
        "sawResultSuccess": saw_result_success,
        "capturedFinalResultHeading": captured_final_result_heading,
        "retryWithReportRepair": False,
    }
    if resume_attempt and saw_stale and not has_structured_success:
        decision.update({"shouldRetry": True, "retryReason": "stale_cursor_session", "retryWithFreshSession": True})
    elif saw_stream_json and not has_structured_success and exit_code != 0:
        decision.update({"shouldRetry": True, "retryReason": "stream_json_startup", "retryWithFreshSession": False})
    elif exit_code == 0 and saw_result_success and saw_assistant_text and not has_structured_success:
        decision.update(
            {
                "shouldRetry": True,
                "retryReason": "unstructured_success_report",
                "retryWithFreshSession": False,
                "retryWithReportRepair": True,
            }
        )
    return decision


def failure_summary(raw_lines: Iterable[str], retry_reason: str | None, attempt_count: int, max_retry_count: int, exit_code: int) -> str:
    seen: list[str] = []
    for line in non_json_raw_lines(raw_lines):
        if line not in seen:
            seen.append(line)
        if len(seen) >= 2:
            break
    snippet = " | ".join(seen) if seen else "No non-JSON stderr summary was captured."
    reason = retry_reason or "unknown_retry_condition"
    max_attempts = max_retry_count + 1
    return (
        f"NEED_HUMAN_INTERVENTION after exhausting retry budget. retryReason={reason}. "
        f"attempt {attempt_count}/{max_attempts}. exitCode={exit_code}. {snippet}"
    )
