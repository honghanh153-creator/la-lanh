import { ArrowLeft, DownloadSimple, LinkBreak, LinkSimple, ShareNetwork } from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
  createShareArtifact,
  revokeShareArtifact,
  type DailyNote,
  type ShareArtifact,
  type ShareFormat,
} from "../../shared/api/client";
import { dailyContextQueryKey, getDailyNoteForContext, parseDailyContext } from "../../shared/astro/dailyContext";
import { BrandMark } from "../../shared/ui/BrandMark";
import { cardSvg, shareCopy } from "./noteCardSvg";

function svgFile(note: DailyNote, format: ShareFormat): File {
  return new File([cardSvg(note, format)], `la-lanh-note-${format}.svg`, { type: "image/svg+xml" });
}

async function pngFile(note: DailyNote, format: ShareFormat): Promise<File> {
  const svg = svgFile(note, format);
  const sourceUrl = URL.createObjectURL(svg);
  try {
    const image = new Image();
    image.decoding = "async";
    image.src = sourceUrl;
    await image.decode();
    const canvas = document.createElement("canvas");
    canvas.width = format === "square_1_1" ? 1080 : 1080;
    canvas.height = format === "square_1_1" ? 1080 : 1920;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Canvas is not available");
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((value) => value ? resolve(value) : reject(new Error("PNG render failed")), "image/png", 0.92);
    });
    return new File([blob], `la-lanh-note-${format}.png`, { type: "image/png" });
  } finally {
    URL.revokeObjectURL(sourceUrl);
  }
}

function shareUrl(artifact: ShareArtifact): string | null {
  if (!artifact.public_path) return null;
  return new URL(artifact.public_path, window.location.origin).toString();
}

export function CardPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const context = parseDailyContext(searchParams.get("context"));
  const noteQuery = useQuery({ queryKey: dailyContextQueryKey(context), queryFn: ({ signal }) => getDailyNoteForContext(context, signal) });
  const [format, setFormat] = useState<ShareFormat>("story_9_16");
  const [artifact, setArtifact] = useState<ShareArtifact | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const createMutation = useMutation({
    mutationFn: () => {
      if (!noteQuery.data) throw new Error("Missing daily note");
      return createShareArtifact(noteQuery.data.id, format, noteQuery.data.reading_projection?.active.revision_id ?? null, context);
    },
    onSuccess: (payload) => {
      setArtifact(payload);
      setMessage("Link chia sẻ đã được tạo. Không kèm ngày/giờ/nơi sinh.");
    },
    onError: () => setMessage("Chưa tạo được link chia sẻ. Thử lại sau một nhịp nhé."),
  });
  const revokeMutation = useMutation({
    mutationFn: () => {
      if (!artifact) throw new Error("Missing share artifact");
      return revokeShareArtifact(artifact.id);
    },
    onSuccess: () => {
      setArtifact(null);
      setMessage("Link đã được thu hồi. Người có link cũ không thể mở lại.");
    },
    onError: () => setMessage("Chưa thu hồi được link. Thử lại khi có kết nối nhé."),
  });

  useEffect(() => setArtifact(null), [format]);

  const note = noteQuery.data;
  const copy = note ? shareCopy(note) : null;

  const download = async () => {
    if (!note) return;
    try {
      const file = await pngFile(note, format);
      const url = URL.createObjectURL(file);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = file.name;
      anchor.click();
      URL.revokeObjectURL(url);
      setMessage("Card PNG đã được tải về.");
    } catch {
      setMessage("Chưa dựng được ảnh. Preview vẫn được giữ để bạn thử lại.");
    }
  };

  const share = async () => {
    if (!note) return;
    try {
      const file = await pngFile(note, format);
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: `Lá Lành · ${shareCopy(note).title}` });
        setMessage("Card đã sẵn sàng bay đi.");
      } else {
        await download();
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") setMessage("Bạn đã đóng bảng chia sẻ. Card vẫn còn nguyên.");
      else setMessage("Chưa chia sẻ được. Hãy tải card và gửi thủ công nhé.");
    }
  };

  const copyLink = async () => {
    if (!artifact) {
      createMutation.mutate();
      return;
    }
    const url = shareUrl(artifact);
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setMessage("Đã copy link chia sẻ.");
    } catch {
      setMessage("Trình duyệt chưa cho copy. Bạn có thể chọn và sao chép link thủ công.");
    }
  };

  return (
    <main className="flow-page card-page">
      <header className="flow-header">
        <button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button>
        <BrandMark />
        <span />
      </header>
      <section className="format-toggle" aria-label="Định dạng card">
        <button aria-pressed={format === "story_9_16"} className={format === "story_9_16" ? "is-active" : ""} onClick={() => setFormat("story_9_16")} type="button">Story 9:16</button>
        <button aria-pressed={format === "square_1_1"} className={format === "square_1_1" ? "is-active" : ""} onClick={() => setFormat("square_1_1")} type="button">Square 1:1</button>
      </section>
      {note && copy ? (
        <section className={`${format === "square_1_1" ? "share-card share-card--square" : "share-card"}${copy.body ? "" : " share-card--minimal"}`}>
          <span className="share-card__logo">LÁ LÀNH*</span>
          <p>{copy.persona}</p>
          <h1>{copy.title}</h1>
          {copy.body ? <blockquote>{copy.body}</blockquote> : null}
          <small>Đúng bản đang mở · không kèm dữ liệu sinh hay căn cứ riêng</small>
        </section>
      ) : (
        <section className="entry-loading"><span className="entry-loading__orbit" /><p>Đang dựng card…</p></section>
      )}
      {message ? <p className="success-message" role="status">{message}</p> : null}
      <footer className="flow-actions">
        <button className="electric-button" disabled={!note} onClick={() => void share()} type="button"><ShareNetwork /> Chia sẻ card</button>
        <button className="outline-button" disabled={!note} onClick={() => createMutation.mutate()} type="button"><LinkSimple /> Tạo safe link</button>
        {artifact ? <button className="outline-button" onClick={() => void copyLink()} type="button"><LinkSimple /> Copy link</button> : null}
        {artifact ? <button className="outline-button" disabled={revokeMutation.isPending} onClick={() => revokeMutation.mutate()} type="button"><LinkBreak /> Thu hồi link</button> : null}
        <button className="outline-button" disabled={!note} onClick={() => void download()} type="button"><DownloadSimple /> Tải ảnh PNG</button>
      </footer>
    </main>
  );
}
