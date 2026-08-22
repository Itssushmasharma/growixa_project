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
