import {
  ArrowClockwise,
  ArrowRight,
  CaretRight,
  Pause,
  Play,
  Smiley,
  Sparkle,
  User,
  X,
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
import { chartDataRevision } from "../../shared/storage/clearChartDerivedData";
import { birthCompletionPrompt } from "../../shared/astro/birthReadiness";
import { dailyContextPath, dailyContextQueryKey } from "../../shared/astro/dailyContext";
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
import { WHY_TODAY_ID } from "../../shared/ui/readingLabels";
import { ResonanceFeedback } from "../../shared/ui/ResonanceFeedback";
import { SignalContextPicker } from "../../shared/ui/SignalContextPicker";
import { laMoodReaction } from "../../shared/ui/la/laVoice";
import { moonPhase } from "../../shared/ui/la/moonPhase";
import { useVibe } from "../../shared/vibe/useVibe";
import { tapFeedback } from "../../shared/ui/la/haptics";
import { NightSky } from "../../shared/ui/NightSky";
import { homeCompanionLine, type HomeCompanionState } from "./companionLine";
import { NightNudgeNotice, WeekRecapNotice } from "./HomeRituals";
import { useNightNudge, useWeekRecap } from "./homeRitualState";
import "./home-vitality.css";

const RITUAL_KEY = "la-lanh-daily-ritual-v1";
const UNLOCK_SNOOZE_KEY = "la-lanh-birth-supplement-snooze-until";

/** True once per note date: the first open of the day plays the unfold ritual. */
function useDailyRitual(noteDate: string | undefined): boolean {
  const [ritual] = useState(() => {
    if (!noteDate) return false;
    try { return localStorage.getItem(RITUAL_KEY) !== noteDate; } catch { return false; }
  });
  useEffect(() => {
    if (!noteDate) return;
    // Stores only the calendar date of the note, never note content or mood.
    try { localStorage.setItem(RITUAL_KEY, noteDate); } catch { /* Storage may be unavailable. */ }
  }, [noteDate]);
  return ritual;
}

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
  const { vibe } = useVibe();
  const direct = vibe === "direct";
  const noteQuery = useQuery({
    queryKey: dailyContextQueryKey("auto", vibe),
    queryFn: async ({ signal }) => {
      const freshNote = direct ? await getDailyNote(signal) : await getDailyNote(signal, vibe);
      // The offline cache keeps the direct wording only.
      if (direct) writeCachedDailyNote(freshNote);
      return freshNote;
    },
    initialData: direct ? cachedAtStart?.note : undefined,
    initialDataUpdatedAt: direct && cachedAtStart ? 0 : undefined,
  });
  const baseNote = noteQuery.data;
  const [contextualNote, setContextualNote] = useState<{ note: DailyNote; revision: number }>();
  const [contextChoice, setContextChoice] = useState<{ value: SignalContext; revision: number }>({ value: "auto", revision: chartDataRevision(queryClient) });
  const currentRevision = chartDataRevision(queryClient);
  const context = contextChoice.revision === currentRevision ? contextChoice.value : "auto";
  const [contextSheetOpen, setContextSheetOpen] = useState(false);
  const [motionPaused, setMotionPaused] = useState(false);
  const note = contextualNote?.revision === currentRevision ? contextualNote.note : baseNote;
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
  const moonLabel = useMemo(() => moonPhase().label, []);
  const ritual = useDailyRitual(note?.note_date);
  const [moodSheetOpen, setMoodSheetOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [resonance, setResonance] = useState<ResonanceChoice | null>(null);
  const [, refreshGift] = useState(0);
  const [, refreshUnlock] = useState(0);
  const [recapDismissed, setRecapDismissed] = useState(false);
  const [lineDismissed, setLineDismissed] = useState(false);
  const nightNudge = useNightNudge();
  const recapCount = useWeekRecap();
  const showGift = Boolean(
    context === "auto"
    && note?.reading_projection
    && availableUpdate
    && !isReadingUpdateDismissed(note.reading_projection.scope_key, availableUpdate.revision_id)
  );
  const snoozedUntil = Number(localStorage.getItem(UNLOCK_SNOOZE_KEY) ?? 0);
  const completionPrompt = birthCompletionPrompt(supplementQuery.data);
  const showUnlock = Boolean(completionPrompt) && snoozedUntil <= Date.now();

  const contextMutation = useMutation({
    onMutate: () => ({ revision: chartDataRevision(queryClient) }),
    mutationFn: async (nextContext: SignalContext) => {
      if (nextContext === "auto") {
        if (!baseNote) throw new Error("Missing daily note");
        return baseNote;
      }
      const cached = queryClient.getQueryData<DailyNote>(dailyContextQueryKey(nextContext, vibe));
      if (cached) return cached;
      if (!baseNote) throw new Error("Missing daily note");
      const projection = direct
        ? await getContextualReading(nextContext)
        : await getContextualReading(nextContext, undefined, vibe);
      return { ...baseNote, reading_projection: projection };
    },
    onSuccess: (nextNote, nextContext, requestContext) => {
      if (requestContext.revision !== chartDataRevision(queryClient)) return;
      if (nextContext !== "auto") {
        queryClient.setQueryData(dailyContextQueryKey(nextContext, vibe), nextNote);
        setContextualNote({ note: nextNote, revision: requestContext.revision });
      } else {
        setContextualNote(undefined);
      }
      setContextChoice({ value: nextContext, revision: requestContext.revision });
      setContextSheetOpen(false);
      setResonance(null);
      setMessage(nextContext === "auto" ? "Đã trở về góc tự động." : "Đã đổi góc nhìn cho note này.");
    },
    onError: (_error, _input, requestContext) => {
      if (!requestContext || requestContext.revision !== chartDataRevision(queryClient)) return;
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
      setMessage(laMoodReaction(payload.mood, vibe));
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

  if (noteQuery.isLoading) return <HomeLoading />;
  const missingSession = isGuestSessionUnavailable(noteQuery.error);

  if (!note) {
    const heading = missingSession ? "Phiên riêng đã khép lại." : noteQuery.isError ? "Note chưa về kịp." : "Chưa có Lá để nhắc bạn.";
    return (
      <main className="app-page home-page signal-note-home" data-home-motion="running">
        <HomeHeader />
        <HomeValueHero moon={moonLabel} />
        <section className="home-daily-signal__paper home-note-state" role={noteQuery.isError || missingSession ? "alert" : undefined}>
          <NightSky dim moon nebula={false} stars={3} />
          <p className="home-daily-signal__eyebrow">Hôm nay của bạn</p>
          <h1>{heading}</h1>
          <p className="home-daily-signal__body">{missingSession
            ? "Mở lại Trạm Bắt Sóng để nối đúng note và Bản đồ của bạn. Chưa cần tài khoản."
            : noteQuery.isError
              ? "Kiểm tra kết nối rồi thử lại."
              : "Khai ngày sinh trước, rồi Lá Lành sẽ để lại một note nhỏ mỗi ngày."}</p>
          {missingSession
            ? <Link className="electric-button" to="/welcome">Mở lại Trạm Bắt Sóng</Link>
            : noteQuery.isError
            ? <button className="electric-button" onClick={() => void noteQuery.refetch()} type="button"><ArrowClockwise aria-hidden="true" weight="bold" />Thử lại</button>
            : <Link className="electric-button" to="/birth">Khai ngày sinh</Link>}
        </section>
        <HomeCompanion line={homeCompanionLine({ state: noteQuery.isError ? "error" : "idle", vibe }).text} />
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
    <main className="app-page home-page signal-note-home" data-home-motion={motionPaused ? "paused" : "running"} data-ritual={ritual ? "today" : undefined}>
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
      <HomeValueHero date={note.note_date} moon={moonLabel} whyPath={activeReading?.sections.transit ? `${dailyContextPath("/note/today", context)}#${WHY_TODAY_ID}` : undefined}>
        <MoodPicker mood={mood} onOpenChange={setMoodSheetOpen} onSelect={(value) => { tapFeedback(); moodMutation.mutate(value); }} open={moodSheetOpen} pending={moodMutation.isPending} />
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
            <NightSky glow orbits planet />
            {noteDecoration}
            <div className="home-daily-signal__copy">
              <p className="home-daily-signal__eyebrow">Hôm nay của bạn</p>
              <h2>{note.title}</h2>
              <p className="home-daily-signal__body">{note.body}</p>
            </div>
            <div className="home-daily-signal__glass uv-glass">
              <footer className="home-note-footer"><Link to={dailyContextPath("/note/today", context)}>Đọc đầy đủ<ArrowRight aria-hidden="true" weight="bold" /></Link>{quickActions}</footer>
            </div>
          </article>
        </section>
      )}

      <HomeCompanion line={lineDismissed ? null : homeCompanionLine({ vibe, companion: activeReading?.sections.companion }).text} onDismissLine={() => setLineDismissed(true)}>
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
        ) : showUnlock && completionPrompt ? (
          <aside aria-label="Còn lá ẩn chờ bạn mở" className="home-la-notice unlock-note">
            <strong className="home-la-notice__eyebrow">Còn lá ẩn chờ bạn mở</strong>
            <p className="home-la-notice__title">{completionPrompt.body}</p>
            <Link className="home-la-notice__cta" to="/birth-time">{completionPrompt.cta}<ArrowRight aria-hidden="true" /></Link>
            <button
              aria-label="Để 3 ngày sau"
              className="home-la-notice__close"
              onClick={() => {
                // Same timestamp-only snooze the birth-time page already writes.
                try { localStorage.setItem(UNLOCK_SNOOZE_KEY, String(Date.now() + 3 * 24 * 60 * 60 * 1000)); } catch { /* Storage may be unavailable. */ }
                refreshUnlock((value) => value + 1);
              }}
              type="button"
            ><X aria-hidden="true" /></button>
          </aside>
        ) : recapCount && !recapDismissed ? (
          <WeekRecapNotice count={recapCount} onDismiss={() => setRecapDismissed(true)} />
        ) : nightNudge ? (
          <NightNudgeNotice {...nightNudge} />
        ) : null}
      </HomeCompanion>

      <HomeExploreRoutes />

      <p className="sr-only" aria-live="polite" role="status">{message}</p>
      {message ? <p className="home-status" aria-hidden="true">{message}</p> : null}

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
        <span aria-hidden="true">{selected ? <span className="mood-quick-trigger__emoji">{selected.emoji}</span> : <Smiley weight="regular" size={22} />}</span>
        <span aria-hidden="true" className="mood-quick-trigger__label">{selected?.value ?? "Chọn mood"}</span>
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
        <Link aria-label="Trang cá nhân" className="profile-orb" to="/profile"><User aria-hidden="true" size={22} /></Link>
      </div>
    </header>
  );
}

function HomeValueHero({ date, moon, whyPath, children }: { date?: string; moon?: string; whyPath?: string; children?: ReactNode }) {
  const displayDate = date ?? new Date().toISOString().slice(0, 10);
  return (
    <section className="home-value-hero">
      <div className="home-value-hero__lead">
        <img alt="" className="home-value-hero__moon-art" src="/assets/ultraviolet/moon.webp" />
        <div className="home-value-hero__meta">
          <time dateTime={displayDate}>{date ? formatNoteDate(date) : "Hôm nay"}</time>
          {moon ? <span className="home-value-hero__moon">{moon}</span> : null}
          {whyPath ? <Link className="home-value-hero__why" to={whyPath}>Vì sao hôm nay?</Link> : null}
        </div>
      </div>
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
        <NightSky glow orbits planet />
        {decoration}
        <div className="home-daily-signal__copy">
          <p className="home-daily-signal__eyebrow">Hôm nay của bạn</p>
          <h2>{activeReading.sections.hook}</h2>
          {body ? <p className="home-daily-signal__body">{body}</p> : null}
        </div>
        <div className="home-daily-signal__glass uv-glass">
          {action ? (
            <aside aria-label="Việc có thể thử hôm nay" className="home-daily-signal__advice">
              <Sparkle aria-hidden="true" className="home-advice-star" weight="fill" />
              <span>Thử một việc nhỏ</span>
              <p>{action}</p>
            </aside>
          ) : null}
          <footer className="home-note-footer"><Link to={detailPath}>Đọc đầy đủ<ArrowRight aria-hidden="true" weight="bold" /></Link>{toolbar}</footer>
        </div>
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
          <strong>Rút Tarot</strong>
          <CaretRight aria-hidden="true" weight="bold" />
        </Link>
        <Link to="/radar">
          <img alt="" src="/assets/ultraviolet/pair.webp" />
          <strong>Mình & người ấy</strong>
          <CaretRight aria-hidden="true" weight="bold" />
        </Link>
      </div>
    </section>
  );
}

/** Lá's row: the sprout and one speech bubble, which is also the single "Lá nhắc" slot. */
function HomeCompanion({
  children,
  line,
  onDismissLine,
  status = false,
}: {
  children?: ReactNode;
  line: string | null;
  onDismissLine?: () => void;
  status?: boolean;
}) {
  const notice = Boolean(children);
  if (!notice && !line) return null;
  return (
    <div className="home-la-row">
      <img alt="" className="home-la-row__sprout" src="/assets/ultraviolet/sprout-3d.png" />
      <div className={notice ? "home-la-row__bubble home-la-row__bubble--notice" : "home-la-row__bubble"}>
        {notice ? children : <>
          <p className="home-la-row__line" role={status ? "status" : undefined}>{line}</p>
          {onDismissLine ? <button aria-label="Ẩn câu của Lá" className="home-la-notice__close" onClick={onDismissLine} type="button"><X aria-hidden="true" /></button> : null}
        </>}
      </div>
    </div>
  );
}

function HomeLoading() {
  const { vibe } = useVibe();
  const state: HomeCompanionState = "loading";
  return (
    <main className="app-page home-page signal-note-home" data-home-motion="running">
      <HomeHeader />
      <HomeValueHero moon={moonPhase().label} />
      <section aria-busy="true" aria-label="Đang mở tín hiệu hôm nay" className="home-daily-signal__paper home-note-skeleton">
        <NightSky moon nebula={false} stars={0} />
        <span className="uv-skeleton uv-skeleton--night" style={{ width: 130, height: 11 }} />
        <span className="uv-skeleton uv-skeleton--night" style={{ width: "min(230px, 80%)", height: 24, marginTop: 20 }} />
        <span className="uv-skeleton uv-skeleton--night" style={{ width: "min(200px, 70%)", height: 24, marginTop: 10 }} />
        <span className="uv-skeleton uv-skeleton--night" style={{ width: 120, height: 24, marginTop: 10 }} />
        <span className="uv-skeleton uv-skeleton--night" style={{ width: "min(280px, 95%)", height: 13, marginTop: 20 }} />
        <span className="uv-skeleton uv-skeleton--night" style={{ width: "min(220px, 78%)", height: 13, marginTop: 9 }} />
        <span className="home-note-skeleton__panel">
          <span className="uv-skeleton uv-skeleton--night" style={{ width: 120, height: 10 }} />
          <span className="uv-skeleton uv-skeleton--night" style={{ width: "min(240px, 90%)", height: 12, marginTop: 14 }} />
          <span className="uv-skeleton uv-skeleton--night" style={{ width: "min(180px, 70%)", height: 12, marginTop: 9 }} />
        </span>
      </section>
      <HomeCompanion line={homeCompanionLine({ state, vibe }).text} status />
      <HomeExploreRoutes />
      <AppNav />
    </main>
  );
}
