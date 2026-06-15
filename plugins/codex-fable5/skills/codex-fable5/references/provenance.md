# Provenance

This project is a Codex-native adaptation. It borrows ideas, not source prompt priority.

## Sources Consulted

- `elder-plinius/CL4R1T4S`, `ANTHROPIC/CLAUDE-FABLE-5.md`, commit `dc626fed52b06d687cdc812d51090c95ed03d575`.
- `fivetaku/fablize`, commit `15912466994e71a234d18fe9c74b46a68fb6a07d`.
- `itsinseong/value-for-fable`, commit `35a9bd27de961a49c343f41ac47c49114d51a328`.

## Currentness Notes

- Re-check provider facts before relying on examples that name a live model. Anthropic announced Claude Fable 5 and Claude Mythos 5 on June 9, 2026 ([announcement](https://www.anthropic.com/news/claude-fable-5-mythos-5)), and its public release notes later reported access suspension on June 12, 2026 ([release notes](https://support.claude.com/en/articles/12138966-release-notes)). Treat model names in this repo as routing examples unless current official docs and the user's account prove availability.
- Do not import source-prompt dates as active dates. Use the current Codex environment date and current official docs for product, pricing, access, model, API, and policy claims.

## Adapted Ideas

From `fablize`:

- Verification grounding for renderable or executable artifacts.
- Multi-story evidence checkpoints with a final verification gate.
- Reproduce-first investigation with competing hypotheses.
- Early-stop prevention: do the promised work or state the exact blocker.
- Capability-ceiling honesty: procedure cannot create model capability.

From `value-for-fable`:

- Value-aware routing rather than model imitation.
- Outcome-first readable communication.
- Clue-first diagnosis and cheapest discriminating measurement.
- Optional 2-pass review for high-cost misses.
- Evidence-backed findings closeout for review issues.
- Long-session drift awareness.
- Avoiding over-compression when readability and completeness matter.

## Licensing Notes

- `CL4R1T4S` and `value-for-fable` are AGPL-3.0-family sources. This project remains AGPL-3.0-or-later.
- `fablize` advertises MIT licensing in its README at the inspected commit. Its code ideas are compatible with this AGPL project, but keep attribution.
- Do not paste large sections of upstream prompt or documentation text into generated user answers. Paraphrase and cite.
