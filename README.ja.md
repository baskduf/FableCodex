<div align="center">
  <img width="280" height="280" alt="FableCodex" src="https://github.com/user-attachments/assets/7dd154af-f885-49ca-8d94-33756e340920" />

  <h1>FableCodex</h1>

  <p>
    <strong>Codex のための、証拠ベースのワークフローゲート。</strong>
  </p>

  <p>
    <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-Skill-black?style=for-the-badge" />
    <img alt="Claude Style" src="https://img.shields.io/badge/Claude--style-Guidance-D97745?style=for-the-badge" />
    <img alt="License AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-blue?style=for-the-badge" />
    <a href="https://github.com/baskduf/FableCodex/actions/workflows/ci.yml">
      <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/baskduf/FableCodex/ci.yml?branch=main&label=CI&style=for-the-badge" />
    </a>
  </p>

  <p>
    <a href="README.md">English</a> |
    <a href="README.ko.md">한국어</a> |
    日本語 |
    <a href="README.zh-CN.md">简体中文</a> |
    <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---

FableCodex は、Codex の作業に Fable 風の運用習慣を追加する Codex プラグインです。先に調査し、目標を追跡し、根拠を残し、レビュー finding を閉じ、完了と言う前に検証する流れを作ります。

少しの手順よりも、手順の抜け漏れのコストが大きい作業で役に立ちます。

> FableCodex は Fable 5 モデルを複製、解放、置換するものではありません。
> モデルの重み、コンテキスト長、学習内容、隠れた安全システムは変更できません。
> Codex-native なワークフロー指針、ローカル ledger、例、coverage accounting、任意の routing ドキュメントを提供するだけです。

## クイックスタート

安定版をインストールします。

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.5.0
codex plugin add codex-fable5@fablecodex
```

Codex を再起動してから、プロンプトで skill を呼び出します。

```text
@codex-fable5 この変更を実装してください。
作業が複数ステップなら goal ledger を作成してください。
最終完了の前に findings を追跡してください。
完了と言う前にプロジェクトのテストを実行してください。
```

軽く確認したい場合は、次のように指定します。

```text
@codex-fable5 短くレビューしてください。
goal ledger は作らず、重要な根拠だけ確認して actionable finding だけ報告してください。
```

## Codex で何が変わるか

`@codex-fable5` を呼び出すと、Codex は skill を読み、より厳密なワークフローを適用します。

1. 行動する前にタスクを分類します。
2. ワークスペース、ファイル、ツール、参照された情報源を確認します。
3. 記憶に頼らず、Codex-native な実ツールを使います。
4. 長い作業では、根拠 checkpoint 付きの goal で進捗を追跡します。
5. レビューに注意が必要な作業では、finding を記録し、最後に findings gate を要求します。
6. テスト、lint、typecheck、スクリーンショット、コマンド出力、ソース確認、connector readback で検証します。
7. 何を変更し、何を検証し、どんなリスクが残るかを報告します。

この skill は手順を強化するものです。モデルそのものの能力を上げるものではありません。

## 使うべき場面

適している作業:

- 複数ステップの実装やリファクタリング。
- 原因がすぐに分からないデバッグ。
- CI 失敗、リリース作業、マイグレーション、セキュリティに関わる変更。
- 未解決 finding が最終完了を止めるべきレビュー。
- Claude/Fable 風のプロンプトを Codex-native な指針へ変換する作業。
- すでに許可されたモデルアクセスがある状態での provider bridge 設定。

使わなくてもよい作業:

- 短い回答。
- ごく小さな単一ファイル修正。
- 検証を前提としないブレインストーミング。
- ledger の手間が実作業より重くなる場合。

## ユーザーが制御する方法

ユーザーはプロンプトでこの skill を制御します。範囲、厳密さ、検証条件、停止条件を具体的に書くのが効果的です。

厳密モード:

```text
@codex-fable5 厳密に進めてください。
goal ledger を使い、レビュー finding を記録し、テストと findings gate が通るまで完了と言わないでください。
```

分析のみ:

```text
@codex-fable5 分析だけしてください。
ファイルは編集せず、ファイル名と行番号付きの finding として報告してください。
```

制限付きの実装:

```text
@codex-fable5 修正を実装してください。
commit、push、branch 削除はしないでください。
unit test を実行し、残るリスクを報告してください。
```

デバッグ:

```text
@codex-fable5 この失敗をデバッグしてください。
まず再現し、複数の仮説を保ち、反証となる根拠を集めてから修正し、検証してください。
```

## Goal Ledger

長い作業では、helper が `.codex-fable5/goals.json` にローカル状態を保存します。

```bash
export PATH="$PWD/plugins/codex-fable5/bin:$PATH"

codex-fable5 goals create --brief "Migration" \
  --goal "inspect::現在の動作とテストを確認する" \
  --goal "change::マイグレーションを実装する" \
  --goal "verify::テストを実行して結果を確認する"

codex-fable5 goals next
```

各 goal を完了するには evidence が必要です。

```bash
codex-fable5 goals checkpoint \
  --id G001 \
  --status complete \
  --evidence "importer.ts と import.test.ts を読み、現在の parser が引用符内のカンマを拒否することを確認した。"
