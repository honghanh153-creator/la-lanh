import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { AppSheet } from "./AppSheet";

function Harness({ closeDisabled = false }: { closeDisabled?: boolean }) {
  const [open, setOpen] = useState(false);
  return <>
    <button onClick={() => setOpen(true)} type="button">Mở lựa chọn</button>
    <AppSheet closeDisabled={closeDisabled} onClose={() => setOpen(false)} open={open} title="Chọn một góc">
      <button type="button">Đầu</button>
      <button type="button">Cuối</button>
    </AppSheet>
  </>;
}

describe("AppSheet", () => {
  it("opens as a named dialog and returns focus after closing", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const trigger = screen.getByRole("button", { name: "Mở lựa chọn" });

    await user.click(trigger);
    expect(screen.getByRole("dialog", { name: "Chọn một góc" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Đóng" })).toHaveFocus();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "Chọn một góc" })).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it("contains keyboard focus within the sheet", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "Mở lựa chọn" }));

    await user.keyboard("{Shift>}{Tab}{/Shift}");
    expect(screen.getByRole("button", { name: "Cuối" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("button", { name: "Đóng" })).toHaveFocus();
  });

  it("does not dismiss while a blocking action is pending", async () => {
    const user = userEvent.setup();
    render(<Harness closeDisabled />);
    await user.click(screen.getByRole("button", { name: "Mở lựa chọn" }));
    await user.keyboard("{Escape}");
    expect(screen.getByRole("dialog", { name: "Chọn một góc" })).toBeInTheDocument();
  });
});
