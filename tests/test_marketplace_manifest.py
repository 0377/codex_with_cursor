#!/usr/bin/env python3
from pathlib import Path
import json


def test_marketplace_manifest_contract() -> None:
    repo = Path(__file__).resolve().parents[1]
    marketplace_path = repo / ".agents" / "plugins" / "marketplace.json"
    plugin_path = repo / ".codex-plugin" / "plugin.json"

    assert marketplace_path.exists()
    assert not (repo / ".claude-plugin" / "marketplace.json").exists()

    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))

    assert marketplace["name"] == "codex-with-cursor"
    assert marketplace["interface"]["displayName"] == "Codex With Cursor"
    assert len(marketplace["plugins"]) == 1

    entry = marketplace["plugins"][0]
    assert entry["name"] == plugin["name"] == "codex-with-cursor"
    assert entry["source"]["source"] == "local"
    assert entry["source"]["path"] == "./plugins/codex-with-cursor"
    assert entry["policy"]["installation"] == "AVAILABLE"
    assert entry["policy"]["authentication"] == "ON_INSTALL"
    assert entry["category"] == "Development"
