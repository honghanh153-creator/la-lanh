import {
  ArrowLeft,
  ArrowRight,
  Briefcase,
  CheckCircle,
  Eye,
  HeartStraight,
  LockKey,
  Sparkle,
  Trash,
  UserCircle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import {
  ApiProblem,
  currentSessionEpoch,
  createTarotGuest,
  deleteTarotSession,
  getSession,
  getTarotSession,
  selectTarotCard,
  startTarotSession,
  type TarotCard,
  type TarotContext,
  type TarotSession,
  type TarotSpread,
} from "../../shared/api/client";
import { SESSION_RESTART_REQUIRED_KEY } from "../../shared/session/sessionIdentity";
import { BrandMark } from "../../shared/ui/BrandMark";
import { NightSky } from "../../shared/ui/NightSky";
import { ReadingDisclaimer } from "../../shared/ui/ReadingDisclaimer";
import { TarotCardArt, TarotCardBack } from "./TarotCardArt";
import { TarotPickFlight } from "./TarotPickFlight";
import { TarotRevealCeremony } from "./TarotRevealCeremony";
import { useTarotMotion } from "./useTarotMotion";
import "./tarot.css";
import "./tarot-polish.css";
import { useVibe } from "../../shared/vibe/useVibe";

const CONTEXTS: Array<{ key: TarotContext; label: string; hint: string }> = [
  { key: "general", label: "Một chuyện", hint: "Chưa cần gọi tên ngay" },
  { key: "relationships", label: "Quan hệ", hint: "Crush, bạn bè, người yêu" },
  { key: "work", label: "Công việc", hint: "Việc, hướng đi, ranh giới" },
  { key: "communication", label: "Giao tiếp", hint: "Một câu đang khó nói" },
  { key: "energy", label: "Năng lượng", hint: "Điều đang làm bạn cạn pin" },
  { key: "self_care", label: "Bản thân", hint: "Nhu cầu đang bị để sau" },
];

const QUESTIONS: Record<TarotContext, string[]> = {
  general: [
    "Mình đang biết điều gì, và đang tự điền phần nào?",
    "Chuyện này cần được nhìn từ góc nào trước?",
    "Một bước nhỏ nào giúp mình bớt mắc kẹt?",
  ],
  relationships: [
    "Giữa tụi mình, điều gì đáng hỏi thẳng thay vì tiếp tục đoán?",
    "Mình đang mang kỳ vọng nào vào kết nối này?",
    "Nếu tiến thêm một nhịp, ranh giới nào nên nói rõ trước?",
  ],
  work: [
    "Việc nào đang lấy công sức nhưng chưa có tiêu chí hoàn thành rõ?",
    "Mình cần nói rõ điều gì trước khi nhận thêm việc?",
    "Bước tiếp theo nào đủ nhỏ để thử mà chưa phải cược tất cả?",
  ],
  communication: [
    "Câu chính nào mình đang né bằng quá nhiều lời giải thích?",
    "Trong cuộc nói chuyện này, điều gì đáng hỏi lại cho rõ?",
    "Mình có thể nói thẳng điều gì mà vẫn giữ được ranh giới?",
  ],
  energy: [
    "Điều gì đang tiêu hao nhiều hơn giá trị nó trả lại?",
    "Mình cần bỏ bớt nhịp nào trước khi thêm giải pháp?",
    "Cơ thể đang báo điều gì mà lịch của mình chưa chịu nghe?",
  ],
  self_care: [
    "Nhu cầu nào của mình đang bị xếp sau mọi người?",
    "Mình đang cần nghỉ, cần giúp hay chỉ cần nói thật một câu?",
    "Một việc chăm mình nào đủ nhỏ để làm ngay hôm nay?",
  ],
};

const PROMPT_CONTEXT: Record<string, TarotContext> = {
  "daily-clarity": "general",
  "daily-next-step": "energy",
  "radar-ask-directly": "relationships",
  "radar-expectation": "relationships",
  "radar-boundary": "relationships",
};

const PROMPT_QUESTION: Record<string, string> = {
  "daily-clarity": QUESTIONS.general[1],
  "daily-next-step": QUESTIONS.energy[1],
  "daily-self-check": QUESTIONS.self_care[1],
  "radar-ask-directly": QUESTIONS.relationships[0],
  "radar-expectation": QUESTIONS.relationships[1],
  "radar-boundary": QUESTIONS.relationships[2],
};

const SPREAD_OPTIONS: Array<{
  key: TarotSpread;
  label: string;
  short: string;
}> = [
  { key: "one_card", label: "1 lá", short: "nhanh" },
  { key: "three_card", label: "3 lá", short: "vừa đủ" },
  { key: "five_card", label: "5 lá", short: "đào sâu" },
];

const SPREAD_COPY: Record<TarotSpread, { title: string; reason: string }> = {
  one_card: {
    title: "1 lá · Chạm đúng điểm",
    reason: "Một góc đủ rõ để bạn đối chiếu ngay với chuyện đang xảy ra.",
  },
  three_card: {
    title: "3 lá · Nhìn rõ trước khi hành động",
    reason: "Đủ để thấy điều đã rõ, điểm dễ bỏ sót và một bước có thể thử.",
  },
  five_card: {
    title: "5 lá · Gỡ chuyện nhiều lớp",
    reason: "Tách dữ kiện, nhu cầu, điểm cấn, phần bạn chọn được và một bước để thử.",
  },
};

function recommendSpread(question: string): TarotSpread {
  const normalized = question.trim().toLocaleLowerCase("vi");
  const needsFive = /(?:giữa|hay là|nên chọn|lựa chọn|ở lại|rời đi|lặp lại|lần nào cũng|cứ mỗi|nói chuyện khó|ranh giới)/i.test(normalized);
  if (needsFive) {
    return "five_card";
  }
  if (normalized.length >= 8 && normalized.length <= 22) {
    return "one_card";
  }
  return "three_card";
}

function startKey(signature: string): string {
  const storageKey = "la-lanh-tarot-start";
  const raw = sessionStorage.getItem(storageKey);
  if (raw) {
    try {
      const cached = JSON.parse(raw) as { signature?: string; key?: string };
      if (cached.signature === signature && cached.key) return cached.key;
    } catch {
      sessionStorage.removeItem(storageKey);
    }
  }
  const key = crypto.randomUUID();
  sessionStorage.setItem(storageKey, JSON.stringify({ signature, key }));
  return key;
}

async function ensureTarotGuest(): Promise<void> {
  const expectedEpoch = currentSessionEpoch();
  try {
    const session = await getSession();
    if (expectedEpoch && expectedEpoch !== session.session_epoch) {
      sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
      throw new ApiProblem(401, "SESSION_CHANGED", "Phiên trên trình duyệt đã đổi.");
    }
  } catch (error) {
    if (error instanceof ApiProblem && error.code === "SESSION_CHANGED") throw error;
    if (!(error instanceof ApiProblem) || error.status !== 401) throw error;
    const key = sessionStorage.getItem("la-lanh-tarot-guest-key") ?? crypto.randomUUID();
    sessionStorage.setItem("la-lanh-tarot-guest-key", key);
    await createTarotGuest(key);
    sessionStorage.removeItem("la-lanh-tarot-guest-key");
  }
}

type PickFlight = { key: string; fanIndex: number; slotIndex: number; card: TarotCard };

function contextFromQuery(promptId: string | null, rawContext: string | null): TarotContext {
  if (promptId && PROMPT_CONTEXT[promptId]) return PROMPT_CONTEXT[promptId];
  return CONTEXTS.some((item) => item.key === rawContext) ? rawContext as TarotContext : "general";
}

export function TarotPage() {
  const { vibe } = useVibe();
  const { sessionId } = useParams();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const promptId = search.get("prompt");
  const source = search.get("origin");
  const origin = source === "daily" || source === "radar" ? source : "direct";
  const initialContext = contextFromQuery(promptId, search.get("context"));
  const initialQuestion = promptId && PROMPT_QUESTION[promptId]
    ? PROMPT_QUESTION[promptId]
    : "";
  const [context, setContext] = useState<TarotContext>(initialContext);
  const [question, setQuestion] = useState(initialQuestion);
  const recommendation = useMemo(() => recommendSpread(question), [question]);
  const questionTooShort = question.trim().length < 8;
  const [spreadOverride, setSpreadOverride] = useState<TarotSpread | null>(null);
  const spread = spreadOverride ?? recommendation;
  const selectedSpreadCopy = SPREAD_COPY[spread];
  const [showStarters, setShowStarters] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [revealSessionId, setRevealSessionId] = useState<string | null>(null);
  const finishReveal = useCallback(() => setRevealSessionId(null), []);
  useEffect(() => () => finishReveal(), [sessionId, finishReveal]);
  const [reframe, setReframe] = useState<{ explanation: string; question: string } | null>(null);
  const motion = useTarotMotion();
  const [flight, setFlight] = useState<PickFlight | null>(null);
  const endFlight = useCallback(() => setFlight(null), []);

  const sessionQuery = useQuery({
    queryKey: ["tarot-session", sessionId],
    queryFn: ({ signal }) => getTarotSession(sessionId ?? "", signal),
    enabled: Boolean(sessionId),
    retry: false,
  });
  const session = sessionQuery.data;

  const start = useMutation({
    mutationFn: async () => {
      await ensureTarotGuest();
      const signature = JSON.stringify({ context, question: question.trim(), spread, origin, promptId, vibe });
      return startTarotSession({
        context,
        question: question.trim(),
        spread,
        origin,
        prompt_id: promptId,
        idempotency_key: startKey(signature),
        ...(vibe === "roast" ? { voice: vibe } : {}),
      });
    },
    onSuccess: (created) => {
      sessionStorage.removeItem("la-lanh-tarot-start");
      setReframe(null);
      queryClient.setQueryData(["tarot-session", created.id], created);
      void navigate(`/tarot/${created.id}`, { replace: true });
    },
    onError: (error) => {
      if (error instanceof ApiProblem && error.code === "SESSION_CHANGED") {
        void navigate("/welcome?restart=1", { replace: true, state: { sessionChanged: true } });
        return;
      }
      if (error instanceof ApiProblem && error.code === "TAROT_QUESTION_REFRAME_REQUIRED") {
        const suggested = error.details.suggested_reframe;
        const explanation = error.details.explanation;
        if (typeof suggested === "string" && typeof explanation === "string") {
          setReframe({ explanation, question: suggested });
        }
      }
    },
  });

  const select = useMutation({
    mutationFn: ({ active, index }: { active: TarotSession; index: number }) => (
      selectTarotCard(active.id, index, active.version)
    ),
    onSuccess: (updated, { active, index }) => {
      if (active.state === "choosing" && updated.state === "complete" && updated.reading) {
        setRevealSessionId(updated.id);
      } else if (motion && updated.state === "choosing") {
        // Presentation only: fly the newly revealed card into its slot.
        const slotIndex = updated.selected_cards.findIndex((item) => item.fan_index === index);
        const picked = updated.selected_cards[slotIndex];
        if (picked && slotIndex >= active.selected_cards.length) {
          setFlight({ key: `${updated.id}:${index}`, fanIndex: index, slotIndex, card: picked.card });
        }
      }
      queryClient.setQueryData(["tarot-session", updated.id], updated);
    },
    onError: () => {
      void sessionQuery.refetch();
    },
  });

  const remove = useMutation({
    mutationFn: (active: TarotSession) => deleteTarotSession(active.id),
    onSuccess: (_data, active) => {
      queryClient.removeQueries({ queryKey: ["tarot-session", active.id] });
      void navigate("/tarot", { replace: true });
      setConfirmDelete(false);
    },
  });

  const selectedIndexes = useMemo(
    () => new Set(session?.selected_cards.map((item) => item.fan_index) ?? []),
    [session?.selected_cards],
  );

  if (sessionId && sessionQuery.isLoading) {
    return <TarotFrame scene step="Đang mở lại"><section className="tarot-loading" aria-label="Đang mở lại phiên Tarot"><span /></section></TarotFrame>;
  }
  if (sessionId && sessionQuery.isError) {
    return <TarotFrame step="Phiên riêng tư"><section className="tarot-state"><h1>Không mở lại được lần bốc này.</h1><p>Phiên có thể đã hết hạn, đã được xóa hoặc thuộc một trình duyệt khác.</p><Link className="tarot-primary" to="/tarot">Bắt đầu lần mới</Link></section></TarotFrame>;
  }
  if (session?.state === "complete" && !session.reading) {
    return <TarotFrame step="Bộ lá đã chọn">
      <section className="tarot-state" role="status">
        <h1>Chưa mở được phần diễn giải.</h1>
        <p>Bộ lá của bạn không thay đổi.</p>
        <ul>{session.selected_cards.map((selected) => <li key={selected.card.id}>
          {selected.position_label}: {selected.card.title_vi}
        </li>)}</ul>
        <Link className="tarot-primary" to="/home">Về hôm nay</Link>
        <button className="tarot-secondary" disabled={remove.isPending} onClick={() => {
          if (confirmDelete) remove.mutate(session);
          else setConfirmDelete(true);
        }} type="button">{confirmDelete ? "Xác nhận xóa" : "Xóa lần bốc này"}</button>
        {confirmDelete ? <button onClick={() => setConfirmDelete(false)} type="button">Giữ lại</button> : null}
        {remove.isError ? <p role="alert">Chưa xóa được. Bạn có thể thử lại.</p> : null}
      </section>
    </TarotFrame>;
  }
  if (session?.state === "complete" && session.reading) {
    if (revealSessionId === session.id) {
      return <TarotFrame scene step="Đang mở bài"><TarotRevealCeremony
        cards={session.selected_cards}
        onComplete={finishReveal}
      /></TarotFrame>;
    }
    return <TarotResult
      confirmDelete={confirmDelete}
      deleting={remove.isPending}
      onDelete={() => {
        if (confirmDelete) remove.mutate(session);
        else setConfirmDelete(true);
      }}
      onKeep={() => setConfirmDelete(false)}
      session={session}
    />;
  }
  if (session) {
    const lastPicked = session.selected_cards.at(-1);
    const pendingIndex = select.isPending ? select.variables?.index ?? null : null;
    const activeFlight = flight && flight.slotIndex < session.selected_cards.length ? flight : null;
    return (
      <TarotFrame scene step={`${session.selected_cards.length}/${session.required_cards} lá`}>
        <section className="tarot-draw-intro">
          <p className="tarot-kicker">Bộ bài đã được khóa cho lần này</p>
          <h1>Chạm lá khiến bạn dừng mắt.</h1>
          <p>Không có lá “đúng” để săn. Thứ tự đã được giữ nguyên trên máy chủ trước khi xòe.</p>
        </section>
        <div className="tarot-question-ticket"><span>Câu bạn mang vào</span><strong>{session.question}</strong></div>
        <div
          aria-label="Các vị trí đã chọn"
          className="tarot-slots"
          data-count={session.required_cards}
          data-tarot-motion={motion ? "on" : "off"}
        >
          {Array.from({ length: session.required_cards }, (_, index) => {
            const selected = session.selected_cards[index];
            const arriving = activeFlight?.slotIndex === index;
            return <div className={selected ? "tarot-slot tarot-slot--filled" : "tarot-slot"} key={index}>
              <span className={arriving ? "tarot-slot__art is-arriving" : "tarot-slot__art"} data-slot-art={index}>
                {selected
                  ? <TarotCardArt card={selected.card} compact decorative />
                  : <span aria-hidden="true" className="tarot-slot__placeholder"><Sparkle weight="fill" /></span>}
              </span>
              <span className="tarot-slot__copy">
                <span>{selected?.position_label ?? `Lá ${index + 1}`}</span>
                <strong>{selected?.card.title_vi ?? "Chưa chọn"}</strong>
              </span>
            </div>;
          })}
        </div>
        <p aria-live="polite" className="sr-only">
          {lastPicked ? `Đã lật ${lastPicked.card.title_vi} cho ${lastPicked.position_label}.` : ""}
        </p>
        <section className="tarot-fan-wrap" aria-label="Bộ bài đang xòe" data-tarot-motion={motion ? "on" : "off"}>
          <p>Kéo ngang rồi chọn một lá</p>
          <TarotFan
            busy={select.isPending}
            fanSize={session.fan_size}
            onPick={(index) => select.mutate({ active: session, index })}
            pendingIndex={pendingIndex}
            selected={selectedIndexes}
          />
        </section>
        {activeFlight ? <TarotPickFlight
          card={activeFlight.card}
          from={() => document.querySelector<HTMLElement>(`[data-fan-index="${activeFlight.fanIndex}"]`)}
          key={activeFlight.key}
          onDone={endFlight}
          to={() => document.querySelector<HTMLElement>(`[data-slot-art="${activeFlight.slotIndex}"]`)}
        /> : null}
        {select.isError ? <p className="tarot-error" role="alert">Kết nối vừa hụt một nhịp. Lá đã chọn vẫn được giữ; mình đang đồng bộ lại.</p> : null}
        <p className="tarot-private"><LockKey aria-hidden="true" /> Chỉ trình duyệt này mở lại được phiên. Không có chế độ bốc offline.</p>
      </TarotFrame>
    );
  }

  return (
    <TarotFrame step="Lá Hỏi">
      <section className="tarot-question-first" aria-labelledby="tarot-question-title">
        <p className="tarot-kicker">Trạm bắt sóng bên trong bạn</p>
        <h1 id="tarot-question-title">Bạn đang muốn gỡ chuyện gì?</h1>
        <label className="tarot-question-field tarot-question-field--hero">
          <span className="sr-only">Câu hỏi của bạn</span>
          <textarea
            maxLength={280}
            onChange={(event) => {
              setQuestion(event.target.value);
              setSpreadOverride(null);
              setReframe(null);
            }}
            placeholder="Ví dụ: Mình nên nói rõ hay chờ thêm?"
            rows={3}
            value={question}
          />
          <small>{question.length}/280</small>
        </label>

        <div aria-label="Chủ đề câu hỏi" className="tarot-context-chips" role="group">
          {CONTEXTS.map((item) => (
            <button
              aria-label={item.label}
              aria-pressed={context === item.key}
              className={context === item.key ? "is-active" : ""}
              key={item.key}
              onClick={() => {
                setContext(item.key);
                setSpreadOverride(null);
                setReframe(null);
              }}
              type="button"
            >
              {item.key === "relationships" ? <HeartStraight aria-hidden="true" /> : null}
              {item.key === "work" ? <Briefcase aria-hidden="true" /> : null}
              {item.key === "self_care" ? <UserCircle aria-hidden="true" /> : null}
              {context === item.key ? <CheckCircle aria-hidden="true" weight="fill" /> : null}
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        <section className="tarot-recommendation" aria-labelledby="tarot-spread-title">
          <div className="tarot-recommendation__copy">
            <span><Sparkle aria-hidden="true" weight="fill" /> {spreadOverride ? "Bạn đã chọn" : "Lá gợi ý"}</span>
            <h2 id="tarot-spread-title">{selectedSpreadCopy.title}</h2>
            <p>{selectedSpreadCopy.reason}</p>
          </div>
          <img alt="" className="tarot-recommendation__icon" src="/assets/ultraviolet/tarot.webp" />
          <div className="tarot-depth" role="group" aria-label="Đổi độ sâu">
            <span>Đổi độ sâu</span>
            {SPREAD_OPTIONS.map((option) => (
              <button
                aria-label={`${option.label}, ${option.short}`}
                aria-pressed={spread === option.key}
                className={spread === option.key ? "is-active" : ""}
                key={option.key}
                onClick={() => setSpreadOverride(option.key)}
                type="button"
              >
                <strong>{option.label}</strong><small>{option.short}</small>
              </button>
            ))}
          </div>
        </section>

        {reframe ? <aside className="tarot-reframe" role="alert"><strong>Đổi góc một chút để bài không nói hộ bạn.</strong><p>{reframe.explanation}</p><button onClick={() => { setQuestion(reframe.question); setSpreadOverride(null); setReframe(null); }} type="button">Dùng câu: “{reframe.question}”</button></aside> : null}
      </section>

      {start.isError && !reframe ? <p className="tarot-error" role="alert">Chưa xòe bài được. Câu hỏi vẫn ở đây; kiểm tra mạng rồi thử lại.</p> : null}
      <footer className="tarot-start-actions">
        <button
          aria-describedby={questionTooShort && !start.isPending ? "tarot-start-hint" : undefined}
          className="tarot-primary"
          disabled={start.isPending || questionTooShort}
          onClick={() => start.mutate()}
          type="button"
        ><Sparkle aria-hidden="true" />{start.isPending ? "Đang khóa bộ bài…" : `Xòe ${spread === "one_card" ? "1" : spread === "three_card" ? "3" : "5"} lá`}<ArrowRight aria-hidden="true" /></button>
        {questionTooShort && !start.isPending ? <p className="tarot-start-hint" id="tarot-start-hint">Nhập câu hỏi từ 8 ký tự trở lên, hoặc chọn một gợi ý ở “Mình chưa biết hỏi gì”.</p> : null}
        <p><LockKey aria-hidden="true" /> Không cần đăng nhập · chỉ gửi khi bạn bấm Xòe bài · mã hóa tối đa 30 ngày · không vào analytics.</p>
      </footer>
      <button
        aria-expanded={showStarters}
        className="tarot-starter-toggle"
        onClick={() => setShowStarters((value) => !value)}
        type="button"
      >
        Mình chưa biết hỏi gì
      </button>
      {showStarters ? <div className="tarot-suggestions tarot-suggestions--compact">
        {QUESTIONS[context].map((suggestion) => <button aria-pressed={question === suggestion} key={suggestion} onClick={() => { setQuestion(suggestion); setSpreadOverride(null); setReframe(null); setShowStarters(false); }} type="button">{suggestion}</button>)}
      </div> : null}
    </TarotFrame>
  );
}

function TarotFrame({ children, step, scene = false }: { children: React.ReactNode; step: string; scene?: boolean }) {
  const navigate = useNavigate();
  return <main className={scene ? "tarot-page tarot-page--scene uv-night-scene" : "tarot-page"}>{scene ? <NightSky orbits planet /> : null}<header className="tarot-header"><button aria-label="Quay lại" onClick={() => void navigate(-1)} type="button"><ArrowLeft aria-hidden="true" /></button><div className="tarot-header__title"><strong>Tarot</strong><span><LockKey aria-hidden="true" /> Riêng tư</span></div><BrandMark /><span className="sr-only">{step}</span></header>{children}</main>;
}

function TarotFan({ fanSize, selected, pendingIndex, busy, onPick }: {
  fanSize: number;
  selected: Set<number>;
  pendingIndex: number | null;
  busy: boolean;
  onPick: (index: number) => void;
}) {
  const fan = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // Open on the middle of the arc so both directions feel reachable.
    const element = fan.current;
    if (element && element.scrollWidth > element.clientWidth) {
      element.scrollLeft = (element.scrollWidth - element.clientWidth) / 2;
    }
  }, []);
  const middle = (fanSize - 1) / 2;
  return <div aria-label={`${fanSize} lá bài úp`} className="tarot-fan" ref={fan} role="group">
    {Array.from({ length: fanSize }, (_, index) => {
      const offset = index - middle;
      const picked = selected.has(index);
      // Saturating arc: the opened middle fans visibly, the long tails settle at a steady tilt.
      const bend = Math.tanh(offset / 12);
      const style = {
        "--fan-angle": `${(bend * 24).toFixed(2)}deg`,
        "--fan-drop": `${(bend * bend * 1.6).toFixed(3)}rem`,
        "--fan-delay": `${Math.round(Math.min(Math.abs(offset), 22) * 18)}ms`,
      } as CSSProperties;
      const className = [
        "tarot-fan-card",
        picked ? "tarot-fan-card--picked" : "",
        pendingIndex === index ? "is-pending" : "",
      ].filter(Boolean).join(" ");
      return <button
        aria-label={`Lá úp ${index + 1} trên ${fanSize}`}
        aria-pressed={picked}
        className={className}
        data-fan-index={index}
        disabled={busy || picked}
        key={index}
        onClick={() => onPick(index)}
        style={style}
        type="button"
      >
        <TarotCardBack />
      </button>;
    })}
  </div>;
}

function TarotResult({ session, confirmDelete, deleting, onDelete, onKeep }: { session: TarotSession; confirmDelete: boolean; deleting: boolean; onDelete: () => void; onKeep: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  const motion = useTarotMotion();
  useEffect(() => { heading.current?.focus(); }, []);
  const reading = session.reading;
  if (!reading) return null;
  const depthLabel = `Trải ${session.required_cards} lá`;
  const openChapter = (key: string) => {
    const chapter = document.getElementById(`tarot-chapter-${key}`);
    if (!(chapter instanceof HTMLDetailsElement)) return;
    chapter.open = true;
    chapter.scrollIntoView?.({ behavior: motion ? "smooth" : "auto", block: "start" });
    chapter.querySelector("summary")?.focus({ preventScroll: true });
  };
  return (
    <TarotFrame step="Bài của bạn">
      <section className="tarot-result-hero tarot-report uv-night" aria-labelledby="tarot-report-title">
        <NightSky stars={5} />
        <div className="tarot-question-ticket">
          <span>Câu bạn đã hỏi</span>
          <strong>{reading.question}</strong>
        </div>
        <p className="tarot-kicker">{depthLabel}</p>
        <h1 id="tarot-report-title" ref={heading} tabIndex={-1}>Tóm tắt bài của bạn</h1>
        <ul
          aria-label="Các lá bạn đã rút"
          className="tarot-spread-row"
          data-count={reading.positions.length}
          data-tarot-motion={motion ? "on" : "off"}
        >
          {reading.positions.map((position, index) => (
            <li key={position.key}>
              <button
                aria-label={`0${index + 1}. ${position.card.title_vi}, ${position.label}. Mở phần đọc lá này`}
                className="tarot-spread-row__card"
                onClick={() => openChapter(position.key)}
                type="button"
              >
                <TarotCardArt card={position.card} compact={reading.positions.length > 3} decorative />
                <span aria-hidden="true">0{index + 1}</span>
              </button>
            </li>
          ))}
        </ul>
        <h2>{reading.headline}</h2>
        <p>{reading.summary}</p>
      </section>

      <section className="tarot-reading" aria-labelledby="tarot-chapters-title">
        <h2 id="tarot-chapters-title" className="tarot-chapters-title">Mở từng lá để đọc thêm</h2>
        {reading.positions.map((position, index) => (
          <details className="tarot-reading-card tarot-chapter" id={`tarot-chapter-${position.key}`} key={position.key}>
            <summary className="tarot-chapter-heading">
              <span aria-hidden="true" className="tarot-chapter-thumb">
                <TarotCardArt card={position.card} compact decorative />
                <span className="tarot-chapter-number">0{index + 1}</span>
              </span>
              <span className="tarot-chapter-labels">
                <strong>{position.card.title_vi}</strong>
                <span>{position.label}</span>
              </span>
              <span className="tarot-chapter-chevron" aria-hidden="true">⌄</span>
            </summary>
            <div className="tarot-reading-copy">
              <p>{position.meaning_here}</p>
              <div className="tarot-scene">
                <Eye aria-hidden="true" />
                <div><strong>Ví dụ để đối chiếu</strong><p>{position.everyday_scene}</p></div>
              </div>
              <blockquote>{position.reflection_question}</blockquote>
              {position.small_action ? (
                <div className="tarot-action">
                  <Sparkle aria-hidden="true" />
                  <div><strong>Một việc bạn có thể thử</strong><p>{position.small_action}</p></div>
                </div>
              ) : null}
            </div>
          </details>
        ))}
      </section>

      <section className="tarot-closing">
        <p>{reading.closing_prompt}</p>
        <ReadingDisclaimer compact>{reading.disclaimer}</ReadingDisclaimer>
        <details className="tarot-tech">
          <summary>Chi tiết kỹ thuật</summary>
          <span>Tên lá gốc: {reading.positions.map((position) => position.card.title_en).join(", ")}</span>
          <span>Engine {reading.provenance.knowledge_version} · bộ {reading.provenance.deck_version}</span>
        </details>
      </section>
      <footer className="tarot-result-actions">
        {confirmDelete ? (
          <div className="tarot-delete-confirm" role="alert">
            <strong>Xóa là mất hẳn bài này.</strong>
            <p>Không có nút hoàn tác và link cũ sẽ không mở lại.</p>
            <div>
              <button disabled={deleting} onClick={onDelete} type="button">
                <Trash aria-hidden="true" />{deleting ? "Đang xóa…" : "Xóa hẳn"}
              </button>
              <button onClick={onKeep} type="button">Giữ lại</button>
            </div>
          </div>
        ) : (
          <>
            <Link className="tarot-primary" to="/tarot"><Sparkle aria-hidden="true" />Hỏi một chuyện khác</Link>
            <button className="tarot-delete" onClick={onDelete} type="button"><Trash aria-hidden="true" /> Xóa bài này</button>
          </>
        )}
      </footer>
    </TarotFrame>
  );
}
