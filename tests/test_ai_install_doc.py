#!/usr/bin/env python3
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
text = (repo / "AI_INSTALL.md").read_text(encoding="utf-8")

assert "<workflow-root>/<platform_scripts>/delegate_to_claude.* -> scripts/*.py -> Claude Code CLI" in text
assert "Any user mention of child-agent, subagent, sub-agent, child-thread, subthread, delegation, worker-execution, or Chinese equivalents such as 子代理、子线程、多代理、委派、派工、执行层 is a workflow trigger." in text
assert "codex_with_cc/scripts/delegate_to_claude.py" in text
assert "<workflow-root>\\windows_scripts\\test_delegate_runtime.ps1" in text
assert "<workflow-root>/macos_scripts/test_delegate_runtime.sh" in text
assert "Windows 目标项目不要安装 `macos_scripts`；macOS 目标项目不要安装 `windows_scripts`。两个平台都必须安装共享的 `scripts/*.py`。" in text
assert "macOS 支持尚未实现" not in text

print("ai install doc tests passed")
