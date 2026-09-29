import {
  ArrowRight,
  HeartStraight,
  Planet,
  Smiley,
  Sparkle,
  UserCircle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
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
import { useDailyExperiment } from "../../shared/hooks/useDailyExperiment";
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
import { ReadingContent } from "../../shared/ui/ReadingContent";
import { ReadingDisclaimer } from "../../shared/ui/ReadingDisclaimer";
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
  const showUnlock = (!activeReading || activeReading.mode !== "full_synthesis")
    && (supplementQuery.data?.profile_level ?? 1) < 2
    && snoozedUntil <= Date.now();

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
      setMoodSheetOpen(false);
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
        <HomePreviewGreeting />
        <HomeQuestionHeading />
        <HomeDailyHeading />
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
        <HomeDiscoveryRouter />
        <AppNav />
      </main>
    );
  }

  const modeLabel = activeReading
    ? activeReading.mode === "full_synthesis" ? "Aura · Tổng hòa lá số" : "Vibe · Một lớp từ ngày sinh"
    : note.persona_mode === "aura" ? "Aura · Tổng hòa lá số" : "Vibe · Một lớp từ ngày sinh";
  const pendingContext = contextMutation.isPending ? contextMutation.variables : null;
  const quickActions = (
    <ResonanceFeedback
      consented={resonanceQuery.data?.consented ?? false}
      onSubmit={(choice) => resonanceMutation.mutate(choice)}
      pending={resonanceMutation.isPending}
      selected={resonance}
    />
  );

  return (
    <main className="app-page home-page signal-note-home">
      <HomeHeader />
      <section className="home-greeting signal-note-greeting">
        <time dateTime={note.note_date}>{formatNoteDate(note.note_date)}</time>
        <h1>{greetingForNow()}, bạn.</h1>
        <span className="transit-pill"><Sparkle aria-hidden="true" weight="fill" /> {modeLabel}</span>
      </section>

      {noteQuery.isError ? (
        <p className="cache-status" role="status">
          {missingSession
            ? <>Đang xem bản đã mở gần nhất trên máy · <Link to="/welcome">Mở lại Trạm để cập nhật Note và Bản đồ</Link></>
            : "Đang xem đúng bản đã mở gần nhất trên máy"}
        </p>
      ) : null}

      <HomeQuestionHeading />
      <HomeDailyHeading />

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
            toolbar={quickActions}
          />
          <div className="signal-note-paper__footer">
            <MoodPicker
              mood={mood}
              onOpenChange={setMoodSheetOpen}
              onSelect={(value) => moodMutation.mutate(value)}
              open={moodSheetOpen}
              pending={moodMutation.isPending}
            />
            <Link className="signal-note-paper__detail" to="/note/today">Đọc note đầy đủ</Link>
          </div>
        </section>
      ) : (
        <section aria-label="Note hôm nay" className="signal-note-paper signal-note-paper--legacy">
          {quickActions}
          <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {modeLabel}</p>
          <h2>{note.title}</h2>
          <p>{note.body}</p>
          <ReadingDisclaimer compact>
            Nội dung dùng để tự soi và đối chiếu; quyết định vẫn thuộc về bạn.
          </ReadingDisclaimer>
          <div className="signal-note-paper__footer">
            <MoodPicker
              mood={mood}
              onOpenChange={setMoodSheetOpen}
              onSelect={(value) => moodMutation.mutate(value)}
              open={moodSheetOpen}
              pending={moodMutation.isPending}
            />
            <Link className="signal-note-paper__detail" to="/note/today">Đọc note đầy đủ</Link>
          </div>
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

      {showUnlock ? (
        <aside className="unlock-note">
          <Planet aria-hidden="true" />
          <div><strong>Còn một lớp chưa mở</strong><p>Thêm giờ và nơi sinh để chuyển từ Vibe sang bản đọc Aura.</p></div>
          <Link to="/birth-time">Mở lớp sâu</Link>
        </aside>
      ) : null}

      <HomeDiscoveryRouter />

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
        <span aria-hidden="true">{selected?.emoji ?? <Smiley weight="duotone" />}</span>
        <strong>{selected?.value ?? "Mood hôm nay?"}</strong>
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

function HomePreviewGreeting() {
  return (
    <section className="home-greeting signal-note-greeting">
      <time dateTime={new Date().toISOString().slice(0, 10)}>Hôm nay</time>
      <h1>{greetingForNow()}, bạn.</h1>
      <span className="transit-pill"><Sparkle aria-hidden="true" weight="fill" /> Chọn điều bạn muốn hiểu</span>
    </section>
  );
}

function HomeQuestionHeading() {
  return (
    <section aria-labelledby="home-question-title" className="home-question-prompt">
      <div className="home-question-router__heading">
        <p className="eyebrow">Bắt đầu từ điều bạn đang nghĩ</p>
        <h2 id="home-question-title">Bạn đang muốn hiểu điều gì?</h2>
        <p>Chọn đúng chuyện bạn đang cần soi.</p>
      </div>
    </section>
  );
}

function HomeDiscoveryRouter() {
  return (
    <section aria-label="Khám phá thêm" className="home-question-router home-discovery-router">
      <div className="home-discovery-router__heading">
        <p className="eyebrow">Muốn soi thêm một chuyện?</p>
        <h2>Chọn góc tiếp theo</h2>
      </div>
      <Link className="home-tarot-spotlight" to="/tarot">
        <span aria-hidden="true" className="home-tarot-spotlight__cards"><i /><i /><i>✦</i></span>
        <span className="home-tarot-spotlight__copy">
          <small>Lá Hỏi · Tarot</small>
          <strong>Có chuyện cứ chạy trong đầu?</strong>
          <em>Đặt câu hỏi, chọn lá, nhìn rõ bước tiếp theo.</em>
        </span>
        <span className="home-tarot-spotlight__action">Hỏi Lá <ArrowRight aria-hidden="true" /></span>
      </Link>
      <div className="home-question-router__choices">
        <Link aria-describedby="home-question-self-hint" to="/natal">
          <UserCircle aria-hidden="true" weight="duotone" />
          <span><strong>Mình</strong><small id="home-question-self-hint">Nhìn pattern của bạn</small></span>
          <ArrowRight aria-hidden="true" />
        </Link>
        <Link aria-describedby="home-question-person-hint" to="/radar">
          <HeartStraight aria-hidden="true" weight="duotone" />
          <span><strong>Một người</strong><small id="home-question-person-hint">Check độ hợp gu</small></span>
          <ArrowRight aria-hidden="true" />
        </Link>
        <Link aria-describedby="home-question-world-hint" state={{ from: "home" }} to="/insights/current-sky?tradition=western">
          <Planet aria-hidden="true" weight="duotone" />
          <span><strong>Hôm nay</strong><small id="home-question-world-hint">Xem bối cảnh đang tác động</small></span>
          <ArrowRight aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}

function HomeDailyHeading() {
  return (
    <section className="home-daily-heading" aria-labelledby="home-daily-title">
      <p className="eyebrow">Tín hiệu hôm nay</p>
      <h2 id="home-daily-title">Còn đây là một góc dành riêng cho hôm nay.</h2>
    </section>
  );
}

function HomeState({ text }: { text: string }) {
  return (
    <main className="app-page home-page signal-note-home">
      <HomeHeader />
      <HomePreviewGreeting />
      <HomeQuestionHeading />
      <HomeDailyHeading />
      <section className="entry-loading"><span className="entry-loading__orbit" /><p>{text}</p></section>
      <HomeDiscoveryRouter />
      <AppNav />
    </main>
  );
}
