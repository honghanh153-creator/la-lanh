import { ArrowLeft, BookmarkSimple, Check, PaperPlaneTilt } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  getDailyNote,
  listSavedNotes,
  saveDailyNote,
} from "../../shared/api/client";
import {
  readCachedDailyNote,
  writeCachedDailyNote,
} from "../../shared/storage/noteCache";
import { useReadingUpdateActivation } from "../../shared/hooks/useReadingUpdateActivation";
import { useDailyExperiment } from "../../shared/hooks/useDailyExperiment";
import { saveNoteLocally } from "../../shared/storage/savedNoteCache";
import "../../shared/styles/signal-note.css";
import { BrandMark } from "../../shared/ui/BrandMark";
import { ReadingContent } from "../../shared/ui/ReadingContent";
import { ReadingDisclaimer } from "../../shared/ui/ReadingDisclaimer";
import { ReadingUpdateGift } from "../../shared/ui/ReadingUpdateGift";

export function NoteDetailPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const cachedAtStart = useMemo(() => readCachedDailyNote(), []);
  const [saved, setSaved] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const query = useQuery({
    queryKey: ["daily-note"],
    queryFn: async ({ signal }) => {
      const freshNote = await getDailyNote(signal);
      writeCachedDailyNote(freshNote);
      return freshNote;
    },
    initialData: cachedAtStart?.note,
    initialDataUpdatedAt: cachedAtStart ? 0 : undefined,
  });
  const note = query.data;
  const activeReading = note?.reading_projection?.active;
  const availableUpdate = note?.reading_projection?.available_update;
  const savedQuery = useQuery({
    queryKey: ["saved-notes"],
    queryFn: ({ signal }) => listSavedNotes(signal),
    enabled: Boolean(note),
  });
  const isSaved = saved || Boolean(note && savedQuery.data?.some((item) => item.daily_note_id === note.id));
  const saveMutation = useMutation({
    mutationFn: () => {
      if (!note) throw new Error("Missing daily note");
      return saveDailyNote(note.id);
    },
    onSuccess: async () => {
      if (note) saveNoteLocally(note);
      setSaved(true);
      setMessage("Note đã nằm yên trong mục Đã lưu.");
      await queryClient.invalidateQueries({ queryKey: ["saved-notes"] });
    },
    onError: () => {
      if (note) saveNoteLocally(note);
      setSaved(true);
      setMessage("Đã lưu note trên máy. Lá Lành sẽ đồng bộ khi có mạng.");
    },
  });
  const activationMutation = useReadingUpdateActivation({
    onSuccess: () => setMessage("Bản đọc mới đã mở — các lớp trong chart đã được nối lại."),
    onError: () => setMessage("Chưa mở được bản mới. Bản hiện tại vẫn được giữ nguyên."),
  });
  const dailyExperiment = useDailyExperiment({
    enabled: Boolean(note?.id),
    onChosen: () => setMessage("Đã giữ một việc nhỏ để thử hôm nay. Bạn có thể dừng bất cứ lúc nào."),
    onUndone: () => setMessage("Đã bỏ giữ việc nhỏ. Không có streak hay đánh dấu hoàn thành nào được tạo."),
    onReflected: () => setMessage("Đã lưu phần nhìn lại riêng cho thử nghiệm này."),
  });

  const chooseExperiment = () => {
    if (!note || !activeReading?.experiment) return;
    const held = dailyExperiment.experiment;
    const expectedHeld = held && held.action_key !== activeReading.experiment.action_key ? held : null;
    dailyExperiment.choose({
      daily_note_id: note.id,
      revision_id: activeReading.revision_id,
      background_lens: "auto",
      action_key: activeReading.experiment.action_key,
      consent_version: "action-experiment-v1",
      expected_experiment_id: expectedHeld?.id ?? null,
      expected_version: expectedHeld?.version ?? null,
    });
  };

  return (
    <main className="flow-page note-detail-page">
      <header className="flow-header">
        <button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft aria-hidden="true" /></button>
        <BrandMark />
        <span className="flow-header__step">Note hôm nay</span>
      </header>

      {query.isLoading ? <section className="reading-skeleton" aria-label="Đang mở bản đọc" /> : null}
      {note ? (
        <>
          {query.isError ? <p className="cache-status" role="status">Đang xem đúng bản đã mở gần nhất trên máy</p> : null}
          {availableUpdate && note.reading_projection ? (
            <ReadingUpdateGift
              activeMode={activeReading?.mode}
              detail
              onActivate={() => {
                if (!note.reading_projection || !availableUpdate) return;
                activationMutation.mutate({
                  scopeKey: note.reading_projection.scope_key,
                  revisionId: availableUpdate.revision_id,
                });
              }}
              pending={activationMutation.isPending}
              update={availableUpdate}
            />
          ) : null}
          {activeReading ? <ReadingContent
            content={activeReading}
            currentExperiment={dailyExperiment.experiment}
            experimentError={dailyExperiment.errorMessage}
            experimentStatus={dailyExperiment.status}
            onChoose={chooseExperiment}
            onReflect={(outcome) => {
              const held = dailyExperiment.experiment;
              if (!held) return;
              dailyExperiment.reflect({
                experiment_id: held.id,
                expected_version: held.version,
                outcome,
              });
            }}
            onUndo={() => {
              const held = dailyExperiment.experiment;
              if (!held) return;
              dailyExperiment.undo({ experiment_id: held.id, expected_version: held.version });
            }}
          /> : (
            <article className="reading-content reading-content--legacy">
              <header className="reading-content__intro">
                <p className="reading-mode">Vibe · Bản tương thích</p>
                <h1>{note.title}</h1>
                <p>{note.full_body}</p>
              </header>
              <ReadingDisclaimer>Nội dung tham khảo; quyền quyết định vẫn ở bạn.</ReadingDisclaimer>
            </article>
          )}

          <section aria-labelledby="daily-tarot-title" className="note-tarot-bridge">
            <p className="eyebrow">Lá Hỏi · tự bốc</p>
            <h2 id="daily-tarot-title">Còn một chỗ muốn nhìn rõ hơn?</h2>
            <p>Giữ nguyên chuyện đang nghĩ tới. Chọn một câu rồi tự rút lá để soi phần bạn thật sự làm được.</p>
            <div>
              <Link to="/tarot?origin=daily&context=general&prompt=daily-clarity">Chuyện này cần nhìn từ góc nào?</Link>
              <Link to="/tarot?origin=daily&context=energy&prompt=daily-next-step">Mình cần bỏ bớt nhịp nào?</Link>
              <Link to="/tarot?origin=daily&context=self_care&prompt=daily-self-check">Mình đang thật sự cần gì?</Link>
            </div>
          </section>

          <p className="sr-only" aria-live="polite" role="status">{message}</p>
          {message ? <p className="home-status" aria-hidden="true">{message}</p> : null}
          <footer className="note-detail-actions">
            <Link className="electric-button" to="/card"><PaperPlaneTilt aria-hidden="true" /> Chia sẻ</Link>
            <button className="outline-button" disabled={isSaved || saveMutation.isPending} onClick={() => saveMutation.mutate()} type="button">
              {isSaved ? <Check aria-hidden="true" /> : <BookmarkSimple aria-hidden="true" />}
              {isSaved ? "Đã lưu" : "Lưu note"}
            </button>
          </footer>
          <Link className="text-link note-detail-back" to="/home">Cập nhật cảm xúc hôm nay</Link>
        </>
      ) : null}
      {!query.isLoading && !note ? (
        <section className="empty-state"><h1>Chưa mở được note.</h1><button className="electric-button" onClick={() => void query.refetch()} type="button">Thử lại</button></section>
      ) : null}
    </main>
  );
}
