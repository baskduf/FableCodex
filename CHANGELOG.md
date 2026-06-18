# Changelog

All notable changes to FableCodex should be documented here.

This project uses a lightweight changelog format:

- `Added` for new docs, skills, scripts, tests, or examples.
- `Changed` for updates to existing behavior or wording.
- `Fixed` for bug fixes.
- `Security` for vulnerability-related changes.

## 0.5.0 - 2026-06-18

### Added

- Added `codex-fable5 version` to report the installed plugin version, paths, and git checkout state.
- Added `codex-fable5 update` to update a clean FableCodex checkout to the latest stable tag or an explicit ref.

### Changed

- Documented the new version and update commands across all localized READMEs.
- Strengthened wrapper tests for dirty-checkout protection and prerelease tag filtering.

## 0.4.4 - 2026-06-18

### Changed

- Split the monolithic script test suite into focused modules while keeping `tests/test_scripts.py` as a compatibility placeholder.
- Extracted shared state, locking, JSON, and event helpers for the goal and findings ledgers into `codex_fable_state.py`.
- Strengthened CI workflow validation so the pinned FABLE-5 source fetch and coverage `--source` validation stay semantically linked.
- Updated contributor, release, and CI verification commands to compile the new shared helper module.

## 0.4.3 - 2026-06-18

### Changed

- Condensed the Codex Fable5 skill body around non-negotiables, a core loop, and a routing map so the primary execution rules stay more salient.
- Strengthened release and test validation around pinned FABLE-5 source coverage and SKILL.md routing-map structure.

## 0.4.2 - 2026-06-18

### Changed

- Reworked the README around quick start, user control, goal ledgers, findings gates, command reference, local state, and explicit limitations.
- Added localized README files for Korean, Japanese, Simplified Chinese, and Traditional Chinese (Taiwan).
- Added explicit conversion priorities and "do not convert" boundaries for turning Claude/Fable prompt sections into Codex-native behavior.
- Added currentness notes for Fable/Mythos provider availability so routing examples are treated as templates unless official docs and account access prove availability.

### Fixed

- Hardened goal and findings ledgers against malformed state, concurrent findings writes, and failed forced plan replacement.
- Made coverage checking tolerate source markdown that starts below an H1 heading.
- Aligned release, contributor, README, and provider-bridge examples with the current package layout and verification commands.
- Removed the fabricated `claude_behavior > critical_child_safety_instructions` row from the coverage matrix. The heading does not exist in the pinned upstream `CLAUDE-FABLE-5.md` (commit `dc626fed`); it was added under a stale assumption. Coverage is now an honest 71/71.
- The CI workflow now fetches the pinned upstream FABLE-5 source and passes it to `fable_coverage.py --source`. Previously the validator ran with no `--source`, which made the matrix self-consistent and could not detect fabricated rows.
- Added `test_coverage_matrix_validates_against_pinned_source` and `test_ci_workflow_validates_against_pinned_source` so this regression cannot recur.

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
