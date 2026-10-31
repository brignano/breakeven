#!/usr/bin/env bash
# Fleet hook: copy to .claude/hooks/session-start.sh in every fleet repo.
# Loads the fleet standard and global context (brignano/ai-tools) into cloud
# sessions. A repo with its own setup (installing deps, etc.) adds that above
# the fleet block. Never fails the session.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 0

# --- repo-specific setup goes here ---

# --- fleet standard (keep as is) ---
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  if [ -x "$HOME/.ai-tools/fleet/session-start.sh" ]; then
    "$HOME/.ai-tools/fleet/session-start.sh"
  else
    git clone -q --depth 1 https://github.com/brignano/ai-tools "$HOME/.ai-tools" 2>/dev/null \
      && bash "$HOME/.ai-tools/fleet/session-start.sh"
  fi
fi
exit 0
