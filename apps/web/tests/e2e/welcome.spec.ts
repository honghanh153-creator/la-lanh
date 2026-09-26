import { expect, test } from "@playwright/test";

test("Trạm Bắt Sóng welcome stays usable at supported mobile widths", async ({ page }) => {
  for (const width of [320, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/welcome");

    await expect(page.getByLabel("Lá Lành")).toBeVisible();
    await expect(page.getByText("TRẠM BẮT SÓNG · 00/02")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Có một tín hiệu đã đi cùng bạn từ ngày bạn xuất hiện." })).toBeVisible();
    await expect(page.getByRole("button", { name: "Đồng ý & bật tín hiệu" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Xem bản mẫu" })).toBeVisible();

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  }

  await page.setViewportSize({ width: 320, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/welcome");
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  await expect(page.getByRole("heading", { name: "Có một tín hiệu đã đi cùng bạn từ ngày bạn xuất hiện." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Đồng ý & bật tín hiệu" })).toBeVisible();
  const accessibilityLayout = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    transition: getComputedStyle(document.querySelector(".signal-progress__fill")!).transitionDuration,
  }));
  expect(accessibilityLayout.overflow).toBeLessThanOrEqual(0);
  expect(Number.parseFloat(accessibilityLayout.transition)).toBeLessThanOrEqual(0.001);
});
