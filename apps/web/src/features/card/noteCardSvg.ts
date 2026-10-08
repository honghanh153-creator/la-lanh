import type { DailyNote, ShareFormat } from "../../shared/api/client";

type ShareableNote = Pick<DailyNote, "title" | "persona_label" | "persona_mode" | "reading_projection">;

export function shareCopy(note: ShareableNote) {
  const reading = note.reading_projection?.active;
  return {
    title: reading?.sections.hook ?? note.title,
    body: reading && reading.mode !== "vibe_fallback" ? reading.sections.manifestation : "",
    persona: `${(reading ? reading.mode !== "vibe_fallback" : note.persona_mode === "aura") ? "Aura" : "Vibe"} · ${note.persona_label}`,
  };
}

function escapeXml(value: string) {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function lines(value: string, max: number) {
  return value.split(/\s+/).filter(Boolean).reduce<string[]>((result, word) => {
    const last = result.at(-1);
    if (!last || `${last} ${word}`.length > max) result.push(word);
    else result[result.length - 1] = `${last} ${word}`;
    return result;
  }, []);
}

export function cardSvg(note: ShareableNote, format: ShareFormat) {
  const copy = shareCopy(note);
  const height = format === "square_1_1" ? 1080 : 1920;
  const title = lines(copy.title, 30);
  const body = lines(copy.body, 48);
  const usable = height - 440;
  // Fit all supplied words; never silently cut the end of the note.
  const scale = Math.min(1, usable / (title.length * 76 + body.length * 48 + 56));
  const titleSize = 60 * scale;
  const bodySize = 34 * scale;
  const titleY = 330;
  const bodyY = titleY + title.length * 76 * scale + 30;
  const text = (rows: string[], y: number, size: number, step: number, weight: number) => `<text x="120" y="${y}" fill="#fff9e9" font-family="Be Vietnam Pro, sans-serif" font-size="${size}" font-weight="${weight}">${rows.map((row, i) => `<tspan x="120" dy="${i ? step : 0}">${escapeXml(row)}</tspan>`).join("")}</text>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="${height}" viewBox="0 0 1080 ${height}">
    <rect width="1080" height="${height}" fill="#f7f4eb"/>
    <text x="70" y="120" fill="#15132c" font-family="Be Vietnam Pro, sans-serif" font-size="64" font-weight="800">Lá Lành<tspan fill="#54249b">*</tspan></text>
    <rect x="60" y="180" width="960" height="${height - 250}" rx="48" fill="#47258c"/>
    <text x="120" y="250" fill="#dfff4f" font-family="Be Vietnam Pro, sans-serif" font-size="28">${escapeXml(copy.persona)}</text>
    ${text(title, titleY, titleSize, 76 * scale, 800)}
    ${body.length ? text(body, bodyY, bodySize, 48 * scale, 400) : ""}
    <text x="120" y="${height - 115}" fill="#fff9e9" font-family="Be Vietnam Pro, sans-serif" font-size="24">Một góc nhìn cho hôm nay · không kèm dữ liệu sinh</text>
  </svg>`;
}
