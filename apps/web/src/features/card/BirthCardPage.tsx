import { ArrowLeft, DownloadSimple, ShareNetwork } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { getBirthProfile, getDailyNote, updateOnboardingStatus, type ZodiacSign } from "../../shared/api/client";
import { primarySunSign } from "../../shared/astro/chart";
import { signDetails } from "../../shared/astro/signs";
import { BrandMark } from "../../shared/ui/BrandMark";

const elementBySign: Record<ZodiacSign, string> = {
  aries: "Lửa", leo: "Lửa", sagittarius: "Lửa",
  taurus: "Đất", virgo: "Đất", capricorn: "Đất",
  gemini: "Khí", libra: "Khí", aquarius: "Khí",
  cancer: "Nước", scorpio: "Nước", pisces: "Nước",
};

function safeSvg(label: string, symbol: string, persona: string, format: "story" | "square"): string {
  const height = format === "story" ? 1920 : 1080;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="${height}" viewBox="0 0 1080 ${height}">
  <rect width="1080" height="${height}" fill="#160620"/><circle cx="880" cy="250" r="260" fill="#d8ff00"/>
  <rect x="80" y="70" width="360" height="110" rx="10" fill="#d8ff00"/><text x="115" y="148" fill="#160620" font-family="Be Vietnam Pro,sans-serif" font-size="72" font-weight="900">Lá Lành*</text>
  <rect x="75" y="${format === "story" ? 430 : 250}" width="930" height="650" rx="35" fill="#fff5df"/>
  <text x="145" y="${format === "story" ? 590 : 410}" fill="#160620" font-family="Be Vietnam Pro,sans-serif" font-size="54">LÁ KHAI SINH · LỚP ĐẦU</text>
  <text x="145" y="${format === "story" ? 790 : 610}" fill="#5a286d" font-family="Be Vietnam Pro,sans-serif" font-size="150">${symbol}</text>
  <text x="310" y="${format === "story" ? 785 : 605}" fill="#160620" font-family="Be Vietnam Pro,sans-serif" font-size="92" font-weight="900">${persona}</text>
  <text x="145" y="${format === "story" ? 900 : 720}" fill="#5a286d" font-family="Be Vietnam Pro,sans-serif" font-size="35">Nguồn: Mặt Trời ${label}</text>
  <text x="145" y="${format === "story" ? 975 : 795}" fill="#160620" font-family="Be Vietnam Pro,sans-serif" font-size="38">Một phần bản đồ của bạn — không phải chiếc hộp định nghĩa bạn.</text>
  <text x="80" y="${height - 90}" fill="#d8ff00" font-family="Be Vietnam Pro,sans-serif" font-size="32">Không kèm ngày / giờ / nơi sinh · la-lanh</text></svg>`;
}

async function pngFile(label: string, symbol: string, persona: string, format: "story" | "square"): Promise<File> {
  const svg = new File([safeSvg(label, symbol, persona, format)], "la-khai-sinh.svg", { type: "image/svg+xml" });
  const sourceUrl = URL.createObjectURL(svg);
  try {
    const image = new Image();
    image.decoding = "async";
    image.src = sourceUrl;
    await image.decode();
    const canvas = document.createElement("canvas");
    canvas.width = 1080;
    canvas.height = format === "story" ? 1920 : 1080;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Canvas is not available");
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((value) => value ? resolve(value) : reject(new Error("PNG render failed")), "image/png", 0.92);
    });
    return new File([blob], `la-khai-sinh-${format}.png`, { type: "image/png" });
  } finally {
    URL.revokeObjectURL(sourceUrl);
  }
}

export function BirthCardPage() {
  const navigate = useNavigate();
  const [format, setFormat] = useState<"story" | "square">("story");
  const [message, setMessage] = useState<string | null>(null);
  const query = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal) });
  const noteQuery = useQuery({ queryKey: ["daily-note"], queryFn: ({ signal }) => getDailyNote(signal) });
  const sign = query.data ? primarySunSign(query.data.calculation) : null;
  const detail = sign ? signDetails[sign] : null;

  const persona = noteQuery.data
    ? `${noteQuery.data.persona_mode === "aura" ? "Aura" : "Vibe"} · ${noteQuery.data.persona_label}`
    : "Lá đầu tiên";
  const file = () => pngFile(detail!.label, detail!.symbol, persona, format);
  const download = async () => {
    if (!detail) return;
    try {
      const asset = await file();
      const url = URL.createObjectURL(asset);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = asset.name;
      anchor.click();
      URL.revokeObjectURL(url);
      setMessage("Đã tải Lá Khai Sinh dạng PNG. Card không kèm dữ liệu sinh.");
    } catch {
      setMessage("Chưa dựng được ảnh PNG. Preview vẫn được giữ để bạn thử lại.");
    }
  };
  const share = async () => {
    if (!detail) return;
    try {
      const asset = await file();
      if (navigator.canShare?.({ files: [asset] })) {
        await navigator.share({ files: [asset], title: `Lá Khai Sinh · ${detail.label}` });
        setMessage("Lá đã sẵn sàng bay đi.");
      } else await download();
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") setMessage("Bạn đã đóng bảng chia sẻ. Card vẫn còn nguyên.");
      else setMessage("Chưa chia sẻ được. Bạn có thể tải card và gửi thủ công.");
    }
  };

  return (
    <main className="flow-page card-page">
      <header className="flow-header"><button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><BrandMark /><span /></header>
      <section className="format-toggle" aria-label="Định dạng Lá Khai Sinh">
        <button aria-pressed={format === "story"} className={format === "story" ? "is-active" : ""} onClick={() => setFormat("story")} type="button">Story 9:16</button>
        <button aria-pressed={format === "square"} className={format === "square" ? "is-active" : ""} onClick={() => setFormat("square")} type="button">Square 1:1</button>
      </section>
      {detail && sign ? <section className={format === "square" ? "share-card birth-share-card share-card--square" : "share-card birth-share-card"} aria-label={`Lá Khai Sinh Mặt Trời ${detail.label}`}>
        <span className="share-card__logo">LÁ LÀNH*</span><p>Lá Khai Sinh · lớp đầu tiên</p>
        <div className="birth-card-sign"><span>{detail.symbol}</span><h1>{noteQuery.data ? `${noteQuery.data.persona_mode === "aura" ? "Aura" : "Vibe"} · ${noteQuery.data.persona_label}` : "Lá đầu tiên"}</h1></div>
        <dl><div><dt>Góc nhìn tổng quan</dt><dd>{detail.note}</dd></div><div><dt>Nguồn đọc</dt><dd>Mặt Trời {detail.label} · nguyên tố {elementBySign[sign]}.</dd></div><div><dt>Điểm dễ mệt</dt><dd>Khi cố sống theo nhịp không thuộc về mình.</dd></div><div><dt>Lời nhắn</dt><dd>Đây là một phần bản đồ, không phải chiếc hộp định nghĩa bạn.</dd></div></dl>
        <small>Không kèm ngày / giờ / nơi sinh</small>
      </section> : <section className="entry-loading"><span className="entry-loading__orbit" /><p>Đang dựng Lá Khai Sinh…</p></section>}
      {message ? <p className="success-message" role="status">{message}</p> : null}
      <footer className="flow-actions"><button className="electric-button" disabled={!detail} onClick={() => void share()} type="button"><ShareNetwork /> Chia sẻ</button><button className="outline-button" disabled={!detail} onClick={() => void download()} type="button"><DownloadSimple /> Tải PNG</button><button className="text-button" onClick={() => void updateOnboardingStatus("completed").finally(() => navigate("/home"))} type="button">Để sau, vào app</button></footer>
    </main>
  );
}
