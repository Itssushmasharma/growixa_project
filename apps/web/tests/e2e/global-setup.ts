import { execFileSync } from "node:child_process";
import path from "node:path";

import { E2E_USER_EMAIL, E2E_USER_PASSWORD } from "./fixtures";

// tests/e2e -> apps/web -> apps -> repo root, where compose.yaml lives.
const REPO_ROOT = path.resolve(__dirname, "../../../..");

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
from growixa_api.db import async_session_factory
from growixa_api.auth.security import hash_password
from growixa_api.users.models import User

async def main():
    async with async_session_factory() as session:
        user = User(
            email="${E2E_USER_EMAIL}",
            password_hash=hash_password("${E2E_USER_PASSWORD}"),
            full_name="E2E Dashboard User",
        )
        session.add(user)
        await session.commit()

asyncio.run(main())
`;

  execFileSync("podman", ["compose", "exec", "-T", "api", "python3", "-c", script], {
    cwd: REPO_ROOT,
    stdio: "inherit",
  });
}
