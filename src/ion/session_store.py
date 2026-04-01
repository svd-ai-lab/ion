"""Persistent session history → ~/.ion/sessions/<session-id>.json."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ion.home import ION_HOME

_log = logging.getLogger("ion.server")


class SessionStore:
    def __init__(self) -> None:
        self.sessions_dir = ION_HOME / "sessions"

    def create(self, session_id: str, metadata: dict) -> Path:
        """Create a new session record."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "session_id": session_id,
            **metadata,
            "runs": [],
            "disconnected_at": None,
        }
        path = self.sessions_dir / f"{session_id}.json"
        path.write_text(json.dumps(record, indent=2))
        return path

    def append_run(self, session_id: str, run_record: dict) -> None:
        """Append an exec record to the session file."""
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            _log.warning("session file missing for %s, skipping persist", session_id)
            return
        data = json.loads(path.read_text())
        data["runs"].append(run_record)
        path.write_text(json.dumps(data, indent=2))

    def close(self, session_id: str, disconnected_at: float) -> None:
        """Mark a session as disconnected."""
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return
        data = json.loads(path.read_text())
        data["disconnected_at"] = disconnected_at
        path.write_text(json.dumps(data, indent=2))

    def get(self, session_id: str) -> dict | None:
        """Read a session record by ID."""
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def list(self) -> list[dict]:
        """List all sessions, newest first."""
        if not self.sessions_dir.exists():
            return []
        sessions = []
        for f in sorted(self.sessions_dir.glob("*.json")):
            data = json.loads(f.read_text())
            sessions.append(data)
        return list(reversed(sessions))
