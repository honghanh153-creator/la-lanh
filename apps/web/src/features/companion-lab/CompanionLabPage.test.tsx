import { fireEvent, render, screen, within } from "@testing-library/react";

import { CompanionLabPage } from "./CompanionLabPage";

function labels() {
  return screen.getAllByRole("img").map((node) => node.getAttribute("aria-label") ?? "");
}

describe("CompanionLabPage", () => {
  beforeEach(() => localStorage.clear());

  it("renders both prototypes side by side with Vietnamese controls", () => {
    render(<CompanionLabPage />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Bạn đồng hành lớn dần");
    expect(screen.getByRole("button", { name: "Chạm vào Mầm Aura" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Chạm vào cây trong cửa sổ trời" })).toBeInTheDocument();
    expect(screen.getByLabelText("Giờ trong ngày")).toBeInTheDocument();
    expect(screen.getByLabelText("Số ngày đã ghé")).toBeInTheDocument();
    expect(screen.getByLabelText("Lễ hội")).toBeInTheDocument();
  });

  it("drives the time of day, growth, vibe and festival preview", () => {
    render(<CompanionLabPage />);
    fireEvent.change(screen.getByLabelText("Giờ trong ngày"), { target: { value: "12" } });
    expect(labels().every((label) => label.includes("buổi trưa"))).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "23h" }));
    expect(labels().every((label) => label.includes("ban đêm"))).toBe(true);
    fireEvent.change(screen.getByLabelText("Số ngày đã ghé"), { target: { value: "120" } });
    expect(labels().every((label) => label.includes("cây lớn"))).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "12h" }));
    fireEvent.click(screen.getByLabelText("Roast 🔥"));
    expect(document.querySelectorAll('.lc-companion[data-vibe="roast"]')).toHaveLength(2);
    fireEvent.change(screen.getByLabelText("Lễ hội"), { target: { value: "trung-thu" } });
    expect(document.querySelectorAll('.lc-companion[data-festival="trung-thu"]')).toHaveLength(2);
  });

  it("previews reduced motion, shuffles the seed and stores nothing", () => {
    render(<CompanionLabPage />);
    fireEvent.click(screen.getByLabelText("Xem tĩnh (giảm chuyển động)"));
    expect(document.querySelectorAll('.lc-companion[data-cmotion="still"]')).toHaveLength(2);
    const seed = screen.getByText(/^[0-9a-f]{8}$/).textContent;
    fireEvent.click(screen.getByRole("button", { name: "Đổi seed" }));
    expect(screen.getByText(/^[0-9a-f]{8}$/).textContent).not.toBe(seed);
    fireEvent.click(screen.getByRole("button", { name: "Chạm vào Mầm Aura" }));
    expect(screen.getByText("đã chạm 1 lần")).toBeInTheDocument();
    expect(localStorage.length).toBe(0);
  });

  it("shows a still matrix of hours and growth levels", () => {
    render(<CompanionLabPage />);
    fireEvent.click(screen.getByLabelText("Bảng xem nhanh"));
    expect(within(screen.getByRole("region", { name: "Bảng xem nhanh theo giờ và số ngày" })).getAllByRole("table")).toHaveLength(2);
    expect(document.querySelectorAll('.clab__matrix .lc-companion[data-cmotion="still"]')).toHaveLength(40);
  });

  it("shows the Lá pixel trial with its four moves, timings and the still preview (#714, #715)", () => {
    render(<CompanionLabPage />);
    const pixel = screen.getByRole("region", { name: "Lá pixel, bản thử" });
    expect(within(pixel).getByText("bản thử, chưa bật cho người dùng")).toBeInTheDocument();
    for (const name of ["Chào", "Ngồi cùng", "Kính rơi", "Uống trà"]) {
      expect(within(pixel).getByRole("rowheader", { name })).toBeInTheDocument();
    }
    fireEvent.click(within(pixel).getByRole("button", { name: "Ngồi cùng" }));
    const la = within(pixel).getByRole("button", { name: "Lá pixel, bấm để chạy động tác Ngồi cùng" });
    expect(la).toHaveAttribute("data-move", "ngoi-cung");
    fireEvent.click(screen.getByLabelText("Xem tĩnh (giảm chuyển động)"));
    expect(la).toHaveAttribute("data-motion", "still");
    expect(localStorage.length).toBe(0);
  });
});
