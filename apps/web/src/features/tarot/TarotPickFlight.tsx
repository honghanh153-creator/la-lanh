import { useLayoutEffect, useRef } from "react";

import type { TarotCard } from "../../shared/api/client";
import { TarotCardArt, TarotCardBack } from "./TarotCardArt";

const DURATION_MS = 1150;

/**
 * Presentation-only: lifts the picked card out of the fan, flips it to its face and
 * lands it on its slot. Callers render it only when motion is allowed; if the browser
 * lacks the Web Animations API or either element is missing, it finishes immediately.
 */
export function TarotPickFlight({ card, from, to, onDone }: {
  card: TarotCard;
  from: () => HTMLElement | null;
  to: () => HTMLElement | null;
  onDone: () => void;
}) {
  const root = useRef<HTMLDivElement>(null);
  const turn = useRef<HTMLDivElement>(null);
  const done = useRef(onDone);
  done.current = onDone;
  const source = useRef(from);
  const target = useRef(to);

  useLayoutEffect(() => {
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      done.current();
    };
    const element = root.current;
    const inner = turn.current;
    const fromElement = source.current();
    const toElement = target.current();
    const fromRect = fromElement?.getBoundingClientRect();
    const toRect = toElement?.getBoundingClientRect();
    if (
      !element || !inner || !fromElement || !fromRect || !toRect
      || typeof element.animate !== "function" || typeof inner.animate !== "function"
      || !fromElement.offsetWidth || !toRect.width
    ) {
      finish();
      return;
    }
    const width = fromElement.offsetWidth;
    const height = (width * 5) / 3;
    element.style.width = `${width}px`;
    element.style.height = `${height}px`;
    const startX = fromRect.left + fromRect.width / 2 - width / 2;
    const startY = fromRect.top + fromRect.height / 2 - height / 2;
    const liftScale = 1.9;
    const liftX = startX - (width * (liftScale - 1)) / 2;
    const liftY = startY - height * 0.62;
    const start = `translate(${startX}px, ${startY}px) scale(1)`;
    const lift = `translate(${liftX}px, ${liftY}px) scale(${liftScale})`;
    const end = `translate(${toRect.left}px, ${toRect.top}px) scale(${toRect.width / width})`;
    const timing: KeyframeAnimationOptions = { duration: DURATION_MS, fill: "forwards" };
    const move = element.animate([
      { transform: start, offset: 0, easing: "cubic-bezier(0.22, 1, 0.36, 1)" },
      { transform: lift, offset: 0.3 },
      { transform: lift, offset: 0.62, easing: "cubic-bezier(0.65, 0, 0.35, 1)" },
      { transform: end, offset: 1 },
    ], timing);
    const flip = inner.animate([
      { transform: "rotateY(0deg)", offset: 0 },
      { transform: "rotateY(0deg)", offset: 0.2, easing: "cubic-bezier(0.45, 0, 0.2, 1)" },
      { transform: "rotateY(180deg)", offset: 0.52 },
      { transform: "rotateY(180deg)", offset: 1 },
    ], timing);
    element.style.visibility = "visible";
    const fallback = window.setTimeout(finish, DURATION_MS + 400);
    move.finished.then(finish, () => undefined);
    return () => {
      window.clearTimeout(fallback);
      if (!finished) {
        move.cancel();
        flip.cancel();
      }
    };
  }, []);

  return <div aria-hidden="true" className="tarot-pick-flight" ref={root}>
    <div className="tarot-pick-flight__turn" ref={turn}>
      <div className="tarot-pick-flight__face tarot-pick-flight__face--back"><TarotCardBack /></div>
      <div className="tarot-pick-flight__face tarot-pick-flight__face--front"><TarotCardArt card={card} decorative /></div>
    </div>
  </div>;
}
