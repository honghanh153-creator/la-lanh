import { useCallback, useEffect, useId, useRef, useState, type CSSProperties, type MouseEvent, type PointerEvent } from "react";

import { useVibe } from "../../vibe/useVibe";
import { tapFeedback } from "../la/haptics";
import {
  BRAND, DEFAULT_COMPANION_SEED, FLAME_PATH, SPARKLE_PATH, STAR_LANTERN_PATH,
  hashRandom, hslToHex, mixColor, petalsPath, sampleByHour, sampleNumber, sleepiness,
} from "./companionArt";
import type { CompanionProps } from "./companionTypes";
import { DAY_PHASE_LABEL, GROWTH_LEVEL_LABEL, dayStage, growthLevel, resolveFestival, type DayPhase } from "./growth";
import {
  playAnimation, tapPoint, useBursts, useCompanionClock, useCompanionMotion, usePageVisible,
} from "./useCompanionRuntime";
import "./companion.css";

const VB = 240;
const HEAD = { x: 120, y: 129 };
const BODY_PATH = "M120 128C151 128 167 152 167 177C167 197 148 208 120 208C92 208 73 197 73 177C73 152 89 128 120 128Z";
const LEAF = "M0 0C-11 -3 -16 -15 -5 -27C1 -30 4 -29 6 -26C12 -15 8 -4 0 0Z";
const LEAF_SHINE = "M-3 -6C-8 -10 -8 -17 -3 -22C-5 -16 -4 -11 -3 -6Z";

/** Aura tint by hour: peach dawn, lime noon, gold afternoon, violet dusk, dim night. */
const AURA_TABLE: ReadonlyArray<readonly [number, readonly [string]]> = [
  [0, ["#3a2a7a"]], [4.8, ["#3a2a7a"]], [6.2, ["#ffc9a8"]], [9, ["#e9ff8f"]], [12.5, ["#dfff4f"]],
  [15.5, ["#ffd36b"]], [17.6, ["#ff9f7a"]], [19, ["#9b6bff"]], [21.5, ["#4b2f9a"]], [24, ["#3a2a7a"]],
];
const STEM_LENGTH: ReadonlyArray<readonly [number, number]> = [[0, 15], [5, 11], [7.4, 44], [20.5, 44], [22, 22], [24, 15]];
const LEAF_SCALE: ReadonlyArray<readonly [number, number]> = [[0, 0.52], [5, 0.48], [6.4, 0.62], [9.4, 1], [20.5, 1], [22, 0.62], [24, 0.52]];
const BUD: ReadonlyArray<readonly [number, number]> = [[0, 0], [9.2, 0], [10.8, 1], [21, 1], [22.6, 0.75], [24, 0]];
const BLOOM: ReadonlyArray<readonly [number, number]> = [[0, 0], [11, 0], [12.3, 1], [19.6, 1], [21, 0], [24, 0]];
/** Lean in degrees: toward the sunrise in the morning, toward the moon at dusk. */
const LEAN: ReadonlyArray<readonly [number, number]> = [[0, 0], [5, 0], [7, -7], [9.5, 0], [17.4, 0], [19, 9], [21, 9], [22.2, 0], [24, 0]];

function stateCopy(phase: DayPhase, bloom: number, bud: number): string {
  switch (phase) {
    case "dawn": return "vừa thức dậy, đang vươn mầm";
    case "morning": return bud > 0.3 ? "hai lá đã xòe, nụ hoa đang nhú" : "đang mọc hai lá non";
    case "noon": return bloom > 0.5 ? "đang nở hoa" : "nụ hoa đang hé";
    case "afternoon": return "hoa nở, hào quang vàng ấm";
    case "evening": return "hào quang tím, đang nghiêng về phía trăng";
    case "night": return "đang ngủ say. Khuya rồi, đi ngủ thôi";
  }
}

const ACCESSORY_COPY = [
  "",
  " Có thêm một chiếc lá nhỏ.",
  " Có thêm lá và một giọt sương.",
  " Có một ụ rêu và cây nấm nhỏ bên cạnh.",
  " Hoa hai tầng cánh, có một đốm sáng làm bạn.",
  " Đội vòng lá trên đầu.",
  " Hào quang có viền vàng.",
];

/**
 * Option B, "Mầm Aura": a glossy jelly sprout with a breathing aura. The aura
 * hue comes only from the random seed (never birth data) and shifts with the
 * time of day. Grows bean → sprout → two leaves → bud → bloom across the day,
 * sleeps at night, and keeps every accessory it has earned.
 */
