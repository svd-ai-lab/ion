# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ion** is a unified CLI for LLM agents to control CAD/CAE simulation software. It wraps tools like PyBaMM and (planned) PyFluent, providing a consistent interface for validating, executing, and querying simulation scripts. Agents write native solver scripts; ion wraps execution with logging and result parsing.

## Commands

```bash
# Install (development mode)
pip install -e ".[dev]"          # core + pytest + ruff
pip install -e ".[pybamm]"       # add optional PyBaMM driver

# Run tests
pytest -q                        # all unit tests
pytest -q -m integration         # integration tests (requires pybamm installed)
pytest tests/test_lint.py        # single test file

# Lint
ruff check src/ion tests         # check style
ruff check --fix src/ion tests   # auto-fix

# CLI usage
ion lint my_script.py
ion run my_script.py --solver=pybamm --json
ion query last --field=voltage_V
ion log
```

## Architecture

### Core abstractions (`src/ion/driver.py`)

`DriverProtocol` defines the interface every solver driver must implement:
- `detect(script)` — regex/AST check to identify which solver a script targets
- `lint(script)` — validate before execution; returns `LintResult` with `Diagnostic` list
- `connect()` — check solver availability and version; returns `ConnectionInfo`
- `parse_output(stdout)` — extract structured results from stdout (convention: last JSON object)

### Driver registry (`src/ion/drivers/__init__.py`)

`DRIVERS` is a list of instantiated driver objects. CLI commands iterate this list calling `detect()` to auto-select or use `--solver` to pick explicitly.

### Execution pipeline

1. `ion run` calls `runner.py` → subprocess execution, captures stdout/stderr, measures duration
2. Result stored in `.ion/runs/NNN.json` via `store.py`
3. `ion query` reads stored runs by numeric ID or `"last"`

### Adding a new driver

Create `src/ion/drivers/<name>.py` implementing `DriverProtocol`, then register it in `src/ion/drivers/__init__.py`. See `pybamm.py` for the reference implementation (106 lines).

### PyFluent

PyFluent driver 实现在 `src/ion/drivers/pyfluent/`。

**当前阶段定位：PyFluent script support v0**

当前实现是 PyFluent 在现有 ion 脚本执行架构下的 v0 接入，本质是让 ion 能够管理、执行和记录独立 pyfluent 脚本的运行结果，**不等同于持久 session + snippet runtime 的 runtime driver**。

在当前 ion 核心架构下，PyFluent 的用户侧推荐用法是通过 `ion run script.py --solver=pyfluent` 执行独立脚本：

```bash
ion lint  my_script.py                    # 检测 pyfluent import + 语法检查
ion run   my_script.py --solver=pyfluent  # subprocess 执行，stdout/stderr 存 .ion/runs/
ion query last                            # 读取最近一次运行的结构化输出
ion log                                   # 浏览运行历史
```

**pyfluent 脚本约定**（作为 `ion run` 的目标脚本）：
```python
import ansys.fluent.core as pyfluent

session = pyfluent.launch_fluent(mode="meshing", ui_mode="gui")
# ... 执行 workflow ...

# 末尾向 stdout 输出一个 JSON 对象，ion 用 parse_output() 提取供 ion query 使用
import json
print(json.dumps({"status": "ok", "cell_count": 12345}))
```

**`connect()` 语义说明**：在当前 `DriverProtocol` 下，`ion connect pyfluent` 执行的是包可用性检查（能否 import ansys-fluent-core），不建立持久 Fluent session。对于支持持久 session runtime 的 solver，后续需要单独扩展协议（见 runtime driver v1 规划）。

**`PyFluentDriver` 定位**：当前主要作为 ion 内部 driver 适配层（DriverProtocol 实现），不作为终端用户首选接口；用户验证与演示优先通过 `ion run` 完成。

`src/ion/drivers/pyfluent/reference/` 包含 pyfluent 用户手册 Markdown 文件，供编写脚本时参考。

## Task Specs

Feature-specific implementation requirements live under `specs/`.
When implementing a new driver or major feature, always follow the corresponding spec file in addition to this CLAUDE.md.

## Test Layout

```
tests/
  fixtures/           # mock solver scripts (good, bad imports, no-solve, etc.)
  integration/        # end-to-end tests marked @pytest.mark.integration
  test_cli.py         # smoke tests
  test_connect.py     # solver availability checks
  test_lint.py        # linting logic
  test_log.py         # run history browsing
  test_query.py       # result extraction
  test_run.py         # subprocess execution
  test_store.py       # persistence layer
```

Integration tests skip gracefully if optional solver packages are not installed (guarded by `HAS_PYBAMM` flag).

## Notes

- Run storage lives in `.ion/runs/` (local, git-ignored)
- `ion watch` (streaming progress) is not yet implemented
- Project uses `uv` for dependency locking (`uv.lock`)

## Development Constraints

- **Do not modify ion core source files** (`src/ion/cli.py`, `src/ion/driver.py`, `src/ion/runner.py`, `src/ion/store.py`, `src/ion/drivers/__init__.py`, `src/ion/drivers/pybamm.py`). These are stable and shared across all drivers.
- All new PyFluent-related code must go under `src/ion/drivers/pyfluent/` only.
- If a change appears to require touching core files, reconsider the approach — find a way to implement it within the driver layer instead.
- **PyFluent 用户侧验证与演示脚本**优先通过 `ion run script.py --solver=pyfluent` 运行。`PyFluentDriver` 当前定位为 ion 内部 driver 适配层，不作为终端用户首选接口。
