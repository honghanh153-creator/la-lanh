import { ArrowLeft, DownloadSimple, ShareNetwork } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getBirthProfile, getDailyNote, updateOnboardingStatus, type ShareFormat } from "../../shared/api/client";
import { primarySunSign } from "../../shared/astro/chart";
import { signDetails } from "../../shared/astro/signs";
import { BrandMark } from "../../shared/ui/BrandMark";
import { birthArtSpec } from "./birthCardArt";
import { shareArtAlt } from "./shareArt";
import { ShareArtPreview } from "./ShareArtPreview";
import { useShareArt } from "./useShareArt";

export function BirthCardPage() {
  const navigate = useNavigate();
  const [format, setFormat] = useState<ShareFormat>("story_9_16");
  const [message, setMessage] = useState<string | null>(null);
  const query = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal) });
  const noteQuery = useQuery({ queryKey: ["daily-note"], queryFn: ({ signal }) => getDailyNote(signal) });
  const sign = query.data ? primarySunSign(query.data.calculation) : null;
  const detail = sign ? signDetails[sign] : null;
  // Wait for the persona tag (or its failure) so the card does not visibly swap labels.
  const personaLabel = noteQuery.data?.persona_label ?? null;
  const spec = useMemo(() => (sign && !noteQuery.isPending ? birthArtSpec(sign, personaLabel) : null), [sign, noteQuery.isPending, personaLabel]);
  const art = useShareArt(spec, format);
  const file = () => art.pngFile(`la-khai-sinh-${format === "story_9_16" ? "story" : "square"}.png`);
  const download = async () => {
    if (!detail || !art.ready) return;
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
    if (!detail || !art.ready) return;
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
        <button aria-pressed={format === "story_9_16"} className={format === "story_9_16" ? "is-active" : ""} onClick={() => setFormat("story_9_16")} type="button">Story 9:16</button>
        <button aria-pressed={format === "square_1_1"} className={format === "square_1_1" ? "is-active" : ""} onClick={() => setFormat("square_1_1")} type="button">Square 1:1</button>
      </section>
      {spec && detail ? <>
        <ShareArtPreview alt={shareArtAlt(spec, format)} format={format} heading={`Lá Khai Sinh · Mặt Trời ${detail.label}`} svg={art.svg} />
        <p className="share-art-privacy">Không kèm ngày / giờ / nơi sinh</p>
      </> : query.isError ? <section className="empty-state">
        <p role="alert">Chưa tải được Lá Khai Sinh.</p>
        <button className="outline-button" disabled={query.isFetching} onClick={() => void query.refetch()} type="button">Thử lại</button>
      </section> : query.data && !sign ? <section className="empty-state">
        <p role="alert">Chưa đủ dữ liệu Mặt Trời để dựng Lá Khai Sinh.</p>
      </section> : <ShareArtPreview alt="" format={format} svg={null} />}
      {message ? <p className="success-message" role="status">{message}</p> : null}
      <footer className="flow-actions"><button className="electric-button" disabled={!art.ready} onClick={() => void share()} type="button"><ShareNetwork /> Chia sẻ</button><button className="outline-button" disabled={!art.ready} onClick={() => void download()} type="button"><DownloadSimple /> Tải PNG</button><button className="text-button" onClick={() => void updateOnboardingStatus("completed").finally(() => navigate("/home"))} type="button">Để sau, vào app</button></footer>
    </main>
  );
}
