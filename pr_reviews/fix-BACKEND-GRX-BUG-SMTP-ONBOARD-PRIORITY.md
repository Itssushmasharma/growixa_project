# PR Handoff — fix/BACKEND/GRX-BUG-SMTP-ONBOARD-PRIORITY

## Summary

Fixes a production bug where "Test send failed: Error connecting to
smtp.iitdeveloper.com on port 587" was shown even though the user had
already configured a real Custom SMTP connection (s61.gocheapweb.com:465)
via Settings > Integrations.

**Root cause**: The `onboard_iitdeveloper.py` CLI script seeded sender
identities linked to a placeholder `EmailProviderConnection`
(`smtp.iitdeveloper.com:587`). When the user later added a real SMTP
connection via the UI, the existing sender identities still pointed to
the old placeholder row — so every test-send and campaign-send used
the wrong host.

**Fix**: Added SMTP priority logic to `onboard_account()`:
- Loads all active connections for the account
- Prefers real user-configured connections (smtp_host != placeholder)
- Deactivates the placeholder if a real one exists
- Reassigns existing sender identities to the real connection

## Branch

`fix/BACKEND/GRX-BUG-SMTP-ONBOARD-PRIORITY`

## Files Changed

- `apps/api/src/growixa_api/cli/onboard_iitdeveloper.py` — SMTP priority logic in section §8

## Commit

f49df0a05647b5b8a040304f13483136bfa330c8

## Risk Level

**LOW** — CLI-only script, no API surface changed, no migrations.

## Production Fix Required (After Merge)

```bash
docker compose exec api python -m growixa_api.cli.onboard_iitdeveloper
```

Expected:
```
[✓] Using real user-configured SMTP: s61.gocheapweb.com:465
[~] Deactivated placeholder SMTP connection: smtp.iitdeveloper.com
[~] Reassigned sender identity info@iitdeveloper.com -> s61.gocheapweb.com
[~] Reassigned sender identity ravi@iitdeveloper.com -> s61.gocheapweb.com
```

## Test Coverage Gap

No tests exist for `onboard_iitdeveloper.py`. Follow-up: add tests for
the multi-connection priority scenario.

## Review Focus Points

1. Does real_epcs / placeholder_epcs partition correctly cover all cases? -> Yes, separates placeholder by host.
2. Is deactivating the placeholder safe (no FK constraints broken)? -> Yes, soft deactivate (`is_active = False`), FK references remain valid in PostgreSQL.
3. Does si.email_provider_connection_id = epc.id correctly reassign sender identities? -> Yes, points to active user-configured connection.
4. Is PLACEHOLDER_HOST constant the right way to identify the placeholder? -> Yes, standard for this script.

## Review Verdict

- **Reviewed Code Commit**: `f49df0a05647b5b8a040304f13483136bfa330c8`
- **Verdict**: `APPROVED`
- **Reviewer**: Google Antigravity (Independent Reviewer)
- **Secrets Inspection**: Clean. No secrets, keys, or credentials leaked.

## Status

- [x] Reviewed Code Commit: f49df0a05647b5b8a040304f13483136bfa330c8
- [x] Approved
- [x] Merged
