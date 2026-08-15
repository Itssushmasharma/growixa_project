"""account_subscriptions.status gains PENDING (Slice 7 GRX-BILL-004)

Revision ID: 60f7c30ff18a
Revises: e926f73f7ece
Create Date: 2026-08-13 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "60f7c30ff18a"
down_revision: str | Sequence[str] | None = "e926f73f7ece"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # A checkout (POST /billing/subscribe) creates the Razorpay Subscription and
    # immediately stores its id on the row -- required so the webhook (GRX-BILL-003)
    # can find it by razorpay_subscription_id once the customer actually authorizes
    # payment. Nothing is granted while PENDING: GRX-BILL-005's quota evaluator treats
    # only ACTIVE/PAST_DUE as "use this plan_id's limits" -- PENDING is a real status a
    # row can sit in, deliberately not a state the evaluator honors.
    op.drop_constraint("ck_account_subscriptions_status", "account_subscriptions", type_="check")
    op.create_check_constraint(
        "ck_account_subscriptions_status",
        "account_subscriptions",
        "status IN ('PENDING', 'ACTIVE', 'PAST_DUE', 'CANCELED', 'HALTED')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_account_subscriptions_status", "account_subscriptions", type_="check")
    op.create_check_constraint(
        "ck_account_subscriptions_status",
        "account_subscriptions",
        "status IN ('ACTIVE', 'PAST_DUE', 'CANCELED', 'HALTED')",
    )
