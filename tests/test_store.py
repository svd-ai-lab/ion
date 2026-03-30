"""Tests for ion run storage — Phase 3."""
import json

from ion.driver import RunResult
from ion.store import RunStore


def _make_run(script="test.py", exit_code=0) -> RunResult:
    return RunResult(
        exit_code=exit_code,
        stdout='{"voltage_V": 3.72}',
        stderr="",
        duration_s=1.5,
        script=script,
        solver="pybamm",
        timestamp="2026-03-23T10:00:00",
    )


class TestRunStore:
    def test_save_creates_json(self, tmp_path):
        store = RunStore(tmp_path / ".ion")
        run_id = store.save(_make_run())
        assert (tmp_path / ".ion" / "runs" / f"{run_id}.json").exists()

    def test_save_content(self, tmp_path):
        store = RunStore(tmp_path / ".ion")
        run_id = store.save(_make_run())
        data = json.loads(
            (tmp_path / ".ion" / "runs" / f"{run_id}.json").read_text()
        )
        assert data["solver"] == "pybamm"
        assert data["exit_code"] == 0
        assert data["script"] == "test.py"

    def test_list_returns_runs(self, tmp_path):
        store = RunStore(tmp_path / ".ion")
        store.save(_make_run(script="a.py"))
        store.save(_make_run(script="b.py"))
        store.save(_make_run(script="c.py"))
        runs = store.list()
        assert len(runs) == 3

    def test_get_by_id(self, tmp_path):
        store = RunStore(tmp_path / ".ion")
        run_id = store.save(_make_run())
        record = store.get(run_id)
        assert record["solver"] == "pybamm"

    def test_get_last(self, tmp_path):
        store = RunStore(tmp_path / ".ion")
        store.save(_make_run(script="first.py"))
        store.save(_make_run(script="second.py"))
        record = store.get("last")
        assert record["script"] == "second.py"

    def test_increments_id(self, tmp_path):
        store = RunStore(tmp_path / ".ion")
        id1 = store.save(_make_run())
        id2 = store.save(_make_run())
        id3 = store.save(_make_run())
        assert id1 == "001"
        assert id2 == "002"
        assert id3 == "003"
