import { expect, test } from "@playwright/test";

const reveal = {
  profile_id: "profile-test",
  snapshot_id: "snapshot-test",
  birth_date: "1990-01-01",
  calculation: {
    status: "certain",
    sign: "capricorn",
    candidates: [],
    provenance: {
      engine: "swiss_ephemeris",
      version: "2.10.3",
      ephemeris_set: "sepl_18+semo_18+seas_18",
      profile: "natal-date-only-v1",
    },
  },
  created_at: "2026-08-31T00:00:00Z",
  resumed: false,
};

test("guest can reveal, save mood, and create a share card", async ({ page }) => {
  await page.route("**/v1/session", async (route) => {
    await route.fulfill({ status: 401, json: { code: "GUEST_SESSION_MISSING" } });
  });
  await page.route("**/v1/guest-sessions", async (route) => {
    await route.fulfill({
      status: 201,
      headers: { "set-cookie": "la_lanh_csrf=csrf-test; Path=/; SameSite=Lax" },
      json: {
        state: "active",
        onboarding_status: "birth_pending",
        expires_at: "2026-09-30T00:00:00Z",
        csrf_token: "csrf-test",
        resumed: false,
      },
    });
  });
  await page.route("**/v1/birth-profile", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({ status: 201, json: reveal });
      return;
    }
    await route.fulfill({ status: 200, json: reveal });
  });

  await page.goto("/welcome");
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByRole("button", { name: "Bắt đầu" }).click();
  await expect(page).toHaveURL(/\/birth$/);

  await page.getByRole("textbox", { name: "Ngày" }).fill("01");
  await page.getByRole("textbox", { name: "Tháng" }).fill("01");
  await page.getByRole("textbox", { name: "Năm" }).fill("1990");
  await page.getByRole("checkbox", { name: "Tôi đã hiểu và đồng ý để Lá Lành xử lý ngày sinh cho mục đích này." }).check();
  await page.getByRole("button", { name: "Bật mí Lá của mình" }).click();

  await expect(page.getByRole("heading", { name: "Ma Kết" })).toBeVisible();
  await page.getByRole("button", { name: "Xem note hôm nay" }).click();

  await expect(page.getByRole("heading", { name: "Này bạn," })).toBeVisible();
  await page.getByRole("button", { name: "Chill" }).click();
  await expect(page.getByRole("button", { name: "Chill" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Lưu lại" }).click();
  await expect(page.getByRole("button", { name: "Đã lưu" })).toBeVisible();

  await page.getByRole("link", { name: "Chia sẻ" }).click();
  await expect(page.getByRole("heading", { name: "Ma Kết" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tải SVG" })).toBeEnabled();
});

test("child birth date is stopped before any personal data is sent", async ({ page }) => {
  let birthProfileRequests = 0;
  await page.route("**/v1/birth-profile", async (route) => {
    birthProfileRequests += 1;
    await route.fulfill({ status: 500, json: { code: "SHOULD_NOT_BE_CALLED" } });
  });

  await page.goto("/birth");
  await page.getByRole("textbox", { name: "Ngày" }).fill("01");
  await page.getByRole("textbox", { name: "Tháng" }).fill("01");
  await page.getByRole("textbox", { name: "Năm" }).fill("2020");
  await page.getByRole("checkbox", { name: "Tôi đã hiểu và đồng ý để Lá Lành xử lý ngày sinh cho mục đích này." }).check();
  await page.getByRole("button", { name: "Bật mí Lá của mình" }).click();

  await expect(page.getByRole("alert")).toContainText("dưới 16 tuổi");
  expect(birthProfileRequests).toBe(0);
});
