<div align="center">
  <img width="280" height="280" alt="FableCodex" src="https://github.com/user-attachments/assets/7dd154af-f885-49ca-8d94-33756e340920" />

  <h1>FableCodex</h1>

  <p>
    <strong>Evidence-based workflow gates for Codex.</strong>
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
    English |
    <a href="README.ko.md">한국어</a> |
    <a href="README.ja.md">日本語</a> |
    <a href="README.zh-CN.md">简体中文</a> |
    <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---

FableCodex is a Codex plugin that adds Fable-inspired operating habits to Codex work: inspect first, track goals, record evidence, close review findings, and verify before claiming completion.

It is useful when the cost of a missed step is higher than the cost of a little process.

> FableCodex does **not** clone, unlock, or replace the Fable 5 model.
> It cannot change model weights, context length, training, or hidden safety systems.
> It only provides Codex-native workflow guidance, local ledgers, examples, coverage accounting, and optional routing docs.

## Quick Start

Install the stable release:

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.4.1
codex plugin add codex-fable5@fablecodex
```

Restart Codex, then ask for the skill in your prompt:

```text
@codex-fable5 Use this skill to implement the change.
Create a goal ledger if the work has multiple steps.
Track findings before final completion.
Run the project tests before saying it is done.
```

For a lighter pass:

```text
@codex-fable5 Review this quickly.
Do not create a goal ledger. Check the key evidence and report only actionable findings.
```

## What Changes In Codex

When you invoke `@codex-fable5`, Codex reads the skill and applies a stricter workflow:

1. Classify the task before acting.
2. Inspect the workspace, files, tools, or cited sources.
3. Use the right Codex-native tools instead of relying on memory.
4. For long work, track goals with evidence checkpoints.
5. For review-sensitive work, track findings and require a final findings gate.
6. Verify with tests, lint, typecheck, screenshots, command output, source inspection, or connector readback.
7. Report what changed, what was verified, and what risk remains.

The skill is procedural. It improves discipline, not raw model capability.

## When To Use It

Use it for:

- Multi-step implementation or refactoring.
- Debugging where the root cause is not obvious.
- CI failures, release work, migrations, or security-sensitive changes.
- Reviews where unresolved findings should block final completion.
- Converting Claude/Fable-style prompts into Codex-native guidance.
- Provider-bridge setup when you already have authorized model access.

Skip it for:

- Short answers.
- Tiny single-file edits.
- Brainstorming where no verification is expected.
- Tasks where the extra ledger process would be heavier than the work itself.

## How Users Control It

The user controls the skill through the prompt. Be explicit about scope, strictness, verification, and stopping rules.

Strict mode:

```text
@codex-fable5 Run this strictly.
Use a goal ledger, record any review findings, and do not finish until tests and findings gate pass.
```

Analysis only:

```text
@codex-fable5 Analyze only.
Do not edit files. Give findings with file and line references.
```

Implementation with limits:

```text
@codex-fable5 Implement the fix.
Do not commit, push, or delete branches.
Run unit tests and report any residual risk.
```

Debugging:

```text
@codex-fable5 Debug this failure.
Reproduce it first, keep multiple hypotheses, gather disconfirming evidence, then fix and verify.
```

## Goal Ledger

For longer work, the helper stores local state in `.codex-fable5/goals.json`.

```bash
export PATH="$PWD/plugins/codex-fable5/bin:$PATH"

codex-fable5 goals create --brief "Migration" \
  --goal "inspect::Find current behavior and tests" \
  --goal "change::Implement the migration" \
  --goal "verify::Run tests and inspect output"

codex-fable5 goals next
```

Each completed goal needs evidence:

```bash
codex-fable5 goals checkpoint \
  --id G001 \
  --status complete \
  --evidence "Read importer.ts and import.test.ts; current parser rejects quoted commas."
```

The final goal also requires verification evidence:

```bash
codex-fable5 goals checkpoint \
  --id G003 \
  --status complete \
  --evidence "Implemented quoted CSV parsing and updated tests." \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "All tests passed."