```

最後の goal には検証根拠も必要です。

```bash
codex-fable5 goals checkpoint \
  --id G003 \
  --status complete \
  --evidence "引用符付き CSV parsing を実装し、テストを更新した。" \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "すべてのテストが通過した。"
```

## Findings Gate

Finding は、最終完了までに忘れてはいけない、受け入れ済みのレビュー指摘です。`.codex-fable5/findings.json` に保存されます。

```bash
codex-fable5 findings add \
  --title "最終検証の不足" \
  --severity high \
  --source review \
  --location "plugins/codex-fable5/skills/codex-fable5/scripts/codex_goals.py" \
  --evidence "テスト実行の証拠がなくても final checkpoint が完了できる。"
```

修正と検証が終わってから finding を resolve します。

```bash
codex-fable5 findings resolve \
  --id F001 \
  --evidence "final checkpoint が verification evidence を要求するようになった。" \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "回帰テストが通過した。"
```

最終完了の前に gate を実行します。

```bash
codex-fable5 findings gate
```

`open` または `blocked` の finding が残っている間、gate は失敗します。blocking finding が残っている場合、最後の goal completion も失敗します。

## コマンド一覧

| コマンド | 目的 |
| --- | --- |
| `codex-fable5 status` | findings と goal の進捗を表示します。 |
| `codex-fable5 version` | インストール済み plugin version、パス、git checkout 状態を表示します。 |
| `codex-fable5 update` | FableCodex checkout/plugin package を最新の安定版 `v*` tag に更新します。 |
| `codex-fable5 goals create` | ローカルの multi-step goal ledger を作成します。 |
| `codex-fable5 goals next` | 次の goal を開始または再開します。 |
| `codex-fable5 goals checkpoint` | evidence 付きで goal を complete、failed、blocked にします。 |
| `codex-fable5 findings add` | 根拠のあるレビュー finding を記録します。 |
| `codex-fable5 findings next` | 優先度が最も高い open finding を表示します。 |
| `codex-fable5 findings resolve` | resolution と verification evidence で finding を閉じます。 |
| `codex-fable5 findings gate` | open または blocked finding が残っていると失敗します。 |

`PATH` を変更しない場合は、checkout helper を直接実行します。

```bash
plugins/codex-fable5/bin/codex-fable5 status
```

`codex-fable5 update` が変更するのは FableCodex checkout/plugin package だけです。model access、provider credential、hidden runtime behavior は変更しません。最新の安定版ではなく開発 branch を意図的に使う場合だけ、`codex-fable5 update --ref main` を使用してください。

## インストール方法

安定版:

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.5.0
codex plugin add codex-fable5@fablecodex
```

開発版:

```bash
codex plugin marketplace add baskduf/FableCodex --ref main
codex plugin add codex-fable5@fablecodex
```

ローカル開発:

```bash
codex plugin marketplace add ~/Desktop/FableCodex
codex plugin add codex-fable5@fablecodex
```

プラグインをインストールまたは更新した後は Codex を再起動してください。

## ローカル状態

FableCodex はローカル作業状態を `.codex-fable5/` 配下に書き込みます。

- `goals.json`: 現在の goal plan と evidence。
- `findings.json`: レビュー finding と closeout evidence。
- `ledger.jsonl`: append-only のイベント履歴。

これらはローカル作業状態です。作業 transcript を意図的に残す場合を除き、commit しないでください。

## Coverage Accounting

ローカルに `CLAUDE-FABLE-5.md` のコピーがある場合、source heading coverage を確認できます。

```bash
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  --source /path/to/CLAUDE-FABLE-5.md
```

目標は source heading の 100% accounting です。つまり、すべての source section に Codex-native な判断が必要です: implemented、adapted、unsupported、not applicable。これはモデル重みや隠れた Claude/Fable runtime parity を意味しません。

## 任意の Provider Bridge

モデル routing については次の文書を読んでください。

```text
plugins/codex-fable5/skills/codex-fable5/references/provider-bridge.md
```

有効な Anthropic アクセス権と、LiteLLM のような OpenAI-compatible gateway が必要です。このリポジトリはモデルアクセスを提供しません。

## テスト

stdlib-only のテストを実行します。

```bash
python3 -m unittest discover -s tests -v
```

## 出典メモ

このプロジェクトは、次の資料に着想を得た Codex-native な再構成です。

- `elder-plinius/CL4R1T4S` `ANTHROPIC/CLAUDE-FABLE-5.md` at commit `dc626fed52b06d687cdc812d51090c95ed03d575`.
- `fivetaku/fablize` at commit `15912466994e71a234d18fe9c74b46a68fb6a07d`.
- `itsinseong/value-for-fable` at commit `35a9bd27de961a49c343f41ac47c49114d51a328`.

元の prompt や文書を再現するのではなく、workflow の考え方を要約し、Codex 向けに適応しています。

## 認知

- FableCodex は [sickn33/antigravity-awesome-skills#686](https://github.com/sickn33/antigravity-awesome-skills/pull/686) に listed されました。

## ライセンス

AGPL-3.0-or-later。`LICENSE`、`NOTICE`、`plugins/codex-fable5/skills/codex-fable5/references/provenance.md` を参照してください。
