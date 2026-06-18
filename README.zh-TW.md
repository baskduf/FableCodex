<div align="center">
  <img width="280" height="280" alt="FableCodex" src="https://github.com/user-attachments/assets/7dd154af-f885-49ca-8d94-33756e340920" />

  <h1>FableCodex</h1>

  <p>
    <strong>給 Codex 使用的證據導向工作流程關卡。</strong>
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
    <a href="README.ja.md">日本語</a> |
    <a href="README.zh-CN.md">简体中文</a> |
    繁體中文（台灣）
  </p>
</div>

---

FableCodex 是一個 Codex 外掛，會把 Fable 風格的工作習慣加入 Codex 流程：先檢查、追蹤目標、留下證據、關閉 review finding，並在宣稱完成前完成驗證。

當「漏掉一步」的代價高於「多一點流程」的代價時，它特別有用。

> FableCodex 不會複製、解鎖或取代 Fable 5 模型。
> 它不能改變模型權重、上下文長度、訓練內容或隱藏的安全系統。
> 它只提供 Codex-native 的工作流程指引、本地 ledger、範例、coverage accounting，以及選用的 routing 文件。

## 快速開始

安裝穩定版：

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.4.4
codex plugin add codex-fable5@fablecodex
```

重新啟動 Codex，然後在提示詞中呼叫這個 skill：

```text
@codex-fable5 使用這個 skill 實作這個變更。
如果工作包含多個步驟，請建立 goal ledger。
最終完成前請追蹤 findings。
在說完成之前，請執行專案測試。
```

如果只想輕量檢查，可以這樣寫：

```text
@codex-fable5 快速 review 一下。
不要建立 goal ledger。只確認關鍵證據，並只回報 actionable finding。
```

## Codex 會有什麼不同

呼叫 `@codex-fable5` 後，Codex 會讀取這個 skill，並套用更嚴謹的流程：

1. 先分類任務，再開始行動。
2. 檢查 workspace、檔案、工具或被引用的來源。
3. 使用 Codex-native 的真實工具，而不是只依賴記憶。
4. 對較長的工作，用帶有 evidence checkpoint 的 goal 追蹤進度。
5. 對 review 敏感的工作，記錄 finding，並要求最後通過 findings gate。
6. 用測試、lint、typecheck、截圖、命令輸出、原始碼檢查或 connector readback 進行驗證。
7. 回報改了什麼、驗證了什麼，以及還剩下什麼風險。

這個 skill 強化的是流程紀律，不是模型本身的能力。

## 什麼時候適合使用

適合：

- 多步驟實作或重構。
- 根因不明顯的除錯。
- CI 失敗、發布工作、遷移或安全敏感變更。
- 未解決 finding 應該阻止最終完成的 review。
- 將 Claude/Fable 風格提示詞轉成 Codex-native 指引。
- 已有授權模型存取權時設定 provider bridge。

不太需要：

- 簡短回答。
- 很小的單檔修改。
- 不需要驗證的腦力激盪。
- ledger 流程比實際工作還重的任務。

## 使用者如何控制它

使用者透過提示詞控制這個 skill。最好明確寫出範圍、嚴格程度、驗證標準與停止條件。

嚴格模式：

```text
@codex-fable5 嚴格執行。
使用 goal ledger，記錄所有 review finding，在測試和 findings gate 通過前不要說完成。
```

只分析：

```text
@codex-fable5 只分析。
不要修改檔案。用帶有檔案和行號的 finding 回報問題。
```

有限制的實作：

```text
@codex-fable5 實作這個修正。
不要 commit、push 或刪除 branch。
執行 unit test，並回報殘餘風險。
```

除錯：

```text
@codex-fable5 除錯這個失敗。
先重現，保留多個假設，收集反證，再修正並驗證。
```

## Goal Ledger

對較長的工作，helper 會把本地狀態存到 `.codex-fable5/goals.json`。

```bash
export PATH="$PWD/plugins/codex-fable5/bin:$PATH"

codex-fable5 goals create --brief "Migration" \
  --goal "inspect::確認目前行為和測試" \
  --goal "change::實作遷移" \
  --goal "verify::執行測試並檢查輸出"

codex-fable5 goals next
```

每個 goal 完成時都需要 evidence：

```bash
codex-fable5 goals checkpoint \
  --id G001 \
  --status complete \
  --evidence "已閱讀 importer.ts 和 import.test.ts；目前 parser 會拒絕引號內的逗號。"
```

最後一個 goal 也需要驗證證據：

```bash
codex-fable5 goals checkpoint \
  --id G003 \
  --status complete \
  --evidence "已實作帶引號的 CSV parsing，並更新測試。" \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "所有測試皆已通過。"
