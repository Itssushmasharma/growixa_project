import { expect, test } from "@playwright/test";

test("root route responds and renders the app", async ({ page }) => {
  const response = await page.goto("/");
  expect(response?.status()).toBe(200);
  await expect(page.getByRole("heading", { name: "Growixa" })).toBeVisible();
});
