# PR Handoff — feature/BACKEND/GRX-EMAIL-013

## Summary

Implements **`GRX-EMAIL-013`** per **`DEC-GRX-035`** (points 1, 2, 7, 8): Multi-SMTP backend schema, guarded delete, and narrowed reassignment.

**Key Deliverables**:
1. **Multi-SMTP Schema & Constraint Relaxation** (Points 1 & 2):
   - Migration `d1e2f3a4b5c6`: added `name` column (required text label) to `email_provider_connections`, defaulting existing rows to `smtp_host`.
   - Dropped old unique index `ux_email_provider_connections_active_per_provider`.
   - Created partial unique index `ux_email_provider_connections_active_postmark` on `(account_id, provider) WHERE (is_active AND provider = 'POSTMARK')` — preserving Postmark single-active rule while allowing multiple active `CUSTOM_SMTP` connections.
   - Created partial unique index `ux_email_provider_connections_active_account_name` on `(account_id, name) WHERE is_active` — ensuring connection names are account-unique among active connections.
   - Mirrored model updated in `apps/worker/src/growixa_worker/models.py`.
2. **Guarded Delete** (Point 7):
   - `DELETE /integrations/email-providers/{id}` (gated on `integrations.manage`): checks if any `sender_identities` reference the connection. If referenced, raises 409 Conflict with a clear message naming the blocking identities. If unreferenced, deletes/deactivates the connection.
3. **Narrowed Auto-Reassignment Regression Prevention** (Point 8):
   - `create_connection` in `growixa_api.integrations.services`: creating an additional `CUSTOM_SMTP` relay leaves existing connections and identities untouched. If `replacing_connection_id` is supplied, deactivates only that specific connection and reassigns *only* identities referencing that connection.
4. **Sender Identity Connection Update**:
   - `PATCH /integrations/sender-identities/{id}`: allows updating an identity's bound connection and metadata.
5. **Data Model Documentation**:
   - Updated `docs/05-data/DATA_MODEL.md` singleton-by-convention notes to document the multi-SMTP rules and constraints.

## Branch

`feature/BACKEND/GRX-EMAIL-013`

## Reviewed Code Commit

`3b06b30`

## Files Changed

- `apps/api/migrations/versions/d1e2f3a4b5c6_multi_smtp_connection_name_and_indexes.py`
- `apps/api/src/growixa_api/integrations/models.py`
- `apps/api/src/growixa_api/integrations/repositories.py`
- `apps/api/src/growixa_api/integrations/schemas.py`
- `apps/api/src/growixa_api/integrations/services.py`
- `apps/api/src/growixa_api/integrations/api.py`
- `apps/worker/src/growixa_worker/models.py`
- `apps/api/src/growixa_api/cli/onboard_iitdeveloper.py`
- `apps/api/src/growixa_api/cli/seed_demo_data.py`
- `docs/05-data/DATA_MODEL.md`
- `docs/00-project-control/MASTER_TASK_TRACKER.md`
- `apps/api/tests/integrations/test_integrations.py`
- `apps/api/tests/permissions/test_cross_tenant_isolation.py`
- `apps/api/tests/analytics/test_analytics.py`
- `apps/api/tests/campaigns/test_campaign_scheduler_ticker.py`
- `apps/api/tests/campaigns/test_campaigns.py`
- `apps/api/tests/dashboard/test_dashboard.py`
- `apps/api/tests/email_delivery/test_email_delivery.py`
- `apps/api/tests/platform_admin/test_platform_admin_usage.py`
- `apps/api/tests/templates/test_templates.py`
- `apps/worker/tests/dispatch/test_dispatch_consumer.py`
- `apps/worker/tests/email/test_send_campaign.py`

## Risk Level

**MEDIUM** — Schema migration modifying partial unique indexes on `email_provider_connections` and adding `name` column; guarded delete and narrowed reassignment logic.

## Re-Review Fixes Applied (Round 2)

