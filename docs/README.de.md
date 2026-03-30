# ion

> Einheitliche CLI für LLM-Agenten zur Steuerung von CAE-Simulationssoftware.

[English](../README.md) | **[Deutsch](#ion)** | [日本語](README.ja.md) | [中文](README.zh.md)

## Was es macht

LLM-Agenten können bereits Simulationsskripte schreiben (PyFluent, MATLAB usw.). Aber es gibt keine Standardmethode, um **schrittweise auszuführen, den Zustand zu beobachten und zu reagieren** — was bei langen, zustandsbehafteten und teuren Simulationen entscheidend ist.

ion ist die fehlende Laufzeitschicht. Wie `ollama` für LLMs, aber für CAE-Solver.

## Architektur

```
Mac / Agent                              Win / Server
┌──────────────┐   HTTP/Tailscale   ┌──────────────────┐
│  ion CLI     │ ────────────────>  │  ion serve       │
│  (Client)    │ <────────────────  │  (FastAPI)       │
└──────────────┘      JSON          │       │          │
                                    │  ┌────▼────────┐ │
                                    │  │ Fluent GUI   │ │
                                    │  │ (Ingenieur   │ │
                                    │  │  beobachtet) │ │
                                    │  └─────────────┘ │
                                    └──────────────────┘
```

## Schnellstart

```bash
# Auf dem Rechner mit Fluent (z.B. win1):
uv pip install ion-cli
ion serve --host 0.0.0.0

# Von überall im Netzwerk:
ion --host 100.90.110.79 connect --solver fluent --mode solver --ui-mode gui
ion --host 100.90.110.79 exec "solver.settings.mesh.check()"
ion --host 100.90.110.79 inspect session.summary
ion --host 100.90.110.79 disconnect
```

## Befehle

| Befehl | Funktion | Analogie |
|---|---|---|
| `ion serve` | HTTP-Server starten, Solver-Sitzungen halten | `ollama serve` |
| `ion connect` | Solver starten, Sitzung öffnen | `docker start` |
| `ion exec` | Code-Snippet in laufender Sitzung ausführen | `docker exec` |
| `ion inspect` | Live-Sitzungszustand abfragen | `docker inspect` |
| `ion ps` | Aktive Sitzungen auflisten | `docker ps` |
| `ion disconnect` | Sitzung beenden | `docker stop` |
| `ion run` | Einmalige Skriptausführung | `docker run` |
| `ion check` | Solver-Verfügbarkeit prüfen | `docker info` |
| `ion lint` | Skript vor Ausführung validieren | `ruff check` |
| `ion logs` | Ausführungsverlauf durchsuchen | `docker logs` |

## Warum nicht einfach Skripte ausführen?

| Traditionell (Fire-and-Forget) | ion (Schritt-für-Schritt-Kontrolle) |
|---|---|
| Ganzes Skript schreiben, ausführen, hoffen | Verbinden → Ausführen → Beobachten → Nächsten Schritt entscheiden |
| Fehler in Schritt 2 stürzt in Schritt 12 ab | Jeder Schritt wird vor dem Fortfahren überprüft |
| Agent kann Solver-Zustand nicht sehen | `ion inspect` zwischen jeder Aktion |
| Fluent bei jedem Lauf neu starten | Persistente Sitzung über Snippets hinweg |
| Keine GUI-Sichtbarkeit | Ingenieur beobachtet GUI, während Agent steuert |

## Unterstützte Solver

| Solver | Status | Backend |
|---|---|---|
| Ansys Fluent | Funktionsfähig | PyFluent (ansys-fluent-core) |
| PyBaMM | Grundlegend | Direktes Python |
| COMSOL | Geplant | MPh |
| OpenFOAM | Geplant | — |

## Lizenz

Apache-2.0
