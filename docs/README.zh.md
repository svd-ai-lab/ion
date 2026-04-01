# ion

> AI Agent 的仿真运行时。

一套用于启动、控制和观测工程仿真的 harness —— 支持 Fluent、COMSOL、MATLAB 和 PyBaMM，适配任何 LLM Agent 或命令行。

[English](../README.md) | [Deutsch](README.de.md) | [日本語](README.ja.md) | **[中文](#ion)**

## 为什么需要 ion

LLM Agent 已经能从训练数据中写出仿真脚本。但工程仿真是**有状态的、耗时的、昂贵的** —— 一次 Fluent 计算要跑几个小时，一个 COMSOL 模型占用几个 GB 的内存，一个错误参数就意味着完全重来。

目前没有标准方式让 Agent 启动求解器、执行一步、观察结果、再决定下一步。ion 填补了这个空白：一套统一的 CLI 和 HTTP 接口，把任何支持的求解器变成可控的、可观测的运行时。

## Agent 控制循环

这是核心理念。不再"写完脚本就跑"，ion 实现了**逐步控制循环**：

```
    ┌─────────────────────────────────────────┐
    │              Agent (LLM)                 │
    │  "网格太粗了 → 细化后重新计算"            │
    └─────────┬───────────────────▲────────────┘
              │ ion exec          │ ion inspect
              │ ion connect       │ ion screenshot
              │ ion lint          │ ion logs
    ┌─────────▼───────────────────┴────────────┐
    │              ion server                   │
    │           (持久化会话)                     │
    │  ┌───────────┐  ┌──────────┐  ┌────────┐ │
    │  │  Fluent   │  │  COMSOL  │  │ MATLAB │ │
    │  │  (GUI)    │  │  (GUI)   │  │        │ │
    │  └───────────┘  └──────────┘  └────────┘ │
    └──────────────────────────────────────────┘
```

Agent 编写代码片段，ion 在活跃会话中执行，Agent 检查结果，决定下一步 —— 全程无需重启求解器。

## 快速开始

```bash
# 在安装了求解器的机器上：
pip install ion-cli
ion serve --host 0.0.0.0

# 从任意位置（Agent 或工程师）：
ion --host 192.168.1.10 connect --solver fluent --mode solver --ui-mode gui
ion --host 192.168.1.10 exec "solver.settings.mesh.check()"
ion --host 192.168.1.10 inspect session.summary
ion --host 192.168.1.10 exec "solver.solution.run_calculation.iterate(iter_count=100)"
ion --host 192.168.1.10 screenshot                          # 查看 GUI 状态
ion --host 192.168.1.10 inspect session.summary              # 检查收敛性
ion --host 192.168.1.10 disconnect
```

## 命令

| 命令 | 功能 | 类比 |
|---|---|---|
| `ion serve` | 启动 HTTP 服务器，持有求解器会话 | `ollama serve` |
| `ion connect` | 启动求解器，建立会话 | `docker start` |
| `ion exec` | 在活跃会话中执行代码片段 | `docker exec` |
| `ion inspect` | 查询实时会话状态 | `docker inspect` |
| `ion screenshot` | 捕获服务器桌面截图 | 屏幕共享 |
| `ion ps` | 列出活跃会话 | `docker ps` |
| `ion disconnect` | 关闭会话 | `docker stop` |
| `ion run` | 一次性脚本执行 | `docker run` |
| `ion check` | 检查求解器可用性 | `docker info` |
| `ion lint` | 执行前验证脚本 | `ruff check` |
| `ion logs` | 浏览运行历史 | `docker logs` |

## 为什么不直接跑脚本？

脚本是特定求解器的自动化。ion 是 Agent 仿真工作流的**控制平面**。

| 维度 | 原始脚本 | ion |
|---|---|---|
| **会话模型** | 一次性进程，每次运行都重启 | 跨代码片段的持久会话 |
| **接口** | 求解器专用 API（PyFluent、MPh、matlab.engine） | 标准 CLI 和 HTTP 生命周期 |
| **可观测性** | stdout / 日志文件 | `inspect`、`screenshot`、`logs`、实时 GUI |
| **故障恢复** | 从头重跑 | 从当前状态继续 |
| **人工监督** | 事后检查输出文件 | Agent 操作时工程师实时观察 GUI |
| **多求解器** | 每个求解器写一套封装 | 统一的驱动协议 |
| **远程执行** | 临时拼凑 SSH/RDP | 明确的客户端-服务器边界 |

> 如果你只需要对单个求解器运行一个可靠的批处理脚本，ion 是不必要的开销。ion 的优势在于 Agent（或工程师）需要**探索、迭代、对仿真状态做出响应**的场景。

## 支持的求解器

| 求解器 | 状态 | 后端 | 会话模式 |
|---|---|---|---|
| Ansys Fluent | 可用 | PyFluent (ansys-fluent-core) | 一次性、持久（网格/求解器）、GUI |
| COMSOL | 可用 | JPype (Java API) | 一次性、持久、GUI |
| MATLAB | 可用 | matlab.engine | 一次性、持久 |
| PyBaMM | 基础支持 | Python 直接调用 | 一次性 |
| OpenFOAM | 计划中 | — | — |

## 面向 Agent 开发者

ion 为你的 Agent 提供工程仿真的**标准接口** —— 同一套命令适用于 Fluent、COMSOL 和 MATLAB：

- **`connect` / `disconnect`** —— 管理求解器生命周期，无需手动管理子进程
- **`exec`** —— 向活跃会话发送代码片段，无需生成完整脚本
- **`inspect`** —— 结构化状态查询（收敛性、网格统计、变量值），Agent 可直接解析
- **`screenshot`** —— 从求解器 GUI 获取视觉反馈，支持多模态 Agent
- **`lint`** —— 在执行前捕获语法错误，避免浪费求解器运行时间
- **远程优先** —— 在 GPU/HPC 机器上运行 `ion serve`，Agent 通过 HTTP 从任意位置连接

支持 Claude Code、Cursor、自定义 Agent 框架，或直接使用 `httpx` 调用。

## 面向仿真工程师

ion 不替代你的求解器 —— 它在外层包裹了一个控制层：

- **保留 GUI** —— Fluent 和 COMSOL 以完整 GUI 运行，你在旁观察，Agent 在驱动
- **持久会话** —— 不再每次修改都重启 Fluent
- **逐步执行** —— Agent 每次只执行一个代码片段，你可以在步骤之间介入
- **运行历史** —— `ion logs` 存储每次执行的输入和输出
- **远程访问** —— 在工作站运行 `ion serve`，从笔记本控制或让 Agent 连接

## 这就是 Harness Engineering

[Harness Engineering](https://openai.com/index/building-with-codex/) 的核心是构建让 AI Agent 稳定工作的系统 —— 规则、工具、验证、反馈循环。ion 为仿真工作流提供了早期 harness 原语：

| Harness 概念 | ion 实现 |
|---|---|
| **规则与接口** | DriverProtocol：每个求解器实现 `connect`、`exec`、`inspect`、`disconnect` |
| **验证** | `ion check`（求解器可用？）、`ion lint`（脚本合法？）、结构化 `inspect` |
| **反馈循环** | `exec` → `inspect` → 决策 → 再次 `exec`，全在一个会话内 |
| **可观测性** | `ion logs`、`ion screenshot`、`ion inspect`、实时 GUI |
| **人机协同** | 持久会话 + GUI + 逐步执行 = 工程师可以监督或随时接管 |

## 架构

```
任意机器                                  安装了求解器的机器
┌──────────────┐    HTTP/Tailscale   ┌──────────────────┐
│  ion CLI     │ ─────────────────>  │  ion serve       │
│  (客户端)     │ <─────────────────  │  (FastAPI)       │
└──────────────┘       JSON          │       │          │
                                     │  ┌────▼────────┐ │
                                     │  │ 求解器 GUI   │ │
                                     │  │ (可选)       │ │
                                     │  └─────────────┘ │
                                     └──────────────────┘
```

## 开发

```bash
# 安装（含所有求解器后端）
uv pip install -e ".[dev,pyfluent]"

# 运行测试
pytest tests/                    # 单元测试（无需求解器）
pytest --ion-host=<IP>           # 集成测试（需要 ion serve + 求解器）

# 代码检查
ruff check src/ion tests
```

## 项目结构

```
src/ion/
    cli.py              # 统一 CLI 入口
    server.py           # HTTP 服务器 (ion serve)
    session.py          # HTTP 客户端（本地或远程）
    driver.py           # DriverProtocol 接口
    runner.py           # 子进程执行
    store.py            # 运行历史 (.ion/runs/)
    drivers/
        fluent/         # Ansys Fluent 驱动
        comsol/         # COMSOL Multiphysics 驱动
        matlab/         # MATLAB 驱动
        pybamm/         # PyBaMM 驱动
```

## 许可证

Apache-2.0
