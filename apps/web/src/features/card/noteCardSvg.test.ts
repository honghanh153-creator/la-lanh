import { describe, expect, it } from "vitest";
import { cardSvg } from "./noteCardSvg";

describe("note card export", () => {
  const note = { title: "Bạn định gửi rồi, nhưng lại sửa thêm.", persona_mode: "vibe", persona_label: "Mộng" } as const;

  it("uses the chosen cream and violet palette for square and story", () => {
    expect(cardSvg(note, "square_1_1")).toContain('height="1080"');
    const story = cardSvg(note, "story_9_16");
    expect(story).toContain('height="1920"');
    expect(story).toContain('#f7f4eb');
    expect(story).toContain('#47258c');
  });

  it("keeps the end of a long title instead of cutting after three lines", () => {
    const svg = cardSvg({ ...note, title: `${"Một câu đủ dài để thử xuống dòng. ".repeat(7)}ĐOẠN CUỐI` }, "square_1_1");
    expect(svg.replace(/<[^>]*>/g, " ")).toMatch(/ĐOẠN\s+CUỐI/);
  });

  it("escapes content and excludes unrelated private data", () => {
    const privateInput = { ...note, title: "<script> & câu thử", birth_date: "1990-03-15" };
    const svg = cardSvg(privateInput, "square_1_1");
    expect(svg).toContain('&lt;script&gt;');
    expect(svg).toContain('&amp;');
    expect(svg).not.toContain("1990-03-15");
  });
});
