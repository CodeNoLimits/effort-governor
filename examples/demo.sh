#!/usr/bin/env bash
# Quick demo: classify a few prompts with the CLI.
set -euo pipefail
CLI="$(cd "$(dirname "$0")/.." && pwd)/bin/effort-select"
for p in \
  "thanks!" \
  "show me the open PRs" \
  "add a tooltip to the button" \
  "why is the deploy failing, debug it" \
  "refactor the whole architecture from scratch, be exhaustive"
do
  printf '%-58s → ' "$p"
  printf '%s' "$p" | /usr/bin/python3 "$CLI" --badge
done
