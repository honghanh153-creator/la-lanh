import { ArrowLeft, CalendarBlank, CheckCircle, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import {
  ApiProblem,
  askMonth,
  crisisNoticeFrom,
  deleteSavedMonthAnswer,
  getMonthStatus,
  getMonthWindow,
  listSavedMonthAnswers,
  saveMonthAnswer,
  withdrawMonthConsent,
  type MonthAnswer,
  type MonthTopic,
  type MonthWindow,
} from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { CrisisNotice } from "../../shared/ui/CrisisNotice";
import { MONTH_TOPICS, monthCopy } from "./monthCopy";
import "./month.css";

import { MONTH_STATUS_KEY } from "./monthQueries";
const SAVED_KEY = ["month-saved"] as const;

/** dd.mm, the app's usual short date. */
function shortDate(iso: string): string {
  const [, month, day] = iso.split("-");
  return `${day}.${month}`;
}

/**
 * "Hỏi về tháng này" (US-25, AK2). No counter, no nudge to ask again, nothing saved unless the
 * person taps "Lưu". The typed question lives in this component's state only and is cleared as
 * soon as it is sent.
 */
export function MonthAskPage() {
  const status = useQuery({ queryKey: MONTH_STATUS_KEY, queryFn: ({ signal }) => getMonthStatus(signal), retry: false });
  const [typed, setTyped] = useState("");
  const [consented, setConsented] = useState(false);
  const [answer, setAnswer] = useState<MonthAnswer | null>(null);
  const [needTopic, setNeedTopic] = useState<string | null>(null);
  const [crisis, setCrisis] = useState<string | null>(null);

  const withdraw = useMutation({
    mutationFn: () => withdrawMonthConsent(),
    onSuccess: () => setConsented(false),
  });
  const ask = useMutation({
    mutationFn: (input: Parameters<typeof askMonth>[0]) => askMonth(input),
    onMutate: () => {
      setCrisis(null);
      setNeedTopic(null);
    },
    onSuccess: (result) => {
      setTyped("");
      if (result.status === "need_topic") {
        setAnswer(null);
        setNeedTopic(result.need_topic ?? null);
        return;
      }
      setAnswer(result.answer ?? null);
    },
    onError: (error) => {
      const notice = crisisNoticeFrom(error);
      if (notice) {
        setTyped("");
        setAnswer(null);
        setCrisis(notice);
      }
    },
  });

  if (status.isPending) return <main className="app-page month-page" aria-busy="true" />;
  if (!status.data?.available) return <Navigate replace to="/home" />;
  const consent = status.data.consent;
  const typedOn = status.data.typed_questions && consent !== null && consent !== undefined;

  function pick(topic: MonthTopic) {
    ask.mutate({ topic });
  }

  function submitTyped() {
    const question = typed.trim();
    if (!question || !consent || !consented) return;
    ask.mutate({ question, consent_version: consent.version });
  }

  return (
    <main className="app-page month-page">
      <header className="cosmic-header">
        <Link aria-label="Về hôm nay" className="icon-button" to="/home"><ArrowLeft aria-hidden="true" /></Link>
        <BrandMark />
        <span aria-hidden="true" />
      </header>

      <section className="month-intro" aria-labelledby="month-title">
        <h1 id="month-title">{monthCopy("month.ui.entry")}</h1>
        <p>{monthCopy("month.ui.intro")}</p>
      </section>

      {crisis ? <CrisisNotice className="month-crisis" text={crisis} /> : null}

      {answer ? (
        <MonthAnswerCard answer={answer} onAgain={() => setAnswer(null)} />
      ) : (
        <section className="month-ask" aria-labelledby="month-topic-heading">
          <h2 id="month-topic-heading">{monthCopy("month.ui.topic_heading")}</h2>
          {needTopic ? <p className="month-need-topic">{needTopic}</p> : null}
          <div className="month-topics" role="group" aria-labelledby="month-topic-heading">
            {MONTH_TOPICS.map((item) => (
              <button disabled={ask.isPending} key={item.key} onClick={() => pick(item.key)} type="button">
                {item.label}
              </button>
            ))}
          </div>
          {typedOn ? (
            <form
              className="month-typed"
              onSubmit={(event) => {
                event.preventDefault();
                submitTyped();
              }}
            >
              <label>
                <span>{monthCopy("month.ui.type_label")}</span>
                <textarea
                  autoComplete="off"
                  maxLength={280}
                  onChange={(event) => setTyped(event.target.value)}
                  rows={3}
                  value={typed}
                />
              </label>
              <label className="month-consent">
                <input checked={consented} onChange={(event) => setConsented(event.target.checked)} type="checkbox" />
                <span>{consent.text}</span>
              </label>
              <button className="electric-button" disabled={ask.isPending || !consented || typed.trim().length < 8} type="submit">
                {monthCopy("month.ui.type_submit")}
              </button>
              <button className="month-withdraw" disabled={withdraw.isPending} onClick={() => withdraw.mutate()} type="button">
                {monthCopy("month.ui.withdraw_consent")}
              </button>
            </form>
          ) : null}
          {ask.isError && !crisis ? <p className="month-error" role="alert">{monthCopy("month.ui.error")}</p> : null}
        </section>
      )}

      <SavedMonthAnswers />
    </main>
  );
}

function MonthAnswerCard({ answer, onAgain }: { answer: MonthAnswer; onAgain: () => void }) {
  const queryClient = useQueryClient();
  const [easier, setEasier] = useState<MonthWindow | null>(null);
  const [saved, setSaved] = useState(false);
  const loadWindow = useMutation({
    mutationFn: () => getMonthWindow(answer.topic),
    onSuccess: setEasier,
  });
  const save = useMutation({
    mutationFn: () => saveMonthAnswer(answer.topic, answer.answer_key),
    onSuccess: () => {
      setSaved(true);
      void queryClient.invalidateQueries({ queryKey: SAVED_KEY });
    },
  });

  return (
    <article className="month-answer" aria-labelledby="month-answer-topic">
      <p className="eyebrow" id="month-answer-topic">{answer.topic_label}</p>
      {answer.reframe ? <p className="month-reframe">{answer.reframe}</p> : null}
      <section>
        <h2>{monthCopy("month.ui.part_theme")}</h2>
        <p>{answer.theme}</p>
      </section>
      <section>
        <h2>{monthCopy("month.ui.part_act")}</h2>
        <p>{answer.act}</p>
      </section>
      <section>
        <h2>{monthCopy("month.ui.part_say")}</h2>
        <blockquote>{answer.say}</blockquote>
      </section>
      <details className="month-basis">
        <summary>{answer.basis.line}</summary>
        <p>{answer.basis.detail}</p>
      </details>
      <p className="month-disclaimer">{answer.disclaimer}</p>

      {/* AK2: collapsed by default, fetched only on tap, never shown on Home. */}
      {easier === null ? (
        <button className="month-window-button" disabled={loadWindow.isPending} onClick={() => loadWindow.mutate()} type="button">
          <CalendarBlank aria-hidden="true" /> {monthCopy("month.ui.window_button")}
        </button>
      ) : (
        <section className="month-window" aria-label={monthCopy("month.ui.window_label")}>
          {easier.found && easier.start && easier.end ? (
            <>
              <p><strong>{monthCopy("month.ui.window_label")}: {easier.start === easier.end ? shortDate(easier.start) : `${shortDate(easier.start)} – ${shortDate(easier.end)}`}</strong></p>
              <p>{easier.line}</p>
              <small>{easier.basis}</small>
            </>
          ) : (
            <p>{monthCopy("month.ui.window_none")}</p>
          )}
        </section>
      )}

      <div className="month-actions">
        <button aria-pressed={saved} className="electric-button" disabled={saved || save.isPending} onClick={() => save.mutate()} type="button">
          {saved ? <><CheckCircle aria-hidden="true" weight="fill" /> {monthCopy("month.ui.saved")}</> : monthCopy("month.ui.save")}
        </button>
        <button className="month-again" onClick={onAgain} type="button">{monthCopy("month.ui.change_topic")}</button>
      </div>
      {save.isError && !(save.error instanceof ApiProblem && save.error.code === "MONTH_ANSWER_CHANGED")
        ? <p className="month-error" role="alert">{monthCopy("month.ui.error")}</p>
        : null}
    </article>
  );
}

/** Saved answers: their own section, loaded only when opened, each one deletable. */
function SavedMonthAnswers() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const saved = useQuery({
    queryKey: SAVED_KEY,
    queryFn: ({ signal }) => listSavedMonthAnswers(signal),
    enabled: open,
    retry: false,
  });
  const remove = useMutation({
    mutationFn: (id: string) => deleteSavedMonthAnswer(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: SAVED_KEY }),
  });

  return (
    <details className="month-saved" onToggle={(event) => setOpen((event.target as HTMLDetailsElement).open)}>
      <summary>{monthCopy("month.ui.saved_heading")}</summary>
      {saved.data && saved.data.length === 0 ? <p>{monthCopy("month.ui.saved_empty")}</p> : null}
      <ul>
        {saved.data?.map((item) => (
          <li key={item.id}>
            <p className="eyebrow">{item.answer.topic_label}</p>
            <p>{item.answer.theme}</p>
            <p>{item.answer.act}</p>
            <blockquote>{item.answer.say}</blockquote>
            <button disabled={remove.isPending} onClick={() => remove.mutate(item.id)} type="button">
              <Trash aria-hidden="true" /> {monthCopy("month.ui.delete")}
            </button>
          </li>
        ))}
      </ul>
    </details>
  );
}
