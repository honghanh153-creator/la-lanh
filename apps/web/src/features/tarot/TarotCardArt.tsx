import { useId, type ReactNode, type SVGProps } from "react";

import {
  PIP_LAYOUTS,
  crescentPath,
  raysPath,
  seededRandom,
  starPoints,
  tarotArtSpec,
  titleLines,
  wavePath,
  type CourtRank,
  type MajorKey,
  type TarotArtInput,
  type TarotArtSpec,
  type TarotPalette,
  type TarotSuit,
} from "./tarotArtSpec";
import "./tarot-art.css";

/*
 * Original procedural Tarot art: simple geometric line-art drawn in code.
 * No third-party imagery. 120×200 coordinate space, motif centred around (60, 92).
 */

type ArtProps = {
  card: TarotArtInput;
  /** Hide from assistive tech when the title is already visible next to the art. */
  decorative?: boolean;
  /** Omit the title band (for small thumbnails). */
  compact?: boolean;
  className?: string;
};

function useSvgId(prefix: string): (name: string) => string {
  const raw = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  return (name) => `${prefix}${raw}-${name}`;
}

function a11yProps(decorative: boolean | undefined, label: string): SVGProps<SVGSVGElement> {
  return decorative ? { "aria-hidden": true } : { role: "img", "aria-label": label };
}

function Sparkles({ seed, color, count = 9 }: { seed: string; color: string; count?: number }) {
  const random = seededRandom(seed);
  const dots: ReactNode[] = [];
  for (let index = 0; index < count; index += 1) {
    const x = 16 + random() * 88;
    const y = 32 + random() * 120;
    const size = 0.6 + random() * 1.1;
    dots.push(<circle cx={x.toFixed(1)} cy={y.toFixed(1)} key={index} r={size.toFixed(2)} />);
  }
  return <g fill={color} opacity="0.55">{dots}</g>;
}

function Frame({ palette, gid }: { palette: TarotPalette; gid: (name: string) => string }) {
  return <g fill="none" stroke={palette.accent}>
    <rect height="190" rx="7" strokeWidth="1.4" width="110" x="5" y="5" />
    <rect height="182" opacity="0.7" rx="5" strokeDasharray="0.1 3.2" strokeLinecap="round" strokeWidth="1.3" width="102" x="9" y="9" />
    <g fill={palette.accent} stroke="none">
      <polygon points="9,5.5 12.5,9 9,12.5 5.5,9" />
      <polygon points="111,5.5 114.5,9 111,12.5 107.5,9" />
      <polygon points="9,187.5 12.5,191 9,194.5 5.5,191" />
      <polygon points="111,187.5 114.5,191 111,194.5 107.5,191" />
    </g>
    <rect fill={`url(#${gid("foil")})`} height="200" rx="10" stroke="none" style={{ mixBlendMode: "screen" }} className="tarot-art__foil" width="120" />
  </g>;
}

function Defs({ palette, gid }: { palette: TarotPalette; gid: (name: string) => string }) {
  return <defs>
    <linearGradient id={gid("bg")} x1="0" x2="0.35" y1="0" y2="1">
      <stop offset="0" stopColor={palette.top} />
      <stop offset="1" stopColor={palette.bottom} />
    </linearGradient>
    <radialGradient cx="0.5" cy="0.44" id={gid("glow")} r="0.5">
      <stop offset="0" stopColor={palette.glow} stopOpacity="0.38" />
      <stop offset="1" stopColor={palette.glow} stopOpacity="0" />
    </radialGradient>
    <linearGradient id={gid("foil")} x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stopColor="#ff9ad5" stopOpacity="0.28" />
      <stop offset="0.3" stopColor="#9ff7ff" stopOpacity="0.05" />
      <stop offset="0.5" stopColor="#dfff4f" stopOpacity="0.26" />
      <stop offset="0.72" stopColor="#c9a8ff" stopOpacity="0.05" />
      <stop offset="1" stopColor="#ffd36e" stopOpacity="0.3" />
    </linearGradient>
  </defs>;
}

/* ---------- Suit glyphs (drawn at origin, ~24 units tall) ---------- */

