# Code Review Handoff: feature/BACKEND/GRX-DEV-SEED-001

- **Branch**: `feature/BACKEND/GRX-DEV-SEED-001`
- **Worktree**: `.worktrees/grx-dev-seed`
- **Developer**: Google Antigravity
- **Date**: 2026-08-15
- **Base**: `main`

---

## 1. Summary of Changes (<= 10 lines)
1. **Development Seed CLI (`apps/api/src/growixa_api/cli/seed_demo_data.py`)**: Added dedicated command `python -m growixa_api.cli.seed_demo_data`.
2. **Resource Coverage**: Populates 20 realistic contacts with tags, 3 contact lists with memberships, 4 responsive email templates, 5 campaigns (DRAFT & SCHEDULED only — no live dispatch), and 5 social media posts.
3. **Safety & Isolation**: Never touches platform admins, billing rows, or RBAC tables. Safe to re-run (idempotent). Supports `SEED_FORCE=1` for full clean re-seed with proper reverse-FK cascading deletes.
4. **Live Verification**: Successfully verified live against running Compose stack with rich populated dashboards.

---

## 2. Changed Files
- `apps/api/src/growixa_api/cli/seed_demo_data.py` [NEW]

---

## 3. Test Commands & Evidence
- Command: `docker compose exec api python -m growixa_api.cli.seed_demo_data`
- Result:
  - Contacts: 20 created with 5 tags
  - Contact Lists: 3 created with memberships
  - Templates: 4 created
  - Campaigns: 5 created (DRAFT/SCHEDULED)
  - Social Posts: 5 created
  - Re-run without `SEED_FORCE=1`: Idempotent (skips existing without error)
  - Re-run with `SEED_FORCE=1`: Cleanly wipes and re-populates without FK violation

---

## 4. Review Focus Points (3-5 items)
1. **Idempotency & Re-entrancy**: Confirm re-running the command does not create duplicate entries or crash.
2. **Reverse FK Deletion Order**: In `SEED_FORCE=1` mode, confirm deletion order respects foreign key constraints.
3. **Sensitive Table Isolation**: Verify the script does not modify platform credentials, billing subscriptions, or RBAC tables.

---

## 5. Review Verdict

- **Reviewer**: Google Antigravity (fresh independent review session)
- **Verdict**: **CHANGES_REQUESTED**
- **Reviewed Code Commit**: `dd9e28c`
- **Comments**: See Review Findings below.

### Review Findings

Verified against the actual code diff in `.worktrees/grx-dev-seed` (`git diff main...feature/BACKEND/GRX-DEV-SEED-001`), not trusting claims in this file.

**Functional verification checks out:**
- Ran `docker compose exec api python -m growixa_api.cli.seed_demo_data` and verified clean population of 20 contacts, 5 tags, 3 contact lists with memberships, 4 email templates with versions, 5 campaigns (DRAFT/SCHEDULED only), and 5 social posts.
- Ran without `SEED_FORCE=1`: Idempotent execution correctly detects existing resources and skips them without errors.
- Ran with `SEED_FORCE=1`: Verified reverse-FK cascading deletion order succeeds cleanly without foreign key constraint violations.
- Security & table isolation: Confirmed the script operates exclusively on customer account entities and does not touch `platform_admins`, platform credentials, billing subscriptions, or RBAC permission tables.

**Blockers preventing merge (CI & quality gates):**

1. **BLOCKER (CI) — `mypy` fails with 7 typecheck errors.**
   `mypy src/growixa_api/cli/seed_demo_data.py` fails on `dd9e28c` with:
   - Line 267, 290, 327: `Invalid index type "Sequence[str]" for "dict[str, UUID]"` / `No overload variant of "get" of "dict" matches argument type "Sequence[str]"` (due to untyped dict inferred type).
   - Line 415, 417, 475, 477: Incompatible type assignment for `days_offset` object passed to `timedelta(days=...)`.
   Fix: Add proper typed dictionaries/dataclasses or explicit typing/casting for `CONTACTS`, `LISTS`, `TEMPLATES_DATA`, `CAMPAIGNS_DATA`, and `SOCIAL_POSTS_DATA`.

2. **BLOCKER (CI) — `ruff check` fails with 38 line-length (E501) errors.**
   `ruff check src/growixa_api/cli/seed_demo_data.py` reports 38 errors for lines exceeding 100 characters (e.g. long strings in data definitions and delete statements). `ci.yml` runs `ruff check .` as step 78 and will fail the build.

3. **BLOCKER (CI) — `ruff format --check` fails.**
   `ruff format --check src/growixa_api/cli/seed_demo_data.py` indicates formatting drift. `ci.yml` runs `ruff format --check .` as step 82.

4. **MEDIUM (Tests) — Missing automated unit / integration test.**
   No test file in `apps/api/tests/` exercises the CLI script or verifies its idempotency/deletion logic in the test suite.

---

## 6. Product Owner Sign-off

- **Status**: **Not Required** (Internal CLI / developer tooling — no customer-facing UI). Note: Branch must first resolve CI blockers above and be re-reviewed.

