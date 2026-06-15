# Changelog

All notable changes to FableCodex should be documented here.

This project uses a lightweight changelog format:

- `Added` for new docs, skills, scripts, tests, or examples.
- `Changed` for updates to existing behavior or wording.
- `Fixed` for bug fixes.
- `Security` for vulnerability-related changes.

## Unreleased

### Changed

- Accounted for the `critical_child_safety_instructions` source heading in the Fable coverage matrix and mapped it to Codex-native safety guidance.
- Added explicit conversion priorities and "do not convert" boundaries for turning Claude/Fable prompt sections into Codex-native behavior.
- Added currentness notes for Fable/Mythos provider availability so routing examples are treated as templates unless official docs and account access prove availability.

## 0.4.1 - 2026-06-15

### Fixed

- Fixed `goals create --force` so stale findings from a replaced plan are archived before they can block the new final checkpoint.
- Fixed malformed `.codex-fable5` ledger JSON handling so CLI commands report controlled `codex-fable5` errors instead of Python tracebacks.

## 0.4.0 - 2026-06-15

### Added

- Added `codex_findings.py` to track evidence-backed review findings and gate final completion.
- Added the `codex-fable5` wrapper command for checkout-based terminal use, with `codex-findings` and `codex-goals` as advanced aliases.

### Changed

- Integrated open or blocked findings into the final `codex_goals.py` checkpoint gate.

## 0.3.1 - 2026-06-15

### Added

- OSS community baseline with contribution, conduct, governance, security, support, and roadmap docs.
- GitHub issue templates, pull request template, and CI workflow.
- Release checklist, CODEOWNERS, repository hygiene ignores, and GitHub Actions update automation.

### Changed

- Standardized local verification, release, and provider bridge examples on `python3`.
- Strengthened marketplace plugin path tests to verify every entry resolves inside the repository.

### Fixed

- Fixed the goal ledger so failed or blocked stories are never reported as complete.
- Reopened failed or blocked stories through `next` before advancing later pending stories.

## 0.3.0

### Added

- Codex Fable5 plugin package.
- Fable-style Codex skill with reference docs.
- Goal ledger, coverage checker, and LiteLLM config helper scripts.
- Local marketplace example and install flow.
