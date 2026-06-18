<div align="center">
  <img width="280" height="280" alt="FableCodex" src="https://github.com/user-attachments/assets/7dd154af-f885-49ca-8d94-33756e340920" />

  <h1>FableCodex</h1>

  <p>
    <strong>面向 Codex 的证据驱动工作流关卡。</strong>
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
    简体中文 |
    <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---

FableCodex 是一个 Codex 插件，用来把 Fable 风格的工作习惯加入 Codex 流程：先检查，再跟踪目标，记录证据，关闭 review finding，并在声称完成前进行验证。

当“漏掉一步”的代价高于“多走一点流程”的代价时，它最有价值。

> FableCodex 不会复制、解锁或替代 Fable 5 模型。
> 它不能改变模型权重、上下文长度、训练内容或隐藏的安全系统。
> 它只提供 Codex-native 的工作流指导、本地 ledger、示例、coverage accounting 和可选的 routing 文档。

## 快速开始

安装稳定版：

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.4.3
codex plugin add codex-fable5@fablecodex
```

重启 Codex，然后在提示词中调用这个 skill：

```text
@codex-fable5 使用这个 skill 实现这个改动。
如果工作包含多个步骤，请创建 goal ledger。
最终完成前请跟踪 findings。
在说完成之前，请运行项目测试。
```

如果只想轻量检查，可以这样写：

```text
@codex-fable5 快速 review 一下。
不要创建 goal ledger。只检查关键证据，并只报告 actionable finding。
```

## Codex 会发生什么变化

调用 `@codex-fable5` 后，Codex 会读取这个 skill，并采用更严格的流程：

1. 先分类任务，再开始行动。
2. 检查 workspace、文件、工具或被引用的来源。
3. 使用 Codex-native 的真实工具，而不是只依赖记忆。
4. 对较长任务，用带 evidence checkpoint 的 goal 跟踪进度。
5. 对 review 敏感的任务，记录 finding，并要求最终 findings gate。
6. 使用测试、lint、typecheck、截图、命令输出、源码检查或 connector readback 做验证。
7. 报告改了什么、验证了什么、还剩什么风险。

这个 skill 改进的是流程纪律，不是模型本身的能力。

## 什么时候适合使用

适合：

- 多步骤实现或重构。
- 根因不明显的调试。
- CI 失败、发布工作、迁移或安全敏感改动。
- 未解决 finding 应该阻止最终完成的 review。
- 把 Claude/Fable 风格提示词转换为 Codex-native 指导。
- 已有授权模型访问权限时配置 provider bridge。

不太需要：

- 简短回答。
- 很小的单文件修改。
- 不需要验证的头脑风暴。
- ledger 流程比实际工作还重的任务。

## 用户如何控制它

用户通过提示词控制这个 skill。最好明确写出范围、严格程度、验证标准和停止条件。

严格模式：

```text
@codex-fable5 严格执行。
使用 goal ledger，记录所有 review finding，在测试和 findings gate 通过前不要说完成。
```

只分析：

```text
@codex-fable5 只分析。
不要修改文件。用带文件和行号的 finding 报告问题。
```

带限制的实现：

```text
@codex-fable5 实现这个修复。
不要 commit、push 或删除 branch。
运行 unit test，并报告残余风险。
```

调试：

```text
@codex-fable5 调试这个失败。
先复现，保留多个假设，收集反证，再修复并验证。
```

## Goal Ledger

对于较长任务，helper 会把本地状态存到 `.codex-fable5/goals.json`。

```bash
export PATH="$PWD/plugins/codex-fable5/bin:$PATH"

codex-fable5 goals create --brief "Migration" \
  --goal "inspect::确认当前行为和测试" \
  --goal "change::实现迁移" \
  --goal "verify::运行测试并检查输出"

codex-fable5 goals next
```

每个 goal 完成时都需要 evidence：

```bash
codex-fable5 goals checkpoint \
  --id G001 \
  --status complete \
  --evidence "已阅读 importer.ts 和 import.test.ts；当前 parser 会拒绝引号内的逗号。"
```

最后一个 goal 还需要验证证据：

```bash
codex-fable5 goals checkpoint \
  --id G003 \
  --status complete \
  --evidence "已实现带引号的 CSV parsing，并更新测试。" \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "所有测试均已通过。"
