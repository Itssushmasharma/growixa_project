# PR Handoff — feature/BACKEND/GRX-AUTO-REASSIGN-SENDER-IDENTITIES

## Summary

Automatically reassigns existing Sender Identities in an account to the newly created/updated active Email Provider Connection (`POST /integrations/email-provider`).

**Root cause fixed**: Previously, when a user configured or updated Custom SMTP in the UI, the API created a new `email_provider_connections` row and deactivated the old one, but left existing `sender_identities` pointing to the old (deactivated/placeholder) connection ID. This caused campaign sends and test sends to fail with errors like `Error connecting to smtp.iitdeveloper.com on port 587` even after the UI connection test succeeded.

**Changes**:
1. Added `reassign_sender_identities_for_account()` in `growixa_api.integrations.repositories`.
2. Updated `create_connection()` in `growixa_api.integrations.services` to automatically reassign all existing sender identities for that account/provider to the new connection.
3. Added automated integration test `test_create_connection_reassigns_existing_sender_identities` in `apps/api/tests/integrations/test_integrations.py`.

## Branch

`feature/BACKEND/GRX-AUTO-REASSIGN-SENDER-IDENTITIES`

## Files Changed

- `apps/api/src/growixa_api/integrations/repositories.py`
- `apps/api/src/growixa_api/integrations/services.py`
- `apps/api/tests/integrations/test_integrations.py`

## Risk Level

**LOW** — Purely database FK reassignment during connection creation; preserves all credentials safely without schema changes.

## Commit

`cd83f3f`

## Review Verdict

- **Reviewed Code Commit**: `cd83f3f`
- **Verdict**: `APPROVED`
- **Reviewer**: Google Antigravity (Independent Reviewer)
- **Secrets Inspection**: Clean. No secrets, keys, or credentials leaked.
- **Tests**: `apps/api/tests/integrations/test_integrations.py` passes 10/10 tests including new `test_create_connection_reassigns_existing_sender_identities`.

## Status

- [x] Reviewed Code Commit: cd83f3f
- [x] Approved
- [ ] Merged
