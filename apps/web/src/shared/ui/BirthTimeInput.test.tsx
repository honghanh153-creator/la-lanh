import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import type { ApproxWindow, BirthTimeMode } from "../api/client";
import { BirthTimeInput } from "./BirthTimeInput";

function Example() {
  const [mode, setMode] = useState<BirthTimeMode>("exact");
  const [time, setTime] = useState("");
  const [window, setWindow] = useState<ApproxWindow>("morning");
  return <BirthTimeInput mode={mode} onModeChange={setMode} time={time} onTimeChange={setTime} window={window} onWindowChange={setWindow} />;
}

describe("BirthTimeInput", () => {
  it("shares exact/approximate/unknown controls without guessing time", async () => {
    const user = userEvent.setup();
    render(<Example />);
    expect(screen.getByRole("button", { name: "Biết giờ" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByLabelText("Giờ (0–23)")).toHaveValue("");
    await user.click(screen.getByRole("button", { name: "Nhớ khoảng" }));
    expect(screen.queryByLabelText("Giờ (0–23)")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Chiều 14–18h" }));
    expect(screen.getByRole("button", { name: "Chiều 14–18h" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Chưa biết" }));
    expect(screen.getByText("Không đoán giờ sinh. Bạn có thể thêm sau.")).toBeInTheDocument();
  });

  it("does not expose approximate time to an API which does not support it", () => {
    render(<BirthTimeInput mode="unknown" onModeChange={vi.fn()} time="" onTimeChange={vi.fn()} modes={["exact", "unknown"]} />);
    expect(screen.queryByRole("button", { name: "Nhớ khoảng" })).not.toBeInTheDocument();
  });

  it("inherits disabled form state, including precision controls", () => {
    render(<fieldset disabled><Example /></fieldset>);
    expect(screen.getByRole("button", { name: "Nhớ khoảng" })).toBeDisabled();
    expect(screen.getByLabelText("Phút (0–59)")).toBeDisabled();
  });
});
