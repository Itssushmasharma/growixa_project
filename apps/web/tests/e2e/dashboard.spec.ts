import { expect, test } from "@playwright/test";

import { E2E_USER_EMAIL, E2E_USER_PASSWORD } from "./fixtures";

test("logged-out user visiting the dashboard is redirected to login", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login$/);
});

test("logging in shows the dashboard shell, and logging out returns to login", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill(E2E_USER_EMAIL);
  await page.getByLabel("Password").fill(E2E_USER_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("Welcome to Growixa")).toBeVisible();
  await expect(page.getByText("E2E Dashboard User")).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login$/);

  // the session is actually gone, not just a client-side navigation
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login$/);
});
