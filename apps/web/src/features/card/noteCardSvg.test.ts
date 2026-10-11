import { describe, expect, it } from "vitest";

import { birthArtSpec } from "./birthCardArt";
import { cardSvg, noteArtSpec, shareCopy } from "./noteCardSvg";
import { buildShareArtSvg, estimateWidth, fitText, shareArtAlt, shareTextPairs, shareThemes } from "./shareArt";

const visibleText = (svg: string) => svg.replace(/<style>[\s\S]*?<\/style>/, " ").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ");

describe("note card export", () => {
  const note = { title: "Bạn định gửi rồi, nhưng lại sửa thêm.", persona_mode: "vibe", persona_label: "Mộng" } as const;

  it("renders story and square canvases in the brand palette", () => {
    expect(cardSvg(note, "square_1_1")).toContain('height="1080"');
    const story = cardSvg(note, "story_9_16");
    expect(story).toContain('height="1920"');
    for (const color of ["#4b278f", "#fff9e9", "#dfff4f"]) expect(story).toContain(color);
  });

  it("uses a plain persona tag and element sticker instead of Vibe/Aura jargon", () => {
    const text = visibleText(cardSvg(note, "story_9_16"));
    expect(text).toContain("Chất Mộng · Nước");
    expect(text).not.toMatch(/Vibe|Aura/);
    expect(shareCopy(note).tag).toBe("Chất Mộng");
  });

  it("keeps the end of a long title instead of cutting it", () => {
    for (const format of ["square_1_1", "story_9_16"] as const) {
      const svg = cardSvg({ ...note, title: `${"Một câu đủ dài để thử xuống dòng. ".repeat(7)}ĐOẠN CUỐI` }, format);
      expect(visibleText(svg)).toMatch(/ĐOẠN\s+CUỐI/);
    }
  });

  it("shows at most one supporting line", () => {
    const svg = buildShareArtSvg(noteArtSpec({ title: "Tiêu đề", body: "Một câu hỗ trợ.", personaLabel: "Nóng" }), "story_9_16");
    expect(svg.match(/class="sup"/g)).toHaveLength(1);
    expect(visibleText(svg)).toContain("Một câu hỗ trợ.");
  });

  it("escapes content and excludes unrelated private data", () => {
    const privateInput = { ...note, title: "<script> & câu thử", birth_date: "1990-03-15" };
    const svg = cardSvg(privateInput, "square_1_1");
    expect(svg).toContain("&lt;script&gt;");
    expect(svg).toContain("&amp;");
    expect(svg).not.toContain("<script>");
    expect(svg).not.toContain("1990-03-15");
  });

  it("strips control and bidi characters from shared text", () => {
    const svg = cardSvg({ ...note, title: `Câu${String.fromCharCode(0x202e)} đảo${String.fromCharCode(0)} chiều` }, "square_1_1");
    expect(svg).not.toContain(String.fromCharCode(0x202e));
    expect(svg).not.toContain(String.fromCharCode(0));
    expect(visibleText(svg)).toContain("Câu đảo chiều");
  });
});

describe("birth card export", () => {
  // A full profile-shaped sample: only sign + persona label may reach the image.
  const profile = {
    birth_date: "1996-06-01",
    birth_time: "07:45",
    birth_place: "Hải Phòng, Việt Nam",
    latitude: 20.8449,
    longitude: 106.6881,
    email: "someone@example.com",
    id: "00000000-0000-4000-8000-0000000000aa",
    sign: "gemini" as const,
    persona_label: "Lanh",
  };

  it("shows the sign glyph sticker and identity line with the privacy footer", () => {
    for (const format of ["story_9_16", "square_1_1"] as const) {
      const spec = birthArtSpec(profile.sign, profile.persona_label);
      const text = visibleText(buildShareArtSvg(spec, format));
      expect(text).toContain("Mặt Trời Song Tử · Khí");
      expect(text).toContain("Không kèm ngày / giờ / nơi sinh");
      expect(text).not.toMatch(/Vibe|Aura|GÓC NHÌN|NGUỒN ĐỌC|ĐIỂM DỄ MỆT/i);
    }
  });

  it("never contains birth date, time, place, coordinates, email or ids", () => {
    const spec = birthArtSpec(profile.sign, profile.persona_label);
    const outputs = (["story_9_16", "square_1_1"] as const).flatMap((format) => [buildShareArtSvg(spec, format), shareArtAlt(spec, format)]);
    for (const output of outputs) {
      for (const secret of ["1996", "06-01", "01/06", "07:45", "Hải Phòng", "20.84", "106.68", "@example.com", "0000-4000"]) {
        expect(output).not.toContain(secret);
      }
    }
  });
});

describe("share art layout", () => {
  it("shrinks text to fit the box without dropping words", () => {
    const text = "Một đoạn chữ rất dài ".repeat(20).trim();
    const fit = fitText(text, { width: 900, height: 300, max: 100, min: 40, maxLines: 3, leading: 1.14, weight: 800 });
    expect(fit.height).toBeLessThanOrEqual(300);
    expect(fit.lines.join(" ")).toBe(text);
    for (const line of fit.lines) expect(estimateWidth(line, fit.size, 800)).toBeLessThanOrEqual(900);
  });

  it("keeps the largest size for short hooks", () => {
    expect(fitText("Chậm mà chắc.", { width: 900, height: 400, max: 128, min: 56, maxLines: 3, leading: 1.14, weight: 800 }).size).toBe(128);
  });

  it("keeps every text colour pair at WCAG AA contrast, including the element glow", () => {
    const luminance = (hex: string) => {
      const channels = [1, 3, 5].map((index) => parseInt(hex.slice(index, index + 2), 16) / 255);
      const [r, g, b] = channels.map((value) => (value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4));
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const ratio = (a: string, b: string) => {
      const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
      return (hi + 0.05) / (lo + 0.05);
    };
    const blend = (fg: string, bg: string, alpha: number) =>
      `#${[1, 3, 5].map((index) => Math.round(parseInt(fg.slice(index, index + 2), 16) * alpha + parseInt(bg.slice(index, index + 2), 16) * (1 - alpha)).toString(16).padStart(2, "0")).join("")}`;
    for (const pair of shareTextPairs) expect(ratio(pair.fg, pair.bg), pair.use).toBeGreaterThanOrEqual(4.5);
    // Text sits outside the strongest part of the glow; check a generous 25 % tint anyway.
    for (const theme of Object.values(shareThemes)) expect(ratio("#fff9e9", blend(theme.glow, "#4b278f", 0.25))).toBeGreaterThanOrEqual(4.5);
  });
});
