# Contributing

Thanks for helping improve FableCodex. This project is a Codex-native workflow plugin, so contributions should preserve its main boundary: it can improve Codex operating habits, but it must not claim to unlock or reproduce the Fable 5 model.

## Good First Contributions

- Improve documentation clarity or examples.
- Add tests for scripts, manifests, and reference files.
- Tighten provider-bridge guidance when official provider behavior changes.
- Add small, verifiable workflow helpers.
- Improve coverage accounting without copying large upstream prompt passages.

## Local Setup

This repository intentionally uses the Python standard library for tests.

```bash
python3 -m unittest discover -s tests -v
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py
```

Before opening a pull request, also run:

```bash
python3 -m py_compile \
  plugins/codex-fable5/skills/codex-fable5/scripts/codex_fable_state.py \
  plugins/codex-fable5/skills/codex-fable5/scripts/codex_findings.py \
  plugins/codex-fable5/skills/codex-fable5/scripts/codex_goals.py \
  plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  plugins/codex-fable5/skills/codex-fable5/scripts/make_litellm_config.py \
  tests/*.py
sh -n plugins/codex-fable5/bin/codex-fable5
sh -n plugins/codex-fable5/bin/codex-findings
sh -n plugins/codex-fable5/bin/codex-goals
```

## Contribution Rules

- Keep changes scoped and evidence-backed.
- Do not paste long source prompt passages or proprietary model instructions.
- Do not claim Claude, Anthropic, Fable, or Mythos identity unless an actual configured provider proves that context.
- Keep provider setup optional and credential-free.
- Do not commit `.codex-fable5/` local task ledgers or secrets.
- Prefer stdlib-only tests unless a dependency materially reduces risk.

## Pull Request Checklist

- The change matches the project boundary and does not overpromise model capability.
- Tests pass locally.
- Any current product, model, API, or provider claim is verified against an official source.
- Documentation is updated when user-facing behavior changes.
- Licensing and attribution notes remain accurate.
