Task: GRX-SAAS-009
Developer: Claude Code
Reviewer: Claude Code (fresh session — same tool as developer, no other tool available;
the explicitly-documented weaker fallback per AGENT_EXECUTION_RULES.md §Who reviews. This
session did not write any of this branch and verified everything against the real diff,
the real database, and re-run tests.)
Branch: feature/BACKEND/GRX-SAAS-009
Worktree: .worktrees/grx-saas-009-monitoring
Base Commit: 617bfc0
Latest Commit: c364db7
Status: APPROVED — pending human sign-off (new platform UI)

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

Verified against the actual branch, the real dev database, and independently re-run
tests — not against this file's claims. Risk treated as HIGH (new permission, migration,
money figures on a privileged control plane).

**Claims that check out.** The migration is parameterized (no string interpolation), uses
a fixed UUID, deletes `platform_role_permissions` before `platform_permissions` on
downgrade (correct FK order), and sits on a linear chain — I confirmed only one migration
revises `fa291f6b37ca`, so no second alembic head. The dev DB is already at
`039f01bed830`. All four granted roles exist in `PLATFORM_ROLES`, and `platform.support`
is correctly *not* granted and has an explicit 403 test. Both routes are gated by
`require_platform_permission`, so `test_protected_routes_audit.py` covers them
automatically with no allowlist edit. The backend test claim is exact — I re-ran
`test_platform_admin_monitoring.py` + `test_platform_admin_dashboard.py` against the real
compose stack: **8 passed**. Frontend re-run: **42 files / 223 tests passed**, `tsc` 0
errors, `eslint` 0 errors. The new pages contain no hardcoded metrics — both fetch real
endpoints. And excluding credit-pack revenue with a documented schema gap, rather than
approximating it, is exactly the right call.

**Resolution summary (commit `c08b5f9`):** findings 1, 2, and 4 fixed with code and
re-verified against the live DB (MRR INR: ₹1,499 → ₹0.00; active-paying: 37 → 1);
finding 3 fixed via honest documentation, not a silent workaround — the real fix needs
a schema decision, flagged below rather than guessed. Finding 5 needed no action
(informational, already tracked elsewhere). Details per finding:

1. **BLOCKER — `mrr_by_currency` / `arr_by_currency` are not per-currency.**
   `get_mrr_totals` sums `SubscriptionPlan.price_usd` **and** `price_inr` across *every*
   ACTIVE subscription with no filter on `AccountSubscription.currency` — so one USD
   customer contributes to the INR total too. Demonstrated read-only against the live dev
   DB:

   | | implementation | currency-filtered |
   |---|---|---|
   | MRR USD | $19.00 | $19.00 |
   | MRR INR | **₹1,499.00** | **₹0.00** |

   There are currently zero INR subscribers, yet the dashboard would report ₹1,499 MRR
   and — after this branch's `× 12` — **₹17,988 ARR** for a currency with no customers.
   The root cause is pre-existing (`get_mrr_totals`, `GRX-SAAS-014`) and reusing it for
   consistency was a defensible instinct, but this branch is what names the output
   `mrr_by_currency`, asserts a per-currency attribution the query does not perform, and
   annualizes it. Fix is small — filter each sum on `AccountSubscription.currency` — and
   it also corrects the platform overview page that shares the function.

   **RESOLVED**: `get_mrr_totals` now sums each currency conditionally on
   `AccountSubscription.currency`. Live-reconfirmed: MRR USD=$19.00, MRR INR=$0.00
   (was ₹1,499.00). `test_platform_admin_dashboard.py` (exercises the same shared
   function) re-run and still passes.

2. **HIGH — `active_subscription_count` counts free accounts.** Every account receives an
   `status="ACTIVE"` Free subscription at registration (`create_default_free_subscription`),
   so on the live DB this reads **37 active subscriptions, 36 of them Free** — one paying
   customer. Rendered on a *financial* dashboard beside MRR/ARR, "Active Subscriptions"
   will be read as paying customers. The docstring's rationale — that it "must match the
   MRR figure shown right next to it" — does not actually hold: MRR is price-weighted, so
   Free contributes 0, while this count is unweighted and Free contributes 1. They share a
   status filter, not a meaning. Either count paying subscriptions (`price_usd`/`price_inr`
   non-null and non-zero) or relabel the card so it cannot be mistaken for paid customers.

   **RESOLVED**: renamed to `active_paying_subscription_count` throughout (dataclass,
   Pydantic schema, route, frontend field + label "Active paying subscriptions") and
   the repository query now filters to a nonzero plan price in the subscription's own
   currency. Live-reconfirmed: 1 (was 37, 36 of them Free).