```

## Findings Gate

Findings are accepted review issues that must not be lost before final completion. They are stored in `.codex-fable5/findings.json`.

```bash
codex-fable5 findings add \
  --title "Missing final verification" \
  --severity high \
  --source review \
  --location "plugins/codex-fable5/skills/codex-fable5/scripts/codex_goals.py:180" \
  --evidence "Final checkpoint can complete without proof that tests ran."
```

Resolve a finding only after the fix and verification are done:

```bash
codex-fable5 findings resolve \
  --id F001 \
  --evidence "Final checkpoints now require verification evidence." \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "Regression test passed."
```

Run the gate before final completion:

```bash
codex-fable5 findings gate
```

The gate fails while `open` or `blocked` findings remain. Final goal completion also fails while blocking findings remain.

## Command Reference

| Command | Purpose |
| --- | --- |
| `codex-fable5 status` | Show findings and goal progress. |
| `codex-fable5 goals create` | Create a local multi-step goal ledger. |
| `codex-fable5 goals next` | Start or resume the next goal. |
| `codex-fable5 goals checkpoint` | Mark a goal complete, failed, or blocked with evidence. |
| `codex-fable5 findings add` | Record an evidence-backed review finding. |
| `codex-fable5 findings next` | Show the highest-priority open finding. |
| `codex-fable5 findings resolve` | Close a finding with resolution and verification evidence. |
| `codex-fable5 findings gate` | Fail if open or blocked findings remain. |

Without changing `PATH`, run the checkout helper directly:

```bash
plugins/codex-fable5/bin/codex-fable5 status
```

## Install Options

Stable release:

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.4.1
codex plugin add codex-fable5@fablecodex
```

Development version:

```bash
codex plugin marketplace add baskduf/FableCodex --ref main
codex plugin add codex-fable5@fablecodex
```

Local development:

```bash
codex plugin marketplace add ~/Desktop/FableCodex
codex plugin add codex-fable5@fablecodex
```

Restart Codex after installing or updating the plugin.

## Local State

FableCodex writes local task state under `.codex-fable5/`:

- `goals.json`: current goal plan and evidence.
- `findings.json`: review findings and closeout evidence.
- `ledger.jsonl`: append-only event history.

These files are local working state and should not be committed unless you intentionally want to preserve a task transcript.

## Coverage Accounting

If you have a local copy of `CLAUDE-FABLE-5.md`, you can check source-heading coverage:

```bash
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  --source /path/to/CLAUDE-FABLE-5.md
```

The target is 100% source-heading accounting. That means every named source section has a Codex-native decision: implemented, adapted, unsupported, or not applicable. It does not mean model-weight parity or hidden Claude/Fable runtime parity.

## Optional Provider Bridge

For model routing, read:

```text
plugins/codex-fable5/skills/codex-fable5/references/provider-bridge.md
```

You need valid Anthropic access and a working OpenAI-compatible gateway such as LiteLLM. This repository does not provide model access.

## Test

Run the stdlib-only test suite:

```bash
python3 -m unittest discover -s tests -v
```

## Source Notes

This is a Codex-native adaptation inspired by:

- `elder-plinius/CL4R1T4S` `ANTHROPIC/CLAUDE-FABLE-5.md` at commit `dc626fed52b06d687cdc812d51090c95ed03d575`.
- `fivetaku/fablize` at commit `15912466994e71a234d18fe9c74b46a68fb6a07d`.
- `itsinseong/value-for-fable` at commit `35a9bd27de961a49c343f41ac47c49114d51a328`.

It paraphrases and adapts workflow ideas instead of reproducing source prompts or documentation.

## Recognition

- FableCodex was listed in [sickn33/antigravity-awesome-skills#686](https://github.com/sickn33/antigravity-awesome-skills/pull/686).

## License

AGPL-3.0-or-later. See `LICENSE`, `NOTICE`, and `plugins/codex-fable5/skills/codex-fable5/references/provenance.md`.
