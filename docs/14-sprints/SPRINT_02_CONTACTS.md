# Sprint 02 — Contacts

- Document ID: DOC-SPRINT-02
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-30
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [DECISIONS §DEC-GRX-010](../00-project-control/DECISIONS.md)

Sprint 2 is Slice 2 (Contacts) from [DEC-GRX-010](../00-project-control/DECISIONS.md). Its
job is to prove a company can build and maintain its own audience: add/import contacts,
organize them with tags/lists/segments, and respect consent/suppression rules — nothing
downstream (no email sending) exists yet, that's Slice 3.

## Included

Per [MVP_SCOPE.md §B](../01-product/MVP_SCOPE.md):

1. Contact CRUD (create, edit, archive) with email-based dedup
2. Contact custom fields
3. Contact tags
4. Contact lists (manually curated)
5. Segments — dynamic (live-evaluated) and saved (frozen snapshot)
6. CSV contact import, with validation, column mapping, and import history
7. Consent status per channel (email, SMS), recorded as an insert-only history
8. Suppression list (unsubscribed / bounced / complained / manual)
9. Contact activity history (via the existing `audit_logs` table, `entity_type = 'contact'`
   — no new activity table)
10. Frontend UI for all of the above, gated by the new `contacts.manage` / `contacts.view`
    permissions

Full data model: [DATA_MODEL.md §Slice 2 entities](../05-data/DATA_MODEL.md#slice-2-entities-full-detail),
[DATABASE_SCHEMA.md §Slice 2](../05-data/DATABASE_SCHEMA.md#slice-2-contacts-tables),
[ERD.md §Slice 2 additions](../05-data/ERD.md#slice-2-contacts-additions). RBAC:
[RBAC.md §Slice 2](../08-security/RBAC.md#slice-2-permission-codes).

Full task breakdown with dependencies: [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md)
(`GRX-CONTACT-*`).

## Explicitly excluded from Sprint 2

- Anything email/social/AI (Slices 3, 5, 6 respectively) — segments and lists are built
  now so Slice 3+ has somewhere to target, but no campaign, send, or publish logic exists
  in Sprint 2.
- Fuzzy/name-based duplicate detection — dedup is email-only in Slice 2.
- OR logic / rule grouping in segment rules — all rules on a segment are AND-combined only.
- Automatic re-evaluation of `SAVED` segments on a schedule — no scheduler exists yet
  (that arrives with Slice 4's worker); re-saving is a manual user action in Slice 2.
- A dedicated `contact_activity` table — activity history reuses `audit_logs`.
- Self-service unsubscribe pages/links — those are a Slice 3+ concern once real sends
  exist to link back from; Slice 2 only builds the suppression/consent data model and an
  admin-facing UI to manage them manually.

If implementing a Sprint 2 task seems to require touching any of the above, stop and flag
it — it means the task is scoped wrong, not that a shortcut through excluded territory is
warranted.

## Sprint 2 acceptance criteria

- An Admin/Marketing Manager can create, edit, and archive a contact.
- Creating or importing a contact with an email that already exists updates the existing
  contact rather than creating a duplicate.
- Contacts can be tagged, added to a manually curated list, and matched by a rule-based
  segment (both `DYNAMIC` and `SAVED`).
- A CSV file can be uploaded, columns mapped to contact fields, and the import produces a
  visible history entry with counts of imported/skipped/errored rows.
- A contact's consent status per channel can be recorded and viewed as a history, not just
  a current flag.
- An email address can be added to the suppression list and is visibly flagged as
  suppressed wherever contacts are shown.
- A user with `contacts.view` but not `contacts.manage` can see contacts/tags/lists/
  segments but cannot create, edit, import, tag, list, or suppress anything (verified by a
  negative test, same pattern as Sprint 1's RBAC tests).
- Automated backend and frontend tests pass; CI passes.

## Definition of done for this sprint

[DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md) applies to every task
in this sprint individually — the sprint itself is done only when every task in
[MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md) tagged `GRX-CONTACT-*`
is `DONE`, not merely attempted.
