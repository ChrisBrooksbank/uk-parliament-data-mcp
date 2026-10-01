#!/usr/bin/env bash
# The session recorded by scripts/record-cli-demo.sh.
# Types each command out, then runs it for real against the live Parliament APIs.
type_cmd() {
  printf '\033[1;32m$\033[0m '
  local s="$1"
  for ((i=0; i<${#s}; i++)); do printf '%s' "${s:$i:1}"; sleep 0.03; done
  sleep 0.6; printf '\n'
}
comment() { printf '\033[2;3m# %s\033[0m\n' "$1"; sleep 1.5; }
# run <shown command> <pause> [stderr: keep|hide]
run() {
  type_cmd "$1"
  if [ "${3:-hide}" = keep ]; then eval "$1"; else eval "$1" 2>/dev/null; fi
  sleep "$2"; printf '\n'
}

clear
comment "How did the Commons vote on the assisted dying bill?"
run 'parliament votes search "Terminally Ill" --house 1 --take 4 --fields "DivisionId,Title,AyeCount,NoCount"' 4
comment "Who is my MP, and how have they voted? (combines 5 API calls)"
run 'parliament my-mp "SW1A 1AA"' 6 keep
comment "Find a member"
run 'parliament members search "Starmer" --take 3 --fields "id,nameDisplayAs,latestHouseMembership.membershipFrom"' 5
