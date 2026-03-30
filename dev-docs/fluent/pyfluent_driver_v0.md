
# PyFluent Driver v0 Spec

> **定位说明（重要）**
>
> 本 spec 描述的是 PyFluent 在现有 ion 脚本执行架构下的 v0 接入方式，
> **不等同于持久 session runtime 集成**。
>
> 当前已实现的是 **PyFluent script support v0**：
> 用户编写独立 pyfluent 脚本，通过 `ion run script.py --solver=pyfluent` 执行，
> ion 负责 subprocess 管理、日志记录、parse_output 和 query。
>
> 持久 session、snippet runtime、inspect/apply 等能力属于 **PyFluent runtime driver v1**，
> 需另开 spec，本文档不涵盖。

## 1. 背景

本规格用于在 `ion` 项目中实现一个最小可执行的 `PyFluent` driver v0。

本阶段目标不是把PyFluent完整包装成一套庞大的CLI命令，也不是实现完整闭环控制，而是先让 `ion` 能够以最小成本托管PyFluent的：

1. 会话启动/连接
2. 小段原生PyFluent脚本执行
3. 少量结构化查询
4. 自动运行日志记录

本driver后续将作为更强控制原语（如 `inspect` / `apply`）的基础。

---

## 2. 目标

实现一个最小的 `src/ion/drivers/pyfluent/` driver，使以下工作流成立：

1. `connect` 到Fluent meshing或solver session
2. 在当前活动session中执行一小段PyFluent代码
3. 捕获stdout / stderr / traceback / 结构化结果
4. 将run记录保存到 `.ion/runs/`
5. 对当前session执行少量固定query

---

## 3. 非目标

本阶段不做以下事情：

1. 不将PyFluent对象树一一映射成大量CLI子命令
2. 不实现完整的 `inspect` / `apply` / `rollback`
3. 不做复杂的安全沙箱
4. 不保证一次性覆盖所有PyFluent能力
5. 不要求真实完成完整网格或完整求解流程
6. 不要求接入所有未来solver的统一状态模型

---

## 4. 代码位置

所有新增源码放在：

```text
src/ion/drivers/pyfluent/
````

建议包含以下文件：

```text
src/ion/drivers/pyfluent/
  __init__.py
  driver.py
  runtime.py
  queries.py
  schemas.py
  demo.py
