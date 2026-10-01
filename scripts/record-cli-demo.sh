#!/usr/bin/env bash
# Re-record docs/media/cli-demo.gif from live Parliament data.
#
# Requires: asciinema (pip install asciinema) and agg
# (cargo install --git https://github.com/asciinema/agg), plus the
# `parliament` CLI on PATH (pip install -e .).
#
#   scripts/record-cli-demo.sh
set -euo pipefail

cd "$(dirname "$0")/.."
cast="$(mktemp --suffix=.cast)"
trap 'rm -f "$cast"' EXIT

asciinema rec -q --overwrite --cols 112 --rows 44 -c "bash scripts/cli-demo-session.sh" "$cast"
agg --theme monokai --font-size 16 --idle-time-limit 6 --last-frame-duration 4 \
  "$cast" docs/media/cli-demo.gif
echo "Wrote docs/media/cli-demo.gif"
