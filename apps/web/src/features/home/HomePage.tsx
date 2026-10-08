import {
  ArrowRight,
  CaretDown,
  Pause,
  Planet,
  Play,
  Smiley,
  Sparkle,
  User,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  checkInMood,
  getBirthSupplement,
  getContextualReading,
  getCurrentMood,
  getDailyNote,
  getResonanceStatus,
  isGuestSessionUnavailable,
  recordResonance,
  type DailyNote,
  type MoodValue,
  type ResonanceChoice,
  type SignalContext,
} from "../../shared/api/client";
import { useReadingUpdateActivation } from "../../shared/hooks/useReadingUpdateActivation";
import { birthCompletionPrompt } from "../../shared/astro/birthReadiness";
import { dailyContextPath } from "../../shared/astro/dailyContext";
import {
  dismissReadingUpdate,
  isReadingUpdateDismissed,
  readCachedDailyNote,
  writeCachedDailyNote,
} from "../../shared/storage/noteCache";
import "../../shared/styles/signal-note.css";
import { AppNav } from "../../shared/ui/AppNav";
import { AppSheet } from "../../shared/ui/AppSheet";
import { BrandMark } from "../../shared/ui/BrandMark";
import { ReadingUpdateGift } from "../../shared/ui/ReadingUpdateGift";
import { ResonanceFeedback } from "../../shared/ui/ResonanceFeedback";
import { SignalContextPicker } from "../../shared/ui/SignalContextPicker";

