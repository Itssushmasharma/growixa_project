# Agent Workspace Rules & Execution Guidelines

This file defines project-specific rules for all AI agents working in this repository.

## 1. Git Branch Workflow
Before starting development on any new feature or task:
1. **Pull Latest Main**: Switch to `main` and pull latest changes:
   ```bash
   git checkout main && git pull origin main
   ```
2. **Checkout Feature Branch**: Create a dedicated branch adhering strictly to the naming convention:
   - Backend features: `feature/BACKEND/<task-id-or-feature-name>` (e.g. `feature/BACKEND/GRX-AUTH-005`)
   - Frontend features: `feature/FRONTEND/<task-id-or-feature-name>` (e.g. `feature/FRONTEND/GRX-COMPANY-002`)

## 2. Commit Message & Co-Author Attribution
1. **Format**: Follow Conventional Commits: `<type>(<scope>): <summary>`.
2. **Co-Author Trailer**: Dynamically query `git config user.name` and `git config user.email` (or terminal user info) and append a `Co-Authored-By:` trailer to every commit message body:
   ```text
   Co-Authored-By: <User Name> <<User Email>>
   ```

## 3. Project Documentation Reference
- Follow all standards in [`docs/12-development/AGENT_EXECUTION_RULES.md`](file:///Users/ravi/Documents/projects/growixa/docs/12-development/AGENT_EXECUTION_RULES.md).
- Keep `docs/00-project-control/PROJECT_STATUS.md` and `MASTER_TASK_TRACKER.md` updated as tasks progress.
