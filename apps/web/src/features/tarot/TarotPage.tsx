import {
  ArrowLeft,
  ArrowRight,
  Briefcase,
  CardsThree,
  CheckCircle,
  Eye,
  HeartStraight,
  LockKey,
  Sparkle,
  Trash,
  UserCircle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import {
  ApiProblem,
  createTarotGuest,
  deleteTarotSession,
  getSession,
  getTarotSession,
  selectTarotCard,
  startTarotSession,
  type TarotContext,
  type TarotSession,
  type TarotSpread,
} from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { ReadingDisclaimer } from "../../shared/ui/ReadingDisclaimer";
import "./tarot.css";
import "./tarot-polish.css";

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

function recommendSpread(question: string): {
  spread: TarotSpread;
  title: string;
  reason: string;
} {
  const normalized = question.trim().toLocaleLowerCase("vi");
  const needsFive = /(?:giữa|hay là|nên chọn|lựa chọn|ở lại|rời đi|lặp lại|lần nào cũng|cứ mỗi|nói chuyện khó|ranh giới)/i.test(normalized);
  if (needsFive) {
    return {
      spread: "five_card",
      title: "5 lá · Gỡ chuyện nhiều lớp",
      reason: "Tách dữ kiện, nhu cầu, điểm cấn, phần bạn chọn được và một bước để thử.",
    };
  }
  if (normalized.length >= 8 && normalized.length <= 22) {
    return {
      spread: "one_card",
      title: "1 lá · Chạm đúng điểm",
      reason: "Một góc đủ rõ để bạn đối chiếu ngay với chuyện đang xảy ra.",
    };
  }
  return {
    spread: "three_card",
    title: "3 lá · Nhìn rõ trước khi hành động",
    reason: "Đủ để thấy điều đã rõ, điểm dễ bỏ sót và một bước có thể thử.",
  };
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
  try {
    await getSession();
  } catch (error) {
    if (!(error instanceof ApiProblem) || error.status !== 401) throw error;
    const key = sessionStorage.getItem("la-lanh-tarot-guest-key") ?? crypto.randomUUID();
    sessionStorage.setItem("la-lanh-tarot-guest-key", key);
    await createTarotGuest(key);
    sessionStorage.removeItem("la-lanh-tarot-guest-key");
  }
}

function contextFromQuery(promptId: string | null, rawContext: string | null): TarotContext {
  if (promptId && PROMPT_CONTEXT[promptId]) return PROMPT_CONTEXT[promptId];
  return CONTEXTS.some((item) => item.key === rawContext) ? rawContext as TarotContext : "general";
}

export function TarotPage() {
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
  const [spreadOverride, setSpreadOverride] = useState<TarotSpread | null>(null);
  const spread = spreadOverride ?? recommendation.spread;
  const [showStarters, setShowStarters] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [reframe, setReframe] = useState<{ explanation: string; question: string } | null>(null);

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
      const signature = JSON.stringify({ context, question: question.trim(), spread, origin, promptId });
      return startTarotSession({
        context,
        question: question.trim(),
        spread,
        origin,
        prompt_id: promptId,
        idempotency_key: startKey(signature),
      });
    },
    onSuccess: (created) => {
      sessionStorage.removeItem("la-lanh-tarot-start");
      setReframe(null);
      queryClient.setQueryData(["tarot-session", created.id], created);
      void navigate(`/tarot/${created.id}`, { replace: true });
    },
    onError: (error) => {
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
    onSuccess: (updated) => {
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
    return <TarotFrame step="Đang mở lại"><section className="tarot-loading" aria-label="Đang mở lại phiên Tarot"><span /></section></TarotFrame>;
  }
  if (sessionId && sessionQuery.isError) {
    return <TarotFrame step="Phiên riêng tư"><section className="tarot-state"><h1>Không mở lại được lần bốc này.</h1><p>Phiên có thể đã hết hạn, đã được xóa hoặc thuộc một trình duyệt khác.</p><Link className="tarot-primary" to="/tarot">Bắt đầu lần mới</Link></section></TarotFrame>;
  }
  if (session?.state === "complete" && session.reading) {
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
    return (
      <TarotFrame step={`${session.selected_cards.length}/${session.required_cards} lá`}>
        <section className="tarot-draw-intro">
          <p className="tarot-kicker">Bộ bài đã được khóa cho lần này</p>
          <h1>Chạm lá khiến bạn dừng mắt.</h1>
          <p>Không có lá “đúng” để săn. Thứ tự đã được giữ nguyên trên máy chủ trước khi xòe.</p>
        </section>
        <div className="tarot-question-ticket"><span>Câu bạn mang vào</span><strong>{session.question}</strong></div>
        <div className="tarot-slots" aria-label="Các vị trí đã chọn">
          {Array.from({ length: session.required_cards }, (_, index) => {
            const selected = session.selected_cards[index];
            return <div className={selected ? "tarot-slot tarot-slot--filled" : "tarot-slot"} key={index}>
              <span>{selected?.position_label ?? `Lá ${index + 1}`}</span>
              <strong>{selected?.card.title_vi ?? "Chưa chọn"}</strong>
            </div>;
          })}
        </div>
        <section className="tarot-fan-wrap" aria-label="Bộ bài đang xòe">
          <p>Kéo ngang rồi chọn một lá</p>
          <div className="tarot-fan" role="group" aria-label="78 lá bài úp">
            {Array.from({ length: session.fan_size }, (_, index) => (
              <button
                aria-label={`Lá úp ${index + 1} trên ${session.fan_size}`}
                aria-pressed={selectedIndexes.has(index)}
                className={selectedIndexes.has(index) ? "tarot-card-back tarot-card-back--picked" : "tarot-card-back"}
                disabled={select.isPending || selectedIndexes.has(index)}
                key={index}
                onClick={() => select.mutate({ active: session, index })}
                style={{ transform: `translateY(${Math.abs(38.5 - index) * 0.45}px) rotate(${(index - 38.5) * 0.18}deg)` }}
                type="button"
              >
                <span>✦</span><small>{index + 1}</small>
              </button>
            ))}
          </div>
        </section>
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

        <div aria-label="Chủ đề câu hỏi" className="tarot-context-chips">
          {CONTEXTS.map((item) => (
            <button
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
            <span><Sparkle aria-hidden="true" weight="fill" /> Lá gợi ý</span>
            <h2 id="tarot-spread-title">{recommendation.title}</h2>
            <p>{recommendation.reason}</p>
          </div>
          <CardsThree aria-hidden="true" className="tarot-recommendation__icon" weight="duotone" />
          <div className="tarot-depth" role="group" aria-label="Đổi độ sâu">
            <span>Đổi độ sâu</span>
            {SPREAD_OPTIONS.map((option) => (
              <button
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
        <button className="tarot-primary" disabled={start.isPending || question.trim().length < 8} onClick={() => start.mutate()} type="button"><Sparkle aria-hidden="true" />{start.isPending ? "Đang khóa bộ bài…" : `Xòe ${spread === "one_card" ? "1" : spread === "three_card" ? "3" : "5"} lá`}<ArrowRight aria-hidden="true" /></button>
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

function TarotFrame({ children, step }: { children: React.ReactNode; step: string }) {
  const navigate = useNavigate();
  return <main className="tarot-page"><header className="tarot-header"><button aria-label="Quay lại" onClick={() => void navigate(-1)} type="button"><ArrowLeft aria-hidden="true" /></button><div className="tarot-header__title"><strong>Tarot</strong><span><LockKey aria-hidden="true" /> Riêng tư</span></div><BrandMark /><span className="sr-only">{step}</span></header>{children}</main>;
}

function TarotResult({ session, confirmDelete, deleting, onDelete, onKeep }: { session: TarotSession; confirmDelete: boolean; deleting: boolean; onDelete: () => void; onKeep: () => void }) {
  const reading = session.reading;
  if (!reading) return null;
  const depthLabel = session.required_cards === 1 ? "Một lá · một điểm chạm" : session.required_cards === 3 ? "Ba lá · ba lớp nhìn" : "Năm lá · một bản đồ rõ hơn";
  return <TarotFrame step="Bài của bạn"><section className="tarot-result-hero"><p className="tarot-kicker">{depthLabel}</p><h1>{reading.headline}</h1><p>{reading.summary}</p><div className="tarot-question-ticket"><span>Câu bạn đã hỏi</span><strong>{reading.question}</strong></div></section><section className="tarot-reading">{reading.positions.map((position, index) => <article className="tarot-reading-card" key={position.key}><div className="tarot-face" aria-label={`Lá ${position.card.title_vi}`}><span>0{index + 1}</span><strong>{position.card.title_vi}</strong><small>{position.card.title_en}</small><i>✦</i></div><div className="tarot-reading-copy"><p className="tarot-position">{position.label}</p><h2>{position.card.core}</h2><p>{position.meaning_here}</p><div className="tarot-scene"><Eye aria-hidden="true" /><div><strong>Ngoài đời có thể trông như…</strong><p>{position.everyday_scene}</p></div></div><blockquote>{position.reflection_question}</blockquote><div className="tarot-action"><Sparkle aria-hidden="true" /><div><strong>Đem ra đời thật</strong><p>{position.small_action}</p></div></div></div></article>)}</section><section className="tarot-closing"><p>{reading.closing_prompt}</p><ReadingDisclaimer compact>{reading.disclaimer}</ReadingDisclaimer><span>Engine {reading.provenance.knowledge_version} · bộ {reading.provenance.deck_version}</span></section><footer className="tarot-result-actions">{confirmDelete ? <div className="tarot-delete-confirm" role="alert"><strong>Xóa là mất hẳn bài này.</strong><p>Không có nút hoàn tác và link cũ sẽ không mở lại.</p><div><button disabled={deleting} onClick={onDelete} type="button"><Trash aria-hidden="true" />{deleting ? "Đang xóa…" : "Xóa hẳn"}</button><button onClick={onKeep} type="button">Giữ lại</button></div></div> : <><Link className="tarot-primary" to="/tarot"><Sparkle aria-hidden="true" />Hỏi một chuyện khác</Link><button className="tarot-delete" onClick={onDelete} type="button"><Trash aria-hidden="true" /> Xóa bài này</button></>}</footer></TarotFrame>;
}