const moods: readonly { value: MoodValue; emoji: string; hint: string }[] = [
  { value: "Rực", emoji: "🤩", hint: "Nhiều năng lượng, muốn bật mode hết mình" },
  { value: "Chill", emoji: "😌", hint: "Ổn áp, cứ thong thả mà đi" },
  { value: "Đuối", emoji: "🫠", hint: "Pin yếu, cần bớt việc một chút" },
  { value: "Căng", emoji: "😵‍💫", hint: "Đầu đang quay, người đang gồng" },
  { value: "Lạc trôi", emoji: "🥴", hint: "Chưa biết mình đang ở nhịp nào" },
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
  const [motionPaused, setMotionPaused] = useState(false);
  const note = contextualNote ?? baseNote;
  const activeReading = note?.reading_projection?.active;
  const availableUpdate = note?.reading_projection?.available_update;
  const moodQuery = useQuery({
    queryKey: ["daily-note-mood", note?.id],
    queryFn: ({ signal }) => getCurrentMood(note!.id, signal),
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
  const [moodSheetOpen, setMoodSheetOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [resonance, setResonance] = useState<ResonanceChoice | null>(null);
  const [, refreshGift] = useState(0);
  const showGift = Boolean(
    context === "auto"
    && note?.reading_projection
    && availableUpdate
    && !isReadingUpdateDismissed(note.reading_projection.scope_key, availableUpdate.revision_id)
  );
  const snoozedUntil = Number(localStorage.getItem("la-lanh-birth-supplement-snooze-until") ?? 0);
  const completionPrompt = birthCompletionPrompt(supplementQuery.data);
  const showUnlock = Boolean(completionPrompt) && snoozedUntil <= Date.now();

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

  const moodMutation = useMutation({
    mutationFn: (value: MoodValue) => {
      if (!note) throw new Error("Missing daily note");
      return checkInMood(note.id, value);
    },
    onMutate: (value) => {
      const previous = mood;
      setMood(value);
      setMoodSheetOpen(false);
      setMessage("Đang lưu cảm xúc này cho bạn…");
      return { previous };
    },
    onSuccess: (payload) => {
      setMood(payload.mood);
      const feedback: Record<MoodValue, string> = {
        "Rực": "Bạn đang nhiều năng lượng. Nhớ để dành một chút cho mình.",
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
  const missingSession = isGuestSessionUnavailable(noteQuery.error);

  if (!note) {
    return (
      <main className="app-page home-page signal-note-home">
        <HomeHeader />
        <HomeValueHero />
        <section className="empty-state">
          <Planet size={52} />
          <h1>{missingSession ? "Phiên riêng đã khép lại." : noteQuery.isError ? "Note chưa về kịp." : "Chưa có Lá để nhắc bạn."}</h1>
          <p>{missingSession
            ? "Mở lại Trạm Bắt Sóng để nối đúng note và Bản đồ của bạn. Chưa cần tài khoản."
            : noteQuery.isError
              ? "Kiểm tra kết nối rồi thử lại."
              : "Khai ngày sinh trước, rồi Lá Lành sẽ để lại một note nhỏ mỗi ngày."}</p>
          {missingSession
            ? <Link className="electric-button" to="/welcome">Mở lại Trạm Bắt Sóng</Link>
            : noteQuery.isError
            ? <button className="electric-button" onClick={() => void noteQuery.refetch()} type="button">Thử lại</button>
            : <Link className="electric-button" to="/birth">Khai ngày sinh</Link>}
        </section>
        <HomeExploreRoutes />
        <AppNav />
      </main>
    );
  }

  const pendingContext = contextMutation.isPending ? contextMutation.variables : null;
  const noteDecoration = <SignalContextPicker
    appearance="moon"
    error={contextMutation.isError ? "Chưa đổi được góc. Note hiện tại vẫn được giữ nguyên; bạn có thể thử lại." : null}
    onOpenChange={(open) => {
      if (open) contextMutation.reset();
      setContextSheetOpen(open);
    }}
    onSelect={handleContextSelect}
    open={contextSheetOpen}
    pending={pendingContext}
    selected={context}
  />;
  const quickActions = (
    <ResonanceFeedback
      sharePath={dailyContextPath("/card", context)}
      consented={resonanceQuery.data?.consented ?? false}
      onSubmit={(choice) => resonanceMutation.mutate(choice)}
      pending={resonanceMutation.isPending}
      selected={resonance}
    />
  );

  return (
    <main className="app-page home-page signal-note-home" data-home-motion={motionPaused ? "paused" : "running"}>
      <HomeHeader motionControl={
        <button
          aria-label={motionPaused ? "Bật chuyển động" : "Tạm dừng chuyển động"}
          className="home-motion-toggle"
          onClick={() => setMotionPaused((paused) => !paused)}
          title={motionPaused ? "Bật chuyển động" : "Tạm dừng chuyển động"}
          type="button"
        >
          {motionPaused ? <Play aria-hidden="true" size={19} /> : <Pause aria-hidden="true" size={19} />}
        </button>
      } />
      <HomeValueHero date={note.note_date}>
        <MoodPicker mood={mood} onOpenChange={setMoodSheetOpen} onSelect={(value) => moodMutation.mutate(value)} open={moodSheetOpen} pending={moodMutation.isPending} />
      </HomeValueHero>

      {noteQuery.isError ? (
        <p className="cache-status" role="status">
          {missingSession
            ? <>Đang xem bản đã mở gần nhất trên máy · <Link to="/welcome">Mở lại Trạm để cập nhật Note và Bản đồ</Link></>
            : "Đang xem đúng bản đã mở gần nhất trên máy"}
        </p>
      ) : null}

      {activeReading ? (
        <HomeDailySignal
          activeReading={activeReading}
          detailPath={dailyContextPath("/note/today", context)}
          decoration={noteDecoration}
          toolbar={quickActions}
        />
      ) : (
        <section aria-label="Note hôm nay" className="home-daily-signal home-daily-signal--legacy">
          <article className="home-daily-signal__paper">
            {noteDecoration}
            <p className="home-daily-signal__eyebrow">Hôm nay của bạn</p>
            <h2>{note.title}</h2>
            <p>{note.body}</p>
            <footer className="home-note-footer"><Link to={dailyContextPath("/note/today", context)}>Đọc thêm <ArrowRight aria-hidden="true" /></Link>{quickActions}</footer>
          </article>
        </section>
      )}

      <HomeExploreRoutes />

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

      <p className="sr-only" aria-live="polite" role="status">{message}</p>
      {message ? <p className="home-status" aria-hidden="true">{message}</p> : null}

      {showUnlock && completionPrompt ? (
        <aside className="unlock-note">
          <Planet aria-hidden="true" />
          <div><strong>Muốn hiểu mình rõ hơn?</strong><p>{completionPrompt.body}</p></div>
          <Link to="/birth-time">{completionPrompt.cta}</Link>
        </aside>
      ) : null}

      <AppNav />
    </main>
  );
}

function MoodPicker({
  mood,
  onOpenChange,
  onSelect,
  open,
  pending,
}: {
  mood: MoodValue | null;
  onOpenChange: (open: boolean) => void;
  onSelect: (value: MoodValue) => void;
  open: boolean;
  pending: boolean;
}) {
  const selected = moods.find((option) => option.value === mood);

  return (
    <>
      <button
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-label={selected ? `Mood hôm nay: ${selected.value}` : "Chọn mood hôm nay"}
        className="mood-quick-trigger"
        onClick={() => onOpenChange(true)}
        type="button"
      >
        <span aria-hidden="true"><Smiley weight="regular" size={28} /></span>
        <strong className="sr-only">{selected?.value ?? "Mood hôm nay?"}</strong>
        <CaretDown aria-hidden="true" size={16} />
      </button>
      <AppSheet
        closeDisabled={pending}
        eyebrow="Check-in riêng"
        onClose={() => onOpenChange(false)}
        open={open}
        title="Hôm nay bạn đang ở mood nào?"
      >
        <div className="mood-sheet__options">
          {moods.map((option) => (
            <button
              aria-pressed={mood === option.value}
              disabled={pending}
              key={option.value}
              onClick={() => onSelect(option.value)}
              type="button"
            >
              <span aria-hidden="true">{option.emoji}</span>
              <span><strong>{option.value}</strong><small>{option.hint}</small></span>
            </button>
          ))}
        </div>
        <p className="mood-sheet__privacy">Chỉ bạn thấy check-in này. Bạn có thể đổi mood bất cứ lúc nào.</p>
      </AppSheet>
    </>
  );
}

function formatNoteDate(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(year, month - 1, day, 12);
  const weekday = new Intl.DateTimeFormat("vi-VN", { weekday: "long" }).format(date);
  return `${weekday}, ${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}`;
}

function HomeHeader({ motionControl }: { motionControl?: ReactNode }) {
  return (
    <header className="home-header">
      <BrandMark />
      <div className="home-header__actions">
        {motionControl}
        <Link aria-label="Trang cá nhân" className="profile-orb" to="/profile"><User aria-hidden="true" size={28} /></Link>
      </div>
    </header>
  );
}

function HomeValueHero({ date, children }: { date?: string; children?: ReactNode }) {
  const displayDate = date ?? new Date().toISOString().slice(0, 10);
  return (
    <section className="home-value-hero">
      <time dateTime={displayDate}>{date ? formatNoteDate(date) : "Hôm nay"}</time>
      <h1 className="sr-only">Hôm nay có gì đáng để ý?</h1>
      {children}
    </section>
  );
}

function HomeDailySignal({
  activeReading,
  detailPath,
  decoration,
  toolbar,
}: {
  activeReading: NonNullable<DailyNote["reading_projection"]>["active"];
  detailPath: string;
  decoration: ReactNode;
  toolbar: ReactNode;
}) {
  if (!activeReading) return null;
  const experiment = activeReading.experiment;
  const body = activeReading.sections.manifestation || activeReading.sections.thesis;
  const action = experiment?.action || activeReading.sections.micro_action;

  return (
    <section aria-label="Note hôm nay" className="home-daily-signal">
      <article className="home-daily-signal__paper">
        {decoration}
        <p className="home-daily-signal__eyebrow">Hôm nay của bạn</p>
        <h2>{activeReading.sections.hook}</h2>
        {body ? <p className="home-daily-signal__body">{body}</p> : null}
        {action ? (
          <aside aria-label="Việc có thể thử hôm nay" className="home-daily-signal__advice">
            <Sparkle aria-hidden="true" className="home-advice-star" weight="fill" />
            <span>Thử một việc nhỏ</span>
            <p>{action}</p>
          </aside>
        ) : null}
        <footer className="home-note-footer"><Link to={detailPath}>Đọc thêm<ArrowRight aria-hidden="true" /></Link>{toolbar}</footer>
      </article>
    </section>
  );
}

function HomeExploreRoutes() {
  return (
    <section aria-label="Khám phá thêm" className="home-explore-routes">
      <h2>Muốn hỏi chuyện khác?</h2>
      <div className="home-explore-routes__choices">
        <Link to="/tarot">
          <img alt="" src="/assets/ultraviolet/tarot.webp" />
          <span><strong>Rút Tarot</strong><ArrowRight aria-hidden="true" /></span>
        </Link>
        <Link to="/radar">
          <img alt="" src="/assets/ultraviolet/pair.webp" />
          <span><strong>Mình & người ấy</strong><ArrowRight aria-hidden="true" /></span>
        </Link>
      </div>
    </section>
  );
}

function HomeState({ text }: { text: string }) {
  return (
    <main className="app-page home-page signal-note-home">
      <HomeHeader />
      <HomeValueHero />
      <section className="entry-loading"><span className="entry-loading__orbit" /><p>{text}</p></section>
      <HomeExploreRoutes />
      <AppNav />
    </main>
  );
}
