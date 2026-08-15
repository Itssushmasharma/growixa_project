#!/usr/bin/env bash
# .agents/scripts/pre_tool_guard.sh
#
# PreToolUse hook — prevents the agent from running expensive/destructive
# commands (pytest, alembic upgrade, npm install, docker build) more than
# once per session unless the code has actually changed.
#
# Input:  JSON on stdin  { "toolCall": { "name": "...", "args": { "CommandLine": "..." } }, "conversationId": "..." }
# Output: JSON on stdout { "decision": "allow|deny|ask", "reason": "..." }

set -euo pipefail

INPUT=$(cat)

# Extract fields
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('toolCall',{}).get('name',''))" 2>/dev/null || echo "")
CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('toolCall',{}).get('args',{}).get('CommandLine',''))" 2>/dev/null || echo "")
CONV_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('conversationId','unknown'))" 2>/dev/null || echo "unknown")

# Only guard run_command tool
if [ "$TOOL_NAME" != "run_command" ]; then
  echo '{"decision":"allow"}'
  exit 0
fi

# Session state file — tracks what commands ran this conversation
STATE_DIR="/tmp/growixa_agent_hooks"
mkdir -p "$STATE_DIR"
STATE_FILE="$STATE_DIR/${CONV_ID}.json"

# Initialize state file if not exists
if [ ! -f "$STATE_FILE" ]; then
  echo '{}' > "$STATE_FILE"
fi

# ─── Patterns to guard against repeating ─────────────────────────────────────

# 1. pytest / test runs — only allow once unless files changed
if echo "$CMD" | grep -qE "pytest|python -m pytest"; then
  KEY="pytest_ran"
  ALREADY=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d.get('$KEY',''))" 2>/dev/null || echo "")
  if [ -n "$ALREADY" ]; then
    echo "{\"decision\":\"ask\",\"reason\":\"Tests were already run this session (at step $ALREADY). Run again only if code changed since then.\"}"
    exit 0
  fi
  # Record that pytest ran at this step
  STEP=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stepIdx','?'))" 2>/dev/null || echo "?")
  python3 -c "
import json
with open('$STATE_FILE') as f: d=json.load(f)
d['$KEY']='$STEP'
with open('$STATE_FILE','w') as f: json.dump(d,f)
" 2>/dev/null || true
  echo '{"decision":"allow"}'
  exit 0
fi

# 2. alembic upgrade head — only allow once per session
if echo "$CMD" | grep -qE "alembic upgrade"; then
  KEY="alembic_upgrade_ran"
  ALREADY=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d.get('$KEY',''))" 2>/dev/null || echo "")
  if [ -n "$ALREADY" ]; then
    echo "{\"decision\":\"deny\",\"reason\":\"alembic upgrade already ran this session (step $ALREADY). Migrations are idempotent — no need to re-run unless a new migration file was added.\"}"
    exit 0
  fi
  STEP=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stepIdx','?'))" 2>/dev/null || echo "?")
  python3 -c "
import json
with open('$STATE_FILE') as f: d=json.load(f)
d['$KEY']='$STEP'
with open('$STATE_FILE','w') as f: json.dump(d,f)
" 2>/dev/null || true
  echo '{"decision":"allow"}'
  exit 0
fi

# 3. docker build — ask before repeating
if echo "$CMD" | grep -qE "docker build|docker compose build"; then
  KEY="docker_build_ran"
  ALREADY=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d.get('$KEY',''))" 2>/dev/null || echo "")
  if [ -n "$ALREADY" ]; then
    echo "{\"decision\":\"ask\",\"reason\":\"Docker build already ran this session (step $ALREADY). Are you sure you want to rebuild? This takes time.\"}"
    exit 0
  fi
  STEP=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stepIdx','?'))" 2>/dev/null || echo "?")
  python3 -c "
import json
with open('$STATE_FILE') as f: d=json.load(f)
d['$KEY']='$STEP'
with open('$STATE_FILE','w') as f: json.dump(d,f)
" 2>/dev/null || true
  echo '{"decision":"allow"}'
  exit 0
fi

# 4. npm install — deny repeat runs (lockfile-driven, no reason to repeat)
if echo "$CMD" | grep -qE "npm install|npm ci"; then
  KEY="npm_install_ran"
  ALREADY=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d.get('$KEY',''))" 2>/dev/null || echo "")
  if [ -n "$ALREADY" ]; then
    echo "{\"decision\":\"deny\",\"reason\":\"npm install already ran this session (step $ALREADY). Skip unless package.json changed.\"}"
    exit 0
  fi
  STEP=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stepIdx','?'))" 2>/dev/null || echo "?")
  python3 -c "
import json
with open('$STATE_FILE') as f: d=json.load(f)
d['$KEY']='$STEP'
with open('$STATE_FILE','w') as f: json.dump(d,f)
" 2>/dev/null || true
  echo '{"decision":"allow"}'
  exit 0
fi

# Default: allow everything else
echo '{"decision":"allow"}'
