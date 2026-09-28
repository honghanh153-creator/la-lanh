import {
  BatteryLow,
  BookmarkSimple,
  Check,
  Lightning,
  PaperPlaneTilt,
  Planet,
  Sparkle,
  Spiral,
  Sun,
  UserCircle,
  Waves,
  type IconProps,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, type ComponentType } from "react";
import { Link } from "react-router-dom";

import {
  checkInMood,
  getBirthSupplement,
  getContextualReading,
  getCurrentMood,
  getDailyNote,
  getResonanceStatus,
  listSavedNotes,
  recordResonance,
  saveDailyNote,
  unsaveDailyNote,
  type DailyNote,
  type MoodValue,
  type ResonanceChoice,
  type SignalContext,
} from "../../shared/api/client";
import { useReadingUpdateActivation } from "../../shared/hooks/useReadingUpdateActivation";
import { useDailyExperiment } from "../../shared/hooks/useDailyExperiment";
import {
  dismissReadingUpdate,
  isReadingUpdateDismissed,
  readCachedDailyNote,
  writeCachedDailyNote,
} from "../../shared/storage/noteCache";
import { readLocalSavedNotes, saveNoteLocally, unsaveNoteLocally } from "../../shared/storage/savedNoteCache";
import "../../shared/styles/signal-note.css";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";
import { ReadingContent } from "../../shared/ui/ReadingContent";
import { ReadingUpdateGift } from "../../shared/ui/ReadingUpdateGift";
import { ResonanceFeedback } from "../../shared/ui/ResonanceFeedback";
import { SignalContextPicker } from "../../shared/ui/SignalContextPicker";

const moods: readonly [MoodValue, ComponentType<IconProps>][] = [
  ["Rực", Sun],
  ["Chill", Waves],
  ["Đuối", BatteryLow],
  ["Căng", Lightning],
  ["Lạc trôi", Spiral],
];

