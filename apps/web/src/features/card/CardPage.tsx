import { ArrowLeft, DownloadSimple, ShareNetwork } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { getBirthProfile } from "../../shared/api/client";
import { signDetails } from "../../shared/astro/signs";
import { BrandMark } from "../../shared/ui/BrandMark";

function cardSvg(label: string, symbol: string, note: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350">
  <rect width="1080" height="1350" rx="52" fill="#160620"/>
  <circle cx="900" cy="300" r="280" fill="#d8ff00"/><circle cx="820" cy="350" r="210" fill="#291135"/>
  <path d="M0 1030 L1080 850 L1080 1350 L0 1350Z" fill="#fff5df"/>
  <text x="72" y="105" fill="#160620" font-family="Arial Black" font-size="56"><tspan fill="#d8ff00">LÁ LÀNH*</tspan></text>
  <text x="80" y="400" fill="#fff5df" font-family="Arial" font-size="38" font-weight="700">MẶT TRỜI CỦA TÔI Ở</text>
  <text x="72" y="610" fill="#d8ff00" font-family="Arial Black" font-size="132">${label.toUpperCase()}</text>
  <text x="760" y="710" fill="#ff6d61" font-family="Arial" font-size="220">${symbol}</text>
  <text x="90" y="1030" fill="#160620" font-family="Arial" font-size="48" font-weight="700">${note}</text>
  <text x="90" y="1250" fill="#6a4776" font-family="Arial" font-size="30">Tính bằng Swiss Ephemeris thật · la-lanh</text>
  </svg>`;
}

function svgFile(label: string, symbol: string, note: string): File {
  return new File([cardSvg(label, symbol, note)], "la-khai-sinh.svg", { type: "image/svg+xml" });
}

export function CardPage() {
  const navigate = useNavigate();
  const query = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal) });
  const [message, setMessage] = useState<string | null>(null);
  const sign = query.data?.calculation.sign ?? query.data?.calculation.candidates[0];
  const detail = sign ? signDetails[sign] : null;

  const download = () => {
    if (!detail) return;
    const file = svgFile(detail.label, detail.symbol, detail.note);
    const url = URL.createObjectURL(file);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = file.name;
    anchor.click();
    URL.revokeObjectURL(url);
    setMessage("Card đã được tải về.");
  };

  const share = async () => {
    if (!detail) return;
    const file = svgFile(detail.label, detail.symbol, detail.note);
    if (navigator.canShare?.({ files: [file] })) {
      await navigator.share({ files: [file], title: `Lá Khai Sinh · ${detail.label}` });
      setMessage("Card đã sẵn sàng bay đi.");
    } else download();
  };

  return (
    <main className="flow-page card-page">
      <header className="flow-header"><button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><BrandMark /><span /></header>
      {detail ? <section className="share-card"><span className="share-card__logo">LÁ LÀNH*</span><p>MẶT TRỜI CỦA TÔI Ở</p><h1>{detail.label}</h1><span className="share-card__symbol">{detail.symbol}</span><blockquote>{detail.note}</blockquote><small>Tính bằng Swiss Ephemeris thật</small></section> : <p>Đang dựng card…</p>}
      {message ? <p className="success-message" role="status">{message}</p> : null}
      <footer className="flow-actions"><button className="electric-button" disabled={!detail} onClick={() => void share()} type="button"><ShareNetwork /> Chia sẻ card</button><button className="outline-button" disabled={!detail} onClick={() => void download()} type="button"><DownloadSimple /> Tải SVG</button></footer>
    </main>
  );
}
