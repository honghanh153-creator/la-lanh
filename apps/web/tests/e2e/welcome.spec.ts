import { expect, test } from "@playwright/test";

test("welcome keeps the Electric Note hierarchy at supported viewports", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByLabel("Lá Lành")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Một lời nhắc đúng lúc." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tiếp tục" })).toBeVisible();
  await expect(page.getByRole("main")).toHaveScreenshot("welcome-electric-note.png", {
    animations: "disabled",
  });
});
