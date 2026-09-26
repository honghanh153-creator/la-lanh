import { BookmarkSimple, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import { listSavedNotes, unsaveDailyNote, type SavedNote } from "../../shared/api/client";
import { readLocalSavedNotes, unsaveNoteLocally } from "../../shared/storage/savedNoteCache";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";

function noteText(saved: SavedNote, key: "title" | "body" | "context_label" | "persona_mode" | "persona_label"): string {
  const value = saved.note_snapshot[key];
  return typeof value === "string" ? value : "";
}

function readingMode(saved: SavedNote): string {
  if (!saved.reading_snapshot) return noteText(saved, "persona_mode") === "aura" ? "Aura" : "Vibe";
  return saved.reading_snapshot.mode === "vibe_fallback" ? "Vibe" : "Aura";
}

export function SavedPage() {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<string | null>(null);
  const undoTimer = useRef<number | null>(null);
  const pendingRemove = useRef<(() => void) | null>(null);
  const savedQuery = useQuery({
    queryKey: ["saved-notes"],
    queryFn: ({ signal }) => listSavedNotes(signal),
  });
  const removeMutation = useMutation({
    mutationFn: ({ dailyNoteId, revisionId }: { dailyNoteId: string; revisionId: string | null }) => (
      unsaveDailyNote(dailyNoteId, revisionId)
    ),
    onSuccess: async (_data, { dailyNoteId }) => {
      unsaveNoteLocally(dailyNoteId);
      setMessage("Đã bỏ lưu note.");
      await queryClient.invalidateQueries({ queryKey: ["saved-notes"] });
    },
  });

  const removeWithUndo = (remove: () => void) => {
    if (undoTimer.current !== null) window.clearTimeout(undoTimer.current);
    setMessage("Note sẽ được bỏ lưu sau 5 giây. Hoàn tác?");
    pendingRemove.current = remove;
    undoTimer.current = window.setTimeout(() => {
      pendingRemove.current?.();
      pendingRemove.current = null;
      undoTimer.current = null;
    }, 5000);
  };

  const undoRemove = () => {
    if (undoTimer.current !== null) window.clearTimeout(undoTimer.current);
    undoTimer.current = null;
    pendingRemove.current = null;
    setMessage("Đã giữ note lại.");
  };

  const notes = savedQuery.data ?? [];
  const localNotes = readLocalSavedNotes().filter(
    (local) => !notes.some((server) => server.daily_note_id === local.daily_note_id),
  );

  return (
    <main className="app-page saved-page">
      <header className="section-header"><BrandMark /><h1>Đã lưu</h1></header>
      {message ? <p className="success-message" role="status">{message} {undoTimer.current !== null ? <button className="text-link" onClick={undoRemove} type="button">Hoàn tác</button> : null}</p> : null}
      {savedQuery.isLoading ? (
        <section className="entry-loading"><span className="entry-loading__orbit" /><p>Đang lật lại những note đã giữ…</p></section>
      ) : notes.length > 0 || localNotes.length > 0 ? (
        <section className="saved-list" aria-label="Những note đã lưu">
          {notes.map((saved) => (
            <article className="paper-panel saved-note" key={saved.id}>
              <p className="eyebrow">{noteText(saved, "persona_label") ? `${readingMode(saved)} · ${noteText(saved, "persona_label")}` : "Một note bạn không muốn bỏ lỡ"}</p>
              <h2>{saved.reading_snapshot?.sections.hook || noteText(saved, "title") || "Một lời nhắc đã lưu"}</h2>
              <p>{saved.reading_snapshot?.sections.manifestation || noteText(saved, "body")}</p>
              {saved.reading_snapshot ? (
                <details className="saved-note__reading">
                  <summary>Mở đúng bản đã lưu</summary>
                  <p>{saved.reading_snapshot.sections.thesis}</p>
                  {saved.reading_snapshot.sections.transit ? <p>{saved.reading_snapshot.sections.transit}</p> : null}
                  <p><strong>Một việc nhỏ:</strong> {saved.reading_snapshot.sections.micro_action}</p>
                  <details>
                    <summary>{saved.reading_snapshot.evidence.title}</summary>
                    <ul>{saved.reading_snapshot.evidence.claims.map((claim) => <li key={claim}>{claim}</li>)}</ul>
                    <p>{saved.reading_snapshot.evidence.framework_disclosure}</p>
                  </details>
                  <small>{saved.reading_snapshot.disclaimer}</small>
                </details>
              ) : null}
              <small>
                Lưu lúc {new Intl.DateTimeFormat("vi-VN", {
                  dateStyle: "medium",
                  timeStyle: "short",
                }).format(new Date(saved.saved_at))}
              </small>
              <button
                className="detail-link"
                disabled={removeMutation.isPending}
                onClick={() => removeWithUndo(() => removeMutation.mutate({
                  dailyNoteId: saved.daily_note_id,
                  revisionId: saved.revision_id ?? null,
                }))}
                type="button"
              >
                <Trash size={16} /> Bỏ lưu
              </button>
            </article>
          ))}
          {localNotes.map((saved) => (
            <article className="paper-panel saved-note" key={saved.daily_note_id}>
              <p className="eyebrow">Đang chờ đồng bộ</p>
              <h2>Note đã được giữ trên máy.</h2>
              <p>Nội dung riêng không được lưu lâu dài trên thiết bị này. Khi có mạng, đúng revision sẽ xuất hiện ở đây.</p>
              <small>Lưu lúc {new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(saved.saved_at))}</small>
              <button className="detail-link" onClick={() => removeWithUndo(() => {
                removeMutation.mutate({
                  dailyNoteId: saved.daily_note_id,
                  revisionId: saved.revision_id ?? null,
                });
              })} type="button"><Trash size={16} /> Bỏ lưu</button>
            </article>
          ))}
        </section>
      ) : (
        <section className="empty-state">
          <BookmarkSimple size={52} />
          <h2>Chưa có note nào nằm lại.</h2>
          <p>Khi một lời nhắc chạm đúng lúc, lưu nó ở đây.</p>
          <Link className="electric-button" to="/home">Về note hôm nay</Link>
        </section>
      )}
      <AppNav />
    </main>
  );
}
