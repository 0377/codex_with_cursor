from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contract import contract_list, load_contract

CONTRACT = load_contract()
ARTIFACT_SCHEMA_VERSION = int(CONTRACT["artifactSchemaVersion"])
INVOCATION_CONTRACT = str(CONTRACT["invocationContract"])
CHILD_MARKER_NAME = str(CONTRACT["childThread"]["markerName"])
CHILD_MARKER_VALUE = str(CONTRACT["childThread"]["markerValue"])
REPORT_HEADINGS = contract_list("reportHeadings")
REPORT_STATUS_VALUES = contract_list("reportStatusValues")
WORKER_ROLES = contract_list("workerRoles")
SKILL_NAME = "codex-with-cursor"



class DelegateError(RuntimeError):
    pass



def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()



def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y")
    return bool(value)



def same_path(a: str | Path, b: str | Path) -> bool:
    left = os.path.normcase(os.path.realpath(os.path.abspath(os.fspath(a))))
    right = os.path.normcase(os.path.realpath(os.path.abspath(os.fspath(b))))
    return left == right
