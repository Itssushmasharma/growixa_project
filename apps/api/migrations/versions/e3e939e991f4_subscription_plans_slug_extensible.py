"""subscription_plans.slug widened for platform-admin-created tiers (Slice 7 GRX-SAAS-006)

Revision ID: e3e939e991f4
Revises: b6eed962fd56
Create Date: 2026-08-14 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3e939e991f4"
down_revision: str | Sequence[str] | None = "b6eed962fd56"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # GRX-SAAS-006 gives platform admins POST /platform/subscription-plans -- a genuine
    # *create*, not just edit, per the product owner's explicit request. The old
    # 4-value whitelist (free/starter/pro/enterprise) made that a lie: any new tier an
    # admin created would violate this CHECK at insert time. Widened to a plain
    # slug-format sanity check (lowercase letters/digits/underscore/hyphen) instead of
    # dropped outright, so garbage input still fails fast at the DB layer.
    #
    # Note this does NOT make a new plan self-serve-checkout-able by itself --
    # POST /billing/subscribe's SubscribeIn.plan_slug (GRX-BILL-004) stays
    # Literal["starter", "pro"] deliberately; wiring a newly-created tier into that
    # customer-facing route is a separate, later change once a real new tier exists
    # (BILLING_SYSTEM_ARCHITECTURE.md §6, open items). A platform admin can still grant
    # a new plan to an account directly via the manual override endpoint this task
    # adds, which looks the plan up by slug with no such Literal restriction.
    op.drop_constraint("ck_subscription_plans_slug", "subscription_plans", type_="check")
    op.create_check_constraint(
        "ck_subscription_plans_slug",
        "subscription_plans",
        "slug ~ '^[a-z0-9_-]+$'",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_subscription_plans_slug", "subscription_plans", type_="check")
    op.create_check_constraint(
        "ck_subscription_plans_slug",
        "subscription_plans",
        "slug IN ('free', 'starter', 'pro', 'enterprise')",
    )
