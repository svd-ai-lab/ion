# PyFluent Runtime Driver v1 — Spec

## 1. Background

### v0 — Script Support

PyFluent script support v0 validates the `ion run script.py --solver=pyfluent`
subprocess model.  Each call is a completely independent OS process:

```
ion run watertight.py --solver=pyfluent
  |
  +-- subprocess.run(["python", "watertight.py"])
       |
       +-- script launches Fluent, executes full workflow, exits
       +-- print(json.dumps({...}))  at end of script
  |
  +-- parse_output(stdout) -> dict
  +-- store in .ion/runs/NNN.json
```

v0 demo scripts (`demo_meshing_watertight.py`, `demo_meshing_fault_tolerant.py`,
`demo_solver_exhaust.py`) are **v0 script support demos**.  They verify that
ion can manage execution of standalone pyfluent scripts.  They do NOT verify
persistent session management, step-by-step snippet execution, or runtime
state observation.

### v1 — Runtime Control

v1 introduces an **in-process persistent session**: ion holds a live PyFluent
session object across multiple snippet executions within the same Python
process.  The core claim to verify is:

> ion can hold a session, repeatedly act on it, observe its state, and
> record the history — without restarting Fluent between actions.

v0 and v1 are completely independent.  Neither modifies the other.

---

## 2. Runtime Control Elements

A runtime control layer has exactly five basic elements.  v1 is designed
explicitly around these five.

### 2.1 Session

**What it is**: a persistent, addressable, stateful PyFluent session object.

**v1 implementation**:
- `ActiveSession` dataclass holds: `session_id` (UUID), `mode` ("meshing" |
  "solver"), `ui_mode`, `connected_at` (timestamp), `run_count` (int),
  `session` (live pyfluent object).
- `connect()` launches Fluent and registers the session.
- `disconnect()` calls `session.exit()` and clears internal state.
- At most one session is active at any time (v1 is single-session).

**What is NOT shared**: session-level state (the Fluent process + its mesh /
solver state) IS persistent.  Python variables defined inside a snippet (exec
namespace) are NOT persistent between run() calls (see §2.5 Boundary).

### 2.2 Action

**What it is**: the ability to apply a local operation to the active session.

**v1 implementation**:
- `run(code, label)` executes a Python snippet via `exec()` inside the
  active session's namespace.
- Injected names: `session`, `meshing` (meshing mode), `solver` (solver mode),
  `_result` (assign to return data).
- On failure: exception is caught, `ok=False`, session is kept alive.
- run() is the only action primitive in v1.  Higher-level actions (step,
  apply) are deferred to v2.

### 2.3 Observation

**What it is**: the ability to read current runtime state without modifying it.

**v1 implementation**:
- `query(name)` dispatches to a named read-only handler.
- Four supported queries, all returning plain dicts:

| Query | Returns |
|---|---|
| `session.summary` | session_id, mode, ui_mode, connected_at, run_count, connected |
| `session.mode` | connected, mode |
| `last.result` | last run's run_id, session_id, label, ok, stdout, stderr, error, result, elapsed_s, started_at |
| `workflow.summary` | connected, workflow_available, workflow_attr (if found) |

- All queries are safe to call when disconnected; they return
  `{"connected": False, ...}` rather than raising.
- Queries never call Fluent APIs that modify state.

### 2.4 History

**What it is**: a durable record of every action and its outcome.

**v1 implementation**:
- Every `run()` call writes one JSON file to `.ion/v1_runs/<run_id>.json`.
- Log format contains all fields needed to reconstruct what happened:
  `run_id`, `session_id`, `label`, `code`, `started_at`, `elapsed_s`,
  `ok`, `stdout`, `stderr`, `error`, `result`.
- Logs survive `disconnect()`.  The `.ion/v1_runs/` directory is never
  cleared by v1 code.
- Logs are separate from v0's `.ion/runs/` to avoid any collision.

### 2.5 Boundary

**What it is**: the defined edge cases for session lifecycle and exec isolation.

**v1 boundary rules**:

