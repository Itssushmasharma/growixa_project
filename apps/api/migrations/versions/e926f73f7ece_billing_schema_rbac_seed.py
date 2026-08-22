"""subscription_plans, account_subscriptions, account_credit_balances,
account_credit_purchases, coupon_codes, coupon_redemptions tables (Slice 7 GRX-BILL-002)

Revision ID: e926f73f7ece
Revises: 2384479986cf
Create Date: 2026-08-13 00:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e926f73f7ece"
down_revision: str | Sequence[str] | None = "2384479986cf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles) — reused here, not
# re-generated, so the new grants attach to the same rows.
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"
ROLE_ADMIN = "8c7ebd1a-f1fe-4d22-bb7f-29c79d0444ce"
ROLE_MARKETING_MANAGER = "6b7dc157-82c4-4878-b12d-826b67cf7181"
ROLE_CONTENT_CREATOR = "03c1c2a9-1315-4a86-93eb-b5c936280372"
ROLE_ANALYST = "6ab3fff0-9fcb-46e0-9cdb-0c54c7032ab3"
ROLE_VIEWER = "cd7ad750-9044-4ee8-919d-9b6a8d2f27ec"

PERM_BILLING_MANAGE = "95d5fb42-fa6e-4be7-bf74-256c775120ad"
PERM_BILLING_VIEW = "2ede5f71-67b8-441e-8a8c-35e1f14c98fa"

# uuid.UUID, not a plain string -- asyncpg needs a real UUID object for
# platform_permissions.id, same fix GRX-AI-002's migration needed for this exact bug.
PLATFORM_PERM_BILLING_MANAGE = uuid.UUID("0d5fe956-012c-4836-beae-c9935937565d")

PLAN_FREE = "ec6e4dfc-72ed-41a9-b6ba-25b0e77c89af"
PLAN_STARTER = "19353027-141d-4695-af62-a5933b1f7190"
PLAN_PRO = "4835af52-7eea-4c6f-b04e-a30014652264"
PLAN_ENTERPRISE = "718c323d-b6b6-43c5-ad2a-bec72b9ed0af"


def upgrade() -> None:
    """Upgrade schema."""
    # The speculative Phase-D placeholder from 3186b6c66a6d is superseded by
    # account_subscriptions.plan_id below — never had a real use.
    op.drop_column("accounts", "plan_id")
    op.drop_constraint("ck_accounts_selected_plan_slug", "accounts", type_="check")
    op.create_check_constraint(
        "ck_accounts_selected_plan_slug",
        "accounts",
        "selected_plan_slug IN ('free', 'starter', 'pro')",
    )

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("price_usd", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_inr", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_contacts", sa.Integer(), nullable=True),
        sa.Column("max_monthly_emails", sa.Integer(), nullable=True),
        sa.Column("max_monthly_ai_runs", sa.Integer(), nullable=True),
        sa.Column("max_social_accounts", sa.Integer(), nullable=True),
        sa.Column("max_user_seats", sa.Integer(), nullable=True),
        sa.Column("allow_byo_ai_key", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("allow_byo_smtp", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("audit_export_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("audit_api_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("razorpay_plan_id_usd", sa.Text(), nullable=True),
        sa.Column("razorpay_plan_id_inr", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "slug IN ('free', 'starter', 'pro', 'enterprise')", name="ck_subscription_plans_slug"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "account_subscriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_email_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("period_ai_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("razorpay_customer_id", sa.Text(), nullable=True),
        sa.Column("razorpay_subscription_id", sa.Text(), nullable=True),
        sa.Column("set_by_platform_admin_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'PAST_DUE', 'CANCELED', 'HALTED')",
            name="ck_account_subscriptions_status",
        ),
        sa.CheckConstraint("currency IN ('USD', 'INR')", name="ck_account_subscriptions_currency"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"]),
        sa.ForeignKeyConstraint(["set_by_platform_admin_id"], ["platform_admins.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id"),
    )

    op.create_table(
        "account_credit_balances",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("credit_type", sa.Text(), nullable=False),
        sa.Column("remaining_credits", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "credit_type IN ('AI_RUNS', 'EMAIL_SENDS', 'CONTACT_SLOTS', 'SOCIAL_POSTS')",
            name="ck_account_credit_balances_credit_type",
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id", "credit_type", name="ux_account_credit_balances_account_type"
        ),
    )

    op.create_table(
        "account_credit_purchases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("credit_type", sa.Text(), nullable=False),
        sa.Column("credits_added", sa.Integer(), nullable=False),
        sa.Column(
            "purchased_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("razorpay_payment_id", sa.Text(), nullable=True),
        sa.Column("granted_by_platform_admin_id", sa.UUID(), nullable=True),
        sa.CheckConstraint(
            "credit_type IN ('AI_RUNS', 'EMAIL_SENDS', 'CONTACT_SLOTS', 'SOCIAL_POSTS')",
            name="ck_account_credit_purchases_credit_type",
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by_platform_admin_id"], ["platform_admins.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("razorpay_payment_id"),
    )
    op.create_index(
        "ix_account_credit_purchases_account_id", "account_credit_purchases", ["account_id"]
    )

    op.create_table(
        "coupon_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("discount_type", sa.Text(), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("credit_type", sa.Text(), nullable=True),
        sa.Column("applicable_plan_slugs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("redemption_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by_platform_admin_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discount_type IN ('PERCENTAGE', 'FIXED_AMOUNT', 'CREDIT_GRANT')",
            name="ck_coupon_codes_discount_type",
        ),
        sa.ForeignKeyConstraint(["created_by_platform_admin_id"], ["platform_admins.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "coupon_redemptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("coupon_code_id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column(
            "redeemed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["coupon_code_id"], ["coupon_codes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "coupon_code_id", "account_id", name="ux_coupon_redemptions_code_account"
        ),
    )

    _seed_billing_permissions()
    _seed_default_plans()
    _backfill_existing_accounts()


def _seed_billing_permissions() -> None:
    """Slice 7 `billing.manage` / `billing.view` (customer RBAC) and
    `platform.billing.manage` (platform RBAC) permission codes, see RBAC.md §Slice 7
    permission codes."""
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.Text()),
        sa.column("description", sa.Text()),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
    )

    op.bulk_insert(
        permissions_table,
        [
            {
                "id": PERM_BILLING_MANAGE,
                "code": "billing.manage",
                "description": (
                    "Subscribe/change plan, buy top-up credits, redeem a coupon code -- "
                    "any action that actually charges the account via Razorpay"
                ),
            },
            {
                "id": PERM_BILLING_VIEW,
                "code": "billing.view",
                "description": "View the account's current plan, usage/quota, and billing history",
            },
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            # billing.manage: Super Admin only, matching integrations.manage's
            # real-money-adjacent precedent (RBAC.md §Slice 7 permission codes).
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_BILLING_MANAGE},
            # billing.view: all six roles, matching company.settings.view's
            # broad-visibility precedent.
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_BILLING_VIEW},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_BILLING_VIEW},
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_BILLING_VIEW},
            {"role_id": ROLE_CONTENT_CREATOR, "permission_id": PERM_BILLING_VIEW},
            {"role_id": ROLE_ANALYST, "permission_id": PERM_BILLING_VIEW},
            {"role_id": ROLE_VIEWER, "permission_id": PERM_BILLING_VIEW},
        ],
    )

    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.billing.manage', "
            "'View/change any account''s plan, subscription status, and credit "
            "balance without a payment; edit plan-wide quotas/prices; manage coupons')"
        ).bindparams(id=PLATFORM_PERM_BILLING_MANAGE)
    )
    # Per RBAC.md §Slice 7 platform permission codes: owner + finance only, NOT admin
    # (unlike platform.accounts.manage/platform.ai.manage) -- billing is
    # platform.finance's stated domain specifically.
    for role in ("platform.owner", "platform.finance"):
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=PLATFORM_PERM_BILLING_MANAGE)
        )


def _seed_default_plans() -> None:
    """The four plan rows -- working-draft quotas/prices per
    BILLING_SYSTEM_ARCHITECTURE.md §2 / subscription_plans_matrix.csv, accepted by the
    product owner as the starting numbers (changeable anytime later via
    platform.billing.manage, no redeploy)."""
    subscription_plans_table = sa.table(
        "subscription_plans",
        sa.column("id", sa.UUID()),
        sa.column("slug", sa.Text()),
        sa.column("name", sa.Text()),
        sa.column("price_usd", sa.Numeric(10, 2)),
        sa.column("price_inr", sa.Numeric(10, 2)),
        sa.column("max_contacts", sa.Integer()),
        sa.column("max_monthly_emails", sa.Integer()),
        sa.column("max_monthly_ai_runs", sa.Integer()),
        sa.column("max_social_accounts", sa.Integer()),
        sa.column("max_user_seats", sa.Integer()),
        sa.column("allow_byo_ai_key", sa.Boolean()),
        sa.column("allow_byo_smtp", sa.Boolean()),
        sa.column("audit_export_enabled", sa.Boolean()),
        sa.column("audit_api_enabled", sa.Boolean()),
    )
    op.bulk_insert(
        subscription_plans_table,
        [
            {
                "id": PLAN_FREE,
                "slug": "free",
                "name": "Free",
                "price_usd": 0,
                "price_inr": 0,
                "max_contacts": 250,
                "max_monthly_emails": 1000,
                "max_monthly_ai_runs": 10,
                "max_social_accounts": 1,
                "max_user_seats": 1,
                "allow_byo_ai_key": False,
                "allow_byo_smtp": False,
                "audit_export_enabled": False,
                "audit_api_enabled": False,
            },
            {
                "id": PLAN_STARTER,
                "slug": "starter",
                "name": "Starter",
                "price_usd": 19,
                "price_inr": 1499,
                "max_contacts": 2500,
                "max_monthly_emails": 15000,
                "max_monthly_ai_runs": 150,
                "max_social_accounts": 3,
                "max_user_seats": 3,
                "allow_byo_ai_key": False,
                "allow_byo_smtp": True,
                "audit_export_enabled": True,
                "audit_api_enabled": False,
            },
            {
                "id": PLAN_PRO,
                "slug": "pro",
                "name": "Pro",
                "price_usd": 49,
                "price_inr": 3999,
                "max_contacts": 15000,
                "max_monthly_emails": 100000,
                "max_monthly_ai_runs": 1000,
                "max_social_accounts": 10,
                "max_user_seats": 10,
                "allow_byo_ai_key": True,
                "allow_byo_smtp": True,
                "audit_export_enabled": True,
                "audit_api_enabled": True,
            },
            {
                "id": PLAN_ENTERPRISE,
                "slug": "enterprise",
                "name": "Enterprise",
                "price_usd": None,
                "price_inr": None,
                "max_contacts": None,
                "max_monthly_emails": None,
                "max_monthly_ai_runs": None,
                "max_social_accounts": None,
                "max_user_seats": None,
                "allow_byo_ai_key": True,
                "allow_byo_smtp": True,
                "audit_export_enabled": True,
                "audit_api_enabled": True,
            },
        ],
    )


def _backfill_existing_accounts() -> None:
    """Every pre-existing account (created before this migration ran) gets a real
    Free-tier account_subscriptions row too -- new accounts get one automatically at
    registration going forward (GRX-BILL-002, accounts/services.py), but this migration
    is what closes the gap for every account already in the database."""
    op.execute(
        sa.text(
            "INSERT INTO account_subscriptions "
            "(id, account_id, plan_id, status, currency, current_period_start, current_period_end) "
            "SELECT gen_random_uuid(), a.id, :plan_id, 'ACTIVE', 'USD', now(), "
            "now() + interval '30 days' "
            "FROM accounts a "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM account_subscriptions s WHERE s.account_id = a.id"
            ")"
            # A real uuid.UUID, not a plain string -- a raw sa.text() bindparam has no
            # column-type info to coerce through, unlike bulk_insert() elsewhere in this
            # file, so asyncpg needs the native type directly (same bug class as
            # PLATFORM_PERM_BILLING_MANAGE above).
        ).bindparams(plan_id=uuid.UUID(PLAN_FREE))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("DELETE FROM platform_role_permissions WHERE permission_id = :id").bindparams(
            id=PLATFORM_PERM_BILLING_MANAGE
        )
    )
    op.execute(
        sa.text("DELETE FROM platform_permissions WHERE id = :id").bindparams(
            id=PLATFORM_PERM_BILLING_MANAGE
        )
    )
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id IN "
        f"('{PERM_BILLING_MANAGE}', '{PERM_BILLING_VIEW}')"
    )
    op.execute(
        f"DELETE FROM permissions WHERE id IN ('{PERM_BILLING_MANAGE}', '{PERM_BILLING_VIEW}')"
    )

    op.drop_table("coupon_redemptions")
    op.drop_table("coupon_codes")
    op.drop_index("ix_account_credit_purchases_account_id", table_name="account_credit_purchases")
    op.drop_table("account_credit_purchases")
    op.drop_table("account_credit_balances")
    op.drop_table("account_subscriptions")
    op.drop_table("subscription_plans")

    op.drop_constraint("ck_accounts_selected_plan_slug", "accounts", type_="check")
    op.execute(
        sa.text(
            "UPDATE accounts "
            "SET selected_plan_slug = 'starter' "
            "WHERE selected_plan_slug IS NOT NULL "
            "AND selected_plan_slug NOT IN ('starter', 'growth')"
        )
    )
    op.create_check_constraint(
        "ck_accounts_selected_plan_slug", "accounts", "selected_plan_slug IN ('starter', 'growth')"
    )
    op.add_column("accounts", sa.Column("plan_id", sa.UUID(), nullable=True))