function SuitGlyph({ suit, x, y, scale, palette }: { suit: TarotSuit; x: number; y: number; scale: number; palette: TarotPalette }) {
  const outline = { stroke: palette.band, strokeWidth: 1.4, strokeLinejoin: "round" as const, strokeLinecap: "round" as const };
  let body: ReactNode;
  if (suit === "cups") {
    body = <>
      <path d="M-9 -10H9Q9 2 0 3Q-9 2 -9 -10Z" fill={palette.ink} {...outline} />
      <path d="M-6 -7.5Q-5 -1 -1 0.5" fill="none" stroke={palette.glow} strokeLinecap="round" strokeWidth="1.3" />
      <path d="M0 3V8.5" fill="none" {...outline} strokeWidth="2.4" />
      <rect fill={palette.accent} height="3" rx="1.5" width="13" x="-6.5" y="8.5" {...outline} />
    </>;
  } else if (suit === "wands") {
    body = <>
      <path d="M-4 12L4 -12" fill="none" stroke={palette.band} strokeLinecap="round" strokeWidth="5.4" />
      <path d="M-4 12L4 -12" fill="none" stroke={palette.ink} strokeLinecap="round" strokeWidth="3" />
      <ellipse cx="5.5" cy="-4" fill={palette.glow} rx="2.2" ry="4.6" transform="rotate(42 5.5 -4)" {...outline} strokeWidth="0.9" />
      <ellipse cx="-4.5" cy="3" fill={palette.glow} rx="2" ry="4.2" transform="rotate(-42 -4.5 3)" {...outline} strokeWidth="0.9" />
      <circle cx="4.2" cy="-12" fill={palette.accent} r="1.8" {...outline} strokeWidth="0.9" />
    </>;
  } else if (suit === "swords") {
    body = <>
      <polygon fill={palette.ink} points="0,-13 2.6,-9 2.6,5 -2.6,5 -2.6,-9" {...outline} />
      <path d="M0 -9V3" stroke={palette.glow} strokeWidth="0.9" />
      <rect fill={palette.accent} height="2.6" rx="1.3" width="15" x="-7.5" y="5" {...outline} strokeWidth="1.1" />
      <path d="M0 7.6V10.6" fill="none" {...outline} strokeWidth="2.4" />
      <circle cx="0" cy="12" fill={palette.accent} r="1.8" {...outline} strokeWidth="1" />
    </>;
  } else {
    body = <>
      <circle cx="0" cy="0" fill={palette.accent} r="10.5" {...outline} />
      <circle cx="0" cy="0" fill="none" r="8.2" stroke={palette.band} strokeWidth="0.6" />
      <polygon fill={palette.ink} points={starPoints(0, 0, 7.4, 2.9, 5)} {...outline} strokeWidth="0.9" />
    </>;
  }
  return <g transform={`translate(${x} ${y}) scale(${scale})`}>{body}</g>;
}

/* ---------- Major arcana motifs ---------- */

