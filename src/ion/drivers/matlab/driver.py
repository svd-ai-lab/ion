"""MATLAB driver for ion."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from ion.driver import ConnectionInfo, Diagnostic, LintResult
from ion.runner import run_subprocess


class MatlabDriver:
    """Lean MATLAB driver focused on CLI-first one-shot execution."""

    @property
    def name(self) -> str:
        return "matlab"

    def detect(self, script: Path) -> bool:
        """Treat `.m` files as MATLAB scripts."""
        return script.suffix.lower() == ".m"

    def lint(self, script: Path) -> LintResult:
        """Run MATLAB-native linting when MATLAB is available."""
        if not self.detect(script):
            return LintResult(
                ok=False,
                diagnostics=[Diagnostic(level="error", message="Not a MATLAB `.m` script")],
            )

        matlab = shutil.which("matlab")
        if matlab is None:
            return LintResult(
                ok=False,
                diagnostics=[
                    Diagnostic(
                        level="error",
                        message="MATLAB is not available on PATH; cannot lint `.m` files",
                    )
                ],
            )

        expr = (
            "issues = checkcode('{path}', '-id'); "
            "if isempty(issues), disp(jsonencode(struct('ok', true, 'diagnostics', {{}}))); "
            "else, msgs = strings(numel(issues), 1); "
            "for i = 1:numel(issues), msgs(i) = string(issues(i).message); end; "
            "payload = struct('ok', false, 'diagnostics', cellstr(msgs)); "
            "disp(jsonencode(payload)); end"
        ).format(path=_matlab_string(script.resolve()))

        result = run_subprocess(
            [matlab, "-batch", expr],
            script=script,
            solver=self.name,
        )
        if result.exit_code != 0:
            return LintResult(
                ok=False,
                diagnostics=[
                    Diagnostic(
                        level="error",
                        message=result.stderr or "MATLAB lint command failed",
                    )
                ],
            )

        payload = self.parse_output(result.stdout)
        diagnostics = [
            Diagnostic(level="warning", message=message)
            for message in payload.get("diagnostics", [])
        ]
        return LintResult(ok=payload.get("ok", not diagnostics), diagnostics=diagnostics)

    def connect(self) -> ConnectionInfo:
        """Check if MATLAB is available on PATH."""
        matlab = shutil.which("matlab")
        if matlab is None:
            return ConnectionInfo(
                solver="matlab",
                version=None,
                status="not_installed",
                message="matlab is not available on PATH",
            )

        return ConnectionInfo(
            solver="matlab",
            version=None,
            status="ok",
            message=f"matlab available at {matlab}",
        )

    def parse_output(self, stdout: str) -> dict:
        """Parse the last JSON object printed by a MATLAB script."""
        for line in reversed(stdout.strip().splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return {}

    def run_file(self, script: Path):
        """Execute a MATLAB `.m` script using MATLAB batch mode."""
        matlab = shutil.which("matlab")
        if matlab is None:
            raise RuntimeError("matlab is not available on PATH")

        expr = f"run('{_matlab_string(script.resolve())}')"
        return run_subprocess(
            [matlab, "-batch", expr],
            script=script,
            solver=self.name,
        )


def _matlab_string(path: Path) -> str:
    """Convert a filesystem path to a MATLAB-quoted string literal."""
    text = path.as_posix()
    return re.sub(r"'", "''", text)
