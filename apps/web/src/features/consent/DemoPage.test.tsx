import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { DemoPage } from "./DemoPage";

describe("DemoPage", () => {
  it("opens privacy details rather than restarting onboarding", () => {
    render(<MemoryRouter initialEntries={["/demo"]}><Routes>
      <Route path="/demo" element={<DemoPage />} />
      <Route path="/privacy" element={<h1>Quyền dữ liệu</h1>} />
      <Route path="/consent" element={<h1>Bắt đầu</h1>} />
    </Routes></MemoryRouter>);

    fireEvent.click(screen.getByRole("button", { name: "Xem lại quyền riêng tư" }));

    expect(screen.getByRole("heading", { name: "Quyền dữ liệu" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Bắt đầu" })).not.toBeInTheDocument();
  });
});
