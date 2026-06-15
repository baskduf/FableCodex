<div align="center">
  <img width="220" height="220" alt="Codex Fable5" src="https://github.com/user-attachments/assets/923052d7-7a76-4791-bdab-89ebe75f01a2" />

  <h1>FableCodex</h1>

  <p>
    <strong>Fable-style workflow guidance for Codex.</strong>
  </p>

  <p>
    <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-Skill-black?style=for-the-badge" />
    <img alt="Claude Style" src="https://img.shields.io/badge/Claude--style-Guidance-D97745?style=for-the-badge" />
    <img alt="License AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-blue?style=for-the-badge" />
    <a href="https://github.com/baskduf/FableCodex/actions/workflows/ci.yml">
      <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/baskduf/FableCodex/ci.yml?branch=main&label=CI&style=for-the-badge" />
    </a>
  </p>
</div>

---

FableCodex is a Codex plugin marketplace that brings Fable-style operating habits into Codex workflows.

It helps Codex work in a more structured way: inspect first, track goals, gather evidence, verify results, and report clearly.

> This project does **not** clone, unlock, or replace the Fable 5 model.<br>
> It only provides workflow guidance, prompts, examples, coverage accounting, and optional routing docs.

---

## What It Does

- Adds a Fable-style, tool-first agent loop for coding and research tasks.
- Provides a simple goal ledger with evidence checkpoints.
- Provides a findings ledger for review issues that must be resolved before final completion.
- Encourages conclusion-first answers, clue-first debugging, and cheapest useful checks first.
- Adds an optional final verification gate before claiming success.
- Tracks `CLAUDE-FABLE-5.md` source-heading coverage with explicit Codex decisions.
- Documents an optional provider bridge for users with valid Anthropic access.

---

## Install

Choose one marketplace source.

Stable release:

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.3.1
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

---

## Use

In Codex:

```text
Use $codex-fable5 to analyze this project.

Use $codex-fable5 to do this with findings tracking.

$codex-fable5로 이 프로젝트를 분석해줘.

$codex-fable5로 이 작업 진행하고, 리뷰 findings도 추적해줘.

$codex-fable5 を使って、このプロジェクトを分析してください。

$codex-fable5 を使ってこの作業を進め、レビュー findings も追跡してください。

请使用 $codex-fable5 分析这个项目。

请使用 $codex-fable5 完成这项工作，并跟踪审查 findings。

請使用 $codex-fable5 分析這個專案。

請使用 $codex-fable5 完成這項工作，並追蹤審查 findings。
```

Use the local helper from a checkout:

```bash
export PATH="$PWD/plugins/codex-fable5/bin:$PATH"
codex-fable5 status
```

Without changing `PATH`, run them by path:

```bash
plugins/codex-fable5/bin/codex-fable5 status
```

For longer work, create a goal ledger:

```bash
codex-fable5 goals create --brief "Migration" \
  --goal "inspect::Find current behavior and tests" \
  --goal "change::Implement the migration" \
  --goal "verify::Run tests and inspect output"
```

Track review findings before final completion:

```bash
codex-fable5 findings add \
  --title "Unresolved review issue" \
  --severity high \
  --source subagent \
  --evidence "Review found a missing final gate."
codex-fable5 findings gate
```

Final goal completion also fails while open or blocked findings remain. `codex-goals` and `codex-findings` are still available as advanced aliases.

---

## Findings Gate

The findings gate is an optional review closeout flow for work where missed issues are costly.

Use it when:

- A review or sub-agent finds actionable issues.
- Verification is uncertain or failed once.
- The task touches several files, migrations, security-sensitive code, or release behavior.

Do not use it for simple edits or routine answers.

In normal Codex use, ask for it in the prompt:

```text
Use $codex-fable5 to implement this and track findings before final completion.
```

For terminal use, add findings as accepted repair work:

```bash
codex-fable5 findings add \
  --title "Missing final verification" \
  --evidence "Review found no command output proving the final state."
codex-fable5 findings next
codex-fable5 findings resolve \
  --id F001 \
  --evidence "Added final verification." \
  --verify-evidence "Tests passed and final status was checked."
codex-fable5 findings gate
```

`codex-fable5 goals checkpoint --status complete` will fail while open or blocked findings remain.

---

## Measure Fable 5 Coverage

If you have a local copy of `CLAUDE-FABLE-5.md`, run:

```bash
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  --source /path/to/CLAUDE-FABLE-5.md
```

The target is 100% source-heading accounting. That means every named source section has a Codex-native decision: implemented, adapted, unsupported, or not applicable. It does not mean model-weight parity or hidden Claude/Fable runtime parity.

---

## Test

Run the stdlib-only test suite:

```bash
python3 -m unittest discover -s tests -v
```
---

## Optional Provider Bridge

For model routing, read:

```text
plugins/codex-fable5/skills/codex-fable5/references/provider-bridge.md
```

You need valid Anthropic access and a working OpenAI-compatible gateway such as LiteLLM.

This repo does not provide model access.

---

## Source Notes

This is a Codex-native adaptation inspired by:

- `elder-plinius/CL4R1T4S` `ANTHROPIC/CLAUDE-FABLE-5.md` at commit `dc626fed52b06d687cdc812d51090c95ed03d575`.
- `fivetaku/fablize` at commit `15912466994e71a234d18fe9c74b46a68fb6a07d`.
- `itsinseong/value-for-fable` at commit `35a9bd27de961a49c343f41ac47c49114d51a328`.

It paraphrases and adapts workflow ideas instead of reproducing the source prompts or documentation.

---

## License

AGPL-3.0-or-later. See `LICENSE`, `NOTICE`, and `plugins/codex-fable5/skills/codex-fable5/references/provenance.md`.
