"""Tests for ion run — Phase 2."""
import json
from pathlib import Path

from click.testing import CliRunner

from ion.cli import main
from ion.runner import execute_script

FIXTURES = Path(__file__).parent / "fixtures"


class TestRunner:
    def test_captures_stdout(self):
        result = execute_script(FIXTURES / "mock_solver.py")
        assert "3.72" in result.stdout

    def test_exit_code_zero(self):
        result = execute_script(FIXTURES / "mock_solver.py")
        assert result.exit_code == 0

    def test_exit_code_nonzero(self):
        result = execute_script(FIXTURES / "mock_fail.py")
        assert result.exit_code == 1

    def test_captures_stderr(self):
        result = execute_script(FIXTURES / "mock_fail.py")
        assert "something went wrong" in result.stderr

    def test_measures_duration(self):
        result = execute_script(FIXTURES / "mock_solver.py")
        assert result.duration_s > 0

    def test_records_timestamp(self):
        from datetime import datetime

        result = execute_script(FIXTURES / "mock_solver.py")
        # Should be valid ISO format
        datetime.fromisoformat(result.timestamp)


class TestRunCLI:
    def test_run_success(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["run", "--solver=pybamm", str(FIXTURES / "mock_solver.py")],
        )
        assert result.exit_code == 0
        assert "3.72" in result.output or "converged" in result.output.lower() or "exit_code" in result.output.lower()

    def test_run_json_output(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--json", "run", "--solver=pybamm", str(FIXTURES / "mock_solver.py")],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "exit_code" in data
        assert "duration_s" in data
