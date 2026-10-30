import { ArrowRight, LockKey, UserFocus } from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useId, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  ApiProblem,
  createHumanTarotRequest,
  currentSessionEpoch,
  type HumanTarotAvailability,
  type TarotContext,
  type TarotSpread,
} from "../../shared/api/client";
import { formatVietnamTime, type TarotMode } from "./humanTarot";
import { ensureTarotGuest } from "./tarotGuest";
import "./human-tarot.css";

export function TarotModeSwitch({ mode, onChange }: { mode: TarotMode; onChange: (mode: TarotMode) => void }) {
  return <div aria-label="Cách bốc bài" className="human-tarot-mode" role="group">
    <button aria-pressed={mode === "self"} className={mode === "self" ? "is-active" : ""} onClick={() => onChange("self")} type="button">
      <strong>Tự bốc ngay</strong><small>Xem bài liền</small>
    </button>
    <button aria-pressed={mode === "human"} className={mode === "human" ? "is-active" : ""} onClick={() => onChange("human")} type="button">
      <strong>Nhờ người bốc</strong><small>Trả bài lúc 10:00</small>
    </button>
  </div>;
}

/**
 * Idempotency key for one unchanged draft in this guest session, in memory only: a retry after a
 * lost response reuses it, so the server answers with the same receipt and takes no second slot.
 */
function useDraftKey() {
  const latest = useRef<{ draft: string; key: string } | null>(null);
  return useCallback((input: object) => {
    const draft = JSON.stringify([currentSessionEpoch(), input]);
    if (latest.current?.draft !== draft) latest.current = { draft, key: crypto.randomUUID() };
    return latest.current.key;
  }, []);
}

export function HumanTarotSubmit({ availability, context, question, spread, questionTooShort }: {
  availability: HumanTarotAvailability;
  context: TarotContext;
  question: string;
  spread: TarotSpread;
  questionTooShort: boolean;
}) {
  const navigate = useNavigate();
  const consentId = useId();
  const [consented, setConsented] = useState(false);
  const [reframe, setReframe] = useState<string | null>(null);
  const keyFor = useDraftKey();
  const create = useMutation({
    mutationFn: async () => {
      await ensureTarotGuest();
      const body = { context, question: question.trim(), spread, consent_version: availability.consent_version };
      return createHumanTarotRequest({ ...body, idempotency_key: keyFor(body) });
    },
    onSuccess: (created) => {
      void navigate(`/tarot/nguoi-boc/${created.id}`, { replace: true });
    },
    onError: (error) => {
      if (error instanceof ApiProblem && error.code === "SESSION_CHANGED") {
        void navigate("/welcome?restart=1", { replace: true, state: { sessionChanged: true } });
        return;
      }
      if (error instanceof ApiProblem && error.code === "TAROT_QUESTION_REFRAME_REQUIRED") {
        const explanation = error.details.explanation;
        setReframe(typeof explanation === "string" ? explanation : null);
      }
    },
  });
  const closesAt = formatVietnamTime(availability.closes_at);
  const releaseAt = formatVietnamTime(availability.release_at);
  const problem = create.error instanceof ApiProblem ? create.error.code : null;

  if (availability.reason === "already_requested" && availability.current_request_id) {
    return <section className="human-tarot-panel" aria-label="Nhờ người bốc">
      <p>Hôm nay bạn đã gửi một câu cho người bốc.</p>
      <Link className="tarot-primary" to={`/tarot/nguoi-boc/${availability.current_request_id}`}>Xem yêu cầu hôm nay<ArrowRight aria-hidden="true" /></Link>
    </section>;
  }
  if (availability.reason === "full" || problem === "HUMAN_TAROT_FULL") {
    return <section className="human-tarot-panel" aria-label="Nhờ người bốc"><p role="status">Hôm nay đã đủ {availability.daily_limit} lượt. Bạn có thể quay lại ngày mai hoặc tự bốc ngay.</p></section>;
  }
  if (availability.reason === "closed" || problem === "HUMAN_TAROT_CLOSED") {
    return <section className="human-tarot-panel" aria-label="Nhờ người bốc"><p role="status">Hôm nay đã ngừng nhận lượt. Ngày mai bạn quay lại nhé.</p></section>;
  }
  return <section className="human-tarot-panel" aria-label="Nhờ người bốc">
    <p className="human-tarot-panel__lead"><UserFocus aria-hidden="true" /> Tối đa {availability.daily_limit} lượt/ngày · Trả bài lúc {releaseAt} hôm nay</p>
    <p className="human-tarot-panel__meta">Giờ Việt Nam · nhận tới {closesAt} · còn {availability.remaining} lượt</p>
    <p className="human-tarot-panel__note">Một người thật của Lá Lành sẽ bốc {spread === "one_card" ? "1" : spread === "three_card" ? "3" : "5"} lá và viết bài riêng cho câu này. Không có AI viết thay.</p>
    <label className="human-tarot-consent" htmlFor={consentId}>
      <input checked={consented} id={consentId} onChange={(event) => setConsented(event.target.checked)} type="checkbox" />
      <span>Mình đồng ý để người bốc của Lá Lành đọc câu hỏi này, và để câu hỏi được lưu tạm trong một Google Sheet riêng của người bốc cho tới khi có bài (tối đa hết ngày). Câu hỏi không kèm tên, ngày sinh hay thông tin tài khoản.</span>
    </label>
    <p className="human-tarot-panel__note">Đừng ghi tên đầy đủ, số điện thoại hay chi tiết giúp nhận ra người khác.</p>
    {reframe ? <p className="tarot-error" role="alert">{reframe}</p> : null}
    {create.isError && !reframe && !problem?.startsWith("HUMAN_TAROT_") ? <p className="tarot-error" role="alert">Chưa gửi được. Câu hỏi vẫn ở đây; kiểm tra mạng rồi thử lại.</p> : null}
    <button
      className="tarot-primary"
      disabled={!consented || questionTooShort || create.isPending}
      onClick={() => create.mutate()}
      type="button"
    >{create.isPending ? "Đang gửi…" : "Gửi cho người bốc"}<ArrowRight aria-hidden="true" /></button>
    <p className="tarot-private"><LockKey aria-hidden="true" /> Chỉ gửi khi bạn bấm · bạn huỷ hoặc xoá được bất cứ lúc nào.</p>
  </section>;
}
