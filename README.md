# ion

> The simulation runtime for AI agents.

A harness for launching, controlling, and observing engineering simulations — across Fluent, COMSOL, MATLAB, and PyBaMM — from any LLM agent or CLI.

**[English](#ion)** | [Deutsch](docs/README.de.md) | [日本語](docs/README.ja.md) | [中文](docs/README.zh.md)

## Why ion exists

LLM agents can already write simulation scripts from training data. But engineering simulations are **stateful, slow, and expensive** — a Fluent run takes hours, a COMSOL model holds gigabytes of state, and a wrong parameter wastes a full restart.

There is no standard way for an agent to launch a solver, execute one step, observe what happened, and decide what to do next. ion fills that gap: a uniform CLI and HTTP interface that turns any supported solver into a controllable, observable runtime.

## The agent loop

This is the core idea. Instead of fire-and-forget scripts, ion enables a **step-by-step control loop**:

```
    ┌─────────────────────────────────────────┐
    │              Agent (LLM)                 │
    │  "mesh looks coarse → refine and rerun" │
    └─────────┬───────────────────▲────────────┘
              │ ion exec          │ ion inspect
              │ ion connect       │ ion screenshot
              │ ion lint          │ ion logs
    ┌─────────▼───────────────────┴────────────┐
    │              ion server                   │
    │         (persistent session)              │
    │  ┌───────────┐  ┌──────────┐  ┌────────┐ │
    │  │  Fluent   │  │  COMSOL  │  │ MATLAB │ │
    │  │  (GUI)    │  │  (GUI)   │  │        │ │
    │  └───────────┘  └──────────┘  └────────┘ │
    └──────────────────────────────────────────┘
```

The agent writes a snippet, ion executes it in a live session, the agent inspects the result, and decides the next step — all without restarting the solver.

## Quick Start

```bash
# On the machine with the solver:
pip install ion-cli
ion serve --host 0.0.0.0

# From anywhere (agent or engineer):
ion --host 192.168.1.10 connect --solver fluent --mode solver --ui-mode gui
ion --host 192.168.1.10 exec "solver.settings.mesh.check()"
ion --host 192.168.1.10 inspect session.summary
ion --host 192.168.1.10 exec "solver.solution.run_calculation.iterate(iter_count=100)"
ion --host 192.168.1.10 screenshot                          # see the GUI state
ion --host 192.168.1.10 inspect session.summary              # check convergence
ion --host 192.168.1.10 disconnect
```

## Commands

| Command | What it does | Analogy |
|---|---|---|
| `ion serve` | Start HTTP server, hold solver sessions | `ollama serve` |
| `ion connect` | Launch solver, open session | `docker start` |
| `ion exec` | Run code snippet in live session | `docker exec` |
| `ion inspect` | Query live session state | `docker inspect` |
| `ion screenshot` | Capture server desktop | screen share |
| `ion ps` | List active sessions | `docker ps` |
| `ion disconnect` | Tear down session | `docker stop` |
| `ion run` | One-shot script execution | `docker run` |
| `ion check` | Verify solver availability | `docker info` |
| `ion lint` | Validate script before running | `ruff check` |
| `ion logs` | Browse run history | `docker logs` |

## Why not just run scripts?

Scripts are solver-specific automation. ion is the **control plane** for agentic simulation workflows.

| Axis | Raw scripts | ion |
|---|---|---|
| **Session model** | One-shot process, restart on every run | Persistent session across snippets |
| **Interface** | Solver-specific APIs (PyFluent, MPh, matlab.engine) | Standard CLI and HTTP lifecycle |
| **Observability** | stdout / log files | `inspect`, `screenshot`, `logs`, live GUI |
| **Recovery** | Rerun from scratch | Continue from current state |
| **Human oversight** | Check output files after the fact | Watch the GUI while the agent operates |
| **Multi-solver** | Custom wrapper per solver | Common driver protocol |
| **Remote execution** | Ad hoc SSH/RDP glue | Explicit client-server boundary |

> If you only need a single trusted batch script for one solver, ion is unnecessary overhead. ion shines when an agent (or engineer) needs to **explore, iterate, and react** to simulation state.

## Supported Solvers

| Solver | Status | Backend | Session modes |
|---|---|---|---|
| Ansys Fluent | Working | PyFluent (ansys-fluent-core) | One-shot, persistent (meshing/solver), GUI |
| COMSOL | Working | JPype (Java API) | One-shot, persistent, GUI |
| MATLAB | Working | matlab.engine | One-shot, persistent |
| PyBaMM | Basic | Direct Python | One-shot |
| OpenFOAM | Planned | — | — |
| [FloTHERM](https://www.siemens.com/en-us/products/simcenter/fluids-thermal-simulation/flotherm/) | Planned | — | — |

## For agent builders

ion gives your agent a **standard interface** to engineering simulations — the same commands work across Fluent, COMSOL, and MATLAB:

- **`connect` / `disconnect`** — manage solver lifecycle without subprocess juggling
- **`exec`** — send code snippets to a live session; no need to generate a full script
- **`inspect`** — structured state queries (convergence, mesh stats, variable values) the agent can parse
- **`screenshot`** — visual feedback from the solver GUI for multimodal agents
- **`lint`** — catch syntax errors before wasting a solver run
- **Remote-first** — `ion serve` on a GPU/HPC machine, agent connects over HTTP from anywhere

Works with Claude Code, Cursor, custom agent frameworks, or plain `httpx` calls.

## For simulation engineers

ion does not replace your solver — it wraps it with a control layer:

- **Keep the GUI** — Fluent and COMSOL run with full GUI; you watch while the agent drives
- **Persistent sessions** — no more restarting Fluent after every change
- **Step-by-step** — the agent executes one snippet at a time; you can intervene between steps
- **Run history** — `ion logs` stores every execution with inputs and outputs
- **Remote access** — run `ion serve` on your workstation, control from your laptop or let an agent connect

## Why this is harness engineering

[Harness engineering](https://openai.com/index/building-with-codex/) is about building the system — rules, tools, verification, feedback loops — that keeps AI agents working reliably. ion provides early harness primitives for simulation workflows:

| Harness concept | ion implementation |
|---|---|
| **Rules & interface** | DriverProtocol: every solver implements `connect`, `exec`, `inspect`, `disconnect` |
| **Verification** | `ion check` (solver available?), `ion lint` (script valid?), structured `inspect` |
| **Feedback loops** | `exec` → `inspect` → decide → `exec` again, all in one session |
| **Observability** | `ion logs`, `ion screenshot`, `ion inspect`, live GUI |
| **Human-in-the-loop** | Persistent sessions + GUI + stepwise execution = engineer can supervise or take over |

## Architecture

```
Any machine                              Any machine (with solver)
┌──────────────┐    HTTP/Tailscale   ┌──────────────────┐
│  ion CLI     │ ─────────────────>  │  ion serve       │
│  (client)    │ <─────────────────  │  (FastAPI)       │
└──────────────┘       JSON          │       │          │
                                     │  ┌────▼────────┐ │
                                     │  │ Solver GUI   │ │
                                     │  │ (optional)   │ │
                                     │  └─────────────┘ │
                                     └──────────────────┘
```

## Development

```bash
# Install with all solver backends
uv pip install -e ".[dev,pyfluent]"

# Run tests
pytest tests/                    # unit tests (no solver needed)
pytest --ion-host=<IP>           # integration tests (needs ion serve + solver)

# Lint
ruff check src/ion tests
```

## Project Structure

```
src/ion/
    cli.py              # unified CLI entry point
    server.py           # HTTP server (ion serve)
    session.py          # HTTP client (local or remote)
    driver.py           # DriverProtocol interface
    runner.py           # subprocess execution
    store.py            # run history (.ion/runs/)
    drivers/
        fluent/         # Ansys Fluent driver
        comsol/         # COMSOL Multiphysics driver
        matlab/         # MATLAB driver
        pybamm/         # PyBaMM driver
```

## License

Apache-2.0
