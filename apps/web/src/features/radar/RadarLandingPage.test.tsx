import { readFileSync } from "node:fs";
import { join } from "node:path";

import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { RadarLandingPage } from "./RadarLandingPage";

describe("RadarLandingPage", () => {
  it("explains private pair matching without promising a discovery pool", () => {
    render(<MemoryRouter><RadarLandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "Xem hai bạn hợp nhau ở đâu." })).toBeInTheDocument();
    expect(screen.getByText(/chỉ nhập thông tin sinh khi đã được người ấy cho phép/)).toBeInTheDocument();
    expect(screen.getByText(/Không gửi link, không tạo hồ sơ/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Xem hợp gu với một người" })).toHaveAttribute("href", "/radar/start");
    expect(screen.queryByRole("navigation", { name: "Tiến độ Radar" })).not.toBeInTheDocument();
    expect(screen.queryByText(/năm lá úp/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Một bậc có tên kèm lý do, vài mảng hợp hoặc cần để ý/)).toBeVisible();
    expect(screen.queryByText(/Không phần trăm hợp nhau/)).not.toBeInTheDocument();
  });

  // Journey review 20.11: English and jargon on the landing scored Radar 3/5 for clarity.
  it("speaks plain Vietnamese outside the owner-only privacy copy", () => {
    render(<MemoryRouter><RadarLandingPage /></MemoryRouter>);

    expect(document.body.textContent).not.toMatch(/Check|chart|Radar|bắt sóng|rung động|lệch sóng|vào gu/);
    // The privacy copy keeps its approved wording until the owner approves a rewrite.
    expect(screen.getByText("“Kín” không có nghĩa là dùng lén dữ liệu")).toBeInTheDocument();
    expect(screen.getByText(/Ngày, giờ và nơi sinh chỉ dùng trong lúc tính/)).toBeInTheDocument();
    expect(screen.getByText(/mà không cần nhắn hay báo cho người ấy/)).toBeInTheDocument();
  });

  it("offers two clearly different ways back to old results", () => {
    render(<MemoryRouter><RadarLandingPage /></MemoryRouter>);

    const history = screen.getByRole("navigation", { name: "Xem lại kết quả" });
    const links = within(history).getAllByRole("link");
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAccessibleName("Người bạn đã xem Mở lại kết quả cũ");
    expect(links[0]).toHaveAttribute("href", "/radar/start#radar-history");
    expect(links[1]).toHaveAccessibleName("Kết quả bạn đã nhận Khi có người mời bạn");
    expect(links[1]).toHaveAttribute("href", "/radar/received");
    for (const link of links) expect(link).toHaveClass("radar-history-link");
  });

  it("gives each history link a tap target of at least 44 px", () => {
    const css = readFileSync(join(process.cwd(), "src/features/radar/radar.css"), "utf8");
    const rule = css.match(/^\.radar-history-link \{([^}]*)\}/m)?.[1] ?? "";

    expect(rule).toMatch(/min-height: 2\.75rem/);
    expect(rule).toMatch(/display: grid/);
    expect(css).toMatch(/^\.radar-landing-history \{[^}]*grid-template-columns/m);
  });
});
