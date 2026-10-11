import { useCallback, useId, useMemo, useRef, type CSSProperties, type MouseEvent, type PointerEvent } from "react";

import { useVibe } from "../../vibe/useVibe";
import { tapFeedback } from "../la/haptics";
import { moonPhase } from "../la/moonPhase";
import {
  BRAND, DEFAULT_COMPANION_SEED, LEAF_PATH, PLANT_TABLE, SKY_TABLE, SPARKLE_PATH, FLAME_PATH, STAR_LANTERN_PATH,
  arcPosition, branchPath, buildTree, circlesPath, eveningGlow, hashRandom, mixColor, moonLitPath,
  nightness, petalsPath, sampleByHour, sleepiness, smoothstep,
} from "./companionArt";
import type { CompanionProps } from "./companionTypes";
import { DAY_PHASE_LABEL, GROWTH_LEVEL_LABEL, dayStage, growthLevel, resolveFestival, type DayPhase } from "./growth";
import {
  playAnimation, tapPoint, useBursts, useCompanionClock, useCompanionMotion, usePageVisible,
} from "./useCompanionRuntime";
import "./companion.css";

const W = 240;
const H = 280;
const WINDOW_PATH = "M22 116A98 98 0 0 1 218 116V250Q218 266 202 266H38Q22 266 22 250Z";
const TREE_BASE = { x: 120, y: 219 };
const TREE_HEIGHT = [42, 62, 84, 102, 116, 126, 134];
const TREE_HALF_WIDTH = [18, 30, 46, 58, 66, 70, 74];
const VINE_REACH = [0, 0, 0.22, 0.38, 0.55, 0.75, 1];

const SUN_TABLE: ReadonlyArray<readonly [number, readonly [string]]> = [
  [0, ["#ff9a6b"]], [5.6, ["#ff9a6b"]], [7, ["#ffc078"]], [10, ["#fff3c4"]], [13, ["#fff6cf"]],
  [16, ["#ffd36b"]], [18, ["#ff8d5c"]], [24, ["#ff8d5c"]],
];
const CLOUD_TABLE: ReadonlyArray<readonly [number, readonly [string]]> = [
  [0, ["#2c2160"]], [5, ["#3d2c72"]], [6.5, ["#ffd2dc"]], [9, ["#ffffff"]], [15, ["#ffffff"]],
  [17.4, ["#ffe2bd"]], [18.8, ["#e7a9d8"]], [20.2, ["#7356b8"]], [22, ["#2c2160"]], [24, ["#2c2160"]],
];

const STATE_COPY: Record<DayPhase, string> = {
  dawn: "chồi non đang thức dậy",
  morning: "đang ra lá non",
  noon: "đang nở hoa",
  afternoon: "đang kết trái vàng",
  evening: "lá đang phát sáng, có đom đóm bay",
  night: "cây đang ngủ, búp hoa khép lại. Khuya rồi, đi ngủ thôi",
};

/** Point along the vine that climbs the window frame, t in [0, 1]. */
function vinePoint(t: number): { x: number; y: number; angle: number } {
  const left = 134;
  const arc = Math.PI * 96;
  const right = 94;
  const total = left + arc + right;
  const d = t * total;
  if (d <= left) return { x: 25, y: 250 - d, angle: 0 };
  if (d <= left + arc) {
    const a = Math.PI - ((d - left) / arc) * Math.PI;
    return { x: 120 + Math.cos(a) * 95, y: 116 - Math.sin(a) * 95, angle: 90 - (a * 180) / Math.PI };
  }
  return { x: 215, y: 116 + (d - left - arc), angle: 180 };
}

/**
 * Option C, "Cửa sổ trời": a small procedural tree under the real local sky.
 * Decorative but labelled: the SVG is role="img" with a Vietnamese state
 * description; the overlay button is the tap target.
 */
