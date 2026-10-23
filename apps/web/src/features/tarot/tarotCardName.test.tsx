import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CardName } from "./TarotCardLabel";
import { cardName } from "./tarotCardName";

describe("card name (US-20 AC12, T04)", () => {
  it("pairs the traditional English title with the Vietnamese one", () => {
    expect(cardName({ title_en: "The Devil", title_vi: "Sợi Ràng" })).toBe("The Devil · Sợi Ràng");
    const { container } = render(<CardName card={{ title_en: "Death", title_vi: "Chuyển Mùa" }} />);
    expect(container).toHaveTextContent("Death · Chuyển Mùa");
    expect(container.querySelector("[lang='en']")).toHaveTextContent("Death");
  });

  it("does not repeat a title that is the same in both languages", () => {
    expect(cardName({ title_en: "", title_vi: "Ẩn Sĩ" })).toBe("Ẩn Sĩ");
    expect(cardName({ title_en: "Tarot", title_vi: "Tarot" })).toBe("Tarot");
  });
});
