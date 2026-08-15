#!/usr/bin/env bash
# .agents/scripts/stop_guard.sh
#
# Stop hook — fires when the agent is about to stop.
# Checks if the agent updated MASTER_TASK_TRACKER.md and PROJECT_STATUS.md
# during this session (if it was doing feature work). Injects a reminder
# if it didn't.
#
# Input:  JSON on stdin  { "conversationId": "...", "terminationReason": "...", "transcriptPath": "..." }
# Output: JSON on stdout { "decision": "continue|stop", "reason": "..." }

set -euo pipefail

INPUT=$(cat)

TERMINATION=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('terminationReason',''))" 2>/dev/null || echo "")
CONV_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('conversationId','unknown'))" 2>/dev/null || echo "unknown")
TRANSCRIPT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('transcriptPath',''))" 2>/dev/null || echo "")

# Only check on normal model stop (not errors or max steps)
if [ "$TERMINATION" != "model_stop" ]; then
  echo '{"decision":""}'
  exit 0
fi

# Check session state — did this session make code changes?
STATE_FILE="/tmp/growixa_agent_hooks/${CONV_ID}.json"
if [ ! -f "$STATE_FILE" ]; then
  echo '{"decision":""}'
  exit 0
fi

# If the agent ran pytest or made code changes (wrote files), check tracker update
CODE_CHANGED=$(python3 -c "
import json
try:
  with open('$STATE_FILE') as f: d=json.load(f)
  keys = ['pytest_ran', 'alembic_upgrade_ran', 'docker_build_ran']
  print('yes' if any(d.get(k) for k in keys) else 'no')
except: print('no')
" 2>/dev/null || echo "no")

if [ "$CODE_CHANGED" != "yes" ]; then
  echo '{"decision":""}'
  exit 0
fi

# Check if MASTER_TASK_TRACKER.md was touched during this session by scanning transcript
TRACKER_UPDATED="no"
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  if grep -q "MASTER_TASK_TRACKER" "$TRANSCRIPT" 2>/dev/null; then
    # Check if it was actually written (not just read)
    if grep -q "write_to_file\|replace_file_content\|multi_replace_file_content" "$TRANSCRIPT" 2>/dev/null; then
      if grep -q "MASTER_TASK_TRACKER\|PROJECT_STATUS" "$TRANSCRIPT" 2>/dev/null; then
        TRACKER_UPDATED="yes"
      fi
    fi
  fi
fi

if [ "$TRACKER_UPDATED" = "no" ]; then
  echo '{
    "decision": "continue",
    "reason": "⚠️ REMINDER: You made code changes this session but did not update docs/00-project-control/MASTER_TASK_TRACKER.md and/or PROJECT_STATUS.md. Per AGENTS.md rule #3, these must be kept updated as tasks progress. Please update the task status to DONE (or current state) before finishing."
  }'
  exit 0
fi

echo '{"decision":""}'
