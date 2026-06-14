# Codex Fable5 Skill

This project packages a Codex skill that adapts Claude Fable 5 style operating guidance into Codex-native workflows.

It does four things:

1. Gives Codex a Fable-style, tool-first agent loop for long-horizon coding and research tasks.
2. Adds a `fablize`-style goal ledger with evidence checkpoints and a final verification gate.
3. Adds `Value-for-Fable`-style operating guidance: conclusion-first prose, clue-first diagnosis, cheapest measurement first, cost-aware routing, and optional 2-pass review.
4. Documents an optional provider bridge for users who already have authorized access to a Fable-compatible Anthropic model and want to route Codex through an OpenAI-compatible gateway.

It does not clone or unlock the Fable 5 model. Prompting and skills can improve behavior, but actual model capability requires an actual model endpoint.

## Contents

- `skills/codex-fable5/`: the installable Codex skill.
- `plugins/codex-fable5/`: plugin wrapper for distributing the skill as a Codex plugin.
- `examples/AGENTS.md`: optional repo guidance for users who want persistent Fable-style behavior without invoking the skill every time.
- `examples/hooks.json`: optional Codex hook reminder example.
- `examples/codex-config.litellm.toml`: example Codex provider config for a LiteLLM gateway.
- `examples/litellm-fable5.yaml`: example LiteLLM config for Anthropic routing.
- `scripts/install.sh`: copies the skill into a local Codex skills directory.

## Install The Skill

From this project root:

```bash
./scripts/install.sh
```

By default the installer copies the skill to:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/codex-fable5
```

Override the target when needed:

```bash
CODEX_SKILLS_DIR="$HOME/.agents/skills" ./scripts/install.sh
```

Restart Codex after installing or updating the skill.

## Use As A Plugin

The plugin wrapper is at:

```text
plugins/codex-fable5
```

Install it with your preferred Codex plugin workflow or copy it into a local plugin marketplace. The plugin contains the same `codex-fable5` skill under its `skills/` directory.

## Use The Skill

In Codex, invoke:

```text
Use $codex-fable5 to run this task with a Fable-style, tool-first Codex workflow.
```

For prompt conversion:

```text
Use $codex-fable5 to convert this Claude/Fable prompt into Codex AGENTS.md guidance.
```

For multi-story work with a verification gate:

```bash
python skills/codex-fable5/scripts/codex_goals.py create --brief "Migration" \
  --goal "inspect::Find current behavior and tests" \
  --goal "change::Implement the migration" \
  --goal "verify::Run tests and inspect output"
```

For actual model routing, read `skills/codex-fable5/references/provider-bridge.md` first. You need valid Anthropic access and a working OpenAI-compatible gateway.

## Source And License

This is a Codex-native adaptation inspired by:

- `elder-plinius/CL4R1T4S` `ANTHROPIC/CLAUDE-FABLE-5.md` at commit `dc626fed52b06d687cdc812d51090c95ed03d575`.
- `fivetaku/fablize` at commit `15912466994e71a234d18fe9c74b46a68fb6a07d`.
- `itsinseong/value-for-fable` at commit `35a9bd27de961a49c343f41ac47c49114d51a328`.

It paraphrases and adapts workflow ideas instead of reproducing the source prompts or documentation.

This adaptation is distributed under AGPL-3.0-or-later. See `NOTICE` and `skills/codex-fable5/references/provenance.md`.
