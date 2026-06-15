# Releasing

This project uses a lightweight release process because it is a small Codex plugin package.

## Release Checklist

1. Confirm the working tree is clean before release edits.
2. Update `CHANGELOG.md`.
3. Update `plugins/codex-fable5/.codex-plugin/plugin.json` when the plugin version changes.
4. Confirm README installation and usage examples still match the packaged plugin.
5. Run local verification:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile \
  plugins/codex-fable5/skills/codex-fable5/scripts/codex_findings.py \
  plugins/codex-fable5/skills/codex-fable5/scripts/codex_goals.py \
  plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  plugins/codex-fable5/skills/codex-fable5/scripts/make_litellm_config.py \
  tests/test_scripts.py
sh -n plugins/codex-fable5/bin/codex-fable5
sh -n plugins/codex-fable5/bin/codex-findings
sh -n plugins/codex-fable5/bin/codex-goals
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py
```

6. Verify no secrets, `.codex-fable5/` ledgers, or local cache files are staged.
7. Commit the release changes.
8. Tag the release with the plugin version, for example:

```bash
git tag v0.3.1
git push origin main --tags
```

9. Create a GitHub release that summarizes user-visible changes and links to the changelog.

## Versioning

Use semantic versioning for the plugin package:

- Patch: documentation fixes, test additions, small script fixes.
- Minor: new workflow guidance, new helper scripts, or new examples.
- Major: breaking plugin layout or behavior changes.

## Release Boundaries

Do not release changes that claim unavailable model access, include credentials, or copy protected prompt text into the repository.