export function HomePage() {
  const queryClient = useQueryClient();
  const cachedAtStart = useMemo(() => readCachedDailyNote(), []);
  const noteQuery = useQuery({
    queryKey: ["daily-note"],
    queryFn: async ({ signal }) => {
      const freshNote = await getDailyNote(signal);
      writeCachedDailyNote(freshNote);
      return freshNote;
    },
    initialData: cachedAtStart?.note,
    initialDataUpdatedAt: cachedAtStart ? 0 : undefined,
  });
  const baseNote = noteQuery.data;
  const [contextualNote, setContextualNote] = useState<DailyNote | undefined>();
  const [context, setContext] = useState<SignalContext>("auto");
  const [contextSheetOpen, setContextSheetOpen] = useState(false);
  const note = contextualNote ?? baseNote;
  const activeReading = note?.reading_projection?.active;
  const availableUpdate = note?.reading_projection?.available_update;
  const moodQuery = useQuery({
    queryKey: ["daily-note-mood", note?.id],
    queryFn: ({ signal }) => getCurrentMood(note!.id, signal),
    enabled: Boolean(note?.id),
  });
  const savedQuery = useQuery({
    queryKey: ["saved-notes"],
    queryFn: ({ signal }) => listSavedNotes(signal),
    enabled: Boolean(note?.id),
  });
  const supplementQuery = useQuery({
    queryKey: ["birth-supplement"],
    queryFn: ({ signal }) => getBirthSupplement(signal),
    retry: false,
  });
  const resonanceQuery = useQuery({
    queryKey: ["daily-note-resonance"],
    queryFn: ({ signal }) => getResonanceStatus(signal),
    enabled: Boolean(note?.id),
    retry: false,
  });
  const [mood, setMood] = useState<MoodValue | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [resonance, setResonance] = useState<ResonanceChoice | null>(null);
  const [localSavedNotes, setLocalSavedNotes] = useState(readLocalSavedNotes);
  const [, refreshGift] = useState(0);
  const showGift = Boolean(
    context === "auto"
    && note?.reading_projection
    && availableUpdate
    && !isReadingUpdateDismissed(note.reading_projection.scope_key, availableUpdate.revision_id)
  );
  const snoozedUntil = Number(localStorage.getItem("la-lanh-birth-supplement-snooze-until") ?? 0);
  const showUnlock = (!activeReading || activeReading.mode !== "full_synthesis")
    && (supplementQuery.data?.profile_level ?? 1) < 2
    && snoozedUntil <= Date.now();
  const saved = Boolean(note && (
    savedQuery.data?.some((item) => item.daily_note_id === note.id)
    || localSavedNotes.some((item) => item.daily_note_id === note.id)
  ));

  const contextMutation = useMutation({
    mutationFn: async (nextContext: SignalContext) => {
      if (nextContext === "auto") {
        if (!baseNote) throw new Error("Missing daily note");
        return baseNote;
      }
      const cached = queryClient.getQueryData<DailyNote>(["daily-note-context", nextContext]);
      if (cached) return cached;
      if (!baseNote) throw new Error("Missing daily note");
      const projection = await getContextualReading(nextContext);
      return { ...baseNote, reading_projection: projection };
    },
    onSuccess: (nextNote, nextContext) => {
      if (nextContext !== "auto") {
        queryClient.setQueryData(["daily-note-context", nextContext], nextNote);
        setContextualNote(nextNote);
      } else {
        setContextualNote(undefined);
      }
      setContext(nextContext);
      setContextSheetOpen(false);
      setResonance(null);
      setMessage(nextContext === "auto" ? "Đã trở về góc tự động." : "Đã đổi góc nhìn cho note này.");
    },
    onError: () => {
      setMessage("Chưa bắt được góc mới. Note đang thấy vẫn được giữ nguyên, không có nội dung mới nào được nhận.");
    },
  });

  const handleContextSelect = (nextContext: SignalContext) => {
    if (nextContext === context) return;
    contextMutation.mutate(nextContext);
  };

  const resonanceMutation = useMutation({
    mutationFn: (choice: ResonanceChoice) => {
      if (!note) throw new Error("Missing daily note");
      return recordResonance(note.id, {
        choice,
        revision_id: activeReading?.revision_id ?? null,
        background_lens: context === "auto" ? null : context,
      });
    },
    onSuccess: async (payload) => {
      setResonance(payload.choice);
      setMessage(payload.choice === "hit" ? "Đã ghi nhận: trúng với bạn." : "Đã ghi nhận: góc này chưa trúng.");
      await queryClient.invalidateQueries({ queryKey: ["daily-note-resonance"] });
    },
    onError: () => setMessage("Phản hồi chưa gửi được. Không có lựa chọn nào được lưu trên máy."),
  });

  const dailyExperiment = useDailyExperiment({
    enabled: Boolean(note?.id),
    onChosen: () => setMessage("Đã giữ một việc nhỏ để thử hôm nay. Bạn có thể dừng bất cứ lúc nào."),
    onUndone: () => setMessage("Đã bỏ giữ việc nhỏ. Không có streak hay đánh dấu hoàn thành nào được tạo."),
    onReflected: () => setMessage("Đã lưu phần nhìn lại riêng cho thử nghiệm này."),
  });

  const moodMutation = useMutation({
    mutationFn: (value: MoodValue) => {
      if (!note) throw new Error("Missing daily note");
      return checkInMood(note.id, value);
    },
    onMutate: (value) => {
      const previous = mood;
      setMood(value);
      setMessage("Đang giữ nhịp này cho bạn…");
      return { previous };
    },
    onSuccess: (payload) => {
      setMood(payload.mood);
      const feedback: Record<MoodValue, string> = {
        "Rực": "Giữ nhịp sáng này, nhưng nhớ để dành một chút cho mình.",
        Chill: "Nhịp này đẹp đấy. Không cần đẩy mọi thứ đi nhanh hơn.",
        "Đuối": "Hôm nay bớt một việc cũng là chăm mình.",
        "Căng": "Thở chậm một nhịp trước khi trả lời điều quan trọng.",
        "Lạc trôi": "Chưa cần hiểu hết. Chỉ cần tìm một điểm để quay về.",
      };
      setMessage(feedback[payload.mood]);
    },
    onError: (_error, value) => {
      localStorage.setItem("la-lanh-pending-mood-v1", JSON.stringify({ note_id: note?.id, mood: value }));
      setMessage("Đã giữ cảm xúc trên máy. Lá Lành sẽ đồng bộ khi có mạng.");
    },
  });

  const activationMutation = useReadingUpdateActivation({
    onSuccess: () => setMessage("Bản đọc mới đã mở. Note giờ nối nhiều lớp trong lá số cùng nhau."),
    onError: () => setMessage("Món quà chưa mở được. Giữ nguyên bản hiện tại và thử lại nhé."),
  });

  const chooseExperiment = () => {
    if (!note || !activeReading?.experiment) return;
    const held = dailyExperiment.experiment;
    const expectedHeld = held && held.action_key !== activeReading.experiment.action_key ? held : null;
    dailyExperiment.choose({
      daily_note_id: note.id,
      revision_id: activeReading.revision_id,
      background_lens: context,
      action_key: activeReading.experiment.action_key,
      consent_version: "action-experiment-v1",
      expected_experiment_id: expectedHeld?.id ?? null,
      expected_version: expectedHeld?.version ?? null,
    });
  };

  const saveMutation = useMutation({
    mutationFn: () => {
      if (!note) throw new Error("Missing daily note");
      return saveDailyNote(note.id, activeReading?.revision_id ?? null);
    },
    onSuccess: async () => {
      if (note) {
        saveNoteLocally(note);
        setLocalSavedNotes(readLocalSavedNotes());
      }
      setMessage("Note đã nằm yên trong mục Đã lưu.");
      await queryClient.invalidateQueries({ queryKey: ["saved-notes"] });
    },
    onError: () => {
      if (note) {
        saveNoteLocally(note);
        setLocalSavedNotes(readLocalSavedNotes());
      }
      setMessage("Đã lưu note trên máy. Lá Lành sẽ đồng bộ khi có mạng.");
    },
  });

  const unsaveMutation = useMutation({
    mutationFn: () => {
      if (!note) throw new Error("Missing daily note");
      return unsaveDailyNote(note.id, activeReading?.revision_id ?? null);
    },
    onSuccess: async () => {
      if (note) {
        unsaveNoteLocally(note.id);
        setLocalSavedNotes(readLocalSavedNotes());
      }
      setMessage("Đã bỏ note khỏi mục Đã lưu.");
      await queryClient.invalidateQueries({ queryKey: ["saved-notes"] });
    },
    onError: () => {
      if (note) {
        unsaveNoteLocally(note.id);
        setLocalSavedNotes(readLocalSavedNotes());
      }
      setMessage("Đã bỏ bản lưu trên máy; server sẽ được cập nhật khi có mạng.");
    },
  });

  useEffect(() => {
    if (moodQuery.data?.mood) setMood(moodQuery.data.mood);
  }, [moodQuery.data]);

  useEffect(() => {
    if (!note || !navigator.onLine) return;
    const raw = localStorage.getItem("la-lanh-pending-mood-v1");
    if (!raw) return;
    try {
      const pendingMood = JSON.parse(raw) as { note_id?: string; mood?: MoodValue };
      if (pendingMood.note_id === note.id && pendingMood.mood) {
        localStorage.removeItem("la-lanh-pending-mood-v1");
        moodMutation.mutate(pendingMood.mood);
      }
    } catch {
      localStorage.removeItem("la-lanh-pending-mood-v1");
    }
  }, [note]); // eslint-disable-line react-hooks/exhaustive-deps

  if (noteQuery.isLoading) return <HomeState text="Đang mở note hôm nay…" />;

  if (!note) {
    return (
      <main className="app-page home-page signal-note-home">
        <HomeHeader />
        <section className="empty-state">
          <Planet size={52} />
          <h1>{noteQuery.isError ? "Note chưa về kịp." : "Chưa có Lá để nhắc bạn."}</h1>
          <p>{noteQuery.isError ? "Kiểm tra kết nối rồi thử lại." : "Khai ngày sinh trước, rồi Lá Lành sẽ để lại một note nhỏ mỗi ngày."}</p>
          {noteQuery.isError
            ? <button className="electric-button" onClick={() => void noteQuery.refetch()} type="button">Thử lại</button>
            : <Link className="electric-button" to="/birth">Khai ngày sinh</Link>}
        </section>
        <AppNav />
      </main>
    );
  }

  const modeLabel = activeReading
    ? activeReading.mode === "full_synthesis" ? "Aura · Tổng hòa lá số" : "Vibe · Một lớp từ ngày sinh"
    : note.persona_mode === "aura" ? "Aura · Tổng hòa lá số" : "Vibe · Một lớp từ ngày sinh";
  const pendingContext = contextMutation.isPending ? contextMutation.variables : null;

  return (
    <main className="app-page home-page signal-note-home">
      <HomeHeader />
      <section className="home-greeting signal-note-greeting">
        <time dateTime={note.note_date}>{formatNoteDate(note.note_date)}</time>
        <h1>{greetingForNow()}, bạn.</h1>
        <span className="transit-pill"><Sparkle aria-hidden="true" weight="fill" /> {modeLabel}</span>
      </section>

      {noteQuery.isError ? <p className="cache-status" role="status">Đang xem đúng bản đã mở gần nhất trên máy</p> : null}

      {activeReading ? (
        <section aria-label="Note hôm nay" className="signal-note-paper">
          <ReadingContent
            compact
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
          />
          <Link className="signal-note-paper__detail" to="/note/today">Đọc note đầy đủ</Link>
        </section>
      ) : (
        <section aria-label="Note hôm nay" className="signal-note-paper signal-note-paper--legacy">
          <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {modeLabel}</p>
          <h2>{note.title}</h2>
          <p>{note.body}</p>
          <p className="reading-content__disclaimer">Một góc để tự soi, không phải chỉ dẫn cố định.</p>
          <Link className="signal-note-paper__detail" to="/note/today">Đọc note đầy đủ</Link>
        </section>
      )}

      <SignalContextPicker
        error={contextMutation.isError ? "Chưa đổi được góc. Note hiện tại vẫn được giữ nguyên; bạn có thể thử lại." : null}
        onOpenChange={(open) => {
          if (open) contextMutation.reset();
          setContextSheetOpen(open);
        }}
        onSelect={handleContextSelect}
        open={contextSheetOpen}
        pending={pendingContext}
        selected={context}
      />

      <ResonanceFeedback
        consented={resonanceQuery.data?.consented ?? false}
        onChangeAngle={() => {
          contextMutation.reset();
          setContextSheetOpen(true);
        }}
        onSubmit={(choice) => resonanceMutation.mutate(choice)}
        pending={resonanceMutation.isPending}
        selected={resonance}
      />

      {showGift && availableUpdate && note.reading_projection ? (
        <ReadingUpdateGift
          activeMode={activeReading?.mode}
          onActivate={() => {
            if (!note.reading_projection || !availableUpdate) return;
            activationMutation.mutate({
              scopeKey: note.reading_projection.scope_key,
              revisionId: availableUpdate.revision_id,
            });
          }}
          onDismiss={() => {
            dismissReadingUpdate(note.reading_projection!.scope_key, availableUpdate.revision_id);
            refreshGift((value) => value + 1);
          }}
          pending={activationMutation.isPending}
          update={availableUpdate}
        />
      ) : null}

      <section className="mood-check" aria-labelledby="mood-title">
        <p className="eyebrow">Check-in riêng</p>
        <h2 id="mood-title">Hôm nay bạn thấy sao?</h2>
        <div>
          {moods.map(([label, Icon]) => (
            <button
              aria-pressed={mood === label}
              className={mood === label ? "mood-chip mood-chip--active" : "mood-chip"}
              key={label}
              onClick={() => moodMutation.mutate(label)}
              type="button"
            >
              <span><Icon aria-hidden="true" size={22} weight="bold" /></span>{label}
            </button>
          ))}
        </div>
      </section>

      <div className="home-actions">
        <Link className="electric-button" to="/card"><PaperPlaneTilt aria-hidden="true" /> Chia sẻ</Link>
        <button
          className="outline-button"
          disabled={saveMutation.isPending || unsaveMutation.isPending}
          onClick={() => saved ? unsaveMutation.mutate() : saveMutation.mutate()}
          type="button"
        >
          {saved ? <Check aria-hidden="true" /> : <BookmarkSimple aria-hidden="true" />}
          {saved ? "Đã lưu" : "Lưu lại"}
        </button>
      </div>

      <p className="sr-only" aria-live="polite" role="status">{message}</p>
      {message ? <p className="home-status" aria-hidden="true">{message}</p> : null}

      {showUnlock ? (
        <aside className="unlock-note">
          <Planet aria-hidden="true" />
          <div><strong>Còn một lớp chưa mở</strong><p>Thêm giờ và nơi sinh để chuyển từ Vibe sang bản đọc Aura.</p></div>
          <Link to="/birth-time">Mở lớp sâu</Link>
        </aside>
      ) : null}

      <section className="home-social-bento" aria-label="Khám phá thêm">
        {(supplementQuery.data?.profile_level ?? 1) === 3 ? <Link className="home-natal-entry" to="/natal"><Planet aria-hidden="true" /><span><small>Bản đọc Natal · đã mở</small><strong>Bạn có muốn hiểu mình hơn?</strong><em>Vì sao một kiểu chuyện hay lặp lại — và bạn đang học điều gì từ chúng?</em></span></Link> : <Link to="/insights"><Planet aria-hidden="true" /><span><small>Bản đồ Lá</small><strong>Đọc tổng hòa chart</strong></span></Link>}
        <Link to="/la-chung"><Sparkle aria-hidden="true" /><span><small>Lá Chứng</small><strong>Nghe một người nhìn bạn</strong></span></Link>
      </section>
      <AppNav />
    </main>
  );
}

function formatNoteDate(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(year, month - 1, day, 12);
  return new Intl.DateTimeFormat("vi-VN", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  }).format(date);
}

function greetingForNow(): string {
  const hour = new Date().getHours();
  if (hour < 11) return "Chào buổi sáng";
  if (hour < 18) return "Chào buổi chiều";
  return "Chào buổi tối";
}

function HomeHeader() {
  return (
    <header className="home-header">
      <BrandMark />
      <Link aria-label="Trang cá nhân" className="profile-orb" to="/profile"><UserCircle aria-hidden="true" size={25} /></Link>
    </header>
  );
}

function HomeState({ text }: { text: string }) {
  return (
    <main className="app-page home-page signal-note-home">
      <HomeHeader />
      <section className="entry-loading"><span className="entry-loading__orbit" /><p>{text}</p></section>
      <AppNav />
    </main>
  );
}