export function SkyWindowCompanion({
  now, growthDays = 0, seed = DEFAULT_COMPANION_SEED, vibe, size = 240, reacting = null,
  onTap, label, still = false, festival = "auto", welcomeBack = false, className = "",
}: CompanionProps) {
  const uid = useId().replace(/:/g, "");
  const rootRef = useRef<HTMLDivElement | null>(null);
  const canopyRef = useRef<SVGGElement | null>(null);
  const visible = usePageVisible();
  const at = useCompanionClock(now, visible);
  const stage = dayStage(at);
  const { motion, canAnimate } = useCompanionMotion({ rootRef, still, resting: stage.resting, visible });
  const { bursts, addBurst } = useBursts();
  const shared = useVibe();
  const activeVibe = vibe ?? shared.vibe;
  const roast = activeVibe === "roast";

  const level = growthLevel(growthDays);
  const h = stage.hour;
  const fest = resolveFestival(festival, at);
  const realMoon = moonPhase(at);
  // Trung Thu falls on lunar 10–16 (moon ≥ ~80% lit); the skin draws the Rằm moon full.
  const moon = fest === "trung-thu" ? { ...realMoon, illumination: Math.max(realMoon.illumination, 0.99), label: "Trăng rằm" } : realMoon;
  const tree = useMemo(
    () => buildTree(seed >>> 0, level, TREE_BASE, { height: TREE_HEIGHT[level], halfWidth: TREE_HALF_WIDTH[level] }),
    [seed, level],
  );

  const [skyTop, skyMid, skyLow] = sampleByHour(SKY_TABLE, h);
  const [leafFill, leafEdge, trunk, hill] = sampleByHour(PLANT_TABLE, h);
  const [sunColor] = sampleByHour(SUN_TABLE, h);
  const [cloudColor] = sampleByHour(CLOUD_TABLE, h);
  const night = nightness(h);
  const sleep = sleepiness(h);
  const glow = eveningGlow(h);
  const sun = arcPosition(h, 5.6, 18.6, { x0: 36, x1: 204, top: 50, horizon: 222 });
  const moonPos = arcPosition(h, 17.4, 30.4, { x0: 44, x1: 196, top: 58, horizon: 222 });
  const moonR = fest === "trung-thu" ? 19 : 11;
  const dayTime = !stage.resting;

  const bloom = fest === "tet" && dayTime
    ? 0.9
    : smoothstep(10.6, 12, h) * (1 - smoothstep(15.2, 16.8, h));
  const bud = h >= 12 ? smoothstep(20.4, 21.4, h) : h < 5 ? 1 : Math.max(1 - smoothstep(5, 7, h), smoothstep(9, 10.4, h) * (1 - bloom));
  const fruit = fest === "tet" ? 0 : smoothstep(14.4, 15.8, h) * (1 - smoothstep(19, 20, h));
  const fireflies = glow;
  const leafScale = (1 - 0.16 * sleep) * (level >= 2 ? 1.45 : 1.3);

  const canopyCenter = useMemo(() => {
    const xs = tree.tips.map((tip) => tip.x);
    const ys = tree.tips.map((tip) => tip.y);
    return {
      x: xs.reduce((a, b) => a + b, 0) / xs.length,
      y: ys.reduce((a, b) => a + b, 0) / ys.length,
      r: TREE_HALF_WIDTH[level] + 16,
    };
  }, [tree, level]);
  const canopyMass = useMemo(() => {
    const r = 6 + level * 1.7;
    const circles: Array<[number, number, number]> = tree.tips.map((tip) => [tip.x, tip.y - 1, r * (0.8 + hashRandom(seed, tip.id, 70) * 0.4)]);
    const maxDepth = Math.max(...tree.branches.map((b) => b.depth));
    tree.branches.filter((b) => b.depth === maxDepth && maxDepth >= 2).forEach((b) => circles.push([(b.x1 + b.x2) / 2, (b.y1 + b.y2) / 2, r * 0.85]));
    return circlesPath(circles);
  }, [tree, level, seed]);
  const topTip = useMemo(() => tree.tips.reduce((a, b) => (b.y < a.y ? b : a)), [tree]);
  const blossomTips = useMemo(() => tree.tips.filter((tip) => hashRandom(seed, tip.id, 60) > 0.4).slice(0, 10), [tree, seed]);
  const fruitTips = useMemo(() => tree.tips.filter((tip) => hashRandom(seed, tip.id, 61) > 0.55).slice(0, 6), [tree, seed]);
  const stars = useMemo(() => {
    const out: Array<{ x: number; y: number; r: number; twinkle: boolean; sparkle: boolean }> = [];
    for (let i = 0; out.length < 22 && i < 80; i += 1) {
      const x = 32 + hashRandom(seed, 900 + i, 0) * 176;
      const y = 28 + hashRandom(seed, 900 + i, 1) * 140;
      if (y < 116 && (x - 120) ** 2 + (y - 116) ** 2 > 86 ** 2) continue;
      const r = 0.5 + hashRandom(seed, 900 + i, 2) * 1.1;
      out.push({ x, y, r, twinkle: i % 3 === 0, sparkle: i % 7 === 3 });
    }
    return out;
  }, [seed]);
  const tetPetal = hashRandom(seed, 77) > 0.5 ? { petal: "#ffd23f", heart: "#ff8a00" } : { petal: "#ff9cc6", heart: "#fff0f6" };
  const flower = fest === "tet" ? tetPetal : { petal: "#fff1f7", heart: "#ffd23f" };
  const lantern = fest === "trung-thu" ? tree.tips.reduce((a, b) => (b.x > a.x ? b : a)) : null;

  const shadowAlpha = sun.up ? 0.18 + 0.1 * Math.sin(sun.t * Math.PI) : 0.12 * (1 - night);
  const shadowShift = sun.up ? (120 - sun.x) * 0.35 : 0;
  const vineReach = VINE_REACH[level];
  const vineLeaves = useMemo(() => {
    const out: Array<{ x: number; y: number; angle: number; t: number; flip: boolean }> = [];
    for (let t = 0.04; t < 1; t += 0.075) {
      const p = vinePoint(t);
      out.push({ ...p, t, flip: Math.round(t * 100) % 2 === 0 });
    }
    return out;
  }, []);

  const levelLabel = GROWTH_LEVEL_LABEL[level];
  const moonText = night > 0.5 ? ` ${moon.label} trên trời.` : "";
  const festText = fest === "tet" ? " Cây đang mặc áo Tết." : fest === "trung-thu" ? " Trăng Trung Thu, có đèn ông sao." : "";
  const giftText = welcomeBack && dayTime ? " Cây giữ cho bạn một chiếc lá mới." : "";
  const ariaLabel = `Cây trong cửa sổ trời, ${DAY_PHASE_LABEL[stage.phase]}, ${STATE_COPY[stage.phase]}. Cây đang là ${levelLabel}.${moonText}${festText}${giftText}`;

  const handleTap = useCallback((event: MouseEvent<HTMLButtonElement>) => {
    onTap?.();
    if (stage.resting) {
      // Night: a single soft sway, no sparkle and no reward (G6).
      if (canAnimate()) playAnimation(canopyRef.current, [{ transform: "rotate(0deg)" }, { transform: "rotate(0.6deg)" }, { transform: "rotate(0deg)" }], { duration: 900, easing: "ease-in-out" });
      return;
    }
    tapFeedback();
    const animate = canAnimate();
    // Still pose (reduced motion) still gets a brief, motionless sparkle as feedback.
    if (!animate && motion !== "still") return;
    const point = tapPoint(event, { width: W, height: H }, { x: canopyCenter.x, y: canopyCenter.y });
    addBurst(point.x, point.y);
    if (animate) playAnimation(canopyRef.current, [
      { transform: "rotate(0deg) translateX(0)" },
      { transform: "rotate(2.4deg) translateX(1px)" },
      { transform: "rotate(-1.8deg) translateX(-1px)" },
      { transform: "rotate(1deg)" },
      { transform: "rotate(-0.4deg)" },
      { transform: "rotate(0deg)" },
    ], { duration: 820, easing: "ease-out" });
  }, [addBurst, canAnimate, canopyCenter, motion, onTap, stage.resting]);

  const handlePointerMove = useCallback((event: PointerEvent<HTMLDivElement>) => {
    const node = rootRef.current;
    if (!node || event.pointerType === "touch" || !canAnimate()) return;
    const rect = node.getBoundingClientRect();
    node.style.setProperty("--lc-px", (((event.clientX - rect.left) / rect.width) * 2 - 1).toFixed(3));
    node.style.setProperty("--lc-py", (((event.clientY - rect.top) / rect.height) * 2 - 1).toFixed(3));
  }, [canAnimate]);

  const id = (name: string) => `${uid}-${name}`;
  const ref = (name: string) => `url(#${id(name)})`;
  const branchesByDepth = [0, 1, 2].map((depth) => tree.branches.filter((b) => (depth < 2 ? b.depth === depth : b.depth >= 2)));
  const branchWidth = (depth: number) => Math.max(1.4, (3.2 + level * 1.15) * 0.64 ** depth);

  return (
    <div
      ref={rootRef}
      className={`lc-companion lc-sky ${className}`.trim()}
      data-phase={stage.phase}
      data-cmotion={motion}
      data-vibe={activeVibe}
      data-festival={fest ?? undefined}
      data-reacting={reacting ?? undefined}
      data-level={level}
      onPointerMove={handlePointerMove}
      style={{ width: size, "--lc-canopy-x": `${canopyCenter.x}px`, "--lc-canopy-y": `${canopyCenter.y}px` } as CSSProperties}
    >
      <svg role="img" aria-label={ariaLabel} viewBox={`0 0 ${W} ${H}`} width="100%" focusable="false" className="lc-svg">
        <defs>
          <clipPath id={id("win")}><path d={WINDOW_PATH} /></clipPath>
          <linearGradient id={id("sky")} x1="0" y1="18" x2="0" y2="266" gradientUnits="userSpaceOnUse">
            <stop offset="0" style={{ stopColor: skyTop }} />
            <stop offset="0.56" style={{ stopColor: skyMid }} />
            <stop offset="0.9" style={{ stopColor: skyLow }} />
          </linearGradient>
          <radialGradient id={id("sunglow")}>
            <stop offset="0" stopColor={sunColor} stopOpacity="0.75" />
            <stop offset="1" stopColor={sunColor} stopOpacity="0" />
          </radialGradient>
          <radialGradient id={id("moonglow")}>
            <stop offset="0" stopColor="#fff4cf" stopOpacity={0.35 + moon.illumination * 0.35} />
            <stop offset="1" stopColor="#fff4cf" stopOpacity="0" />
          </radialGradient>
          <radialGradient id={id("lime")}>
            <stop offset="0" stopColor={BRAND.lime} stopOpacity="0.85" />
            <stop offset="1" stopColor={BRAND.lime} stopOpacity="0" />
          </radialGradient>
          <linearGradient id={id("glass")} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0.28" />
            <stop offset="0.45" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
          <radialGradient id={id("fruit")} cx="0.35" cy="0.35">
            <stop offset="0" stopColor="#fff2a8" />
            <stop offset="0.6" stopColor="#ffc23d" />
            <stop offset="1" stopColor="#e8892a" />
          </radialGradient>
        </defs>

        <ellipse cx="120" cy="272" rx="100" ry="7" fill={BRAND.violet} opacity="0.16" />

        <g clipPath={ref("win")}>
          <rect x="0" y="0" width={W} height={H} fill={ref("sky")} />

          <g className="lc-layer lc-layer--stars" opacity={night}>
            {night > 0.02 ? stars.map((star, i) => (star.sparkle
              ? <g key={i} transform={`translate(${star.x.toFixed(1)} ${star.y.toFixed(1)}) scale(${(star.r * 0.45).toFixed(2)})`}><path className="lc-twinkle" d={SPARKLE_PATH} fill="#fff9e9" style={{ animationDelay: `${(i % 5) * 0.7}s` }} /></g>
              : <circle key={i} className={star.twinkle ? "lc-twinkle" : undefined} cx={star.x.toFixed(1)} cy={star.y.toFixed(1)} r={star.r.toFixed(2)} fill="#fff9e9" style={star.twinkle ? { animationDelay: `${(i % 6) * 0.55}s` } : undefined} />)) : null}
          </g>

          {sun.up ? (
            <g className="lc-sun">
              <circle cx={sun.x} cy={sun.y} r="46" fill={ref("sunglow")} />
              <circle cx={sun.x} cy={sun.y} r="13" fill={sunColor} />
              {roast ? (
                <g className="lc-shades" transform={`translate(${sun.x} ${sun.y})`}>
                  <path d="M-10 -3h8.5a1 1 0 0 1 1 1.2l-.8 3.2a3 3 0 0 1-3 2.4h-2.6a3 3 0 0 1-3-2.4l-.9-3.2a1 1 0 0 1 .8-1.2ZM1.5 -3H10a1 1 0 0 1 .8 1.2l-.9 3.2a3 3 0 0 1-3 2.4H4.3a3 3 0 0 1-3-2.4l-.8-3.2a1 1 0 0 1 1-1.2Z" fill="#1d1238" />
                  <path d="M-2.5 6.5Q1 8.5 5 5.5" stroke="#1d1238" strokeWidth="1.3" fill="none" strokeLinecap="round" />
                </g>
              ) : null}
            </g>
          ) : null}

          {moonPos.up ? (
            <g className="lc-moon" transform={`translate(${moonPos.x.toFixed(1)} ${moonPos.y.toFixed(1)})`} opacity={Math.max(0.25, night)}>
              <circle r={moonR * (fest === "trung-thu" ? 3.2 : 2.6)} fill={ref("moonglow")} />
              <circle r={moonR} fill="#3a2a5c" opacity="0.55" />
              {moonLitPath(0, 0, moonR, moon) ? <path d={moonLitPath(0, 0, moonR, moon) ?? ""} fill="#fff4cf" /> : null}
            </g>
          ) : null}

          <g className="lc-layer lc-layer--clouds" opacity={0.92 - night * 0.6}>
            {[
              { y: 74, x: 52, s: 1, d: 46 },
              { y: 112, x: 168, s: 0.8, d: 58 },
              { y: 146, x: 82, s: 0.62, d: 38 },
            ].map((cloud, i) => (
              <g key={i} className="lc-cloud" style={{ animationDuration: `${cloud.d}s`, animationDelay: `${-i * 9}s` }}>
                <path
                  d={circlesPath([[cloud.x - 14 * cloud.s, cloud.y, 9 * cloud.s], [cloud.x, cloud.y - 6 * cloud.s, 12 * cloud.s], [cloud.x + 15 * cloud.s, cloud.y - 1 * cloud.s, 9 * cloud.s], [cloud.x + 4 * cloud.s, cloud.y + 3 * cloud.s, 9 * cloud.s]])}
                  fill={cloudColor}
                />
              </g>
            ))}
          </g>

          {sun.up && h > 6.4 && h < 17.6 ? (
            <g className="lc-birds" stroke="#3a2a5c" strokeWidth="1.3" fill="none" strokeLinecap="round" opacity="0.7">
              <path className="lc-wing" d="M0 0q3 -3 6 0q3 -3 6 0" />
              <path className="lc-wing" d="M16 -8q2.4 -2.4 4.8 0q2.4 -2.4 4.8 0" style={{ animationDelay: "-0.2s" }} />
            </g>
          ) : null}

          <path className="lc-layer lc-layer--far" d="M18 212C58 194 98 204 140 198S206 188 222 196V270H18Z" fill={mixColor(hill, skyLow, 0.5)} />
          <path d="M18 236C56 222 94 214 120 214S190 222 222 232V270H18Z" fill={hill} />
          {level >= 1 ? (
            <path d="M44 229l2 -6l1.5 6M58 224l2 -7l1.6 7M180 226l1.6 -6l2 6M194 230l1.5 -5l2 5" stroke={mixColor(hill, leafFill, 0.6)} strokeWidth="1.4" fill="none" strokeLinecap="round" />
          ) : null}
          {level >= 3 ? (
            <g>
              <circle cx="66" cy="226" r="2.2" fill={stage.resting ? "#6b5aa8" : "#ff9cc6"} />
              <circle cx="172" cy="225" r="2" fill={stage.resting ? "#6b5aa8" : "#fff1f7"} />
              <circle cx="186" cy="232" r="1.8" fill={stage.resting ? "#6b5aa8" : BRAND.lime} />
            </g>
          ) : null}
          {level >= 5 ? (
            <g transform="translate(78 232)">
              <path d="M-1.2 0V-5h2.4V0Z" fill="#fff1e0" />
              <path d="M-5 -4.5a5 4.2 0 0 1 10 0Z" fill={stage.resting ? "#7a5fb3" : BRAND.coral} />
              <circle cx="-1.6" cy="-6" r="0.9" fill="#fff9e9" />
            </g>
          ) : null}

          <ellipse
            cx={TREE_BASE.x + shadowShift}
            cy={TREE_BASE.y + 3}
            rx={18 + level * 6 + Math.abs(shadowShift) * 0.5}
            ry="4.5"
            fill="#1d1238"
            opacity={shadowAlpha}
          />

          <g className="lc-layer lc-layer--tree">
            <g className="lc-tree">
              <circle cx={canopyCenter.x} cy={canopyCenter.y} r={canopyCenter.r * 1.35} fill={ref("lime")} opacity={glow * 0.55} className="lc-canopy-glow" />
              <g fill="none" stroke={trunk} strokeLinecap="round">
                {branchesByDepth.map((list, depth) => list.length ? <path key={depth} d={branchPath(list)} strokeWidth={branchWidth(depth)} /> : null)}
              </g>
              <g ref={canopyRef} className="lc-canopy">
                {level >= 1 ? <path d={canopyMass} fill={mixColor(leafFill, trunk, 0.3)} opacity={0.92} /> : null}
                {[0, 1, 2].map((group) => (
                  <g key={group} className={`lc-leaves lc-leaves--${group}`} fill={leafFill} stroke={leafEdge} strokeWidth={glow > 0.3 ? 0.9 : 0.6}>
                    {tree.leaves.filter((leaf) => leaf.group === group).map((leaf) => (
                      <path key={leaf.id} d={LEAF_PATH} transform={`translate(${leaf.x.toFixed(1)} ${leaf.y.toFixed(1)}) rotate(${leaf.angle.toFixed(1)}) scale(${(leaf.scale * leafScale).toFixed(2)})`} />
                    ))}
                  </g>
                ))}
                {bloom > 0.05 ? blossomTips.map((tip) => (
                  <g key={tip.id} transform={`translate(${tip.x.toFixed(1)} ${(tip.y - 2).toFixed(1)}) scale(${(0.35 + 0.65 * bloom).toFixed(2)}) rotate(${(hashRandom(seed, tip.id, 62) * 72).toFixed(0)})`}>
                    <path d={petalsPath(5, 3.1, 2.7)} fill={flower.petal} opacity={0.4 + bloom * 0.6} />
                    <circle r="1.7" fill={flower.heart} />
                  </g>
                )) : null}
                {bud > 0.05 && bloom < 0.6 ? blossomTips.map((tip) => (
                  <path key={`b${tip.id}`} d="M0 1.6C-1.8 1.6 -2 -0.6 0 -3.4C2 -0.6 1.8 1.6 0 1.6Z" transform={`translate(${tip.x.toFixed(1)} ${(tip.y - 2).toFixed(1)}) scale(${(bud * 1.1).toFixed(2)})`} fill={stage.resting ? "#6a4bb5" : fest === "tet" ? tetPetal.petal : "#f7b8d6"} stroke={stage.resting ? BRAND.lime : "none"} strokeOpacity="0.5" strokeWidth="0.5" />
                )) : null}
                {fruit > 0.05 ? fruitTips.map((tip) => (
                  <circle key={`f${tip.id}`} cx={tip.x.toFixed(1)} cy={(tip.y + 3).toFixed(1)} r={(2.9 * fruit).toFixed(2)} fill={ref("fruit")} />
                )) : null}
                {lantern ? (
                  <g transform={`translate(${lantern.x.toFixed(1)} ${lantern.y.toFixed(1)})`}>
                    <g className="lc-lantern">
                      <path d="M0 0V9" stroke="#3a2a5c" strokeWidth="0.8" />
                      <circle cy="16" r="11" fill="#ffd23f" opacity={0.12 + glow * 0.3} />
                      <path d={STAR_LANTERN_PATH} transform="translate(0 16)" fill="#ff5a4a" stroke="#ffd23f" strokeWidth="0.9" />
                    </g>
                  </g>
                ) : null}
                {welcomeBack && dayTime ? (
                  <g transform={`translate(${topTip.x.toFixed(1)} ${topTip.y.toFixed(1)})`}>
                    <circle r="10" fill={ref("lime")} className="lc-gift-glow" />
                    <path d={LEAF_PATH} transform="rotate(12) scale(1.15)" fill={BRAND.lime} stroke={BRAND.violet} strokeWidth="0.8" />
                    <g transform="translate(8 -14) scale(0.55)"><path className="lc-twinkle" d={SPARKLE_PATH} fill="#fff9e9" /></g>
                  </g>
                ) : null}
              </g>
            </g>
          </g>

          {fireflies > 0.02 ? (
            <g className="lc-fireflies" opacity={fireflies}>
              {[0, 1, 2, 3, 4, 5].map((i) => {
                const x = canopyCenter.x + (hashRandom(seed, 700 + i, 0) - 0.5) * canopyCenter.r * 2.4;
                const y = canopyCenter.y + (hashRandom(seed, 700 + i, 1) - 0.3) * canopyCenter.r * 1.6;
                return (
                  <g key={i} transform={`translate(${x.toFixed(1)} ${y.toFixed(1)})`}>
                    <g className="lc-firefly" style={{ animationDelay: `${-i * 1.3}s`, animationDuration: `${5 + (i % 3)}s` }}>
                      <circle r="5" fill={ref("lime")} />
                      <circle r="1.2" fill="#f6ffbf" />
                    </g>
                  </g>
                );
              })}
            </g>
          ) : null}

          {bloom > 0.4 && dayTime ? (
            <g className="lc-petals" fill={flower.petal}>
              {[0, 1, 2].map((i) => (
                <g key={i} transform={`translate(${(canopyCenter.x + (i - 1) * 26).toFixed(1)} ${canopyCenter.y.toFixed(1)})`}>
                  <ellipse className="lc-petal" rx="1.9" ry="1.2" style={{ animationDelay: `${-i * 3.1}s` }} />
                </g>
              ))}
            </g>
          ) : null}

          {fest === "tet" && glow > 0.2 ? (
            <g className="lc-fireworks">
              {[{ x: 64, y: 70, c: "#ffd23f" }, { x: 178, y: 92, c: "#ff9cc6" }].map((fw, i) => (
                <g key={i} transform={`translate(${fw.x} ${fw.y})`}>
                  <g className="lc-firework" style={{ animationDelay: `${i * 1.7}s` }}>
                    <path d="M0 -6V-13M0 6V13M-6 0H-13M6 0H13M4.3 -4.3L9.2 -9.2M-4.3 4.3L-9.2 9.2M4.3 4.3L9.2 9.2M-4.3 -4.3L-9.2 -9.2" stroke={fw.c} strokeWidth="1.6" strokeLinecap="round" />
                  </g>
                </g>
              ))}
            </g>
          ) : null}

          {roast && dayTime ? (
            <g className="lc-roast-sparks">
              {[{ x: 50, y: 222 }, { x: 196, y: 220 }, { x: 160, y: 236 }].map((spark, i) => (
                <g key={i} transform={`translate(${spark.x} ${spark.y})`}>
                  <path className="lc-flame" d={FLAME_PATH} fill={i === 1 ? BRAND.lime : BRAND.coral} style={{ animationDelay: `${-i * 0.4}s` }} />
                </g>
              ))}
            </g>
          ) : null}

          {stage.resting ? (
            <g className="lc-zz" fill="#fff9e9" fontFamily="'Be Vietnam Pro', system-ui, sans-serif" fontWeight="700">
              <text className="lc-z" x={canopyCenter.x + canopyCenter.r * 0.6} y={canopyCenter.y - 6} fontSize="10">z</text>
              <text className="lc-z" x={canopyCenter.x + canopyCenter.r * 0.6 + 8} y={canopyCenter.y - 16} fontSize="7" style={{ animationDelay: "0.9s" }}>z</text>
            </g>
          ) : null}

          {bursts.map((burst) => (
            <g key={burst.id} transform={`translate(${burst.x.toFixed(1)} ${burst.y.toFixed(1)})`}>
              <g className="lc-burst">
                <path d={SPARKLE_PATH} transform="scale(1.4)" fill={roast ? BRAND.coral : BRAND.lime} />
                {[0, 1, 2, 3, 4].map((i) => (
                  <circle key={i} className="lc-burst-dot" r="1.4" fill={i % 2 ? "#fff9e9" : BRAND.lime} style={{ "--lc-dx": `${Math.cos((i / 5) * Math.PI * 2) * 16}px`, "--lc-dy": `${Math.sin((i / 5) * Math.PI * 2) * 16}px` } as CSSProperties} />
                ))}
              </g>
            </g>
          ))}

          {reacting === "happy" && dayTime ? (
            <g className="lc-react-happy">
              {[0, 1, 2].map((i) => (
                <g key={i} transform={`translate(${(canopyCenter.x + (i - 1) * canopyCenter.r * 0.8).toFixed(1)} ${(canopyCenter.y - canopyCenter.r * 0.5 + (i % 2) * 14).toFixed(1)}) scale(0.8)`}><path className="lc-twinkle" d={SPARKLE_PATH} fill={roast ? BRAND.coral : BRAND.lime} style={{ animationDelay: `${i * 0.3}s` }} /></g>
              ))}
            </g>
          ) : null}
          {reacting === "think" && dayTime ? (
            <g transform={`translate(${canopyCenter.x.toFixed(1)} ${canopyCenter.y.toFixed(1)})`}>
              <g className="lc-orbit" style={{ "--lc-orbit-r": `${canopyCenter.r}px` } as CSSProperties}>
                <circle cx={canopyCenter.r} r="5" fill={ref("lime")} />
                <circle cx={canopyCenter.r} r="1.6" fill="#f6ffbf" />
              </g>
            </g>
          ) : null}

          <rect x="0" y="0" width={W} height="170" fill={ref("glass")} pointerEvents="none" />
        </g>


        <path d={WINDOW_PATH} fill="none" stroke={BRAND.creamText} strokeWidth="9" />
        <path d={WINDOW_PATH} fill="none" stroke={roast ? BRAND.coral : BRAND.violet} strokeWidth="1.6" strokeOpacity="0.85" transform="translate(120 141) scale(0.955) translate(-120 -141)" />
        <path d={WINDOW_PATH} fill="none" stroke={BRAND.violet} strokeOpacity="0.22" strokeWidth="1" transform="translate(120 141) scale(1.045) translate(-120 -141)" />
        {vineReach > 0 ? (
          <g className="lc-vine">
            <path
              d="M25 250V116A95 95 0 0 1 215 116V210"
              pathLength={1}
              strokeDasharray={`${vineReach} 1`}
              stroke={mixColor(trunk, leafFill, 0.65)}
              strokeWidth="2.2"
              fill="none"
              strokeLinecap="round"
            />
            {vineLeaves.filter((leaf) => leaf.t < vineReach).map((leaf, i) => (
              <path key={i} d={LEAF_PATH} transform={`translate(${leaf.x.toFixed(1)} ${leaf.y.toFixed(1)}) rotate(${(leaf.angle + (leaf.flip ? 60 : -60)).toFixed(0)}) scale(0.8)`} fill={leafFill} stroke={leafEdge} strokeWidth="0.8" />
            ))}
          </g>
        ) : null}
        <rect x="12" y="262" width="216" height="11" rx="5.5" fill={BRAND.creamText} stroke={BRAND.violet} strokeOpacity="0.2" />
      </svg>
      <button
        type="button"
        className="lc-companion__hit"
        aria-label={label ?? "Chạm vào cây trong cửa sổ trời"}
        onClick={handleTap}
      />
    </div>
  );
}
