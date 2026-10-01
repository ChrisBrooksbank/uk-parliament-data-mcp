#!/usr/bin/env bash
# Re-record docs/media/mcp-demo.gif: a real Claude Code session using this MCP server.
#
# Requires: asciinema (pip install asciinema), agg
# (cargo install --git https://github.com/asciinema/agg), an authenticated
# `claude` CLI, and this package installed (pip install -e .).
#
# The answer differs between runs. Record a few takes and keep the best one,
# but don't edit a take.
#
#   scripts/record-mcp-demo.sh ["question"]
set -euo pipefail

cd "$(dirname "$0")/.."
question="${1:-Who is the MP for SW1A 1AA, and how did they vote on the assisted dying bill in September? Keep it brief and list the Parliament API URLs you used.}"
cast="$(mktemp --suffix=.cast)"
trap 'rm -f "$cast"' EXIT

asciinema rec -q --overwrite --cols 112 --rows 34 \
  -c "python scripts/mcp-demo-session.py $(printf '%q' "$question")" "$cast"
agg --theme monokai --font-size 16 --idle-time-limit 4 --last-frame-duration 8 \
  "$cast" docs/media/mcp-demo.gif
echo "Wrote docs/media/mcp-demo.gif"