```

## Findings Gate

Finding 是已经接受的 review 问题，最终完成前不能遗忘。它们存放在 `.codex-fable5/findings.json`。

```bash
codex-fable5 findings add \
  --title "缺少最终验证" \
  --severity high \
  --source review \
  --location "plugins/codex-fable5/skills/codex-fable5/scripts/codex_goals.py" \
  --evidence "即使没有测试运行证明，final checkpoint 也可以完成。"
```

只有完成修复和验证后，才 resolve finding：

```bash
codex-fable5 findings resolve \
  --id F001 \
  --evidence "final checkpoint 现在要求提供 verification evidence。" \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "回归测试已通过。"
```

最终完成前运行 gate：

```bash
codex-fable5 findings gate
```

只要还存在 `open` 或 `blocked` finding，gate 就会失败。最终 goal completion 在存在 blocking finding 时也会失败。

## 命令参考

| 命令 | 用途 |
| --- | --- |
| `codex-fable5 status` | 查看 findings 和 goal 进度。 |
| `codex-fable5 goals create` | 创建本地 multi-step goal ledger。 |
| `codex-fable5 goals next` | 开始或继续下一个 goal。 |
| `codex-fable5 goals checkpoint` | 带 evidence 将 goal 标记为 complete、failed 或 blocked。 |
| `codex-fable5 findings add` | 记录有证据支持的 review finding。 |
| `codex-fable5 findings next` | 显示优先级最高的 open finding。 |
| `codex-fable5 findings resolve` | 用 resolution 和 verification evidence 关闭 finding。 |
| `codex-fable5 findings gate` | 如果还有 open 或 blocked finding，则失败。 |

如果不想修改 `PATH`，可以直接运行 checkout helper：

```bash
plugins/codex-fable5/bin/codex-fable5 status
```

## 安装选项

稳定版：

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.4.3
codex plugin add codex-fable5@fablecodex
```

开发版：

```bash
codex plugin marketplace add baskduf/FableCodex --ref main
codex plugin add codex-fable5@fablecodex
```

本地开发：

```bash
codex plugin marketplace add ~/Desktop/FableCodex
codex plugin add codex-fable5@fablecodex
```

安装或更新插件后，请重启 Codex。

## 本地状态

FableCodex 会把本地任务状态写入 `.codex-fable5/`：

- `goals.json`：当前 goal plan 和 evidence。
- `findings.json`：review finding 和 closeout evidence。
- `ledger.jsonl`：append-only 事件历史。

这些文件是本地工作状态。除非你明确想保留任务 transcript，否则不要提交它们。

## Coverage Accounting

如果你有本地的 `CLAUDE-FABLE-5.md`，可以检查 source-heading coverage：

```bash
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  --source /path/to/CLAUDE-FABLE-5.md
```

目标是 100% source-heading accounting。也就是说，每个命名的 source section 都要有 Codex-native 决策：implemented、adapted、unsupported 或 not applicable。这不代表模型权重等同，也不代表隐藏的 Claude/Fable runtime parity。

## 可选 Provider Bridge

模型 routing 请阅读：

```text
plugins/codex-fable5/skills/codex-fable5/references/provider-bridge.md
```

你需要有效的 Anthropic 访问权限，以及 LiteLLM 这样的 OpenAI-compatible gateway。本仓库不提供模型访问权限。

## 测试

运行 stdlib-only 测试：

```bash
python3 -m unittest discover -s tests -v
```

## 来源说明

这是一个 Codex-native 改编，灵感来自：

- `elder-plinius/CL4R1T4S` `ANTHROPIC/CLAUDE-FABLE-5.md` at commit `dc626fed52b06d687cdc812d51090c95ed03d575`.
- `fivetaku/fablize` at commit `15912466994e71a234d18fe9c74b46a68fb6a07d`.
- `itsinseong/value-for-fable` at commit `35a9bd27de961a49c343f41ac47c49114d51a328`.

它会转述并适配工作流思想，而不是复刻原始 prompt 或文档。

## 认可

- FableCodex 已在 [sickn33/antigravity-awesome-skills#686](https://github.com/sickn33/antigravity-awesome-skills/pull/686) 中 listed。

## 许可证

AGPL-3.0-or-later。请参阅 `LICENSE`、`NOTICE` 和 `plugins/codex-fable5/skills/codex-fable5/references/provenance.md`。
