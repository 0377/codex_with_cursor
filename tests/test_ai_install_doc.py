#!/usr/bin/env python3
from pathlib import Path

repo = Path(__file__).resolve().parents[1]


def test_ai_install_doc_contract() -> None:
    text = (repo / "AI_INSTALL.md").read_text(encoding="utf-8")
    legacy_installer_stem = "_".join(("install", "codex", "with", "cc"))
    legacy_scope_phrase = "".join(("全局", " skill"))
    compat_phrase = "".join(("兼容", "路径"))

    assert "codex plugin install https://github.com/0377/codex_with_cursor" not in text
    assert "codex plugin install /path/to/codex_with_cursor" not in text
    assert "codex-with-cursor@aiskyhub" not in text
    assert "marketplace-only" not in text
    assert "Git marketplace" in text or "marketplace" in text
    assert "codex plugin marketplace add 0377/codex_with_cursor" in text
    assert "codex plugin marketplace add /path/to/codex_with_cursor" in text
    assert "git clone https://github.com/0377/codex_with_cursor.git" in text
    assert "codex plugin marketplace list" in text
    assert "codex plugin add codex-with-cursor@<MARKETPLACE>" in text
    assert "codex plugin marketplace upgrade <MARKETPLACE>" in text
    assert ".agents/plugins/marketplace.json" in text
    assert "已废弃的 `codex plugin install`" in text
    assert '[plugins."codex-with-cursor@codex-with-cursor"]' in text
    assert "如果宿主环境还没有安装 `codex` CLI，先自动安装官方 CLI，再继续后续步骤。" in text
    assert "### 1. 检查并安装 Codex CLI" in text
    assert "command -v agent" in text
    assert "Get-Command codex -ErrorAction SilentlyContinue" in text
    assert "command -v codex" in text
    assert "npm i -g @openai/codex" in text
    assert "若 `npm` 不存在或安装失败，直接报告失败并停止" in text
    assert "$codex-with-cursor" in text
    assert "docs/codex_with_cc" in text
    assert ".codex/skills/codex-with-cc" in text
    assert "<!-- BEGIN CODEX_WITH_CC --> ... <!-- END CODEX_WITH_CC -->" in text
    assert "$HOME/.codex/skills/codex-with-cc" in text
    assert "Any user mention of child-agent, subagent, sub-agent, child-thread, subthread, delegation, worker-execution, or Chinese equivalents such as 子代理、子线程、多代理、委派、派工、执行层 is a workflow trigger." in text
    assert "delegate_to_cursor" in text
    assert "CODEX_CURSOR_CHILD_THREAD" in text
    assert ".codex/codex_with_cursor/cursor-delegate" in text
    assert "cursor_<RunId>.md" in text
    assert "workflow/task/run" in text
    assert "WorkflowId" in text
    assert "verify_delegate_run" in text
    assert "verify_delegate_workflow" in text
    assert "<installed-workflow-root>" in text
    assert "skills/codex-with-cursor" in text
    assert ".claude-plugin/marketplace.json" not in text
    assert "## 安装或更新完成后告知用户" in text
    assert "marketplace 名称" in text
    assert "marketplace upgrade" in text
    assert f"{legacy_installer_stem}.ps1" not in text
    assert legacy_scope_phrase not in text
    assert compat_phrase not in text
