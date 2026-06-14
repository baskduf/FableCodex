#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/skills/codex-fable5"
TARGET_ROOT="${CODEX_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"
TARGET="$TARGET_ROOT/codex-fable5"
PLUGIN_SRC="$ROOT/plugins/codex-fable5"

if [[ ! -f "$SRC/SKILL.md" ]]; then
  echo "Cannot find skill at $SRC" >&2
  exit 1
fi

mkdir -p "$TARGET_ROOT"
rm -rf "$TARGET"
cp -R "$SRC" "$TARGET"

echo "Installed codex-fable5 to $TARGET"
if [[ -d "$PLUGIN_SRC/.codex-plugin" ]]; then
  echo "Plugin wrapper is available at $PLUGIN_SRC"
fi
echo "Restart Codex, then invoke: Use \$codex-fable5 to run this task with a Fable-style Codex workflow."