```

## Findings Gate

Finding 是已接受的 review 問題，在最終完成前不能被遺忘。它們會存放在 `.codex-fable5/findings.json`。

```bash
codex-fable5 findings add \
  --title "缺少最終驗證" \
  --severity high \
  --source review \
  --location "plugins/codex-fable5/skills/codex-fable5/scripts/codex_goals.py" \
  --evidence "即使沒有測試執行證明，final checkpoint 也可以完成。"
```

只有在修正和驗證都完成後，才 resolve finding：

```bash
codex-fable5 findings resolve \
  --id F001 \
  --evidence "final checkpoint 現在要求提供 verification evidence。" \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "回歸測試已通過。"
```

最終完成前執行 gate：

```bash
codex-fable5 findings gate
```

只要還有 `open` 或 `blocked` finding，gate 就會失敗。最終 goal completion 在有 blocking finding 時也會失敗。

## 指令參考

| 指令 | 用途 |
| --- | --- |
| `codex-fable5 status` | 查看 findings 和 goal 進度。 |
| `codex-fable5 version` | 顯示已安裝的 plugin version、路徑和 git checkout 狀態。 |
| `codex-fable5 update` | 將 FableCodex checkout/plugin package 更新到最新穩定 `v*` tag。 |
| `codex-fable5 goals create` | 建立本地 multi-step goal ledger。 |
| `codex-fable5 goals next` | 開始或繼續下一個 goal。 |
| `codex-fable5 goals checkpoint` | 帶 evidence 將 goal 標記為 complete、failed 或 blocked。 |
| `codex-fable5 findings add` | 記錄有證據支持的 review finding。 |
| `codex-fable5 findings next` | 顯示優先權最高的 open finding。 |
| `codex-fable5 findings resolve` | 用 resolution 和 verification evidence 關閉 finding。 |
| `codex-fable5 findings gate` | 如果還有 open 或 blocked finding，則失敗。 |

如果不想修改 `PATH`，可以直接執行 checkout helper：

```bash
plugins/codex-fable5/bin/codex-fable5 status
```

`codex-fable5 update` 只會變更 FableCodex checkout/plugin package。它不會變更 model access、provider credential 或 hidden runtime behavior。只有在你明確想使用開發 branch 而不是最新穩定版時，才使用 `codex-fable5 update --ref main`。

## 安裝選項

穩定版：

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.4.4
codex plugin add codex-fable5@fablecodex
```

開發版：

```bash
codex plugin marketplace add baskduf/FableCodex --ref main
codex plugin add codex-fable5@fablecodex
```

本地開發：

```bash
codex plugin marketplace add ~/Desktop/FableCodex
codex plugin add codex-fable5@fablecodex
```

安裝或更新外掛後，請重新啟動 Codex。

## 本地狀態

FableCodex 會把本地任務狀態寫入 `.codex-fable5/`：

- `goals.json`：目前的 goal plan 和 evidence。
- `findings.json`：review finding 和 closeout evidence。
- `ledger.jsonl`：append-only 事件歷史。

這些檔案是本地工作狀態。除非你明確想保留任務 transcript，否則不要提交它們。

## Coverage Accounting

如果你有本地的 `CLAUDE-FABLE-5.md`，可以檢查 source-heading coverage：

```bash
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  --source /path/to/CLAUDE-FABLE-5.md
```

目標是 100% source-heading accounting。也就是說，每個命名的 source section 都要有 Codex-native 決策：implemented、adapted、unsupported 或 not applicable。這不代表模型權重等同，也不代表隱藏的 Claude/Fable runtime parity。

## 選用 Provider Bridge

模型 routing 請閱讀：

```text
plugins/codex-fable5/skills/codex-fable5/references/provider-bridge.md
```

你需要有效的 Anthropic 存取權，以及 LiteLLM 這類 OpenAI-compatible gateway。本 repository 不提供模型存取權。

## 測試

執行 stdlib-only 測試：

```bash
python3 -m unittest discover -s tests -v
```

## 來源說明

這是 Codex-native 改編，靈感來自：

- `elder-plinius/CL4R1T4S` `ANTHROPIC/CLAUDE-FABLE-5.md` at commit `dc626fed52b06d687cdc812d51090c95ed03d575`.
- `fivetaku/fablize` at commit `15912466994e71a234d18fe9c74b46a68fb6a07d`.
- `itsinseong/value-for-fable` at commit `35a9bd27de961a49c343f41ac47c49114d51a328`.

它會轉述並適配工作流程概念，而不是重現原始 prompt 或文件。

## 認可

- FableCodex 已在 [sickn33/antigravity-awesome-skills#686](https://github.com/sickn33/antigravity-awesome-skills/pull/686) 中 listed。

## 授權

AGPL-3.0-or-later。請參閱 `LICENSE`、`NOTICE` 和 `plugins/codex-fable5/skills/codex-fable5/references/provenance.md`。
