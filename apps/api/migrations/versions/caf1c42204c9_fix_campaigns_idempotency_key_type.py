"""fix campaigns.idempotency_key type drift

Revision ID: caf1c42204c9
Revises: 4a92b8107c12
Create Date: 2026-08-06 18:10:00.000000

Two Sprint 4 worktrees independently authored GRX-SCHED-001. The version that
landed on main via merge (`4a92b8107c12`) defines `idempotency_key` as
`UUID NOT NULL UNIQUE` in its `upgrade()`, but a different pre-merge worktree
had already run an *earlier* draft of that same revision ID against this dev
database — one that added `idempotency_key` as a plain nullable `TEXT`
column, with no unique constraint. Because Alembic's `alembic_version`
bookkeeping only tracks the revision ID (not the migration file's content), it
still reports `4a92b8107c12` as fully applied even though the actual column
on disk no longer matches what that revision's current file defines —
confirmed via `alembic check`, which reported drift only on this column (the
scheduled_at/cancelled_at columns, the index, and the CHECK constraint all
already matched).

`campaigns` has zero rows in every environment this has been applied to, so
there's no data to migrate — this originally dropped and re-added the column
to match `4a92b8107c12`'s own definition exactly, rather than editing history.

UPDATE (still GRX-SCHED-002 prep, same day): that original upgrade()/
downgrade() pair turned out to be a no-op with a landmine in it.
`4a92b8107c12` *already* creates `idempotency_key` as `UUID NOT NULL UNIQUE`
with a constraint named `uq_campaigns_idempotency_key` — identical to what
this revision redundantly re-created. Redundant on the way up is harmless,
but on the way down it isn't: this revision's downgrade() dropped
`uq_campaigns_idempotency_key`, and then `4a92b8107c12`'s own downgrade()
immediately tried to drop the *same* constraint name again, failing with
"constraint does not exist" (caught by
`test_alembic_upgrade_head_then_downgrade_base_round_trips_cleanly`). Since
this revision's only job was already fully subsumed by `4a92b8107c12`, both
functions are now no-ops — the revision id stays in the chain purely as a
historical marker for the drift-reconciliation event described above.
"""

# revision identifiers, used by Alembic.
revision: str = "caf1c42204c9"
down_revision: str = "4a92b8107c12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
