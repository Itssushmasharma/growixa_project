"""Seed-data migration test (GRX-AUTH-001).

Integration-tier test per TEST_STRATEGY.md §Database migration tests — requires a real
reachable PostgreSQL instance. A plain sync test for the same reason as test_migrations.py:
Alembic's async env.py drives its own event loop internally via asyncio.run(...).
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from growixa_api.config import get_settings

ALEMBIC_INI = Path(__file__).resolve().parent.parent.parent / "alembic.ini"

EXPECTED_ROLES = {
    "Super Admin",
    "Admin",
    "Marketing Manager",
    "Content Creator",
    "Analyst",
    "Viewer",
}

EXPECTED_PERMISSIONS = {
    "users.manage",
    "roles.manage",
    "company.settings.edit",
    "company.settings.view",
    "audit.view",
    "admin.access",
    # Slice 2 additions (GRX-CONTACT-001) — see RBAC.md §Slice 2 permission codes.
    "contacts.manage",
    "contacts.view",
    # Slice 3 additions (GRX-EMAIL-001..004) — see RBAC.md §Slice 3 permission codes.
    "integrations.manage",
    "campaigns.manage",
    "campaigns.view",
    "campaigns.send",
    # Slice 5 additions (GRX-SOCIAL-002) — see RBAC.md §Slice 5 permission codes.
    "social.manage",
    "social.publish",
    "social.view",
    # Slice 6 additions (GRX-AI-002) — see RBAC.md §Slice 6 permission codes.
    "ai.manage",
    "ai.view",
    # Phase 5 approval workflow (GRX-AI-006) — human-manager review gate.
    "ai.review",
    # Slice 7 additions (GRX-BILL-002) — see RBAC.md §Slice 7 permission codes.
    "billing.manage",
    "billing.view",
}

# permission code -> set of role names granted that permission, per RBAC.md's Sprint 1 and
# Slice 2 role -> permission matrices. This test checks the database as of `head`, so it's
# extended (not re-pinned to one migration) each time a later migration adds permissions.
EXPECTED_MATRIX: dict[str, set[str]] = {
    "users.manage": {"Super Admin", "Admin"},
    "roles.manage": {"Super Admin", "Admin"},
    "company.settings.edit": {"Super Admin", "Admin"},
    "company.settings.view": EXPECTED_ROLES,
    "audit.view": {"Super Admin", "Admin"},
    "admin.access": {"Super Admin", "Admin"},
    "contacts.manage": {"Super Admin", "Admin", "Marketing Manager"},
    "contacts.view": {"Super Admin", "Admin", "Marketing Manager", "Analyst"},
    "integrations.manage": {"Super Admin"},
    "campaigns.manage": {"Super Admin", "Admin", "Marketing Manager", "Content Creator"},
    "campaigns.view": {
        "Super Admin",
        "Admin",
        "Marketing Manager",
        "Content Creator",
        "Analyst",
    },
    "campaigns.send": {"Super Admin", "Admin", "Marketing Manager"},
    "social.manage": {"Super Admin", "Admin", "Marketing Manager", "Content Creator"},
    "social.publish": {"Super Admin", "Admin", "Marketing Manager"},
    "social.view": {
        "Super Admin",
        "Admin",
        "Marketing Manager",
        "Content Creator",
        "Analyst",
    },
    "ai.manage": {"Super Admin", "Admin", "Marketing Manager", "Content Creator"},
    "ai.view": {
        "Super Admin",
        "Admin",
        "Marketing Manager",
        "Content Creator",
        "Analyst",
    },
    # Content Creator intentionally excluded: generates content but cannot self-approve.
    "ai.review": {"Super Admin", "Admin", "Marketing Manager"},
    "billing.manage": {"Super Admin"},
    "billing.view": EXPECTED_ROLES,
}


def _sync_database_url() -> str:
    return get_settings().database_url.replace("+asyncpg", "+psycopg")


@pytest.mark.integration
def test_migration_seeds_sprint_1_roles_permissions_and_matrix() -> None:
    config = Config(str(ALEMBIC_INI))
    command.upgrade(config, "head")

    engine = create_engine(_sync_database_url())
    try:
        with engine.connect() as conn:
            role_names = {row[0] for row in conn.execute(text("SELECT name FROM roles"))}
            permission_codes = {
                row[0] for row in conn.execute(text("SELECT code FROM permissions"))
            }
            matrix_rows = conn.execute(
                text(
                    "SELECT p.code, r.name FROM role_permissions rp "
                    "JOIN roles r ON r.id = rp.role_id "
                    "JOIN permissions p ON p.id = rp.permission_id"
                )
            ).all()
    finally:
        engine.dispose()

    assert role_names == EXPECTED_ROLES
    assert permission_codes == EXPECTED_PERMISSIONS

    actual_matrix: dict[str, set[str]] = {}
    for code, role_name in matrix_rows:
        actual_matrix.setdefault(code, set()).add(role_name)
    assert actual_matrix == EXPECTED_MATRIX
