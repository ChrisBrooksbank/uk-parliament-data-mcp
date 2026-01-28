#!/bin/bash
# Ralph Wiggum Loop - UK Parliament MCP Migration
# Usage:
#   ./loop.sh          # Build mode, unlimited iterations
#   ./loop.sh plan     # Planning mode
#   ./loop.sh 20       # Build mode, max 20 iterations
#   ./loop.sh plan 5   # Planning mode, max 5 iterations

MODE="build"
MAX=0

# Parse arguments
for arg in "$@"; do
    if [[ "$arg" == "plan" ]]; then
        MODE="plan"
    elif [[ "$arg" =~ ^[0-9]+$ ]]; then
        MAX=$arg
    fi
done

# Select prompt file
if [[ "$MODE" == "plan" ]]; then
    PROMPT="PROMPT_plan.md"
else
    PROMPT="PROMPT_build.md"
fi

echo "=== Ralph Wiggum Loop ==="
echo "Mode: $MODE"
echo "Prompt: $PROMPT"
echo "Max iterations: $([ $MAX -gt 0 ] && echo $MAX || echo 'unlimited')"
echo "========================="
echo ""

count=0
while :; do
    ((count++))
    echo "--- Iteration $count ---"

    cat "$PROMPT" | claude --dangerously-skip-permissions

    if [[ $MAX -gt 0 && $count -ge $MAX ]]; then
        echo ""
        echo "=== Max iterations ($MAX) reached ==="
        break
    fi

    echo ""
    echo "--- Iteration $count complete. Starting next... ---"
    echo ""
done

echo "=== Loop finished after $count iterations ==="
