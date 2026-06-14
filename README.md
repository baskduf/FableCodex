<div align="center">
  <img width="220" height="220" alt="Codex Fable5" src="https://github.com/user-attachments/assets/923052d7-7a76-4791-bdab-89ebe75f01a2" />

  <h1>Codex Fable5 Skill</h1>

  <p>
    <strong>Fable-style workflow guidance for Codex.</strong>
  </p>

  <p>
    <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-Skill-black?style=for-the-badge" />
    <img alt="Claude Style" src="https://img.shields.io/badge/Claude--style-Guidance-D97745?style=for-the-badge" />
    <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" />
  </p>
</div>

---

Codex Fable5 Skill is a Codex-native skill that brings Fable-style operating habits into Codex workflows.

It helps Codex work in a more structured way: inspect first, track goals, gather evidence, verify results, and report clearly.

> This project does **not** clone, unlock, or replace the Fable 5 model.<br>
> It only provides workflow guidance, prompts, examples, coverage accounting, and optional routing docs.

---

## What It Does

- Adds a Fable-style, tool-first agent loop for coding and research tasks.
- Provides a simple goal ledger with evidence checkpoints.
- Encourages conclusion-first answers, clue-first debugging, and cheapest useful checks first.
- Adds an optional final verification gate before claiming success.
- Tracks `CLAUDE-FABLE-5.md` source-heading coverage with explicit Codex decisions.
- Documents an optional provider bridge for users with valid Anthropic access.

---

## Contents

```text
skills/codex-fable5/
  Installable Codex skill.

skills/codex-fable5/references/coverage-matrix.md
  Source-section accountability matrix for Fable 5 adaptation.

skills/codex-fable5/scripts/fable_coverage.py
  Validates that a local source prompt's headings are accounted for by the matrix.

plugins/codex-fable5/
  Plugin wrapper for distributing the skill.

evals/fable-style-evals.md
  Behavioral prompts and scoring for Fable-style Codex operation.

examples/AGENTS.md
  Optional repo guidance for persistent Fable-style behavior.

examples/hooks.json
  Optional Codex hook reminder example.

examples/codex-config.litellm.toml
  Example Codex provider config for LiteLLM.

examples/litellm-fable5.yaml
  Example LiteLLM config for Anthropic routing.

scripts/install.sh
  Local installer for the skill.
```

---

## Install

From this project root:

```bash
./scripts/install.sh
```

By default, the installer copies the skill to:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/codex-fable5
```

You can override the target:

```bash
CODEX_SKILLS_DIR="$HOME/.agents/skills" ./scripts/install.sh
```

Restart Codex after installing or updating the skill.

---

## Use

In Codex:

```text
Use $codex-fable5 to run this task with a Fable-style, tool-first Codex workflow.
```

Convert a Claude/Fable-style prompt into Codex guidance:

```text
Use $codex-fable5 to convert this Claude/Fable prompt into Codex AGENTS.md guidance.
```

Create a simple multi-goal ledger:

```bash
python skills/codex-fable5/scripts/codex_goals.py create --brief "Migration" \
  --goal "inspect::Find current behavior and tests" \
  --goal "change::Implement the migration" \
  --goal "verify::Run tests and inspect output"
```

---

## Measure Fable 5 Coverage

If you have a local copy of `CLAUDE-FABLE-5.md`, run:

```bash
python skills/codex-fable5/scripts/fable_coverage.py \
  --source /path/to/CLAUDE-FABLE-5.md
```

The target is 100% source-heading accounting. That means every named source section has a Codex-native decision: implemented, adapted, unsupported, or not applicable. It does not mean model-weight parity or hidden Claude/Fable runtime parity.

---

## Optional Provider Bridge

For model routing, read:

```text
skills/codex-fable5/references/provider-bridge.md
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

MIT. See `LICENSE`, `NOTICE`, and `skills/codex-fable5/references/provenance.md`.
