#!/usr/bin/env python3
from pathlib import Path
import json


def test_plugin_manifest_and_docs_contract() -> None:
    repo = Path(__file__).resolve().parents[1]
    codex_plugin_path = repo / ".codex-plugin" / "plugin.json"
    skill_path = repo / "skills" / "codex-with-cursor" / "SKILL.md"
    readme_text = (repo / "README.md").read_text(encoding="utf-8")
    ai_install_text = (repo / "AI_INSTALL.md").read_text(encoding="utf-8")
    legacy_scope_phrase = "".join(("全局", " skill 安装"))
    compat_install_phrase = "".join(("兼容", "安装"))

    assert codex_plugin_path.exists()
    assert not (repo / ".claude-plugin" / "plugin.json").exists()
    assert skill_path.exists()

    codex_plugin = json.loads(codex_plugin_path.read_text(encoding="utf-8"))
    assert codex_plugin["name"] == "codex-with-cursor"
    assert codex_plugin["version"] == "1.1.0"
    assert codex_plugin["skills"] == "./skills/"
    assert codex_plugin["hooks"] == "./hooks/hooks.json"
    assert (repo / "hooks" / "hooks.json").exists()

    codex_interface = codex_plugin["interface"]
    assert codex_interface["displayName"] == "Codex With Cursor"
    assert "Codex" in codex_interface["shortDescription"]
    assert "Cursor Agent" in codex_interface["shortDescription"]
    assert "aiskyhub" not in codex_interface["longDescription"].lower()
    assert "marketplace" not in codex_interface["longDescription"].lower()
    assert "Read" in codex_interface["capabilities"]
    assert "Write" in codex_interface["capabilities"]
    assert any("codex-with-cursor" in prompt for prompt in codex_interface["defaultPrompt"])

    assert "[AI_INSTALL.md](AI_INSTALL.md)" in readme_text
    assert "https://github.com/aiskyhub/codex_with_cc" in readme_text
    assert "安装或更新" in readme_text
    assert "当前 Codex 环境" in readme_text
    assert compat_install_phrase not in readme_text

    assert "marketplace-only" not in ai_install_text
    assert "仓库直装" in ai_install_text
    assert legacy_scope_phrase not in ai_install_text
    assert "codex-with-cursor" in ai_install_text
