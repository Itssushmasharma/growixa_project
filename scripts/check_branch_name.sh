#!/usr/bin/env bash
# ==============================================================================
# Growixa Branch Name & Main Commit Validator (Pre-Commit Hook)
# 1. Blocks direct commits to 'main'
# 2. Enforces branch naming convention: <type>/<SCOPE>/<task-id-or-name>
# ==============================================================================

set -e

current_branch=$(git branch --show-current 2>/dev/null || git symbolic-ref --short HEAD 2>/dev/null || echo "")

# If in detached HEAD state (e.g. during rebase, bisect, or CI detached checkout), skip check
if [ -z "$current_branch" ]; then
  exit 0
fi

# 1. Block commits directly to main
if [ "$current_branch" = "main" ]; then
  echo ""
  echo "======================================================================"
  echo "❌ COMMIT BLOCKED: Direct commit to 'main' is strictly forbidden."
  echo "======================================================================"
  echo "👉 You must work in a feature branch and merge via Pull Request."
  echo "   Run:"
  echo "   git checkout -b feature/BACKEND/<task-id>"
  echo "   (or feature/FRONTEND/<task-id>)"
  echo "======================================================================"
  echo ""
  exit 1
fi

# 2. Enforce branch naming standard
VALID_BRANCH_PATTERN="^(feature|fix|chore|infra|refactor|hotfix|docs|test)/(BACKEND|FRONTEND|INFRA|CORE|SHARED|DEVOPS)/[A-Za-z0-9._-]+$"

if [[ ! "$current_branch" =~ $VALID_BRANCH_PATTERN ]]; then
  echo ""
  echo "======================================================================"
  echo "❌ COMMIT BLOCKED: Invalid branch name '$current_branch'"
  echo "======================================================================"
  echo "👉 Current branch does not adhere to Growixa naming standards."
  echo ""
  echo "Allowed Format:"
  echo "  <type>/<SCOPE>/<task-id-or-name>"
  echo ""
  echo "Examples:"
  echo "  - feature/BACKEND/GRX-AUTH-005"
  echo "  - feature/FRONTEND/GRX-COMPANY-002"
  echo "  - fix/BACKEND/GRX-BUG-012"
  echo "  - infra/INFRA/OVH-DEPLOY-001"
  echo ""
  echo "Valid Types : feature, fix, chore, infra, refactor, hotfix, docs, test"
  echo "Valid Scopes: BACKEND, FRONTEND, INFRA, CORE, SHARED, DEVOPS"
  echo ""
  echo "👉 Rename your branch with:"
  echo "   git branch -m <valid-branch-name>"
  echo "======================================================================"
  echo ""
  exit 1
fi

exit 0
