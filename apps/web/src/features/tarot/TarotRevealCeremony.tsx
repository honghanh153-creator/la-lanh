import { Sparkle } from "@phosphor-icons/react";
import { useCallback, useEffect, useRef } from "react";

import type { TarotSession } from "../../shared/api/client";
import { useOnboardingMotion } from "../../shared/ui/onboardingMotion";
import { TarotCardArt, TarotCardBack } from "./TarotCardArt";
import "./tarot-reveal.css";

export function TarotRevealCeremony({ cards, onComplete }: {
  cards: TarotSession["selected_cards"];
  onComplete: () => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  const timer = useRef<number | null>(null);
  const finished = useRef(false);
  const { paused } = useOnboardingMotion();
  const finish = useCallback(() => {
    if (finished.current) return;
    finished.current = true;
    if (timer.current !== null) window.clearTimeout(timer.current);
    onComplete();
  }, [onComplete]);

  useEffect(() => {
    const preference = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (paused || preference?.matches) {
      finish();
      return;
    }
    heading.current?.focus();
    timer.current = window.setTimeout(finish, 2800);
    const reduceMotion = (event: MediaQueryListEvent) => {
      if (event.matches) finish();
    };
    preference?.addEventListener("change", reduceMotion);
    return () => {
      if (timer.current !== null) window.clearTimeout(timer.current);
      preference?.removeEventListener("change", reduceMotion);
    };
  }, [finish, paused]);

  return <section className="tarot-reveal" aria-labelledby="tarot-reveal-title">
    <div className="tarot-reveal__halo" aria-hidden="true" />
    <div className="tarot-reveal__orbit" aria-hidden="true"><Sparkle weight="fill" /></div>
    <p className="tarot-reveal__eyebrow">Đã chọn đủ {cards.length} lá</p>
    <h1 id="tarot-reveal-title" ref={heading} tabIndex={-1}>Bài của bạn đang mở</h1>
    <div className="tarot-reveal__cards" data-count={cards.length} aria-label="Những lá bạn đã chọn" role="group">
      {cards.map((selected, index) => <div className="tarot-reveal__card" key={selected.position_key}>
        <div className="tarot-reveal__turn" style={{ animationDelay: `${180 + index * 180}ms` }}>
          <div className="tarot-reveal__back" aria-hidden="true"><TarotCardBack /></div>
          <div className="tarot-reveal__front">
            <TarotCardArt card={selected.card} />
          </div>
        </div>
      </div>)}
    </div>
    <p className="tarot-reveal__caption">Một chút tò mò. Rồi mình đọc từng lá nhé.</p>
    <button className="tarot-reveal__skip" onClick={finish} type="button">Xem bài ngay →</button>
  </section>;
}