export function AuraSproutCompanion({
  now, growthDays = 0, seed = DEFAULT_COMPANION_SEED, vibe, size = 220, reacting = null,
  onTap, label, still = false, festival = "auto", welcomeBack = false, className = "",
}: CompanionProps) {
  const uid = useId().replace(/:/g, "");
  const rootRef = useRef<HTMLDivElement | null>(null);
  const reactRef = useRef<SVGGElement | null>(null);
  const eyesRef = useRef<SVGGElement | null>(null);
  const visible = usePageVisible();
  const at = useCompanionClock(now, visible);
  const stage = dayStage(at);
  const { motion, canAnimate } = useCompanionMotion({ rootRef, still, resting: stage.resting, visible });
  const { bursts, addBurst } = useBursts();
  const [tapJoy, setTapJoy] = useState(false);
  // Mischief: short, random tricks so the sprout feels cheeky, never needy.
  const [trick, setTrick] = useState<Trick | null>(null);
  const shared = useVibe();
  const activeVibe = vibe ?? shared.vibe;
  const roast = activeVibe === "roast";

  const level = growthLevel(growthDays);
  const h = stage.hour;
  const fest = resolveFestival(festival, at);
  const sleep = sleepiness(h);
  const asleep = sleep > 0.55;
  const stemLength = sampleNumber(STEM_LENGTH, h) * (1 + level * 0.05);
  const leafScale = sampleNumber(LEAF_SCALE, h) * 1.22;
  const bud = sampleNumber(BUD, h);
  const bloom = fest === "tet" && !stage.resting ? Math.max(0.85, sampleNumber(BLOOM, h)) : sampleNumber(BLOOM, h);
  const lean = sampleNumber(LEAN, h);

  const seedHue = Math.floor(hashRandom(seed >>> 0, 11) * 360);
  const seedColor = hslToHex(seedHue, 88, 70);
  const [phaseTint] = sampleByHour(AURA_TABLE, h);
  const auraOuter = roast ? mixColor(phaseTint, BRAND.coral, 0.35) : phaseTint;
  const auraInner = mixColor(seedColor, phaseTint, 0.35);
  const tetPalette = hashRandom(seed >>> 0, 77) > 0.5 ? { petal: "#ffd23f", deep: "#ff9a1f" } : { petal: "#ff9cc6", deep: "#ff5f9e" };
  const petalHue = (300 + (seedHue % 75)) % 360;
  const petal = fest === "tet" ? tetPalette.petal : hslToHex(petalHue, 95, 80);
  const petalDeep = fest === "tet" ? tetPalette.deep : hslToHex(petalHue, 82, 62);

  const happy = !asleep && (reacting === "happy" || tapJoy);
  const thinking = !asleep && reacting === "think" && !tapJoy;
  const top = { x: HEAD.x, y: HEAD.y - stemLength };
  const leafAngle = 62 + 70 * sleep;

  // Lively idle: random blinks and glances while motion runs and Lá is awake.
  useEffect(() => {
    if (motion !== "running" || asleep) return undefined;
    let timer = 0;
    let glanceTimer = 0;
    const root = rootRef.current;
    const blink = () => {
      if (canAnimate()) {
        const double = Math.random() < 0.2;
        playAnimation(eyesRef.current, double
          ? [{ transform: "scaleY(1)" }, { transform: "scaleY(0.1)" }, { transform: "scaleY(1)" }, { transform: "scaleY(0.1)" }, { transform: "scaleY(1)" }]
          : [{ transform: "scaleY(1)" }, { transform: "scaleY(0.08)" }, { transform: "scaleY(1)" }], { duration: double ? 360 : 170, easing: "ease-in-out" });
      }
      timer = window.setTimeout(blink, 2400 + Math.random() * 3600);
    };
    const glance = () => {
      if (canAnimate() && root && root.dataset.pointer !== "on") {
        root.style.setProperty("--lc-lx", ((Math.random() - 0.5) * 1.4).toFixed(2));
        root.style.setProperty("--lc-ly", ((Math.random() - 0.6) * 1).toFixed(2));
        window.setTimeout(() => {
          if (root.dataset.pointer !== "on") {
            root.style.setProperty("--lc-lx", "0");
            root.style.setProperty("--lc-ly", "0");
          }
        }, 1300);
      }
      glanceTimer = window.setTimeout(glance, 3800 + Math.random() * 4200);
    };
    let trickTimer = 0;
    const mischief = () => {
      if (canAnimate()) {
        const next = IDLE_TRICKS[Math.floor(Math.random() * IDLE_TRICKS.length)];
        setTrick(next);
        playTrickBody(reactRef.current, next);
      }
      trickTimer = window.setTimeout(mischief, 4200 + Math.random() * 4800);
    };
    timer = window.setTimeout(blink, 1800);
    glanceTimer = window.setTimeout(glance, 2600);
    trickTimer = window.setTimeout(mischief, 3200);
    return () => {
      window.clearTimeout(timer);
      window.clearTimeout(glanceTimer);
      window.clearTimeout(trickTimer);
    };
  }, [motion, asleep, canAnimate]);

  useEffect(() => {
    if (!trick) return undefined;
    const timer = window.setTimeout(() => setTrick(null), TRICK_MS[trick]);
    return () => window.clearTimeout(timer);
  }, [trick]);

  // A happy reaction from outside gets one joyful hop.
  useEffect(() => {
    if (reacting !== "happy" || asleep || !canAnimate()) return;
    playAnimation(reactRef.current, [
      { transform: "translateY(0) scale(1, 1)" },
      { transform: "translateY(2px) scale(1.12, 0.86)", offset: 0.18 },
      { transform: "translateY(-16px) scale(0.9, 1.12)", offset: 0.45 },
      { transform: "translateY(0) scale(1.08, 0.92)", offset: 0.72 },
      { transform: "translateY(0) scale(1, 1)" },
    ], { duration: 820, easing: "cubic-bezier(.3,.7,.4,1)" });
  }, [reacting, asleep, canAnimate]);

  useEffect(() => {
    if (!tapJoy) return undefined;
    const timer = window.setTimeout(() => setTapJoy(false), 1100);
    return () => window.clearTimeout(timer);
  }, [tapJoy]);

  const handleTap = useCallback((event: MouseEvent<HTMLButtonElement>) => {
    onTap?.();
    if (asleep) {
      // Sleeping: a tiny squish only. No sparkle, no reward (G6).
      if (canAnimate()) playAnimation(reactRef.current, [{ transform: "scale(1, 1)" }, { transform: "scale(1.03, 0.97)" }, { transform: "scale(1, 1)" }], { duration: 700, easing: "ease-in-out" });
      return;
    }
    tapFeedback();
    const point = tapPoint(event, { width: VB, height: VB }, { x: 120, y: 150 });
    const root = rootRef.current;
    if (root) {
      root.style.setProperty("--lc-lx", Math.max(-1, Math.min(1, (point.x - 120) / 70)).toFixed(2));
      root.style.setProperty("--lc-ly", Math.max(-1, Math.min(1, (point.y - 168) / 70)).toFixed(2));
    }
    const animate = canAnimate();
    // Taps get a random cheeky answer: a giggle-squish, a "nyeh" with tongue
    // out, or a playful dodge away from the finger.
    const roll = Math.random();
    const answer: Trick | "joy" = roll < 0.4 ? "joy" : roll < 0.7 ? "nyeh" : "dodge";
    if (answer === "joy") setTapJoy(true);
    else { setTapJoy(false); setTrick(answer); }
    if (!animate && motion !== "still") return;
    addBurst(point.x, Math.min(point.y, 150));
    if (!animate) return;
    if (answer === "joy") playAnimation(reactRef.current, [
      { transform: "scale(1, 1)" },
      { transform: "scale(1.16, 0.84)", offset: 0.14 },
      { transform: "scale(0.9, 1.12) translateY(-6px)", offset: 0.34 },
      { transform: "scale(1.06, 0.95)", offset: 0.55 },
      { transform: "scale(0.98, 1.02)", offset: 0.75 },
      { transform: "scale(1, 1)" },
    ], { duration: 900, easing: "ease-out" });
    else playTrickBody(reactRef.current, answer, point.x < 120 ? 1 : -1);
  }, [addBurst, asleep, canAnimate, motion, onTap]);

  const handlePointerMove = useCallback((event: PointerEvent<HTMLDivElement>) => {
    const node = rootRef.current;
    if (!node || event.pointerType === "touch" || asleep || !canAnimate()) return;
    const rect = node.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * VB;
    const y = ((event.clientY - rect.top) / rect.height) * VB;
    node.dataset.pointer = "on";
    node.style.setProperty("--lc-lx", Math.max(-1, Math.min(1, (x - 120) / 90)).toFixed(2));
    node.style.setProperty("--lc-ly", Math.max(-1, Math.min(1, (y - 168) / 90)).toFixed(2));
  }, [asleep, canAnimate]);

  const handlePointerLeave = useCallback(() => {
    const node = rootRef.current;
    if (!node) return;
    delete node.dataset.pointer;
    node.style.setProperty("--lc-lx", "0");
    node.style.setProperty("--lc-ly", "0");
  }, []);

  const id = (name: string) => `${uid}-${name}`;
  const ref = (name: string) => `url(#${id(name)})`;
  const eyeY = 167;
  const ink = "#24123f";

  const ariaLabel = `Mầm Aura, ${DAY_PHASE_LABEL[stage.phase]}, ${stateCopy(stage.phase, bloom, bud)}${!asleep ? ", vẻ mặt tinh nghịch" : ""}. Mầm đang là ${GROWTH_LEVEL_LABEL[level]}.${ACCESSORY_COPY[level]}${fest === "tet" ? " Hoa đang mặc sắc Tết." : fest === "trung-thu" ? " Trăng Trung Thu sau lưng, có đèn ông sao." : ""}${welcomeBack && !stage.resting ? " Mầm giữ cho bạn một chiếc lá mới." : ""}`;

  const leaves = [
    { side: -1, x: top.x, y: top.y + 7, scale: leafScale, angle: -leafAngle },
    { side: 1, x: top.x, y: top.y + 7, scale: leafScale, angle: leafAngle },
  ];
  if (level >= 1) leaves.push({ side: -1, x: HEAD.x, y: HEAD.y - stemLength * 0.42, scale: 0.68 * leafScale, angle: -78 - 40 * sleep });
  if (level >= 2) leaves.push({ side: 1, x: HEAD.x, y: HEAD.y - stemLength * 0.62, scale: 0.62 * leafScale, angle: 80 + 40 * sleep });

  return (
    <div
      ref={rootRef}
      className={`lc-companion lc-aura ${className}`.trim()}
      data-phase={stage.phase}
      data-cmotion={motion}
      data-vibe={activeVibe}
      data-festival={fest ?? undefined}
      data-reacting={reacting ?? undefined}
      data-level={level}
      data-asleep={asleep ? "true" : undefined}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      style={{ width: size }}
    >
      <svg role="img" aria-label={ariaLabel} viewBox={`0 0 ${VB} ${VB}`} width="100%" focusable="false" className="lc-svg">
        <defs>
          <radialGradient id={id("aura")}>
            <stop offset="0" style={{ stopColor: auraInner }} stopOpacity="1" />
            <stop offset="0.5" style={{ stopColor: auraOuter }} stopOpacity="0.6" />
            <stop offset="1" style={{ stopColor: auraOuter }} stopOpacity="0" />
          </radialGradient>
          <linearGradient id={id("ring")} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" style={{ stopColor: auraInner }} />
            <stop offset="1" stopColor={roast ? BRAND.coral : BRAND.lime} />
          </linearGradient>
          <radialGradient id={id("body")} cx="0.38" cy="0.3" r="0.78">
            <stop offset="0" stopColor="#f4ffd2" />
            <stop offset="0.3" stopColor="#b6ff2a" />
            <stop offset="0.7" stopColor="#3ff23a" />
            <stop offset="1" stopColor="#13c24a" />
          </radialGradient>
          <radialGradient id={id("core")} cx="0.5" cy="0.7" r="0.6">
            <stop offset="0" stopColor={BRAND.lime} stopOpacity="0.95" />
            <stop offset="1" stopColor={BRAND.lime} stopOpacity="0" />
          </radialGradient>
          <linearGradient id={id("gloss")} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0.95" />
            <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
          <linearGradient id={id("leaf")} x1="0" y1="1" x2="0.4" y2="0">
            <stop offset="0" stopColor="#1fc94a" />
            <stop offset="0.6" stopColor="#7dff3a" />
            <stop offset="1" stopColor="#efffa0" />
          </linearGradient>
          <radialGradient id={id("petal")} cx="0.5" cy="0.5" r="0.6">
            <stop offset="0" stopColor="#fffaf2" />
            <stop offset="0.5" stopColor={petal} />
            <stop offset="1" stopColor={petalDeep} />
          </radialGradient>
          <radialGradient id={id("glow")}>
            <stop offset="0" stopColor={BRAND.lime} stopOpacity="0.9" />
            <stop offset="1" stopColor={BRAND.lime} stopOpacity="0" />
          </radialGradient>
          <radialGradient id={id("moon")} cx="0.42" cy="0.4">
            <stop offset="0" stopColor="#fffbe6" />
            <stop offset="0.7" stopColor="#ffe9a6" />
            <stop offset="1" stopColor="#ffd36b" />
          </radialGradient>
        </defs>

        <g className="lc-aura-wrap" opacity={1 - sleep * 0.62}>
          {fest === "trung-thu" ? (
            <g>
              <circle cx="120" cy="120" r="96" fill={ref("glow")} opacity="0.25" />
              <circle cx="120" cy="118" r="70" fill={ref("moon")} className="lc-festival-moon" />
              <circle cx="98" cy="102" r="9" fill="#f2d68a" opacity="0.5" />
              <circle cx="140" cy="132" r="6" fill="#f2d68a" opacity="0.45" />
            </g>
          ) : (
            <circle className="lc-aura-halo" cx="120" cy="140" r="108" fill={ref("aura")} />
          )}
          <circle className="lc-aura-ring" cx="120" cy="146" r="84" fill="none" stroke={ref("ring")} strokeWidth={level >= 6 ? 3.2 : 2.2} strokeDasharray="2 10" strokeLinecap="round" opacity="0.7" />
          {level >= 6 ? <circle cx="120" cy="146" r="94" fill="none" stroke="#ffd36b" strokeWidth="1.4" opacity="0.65" className="lc-aura-ring lc-aura-ring--gold" /> : null}
          {!stage.resting ? [0, 1, 2].map((i) => (
            <g key={i} transform={`translate(${[46, 190, 176][i]} ${[96, 82, 196][i]}) scale(${[0.7, 0.55, 0.45][i]})`}><path className="lc-twinkle" d={SPARKLE_PATH} fill={i === 1 && roast ? BRAND.coral : "#fff9e9"} style={{ animationDelay: `${i * 0.8}s` }} /></g>
          )) : null}
        </g>

        {fest === "trung-thu" ? (
          <g transform="translate(186 128)">
            <g className="lc-lantern">
              <path d="M0 -26V-8" stroke="#3a2a5c" strokeWidth="1" />
              <circle r="14" fill="#ffd23f" opacity={stage.resting ? 0.15 : 0.35} />
              <path d={STAR_LANTERN_PATH} transform="scale(1.5)" fill="#ff5a4a" stroke="#ffd23f" strokeWidth="0.8" />
              <ellipse cx="-3" cy="-4" rx="2.4" ry="1.4" fill="#ffffff" opacity="0.6" />
            </g>
          </g>
        ) : null}
        {fest === "tet" && !stage.resting ? (
          <g className="lc-confetti">
            {[[44, 150, "#ff5a4a"], [62, 104, "#ffd23f"], [188, 112, "#ff9cc6"], [200, 170, "#ffd23f"], [176, 74, "#ff5a4a"]].map(([x, y, c], i) => (
              <g key={i} transform={`translate(${x} ${y})`}>
                <rect className="lc-bob" x="-3" y="-2" width="6" height="4" rx="2" fill={c as string} style={{ animationDelay: `${-i * 0.6}s` }} />
              </g>
            ))}
          </g>
        ) : null}

        <ellipse className="lc-shadow" cx="120" cy="209" rx="46" ry="7" fill={BRAND.violetDeep} opacity="0.22" />

        {level >= 3 ? (
          <g>
            <path d="M58 210C58 199 70 194 82 197C90 191 102 197 100 210Z" fill={stage.resting ? "#4a5d6a" : "#7fbf5a"} />
            <path d="M68 197V190h3v7Z" fill="#fff1e0" />
            <path d="M63 191a6.5 5.5 0 0 1 13 0Z" fill={stage.resting ? "#7a5fb3" : BRAND.coral} />
            <circle cx="67" cy="188.5" r="1.1" fill="#fff9e9" />
          </g>
        ) : null}

        <g transform={`translate(120 208) scale(${(0.84 + level * 0.027).toFixed(3)}) translate(-120 -208)`}>
        <g ref={reactRef} className="lc-react">
          <g className="lc-jelly">
            <g transform={`rotate(${lean.toFixed(2)} ${HEAD.x} ${HEAD.y + 4})`}>
              <g className="lc-stem">
                <path d={`M${HEAD.x} ${HEAD.y + 4}Q${HEAD.x - 5} ${HEAD.y - stemLength * 0.5} ${top.x} ${top.y}`} stroke="#2fd94a" strokeWidth="5" strokeLinecap="round" fill="none" />
                <path d={`M${HEAD.x - 1} ${HEAD.y}Q${HEAD.x - 5.5} ${HEAD.y - stemLength * 0.5} ${top.x - 1} ${top.y + 2}`} stroke="#d8ff9a" strokeWidth="1.2" strokeLinecap="round" fill="none" opacity="0.7" />
                {leaves.map((leaf, i) => (
                  <g key={i} transform={`translate(${leaf.x.toFixed(1)} ${leaf.y.toFixed(1)}) rotate(${leaf.angle.toFixed(1)}) scale(${leaf.scale.toFixed(3)})`}>
                    <g className={`lc-leaf lc-leaf--${leaf.side < 0 ? "l" : "r"}`}>
                      <path d={LEAF} fill={ref("leaf")} />
                      <path d={LEAF_SHINE} fill="#ffffff" opacity="0.55" />
                      {i === 1 && level >= 2 && !asleep ? <circle className="lc-dew" cx="2" cy="-14" r="2.6" fill="#e9fbff" opacity="0.85" stroke="#ffffff" strokeWidth="0.6" /> : null}
                    </g>
                  </g>
                ))}
                {welcomeBack && !stage.resting ? (
                  <g transform={`translate(${HEAD.x} ${HEAD.y - stemLength * 0.3}) rotate(-120) scale(0.5)`}>
                    <circle r="16" fill={ref("glow")} className="lc-gift-glow" />
                    <path d={LEAF} fill={BRAND.lime} stroke={BRAND.violet} strokeWidth="1.4" />
                  </g>
                ) : null}
                <g transform={`translate(${top.x} ${top.y})`}>
                  {bud > 0.02 && bloom < 0.98 ? (
                    <g transform={`scale(${(bud * (1 - bloom * 0.6)).toFixed(3)})`}>
                      <path d="M0 3C-6 3 -7 -4 0 -13C7 -4 6 3 0 3Z" fill={ref("petal")} />
                      <path d="M-2 -2C-3 -5 -2 -8 0 -10" stroke="#ffffff" strokeWidth="1.2" strokeLinecap="round" fill="none" opacity="0.7" />
                    </g>
                  ) : null}
                  {bloom > 0.02 ? (
                    <g className="lc-bloom" transform={`scale(${(0.25 + 0.75 * bloom).toFixed(3)})`}>
                      {level >= 4 ? <path d={petalsPath(6, 10, 7)} fill={petalDeep} opacity="0.75" transform="rotate(30)" /> : null}
                      <path d={petalsPath(6, 7.5, 6.2)} fill={ref("petal")} />
                      <circle r="4.6" fill="#ffd23f" />
                      <circle cx="-1.4" cy="-1.6" r="1.5" fill="#fffbe0" />
                    </g>
                  ) : null}
                </g>
              </g>
            </g>

            <g className="lc-body">
              <path d={BODY_PATH} fill={ref("body")} />
              <ellipse cx="120" cy="190" rx="34" ry="15" fill={ref("core")} />
              <path d="M84 192C92 203 108 206 120 206C134 206 148 203 156 193C148 199 134 202 120 202C106 202 93 199 84 192Z" fill="#f2ffc4" opacity="0.55" />
              <path d={BODY_PATH} fill="none" stroke="#ffffff" strokeOpacity="0.35" strokeWidth="1.4" />
              <path d="M92 146C98 136 110 132 118 133C108 138 100 146 96 156C93 155 91 151 92 146Z" fill={ref("gloss")} />
              <ellipse cx="147" cy="152" rx="3.4" ry="2.2" fill="#ffffff" opacity="0.7" transform="rotate(-30 147 152)" />
              {level >= 5 ? (
                <g>
                  {[-16, 0, 16].map((dx, i) => (
                    <path key={i} d="M0 0C-5 -2 -7 -8 -1 -13C4 -9 4 -3 0 0Z" transform={`translate(${HEAD.x + dx} ${HEAD.y + 3 + Math.abs(dx) * 0.25}) rotate(${dx * 2.2}) scale(1.1)`} fill={i === 1 ? "#ffd23f" : "#9be35a"} stroke="#4c9a45" strokeWidth="0.6" />
                  ))}
                </g>
              ) : null}
              <path d={BODY_PATH} fill={BRAND.violetDeep} opacity={sleep * 0.3} />
              <ellipse cx="96" cy="181" rx="7" ry="3.8" fill={roast ? BRAND.coral : "#ff7fb5"} opacity={0.62 + (happy ? 0.25 : 0)} />
              <ellipse cx="144" cy="181" rx="7" ry="3.8" fill={roast ? BRAND.coral : "#ff7fb5"} opacity={0.62 + (happy ? 0.25 : 0)} />

              {asleep ? (
                <g stroke={ink} strokeWidth="2.4" strokeLinecap="round" fill="none">
                  <path d={`M98 ${eyeY}Q104 ${eyeY + 5} 110 ${eyeY}`} />
                  <path d={`M130 ${eyeY}Q136 ${eyeY + 5} 142 ${eyeY}`} />
                  <path d="M116 184Q120 186.5 124 184" strokeWidth="1.8" />
                </g>
              ) : happy ? (
                <g>
                  <g stroke={ink} strokeWidth="2.6" strokeLinecap="round" fill="none">
                    <path d={`M97 ${eyeY + 2}Q104 ${eyeY - 6} 111 ${eyeY + 2}`} />
                    <path d={`M129 ${eyeY + 2}Q136 ${eyeY - 6} 143 ${eyeY + 2}`} />
                  </g>
                  <path d="M111 179Q120 194 129 179Z" fill={ink} />
                  <path d="M115 186Q120 190 125 186Q120 184 115 186Z" fill="#ff8fbf" />
                </g>
              ) : (
                <g>
                  <g ref={eyesRef} className="lc-eyes">
                    <g transform={trick === "side" ? "translate(-4.5 1)" : undefined}>
                      <g className="lc-pupils">
                        <ellipse cx="104" cy={roast ? eyeY + 1.5 : eyeY} rx="6.4" ry={roast ? 5.6 : 7.8} fill={ink} />
                        <circle cx="106.4" cy={eyeY - 3} r="2.4" fill="#ffffff" />
                        <circle cx="102" cy={eyeY + 3} r="1.1" fill="#ffffff" opacity="0.85" />
                        {trick === "wink" || trick === "nyeh" ? null : <>
                          <ellipse cx="136" cy={roast ? eyeY + 1.5 : eyeY - 0.5} rx="6.4" ry={roast ? 5.6 : 8.4} fill={ink} />
                          <circle cx="138.4" cy={eyeY - 3.5} r="2.6" fill="#ffffff" />
                          <circle cx="134" cy={eyeY + 3} r="1.1" fill="#ffffff" opacity="0.85" />
                        </>}
                      </g>
                    </g>
                  </g>
                  {trick === "wink" || trick === "nyeh"
                    ? <path d={`M129 ${eyeY + 1}L136 ${eyeY - 3}L143 ${eyeY + 1}`} stroke={ink} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                    : null}
                  <g stroke={ink} strokeWidth="2.4" strokeLinecap="round" fill="none" className="lc-brows">
                    {roast
                      ? <><path d="M96 155Q103 149 111 154" /><path d="M129 158L143 156" /></>
                      : trick === "side"
                        ? <><path d="M96 156L111 154" /><path d="M129 154L144 156" /></>
                        : <><path d="M97 154Q103 150.5 110 153" /><path d="M129 151Q136 145 144 150" /></>}
                  </g>
                  {thinking && !trick ? (
                    <circle cx="125" cy="184" r="2.6" fill={ink} />
                  ) : trick === "blep" || trick === "nyeh" ? (
                    <g>
                      <path d="M110 180Q120 188 131 179" stroke={ink} strokeWidth="2.4" strokeLinecap="round" fill="none" />
                      <path className="lc-tongue" d="M119 184.5Q119 194 125 194Q130.5 193.5 128.5 183.5Z" fill="#ff7fa8" stroke={ink} strokeWidth="1.8" strokeLinejoin="round" />
                      <path d="M124.3 186.5V190.5" stroke="#c94f7c" strokeWidth="1" strokeLinecap="round" />
                    </g>
                  ) : roast ? (
                    <path d="M111 183Q121 186 130 177" stroke={ink} strokeWidth="2.4" strokeLinecap="round" fill="none" />
                  ) : (
                    <g>
                      <path d="M109 179.5Q119 191 131.5 178" stroke={ink} strokeWidth="2.4" strokeLinecap="round" fill="none" />
                      <path d="M126.5 183.6L128.6 187.4L130.2 182.4" fill="#ffffff" stroke={ink} strokeWidth="1.3" strokeLinejoin="round" />
                    </g>
                  )}
                </g>
              )}
            </g>
          </g>
        </g>
        </g>

        {level >= 4 && !asleep ? (
          <g transform="translate(120 146)">
            <g className="lc-orbit lc-orbit--slow">
              <circle cx="78" r="7" fill={ref("glow")} />
              <circle cx="78" r="2" fill="#f6ffbf" />
            </g>
          </g>
        ) : null}

        {thinking ? (
          <g className="lc-think" fill="#fff9e9" stroke={BRAND.violet} strokeWidth="1">
            <circle cx="160" cy="118" r="3" />
            <circle cx="170" cy="104" r="4.5" style={{ animationDelay: "0.2s" }} />
            <circle cx="184" cy="88" r="6.5" style={{ animationDelay: "0.4s" }} />
          </g>
        ) : null}

        {roast && !asleep ? (
          <g className="lc-roast-sparks">
            {[{ x: 64, y: 136 }, { x: 178, y: 140 }, { x: 160, y: 96 }].map((spark, i) => (
              <g key={i} transform={`translate(${spark.x} ${spark.y}) scale(${i === 2 ? 0.8 : 1.1})`}>
                <path className="lc-flame" d={FLAME_PATH} fill={i === 1 ? BRAND.lime : BRAND.coral} style={{ animationDelay: `${-i * 0.35}s` }} />
              </g>
            ))}
          </g>
        ) : null}

        {asleep ? (
          <g className="lc-zz" fill={stage.resting ? "#fff9e9" : BRAND.violet} fontFamily="'Be Vietnam Pro', system-ui, sans-serif" fontWeight="700">
            <text className="lc-z" x="156" y="138" fontSize="13">z</text>
            <text className="lc-z" x="168" y="122" fontSize="9" style={{ animationDelay: "0.9s" }}>z</text>
          </g>
        ) : null}

        {bursts.map((burst) => (
          <g key={burst.id} transform={`translate(${burst.x.toFixed(1)} ${burst.y.toFixed(1)})`}>
            <g className="lc-burst">
              {roast
                ? <path d={FLAME_PATH} transform="scale(2.2)" fill={BRAND.coral} />
                : <path d={SPARKLE_PATH} transform="scale(1.6)" fill={BRAND.lime} />}
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <circle key={i} className="lc-burst-dot" r={i % 2 ? 1.6 : 2.2} fill={i % 2 ? "#fff9e9" : roast ? BRAND.lime : "#ff9cc6"} style={{ "--lc-dx": `${Math.cos((i / 6) * Math.PI * 2) * 20}px`, "--lc-dy": `${Math.sin((i / 6) * Math.PI * 2) * 20}px` } as CSSProperties} />
              ))}
            </g>
          </g>
        ))}
      </svg>
      <button
        type="button"
        className="lc-companion__hit lc-companion__hit--round"
        aria-label={label ?? "Chạm vào Mầm Aura"}
        onClick={handleTap}
      />
    </div>
  );
}

