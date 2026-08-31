import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import { WelcomePage } from "./WelcomePage";

function renderPage() {
  return render(<MemoryRouter><WelcomePage /></MemoryRouter>);
}

describe("WelcomePage", () => {
  it("renders the preserved Electric Note welcome baseline", () => {
    renderPage();

    expect(screen.getByLabelText("Lá Lành")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Một lời nhắc đúng lúc." })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tiếp tục" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Bỏ qua giới thiệu" })).toBeInTheDocument();
  });

  it("moves to the second welcome message without requesting API data", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    renderPage();
    await user.click(screen.getByRole("button", { name: "Tiếp tục" }));

    expect(screen.getByRole("heading", { name: "Chỉ cần ngày sinh. Thế là đủ." })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Bắt đầu" })).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();

    fetchSpy.mockRestore();
  });
});
