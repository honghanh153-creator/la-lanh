import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { BirthTimePicker } from "./BirthTimePicker";

function Harness() {
  const [value, setValue] = useState("");
  return <><BirthTimePicker value={value} onChange={setValue} /><output data-testid="time">{value}</output></>;
}

describe("BirthTimePicker", () => {
  it("does not invent minutes when only an hour is selected", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.selectOptions(screen.getByLabelText("Giờ (0–23)"), "07");
    expect(screen.getByTestId("time")).toHaveTextContent("07:");
    expect(screen.getByLabelText("Phút (0–59)")).toHaveValue("");
    await user.selectOptions(screen.getByLabelText("Phút (0–59)"), "30");
    expect(screen.getByTestId("time")).toHaveTextContent("07:30");
  });

  it("supports midnight and clearing either field", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.selectOptions(screen.getByLabelText("Phút (0–59)"), "00");
    expect(screen.getByLabelText("Giờ (0–23)")).toHaveValue("");
    await user.selectOptions(screen.getByLabelText("Giờ (0–23)"), "00");
    expect(screen.getByTestId("time")).toHaveTextContent("00:00");
    await user.selectOptions(screen.getByLabelText("Giờ (0–23)"), "");
    expect(screen.getByTestId("time")).toHaveTextContent(":00");
  });
});
