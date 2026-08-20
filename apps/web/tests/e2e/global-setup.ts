import { execFileSync } from "node:child_process";
import path from "node:path";

import { E2E_USER_EMAIL, E2E_USER_PASSWORD } from "./fixtures";

// tests/e2e -> apps/web -> apps -> repo root, where compose.yaml lives.
const REPO_ROOT = path.resolve(__dirname, "../../../..");

// "podman" locally (this project's dev environment); GitHub Actions' runners have real
// Docker, so CI sets COMPOSE_BIN=docker instead (see .github/workflows/ci.yml).
const COMPOSE_BIN = process.env.COMPOSE_BIN ?? "podman";

/**
 * Creates a fixed test user directly via the ORM inside the running `api` container — the
 * same technique used throughout this project's manual Compose verification, since there
 * is no public "create user" endpoint (invitations require an existing admin session).
 * Requires the Compose stack to already be running; this test suite is a live e2e check
 * against real Postgres/Redis, not an isolated unit test.
 */
export default function globalSetup(): void {
  const script = `
import asyncio
from sqlalchemy import select

from growixa_api.db import async_session_factory
from growixa_api.auth.security import hash_password
from growixa_api.accounts.models import Account  # must be imported so SQLAlchemy can
from growixa_api.roles.models import Role         # resolve users.account_id -> accounts.id
from growixa_api.users.models import User, UserRole

async def main():
    async with async_session_factory() as session:
        # Idempotent: skip if the e2e user was already created by a previous run.
        existing = (await session.execute(select(User).where(User.email == "${E2E_USER_EMAIL}"))).scalar_one_or_none()
        if existing:
            return

        # Admin, not just any role: the team-management e2e test needs users.manage to
        # invite/list/change roles, and this same fixed user is reused across every e2e
        # spec rather than provisioning one per test file.
        admin_role = (await session.execute(select(Role).where(Role.name == "Admin"))).scalar_one()

        # Every User requires an account_id (NOT NULL FK to accounts.id). Create a
        # dedicated e2e account so teardown can delete it in isolation without touching
        # real seed data.
        account = Account(name="E2E Test Account")
        session.add(account)
        await session.flush()  # populate account.id before referencing it

        user = User(
            account_id=account.id,
            email="${E2E_USER_EMAIL}",
            password_hash=hash_password("${E2E_USER_PASSWORD}"),
            full_name="E2E Dashboard User",
        )
        session.add(user)
        await session.flush()
        session.add(UserRole(user_id=user.id, role_id=admin_role.id))
        await session.commit()

asyncio.run(main())
`;

  execFileSync(COMPOSE_BIN, ["compose", "exec", "-T", "api", "python3", "-c", script], {
    cwd: REPO_ROOT,
    stdio: "inherit",
  });
}
