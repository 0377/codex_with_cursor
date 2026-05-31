#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "codex-with-cursor" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from codex_with_cursor_runtime.delegate import _StatusWriteThrottle


def test_status_write_throttle_batches_writes(tmp_path: Path) -> None:
    status_path = tmp_path / "status_test.json"
    status: dict[str, object] = {"linesWritten": 0}
    write_calls: list[Path] = []

    def recording_write_json(path: Path, payload: dict) -> None:
        write_calls.append(path)

    with patch("codex_with_cursor_runtime.delegate.write_json", side_effect=recording_write_json):
        throttle = _StatusWriteThrottle(status_path, status, min_interval_s=3600.0, min_line_delta=50)
        for _ in range(120):
            throttle.bump()
        throttle.bump(force=True)

    assert len(write_calls) < 120
    assert len(write_calls) >= 2
    assert all(path == status_path for path in write_calls)
