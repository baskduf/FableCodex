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
  tests/*.py
sh -n plugins/codex-fable5/bin/codex-fable5
sh -n plugins/codex-fable5/bin/codex-findings
sh -n plugins/codex-fable5/bin/codex-goals
PIN=$(python3 - <<'PY'
import re
from pathlib import Path
text = Path("README.md").read_text(encoding="utf-8")
match = re.search(r"`elder-plinius/CL4R1T4S`\s+`ANTHROPIC/CLAUDE-FABLE-5\.md`\s+at commit\s+`([0-9a-f]{40})`", text)
if not match:
    raise SystemExit("pinned FABLE-5 SHA not found in README.md")
print(match.group(1))
PY
)
mkdir -p build/fable5
curl -fsSL \
  "https://raw.githubusercontent.com/elder-plinius/CL4R1T4S/${PIN}/ANTHROPIC/CLAUDE-FABLE-5.md" \
  -o build/fable5/CLAUDE-FABLE-5.md
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  --source build/fable5/CLAUDE-FABLE-5.md
```

6. Verify no secrets, `.codex-fable5/` ledgers, or local cache files are staged.
7. Commit the release changes.
8. Tag the release with the plugin version, for example:

```bash
VERSION=$(python3 -c 'import json; print(json.load(open("plugins/codex-fable5/.codex-plugin/plugin.json"))["version"])')
git tag "v${VERSION}"
git push origin main "v${VERSION}"
```

9. Create a GitHub release that summarizes user-visible changes and links to the changelog.

## Versioning

Use semantic versioning for the plugin package:

- Patch: documentation fixes, test additions, small script fixes.
- Minor: new workflow guidance, new helper scripts, or new examples.
- Major: breaking plugin layout or behavior changes.

## Release Boundaries

Do not release changes that claim unavailable model access, include credentials, or copy protected prompt text into the repository.
