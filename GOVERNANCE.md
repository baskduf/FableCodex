# Governance

FableCodex is maintained as a small, pragmatic OSS project. The governance model is intentionally lightweight until the contributor base grows.

## Roles

- Maintainers own releases, plugin packaging, security response, and final merge decisions.
- Contributors propose changes through issues and pull requests.
- Reviewers may provide technical feedback, testing, and documentation review without release authority.

## Decision Making

Maintainers prefer consensus, but the project optimizes for clear boundaries and verifiable behavior over broad agreement. A change is easier to accept when it:

- Preserves the "workflow adaptation, not model replacement" boundary.
- Improves user outcomes with concrete evidence.
- Adds or updates tests for behavior that can regress.
- Avoids credential, copyright, and provider identity risk.
- Keeps the plugin small enough to understand.

If maintainers disagree, the default decision is to keep the current behavior until a narrower, better-evidenced proposal exists.

## Release Criteria

A release should have:

- Passing tests.
- Valid plugin and marketplace manifests.
- Updated README, NOTICE, or provenance notes when relevant.
- No committed secrets or local task state.
- A clear changelog or release note for user-visible changes.

## Project Boundaries

FableCodex may provide Codex skills, examples, tests, docs, and optional provider-bridge guidance. It should not ship hidden credentials, claim unavailable model access, impersonate another provider, or copy large protected prompt text.