| Situation | Behaviour |
|---|---|
| `run()` when disconnected | Raises `RuntimeError("No active session.")` |
| `query()` when disconnected | Returns `{"connected": False, ...}` (no raise) |
| `run()` raises exception | `ok=False`, `error` contains traceback, session stays alive |
| `disconnect()` when disconnected | Returns `{"ok": False, "reason": "no active session"}` |
| Variables defined in snippet N | NOT visible in snippet N+1 (fresh exec namespace each call) |
| Session object across snippets | Same live pyfluent object — Fluent state IS shared |
| `_last_result` after `disconnect()` | Cleared to None (in-memory only; on-disk logs retained) |

These rules are tested explicitly in `TestBoundary`.

---

## 3. Minimum Interface

```python
class PyFluentRuntimeV1:

    def connect(
        self,
        mode: str = "meshing",       # "meshing" | "solver"
        ui_mode: str = "no_gui",     # "no_gui"  | "gui"
        precision: str = "double",
        processor_count: int = 1,
    ) -> dict:
        # {"ok": True, "session_id": str, "mode": str, "ui_mode": str, "connected_at": float}

    def run(self, code: str, label: str = "snippet") -> dict:
        # {"run_id": str, "ok": bool, "label": str, "stdout": str, "stderr": str,
        #  "error": str|None, "result": any, "elapsed_s": float}

    def query(self, name: str) -> dict:
        # name in: "session.summary", "session.mode", "last.result", "workflow.summary"

    def disconnect(self) -> dict:
        # {"ok": bool, "session_id": str|None}

    # Internal helper (test injection point):
    def _register_session(self, session: object, mode: str, ui_mode: str) -> dict: ...

    @property
    def connected(self) -> bool: ...   # True iff active session exists
    @property
    def active(self) -> ActiveSession | None: ...
    @property
    def last_result(self) -> SnippetResult | None: ...
```

---

## 4. Internal Module Layout

```
src/ion/drivers/pyfluent/runtime_v1/
    __init__.py       # exports PyFluentRuntimeV1
    session.py        # ActiveSession dataclass
    executor.py       # SnippetExecutor + SnippetResult
    log.py            # RunLog  -> .ion/v1_runs/<run_id>.json
    queries.py        # 4 query handlers
    core.py           # PyFluentRuntimeV1 (assembles the above)
```