1. **Blocker 1 Fixed**: `replacing_connection_id` validation now raises `EmailProviderConnectionNotFoundError` (404) if it refers to a non-existent, cross-account, or inactive connection. Added regression test `test_replacing_invalid_connection_id_returns_404`.
2. **Blocker 2 Fixed**: `delete_email_provider_connection` executes real SQL `DELETE` after the guard confirms zero references. `list_email_provider_connections` filters `is_active.is_(True)`. Added assertion proving deleted connection no longer appears in connection lists.
3. **Migration Hardening**: Backfill sets name to `Postmark` for Postmark rows and `smtp_host` for Custom SMTP, then automatically disambiguates any duplicate active names within an account before index creation.
4. **MissingGreenlet Comment**: Restored explanatory comment above `await session.refresh(identity)`.

## Validation Commands Run & Results

- `pytest apps/api/tests/integrations/test_integrations.py -v`: 10/10 passed
- `pytest apps/api/tests/permissions/test_protected_routes_audit.py -v`: 3/3 passed
- `pytest apps/api/tests/permissions/test_cross_tenant_isolation.py -v`: 23/23 passed
- `pytest apps/api/tests/`: 416/416 passed (including alembic upgrade/downgrade round-trip test)
- `pytest apps/worker/tests/`: 29/29 passed
- `ruff check .`: 0 errors
- `ruff format --check .`: all files formatted
- `mypy src` (api + worker): 0 issues in 198 files
- `npm run typecheck && npm run lint && npm run format:check && npm run test` (web): 51/51 test files passed (280/280 tests)

## Review Checklist

- [ ] Multiple active `CUSTOM_SMTP` connections can be created with distinct names on the same account.
- [ ] Only one active `POSTMARK` connection allowed per account (creating a second deactivates the prior one).
- [ ] Deleting a connection referenced by sender identities is refused with 409 Conflict naming the blocking identities.
- [ ] Deleting an unreferenced connection succeeds (204 No Content) and removes it from connection list.
- [ ] Supplying an invalid or inactive `replacing_connection_id` returns 404 Not Found.
- [ ] Narrowed reassignment: replacing connection A does not repoint identities referencing connection B.
- [ ] Worker `models.py` mirrors the `name` column.
- [ ] No hardcoded secrets in diff.

## Status

**READY_FOR_REVIEW**

---

### Review Verdict (to be filled by independent reviewer)

- **Reviewer**: _pending_
- **Review Decision**: _pending_
- **Reviewed Code Commit**: `5448511`
- **Notes**: _pending_

---

## Independent Review

Reviewer: Claude Code (did not author this branch)
Review Date: 2026-08-22
Reviewed Code Commit: `5448511`
Risk: **HIGH** — schema migration on a tenant table, plus the delete path for credentials
that live sends depend on.

Reviewed in an isolated worktree rather than the shared root workspace, because the root
workspace currently carries another agent's uncommitted work and contaminates whole-repo
gate runs.

### What is right, and it is most of it

**Account isolation holds.** Every new repository function filters on `account_id` —
`list_sender_identities_referencing_connection`, `deactivate_email_provider_connection`,
`delete_email_provider_connection`, and `update_sender_identity` (via `get_sender_identity`).
No new query can reach another tenant's row.

**The worker's duplicate model was updated.** `apps/worker/src/growixa_worker/models.py`
gains the `name` column. This is the repo's most-repeated trap — the worker resolves data
through its own models — and it was handled without being prompted.

**The migration's NOT NULL backfill is safe.** `name` is backfilled from `smtp_host` before
`alter_column(nullable=False)`, and `smtp_host` is itself `NOT NULL`, so the backfill cannot
leave a NULL behind and the constraint cannot fail on existing data.

**Test coverage is genuinely strong** — eight tests covering single-active POSTMARK,
multiple CUSTOM_SMTP with distinct names, the guarded delete, a named *regression* test for
the narrowed reassignment, the PATCH endpoint, account isolation, and permission gating.
The regression test for the reassignment narrowing is the right instinct: that is the exact
behaviour GRX-AUTO-REASSIGN-SENDER-IDENTITIES shipped and this branch deliberately changes.

**Scope discipline.** SPF alignment (`DEC-GRX-035` point 4) is correctly left to
`GRX-EMAIL-014` rather than smuggled in here.

Static gates re-run independently in the clean worktree: `ruff check` **All checks
passed**, `ruff format --check` **294 files already formatted**, `mypy` **Success, 292
source files**.

