import { expect, test } from "@playwright/test";

const heading = /Hiểu mình hơn\.|Bớt overthinking\./;

test("welcome stays usable at supported mobile widths", async ({ page }) => {
  for (const width of [320, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/welcome");

    await expect(page.getByLabel("Lá Lành")).toBeVisible();
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
    await expect(page.getByRole("button", { name: "Đồng ý & bắt đầu" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Đăng nhập" })).toBeVisible();
    await expect(page.getByText("Chỉ cần ngày sinh · Chưa cần tài khoản")).toBeVisible();
    await expect(page.getByRole("link", { name: "Xem chi tiết" })).toHaveAttribute("href", "/privacy");

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  }

  await page.setViewportSize({ width: 320, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/welcome");
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  await expect(page.getByRole("button", { name: "Đồng ý & bắt đầu" })).toBeVisible();
  const accessibilityLayout = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    heroAnimations: Array.from(document.querySelectorAll(".welcome-intro__hero *"))
      .map((element) => getComputedStyle(element).animationName)
      .filter((name) => name !== "none"),
  }));
  expect(accessibilityLayout.overflow).toBeLessThanOrEqual(0);
  expect(accessibilityLayout.heroAnimations).toEqual([]);
  await expect(page.getByRole("button", { name: /chuyển động/ })).toBeHidden();
});