No existing file under `src/ion/drivers/pyfluent/` is modified.
Logs go to `.ion/v1_runs/` (separate from v0's `.ion/runs/`).

---

## 5. Testing a Good Runtime

A runtime is "good" when it passes tests across all five elements.
Running a demo script end-to-end is **not** sufficient — that tests the
script, not the runtime.

### Test category map

| Category | Element | Key question |
|---|---|---|
| Session | Session | Was a real session established? |
| Persistence | Session | Is the same session reused? |
| Action | Action | Can code be executed? |
| Observation | Observation | Does query() return accurate state? |
| History | History | Is every run durably logged? |
| Boundary | Boundary | Are edge cases handled correctly? |
| Smoke (integration) | All | Does the full lifecycle work with real Fluent? |

### Category 1 — Session Test

Goal: verify that a session is truly established and queryable.

Required coverage:
- `connect()` / `_register_session()` returns `ok=True` with `session_id`
- `connected` property is `True` after connect
- `mode` is correctly recorded
- `query("session.summary")` returns `connected=True` with all required fields

### Category 2 — Persistence Test

Goal: verify that the runtime truly holds one session across multiple runs,
not re-creating a session on each call.

Required coverage:
- `run_count == 1` after first `run()`
- `run_count == 2` after second `run()`
- `session_id` is identical in both `run()` results (via `query`)
- `query("session.summary")` reflects accumulated state

### Category 3 — Action Test

Goal: verify that `run()` correctly executes snippets.

Required coverage:
- Valid code returns `ok=True`
- stdout is captured
- `_result` assignment is returned
- Bad code (exception) returns `ok=False`, `error` not None
- `meshing` is injected in meshing mode
- `solver` is injected in solver mode

### Category 4 — Observation Test

Goal: verify that `query()` returns semantically correct, field-complete dicts.

Required coverage:
- `session.summary`: has `session_id`, `mode`, `ui_mode`, `connected_at`,
  `run_count`, `connected`
- `session.mode`: has `connected`, `mode`
- `last.result` before run: `has_last_run=False`
- `last.result` after run: has `run_id`, `session_id`, `label`, `ok`,
  `stdout`, `stderr`, `error`, `result`, `elapsed_s`, `started_at`
- `workflow.summary` on a session with a workflow attr: `workflow_available=True`
- `workflow.summary` on a session without a workflow attr: `workflow_available=False`

### Category 5 — History Test

Goal: verify that every run is durably logged with all required fields.

Required coverage:
- Each `run()` writes exactly one JSON file to `.ion/v1_runs/`
- Log file contains: `run_id`, `session_id`, `label`, `code`, `started_at`,
  `elapsed_s`, `ok`, `stdout`, `stderr`, `error`, `result`
- Two `run()` calls write two separate log files
- Log files survive (are not cleared by) `disconnect()`

### Category 6 — Boundary Test

Goal: verify that runtime edge cases behave according to the rules in §2.5.

Required coverage:
- `run()` after `disconnect()` raises `RuntimeError`
- `query()` after `disconnect()` returns `connected=False` (no raise)
- `run()` failure keeps session alive (`connected` still `True`)
- `run()` failure still increments `run_count` (it is an attempt, not a success)
- Python variables set in snippet N are NOT visible in snippet N+1
- Session object identity is the same across all runs
- `disconnect()` without a session returns `ok=False`

### Category 7 — Real Runtime Smoke Test (integration)

File: `tests/integration/test_pyfluent_runtime_v1_smoke.py`
Marker: `@pytest.mark.integration`
Requires: Ansys Fluent 2024 R1, ansys-fluent-core 0.37.2

Minimal case only:
1. `connect(mode="meshing", ui_mode="no_gui")`
2. `run("print('smoke ok')")`
3. `query("session.summary")` — assert `run_count == 1`
4. `disconnect()`

This test verifies the full lifecycle with a real Fluent process.
It does NOT run full watertight / fault-tolerant / solver workflows.
Those belong to v0 script support demos.

---

## 6. Acceptance Criteria

| ID | Element | Criterion |
|---|---|---|
| AC-S1 | Session | `connect()` returns `ok=True` with UUID `session_id` |
| AC-S2 | Session | `connected` property is `True` after connect |
| AC-P1 | Persistence | `run_count == 1` after first run |
| AC-P2 | Persistence | `run_count == 2` after second run |
| AC-P3 | Persistence | `session_id` unchanged across runs |
| AC-A1 | Action | Valid snippet returns `ok=True` |
| AC-A2 | Action | Bad snippet returns `ok=False`, `error` not None |
| AC-A3 | Action | Session stays alive after bad snippet |
| AC-O1 | Observation | `session.summary` has all 6 required fields |
| AC-O2 | Observation | `last.result` has all 10 required fields after a run |
| AC-H1 | History | Every run writes one `.ion/v1_runs/*.json` file |
| AC-H2 | History | Log file contains all 11 required fields |
| AC-B1 | Boundary | `run()` raises after `disconnect()` |
| AC-B2 | Boundary | `query()` returns `connected=False` after `disconnect()` |
| AC-B3 | Boundary | Variables do not leak between snippets |
| AC-B4 | Boundary | Session object identity same across runs |

All unit tests (AC-S1 through AC-B4) must pass without Fluent installed.

---

## 7. v0 vs v1 Summary

| Dimension | v0 (script support) | v1 (runtime driver) |
|---|---|---|
| Execution model | subprocess (one-shot) | in-process (persistent) |
| Session lifetime | per script invocation | connect() → disconnect() |
| Multi-step control | script must do it all | run() called N times |
| State observation | stdout JSON at end | query() at any time |
| History | .ion/runs/NNN.json | .ion/v1_runs/<uuid>.json |
| CLI integration | `ion run script.py` | Python API only (v1) |
| Demo scripts | demo_meshing_*.py, demo_solver_*.py | demo_runtime_v1.py |

---

## 8. Future Evolution to v2

The `run()` / `query()` interface defined in v1 is the stable foundation for v2.

v2 additions (without changing v1's interface):
- `inspect(query_name)` → batch queries, mesh statistics, field data
- `apply(spec: dict)` → translate a declarative spec into `run()` sequences
- `checkpoint()` → save session state (if pyfluent 0.37.2 supports it)
- CLI sub-commands wrapping the v1 Python API
- Multi-session registry