### Required change 1 — `replacing_connection_id` is silently ignored when it does not resolve

`services.py`, `create_connection`:

```python
if data.replacing_connection_id is not None:
    old_conn = await get_email_provider_connection(session, account_id, data.replacing_connection_id)
    if old_conn is not None and old_conn.is_active:
        ...deactivate + reassign...
```

If `replacing_connection_id` names a connection that does not exist, belongs to **another
account**, or is already inactive, both branches fall through silently and the request
still succeeds — creating a **new active connection without replacing anything**.

The caller explicitly asked to replace relay X. Before this branch that mistake was
invisible because CUSTOM_SMTP was capped at one active row. Now that point 1 permits
multiple active connections, the same mistake leaves the account with **two active relays
where the operator believes there is one**, and identities still bound to the old
credentials. That is precisely the "which relay actually sent this?" confusion
`DEC-GRX-035` point 6 exists to prevent.

`EmailProviderConnectionIn.replacing_connection_id` is a bare `uuid.UUID | None` with no
validation, so nothing upstream catches it either.

Raise `EmailProviderConnectionNotFoundError` → **404** when the id does not resolve to a
connection in this account. Decide explicitly what an already-inactive target means — 404
or a no-op — but do not leave it silent. A test asserting that a foreign account's
connection id returns 404 would also close a small isolation gap: today it is accepted
and ignored rather than rejected.

### Required change 2 — "delete" does not delete, and nothing says so

`repositories.delete_email_provider_connection` issues
`update(...).values(is_active=False)`. It does not delete. Meanwhile:

- the route is `@router.delete(...)` returning **204 No Content**
- the service function is `delete_connection`, its error is
  `ConnectionReferencedBySenderIdentitiesError("Cannot delete connection...")`
- `DEC-GRX-035` point 7 justifies the guard by saying an unguarded delete "either raises an
  FK violation or orphans identities" — a rationale that only applies to a real `DELETE`

Soft-deactivation is a reasonable choice here and consistent with this module's
existing "deactivate, never overwrite, keep credential history" convention. **The problem
is that nothing in the code says that is what is happening**, and one consequence is
user-visible: `list_email_provider_connections` does **not** filter `is_active`, so a
connection the user just "deleted" with a 204 keeps coming back from `GET
/integrations/email-providers`.

`EmailProviderConnectionOut` does expose `is_active`, so the frontend *can* filter — but
that is now an undocumented cross-task dependency on `GRX-EMAIL-015`, and if 015 does not
filter, users will see deleted relays with no way to remove them.

Either is acceptable; pick one and make it explicit:
1. keep soft-deactivation, rename the repository function to say so
   (`deactivate_email_provider_connection_permanently` or similar), document it in the
   route docstring, and record the `is_active` filtering requirement on `GRX-EMAIL-015`; or
2. filter `is_active` out of the list endpoint so the 204 matches what the user observes.

### Non-blocking findings

**F3 — migration index collision is possible, though narrow.** The backfill sets
`name = smtp_host` for every row, then creates a unique index on `(account_id, name) WHERE
is_active`. The old index capped actives at one *per provider*, so an account may hold one
active POSTMARK **and** one active CUSTOM_SMTP. If both carry the same `smtp_host` — a
customer whose CUSTOM_SMTP points at Postmark's relay, which this codebase notes is just
SMTP — the backfill produces duplicate names and index creation aborts the migration
mid-deploy. A dedupe in the backfill (append the provider or a row number on collision)
removes the risk for a few lines. Worth checking production for such a row before deploying.

**F4 — an explanatory comment was deleted without cause.** In
`update_identity_verification_status`, the comment explaining that `await
session.refresh(identity)` exists to avoid `MissingGreenlet` from `updated_at`'s
server-side `onupdate` is removed while the `refresh` call itself stays. That comment is
load-bearing knowledge; without it the next reader sees a redundant refresh and deletes it.
Restore it. Nothing else in the diff explains the constraint.

