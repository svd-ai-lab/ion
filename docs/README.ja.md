# ion

> AIエージェントのためのシミュレーションランタイム。

Fluent、COMSOL、MATLAB、PyBaMM全体にわたるエンジニアリングシミュレーションの起動・制御・観測のためのハーネス — あらゆるLLMエージェントやCLIから利用可能。

[English](../README.md) | [Deutsch](README.de.md) | **[日本語](#ion)** | [中文](README.zh.md)

## なぜionが必要か

LLMエージェントはトレーニングデータからシミュレーションスクリプトを書くことができます。しかしエンジニアリングシミュレーションは**ステートフルで、時間がかかり、コストが高い** — Fluentの計算は数時間かかり、COMSOLモデルは数GBのメモリを消費し、パラメータの間違いは完全なやり直しを意味します。

エージェントがソルバーを起動し、1ステップを実行し、結果を観察し、次のステップを決定するための標準的な方法がありません。ionがこのギャップを埋めます：サポートされるあらゆるソルバーを制御可能で観測可能なランタイムに変える統一CLIおよびHTTPインターフェースです。

## エージェントループ

これがコアとなるアイデアです。「書いて実行して祈る」スクリプトの代わりに、ionは**ステップごとの制御ループ**を実現します：

```
    ┌─────────────────────────────────────────┐
    │              Agent (LLM)                 │
    │  "メッシュが粗い → 細分化して再計算"       │
    └─────────┬───────────────────▲────────────┘
              │ ion exec          │ ion inspect
              │ ion connect       │ ion screenshot
              │ ion lint          │ ion logs
    ┌─────────▼───────────────────┴────────────┐
    │              ion server                   │
    │          (永続セッション)                   │
    │  ┌───────────┐  ┌──────────┐  ┌────────┐ │
    │  │  Fluent   │  │  COMSOL  │  │ MATLAB │ │
    │  │  (GUI)    │  │  (GUI)   │  │        │ │
    │  └───────────┘  └──────────┘  └────────┘ │
    └──────────────────────────────────────────┘
```

エージェントがスニペットを書き、ionがライブセッションで実行し、エージェントが結果を確認して次のステップを決定 — ソルバーの再起動は不要です。

## クイックスタート

```bash
# ソルバーがインストールされたマシンで：
pip install ion-cli
ion serve --host 0.0.0.0

# どこからでも（エージェントまたはエンジニア）：
ion --host 192.168.1.10 connect --solver fluent --mode solver --ui-mode gui
ion --host 192.168.1.10 exec "solver.settings.mesh.check()"
ion --host 192.168.1.10 inspect session.summary
ion --host 192.168.1.10 exec "solver.solution.run_calculation.iterate(iter_count=100)"
ion --host 192.168.1.10 screenshot                          # GUI状態を確認
ion --host 192.168.1.10 inspect session.summary              # 収束を確認
ion --host 192.168.1.10 disconnect
```

## コマンド

| コマンド | 機能 | 類似ツール |
|---|---|---|
| `ion serve` | HTTPサーバーを起動、ソルバーセッションを保持 | `ollama serve` |
| `ion connect` | ソルバーを起動、セッションを開く | `docker start` |
| `ion exec` | ライブセッションでコードスニペットを実行 | `docker exec` |
| `ion inspect` | ライブセッション状態を照会 | `docker inspect` |
| `ion screenshot` | サーバーデスクトップをキャプチャ | 画面共有 |
| `ion ps` | アクティブセッションを一覧表示 | `docker ps` |
| `ion disconnect` | セッションを終了 | `docker stop` |
| `ion run` | ワンショットスクリプト実行 | `docker run` |
| `ion check` | ソルバーの利用可能性を確認 | `docker info` |
| `ion lint` | 実行前にスクリプトを検証 | `ruff check` |
| `ion logs` | 実行履歴を閲覧 | `docker logs` |

## なぜスクリプトをそのまま実行しないのか？

スクリプトはソルバー固有の自動化です。ionはエージェントシミュレーションワークフローの**制御プレーン**です。

| 軸 | 生のスクリプト | ion |
|---|---|---|
| **セッションモデル** | 使い捨てプロセス、毎回再起動 | スニペット間で永続セッション |
| **インターフェース** | ソルバー固有のAPI（PyFluent、MPh、matlab.engine） | 標準CLIおよびHTTPライフサイクル |
| **オブザーバビリティ** | stdout / ログファイル | `inspect`、`screenshot`、`logs`、ライブGUI |
| **リカバリー** | 最初からやり直し | 現在の状態から継続 |
| **人間の監視** | 実行後に出力ファイルを確認 | エージェント操作中にGUIを監視 |
| **マルチソルバー** | ソルバーごとにカスタムラッパー | 共通ドライバープロトコル |
| **リモート実行** | アドホックなSSH/RDP | 明示的なクライアント-サーバー境界 |

> 単一のソルバーで信頼できるバッチスクリプトを実行するだけなら、ionは不要なオーバーヘッドです。ionはエージェント（またはエンジニア）がシミュレーション状態を**探索、反復、対応する**必要がある場合に力を発揮します。

## 対応ソルバー

| ソルバー | 状態 | バックエンド | セッションモード |
|---|---|---|---|
| Ansys Fluent | 動作中 | PyFluent (ansys-fluent-core) | ワンショット、永続（メッシュ/ソルバー）、GUI |
| COMSOL | 動作中 | JPype (Java API) | ワンショット、永続、GUI |
| MATLAB | 動作中 | matlab.engine | ワンショット、永続 |
| PyBaMM | 基本対応 | Python直接実行 | ワンショット |
| OpenFOAM | 予定 | — | — |

## エージェント開発者向け

ionはエンジニアリングシミュレーションのための**標準インターフェース**を提供します — 同じコマンドがFluent、COMSOL、MATLABで動作します：

- **`connect` / `disconnect`** — サブプロセスの管理なしにソルバーライフサイクルを管理
- **`exec`** — ライブセッションにコードスニペットを送信。完全なスクリプトの生成は不要
- **`inspect`** — 構造化された状態クエリ（収束、メッシュ統計、変数値）をエージェントがパース可能
- **`screenshot`** — マルチモーダルエージェント向けにソルバーGUIからビジュアルフィードバック
- **`lint`** — 実行前に構文エラーをキャッチし、ソルバーの実行時間を無駄にしない
- **リモートファースト** — GPU/HPCマシンで`ion serve`を実行、エージェントがHTTP経由でどこからでも接続

Claude Code、Cursor、カスタムエージェントフレームワーク、または直接`httpx`呼び出しに対応。

## シミュレーションエンジニア向け

ionはソルバーを置き換えるのではなく、制御レイヤーで包みます：

- **GUIを維持** — FluentとCOMSOLはフルGUIで動作。エージェントが操作中、あなたが監視
- **永続セッション** — 変更のたびにFluentを再起動する必要なし
- **ステップ実行** — エージェントは一度に1つのスニペットを実行。ステップ間で介入可能
- **実行履歴** — `ion logs`が入出力を含むすべての実行を記録
- **リモートアクセス** — ワークステーションで`ion serve`を実行、ラップトップから制御またはエージェントが接続

## これがハーネスエンジニアリングである理由

[ハーネスエンジニアリング](https://openai.com/index/building-with-codex/)は、AIエージェントを安定的に動作させるためのシステム — ルール、ツール、検証、フィードバックループ — を構築することです。ionはシミュレーションワークフロー向けの初期ハーネスプリミティブを提供します：

| ハーネスの概念 | ionの実装 |
|---|---|
| **ルールとインターフェース** | DriverProtocol：各ソルバーが`connect`、`exec`、`inspect`、`disconnect`を実装 |
| **検証** | `ion check`（ソルバー利用可能？）、`ion lint`（スクリプト有効？）、構造化`inspect` |
| **フィードバックループ** | `exec` → `inspect` → 判断 → 再度`exec`、すべて1セッション内 |
| **オブザーバビリティ** | `ion logs`、`ion screenshot`、`ion inspect`、ライブGUI |
| **ヒューマンインザループ** | 永続セッション + GUI + ステップ実行 = エンジニアが監視・介入可能 |

## アーキテクチャ

```
任意のマシン                              ソルバーのあるマシン
┌──────────────┐    HTTP/Tailscale   ┌──────────────────┐
│  ion CLI     │ ─────────────────>  │  ion serve       │
│  (クライアント) │ <─────────────────  │  (FastAPI)       │
└──────────────┘       JSON          │       │          │
                                     │  ┌────▼────────┐ │
                                     │  │ ソルバーGUI   │ │
                                     │  │ (オプション)  │ │
                                     │  └─────────────┘ │
                                     └──────────────────┘
```

## 開発

```bash
# すべてのソルバーバックエンドでインストール
uv pip install -e ".[dev,pyfluent]"

# テスト実行
pytest tests/                    # ユニットテスト（ソルバー不要）
pytest --ion-host=<IP>           # 統合テスト（ion serve + ソルバーが必要）

# リント
ruff check src/ion tests
```

## プロジェクト構造

```
src/ion/
    cli.py              # 統一CLIエントリポイント
    server.py           # HTTPサーバー (ion serve)
    session.py          # HTTPクライアント（ローカルまたはリモート）
    driver.py           # DriverProtocolインターフェース
    runner.py           # サブプロセス実行
    store.py            # 実行履歴 (.ion/runs/)
    drivers/
        fluent/         # Ansys Fluentドライバー
        comsol/         # COMSOL Multiphysicsドライバー
        matlab/         # MATLABドライバー
        pybamm/         # PyBaMMドライバー
```

## ライセンス

Apache-2.0