3. **MEDIUM — churn systematically under-counts, and the label overstates it.**
   `downgrade_expired_cancellations` sets `status = 'ACTIVE'` when a canceled
   subscription's paid period ends. So a subscription that churned 25 days ago but whose
   period ended 3 days ago is no longer `CANCELED` and silently drops out of
   `churned_last_30_days`. What the metric actually measures is "cancellations still
   inside their paid period", not "churned in the last 30 days" — the `updated_at` proxy
   is honestly documented, but this interaction with the downgrade ticker is not, and it
   biases the number in one direction. Compounding it, the denominator `active + churned`
   inherits finding 2's free accounts, so the published churn *rate* is diluted as well.

   **PARTIALLY RESOLVED, rest flagged not guessed**: the churn-rate denominator now
   correctly uses `active_paying_subscription_count` (finding 2's fix), so that half of
   the dilution is gone. The under-counting itself (the downgrade-ticker interaction) is
   NOT code-fixed — it needs a schema decision (a dedicated status-history table, or a
   `churned_at` column that survives the ticker). Instead, `get_financial_metrics`'s
   docstring now explicitly documents the exact mechanism and says plainly what the
   metric actually measures ("cancellations still inside their original paid period, not
   true 30-day churn") rather than leaving the caveat implicit. Not silently worked
   around — flagged for the product-owner decision noted below.

4. **MEDIUM — two tests do not test what their names assert.**
   - `test_financial_metrics_computes_mrr_arr_per_currency_not_summed_together` asserts
     `mrr_by_currency["USD"] >= starter.price_usd`. With `>=`, it passes *precisely when
     the currencies are summed together* — the bug in finding 1 is what its name forbids,
     and the test is green. Written as `==` it would fail today.
   - `test_financial_metrics_churn_counts_only_cancellations_in_the_last_30_days` asserts
     `churned_last_30_days >= 1`, then "proves" the 90-day row is excluded by re-querying
     that row and asserting its own `updated_at` is old — i.e. it asserts the fixture it
     just created, never that the metric excluded it.

   Both would pass against an implementation that ignored currency and window entirely.
   The `>=` style looks like an accommodation for the shared, non-isolated dev database
   the Tests section already flags; the fix is to assert on a delta (measure before,
   create, measure after) rather than to loosen the comparison.

   **RESOLVED**: both tests rewritten to measure `metrics_before`/`metrics` and assert
   the exact delta (`== pytest.approx(...)` for the currency test, `== 1`/`== 2` for the
   churn/count deltas) — robust against the shared, non-isolated dev DB, and would
   correctly fail if findings 1 or 3's bugs were reintroduced. Re-run: both pass.

5. **LOW — one overstated test claim.** "`prettier --check` ... clean" is true for this
   branch's own files but not repo-wide: `npm run format:check` still fails on 7 files,
   all inherited from the `GRX-AI-STUDIO-001` merge and being fixed separately on
   `feature/FRONTEND/GRX-LINT-FORMAT-CLEANUP`. Not this branch's defect — noted so the
   stronger claim isn't passed through, and so the merge order is clear: CI's frontend job
   stays red until that cleanup branch lands.

Security/isolation: no findings. Platform-admin routes are cross-account by design and
correctly sit behind `require_platform_permission`; no customer-facing route, no
`account_id` scoping regression, no secrets or vendor identifiers in the diff. The
queue-depth passive-declare-per-channel rationale is sound — a failed passive declare does
invalidate the channel, so a shared channel would break every check after the first
missing queue.

## Re-Review (after `c08b5f9` / `c364db7`)

Every claimed fix re-verified against the actual diff, the live database, and re-run
tests — not from the resolution notes above.

1. **Finding 1 (BLOCKER) — genuinely fixed.** `get_mrr_totals` now wraps each sum in a
   `case()` keyed on `AccountSubscription.currency`, so a plan's `price_usd` is only
   credited when the subscription actually bills in USD. NULL-priced Enterprise rows still
   fall through to 0 correctly (the `case` yields NULL, `SUM` skips it, the outer
   `coalesce` covers the all-NULL case). Re-measured on the live DB: **MRR USD $19.00,
   MRR INR ₹0.00** — down from the ₹1,499.00 (₹17,988 phantom ARR) the original reported.

2. **Finding 2 (HIGH) — genuinely fixed.** Renamed `active_paying_subscription_count` and
   propagated end to end: dataclass, `schemas.py`, route, `types.ts`, `finance-page.tsx`,
   and the test — the rendered label is now "Active paying subscriptions". The query joins
   the plan and requires a nonzero price *in the subscription's own currency*. Live:
   **1**, down from 37 (36 of which were the default Free rows).

3. **Finding 3 (MEDIUM) — resolved as far as it honestly can be.** The rate denominator
   now uses the paying count, removing the dilution half. The under-count itself is
   documented rather than silently patched: the docstring now names the downgrade-ticker
   mechanism and states plainly what the number measures ("cancellations still inside
   their original paid period, not true 30-day churn"). Correct call — the real fix needs
   a `churned_at` column or status-history table, which is a schema decision, not a
   review-cycle change. Left open for the product owner below.

4. **Finding 4 (MEDIUM) — genuinely fixed, and I checked the tests now actually bite.**
   Both are delta-based against a `metrics_before` snapshot. The currency test asserts the
   USD delta `== pytest.approx(starter.price_usd)`; under the pre-fix code that delta would
   have been $19 + $49 = $68, so it now fails on exactly the bug its name forbids — which
   was the whole complaint. The churn test asserts `delta == 1`, so the 90-day row must be
   excluded by the *metric*, not merely by re-reading its own fixture. The self-referential
   assertion block is gone.

5. **Finding 5 — no longer applicable.** It was informational, and current `main` is
   already prettier-clean, so it has resolved itself.

Independently re-run at `c364db7`. Backend, against the real compose stack: **8 passed**;
`ruff check` clean; `ruff format --check` 7 files already formatted; `mypy` no issues in 6
source files. Frontend: **42 files / 223 tests passed**, `tsc` 0 errors, `eslint` 0 errors.
Merges into current `main` with **0 conflicts**.

Two notes, neither blocking:

- **NEW (LOW) — Enterprise is now excluded from "Active paying subscriptions".** The
  filter is `case(... ) > 0`, and Enterprise carries NULL prices by design
  (DEC-GRX-030), so `NULL > 0` is NULL and those rows drop out. Zero impact today — I
  confirmed there are currently **0 active Enterprise subscriptions** — but once a
  contact-sales customer exists they will be invisible in a count labelled "paying". The
  metric is really *self-serve* paying subscriptions. Worth either renaming or counting
  Enterprise explicitly when the first one lands.
- **Small correction to the resolution note for finding 4.** It says the rewritten tests
  "would correctly fail if findings 1 or 3's bugs were reintroduced". True for finding 1;
  not for finding 3, whose under-count is deliberately not fixed, so no test can fail on
  it. The test does correctly verify the 30-day window, which is what it claims in its
  name.

`format:check` shows 7 failures in this worktree, but those are base-staleness — the
branch is cut from `617bfc0` and is 46 commits behind; current `main` is prettier-clean, so
they disappear on merge. Not a defect in this branch.

## Review Decision
APPROVED

## Reviewed Code Commit
c364db7

## Review Record Commit


## Human Approval
Required (new UI: `/platform/monitoring`, `/platform/finance`). Not yet eligible — pending
re-review. One open product question remains from the prior review, not resolved by this
fix cycle: should churn be measured from a real status-change history (a small schema
addition — a dedicated table, or a `churned_at` column that survives the downgrade
ticker) rather than the documented `updated_at`-proxy limitation? Deferred to the product
owner rather than guessed; current behavior is honestly documented, not silently wrong.

Status: APPROVED — pending human sign-off (new platform UI)