**F5 — the binding endpoint ships before its gate.** `PATCH
/integrations/sender-identities/{id}` lets an identity be bound to any connection in the
account with no SPF alignment check, which `DEC-GRX-035` point 4 requires before an
identity "may be bound to a connection". Scoping it to `GRX-EMAIL-014` is correct, but
between this merge and that one the product permits exactly what the decision says must be
gated. Either sequence 014 close behind, or note the interim gap on 014's row.

**F6 — `name` has no length or content validation.** `name: str` accepts `""`. The unique
index then permits exactly one empty-named active connection per account, which is a
confusing way to discover the problem. A `min_length=1` on the schema is one line.

### Evidence gap — stated rather than glossed

**I could not run the backend test suite.** Docker is not running on this machine, so the
test database is unreachable and `pytest` fails at connection, not at assertions. I also
could not execute the migration, so the `NOT NULL` backfill and both new partial indexes
are verified **by reading only** — and F3 above is exactly the kind of thing a real
`alembic upgrade head` against production-shaped data would surface. Given this branch
carries a schema migration on a tenant table, **someone with a working stack must run
`pytest tests/integrations` and an actual `alembic upgrade head` before this merges.** My
static analysis is not a substitute for that on a migration.

### Not findings

No secrets in the diff — `smtp_password` continues to be stored encrypted and the webhook
password keeps its return-once convention. The cross-tenant isolation test is not weakened;
it only gains the now-required `name` field. `scripts/tracker_to_csv.py` picks up a
cosmetic re-wrap and a 644→755 mode change (it has a shebang) — unrelated to this task but
harmless.

## Review Decision

**CHANGES_REQUESTED**

The design is right, the isolation is right, the tests are the best I have reviewed in this
repo, and the worker-model trap was handled unprompted. Two things block: a silent no-op on
an explicit replace request that can now leave an account with two active relays, and a
delete path whose name, HTTP verb, and status code all promise something the implementation
does not do while the list endpoint keeps returning the "deleted" row. Both are small and
local — this should come back quickly.

## Reviewed Code Commit

`5448511`

## Human Approval

**Required** before merge regardless of the re-review outcome — this carries a schema
migration on a tenant table and changes how customer sending credentials are replaced and
removed.

---

## Independent Review — Round 2

Reviewer: Claude Code (did not author this branch)
Review Date: 2026-08-22
Reviewed Code Commit: `3b06b30` (handoff updated in `bc0814e`)
Review Decision: **APPROVED**

Both blockers are resolved, and every claim below was checked against the diff rather than
the round-2 summary.

