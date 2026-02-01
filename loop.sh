#!/bin/bash
# Ralph Wiggum Loop - Fresh context per iteration
# Usage: ./loop.sh [plan|build] [max_iterations]
#
# Examples:
#   ./loop.sh plan      # Planning mode, unlimited
#   ./loop.sh plan 5    # Planning mode, max 5 iterations
#   ./loop.sh build     # Build mode, unlimited
#   ./loop.sh build 20  # Build mode, max 20 iterations

set -e

MODE="${1:-build}"
MAX_ITERATIONS="${2:-0}"
ITERATION=0

if [ "$MODE" = "plan" ]; then
  PROMPT_FILE="PROMPT_plan.md"
elif [ "$MODE" = "build" ]; then
  PROMPT_FILE="PROMPT_build.md"
else
  echo "Usage: ./loop.sh [plan|build] [max_iterations]"
  exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
  echo "Error: $PROMPT_FILE not found"
  exit 1
fi

echo "=========================================="
echo "Ralph Wiggum Loop - Improvements"
echo "Mode: $MODE"
echo "Prompt: $PROMPT_FILE"
[ $MAX_ITERATIONS -gt 0 ] && echo "Max iterations: $MAX_ITERATIONS"
echo "=========================================="

while true; do
  if [ $MAX_ITERATIONS -gt 0 ] && [ $ITERATION -ge $MAX_ITERATIONS ]; then
    echo ""
    echo "Reached max iterations ($MAX_ITERATIONS). Stopping."
    break
  fi

  ITERATION=$((ITERATION + 1))
  echo ""
  echo "=========================================="
  echo "Iteration $ITERATION (Mode: $MODE)"
  echo "$(date '+%Y-%m-%d %H:%M:%S')"
  echo "=========================================="

  # Fresh Claude session each iteration - context resets!
  cat "$PROMPT_FILE" | claude -p \
    --dangerously-skip-permissions \
    --model sonnet

  # Auto-commit progress after each iteration
  git add -A
  if ! git diff --staged --quiet; then
    git commit -m "Ralph iteration $ITERATION ($MODE mode)

Co-Authored-By: Claude <noreply@anthropic.com>"
    echo "Changes committed."
  else
    echo "No changes to commit."
  fi

  echo "Iteration $ITERATION complete."
  sleep 2
done

echo ""
echo "Ralph loop finished after $ITERATION iterations."
