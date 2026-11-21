import { ArrowLeft, CalendarBlank, CheckCircle, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import {
  ApiProblem,
  askMonth,
  deleteSavedMonthAnswer,
  getMonthStatus,
  getMonthWindow,
  listSavedMonthAnswers,
  saveMonthAnswer,
  type MonthAnswer,
  type MonthPreset,
  type MonthPresetId,
  type MonthTopic,
  type MonthWindow,
} from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { MONTH_TOPICS, monthCopy } from "./monthCopy";
import "./month.css";

import { MONTH_STATUS_KEY } from "./monthQueries";
const SAVED_KEY = ["month-saved"] as const;

/** dd.mm, the app's usual short date. */
function shortDate(iso: string): string {
  const [, month, day] = iso.split("-");
  return `${day}.${month}`;
}

type Ask = { topic: MonthTopic; preset?: MonthPresetId | null };

/**
 * "Hỏi về tháng này" (US-25, AK2). No counter, no nudge to ask again, nothing saved unless the
 * person taps "Lưu". People pick a topic or a preset question; there is no typed box (owner chose
 * AS1 on 21.11.2026), so nothing they write is collected.
 */
export function MonthAskPage() {
  const status = useQuery({ queryKey: MONTH_STATUS_KEY, queryFn: ({ signal }) => getMonthStatus(signal), retry: false });
  const [answer, setAnswer] = useState<MonthAnswer | null>(null);

  const ask = useMutation({
    mutationFn: (input: Ask) => askMonth(input),
    onSuccess: (result) => setAnswer(result.answer),
  });

  if (status.isPending) return <main className="app-page month-page" aria-busy="true" />;
  if (!status.data?.available) return <Navigate replace to="/home" />;
  const presets = status.data.presets ?? [];

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

      {answer ? (
        <MonthAnswerCard
          answer={answer}
          asking={ask.isPending}
          onAgain={() => setAnswer(null)}
          onAsk={(input) => ask.mutate(input)}
          presets={presets.filter((item) => item.topic === answer.topic && item.id !== answer.preset)}
        />
      ) : (
        <section className="month-ask" aria-labelledby="month-topic-heading">
          <h2 id="month-topic-heading">{monthCopy("month.ui.topic_heading")}</h2>
          <div className="month-topics" role="group" aria-labelledby="month-topic-heading">
            {MONTH_TOPICS.map((item) => (
              <button disabled={ask.isPending} key={item.key} onClick={() => ask.mutate({ topic: item.key })} type="button">
                {item.label}
              </button>
            ))}
          </div>
          {presets.length > 0 ? (
            <section className="month-presets" aria-labelledby="month-preset-heading">
              <h2 id="month-preset-heading">{monthCopy("month.ui.preset_heading")}</h2>
              {MONTH_TOPICS.map((topic) => {
                const group = presets.filter((item) => item.topic === topic.key);
                if (group.length === 0) return null;
                return (
                  <div className="month-preset-group" key={topic.key}>
                    <p className="eyebrow">{topic.label}</p>
                    <PresetList asking={ask.isPending} items={group} onAsk={(input) => ask.mutate(input)} />
                  </div>
                );
              })}
            </section>
          ) : null}
        </section>
      )}
      {ask.isError ? <p className="month-error" role="alert">{monthCopy("month.ui.error")}</p> : null}

      <SavedMonthAnswers />
    </main>
  );
}

function PresetList({ items, asking, onAsk }: { items: MonthPreset[]; asking: boolean; onAsk: (input: Ask) => void }) {
  return (
    <ul className="month-preset-list">
      {items.map((item) => (
        <li key={item.id}>
          <button disabled={asking} onClick={() => onAsk({ topic: item.topic, preset: item.id })} type="button">
            {item.text}
          </button>
        </li>
      ))}
    </ul>
  );
}

function MonthAnswerCard({
  answer,
  asking,
  onAgain,
  onAsk,
  presets,
}: {
  answer: MonthAnswer;
  asking: boolean;
  onAgain: () => void;
  onAsk: (input: Ask) => void;
  presets: MonthPreset[];
}) {
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
      {answer.question ? <h2 className="month-question">{answer.question}</h2> : null}
      {answer.tip ? (
        <section>
          <h2>{monthCopy("month.ui.part_tip")}</h2>
          <p>{answer.tip}</p>
        </section>
      ) : null}
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

      {presets.length > 0 ? (
        <section className="month-presets" aria-labelledby="month-more-presets">
          <h2 id="month-more-presets">{monthCopy("month.ui.more_presets")}</h2>
          <PresetList asking={asking} items={presets} onAsk={onAsk} />
        </section>
      ) : null}
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
            {item.answer.question ? <p className="month-question">{item.answer.question}</p> : null}
            {item.answer.tip ? <p>{item.answer.tip}</p> : null}
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
