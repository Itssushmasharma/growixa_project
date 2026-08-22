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

`5448511`

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

## Validation Commands Run & Results

- `pytest apps/api/tests/integrations/test_integrations.py -v`: 9/9 passed
- `pytest apps/api/tests/permissions/test_protected_routes_audit.py -v`: 3/3 passed
- `pytest apps/api/tests/permissions/test_cross_tenant_isolation.py -v`: 23/23 passed
- `pytest apps/worker/tests/`: 29/29 passed
- `ruff check .`: 0 errors
- `ruff format --check .`: all files formatted
- `mypy src` (api + worker): 0 issues in 198 files
- `npm run typecheck && npm run lint && npm run format:check && npm run test` (web): 51/51 test files passed (280/280 tests)

## Review Checklist

- [ ] Multiple active `CUSTOM_SMTP` connections can be created with distinct names on the same account.
- [ ] Only one active `POSTMARK` connection allowed per account (creating a second deactivates the prior one).
- [ ] Deleting a connection referenced by sender identities is refused with 409 Conflict naming the blocking identities.
- [ ] Deleting an unreferenced connection succeeds (204 No Content).
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
