#!/usr/bin/env python3
"""Shared Codex Fable5 local state helpers."""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback only.
    fcntl = None

STATE_DIR = Path(".codex-fable5")
GOALS_FILE = STATE_DIR / "goals.json"
FINDINGS_FILE = STATE_DIR / "findings.json"
LEDGER_FILE = STATE_DIR / "ledger.jsonl"
LOCK_FILE = STATE_DIR / "state.lock"
LOCK_TIMEOUT_SECONDS = 30.0


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def locked_state() -> Iterator[None]:
    STATE_DIR.mkdir(exist_ok=True)
    if fcntl is None:
        fallback = STATE_DIR / "state.lockdir"
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fallback.mkdir()
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    sys.exit(f"codex-fable5: timed out waiting for state lock ({fallback}).")
                time.sleep(0.05)
        try:
            yield
        finally:
            fallback.rmdir()
        return

    with LOCK_FILE.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(
            f"codex-fable5: {label} is not valid JSON "
            f"({path}:{exc.lineno}:{exc.colno}: {exc.msg})."
        )


def write_json(path: Path, data: dict[str, Any]) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    tmp_name = ""
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=STATE_DIR,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        tmp_name = handle.name
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    Path(tmp_name).replace(path)


def append_event(event: str, **fields: Any) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    record = {"ts": now(), "event": event, **fields}
    with LEDGER_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def require_object(value: Any, path: Path, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        sys.exit(f"codex-fable5: {label} must be a JSON object ({path}).")
    return value