**Blocker 1 — `replacing_connection_id` now fails loudly.** The condition was inverted to
`if old_conn is None or not old_conn.is_active: raise EmailProviderConnectionNotFoundError`,
and `api.py` maps it to a **404** with a distinct message ("Email provider connection to
replace not found") so it is not confused with the identity 404 on the same router. Because
`get_email_provider_connection` is account-scoped, another account's id returns `None` and
therefore 404 — the small isolation gap I raised is closed by the same change.
`test_replacing_invalid_connection_id_returns_404` covers it.

**Blocker 2 — resolved by making the contract true rather than documenting the mismatch.**
`delete_email_provider_connection` now issues a real `delete()`, and
`list_email_provider_connections` filters `is_active`. So `DELETE` really deletes, `204`
means gone, and the list reflects it. That is the stronger of the two options I offered and
it removes the undocumented dependency on `GRX-EMAIL-015` filtering client-side.

I checked the blast radius of the list filter, since narrowing a shared query is where this
kind of fix usually breaks something else. There are exactly three callers and all are
correct under the new behaviour: the route (should show only live connections), `services.py:65`
`list_connections` (same), and `services.py:87`, which uses it to find the active POSTMARK
row to deactivate — actives are all it ever wanted, and its now-redundant `and c.is_active`
filter is harmless.

The hard delete is safe **because** of the guard: `sender_identities.email_provider_connection_id`
is `NOT NULL` with no `ondelete`, so the 409 is what stands between this and an FK violation.
`test_guarded_delete_email_provider_connection` pins the whole contract — 409 naming the
blocking identity, 204 for an unreferenced one, and an assertion that it is then absent from
the list.

**F3 — migration collision fixed properly.** The backfill now names POSTMARK rows
`'Postmark'` and CUSTOM_SMTP rows by `smtp_host`, then de-duplicates with a `ROW_NUMBER()
OVER (PARTITION BY account_id, name ORDER BY created_at)` pass appending ` (2)`, ` (3)` to
collisions among active rows before the unique index is created. The abort case I raised
cannot occur.

**F4 — the `MissingGreenlet` comment is restored**, now on the `session.refresh` in
`api.py` where the call actually lives.

Gates re-run independently at `3b06b30`, again in an isolated worktree: `ruff check` **All
checks passed** · `ruff format --check` **294 files already formatted** · `mypy`
**Success, 292 source files**. Ten tests in `test_integrations.py` covering single-active
POSTMARK, multiple named CUSTOM_SMTP, the guarded delete, the invalid-replacement 404, the
reassignment-narrowing regression, the PATCH endpoint, account isolation and permission
gating.

### Still open, deliberately

**F5 stands.** `DEC-GRX-035` is now `APPROVED` (product owner, 2026-08-17), and its new
point 9 makes multi-SMTP **ungated by plan tier** — that is a *pricing* decision and does
not touch point 4, which still requires an SPF alignment check before an identity may be
bound to a connection. `PATCH /integrations/sender-identities/{id}` ships here without that
check, so until `GRX-EMAIL-014` lands the product permits unaligned binding. Correctly
scoped out; worth sequencing 014 close behind rather than leaving the window open.

**F6 (`name` accepts `""`)** is unaddressed and remains cosmetic.

**Minor, non-blocking:** `docs/04-architecture/BILLING_SYSTEM_ARCHITECTURE.md` picks up a
reformat of its embedded Python examples — unrelated to multi-SMTP, harmless.

### The evidence gap has not changed, and it still matters most here

**I could not run `pytest` or `alembic upgrade head`** — Docker is unavailable on this
machine, so the test database is unreachable and the migration was verified by reading
only. That limitation is unchanged from round 1 and is more consequential than usual: this
branch alters a tenant table, and the round-2 fixes include **new SQL** (the `ROW_NUMBER()`
de-duplication) that has never been executed. Approving the code is not the same as
certifying the migration runs.

**Before merge, on a machine with the stack up:** `pytest tests/integrations` must pass, and
`alembic upgrade head` must be run against production-shaped data — ideally a restore of the
production database, since the de-duplication path only exercises on real duplicate names.
`scripts/deploy_vps.sh` now takes a pre-migration backup, which is the safety net if this
goes wrong on deploy.

## Round 2 Review Decision

**APPROVED**

## Round 2 Reviewed Code Commit

`3b06b30`

## Human Approval

**Required** — schema migration on a tenant table plus changes to how customer sending
credentials are replaced and permanently removed. Note the delete is now genuinely
destructive: a connection with no bound identities is erased, not deactivated, so its
credential history does not survive. That is consistent with `DEC-GRX-035` point 7 and is
guarded, but it is a product decision worth confirming explicitly rather than inheriting
from a code review.

---

## Product Owner Sign-off

- **Status: APPROVED** — signed off by Ravi Kant Yadav (product owner), 2026-08-22,
  following the round-2 independent approval at `3b06b30`.
- **Scope confirmed**, including the point the round-2 review asked to be decided
  explicitly rather than inherited: **deleting a connection is now genuinely destructive.**
  A connection with no bound sender identities is erased rather than deactivated, so its
  credential history does not survive. This matches `DEC-GRX-035` point 7 and is guarded by
  the 409 that blocks deletion while any identity still references it.
- `DEC-GRX-035` itself is `APPROVED` (product owner, 2026-08-17), including point 9 —
  multi-SMTP is ungated by plan tier at launch.

**Carried into merge, not resolved by this sign-off** — the round-2 evidence gap stands:
`pytest tests/integrations` and `alembic upgrade head` could not be run at review time
because Docker was unavailable, and the round-2 de-duplication SQL in the migration has
never been executed anywhere. Run both against production-shaped data before deploying.
`scripts/deploy_vps.sh` takes a pre-migration backup, which is the safety net if the
migration fails on deploy.

Status: APPROVED — cleared for merge
