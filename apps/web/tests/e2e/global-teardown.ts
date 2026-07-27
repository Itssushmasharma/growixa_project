import { execFileSync } from "node:child_process";
import path from "node:path";

import { E2E_USER_EMAIL } from "./fixtures";

const REPO_ROOT = path.resolve(__dirname, "../../../..");
const COMPOSE_BIN = process.env.COMPOSE_BIN ?? "podman";

export default function globalTeardown(): void {
  const script = `
import asyncio
from sqlalchemy import delete, select

from growixa_api.audit.models import AuditLog
from growixa_api.auth.models import RefreshToken
from growixa_api.db import async_session_factory
from growixa_api.users.models import User

async def main():
    async with async_session_factory() as session:
        result = await session.execute(select(User.id).where(User.email == "${E2E_USER_EMAIL}"))
        user_id = result.scalar_one_or_none()
        if user_id is None:
            return
        await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()

asyncio.run(main())
`;

  execFileSync(COMPOSE_BIN, ["compose", "exec", "-T", "api", "python3", "-c", script], {
    cwd: REPO_ROOT,
    stdio: "inherit",
  });
}
