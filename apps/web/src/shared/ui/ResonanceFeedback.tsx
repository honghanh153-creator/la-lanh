import { ArrowBendUpRight, ThumbsDown, ThumbsUp, X } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import type { ResonanceChoice } from "../api/client";

type ResonanceFeedbackProps = {
  consented: boolean;
  selected: ResonanceChoice | null;
  pending: boolean;
  onSubmit: (choice: ResonanceChoice) => void;
  onChangeAngle: () => void;
};

export function ResonanceFeedback({
  consented,
  selected,
  pending,
  onSubmit,
  onChangeAngle,
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
    <section aria-labelledby="resonance-title" className="resonance-feedback">
      <div className="resonance-feedback__heading">
        <div>
          <p className="eyebrow">Bạn thấy sao?</p>
          <h2 id="resonance-title">Góc này có chạm đúng không?</h2>
        </div>
        <span aria-hidden="true">01 tín hiệu</span>
      </div>
      <div className="resonance-feedback__actions">
        <button
          aria-pressed={selected === "hit"}
          disabled={pending}
          onClick={(event) => choose("hit", event.currentTarget)}
          type="button"
        >
          <ThumbsUp aria-hidden="true" weight={selected === "hit" ? "fill" : "regular"} />
          Trúng
        </button>
        <button
          aria-pressed={selected === "miss"}
          disabled={pending}
          onClick={(event) => choose("miss", event.currentTarget)}
          type="button"
        >
          <ThumbsDown aria-hidden="true" weight={selected === "miss" ? "fill" : "regular"} />
          Chưa trúng
        </button>
        <button disabled={pending} onClick={onChangeAngle} type="button">
          <ArrowBendUpRight aria-hidden="true" />
          Đổi góc
        </button>
      </div>
      <p className="resonance-feedback__note">
        Phản hồi chỉ nói về cách diễn đạt, không đánh giá bạn hay độ đúng của chiêm tinh.
      </p>

      {consentDialog}
    </section>
  );
}
