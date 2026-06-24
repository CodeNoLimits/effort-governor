#!/usr/bin/env bash
# Grok / tmux adapter for effort-governor.
#
# Grok (and most TUI agents) take a prompt string. There is no per-turn effort
# budget to set, so we PREFIX the prompt with a calibrated effort directive —
# the same engine that drives the Claude Code hook.
#
# Usage A — wrap a single send:
#   source adapters/grok_tmux/grok_effort_prefix.sh
#   grok-ask "$(effort_prefix "refactor the auth module") refactor the auth module"
#
# Usage B — inside your own controller (e.g. grokctl), build the framed prompt:
#   eff="$(printf '%s' "$task" | effort-select --prefix)"
#   grok -p "[$eff] $task"
#
# Point EFFORT_GOVERNOR_HOME at this repo (defaults shown below).
EFFORT_GOVERNOR_HOME="${EFFORT_GOVERNOR_HOME:-$HOME/Projects/Active/effort-governor}"

effort_prefix() {  # $* = task ; echoes "[EFFORT <LEVEL> — <directive>]"
  local task="$*" eff
  eff="$(printf '%s' "$task" | /usr/bin/python3 "$EFFORT_GOVERNOR_HOME/bin/effort-select" --prefix 2>/dev/null)"
  [ -n "$eff" ] && printf '[%s]' "$eff"
}

# If run directly: print the prefix for the given/std-in task.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  if [ $# -gt 0 ]; then effort_prefix "$@"; else effort_prefix "$(cat)"; fi
  echo
fi