```

如项目当前已有driver注册机制，请按现有模式注册该driver。

---

## 5. 设计原则

### 5.1 薄适配层

本driver应尽量薄，不重写PyFluent能力，不镜像PyFluent对象树，仅提供最小托管能力。

### 5.2 原生脚本优先

本阶段主要通过执行小段原生PyFluent脚本来复用官方能力。

### 5.3 持久session

多个 `run` 之间必须共享同一个活动session，不能每次都重启Fluent。

### 5.4 可结构化记录

所有 `run` 必须生成结构化日志，便于后续查询、回放、调试与训练。

### 5.5 可逐步扩展

实现要为后续新增：

* `inspect`
* `apply`
* 更多 `query`
  预留空间，但本轮不实现。

---

## 6. 输入与输出

## 6.1 connect 输入

### Python层接口建议

```python
connect(
    mode: str = "meshing",
    ip: str | None = None,
    port: int | None = None,
    password: str | None = None,
) -> dict
```

### 输入语义

* `mode`

  * `"meshing"`：本地启动meshing session
  * `"solver"`：本地启动solver session
* `ip/port/password`

  * 若提供，则尝试连接已有session
  * v0允许仅先支持已有solver session连接

### connect 输出

返回结构化字典，至少包含：

```json
{
  "ok": true,
  "session_id": "uuid",
  "mode": "meshing",
  "source": "install"
}
```

或

```json
{
  "ok": true,
  "session_id": "uuid",
  "mode": "solver",
  "source": "connection"
}
```

出错时应抛出明确异常，或返回带错误说明的结构化结果，保持与项目现有driver风格一致。

---

## 6.2 run 输入

### Python层接口建议

```python
run(
    code: str,
    label: str = "pyfluent-snippet",
) -> dict
```

### 输入语义

* `code`

  * 一段可执行的PyFluent Python代码
  * 必须在当前活动session上下文中执行
* `label`

  * 给本次run打标签，便于日志检索与调试

### 执行上下文要求

run执行时，至少注入以下变量名：

* `session`
* `solver`
* `meshing`
* `_result`

说明：

* 若当前session是solver，则 `solver=session`，`meshing=None`
* 若当前session是meshing，则 `meshing=session`，`solver=None`
* 用户可以给 `_result` 赋值，用于返回结构化结果

### run 输出

返回结构化字典，至少包含：

```json
{
  "run_id": "uuid",
  "ok": true,
  "label": "create-watertight",
  "stdout": "",
  "stderr": "",
  "error": null,
  "result": {
    "watertight_created": true
  }
}
```

失败时例如：

```json
{
  "run_id": "uuid",
  "ok": false,
  "label": "bad-snippet",
  "stdout": "",
  "stderr": "",
  "error": "Traceback ...",
  "result": null
}
```

---

## 6.3 query 输入

### Python层接口建议

```python
query(name: str) -> dict
```

### v0必须支持的query名字

* `session.summary`
* `workflow.summary`
* `last.result`
* `field.catalog`

### query 输出

必须返回结构化字典，不允许直接返回任意原生对象。

---

## 7. 日志与持久化要求

每次 `run` 后都必须在以下目录生成一条JSON日志：

```text
.ion/runs/
```

日志文件内容至少包含：

```json
{
  "run_id": "uuid",
  "label": "create-watertight",
  "code": "...",
  "started_at": 0.0,
  "ended_at": 0.0,
  "ok": true,
  "stdout": "",
  "stderr": "",
  "error": null,
  "result": {},
  "session_id": "uuid",
  "solver_kind": "meshing"
}
```

要求：

1. JSON必须可读
2. 文件名可用 `run_id.json`
3. 若目录不存在，自动创建
4. 不覆盖其他run记录

---

## 8. 查询语义要求

## 8.1 session.summary

至少返回：

```json
{
  "session_id": "uuid",
  "solver_kind": "meshing",
  "has_last_run": true
}
```

---

## 8.2 workflow.summary

目标不是穷举所有PyFluent workflow内容，而是返回一个兼容性摘要。

建议逻辑：

* 检查session对象上是否有常见workflow相关属性，例如：

  * `workflow`
  * `meshing_workflow`
  * `watertight`
* 若存在，返回：

  * 命中的属性名
  * 其repr摘要
* 若不存在，也返回明确说明

例如：

```json
{
  "session_id": "uuid",
  "solver_kind": "meshing",
  "workflow_attr": "watertight",
  "workflow_repr": "<...>"
}
```

或

```json
{
  "session_id": "uuid",
  "solver_kind": "solver",
  "workflow_available": false,
  "reason": "no meshing workflow attribute detected"
}
```

---

## 8.3 last.result

至少返回最近一次run的结构化摘要：

```json
{
  "has_last_run": true,
  "run_id": "uuid",
  "label": "create-watertight",
  "ok": true,
  "stdout": "",
  "stderr": "",
  "error": null,
  "result": {
    "watertight_created": true
  }
}
```

若还没有run，则返回：

```json
{
  "has_last_run": false
}
```

---

## 8.4 field.catalog

若当前session支持field接口，则返回：

```json
{
  "available": true,
  "scalar_names": ["pressure", "temperature"],
  "vector_names": ["velocity"],
  "surface_names": ["wall", "inlet"]
}
```

若不支持，则返回：

```json
{
  "available": false,
  "reason": "session has no fields interface"
}
```

---

## 9. 与PyFluent cheat sheet的对照要求

本阶段不是一次性把全部清单做成结构化命令，而是确保driver路线将来能够复现这些流程。

也就是说，后续应能通过 `connect + run + query + log` 逐步复现如下能力：

### 9.1 Session与连接

* launch solver session
* launch meshing session
* connect existing solver session

### 9.2 文件与网格

* read case
* read case/data
* write case
* write case/data
* watertight meshing workflow
* switch_to_solver

### 9.3 求解设置

* physics setup
* materials
* models
* solution methods
* report definitions
* initialization
* iterate

### 9.4 数据接口

* field data
* reduction
* solution variables

本轮不要求全部结构化实现，但代码结构必须允许后续逐步补齐。

---

## 10. Demo要求

必须提供一个最小 `demo.py`，演示如下步骤：

1. 创建 `PyFluentDriver`
2. `connect(mode="meshing")`
3. `query("session.summary")`
4. `run()` 一个小snippet
5. `query("last.result")`
6. `query("workflow.summary")`

推荐snippet：

```python
watertight = meshing.watertight()
_result = {"watertight_created": watertight is not None}
```

说明：

* demo目标是证明driver通路打通
* 不要求一定导入真实几何并完成网格生成
* 但必须体现session持久化和query可用

---

## 11. 测试要求

必须新增自动化测试，优先覆盖Python层driver。

建议测试文件：

```text
tests/test_pyfluent_driver_v0.py
```

若项目已有更适合的目录布局，则遵循现有测试风格。

### 11.1 单元测试应覆盖

#### 测试1：runtime/session注册

验证：

* register_session后有active session
* active session可被取回

#### 测试2：run成功路径

使用fake session或mock对象，执行一段简单代码，例如：

```python
print("hello")
_result = {"x": 1}
```

验证：

* `ok == True`
* stdout包含hello
* result为`{"x": 1}`
* `.ion/runs/`下生成日志文件

#### 测试3：run异常路径

执行会抛异常的代码，例如：

```python
raise RuntimeError("boom")
```

验证：

* `ok == False`
* `error`包含traceback
* 日志仍然被写出

#### 测试4：query(session.summary)

验证返回字段完整。

#### 测试5：query(last.result)

验证最近run结果可被读取。

#### 测试6：workflow.summary的兼容性

分别对：

* 无workflow属性的fake session
* 有`watertight`或`workflow`属性的fake session

验证不会崩溃，并能返回合理摘要。

### 11.2 可选集成测试

如果本地安装了PyFluent/Fluent环境，则可增加集成测试，但必须满足：

* 没有安装时自动skip
* 不影响默认CI通过

---

### 11.3 真实 PyFluent 集成测试算例

本节定义4个基于真实 Fluent 2024 R1 的端到端集成测试，覆盖 meshing 和 solver 两条路径。

测试文件布局：

```text
tests/integration/
    test_pyfluent_meshing.py    # Meshing Case 1 + Case 2
    test_pyfluent_solver.py     # Solver Case 1 + Case 2
