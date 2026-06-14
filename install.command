#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "FableCodex installer"
echo "Project: $ROOT"
echo

"$ROOT/scripts/install.sh"

echo
echo "Done. Restart Codex, then invoke:"
echo 'Use $codex-fable5 to run this task with a Fable-style Codex workflow.'
echo

if [[ -t 0 ]]; then
  read -r -p "Press Return to close this window..."
fi
