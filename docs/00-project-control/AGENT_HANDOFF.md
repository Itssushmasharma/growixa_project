# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-31
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-CONTACT-003` — Segments (dynamic and saved). Picked immediately after
`GRX-CONTACT-002` per the user's "go".

## Work completed

- New tables (migration `18cf808f2b87`): `segments`, `segment_rules`, `segment_members`.
- Rule evaluator (`contacts/repositories.py`'s `build_rule_condition` +
  `evaluate_segment_rules`/`count_dynamic_segment_members`) translates a validated
  `(field, operator, value)` triple into a SQLAlchemy condition over `Contact`. Supported
  fields: `status`/`source` (equals), `email` (equals/contains), `tag` (equals),
  `created_at` (before/after, ISO-8601 value), `custom_field:<key>` (equals/contains,
  key must exist). All rules on a segment are AND-combined only — no OR/grouping, per
  the Slice 2 scope decision made during planning.
- `POST /contacts/segments` validates every rule before creating anything
  (`_validate_segment_rule` in `services.py`) — unsupported field, wrong operator for a
  field, unknown custom-field key, or an unparseable `created_at` date all return 400.
- `DYNAMIC` segments: membership computed live on every `GET`. `SAVED` segments:
  membership evaluated once at creation and written into `segment_members`, never
  re-evaluated automatically (no scheduler exists yet — that's Slice 4).
- Endpoints: `GET`/`POST /contacts/segments`, `GET /contacts/segments/{id}`, `GET
  /contacts/segments/{id}/members` (returns full `ContactOut` snapshots, reusing the
  same `_snapshot` helper as contacts/tags/lists).

## A scope note worth flagging

Slice 2 planning (this session, `GRX-CONTACT-003`'s tracker row) had named
`consent_status` as an example segment-rule field. It is **not implemented** — the
`consent_records` table doesn't exist until `GRX-CONTACT-005`. Using `consent_status` as
a rule field today correctly 400s as "unsupported field" rather than silently matching
zero contacts. Extend `SEGMENT_RULE_FIELD_OPERATORS` in `repositories.py` once
`GRX-CONTACT-005` lands.

## Files changed

- `apps/api/src/growixa_api/contacts/models.py` (added `Segment`, `SegmentRule`,
  `SegmentMember`; `SegmentRule.segment_id` has `index=True`)
- `apps/api/src/growixa_api/contacts/repositories.py` (rule evaluator + segment CRUD)
- `apps/api/src/growixa_api/contacts/services.py` (`SegmentDetail` type alias; rule
  validation; `create_segment_with_rules`, `get_segment_with_details`,
  `list_segments_with_details`, `list_segment_members`)
- `apps/api/src/growixa_api/contacts/schemas.py` (`SegmentRuleIn`/`Out`, `SegmentIn`/`Out`)
- `apps/api/src/growixa_api/contacts/api.py` (new segment routes, `_segment_to_out`)
- `apps/api/migrations/versions/18cf808f2b87_segments.py` (new)
- `apps/api/tests/test_contacts_segments.py` (new, 9 tests)
- `docs/00-project-control/MASTER_TASK_TRACKER.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`
  (this update)

## Commands executed

```bash
cd apps/api
.venv/bin/alembic revision --autogenerate -m "segments"
# hand-added an index on segment_rules.segment_id, then added index=True to the ORM
# model to match (alembic check caught the model/migration mismatch on the first pass)
.venv/bin/alembic upgrade head
.venv/bin/ruff check . && .venv/bin/ruff format . && .venv/bin/mypy .
.venv/bin/pytest -q   # 85 passed, 3 skipped (93% coverage)
.venv/bin/alembic check   # no drift

cd ../..
podman compose up -d --build api
# full pytest run wiped admin@growixa.local again (same as after every prior task this
# session) — recreated it
# live curl: create a tag, tag contact A, create both a DYNAMIC and a SAVED segment on
# the same rule (both member_count 1) -> tag contact B (created after both segments) ->
# DYNAMIC now member_count 2, SAVED still 1 -> Analyst 200/403 split -> Viewer 403
# cleaned up all smoke-test rows afterward
```

## Test results

`ruff`/`mypy` clean. `pytest` 85 passed, 3 skipped (93% coverage, 9 new tests).
`alembic check` → no drift. Live-verified end-to-end against rebuilt Compose containers,
including the DYNAMIC-vs-SAVED live/frozen distinction that's the whole point of this task.

## Migrations

`18cf808f2b87` — `segments`, `segment_rules`, `segment_members` tables, plus an index on
`segment_rules.segment_id`. No permission seed needed — existing `contacts.manage`/
`contacts.view` already cover segments.

## Decisions

None new beyond the scope note above (declined to implement `consent_status` early).

## Blockers

None.

## Known issues

- Same carryover list as prior Slice 2 entries: possible latent `MissingGreenlet` in
  `company_profile` (background task filed, unresolved), `GRX-DEVOPS-001` still
  `IN_REVIEW`, `GRX-DOC-003` blocked on that push.
- Running the full `pytest` suite locally continues to wipe manually created Compose
  database rows via the migration round-trip test — same as every prior task this
  session, not a new issue.

## Current state

`GRX-CONTACT-003` is `DONE`. This closes out the backend half of Slice 2's core
contact-organization features (contacts, tags, lists, segments). Sprint 2's next `READY`
task is `GRX-CONTACT-004` (CSV contact import).

## Exact next task

`GRX-CONTACT-004` — CSV contact import (`contact_imports`, `contact_import_rows` tables +
API; upload, column mapping, validation, per-row status, import history). No explicit
user direction beyond continuing Sprint 2; awaiting confirmation before picking it up.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
podman compose up -d
```

## Latest commit

`a725e0e` — feat(contacts): dynamic and saved segments (GRX-CONTACT-003)
