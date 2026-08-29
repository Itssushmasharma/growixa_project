Task: Fix DATABASE_SCHEMA.md doc-drift — email_templates/email_template_versions missing account_id
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: docs/BACKEND/fix-email-templates-schema-doc
Worktree: .worktrees/grx-schema-doc-fix
Base Commit: 14c7601
Latest Commit: f4a6bfe
Status: APPROVED

## What Changed

`docs/05-data/DATABASE_SCHEMA.md` — added the `account_id` column row to both the
`email_templates` and `email_template_versions` table listings.

## Why

Both tables have `account_id: Mapped[uuid.UUID]` (`nullable=False`, FK → `accounts.id`
`ON DELETE CASCADE`) in the real model
(`apps/api/src/growixa_api/templates/models.py`), but the schema doc's listing omitted
the column entirely for both tables. Found while writing up `GRX-EMAIL-016`'s spec (a
BACKLOG task that will need to edit this same table's schema later) — fixed standalone
since it's a pre-existing doc-accuracy bug independent of whether that task proceeds.

## Important Files

- `docs/05-data/DATABASE_SCHEMA.md` (the only change)

## Tests

Documentation-only change — no tests applicable. Verified the column addition against
the real model directly (`apps/api/src/growixa_api/templates/models.py` lines 15-20,
44-49).

## Known Issues / Evidence Gaps

None.

## Review Findings

1. **Scope confirmed.** `git diff main...HEAD` (at commit f4a6bfe, before the handoff-add
   commit) touches exactly one file, `docs/05-data/DATABASE_SCHEMA.md`, adding exactly one
   row to each of the two table listings (`email_templates`, `email_template_versions`).
   No code, tests, config, or migrations changed.
2. **Accuracy verified against the real model** — read
   `apps/api/src/growixa_api/templates/models.py` directly:
   - `EmailTemplate.account_id`: `UUID(as_uuid=True)`, `ForeignKey("accounts.id",
     ondelete="CASCADE")`, `nullable=False`. Matches the added doc row: `uuid | FK →
     accounts.id ON DELETE CASCADE, NOT NULL`.
   - `EmailTemplateVersion.account_id`: same type/FK/CASCADE/NOT NULL, with a code comment
     confirming it's denormalized from `template_id`'s own `account_id` (kept for
     account-scoping consistency per GRX-SAAS-001). Matches the added doc row, including the
     "denormalized from `template_id`'s own `account_id`" annotation.
   - Both rows correctly accurate; no overclaim or invented detail.
3. **Secrets scan.** Diff is pure Markdown table-row text (column name, type, FK
   description) — no tokens, keys, passwords, or credentials of any kind. Clean.
4. **Placement/formatting.** Both new rows are inserted immediately after the `id` row in
   their respective table listings, consistent with the doc's existing convention of
   listing `account_id` right after `id` for other account-scoped tables in this file.
5. No scope creep — nothing else in the file was touched.

## Review Decision
APPROVED

## Reviewed Code Commit
af1f25fc353920dd74cef680c9620ce82714cc75

## Review Record Commit


## Human Approval
Not Required — documentation-only, no code/behavior change.

Status: APPROVED