function MajorMotif({ motif, palette }: { motif: MajorKey | null; palette: TarotPalette }) {
  const ink = palette.ink;
  const gold = palette.accent;
  const lime = palette.glow;
  const line = { fill: "none", stroke: ink, strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const goldLine = { ...line, stroke: gold };
  const limeLine = { ...line, stroke: lime };
  switch (motif) {
    case "fool":
      return <g>
        <ellipse cx="60" cy="94" opacity="0.45" rx="27" ry="36" {...goldLine} strokeWidth="1.2" />
        <circle cx="88" cy="48" fill={gold} r="7" />
        <path d={raysPath(88, 48, 10, 14.5, 10)} {...goldLine} strokeWidth="1.4" />
        <path d="M16 150H48L62 126H104" {...line} />
        <path d="M30 140Q48 66 86 104" {...limeLine} strokeDasharray="0.1 5.5" strokeWidth="2.8" />
        <polygon fill={lime} points={starPoints(52, 84, 7, 2.2, 4)} />
        <circle cx="86" cy="104" fill={ink} r="3" />
      </g>;
    case "magician":
      return <g>
        <path d="M60 52C52 42 40 42 40 52C40 62 52 62 60 52C68 42 80 42 80 52C80 62 68 62 60 52Z" {...limeLine} strokeWidth="2.2" />
        <path d={raysPath(60, 72, 7, 12, 8, 22.5)} {...goldLine} strokeWidth="1.2" />
        <path d="M60 72V122" {...line} strokeWidth="3" />
        <circle cx="60" cy="72" fill={gold} r="3.4" />
        <circle cx="60" cy="122" fill={gold} r="3" />
        <path d="M22 134H98" {...line} />
        <path d="M27 124H37Q37 130 32 130Q27 130 27 124Z" fill={gold} />
        <circle cx="50" cy="127" fill="none" r="3.4" stroke={gold} strokeWidth="1.4" />
        <path d="M70 120V131M67 128H73" {...goldLine} strokeWidth="1.4" />
        <path d="M86 131L91 120" {...goldLine} strokeWidth="1.6" />
      </g>;
    case "high-priestess":
      return <g>
        <rect fill={palette.band} height="96" rx="2" stroke={ink} strokeWidth="1.6" width="13" x="22" y="50" />
        <rect fill={ink} height="96" rx="2" width="13" x="85" y="50" />
        <path d="M20 50H37M83 50H100" {...goldLine} strokeWidth="2.6" />
        <path d="M44 132Q60 120 76 132" {...line} strokeWidth="1.4" opacity="0.6" />
        <path d="M44 140Q60 128 76 140" {...line} strokeWidth="1.4" opacity="0.4" />
        <path d={crescentPath(60, 84, 17)} fill={gold} />
        <path d="M60 106V120M53 113H67" {...limeLine} />
      </g>;
    case "empress": {
      const stars: ReactNode[] = [];
      for (let index = 0; index < 12; index += 1) {
        const angle = ((200 + (index * 140) / 11) * Math.PI) / 180;
        stars.push(<circle cx={(60 + 33 * Math.cos(angle)).toFixed(1)} cy={(82 + 33 * Math.sin(angle)).toFixed(1)} key={index} r="1.7" />);
      }
      return <g>
        <g fill={gold}>{stars}</g>
        <circle cx="60" cy="80" r="17" {...limeLine} strokeWidth="2.6" />
        <path d="M60 97V128M48 113H72" {...limeLine} strokeWidth="2.6" />
        <path d="M26 150Q28 128 36 112M94 150Q92 128 84 112" {...line} strokeWidth="1.6" />
        <g fill={gold}>
          <ellipse cx="30" cy="128" rx="2" ry="4.4" transform="rotate(-30 30 128)" />
          <ellipse cx="34" cy="117" rx="2" ry="4.4" transform="rotate(-20 34 117)" />
          <ellipse cx="90" cy="128" rx="2" ry="4.4" transform="rotate(30 90 128)" />
          <ellipse cx="86" cy="117" rx="2" ry="4.4" transform="rotate(20 86 117)" />
        </g>
      </g>;
    }
    case "emperor":
      return <g>
        <polyline points="16,150 38,110 50,124 70,92 84,112 104,150" {...goldLine} strokeWidth="1.4" opacity="0.7" />
        <rect height="56" rx="3" width="48" x="36" y="72" {...line} fill={palette.band} />
        <rect height="40" rx="2" width="32" x="44" y="80" {...goldLine} strokeWidth="1" />
        <path d="M36 72Q26 68 28 78Q30 86 38 82M84 72Q94 68 92 78Q90 86 82 82" {...line} strokeWidth="1.8" />
        <circle cx="60" cy="103" fill={gold} r="8" />
        <path d="M60 95V86M56 89H64" {...goldLine} strokeWidth="1.8" />
      </g>;
    case "hierophant":
      return <g>
        <path d="M60 42V122" {...line} strokeWidth="3" />
        <path d="M52 54H68M48 64H72M44 74H76" {...goldLine} strokeWidth="2.6" />
        <path d="M40 150L78 120M80 150L42 120" {...line} strokeWidth="2" />
        <circle cx="38" cy="118" fill="none" r="4.4" stroke={gold} strokeWidth="2" />
        <circle cx="82" cy="118" fill="none" r="4.4" stroke={gold} strokeWidth="2" />
        <path d="M72 145L76 149M48 145L44 149" {...limeLine} strokeWidth="2" />
      </g>;
    case "lovers":
      return <g>
        <circle cx="60" cy="50" fill={gold} r="8" />
        <path d={raysPath(60, 50, 11, 16, 12)} {...goldLine} strokeWidth="1.3" />
        <circle cx="49" cy="104" r="21" {...limeLine} strokeWidth="2.2" />
        <circle cx="71" cy="104" r="21" {...line} strokeWidth="2.2" />
        <path d="M60 116C50 108 52 98 57 99C59 99 60 101 60 103C60 101 61 99 63 99C68 98 70 108 60 116Z" fill={gold} />
      </g>;
    case "chariot":
      return <g>
        <path d="M26 64Q60 44 94 64" {...line} strokeWidth="1.8" />
        <g fill={gold}>
          <polygon points={starPoints(38, 62, 3.4, 1.2, 4)} />
          <polygon points={starPoints(60, 56, 3.4, 1.2, 4)} />
          <polygon points={starPoints(82, 62, 3.4, 1.2, 4)} />
        </g>
        <path d="M30 66V120M90 66V120" {...line} strokeWidth="1.4" opacity="0.6" />
        <rect height="34" rx="3" width="46" x="37" y="82" {...line} fill={palette.band} />
        <circle cx="60" cy="96" fill={lime} r="4" />
        <path d="M45 96Q52 89 56 95M75 96Q68 89 64 95" {...limeLine} strokeWidth="1.6" />
        <circle cx="40" cy="128" r="10" {...goldLine} fill={palette.band} />
        <circle cx="80" cy="128" fill={ink} r="10" stroke={gold} strokeWidth="2" />
        <path d={raysPath(40, 128, 0, 10, 6)} {...goldLine} strokeWidth="1" />
        <path d={raysPath(80, 128, 0, 10, 6)} stroke={palette.band} strokeWidth="1" />
      </g>;
    case "strength":
      return <g>
        <path d="M60 48C55 41 46 41 46 48C46 55 55 55 60 48C65 41 74 41 74 48C74 55 65 55 60 48Z" {...limeLine} strokeWidth="1.8" />
        <path d={raysPath(60, 100, 20, 31, 20)} {...goldLine} strokeWidth="4" />
        <circle cx="60" cy="100" fill={gold} r="19" />
        <circle cx="53" cy="97" fill={palette.band} r="2" />
        <circle cx="67" cy="97" fill={palette.band} r="2" />
        <path d="M54 106Q60 111 66 106" fill="none" stroke={palette.band} strokeLinecap="round" strokeWidth="1.8" />
        <path d="M24 146Q60 132 96 146" {...limeLine} strokeDasharray="0.1 5" strokeWidth="3" />
      </g>;
    case "hermit":
      return <g>
        <polyline points="16,152 50,114 62,126 80,102 104,152" {...goldLine} strokeWidth="1.4" opacity="0.7" />
        <path d="M42 56L30 152" {...line} strokeWidth="2.6" />
        <circle cx="80" cy="74" fill={lime} opacity="0.18" r="20" />
        <path d={raysPath(80, 74, 14, 20, 12, 15)} {...limeLine} strokeWidth="1" />
        <path d="M80 52V62" {...line} strokeWidth="1.4" />
        <rect height="24" rx="3" width="18" x="71" y="62" {...line} />
        <polygon fill={lime} points={starPoints(80, 74, 6.4, 3.4, 6)} />
      </g>;
    case "wheel-of-fortune":
      return <g>
        <circle cx="60" cy="94" r="34" {...line} />
        <circle cx="60" cy="94" r="26" {...goldLine} strokeWidth="1" />
        <path d={raysPath(60, 94, 8, 34, 8)} {...line} strokeWidth="1.6" />
        <circle cx="60" cy="94" fill={gold} r="8" />
        <g fill={lime}>
          <circle cx="81.2" cy="72.8" r="2.6" />
          <circle cx="38.8" cy="72.8" r="2.6" />
          <circle cx="81.2" cy="115.2" r="2.6" />
          <circle cx="38.8" cy="115.2" r="2.6" />
        </g>
        <g fill="none" stroke={gold} strokeWidth="1.4">
          <circle cx="24" cy="46" r="3.6" />
          <circle cx="96" cy="46" r="3.6" />
          <circle cx="24" cy="144" r="3.6" />
          <circle cx="96" cy="144" r="3.6" />
        </g>
      </g>;
    case "justice":
      return <g>
        <polygon fill={ink} points="60,40 63,46 63,116 57,116 57,46" />
        <path d="M50 118H70" {...goldLine} strokeWidth="3" />
        <path d="M60 120V132" {...line} strokeWidth="2.6" />
        <circle cx="60" cy="135" fill={gold} r="3" />
        <path d="M28 70H92" {...goldLine} strokeWidth="2" />
        <path d="M32 70L24 94M32 70L40 94M88 70L80 94M88 70L96 94" {...goldLine} strokeWidth="1" />
        <path d="M21 94Q32 104 43 94Z" fill={lime} />
        <path d="M77 94Q88 104 99 94Z" fill={lime} />
      </g>;
    case "hanged-man":
      return <g>
        <path d="M30 46H90" {...line} strokeWidth="3" />
        <path d="M34 46V150M86 46V150" {...line} strokeWidth="2" opacity="0.7" />
        <g fill={lime}>
          <ellipse cx="38" cy="78" rx="2" ry="4" transform="rotate(35 38 78)" />
          <ellipse cx="82" cy="112" rx="2" ry="4" transform="rotate(-35 82 112)" />
        </g>
        <path d="M60 46V60" {...goldLine} strokeWidth="1.4" />
        <path d="M60 60V96M60 66L49 78L60 86M60 96L51 103M60 96L69 103" {...line} strokeWidth="2.4" />
        <circle cx="60" cy="110" fill={lime} opacity="0.22" r="15" />
        <path d={raysPath(60, 110, 12, 16, 12)} {...limeLine} strokeWidth="1" />
        <circle cx="60" cy="110" fill={gold} r="7" />
      </g>;
    case "death":
      return <g>
        <g fill={palette.band} stroke={ink} strokeWidth="1.4">
          <rect height="28" width="12" x="20" y="92" />
          <rect height="28" width="12" x="88" y="92" />
        </g>
        <path d={raysPath(60, 120, 26, 36, 9, 0, [195, 345])} {...goldLine} strokeWidth="1.6" />
        <path d="M37 120A23 23 0 0 1 83 120Z" fill={gold} />
        <path d="M16 120H104" {...line} />
        <path d={wavePath(22, 132, 76, 2.6)} {...limeLine} strokeWidth="1.6" />
        <path d={wavePath(30, 142, 60, 2.2)} {...limeLine} strokeWidth="1.2" opacity="0.7" />
        <g fill={ink}>
          <circle cx="60" cy="49" r="5.4" />
          <circle cx="68.6" cy="55.2" r="5.4" />
          <circle cx="65.3" cy="65.3" r="5.4" />
          <circle cx="54.7" cy="65.3" r="5.4" />
          <circle cx="51.4" cy="55.2" r="5.4" />
        </g>
        <circle cx="60" cy="58" fill={lime} r="4" />
      </g>;
    case "temperance":
      return <g>
        <polygon fill={gold} opacity="0.85" points={starPoints(90, 46, 6, 2, 4)} />
        <g transform="translate(38 66) rotate(-28)">
          <path d="M-9 -10H9Q9 2 0 3Q-9 2 -9 -10Z" fill={ink} />
          <path d="M0 3V8M-5 9H5" {...line} strokeWidth="2" />
        </g>
        <g transform="translate(82 112) rotate(14)">
          <path d="M-9 -10H9Q9 2 0 3Q-9 2 -9 -10Z" fill={gold} />
          <path d="M0 3V8M-5 9H5" {...goldLine} strokeWidth="2" />
        </g>
        <path d="M45 60C62 60 78 80 80 100" {...limeLine} strokeWidth="3.2" />
        <rect height="20" width="20" x="50" y="128" {...line} strokeWidth="1.6" />
        <polygon fill={gold} points="60,131 68,145 52,145" />
      </g>;
    case "devil":
      return <g>
        <path d="M60 46C54 56 66 58 60 70C70 62 66 52 60 46Z" fill={gold} />
        <path d="M60 70V80" {...line} strokeWidth="2" />
        <path d="M28 88C44 70 76 106 92 88" {...limeLine} strokeWidth="2.4" />
        <rect height="40" rx="3" width="24" x="48" y="102" {...line} fill={palette.band} />
        <ellipse cx="38" cy="122" rx="10" ry="14" {...goldLine} strokeDasharray="30 8" />
        <ellipse cx="82" cy="122" rx="10" ry="14" {...goldLine} strokeDasharray="30 8" strokeDashoffset="20" />
        <path d="M18 150H102" {...line} strokeWidth="1.4" opacity="0.6" />
      </g>;
    case "tower":
      return <g>
        <path d="M28 34L46 54L39 56L56 74" {...limeLine} strokeWidth="2.6" />
        <rect height="86" width="28" x="46" y="64" {...line} fill={palette.band} />
        <path d="M46 64V58H52V64M58 64V58H64V64M70 64V58H74V64" {...line} strokeWidth="1.6" />
        <g fill={gold}>
          <rect height="9" rx="1" width="5" x="57.5" y="84" />
          <rect height="9" rx="1" width="5" x="57.5" y="110" />
        </g>
        <polygon fill={gold} points="80,56 83,47 86,53 90,45 92,57" transform="rotate(24 86 52)" />
        <g fill={gold}>
          <circle cx="34" cy="92" r="1.8" />
          <circle cx="28" cy="112" r="1.4" />
          <circle cx="88" cy="88" r="1.8" />
          <circle cx="94" cy="110" r="1.4" />
          <circle cx="84" cy="128" r="1.6" />
        </g>
        <path d="M20 150H100" {...line} />
      </g>;
    case "star": {
      const small: Array<[number, number]> = [[26, 50], [94, 50], [22, 86], [98, 86], [34, 112], [86, 112], [60, 40]];
      return <g>
        <circle cx="60" cy="76" fill={lime} opacity="0.22" r="26" />
        <polygon fill={gold} points={starPoints(60, 76, 24, 8, 8)} />
        <polygon fill={ink} points={starPoints(60, 76, 9, 4, 8, -67.5)} />
        <g fill={ink}>{small.map(([x, y]) => <polygon key={`${x}-${y}`} points={starPoints(x, y, 4, 1.4, 8)} />)}</g>
        <path d="M60 104V124" {...limeLine} strokeDasharray="0.1 4.5" strokeWidth="2.4" />
        <path d={wavePath(18, 132, 84, 3)} {...limeLine} strokeWidth="1.8" />
        <path d={wavePath(26, 143, 68, 2.4)} {...line} strokeWidth="1.3" opacity="0.7" />
      </g>;
    }
    case "moon":
      return <g>
        <circle cx="60" cy="58" r="17" {...line} strokeWidth="1" opacity="0.5" />
        <path d={crescentPath(60, 58, 17)} fill={gold} />
        <g fill={lime}>
          <path d="M44 84Q42 88 44 90Q46 88 44 84Z" />
          <path d="M60 86Q58 90 60 92Q62 90 60 86Z" />
          <path d="M76 84Q74 88 76 90Q78 88 76 84Z" />
        </g>
        <g fill={palette.band} stroke={ink} strokeWidth="1.4">
          <path d="M20 132V98L27 90L34 98V132Z" />
          <path d="M86 132V98L93 90L100 98V132Z" />
        </g>
        <path d="M60 140Q46 126 62 116T58 96" {...line} strokeDasharray="2 3.4" strokeWidth="1.6" />
        <ellipse cx="60" cy="146" rx="28" ry="6" {...limeLine} strokeWidth="1.6" />
        <path d={wavePath(40, 146, 40, 1.6)} {...limeLine} strokeWidth="1" />
      </g>;
    case "sun":
      return <g>
        <path d={raysPath(60, 88, 26, 42, 12)} {...goldLine} strokeWidth="2.6" />
        <path d={raysPath(60, 88, 26, 34, 12, 15)} {...limeLine} strokeWidth="2" />
        <circle cx="60" cy="88" fill={gold} r="22" />
        <circle cx="53" cy="85" fill={palette.band} r="2.2" />
        <circle cx="67" cy="85" fill={palette.band} r="2.2" />
        <path d="M52 94Q60 101 68 94" fill="none" stroke={palette.band} strokeLinecap="round" strokeWidth="2" />
        <g fill={lime}>
          <circle cx="32" cy="142" r="4.4" />
          <circle cx="60" cy="146" r="4.4" />
          <circle cx="88" cy="142" r="4.4" />
        </g>
        <g fill={palette.band}>
          <circle cx="32" cy="142" r="1.8" />
          <circle cx="60" cy="146" r="1.8" />
          <circle cx="88" cy="142" r="1.8" />
        </g>
      </g>;
    case "judgement":
      return <g>
        <path d="M26 50Q40 42 54 50" {...line} strokeWidth="1.4" opacity="0.6" />
        <path d="M66 46Q80 38 94 46" {...line} strokeWidth="1.4" opacity="0.6" />
        <path d="M26 52L70 66L80 58V82L70 74L26 60Z" fill={gold} />
        <path d={raysPath(80, 70, 6, 14, 5, 0, [-40, 40])} {...limeLine} strokeWidth="1.4" />
        <rect fill={ink} height="14" width="14" x="42" y="62" />
        <path d="M49 64V74M44 69H54" stroke={palette.band} strokeWidth="1.6" />
        {[34, 60, 86].map((x) => <g key={x}>
          <circle cx={x} cy="118" r="5" {...line} strokeWidth="1.8" />
          <path d={`M${x - 9} 106L${x} 126L${x + 9} 106`} {...limeLine} strokeWidth="1.8" />
          <rect fill={palette.band} height="12" rx="2" stroke={ink} strokeWidth="1.2" width="20" x={x - 10} y="134" />
        </g>)}
      </g>;
    case "world": {
      const leaves: ReactNode[] = [];
      for (let index = 0; index < 16; index += 1) {
        const angle = (index * Math.PI * 2) / 16;
        const x = 60 + 28 * Math.cos(angle);
        const y = 94 + 40 * Math.sin(angle);
        const tangent = (Math.atan2(40 * Math.cos(angle), -28 * Math.sin(angle)) * 180) / Math.PI;
        leaves.push(<ellipse cx={x.toFixed(1)} cy={y.toFixed(1)} key={index} rx="2.2" ry="5" transform={`rotate(${(tangent + 90).toFixed(0)} ${x.toFixed(1)} ${y.toFixed(1)})`} />);
      }
      return <g>
        <ellipse cx="60" cy="94" rx="28" ry="40" {...limeLine} strokeWidth="1.6" />
        <g fill={gold}>{leaves}</g>
        <path d="M54 50L66 58M66 50L54 58M54 130L66 138M66 130L54 138" {...line} strokeWidth="1.8" />
        <polygon fill={ink} points={starPoints(60, 94, 13, 3.6, 4)} />
        <circle cx="22" cy="44" fill="#ff8b6b" r="5" />
        <circle cx="98" cy="44" fill="#57d6cf" r="5" />
        <circle cx="22" cy="146" fill="#c3b1ff" r="5" />
        <circle cx="98" cy="146" fill={lime} r="5" />
      </g>;
    }
    default:
      return <g>
        <circle cx="60" cy="92" fill={lime} opacity="0.2" r="28" />
        <polygon fill={gold} points={starPoints(60, 92, 22, 7, 8)} />
      </g>;
  }
}

/* ---------- Minor arcana motifs ---------- */

function CourtMotif({ court, suit, palette }: { court: CourtRank; suit: TarotSuit; palette: TarotPalette }) {
  const outline = { stroke: palette.band, strokeWidth: 1.4, strokeLinejoin: "round" as const };
  const dots = { page: 1, knight: 2, queen: 3, king: 4 }[court];
  let crown: ReactNode;
  if (court === "page") {
    crown = <>
      <ellipse cx="60" cy="62" fill="none" rx="15" ry="4.6" stroke={palette.accent} strokeWidth="2.6" />
      <circle cx="60" cy="57.6" fill={palette.glow} r="3" {...outline} strokeWidth="1" />
    </>;
  } else if (court === "knight") {
    crown = <>
      <path d="M42 66L60 50L78 66" fill="none" stroke={palette.accent} strokeLinecap="round" strokeLinejoin="round" strokeWidth="3.4" />
      <path d="M47 74L60 62L73 74" fill="none" stroke={palette.glow} strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.4" />
      <path d="M18 98H32M14 106H30M18 114H32" fill="none" stroke={palette.ink} strokeLinecap="round" strokeWidth="1.8" opacity="0.8" />
    </>;
  } else if (court === "queen") {
    crown = <>
      <path d="M43 70V55Q48 62 52 52Q56 62 60 47Q64 62 68 52Q72 62 77 55V70Z" fill={palette.accent} {...outline} />
      <g fill={palette.glow} {...outline} strokeWidth="0.9">
        <circle cx="52" cy="51" r="2" />
        <circle cx="60" cy="46" r="2.2" />
        <circle cx="68" cy="51" r="2" />
      </g>
    </>;
  } else {
    crown = <>
      <polygon fill={palette.accent} points="41,72 41,56 48,63 54,50 60,61 66,50 72,63 79,56 79,72" {...outline} />
      <path d="M60 50V40M55 44.5H65" fill="none" stroke={palette.accent} strokeLinecap="round" strokeWidth="2.4" />
      <rect fill={palette.band} height="4" opacity="0.6" width="38" x="41" y="66" />
    </>;
  }
  return <g>
    <rect fill={palette.band} height="52" opacity="0.32" rx="26" width="92" x="14" y="80" />
    <rect fill="none" height="44" opacity="0.6" rx="22" stroke={palette.accent} strokeWidth="0.8" width="84" x="18" y="84" />
    {crown}
    <SuitGlyph palette={palette} scale={1.7} suit={suit} x={60} y={106} />
    <g fill={palette.accent}>
      {Array.from({ length: dots }, (_, index) => (
        <polygon key={index} points={starPoints(60 + (index - (dots - 1) / 2) * 9, 146, 3.2, 1.2, 4)} />
      ))}
    </g>
  </g>;
}

function MinorMotif({ spec }: { spec: Extract<TarotArtSpec, { kind: "minor" }> }) {
  const { palette, suit } = spec;
  if (spec.court) return <CourtMotif court={spec.court} palette={palette} suit={suit} />;
  if (spec.pips && PIP_LAYOUTS[spec.pips]) {
    const layout = PIP_LAYOUTS[spec.pips];
    const scale = spec.pips <= 3 ? 1.2 : spec.pips <= 6 ? 1 : 0.82;
    return <g>
      {layout.map(([x, y], index) => <SuitGlyph key={index} palette={palette} scale={scale} suit={suit} x={x} y={y} />)}
    </g>;
  }
  // Ace: one big radiant glyph.
  return <g>
    <circle cx="60" cy="92" fill={palette.glow} opacity="0.2" r="34" />
    <path d={raysPath(60, 92, 32, 42, 16)} fill="none" stroke={palette.accent} strokeLinecap="round" strokeWidth="1.6" />
    <g fill={palette.ink}>
      <polygon points={starPoints(28, 56, 4, 1.3, 4)} />
      <polygon points={starPoints(92, 60, 3.4, 1.1, 4)} />
      <polygon points={starPoints(30, 132, 3.2, 1.1, 4)} />
      <polygon points={starPoints(90, 128, 4, 1.3, 4)} />
    </g>
    <SuitGlyph palette={palette} scale={2.5} suit={suit} x={60} y={92} />
  </g>;
}

/* ---------- Public components ---------- */

export function TarotCardArt({ card, decorative, compact, className }: ArtProps) {
  const gid = useSvgId("tca");
  const spec = tarotArtSpec(card);
  const { palette } = spec;
  const lines = titleLines(card.title_vi);
  const length = card.title_vi.length;
  const fontSize = lines.length > 1 ? 9.8 : length > 12 ? 9.4 : length > 9 ? 10.5 : 12;
  const kindClass = spec.kind === "major" ? "tarot-art--major" : `tarot-art--${spec.suit}`;
  return <svg
    {...a11yProps(decorative, card.title_vi)}
    className={["tarot-art", kindClass, className].filter(Boolean).join(" ")}
    data-art={spec.signature}
    focusable="false"
    viewBox="0 0 120 200"
    xmlns="http://www.w3.org/2000/svg"
  >
    <Defs gid={gid} palette={palette} />
    <rect fill={`url(#${gid("bg")})`} height="200" rx="10" width="120" />
    <rect fill={`url(#${gid("glow")})`} height="200" rx="10" width="120" />
    <Sparkles color={palette.ink} seed={card.id} />
    {spec.kind === "major" ? <MajorMotif motif={spec.key} palette={palette} /> : <MinorMotif spec={spec} />}
    {spec.numeral ? <g>
      <path d="M38 22H48M72 22H82" stroke={palette.accent} strokeLinecap="round" strokeWidth="1" />
      <text fill={palette.accent} fontSize="10" fontWeight="800" letterSpacing="1" textAnchor="middle" x="60" y="25.5">{spec.numeral}</text>
    </g> : <polygon fill={palette.accent} points={starPoints(60, 22, 4, 1.4, 4)} />}
    {compact ? null : <g>
      <rect fill={palette.band} height="30" opacity="0.86" rx="15" width="96" x="12" y="158" />
      <rect fill="none" height="26" opacity="0.7" rx="13" stroke={palette.accent} strokeWidth="0.7" width="92" x="14" y="160" />
      <text fill={palette.ink} fontSize={fontSize} fontWeight="800" textAnchor="middle" x="60" y={lines.length > 1 ? 170.5 : 176.5}>
        {lines.length > 1 ? lines.map((text, index) => <tspan dy={index === 0 ? 0 : 10} key={text} x="60">{text}</tspan>) : lines[0]}
      </text>
    </g>}
    <Frame gid={gid} palette={palette} />
  </svg>;
}

export function TarotCardBack({ className, label }: { className?: string; label?: string }) {
  const gid = useSvgId("tcb");
  const lime = "#dfff4f";
  const cream = "#fff9e9";
  const gold = "#ffd36e";
  return <svg
    {...a11yProps(!label, label ?? "")}
    className={["tarot-art", "tarot-art--back", className].filter(Boolean).join(" ")}
    focusable="false"
    viewBox="0 0 120 200"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <linearGradient id={gid("bg")} x1="0" x2="0.4" y1="0" y2="1">
        <stop offset="0" stopColor="#5b30a8" />
        <stop offset="1" stopColor="#22104a" />
      </linearGradient>
      <linearGradient id={gid("foil")} x1="0" x2="1" y1="0" y2="1">
        <stop offset="0" stopColor="#ff9ad5" stopOpacity="0.22" />
        <stop offset="0.45" stopColor="#9ff7ff" stopOpacity="0.04" />
        <stop offset="0.6" stopColor="#dfff4f" stopOpacity="0.22" />
        <stop offset="1" stopColor="#c9a8ff" stopOpacity="0.12" />
      </linearGradient>
    </defs>
    <rect fill={`url(#${gid("bg")})`} height="200" rx="10" width="120" />
    <rect fill="none" height="190" rx="7" stroke={lime} strokeWidth="1.6" width="110" x="5" y="5" />
    <rect fill="none" height="176" opacity="0.55" rx="4" stroke={cream} strokeDasharray="0.1 4" strokeLinecap="round" strokeWidth="1.4" width="96" x="12" y="12" />
    <circle cx="60" cy="100" fill={lime} opacity="0.14" r="40" />
    <circle cx="60" cy="100" fill="none" r="34" stroke={cream} strokeDasharray="0.1 6.2" strokeLinecap="round" strokeWidth="2" opacity="0.8" />
    <circle cx="60" cy="100" fill="none" r="25" stroke={lime} strokeWidth="1.6" />
    <polygon fill={lime} points={starPoints(60, 100, 18, 6, 8)} />
    <circle cx="60" cy="100" fill="#22104a" r="4.4" />
    <path d={crescentPath(28, 100, 7)} fill={gold} />
    <path d={crescentPath(92, 100, 7)} fill={gold} transform="rotate(180 92 100)" />
    <g fill={lime}>
      <polygon points={starPoints(60, 40, 6, 1.8, 4)} />
      <polygon points={starPoints(60, 160, 6, 1.8, 4)} />
    </g>
    <g fill={cream} opacity="0.75">
      <circle cx="24" cy="30" r="1.2" />
      <circle cx="96" cy="34" r="1" />
      <circle cx="26" cy="168" r="1" />
      <circle cx="94" cy="170" r="1.2" />
    </g>
    <rect className="tarot-art__foil" fill={`url(#${gid("foil")})`} height="200" rx="10" style={{ mixBlendMode: "screen" }} width="120" />
  </svg>;
}
