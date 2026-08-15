Task: GRX-SAAS-009
Developer: Claude Code
Reviewer:
Branch: feature/BACKEND/GRX-SAAS-009
Worktree: .worktrees/grx-saas-009-monitoring
Base Commit: 617bfc0
Latest Commit: 5748993
Status: READY_FOR_REVIEW

## What Changed
- **Infra monitoring**: `GET /platform/monitoring/queues` — real RabbitMQ queue depths
  for `grx.campaigns.dispatch`/`grx.social.dispatch` plus their full retry.0/1/2 ladder
  (matches worker's `MAX_DISPATCH_ATTEMPTS=3`) and DLQ. `health.py`'s
  `get_queue_depths()` uses a passive AMQP declare with a fresh channel per queue (a
  failed passive declare invalidates the whole channel, so reusing one across queues
  would break every check after the first missing queue). Not on the public `/health`
  check — platform-admin-gated only.
- **Financial dashboard**: `GET /platform/monitoring/financials` — MRR/ARR per
  currency, active subscription count, 30-day churn rate. Reuses the platform overview
  page's existing `get_mrr_totals()` (ACTIVE-only) rather than a second definition —
  see "Real mid-build correction" below.
- New `platform.monitoring.manage` permission (migration `039f01bed830`), granted to
  `platform.owner`/`admin`/`operations`/`finance`.
- New frontend pages `/platform/monitoring` and `/platform/finance`, sidebar entries
  gated on the new permission. Finance page reuses the existing shared `MetricCard`
  component and the same `formatMoney` pattern as the platform overview page.

## Why
`MASTER_TASK_TRACKER.md`'s `GRX-SAAS-009` (fully unblocked, no open product questions,
picked as the next task after triaging `need_review_docs/` and the tracker backlog).
Closes a real gap confirmed via this project's own prior live debugging: no endpoint
exposed RabbitMQ queue depth, requiring raw `rabbitmqctl` calls.

## Important Files
- `apps/api/src/growixa_api/health.py` — `get_queue_depths()`,
  `_monitored_queue_names()`
- `apps/api/src/growixa_api/platform_admin/repositories.py` —
  `count_active_subscriptions`, `count_subscriptions_canceled_since`
- `apps/api/src/growixa_api/platform_admin/services.py` — `get_financial_metrics`,
  `FinancialMetrics`
- `apps/api/src/growixa_api/platform_admin/api.py` — `monitoring_router`,
  `_require_monitoring_manage`
- `apps/api/migrations/versions/039f01bed830_platform_monitoring_manage_permission.py`
- `apps/api/tests/test_platform_admin_monitoring.py`
- `apps/web/src/app/(platform)/platform/(protected)/monitoring/` (new)
- `apps/web/src/app/(platform)/platform/(protected)/finance/` (new)
- `apps/web/src/app/(platform)/platform/(protected)/sidebar.tsx` (extended)

## Tests
- Commands: `ruff check`, `ruff format --check`, `mypy` (all new/changed backend
  files); `pytest tests/test_platform_admin_monitoring.py tests/test_platform_admin_dashboard.py`
  run against the real Postgres/Redis/RabbitMQ stack via a throwaway container on the
  compose network (`growixa_growixa-net`) — not mocked.
- Result: 8/8 passed (5 new + 3 existing dashboard tests, run together to confirm the
  `get_mrr_totals` reuse didn't break the existing dashboard). `ruff`/`mypy` clean
  (only pre-existing, unrelated errors remain — same set present on unmodified `main`).
- Migration: upgrade/downgrade/re-upgrade verified against the real dev DB;
  `alembic check` clean.
- Frontend: `eslint`, `tsc --noEmit`, `prettier --check`, `vitest run` (223 passed, up
  from 217) all clean; `next build` compiles both new routes with no conflicts.
- Full-suite regression check: ran the entire backend suite against unmodified `main`
  as a control (same environment) — identical pre-existing failure pattern in both (27
  failed on `main`, 26 failed on this branch before the frontend commit) — confirmed
  via diff that this is shared-dev-Postgres test pollution from repeated non-isolated
  runs (same class of issue as the already-documented scheduler-ticker clock-drift
  problem), not a regression introduced here. `test_campaign_scheduler_ticker.py`/
  `test_social_scheduler_ticker.py` deselected per that existing precedent.

## Known Issues / Evidence Gaps
Top-up/credit-pack revenue is deliberately NOT included in the financial dashboard:
`account_credit_purchases` records `credits_added` but not the amount paid or
currency, and has no FK back to which `credit_pack`/price was purchased — computing a
dollar figure would mean guessing at a mapping the schema doesn't capture. Documented
in `get_financial_metrics`'s docstring as a real data-model gap needing its own schema
decision (e.g. a `credit_pack_id`/`amount_paid`/`currency` column), not approximated.

## Review Findings


## Review Decision


## Reviewed Code Commit


## Review Record Commit


## Human Approval
Required (new UI: `/platform/monitoring`, `/platform/finance`)

Status:
