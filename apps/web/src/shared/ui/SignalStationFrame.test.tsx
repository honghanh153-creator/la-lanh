import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Link, MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppShell } from "../../app/AppShell";
import ultravioletStyles from "../styles/ultraviolet.css?raw";
import { SignalStationFrame } from "./SignalStationFrame";

describe("SignalStationFrame", () => {
  afterEach(() => vi.restoreAllMocks());
  it("gives the reduced-motion preference priority over specific onboarding selectors", () => {
    const css = ultravioletStyles;
    const media = css.slice(css.lastIndexOf("@media (prefers-reduced-motion: reduce)"));
    expect(media).toContain("animation: none !important");
    expect(media).toContain("transition: none !important");
    expect(media).toContain(".signal-motion-toggle { display: none; }");
    expect(css).toContain("onboarding-planet-drift 6800ms ease-in-out infinite");
    expect(css).toContain('data-motion-paused="true"');
    expect(css).toContain("animation-play-state: paused");
  });

  it("pauses and resumes decoration without disabling the form or next action", async () => {
    const user = userEvent.setup();
    render(
      <SignalStationFrame act={1} titleId="title" actions={<button>Tiếp tục</button>}>
        <h1 id="title">Ngày sinh</h1>
        <label>Ngày<input inputMode="numeric" /></label>
      </SignalStationFrame>,
    );
    await user.click(screen.getByRole("button", { name: "Tạm dừng chuyển động" }));
    expect(screen.getByRole("main")).toHaveAttribute("data-motion-paused", "true");
    await user.type(screen.getByRole("textbox", { name: "Ngày" }), "15");
    expect(screen.getByRole("textbox", { name: "Ngày" })).toHaveValue("15");
    expect(screen.getByRole("button", { name: "Tiếp tục" })).toBeEnabled();
    await user.click(screen.getByRole("button", { name: "Tiếp tục chuyển động" }));
    expect(screen.getByRole("main")).toHaveAttribute("data-motion-paused", "false");
  });

  it("keeps pause active after navigating between onboarding steps", async () => {
    vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/welcome"]}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/welcome" element={
              <SignalStationFrame act={0} titleId="welcome" actions={<Link to="/birth">Tiếp tục</Link>}>
                <h1 id="welcome">Bắt đầu</h1>
              </SignalStationFrame>
            } />
            <Route path="/birth" element={
              <SignalStationFrame act={1} titleId="birth" actions={<Link to="/reveal">Mở lá</Link>}>
                <h1 id="birth">Ngày sinh</h1>
              </SignalStationFrame>
            } />
            <Route path="/reveal" element={
              <SignalStationFrame act={2} titleId="reveal"><h1 id="reveal">Lá đầu tiên</h1></SignalStationFrame>
            } />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    await user.click(screen.getByRole("button", { name: "Tạm dừng chuyển động" }));
    await user.click(screen.getByRole("link", { name: "Tiếp tục" }));
    expect(screen.getByRole("main")).toHaveAttribute("data-motion-paused", "true");
    await user.click(screen.getByRole("link", { name: "Mở lá" }));
    expect(screen.getByRole("heading", { name: "Lá đầu tiên" })).toBeVisible();
    expect(screen.getByRole("main")).toHaveAttribute("data-motion-paused", "true");
    await user.click(screen.getByRole("button", { name: "Tiếp tục chuyển động" }));
    expect(screen.getByRole("main")).toHaveAttribute("data-motion-paused", "false");
  });

  it("keeps content and actions available immediately at every step", () => {
    const { rerender } = render(
      <SignalStationFrame act={0} titleId="title" actions={<button>Tiếp tục</button>}>
        <h1 id="title">Bắt đầu</h1>
      </SignalStationFrame>,
    );
    for (const act of [0, 1, 2] as const) {
      rerender(
        <SignalStationFrame act={act} titleId="title" actions={<button>Tiếp tục</button>}>
          <h1 id="title">Bắt đầu</h1>
        </SignalStationFrame>,
      );
      expect(screen.getByRole("heading", { name: "Bắt đầu" })).toBeVisible();
      expect(screen.getByRole("button", { name: "Tiếp tục" })).toBeEnabled();
      expect(screen.getByLabelText(new RegExp(`bước ${act + 1} trên 3`))).toBeVisible();
      expect(document.querySelector(".signal-station__art")).toHaveAttribute("aria-hidden", "true");
      expect(screen.getByRole("main")).not.toHaveAttribute("aria-busy");
    }
  });

  it("marks only real request loading as busy, without removing the action", () => {
    render(
      <SignalStationFrame act={2} loading titleId="title" actions={<button disabled>Đang mở</button>}>
        <h1 id="title">Đang tải</h1>
      </SignalStationFrame>,
    );
    expect(screen.getByRole("main")).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("button", { name: "Đang mở" })).toBeDisabled();
  });
});
