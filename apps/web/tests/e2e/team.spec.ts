import { execFileSync } from "node:child_process";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { E2E_USER_EMAIL, E2E_USER_PASSWORD } from "./fixtures";

const REPO_ROOT = path.resolve(__dirname, "../../../..");
const COMPOSE_BIN = process.env.COMPOSE_BIN ?? "podman";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function cleanupInvitedUser(email: string): void {
  const script = `
import asyncio
from sqlalchemy import delete, select

from growixa_api.audit.models import AuditLog
from growixa_api.auth.models import RefreshToken
from growixa_api.db import async_session_factory
from growixa_api.users.models import User, UserInvitation, UserRole

async def main():
    async with async_session_factory() as session:
        result = await session.execute(select(User.id).where(User.email == "${email}"))
        user_id = result.scalar_one_or_none()
        if user_id is not None:
            await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
            await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user_id))
            await session.execute(delete(UserRole).where(UserRole.user_id == user_id))
            await session.execute(delete(User).where(User.id == user_id))
        await session.execute(delete(UserInvitation).where(UserInvitation.email == "${email}"))
        await session.commit()

asyncio.run(main())
`;
  execFileSync(COMPOSE_BIN, ["compose", "exec", "-T", "api", "python3", "-c", script], {
    cwd: REPO_ROOT,
    stdio: "inherit",
  });
}

// There's no "accept invitation" page in the frontend yet (accepting is still an
// API-only flow, per GRX-USER-001's interim no-email-delivery design) — so this test
// drives the admin-facing invite through the real UI, accepts via a direct API call (the
// only way a real invitee could do it today, e.g. via a shared link hitting the API), and
// then logs in as the new user through the real UI again to prove the whole loop works.
test("admin invites a user, the invitee accepts, and logs in (GRX-USER-002 happy path)", async ({
  page,
}) => {
  const invitedEmail = `e2e-invitee-${Date.now()}@example.com`;
  const invitedPassword = "E2E-Invitee-Password-123!";

  try {
    await page.goto("/login");
    await page.getByLabel("Email").fill(E2E_USER_EMAIL);
    await page.getByLabel("Password").fill(E2E_USER_PASSWORD);
    await page.getByRole("button", { name: "Login to Growixa" }).click();
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.getByRole("link", { name: "Team" }).click();
    await expect(page).toHaveURL(/\/dashboard\/team$/);

    await page.getByRole("button", { name: "+ Invite user" }).click();
    await page.getByLabel("Email").fill(invitedEmail);
    await page.getByRole("button", { name: "Send invite" }).click();

    await expect(page.getByText(new RegExp(`Invitation sent to ${invitedEmail}`))).toBeVisible();
    const inviteToken = await page.locator("code").textContent();
    expect(inviteToken).toBeTruthy();

    const acceptResponse = await page.request.post(`${API_URL}/users/invitations/accept`, {
      data: {
        token: inviteToken,
        password: invitedPassword,
        full_name: "E2E Invitee",
      },
    });
    expect(acceptResponse.ok()).toBe(true);

    await page.context().clearCookies();
    await page.goto("/login");
    await page.getByLabel("Email").fill(invitedEmail);
    await page.getByLabel("Password").fill(invitedPassword);
    await page.getByRole("button", { name: "Login to Growixa" }).click();

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByText("E2E Invitee")).toBeVisible();
  } finally {
    cleanupInvitedUser(invitedEmail);
  }
});
