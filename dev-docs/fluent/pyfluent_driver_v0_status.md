# PyFluent Script Support v0 — 阶段性状态说明

> 对应规格：`specs/pyfluent_driver_v0.md`
> 最后更新：2026-03-25

---

## 本阶段正式定位

**PyFluent script support v0**：让 ion 能够管理、执行和记录独立 pyfluent 脚本的运行结果。

- 用户编写独立 pyfluent 脚本（自行调用 `pyfluent.launch_fluent()`）
- 通过 `ion run script.py --solver=pyfluent` 执行
- ion 负责：subprocess、计时、stdout/stderr 捕获、parse_output、日志存 `.ion/runs/`
- `ion query` / `ion log` 查阅结果

**本阶段不是**：持久 session + snippet runtime 的 runtime driver。
`PyFluentDriver.launch() / run() / query()` 等内部 API 存在于代码库中，但不作为当前用户主路径。

---

## ✅ 已完成（script support v0）

| 能力 | 文件 | 说明 |
|------|------|------|
| `detect()` — 识别 pyfluent 脚本 | `driver.py` | 正则匹配 `import ansys.fluent` |
| `lint()` — 语法检查 | `driver.py` | AST parse，返回 `LintResult` |
| `connect()` — 包可用性检查 | `driver.py` | 检查 ansys-fluent-core 是否可 import，不启动 Fluent session |
| `parse_output(stdout)` — 提取 JSON | `driver.py` | 提取 stdout 最后一个 JSON 对象，供 `ion query` 使用 |
| `PyFluentDriver` 注册在 `DRIVERS` 列表 | `src/ion/drivers/__init__.py` | `ion run --solver=pyfluent` / `ion lint` 可用 |
| 单元测试 7 个，覆盖 DriverProtocol 各方法 | `tests/test_pyfluent_driver_v0.py` | 无需 Fluent，CI 可直接运行 |

---

## ⚠️ 存在但定位待收口（内部 API，非当前用户主路径）

以下代码存在于仓库，但属于原始 spec 中 runtime driver 方向的早期实现，
当前阶段不作为用户主路径，后续可在 runtime driver v1 中正式启用。

| 文件 | 内容 | 说明 |
|------|------|------|
| `runtime.py` | session 注册、exec_snippet、JSON 日志 | runtime driver 内部逻辑 |
| `queries.py` | 4 个 named query handler | runtime driver 内部逻辑 |
| `schemas.py` | `SessionInfo` / `RunRecord` dataclass | runtime driver 内部数据结构 |
| `driver.py` 中 `launch() / run() / query()` | 扩展 API | 非 DriverProtocol，供内部使用 |
| `examples/demo_watertight_via_driver.py` | 直接调用 Driver API | 非用户主路径；待改写为独立脚本 |
| `demo.py` | 直接调用 Driver API | 非用户主路径 |
| `tests/integration/` | 使用 Driver API 的集成测试框架 | 非当前主路径，可作为 v1 基础保留 |

---

## ❌ 未完成（属于 runtime driver v1，本轮不实现）

| 能力 | 说明 |
|------|------|
| 持久 session 管理 | launch/connect/disconnect 生命周期 |
| snippet runtime（`driver.run(code)`） | 在持久 session 中执行代码片段 |
| `inspect` / `apply` | 结构化状态读写 |
| 扩展 query（mesh.quality、solver.residuals 等） | 需要持久 session |
| 弱 lint（语义检查） | 超出 v0 scope |

---

## 验证方法（当前阶段）

### 无需 Fluent（CI 默认）
```bash
cd ion-main
pytest -q tests/test_pyfluent_driver_v0.py   # 7 passed
ruff check src/ion tests                      # no errors
ion connect pyfluent --json                   # {"status": "ok", "version": "0.37.2", ...}
```

### 需要真实 Fluent 2024 R1（通过 ion CLI）
```bash
# 脚本检测 + 语法检查（无需启动 Fluent）
ion lint  examples/my_pyfluent_script.py

# subprocess 执行（脚本内自行启动 Fluent GUI，末尾 print JSON）
ion run   examples/my_pyfluent_script.py --solver=pyfluent --json

# 查看结构化结果
ion query last --json
ion log
```

---

## 下一步

- **当前**：将 `examples/` 下演示脚本改写为 `ion run` 兼容的独立 pyfluent 脚本，跑通 watertight meshing 流程
- **后续 v1**：另开 `specs/pyfluent_runtime_driver_v1.md`，在此基础上实现持久 session + snippet runtime
