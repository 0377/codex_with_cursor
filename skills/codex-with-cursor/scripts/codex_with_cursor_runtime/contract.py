from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def load_contract() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "contract.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def contract_list(name: str) -> tuple[str, ...]:
    value = load_contract().get(name, [])
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def cursor_agent_contract() -> dict[str, Any]:
    value = load_contract().get("cursorAgent", {})
    return value if isinstance(value, dict) else {}


def default_cursor_model() -> str:
    return str(cursor_agent_contract().get("defaultModel") or "composer-2.5")


def cursor_agent_executable() -> str:
    return str(cursor_agent_contract().get("executable") or "agent")
