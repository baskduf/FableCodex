# Security Policy

FableCodex is mostly documentation and small local helper scripts, but security still matters because the project discusses model routing, provider credentials, and local automation.

## Supported Versions

Security fixes target the default branch first. Released plugin versions should be updated when a fix affects installed users.

## Reporting a Vulnerability

If GitHub private vulnerability reporting is enabled, use the repository's Security tab. If it is not enabled, open a minimal public issue asking for private maintainer contact and do not include exploit details, secrets, tokens, or reproduction steps that could harm users.

Please include privately:

- A short summary of the issue.
- Affected files or workflows.
- Reproduction steps.
- Impact and likely severity.
- Suggested fix, if known.

## Security Boundaries

- Do not commit API keys, LiteLLM keys, Anthropic keys, OpenAI keys, or provider tokens.
- Do not add generated apps that assume hidden provider credentials exist.
- Do not paste leaked or proprietary system prompts as project content.
- Do not add commands that exfiltrate local files, environment variables, or connector data.
- Keep provider bridge examples credential-free and clearly optional.

## Disclosure

Maintainers should acknowledge valid reports, prepare a fix on a private branch or local patch when possible, and publish a concise advisory or release note after users can update.

