import { act, fireEvent, render, screen } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";

import { PrivatePortalContext } from "./privatePortal";
import { ResonanceFeedback } from "./ResonanceFeedback";

let setVisible: (visible: boolean) => void = () => {};

function Region({ children }: { children: ReactNode }) {
  const [visible, update] = useState(true);
  const [target, setTarget] = useState<HTMLElement | null>(null);
  setVisible = update;
  return <MemoryRouter>
    <div hidden={!visible}>
      <PrivatePortalContext.Provider value={{ target, visible }}>{children}</PrivatePortalContext.Provider>
      <div ref={setTarget} />
    </div>
  </MemoryRouter>;
}

it("puts focus back in the resonance consent dialog when the private region shows again", () => {
  render(<Region><ResonanceFeedback consented={false} onSubmit={vi.fn()} pending={false} selected={null} /></Region>);

  fireEvent.click(screen.getByRole("button", { name: "Trúng" }));
  const dialog = screen.getByRole("dialog");
  const close = screen.getByRole("button", { name: "Đóng" });
  expect(document.activeElement).toBe(close);

  act(() => { setVisible(false); });
  act(() => { close.blur(); });
  expect(document.activeElement).toBe(document.body);

  act(() => { setVisible(true); });
  expect(document.activeElement).toBe(close);
  fireEvent.keyDown(dialog, { key: "Escape" });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