type Trick = "wink" | "blep" | "side" | "wiggle" | "nyeh" | "dodge";

const IDLE_TRICKS: readonly Trick[] = ["wink", "blep", "side", "wiggle", "wink", "side"];

const TRICK_MS: Record<Trick, number> = {
  wink: 650, blep: 1100, side: 1500, wiggle: 900, nyeh: 1200, dodge: 900,
};

/** Body motion that goes with a trick; the face is rendered from state. */
function playTrickBody(node: SVGGElement | null, trick: Trick, away = 1): void {
  if (trick === "wiggle") {
    playAnimation(node, [
      { transform: "rotate(0deg)" },
      { transform: "rotate(-7deg) translateX(-2px)", offset: 0.2 },
      { transform: "rotate(7deg) translateX(2px)", offset: 0.45 },
      { transform: "rotate(-4deg)", offset: 0.7 },
      { transform: "rotate(0deg)" },
    ], { duration: 820, easing: "ease-in-out" });
  } else if (trick === "dodge") {
    playAnimation(node, [
      { transform: "translateX(0) rotate(0deg)" },
      { transform: `translateX(${18 * away}px) translateY(-8px) rotate(${10 * away}deg) scale(0.95, 1.05)`, offset: 0.3 },
      { transform: `translateX(${12 * away}px) rotate(${-4 * away}deg)`, offset: 0.55 },
      { transform: "translateX(0) rotate(0deg) scale(1.05, 0.95)", offset: 0.82 },
      { transform: "translateX(0) rotate(0deg)" },
    ], { duration: 820, easing: "cubic-bezier(.3,.8,.4,1)" });
  } else if (trick === "nyeh" || trick === "blep") {
    playAnimation(node, [
      { transform: "rotate(0deg)" },
      { transform: "rotate(-5deg) scale(1.04, 0.97)", offset: 0.3 },
      { transform: "rotate(3deg)", offset: 0.65 },
      { transform: "rotate(0deg)" },
    ], { duration: 700, easing: "ease-out" });
  }
}
