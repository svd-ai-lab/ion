# ion

> Die Simulations-Runtime für KI-Agenten.

Ein Harness zum Starten, Steuern und Beobachten von Ingenieur-Simulationen — über Fluent, COMSOL, MATLAB und PyBaMM — von jedem LLM-Agenten oder CLI aus.

[English](../README.md) | **[Deutsch](#ion)** | [日本語](README.ja.md) | [中文](README.zh.md)

## Warum ion existiert

LLM-Agenten können bereits Simulationsskripte aus Trainingsdaten schreiben. Aber Ingenieursimulationen sind **zustandsbehaftet, langsam und teuer** — ein Fluent-Lauf dauert Stunden, ein COMSOL-Modell belegt Gigabytes an Speicher, und ein falscher Parameter bedeutet einen kompletten Neustart.

Es gibt keine Standardmethode, mit der ein Agent einen Solver starten, einen Schritt ausführen, das Ergebnis beobachten und den nächsten Schritt entscheiden kann. ion füllt diese Lücke: eine einheitliche CLI- und HTTP-Schnittstelle, die jeden unterstützten Solver in eine steuerbare, beobachtbare Runtime verwandelt.

## Die Agenten-Schleife

Das ist die Kernidee. Statt Fire-and-Forget-Skripten ermöglicht ion eine **schrittweise Kontrollschleife**:

```
    ┌─────────────────────────────────────────┐
    │              Agent (LLM)                 │
    │  "Netz ist zu grob → verfeinern"         │
    └─────────┬───────────────────▲────────────┘
              │ ion exec          │ ion inspect
              │ ion connect       │ ion screenshot
              │ ion lint          │ ion logs
    ┌─────────▼───────────────────┴────────────┐
    │              ion server                   │
    │         (persistente Sitzung)             │
    │  ┌───────────┐  ┌──────────┐  ┌────────┐ │
    │  │  Fluent   │  │  COMSOL  │  │ MATLAB │ │
    │  │  (GUI)    │  │  (GUI)   │  │        │ │
    │  └───────────┘  └──────────┘  └────────┘ │
    └──────────────────────────────────────────┘
```

Der Agent schreibt ein Snippet, ion führt es in einer Live-Sitzung aus, der Agent prüft das Ergebnis und entscheidet den nächsten Schritt — alles ohne den Solver neu zu starten.

## Schnellstart

```bash
# Auf dem Rechner mit dem Solver:
pip install ion-cli
ion serve --host 0.0.0.0

# Von überall (Agent oder Ingenieur):
ion --host 192.168.1.10 connect --solver fluent --mode solver --ui-mode gui
ion --host 192.168.1.10 exec "solver.settings.mesh.check()"
ion --host 192.168.1.10 inspect session.summary
ion --host 192.168.1.10 exec "solver.solution.run_calculation.iterate(iter_count=100)"
ion --host 192.168.1.10 screenshot                          # GUI-Zustand sehen
ion --host 192.168.1.10 inspect session.summary              # Konvergenz prüfen
ion --host 192.168.1.10 disconnect
```

## Befehle

| Befehl | Funktion | Analogie |
|---|---|---|
| `ion serve` | HTTP-Server starten, Solver-Sitzungen halten | `ollama serve` |
| `ion connect` | Solver starten, Sitzung öffnen | `docker start` |
| `ion exec` | Code-Snippet in laufender Sitzung ausführen | `docker exec` |
| `ion inspect` | Live-Sitzungszustand abfragen | `docker inspect` |
| `ion screenshot` | Server-Desktop erfassen | Bildschirmfreigabe |
| `ion ps` | Aktive Sitzungen auflisten | `docker ps` |
| `ion disconnect` | Sitzung beenden | `docker stop` |
| `ion run` | Einmalige Skriptausführung | `docker run` |
| `ion check` | Solver-Verfügbarkeit prüfen | `docker info` |
| `ion lint` | Skript vor Ausführung validieren | `ruff check` |
| `ion logs` | Ausführungsverlauf durchsuchen | `docker logs` |

## Warum nicht einfach Skripte ausführen?

Skripte sind solver-spezifische Automatisierung. ion ist die **Steuerungsebene** für agentenbasierte Simulations-Workflows.

| Achse | Reine Skripte | ion |
|---|---|---|
| **Sitzungsmodell** | Einmal-Prozess, Neustart bei jedem Lauf | Persistente Sitzung über Snippets hinweg |
| **Schnittstelle** | Solver-spezifische APIs (PyFluent, MPh, matlab.engine) | Standard-CLI und HTTP-Lebenszyklus |
| **Beobachtbarkeit** | stdout / Logdateien | `inspect`, `screenshot`, `logs`, Live-GUI |
| **Wiederherstellung** | Von vorn beginnen | Vom aktuellen Zustand fortfahren |
| **Menschliche Aufsicht** | Ausgabedateien nachträglich prüfen | GUI beobachten, während der Agent arbeitet |
| **Multi-Solver** | Eigener Wrapper pro Solver | Gemeinsames Treiberprotokoll |
| **Remote-Ausführung** | Ad-hoc SSH/RDP | Explizite Client-Server-Grenze |

> Wenn Sie nur ein einzelnes bewährtes Batch-Skript für einen Solver benötigen, ist ion unnötiger Overhead. ion glänzt, wenn ein Agent (oder Ingenieur) **erkunden, iterieren und auf den Simulationszustand reagieren** muss.

## Unterstützte Solver

| Solver | Status | Backend | Sitzungsmodi |
|---|---|---|---|
| Ansys Fluent | Funktionsfähig | PyFluent (ansys-fluent-core) | Einmalig, persistierend (Netz/Solver), GUI |
| COMSOL | Funktionsfähig | JPype (Java API) | Einmalig, persistierend, GUI |
| MATLAB | Funktionsfähig | matlab.engine | Einmalig, persistierend |
| PyBaMM | Grundlegend | Direktes Python | Einmalig |
| OpenFOAM | Geplant | — | — |
| [FloTHERM](https://www.siemens.com/en-us/products/simcenter/fluids-thermal-simulation/flotherm/) | Geplant | — | — |

## Für Agenten-Entwickler

ion gibt Ihrem Agenten eine **Standardschnittstelle** für Ingenieursimulationen — dieselben Befehle funktionieren mit Fluent, COMSOL und MATLAB:

- **`connect` / `disconnect`** — Solver-Lebenszyklus verwalten ohne Subprozess-Jonglage
- **`exec`** — Code-Snippets an eine laufende Sitzung senden; kein vollständiges Skript nötig
- **`inspect`** — Strukturierte Zustandsabfragen (Konvergenz, Netz-Statistiken, Variablenwerte), die der Agent parsen kann
- **`screenshot`** — Visuelles Feedback von der Solver-GUI für multimodale Agenten
- **`lint`** — Syntaxfehler vor der Ausführung abfangen, um Solver-Laufzeit nicht zu verschwenden
- **Remote-first** — `ion serve` auf GPU/HPC-Maschine, Agent verbindet sich per HTTP von überall

Funktioniert mit Claude Code, Cursor, eigenen Agenten-Frameworks oder reinen `httpx`-Aufrufen.

## Für Simulationsingenieure

ion ersetzt nicht Ihren Solver — es umhüllt ihn mit einer Steuerungsschicht:

- **GUI bleibt erhalten** — Fluent und COMSOL laufen mit voller GUI; Sie beobachten, während der Agent steuert
- **Persistente Sitzungen** — kein Fluent-Neustart nach jeder Änderung
- **Schrittweise Ausführung** — der Agent führt jeweils ein Snippet aus; Sie können zwischen den Schritten eingreifen
- **Ausführungsverlauf** — `ion logs` speichert jede Ausführung mit Ein- und Ausgaben
- **Remote-Zugriff** — `ion serve` auf Ihrer Workstation, Steuerung vom Laptop oder Agent-Zugriff

## Warum das Harness Engineering ist

[Harness Engineering](https://openai.com/index/building-with-codex/) bedeutet, das System zu bauen — Regeln, Werkzeuge, Verifikation, Feedback-Schleifen — das KI-Agenten zuverlässig arbeiten lässt. ion liefert frühe Harness-Primitiven für Simulations-Workflows:

| Harness-Konzept | ion-Umsetzung |
|---|---|
| **Regeln & Schnittstelle** | DriverProtocol: jeder Solver implementiert `connect`, `exec`, `inspect`, `disconnect` |
| **Verifikation** | `ion check` (Solver verfügbar?), `ion lint` (Skript gültig?), strukturiertes `inspect` |
| **Feedback-Schleifen** | `exec` → `inspect` → Entscheidung → erneut `exec`, alles in einer Sitzung |
| **Beobachtbarkeit** | `ion logs`, `ion screenshot`, `ion inspect`, Live-GUI |
| **Mensch-in-der-Schleife** | Persistente Sitzungen + GUI + schrittweise Ausführung = Ingenieur kann überwachen oder übernehmen |

## Architektur

```
Beliebiger Rechner                       Rechner mit Solver
┌──────────────┐    HTTP/Tailscale   ┌──────────────────┐
│  ion CLI     │ ─────────────────>  │  ion serve       │
│  (Client)    │ <─────────────────  │  (FastAPI)       │
└──────────────┘       JSON          │       │          │
                                     │  ┌────▼────────┐ │
                                     │  │ Solver GUI   │ │
                                     │  │ (optional)   │ │
                                     │  └─────────────┘ │
                                     └──────────────────┘
```

## Entwicklung

```bash
# Installation mit allen Solver-Backends
uv pip install -e ".[dev,pyfluent]"

# Tests ausführen
pytest tests/                    # Unit-Tests (kein Solver nötig)
pytest --ion-host=<IP>           # Integrationstests (benötigt ion serve + Solver)

# Lint
ruff check src/ion tests
```

## Projektstruktur

```
src/ion/
    cli.py              # Einheitlicher CLI-Einstiegspunkt
    server.py           # HTTP-Server (ion serve)
    session.py          # HTTP-Client (lokal oder remote)
    driver.py           # DriverProtocol-Schnittstelle
    runner.py           # Subprozess-Ausführung
    store.py            # Ausführungsverlauf (.ion/runs/)
    drivers/
        fluent/         # Ansys Fluent Treiber
        comsol/         # COMSOL Multiphysics Treiber
        matlab/         # MATLAB Treiber
        pybamm/         # PyBaMM Treiber
```

## Lizenz

Apache-2.0
