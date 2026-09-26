import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { RadarLandingPage } from "./RadarLandingPage";

describe("RadarLandingPage", () => {
  it("explains private pair matching without promising a discovery pool", () => {
    render(<MemoryRouter><RadarLandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "Check thử hai bạn bắt sóng ở đâu." })).toBeInTheDocument();
    expect(screen.getByText(/chỉ nhập thông tin sinh khi đã được người ấy cho phép/)).toBeInTheDocument();
    expect(screen.getByText(/Không gửi link, không tạo hồ sơ/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Check kín một người" })).toHaveAttribute("href", "/radar/start");
    expect(screen.getByRole("navigation", { name: "Tiến độ Radar" })).toBeInTheDocument();
    expect(screen.getByText("Bắt đầu").closest('[aria-current="step"]')).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Xem kết quả đã có" })).toHaveAttribute("href", "/radar/start#radar-history");
    expect(screen.queryByText(/năm lá úp/i)).not.toBeInTheDocument();
  });
});
