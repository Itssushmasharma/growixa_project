import { expect, test } from "@playwright/test";

test("an anonymous visitor to the root route sees the Growixa brand landing page", async ({
  page,
}) => {
  const response = await page.goto("/");
  expect(response?.status()).toBe(200);
  await expect(page.getByText("Grow Faster. Market Smarter.")).toBeVisible();
});
