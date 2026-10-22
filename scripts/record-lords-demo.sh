#!/usr/bin/env bash
# Re-record docs/media/lords-demo.gif from live Parliament data.
#
# Requires: asciinema (pip install asciinema), agg
# (cargo install --git https://github.com/asciinema/agg), poppler-utils (pdftotext)
# and the `parliament` CLI on PATH (pip install -e .).
#
#   scripts/record-lords-demo.sh
set -euo pipefail

cd "$(dirname "$0")/.."
cast="$(mktemp --suffix=.cast)"
trap 'rm -f "$cast"' EXIT

asciinema rec -q --overwrite --cols 112 --rows 44 -c "bash scripts/lords-demo-session.sh" "$cast"
agg --theme monokai --font-size 16 --idle-time-limit 6 --last-frame-duration 4 \
  "$cast" docs/media/lords-demo.gif
echo "Wrote docs/media/lords-demo.gif"
