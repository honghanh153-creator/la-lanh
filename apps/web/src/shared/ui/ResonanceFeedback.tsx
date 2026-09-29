import { ShareNetwork, ThumbsDown, ThumbsUp, X } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";

import type { ResonanceChoice } from "../api/client";

type ResonanceFeedbackProps = {
  consented: boolean;
  selected: ResonanceChoice | null;
  pending: boolean;
  onSubmit: (choice: ResonanceChoice) => void;
};

export function ResonanceFeedback({
  consented,
  selected,
  pending,
  onSubmit,
}: ResonanceFeedbackProps) {
  const [consentChoice, setConsentChoice] = useState<ResonanceChoice | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const choiceButtonRef = useRef<HTMLButtonElement>(null);
  const wasOpenRef = useRef(false);

  useEffect(() => {
    if (consentChoice) {
      wasOpenRef.current = true;
      closeButtonRef.current?.focus();
    } else if (wasOpenRef.current) {
      wasOpenRef.current = false;
      choiceButtonRef.current?.focus();
    }
  }, [consentChoice]);

  const choose = (choice: ResonanceChoice, trigger: HTMLButtonElement) => {
    if (consented) onSubmit(choice);
    else {
      choiceButtonRef.current = trigger;
      setConsentChoice(choice);
    }
  };

  const consentDialog = consentChoice ? createPortal(
    <div className="signal-consent-backdrop">
      <dialog
        aria-labelledby="resonance-consent-title"
        aria-modal="true"
        className="signal-consent"
        onKeyDown={(event) => {
          if (event.key === "Escape" && !pending) {
            event.preventDefault();
            setConsentChoice(null);
            return;
          }
          if (event.key !== "Tab") return;
          const buttons = Array.from(
            event.currentTarget.querySelectorAll<HTMLButtonElement>("button:not(:disabled)"),
          );
          const first = buttons[0];
          const last = buttons.at(-1);
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }}
        open
      >
        <button
          aria-label="Đóng"
          className="signal-consent__close"
          disabled={pending}
          onClick={() => setConsentChoice(null)}
          ref={closeButtonRef}
          type="button"
        >
          <X aria-hidden="true" />
        </button>
        <p className="eyebrow">Trước khi gửi</p>
        <h2 id="resonance-consent-title">Giữ phản hồi này?</h2>
        <p>
          Lá Lành sẽ giữ lựa chọn “trúng” hoặc “chưa trúng” tối đa 30 ngày để hiểu chất lượng cách diễn đạt.
          Không có ghi chú tự do, không dùng để suy đoán tính cách.
        </p>
        <div className="signal-consent__actions">
          <button
            className="electric-button"
            disabled={pending}
            onClick={() => {
              onSubmit(consentChoice);
              setConsentChoice(null);
            }}
            type="button"
          >
            {pending ? "Đang gửi…" : "Đồng ý và gửi"}
          </button>
          <button
            className="text-button"
            disabled={pending}
            onClick={() => setConsentChoice(null)}
            type="button"
          >
            Để sau
          </button>
        </div>
      </dialog>
    </div>,
    document.body,
  ) : null;

  return (
    <>
      <div aria-label="Phản hồi và chia sẻ note" className="note-quick-actions" role="group">
        <button
          aria-label="Trúng"
          aria-pressed={selected === "hit"}
          disabled={pending}
          onClick={(event) => choose("hit", event.currentTarget)}
          title="Trúng"
          type="button"
        >
          <ThumbsUp aria-hidden="true" weight={selected === "hit" ? "fill" : "regular"} />
        </button>
        <button
          aria-label="Chưa trúng"
          aria-pressed={selected === "miss"}
          disabled={pending}
          onClick={(event) => choose("miss", event.currentTarget)}
          title="Chưa trúng"
          type="button"
        >
          <ThumbsDown aria-hidden="true" weight={selected === "miss" ? "fill" : "regular"} />
        </button>
        <Link aria-label="Chia sẻ note" title="Chia sẻ note" to="/card">
          <ShareNetwork aria-hidden="true" />
        </Link>
      </div>
      {consentDialog}
    </>
  );
}
