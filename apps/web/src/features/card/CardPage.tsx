import { ArrowLeft, DownloadSimple, LinkBreak, LinkSimple, ShareNetwork } from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
  createShareArtifact,
  revokeShareArtifact,
  type ShareArtifact,
  type ShareFormat,
} from "../../shared/api/client";
import { dailyContextQueryKey, getDailyNoteForContext, parseDailyContext } from "../../shared/astro/dailyContext";
import { noteSpecFromNote, shareCopy } from "./noteCardSvg";
import { shareArtAlt } from "./shareArt";
import { ShareArtPreview } from "./ShareArtPreview";
import { useShareArt } from "./useShareArt";

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
  const spec = useMemo(() => (note ? noteSpecFromNote(note) : null), [note]);
  const art = useShareArt(spec, format);
  const fileName = `la-lanh-note-${format}.png`;

  const download = async () => {
    if (!art.ready) return;
    try {
      const file = await art.pngFile(fileName);
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
    if (!note || !art.ready) return;
    try {
      const file = await art.pngFile(fileName);
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
      <header className="flow-header uv-topbar">
        <button aria-label="Quay lại" className="icon-button uv-topbar__icon" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button>
        <span className="uv-topbar__title">Chia sẻ card</span>
        <span aria-hidden="true" className="uv-topbar__spacer" />
      </header>
      <section className="format-toggle" aria-label="Định dạng card">
        <button aria-pressed={format === "story_9_16"} className={format === "story_9_16" ? "is-active" : ""} onClick={() => setFormat("story_9_16")} type="button">Story 9:16</button>
        <button aria-pressed={format === "square_1_1"} className={format === "square_1_1" ? "is-active" : ""} onClick={() => setFormat("square_1_1")} type="button">Square 1:1</button>
      </section>
      {note && copy && spec ? (
        <>
          <ShareArtPreview alt={shareArtAlt(spec, format)} format={format} heading={copy.title} svg={art.svg} />
          <p className="share-art-privacy">Đúng bản đang mở · không kèm ngày / giờ / nơi sinh hay căn cứ riêng</p>
        </>
      ) : noteQuery.isError ? (
        <section className="empty-state">
          <p role="alert">Chưa tải được note để tạo card.</p>
          <button className="outline-button" disabled={noteQuery.isFetching} onClick={() => void noteQuery.refetch()} type="button">Thử lại</button>
        </section>
      ) : (
        <ShareArtPreview alt="" format={format} svg={null} />
      )}
      {message ? <p className="success-message" role="status">{message}</p> : null}
      <footer className="flow-actions">
        <button className="electric-button" disabled={!art.ready} onClick={() => void share()} type="button"><ShareNetwork /> Chia sẻ card</button>
        <button className="outline-button" disabled={!note} onClick={() => createMutation.mutate()} type="button"><LinkSimple /> Tạo safe link</button>
        {artifact ? <button className="outline-button" onClick={() => void copyLink()} type="button"><LinkSimple /> Copy link</button> : null}
        {artifact && shareUrl(artifact) ? <label>
          <span>Link chia sẻ</span>
          <input aria-label="Link chia sẻ" onFocus={(event) => event.currentTarget.select()} readOnly value={shareUrl(artifact) ?? ""} />
        </label> : null}
        {artifact ? <button className="outline-button" disabled={revokeMutation.isPending} onClick={() => revokeMutation.mutate()} type="button"><LinkBreak /> Thu hồi link</button> : null}
        <button className="outline-button" disabled={!art.ready} onClick={() => void download()} type="button"><DownloadSimple /> Tải ảnh PNG</button>
      </footer>
    </main>
  );
}