```

所有测试满足：

* 标记为 `@pytest.mark.integration`，需 `-m integration` 手动触发
* 无 Fluent / ansys-fluent-core 时自动 `pytest.skip`
* 使用 `scope="module"` 的 session fixture，每个测试文件只启动一次 Fluent 进程
* 算例文件通过 `pyfluent.examples.download_file()` 下载，下载失败则 skip

---

#### Meshing Case 1 — Watertight Geometry 完整流程

**算例文件：** `mixing_elbow.pmdb`（`pyfluent/mixing_elbow`）

**测试步骤：**

1. `driver.launch(mode="meshing")` 启动 meshing session
2. `driver.run()` 执行完整 watertight 工作流：
   - `watertight = meshing.watertight()`
   - `import_geometry`（文件名、单位 `"in"`）→ 执行
   - `add_local_sizing_wtm.add_child_to_task()` → 执行
   - `create_surface_mesh`（`max_size=0.3`）→ 执行
   - `describe_geometry`（`setup_type="fluid"`）→ 执行
   - `create_volume_mesh_wtm`（`volume_fill="poly-hexcore"`）→ 执行
   - `_result = {"surface_done": True, "volume_done": True}`
3. `driver.query("workflow.summary")`

**验证点：**

* `run_result["ok"] is True`
* `run_result["result"]["volume_done"] is True`
* `run_result["stdout"]` 无 traceback
* `query("workflow.summary")["workflow_attr"] == "watertight"`
* `.ion/runs/*.json` 日志字段完整（`solver_kind=="meshing"`）

---

#### Meshing Case 2 — Fault-Tolerant Meshing 完整流程

**算例文件：** `exhaust_system.fmd`（`pyfluent/exhaust_system`）

**测试步骤：**

1. `driver.launch(mode="meshing")` 启动新 meshing session
2. `driver.run()` 执行完整 fault-tolerant 工作流：
   - `ft = meshing.fault_tolerant()`
   - `ft.import_cad_and_part_management.context.set_state(0)` → 执行
   - `ft.describe_geometry_and_flow.add_enclosure.set_state("No")`
   - `ft.describe_geometry_and_flow.flow_type.set_state("Internal flow through the object")` → 执行
   - 依次执行 capping、extract edge features、identify regions、generate surface mesh、generate volume mesh
   - `_result = {"ft_mesh_done": True}`

**验证点：**

* `run_result["ok"] is True`
* `run_result["result"]["ft_mesh_done"] is True`
* `.ion/runs/*.json` 日志已写出
* 无未捕获异常

---

#### Solver Case 1 — mixing_elbow 场量查询与 Reduction

**算例文件：** `mixing_elbow.cas.h5` + `mixing_elbow.dat.h5`（`pyfluent/mixing_elbow`）

**测试步骤：**

1. `driver.launch(mode="solver")` 启动 solver session
2. `driver.run()` 执行：

```python
solver.settings.file.read_case_data(file_name=case_file)
from ansys.fluent.core.solver.function import reduction
from ansys.units import VariableCatalog
field_data = solver.fields.field_data
scalar_names = field_data.scalar_fields.allowed_values()
avg_p = reduction.area_average(
    VariableCatalog.ABSOLUTE_PRESSURE,
    locations=["cold-inlet"],
    ctxt=solver,
)
_result = {
    "scalar_count": len(scalar_names),
    "avg_pressure": float(avg_p),
    "has_pressure_field": "pressure" in scalar_names,
}
```

3. `driver.query("field.catalog")`
4. `driver.query("last.result")`

**验证点：**

* `run_result["ok"] is True`
* `result["scalar_count"] > 0`
* `result["avg_pressure"] > 0`
* `result["has_pressure_field"] is True`
* `query("field.catalog")["available"] is True`
* `query("field.catalog")["scalar_names"]` 非空

---

#### Solver Case 2 — exhaust_system 初始化与迭代求解

**算例文件：** `exhaust_system.cas.h5` + `exhaust_system.dat.h5`（`pyfluent/exhaust_system`）

**测试步骤：**

1. `driver.launch(mode="solver")` 启动 solver session
2. `driver.run()` 执行：

```python
solver.settings.file.read_case_data(file_name=case_file)
solver.solution.initialization.hybrid_initialize()
solver.solution.run_calculation.iterate(iter_count=5)
_result = {"converged": True, "iters_requested": 5}
```

3. `driver.query("last.result")`
4. `driver.query("session.summary")`

**验证点：**

* `run_result["ok"] is True`
* `run_result["error"] is None`
* `result["iters_requested"] == 5`
* `query("session.summary")["solver_kind"] == "solver"`
* `.ion/runs/*.json` `started_at < ended_at`（实际耗时被记录）

---

## 12. 验证方法

完成实现后，应按以下顺序验证：

### 12.1 静态检查

运行项目现有lint工具，例如：

```bash
ruff check src/ion tests
```

### 12.2 单元测试

运行新增测试，例如：

```bash
pytest -q tests/test_pyfluent_driver_v0.py
```

### 12.3 Demo手动验证

运行demo，验证：

1. 能成功connect
2. 能执行一个snippet
3. 能返回last.result
4. 能产生日志JSON

### 12.4 日志验证

检查 `.ion/runs/` 下是否生成JSON文件，并确认字段完整。

---

## 13. 验收标准

本轮验收通过的最低标准：

1. 能创建 `PyFluentDriver`
2. 能成功 `connect(mode="meshing")` 或 `connect(mode="solver")`
3. 能在活动session中 `run` 一段小代码
4. `run` 的 stdout / stderr / traceback / result 能结构化返回
5. 每次 `run` 都会写 `.ion/runs/*.json`
6. `query("session.summary")` 可工作
7. `query("last.result")` 可工作
8. `query("workflow.summary")` 在无workflow属性时也不会崩溃
9. 有至少一份自动化测试文件覆盖成功与失败路径
10. 提供可运行的 `demo.py`

---

## 14. 推荐实现顺序

请严格按以下顺序实现：

### 第一步

实现 `runtime.py`

* session注册
* active session
* run record
* JSON日志

### 第二步

实现 `driver.py`

* connect
* run
* query调度

### 第三步

实现 `queries.py`

* 4个固定query

### 第四步

实现 `demo.py`

### 第五步

补测试

### 第六步

补最小文档注释

---

## 15. 下一轮扩展方向（本轮不实现）

下一轮优先级建议：

1. 新增 `inspect`
2. 新增 `apply`
3. query扩展到：

   * `mesh.quality`
   * `solver.residuals`
   * `reduction.summary`
4. 增加弱lint
5. 增加按label或run_id检索历史
6. 增加更安全的snippet执行边界

---

## 16. 最终约束

本轮实现必须始终遵守以下约束：

1. 优先最小可执行，不要过度设计
2. 不要镜像PyFluent对象树
3. 不要提前做大而全CLI
4. 不要破坏现有ion架构
5. 不要引入必须依赖真实Fluent环境才能通过的默认测试


