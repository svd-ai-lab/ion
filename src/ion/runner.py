"""Subprocess execution engine for ion."""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ion.driver import RunResult


def execute_script(
    script: Path,
    python: str | None = None,
    solver: str = "unknown",
) -> RunResult:
    """Execute a Python script in a subprocess and capture results."""
    if python is None:
        python = sys.executable

    start = time.monotonic()
    proc = subprocess.run(
        [python, str(script)],
        capture_output=True,
        text=True,
    )
    duration = time.monotonic() - start

    return RunResult(
        exit_code=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
        duration_s=round(duration, 3),
        script=str(script),
        solver=solver,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
