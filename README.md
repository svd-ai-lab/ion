# ion

> The simulation runtime for AI agents.

**[English](#ion)** | [Deutsch](docs/README.de.md) | [日本語](docs/README.ja.md) | [中文](docs/README.zh.md)

## What it does

LLM agents already know how to write simulation scripts (PyFluent, MATLAB, etc.) from training data. But there's no standard way to **launch, control, and observe** simulations — which matters when they're long, stateful, and expensive.

ion gives AI agents (and engineers) a standard interface to engineering simulations — whether running locally, in Docker, or on cloud/HPC. Like a container runtime standardized how Kubernetes talks to containers, ion standardizes how agents talk to solvers.

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

## Quick Start

```bash
# On the machine with Fluent (e.g. win1):
uv pip install ion-cli
ion serve --host 0.0.0.0

# From anywhere on the network:
ion --host 100.90.110.79 connect --solver fluent --mode solver --ui-mode gui
ion --host 100.90.110.79 exec "solver.settings.mesh.check()"
ion --host 100.90.110.79 inspect session.summary
ion --host 100.90.110.79 disconnect
```

## Commands

| Command | What it does | Analogy |
|---|---|---|
| `ion serve` | Start HTTP server, hold solver sessions | `ollama serve` |
| `ion connect` | Launch solver, open session | `docker start` |
| `ion exec` | Run code snippet in live session | `docker exec` |
| `ion inspect` | Query live session state | `docker inspect` |
| `ion ps` | List active sessions | `docker ps` |
| `ion disconnect` | Tear down session | `docker stop` |
| `ion run` | One-shot script execution | `docker run` |
| `ion check` | Verify solver availability | `docker info` |
| `ion lint` | Validate script before running | `ruff check` |
| `ion logs` | Browse run history | `docker logs` |

## Why not just run scripts?

| Traditional (fire-and-forget) | ion (step-by-step control) |
|---|---|
| Write full script, run, hope it works | Connect → execute → observe → decide next step |
| Error at step 2 crashes at step 12 | Each step verified before proceeding |
| Agent can't see solver state | `ion inspect` between every action |
| Restart Fluent on every run | Persistent session across snippets |
| No GUI visibility | Engineer watches GUI while agent drives |

## Supported Solvers

| Solver | Status | Backend |
|---|---|---|
| Ansys Fluent | Working | PyFluent (ansys-fluent-core) |
| PyBaMM | Basic | Direct Python |
| COMSOL | Planned | MPh |
| OpenFOAM | Planned | — |

## Development

```bash
# Install
uv pip install -e ".[dev,pyfluent]"

# Run tests
pytest tests/                    # unit tests (no solver needed)
pytest --ion-host=<IP>           # integration tests (needs ion serve + Fluent)

# Lint
ruff check src/ion tests
```

## Project Structure

```
src/ion/
    cli.py              # unified CLI entry point
    server.py           # HTTP server (ion serve)
    session.py          # HTTP client (local or remote)
    drivers/
        fluent/         # Ansys Fluent driver
            driver.py
            tests/
                test_driver.py
                test_integration.py
        pybamm/         # PyBaMM driver
            driver.py
```

## License

Apache-2.0
