import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TarotCardArt, TarotCardBack } from "./TarotCardArt";
import { MAJOR_KEYS, RANKS, SUITS, tarotArtSpec, titleLines, type TarotArtInput } from "./tarotArtSpec";

const MAJOR_TITLES = [
  "Kẻ Khờ", "Pháp Sư", "Nữ Tư Tế", "Hoàng Hậu", "Hoàng Đế", "Người Giữ Nếp", "Người Tình", "Cỗ Xe",
  "Sức Mạnh", "Ẩn Sĩ", "Bánh Xe", "Công Lý", "Người Treo Ngược", "Chuyển Mùa", "Tiết Chế", "Sợi Ràng",
  "Tòa Tháp", "Ngôi Sao", "Mặt Trăng", "Mặt Trời", "Tiếng Gọi", "Thế Giới",
];
const majors: TarotArtInput[] = MAJOR_KEYS.map((key, index) => ({
  id: `major-${key}`, arcana: "major", title_vi: MAJOR_TITLES[index],
}));
const minors: TarotArtInput[] = SUITS.flatMap((suit) => RANKS.map((rank) => ({
  id: `${suit}-${rank}`, arcana: "minor" as const, suit, rank, title_vi: `${rank} ${suit}`,
})));

function normalized(html: string): string {
  return html.replace(/tc[ab][A-Za-z0-9_-]*?-(bg|glow|foil)/g, "ID-$1");
}

describe("TarotCardArt", () => {
  it("draws a distinct, labelled composition for each of the 22 major arcana", () => {
    const { container } = render(<>{majors.map((card) => <TarotCardArt card={card} key={card.id} />)}</>);
    const images = screen.getAllByRole("img");
    expect(images.map((image) => image.getAttribute("aria-label"))).toEqual(MAJOR_TITLES);
    const signatures = new Set(images.map((image) => image.getAttribute("data-art")));
    expect(signatures.size).toBe(22);
    expect(signatures.has("major:unknown")).toBe(false);
    const motifs = new Set([...container.querySelectorAll("svg")].map((svg) => normalized(svg.innerHTML)));
    expect(motifs.size).toBe(22);
    expect(majors.map((card) => tarotArtSpec(card).numeral)).toEqual([
      "0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
      "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI",
    ]);
  });

  it("gives all 56 minor arcana a distinct suit/rank composition on one deck colour", () => {
    const specs = minors.map((card) => tarotArtSpec(card));
    expect(new Set(specs.map((spec) => spec.signature)).size).toBe(56);
    const { container } = render(<>{minors.map((card) => <TarotCardArt card={card} key={card.id} />)}</>);
    expect(new Set([...container.querySelectorAll("svg")].map((svg) => normalized(svg.innerHTML))).size).toBe(56);
    expect(screen.getByRole("img", { name: "king swords" })).toHaveAttribute("data-art", "minor:swords:king");
    const wands = tarotArtSpec({ id: "wands-ace", arcana: "minor", suit: "wands", rank: "ace", title_vi: "Át Gậy" });
    const cups = tarotArtSpec({ id: "cups-ace", arcana: "minor", suit: "cups", rank: "ace", title_vi: "Át Cốc" });
    // One violet deck; suits differ by symbol colour, not background.
    expect(wands.palette.top).toBe(cups.palette.top);
    expect(wands.palette.accent).not.toBe(cups.palette.accent);
    const court = specs.filter((spec) => spec.kind === "minor" && spec.court).map((spec) => spec.signature);
    expect(court).toHaveLength(16);
  });

  it("derives suit and rank from the id when the API omits them", () => {
    expect(tarotArtSpec({ id: "pentacles-10", arcana: "minor", title_vi: "Mười Tiền" })).toMatchObject({
      kind: "minor", suit: "pentacles", rank: "10", pips: 10, numeral: "X",
    });
  });

  it("is deterministic: the same card always renders the same art", () => {
    const card = majors[17];
    const first = render(<TarotCardArt card={card} />).container.innerHTML;
    const second = render(<TarotCardArt card={card} />).container.innerHTML;
    expect(normalized(first)).toBe(normalized(second));
  });

  it("hides decorative art from assistive tech and drops the title band when compact", () => {
    const { container } = render(<TarotCardArt card={majors[9]} compact decorative />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("aria-hidden", "true");
    expect(svg).not.toHaveAttribute("role");
    expect(screen.queryByText("Ẩn Sĩ")).not.toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("wraps long Vietnamese titles onto two lines", () => {
    expect(titleLines("Người Treo Ngược")).toEqual(["Người Treo", "Ngược"]);
    expect(titleLines("Ẩn Sĩ")).toEqual(["Ẩn Sĩ"]);
  });
});

describe("TarotCardBack", () => {
  it("shows a mystical back with no numbers or text and is decorative by default", () => {
    const { container } = render(<TarotCardBack />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("aria-hidden", "true");
    expect(svg?.querySelectorAll("text")).toHaveLength(0);
    expect(svg?.textContent).toBe("");
  });
});
