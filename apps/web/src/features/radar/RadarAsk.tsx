import { ChatCircleText, Copy } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { getRadarAskAnswer, getRadarAskQuestions } from "../../shared/api/client";

/**
 * "Hỏi về hai bạn" (Hợp gu direction B): pick a pre-written question, read an answer built from
 * this pair's stored reading. No typing, nothing saved. Hidden until the server offers questions,
 * which it does only once their lines are approved.
 */
export function RadarAsk({ requestId }: { requestId: string }) {
  const [chosen, setChosen] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const questions = useQuery({
    queryKey: ["radar-ask", requestId],
    queryFn: ({ signal }) => getRadarAskQuestions(requestId, signal),
    retry: false,
    gcTime: 0,
  });
  const answer = useQuery({
    queryKey: ["radar-ask", requestId, chosen],
    queryFn: ({ signal }) => getRadarAskAnswer(requestId, chosen ?? "", signal),
    enabled: chosen !== null,
    retry: false,
    gcTime: 0,
  });
  const list = questions.data?.questions ?? [];
  if (!list.length) return null;
  const choose = (id: string | null) => {
    setCopied(false);
    setChosen(id);
  };
  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };
  return <section aria-labelledby="radar-ask-heading" className="radar-ask">
    <p className="eyebrow"><ChatCircleText /> Hỏi về hai bạn</p>
    <h2 id="radar-ask-heading">Bạn muốn hỏi gì về hai bạn?</h2>
    {chosen === null ? <ul className="radar-ask__questions">{list.map((item) => <li key={item.id}><button onClick={() => choose(item.id)} type="button">{item.text}</button></li>)}</ul> : null}
    {chosen !== null && answer.isPending ? <p role="status">Đang xem…</p> : null}
    {chosen !== null && answer.isError ? <p className="matching-message" role="alert">Chưa mở được câu trả lời. Thử lại sau nhé.</p> : null}
    {chosen !== null && answer.data ? <article className="radar-ask__answer" aria-live="polite">
      <p className="radar-ask__question">{answer.data.question}</p>
      <p className="radar-ask__say">{answer.data.say}</p>
      {answer.data.why ? <p>Vì sao: {answer.data.why}</p> : null}
      {answer.data.try_today ? <p>{answer.data.try_today}</p> : null}
      <blockquote>“{answer.data.can_send}”</blockquote>
      <button className="matching-secondary" onClick={() => void copy(answer.data.can_send)} type="button"><Copy /> {copied ? "Đã chép câu" : "Chép câu này"}</button>
      {answer.data.based_on ? <details><summary>Dựa vào</summary><p>{answer.data.based_on.label} · {answer.data.based_on.level_label}{answer.data.based_on.technical_note ? `. ${answer.data.based_on.technical_note}` : ""}</p></details> : null}
    </article> : null}
    {chosen !== null ? <button className="matching-secondary" onClick={() => choose(null)} type="button">Hỏi câu khác</button> : null}
  </section>;
}
