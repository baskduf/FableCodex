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
- Encourages conclusion-first answers, clue-first debugging, and cheapest useful checks first.
- Adds an optional final verification gate before claiming success.
- Tracks `CLAUDE-FABLE-5.md` source-heading coverage with explicit Codex decisions.
- Documents an optional provider bridge for users with valid Anthropic access.

---

## Contents

```text
.agents/plugins/marketplace.json
  Repo-local Codex marketplace entry.

plugins/codex-fable5/
  Marketplace plugin package.

plugins/codex-fable5/skills/codex-fable5/
  Codex skill bundled inside the plugin.

plugins/codex-fable5/skills/codex-fable5/references/coverage-matrix.md
  Source-section accountability matrix for Fable 5 adaptation.

plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py
  Validates that a local source prompt's headings are accounted for by the matrix.

evals/fable-style-evals.md
  Behavioral prompts and scoring for Fable-style Codex operation.

tests/test_scripts.py
  Stdlib-only regression tests for manifests, scripts, and license text.

.github/workflows/ci.yml
  GitHub Actions CI for tests, script compilation, and coverage matrix validation.

.github/CODEOWNERS, .github/dependabot.yml
  Maintainer ownership and GitHub Actions dependency update automation.

CONTRIBUTING.md, CODE_OF_CONDUCT.md, GOVERNANCE.md, SECURITY.md, SUPPORT.md, ROADMAP.md, CHANGELOG.md
  OSS contribution, conduct, governance, security, support, planning, and release notes.

docs/RELEASING.md
  Release checklist for plugin version updates.

examples/AGENTS.md
  Optional repo guidance for persistent Fable-style behavior.

examples/hooks.json
  Optional Codex hook reminder example.

examples/codex-config.litellm.toml
  Example Codex provider config for LiteLLM.

examples/litellm-fable5.yaml
  Example LiteLLM config for Anthropic routing.
```

---

## Install

Use this repo directly as a local marketplace:

```bash
codex plugin marketplace add ~/Desktop/FableCodex
codex plugin add codex-fable5@fablecodex
```

Restart Codex after installing or updating the plugin.

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
python3 plugins/codex-fable5/skills/codex-fable5/scripts/codex_goals.py create --brief "Migration" \
  --goal "inspect::Find current behavior and tests" \
  --goal "change::Implement the migration" \
  --goal "verify::Run tests and inspect output"
```

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

## Community

- Read `CONTRIBUTING.md` before opening issues or pull requests.
- Use `CODE_OF_CONDUCT.md` as the participation baseline.
- Follow `SECURITY.md` for vulnerability reports and provider credential concerns.
- Use `GOVERNANCE.md` and `ROADMAP.md` to understand project direction and decision-making.
- Use `docs/RELEASING.md` when cutting plugin releases.

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
