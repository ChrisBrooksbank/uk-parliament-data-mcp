#!/usr/bin/env bash
# The session recorded by scripts/record-lords-demo.sh.
# Types each command out, then runs it for real against the live Parliament APIs.
# Needs `parliament`, curl and pdftotext (poppler-utils) on PATH.
type_cmd() {
  printf '\033[1;32m$\033[0m '
  local s="$1"
  for ((i=0; i<${#s}; i++)); do printf '%s' "${s:$i:1}"; sleep 0.03; done
  sleep 0.6; printf '\n'
}
comment() { printf '\033[2;3m# %s\033[0m\n' "$1"; sleep 1.5; }
# run <shown command> <pause>
run() {
  type_cmd "$1"
  eval "$1" 2>/dev/null
  sleep "$2"; printf '\n'
}

paper=/tmp/lords-order-paper.pdf
trap 'rm -f "$paper"' EXIT
base=https://services.lordsbusiness.parliament.uk/api/v1/DocumentForDay

clear
comment "What is on the Lords order paper on 15 January 2025?"
run 'parliament lords-business documents 2025-01-15 --format table' 4
comment "The order paper is a PDF (DocumentForDayId 5947). The CLI describes it..."
run 'parliament lords-business document 5947 --fields "contentType,sizeBytes" --format table' 3
comment "...and the file itself is one download away."
run "curl -s -o $paper $base/5947 && file -b $paper" 3
comment "...and read the oral questions."
run "pdftotext -layout $paper - | sed -n '/^Oral questions/,/^Data (Use/p' | head -n -1" 6
comment "Which bills and regulations are named?"
run "pdftotext -layout $paper - | sed -n '/^Data (Use/,\$p' | grep -oE '^[A-Z][A-Za-z() -]*(Bill( \[HL\])?\)?|Regulations 20[0-9]{2})'" 6
