import "./night-sky.css";

type NightSkyProps = {
  /** Moon half outside the top-right corner, with a soft glow. */
  moon?: boolean;
  /** Only the moon glow, for cards whose moon is an interactive control. */
  glow?: boolean;
  /** Textured planet with a ring, low in the bottom-left corner. */
  planet?: boolean;
  /** Number of twinkling stars (0–6). */
  stars?: number;
  /** Blurred nebula blobs behind the content. */
  nebula?: boolean;
  /** Faint orbit lines and one shooting star. */
  orbits?: boolean;
  /** Dim the moon (empty and error states). */
  dim?: boolean;
  className?: string;
};

const STAR_POSITIONS = [
  { left: "49%", top: 22, size: 3 },
  { left: "75%", top: 196, size: 2 },
  { left: "40%", top: 168, size: 2 },
  { left: "64%", top: 44, size: 2 },
  { left: "91%", top: 150, size: 3 },
  { left: "7%", top: 14, size: 2 },
] as const;

const SPARKLE_PATH = "M12 2c.6 4.8 2.5 7.6 8 10c-5.5 2.4-7.4 5.2-8 10c-.6-4.8-2.5-7.6-8-10c5.5-2.4 7.4-5.2 8-10z";

/**
 * Decorative layers of a night card: nebula, stars, planet and moon. Purely
 * visual (aria-hidden); every animation stops under reduced motion and when
 * the user pauses motion on Home or in the app.
 */
export function NightSky({
  moon = false,
  glow = false,
  planet = false,
  stars = 6,
  nebula = true,
  orbits = false,
  dim = false,
  className = "",
}: NightSkyProps) {
  const count = Math.max(0, Math.min(stars, STAR_POSITIONS.length));
  return (
    <div aria-hidden="true" className={`night-sky${dim ? " night-sky--dim" : ""} ${className}`.trim()}>
      {nebula ? <>
        <span className="night-sky__nebula night-sky__nebula--1" />
        <span className="night-sky__nebula night-sky__nebula--2" />
        <span className="night-sky__nebula night-sky__nebula--3" />
      </> : null}
      {orbits ? (
        <svg className="night-sky__orbits" preserveAspectRatio="xMidYMid slice" viewBox="0 0 350 350">
          <ellipse cx="300" cy="30" fill="none" rx="270" ry="120" stroke="#fff" strokeOpacity="0.07" transform="rotate(-12 300 30)" />
          <ellipse cx="300" cy="30" fill="none" rx="335" ry="172" stroke="#fff" strokeDasharray="2 6" strokeOpacity="0.05" transform="rotate(-12 300 30)" />
        </svg>
      ) : null}
      {STAR_POSITIONS.slice(0, count).map((star, index) => (
        <span
          className="night-sky__star"
          key={index}
          style={{ left: star.left, top: star.top, width: star.size, height: star.size, animationDelay: `${-0.6 * index}s` }}
        />
      ))}
      {count > 2 ? (
        <svg className="night-sky__sparkle" viewBox="0 0 24 24"><path d={SPARKLE_PATH} /></svg>
      ) : null}
      {orbits ? <span className="night-sky__shoot" /> : null}
      {planet ? (
        <span className="night-sky__planet">
          <svg className="night-sky__ring night-sky__ring--back" viewBox="0 0 420 240">
            <g transform="rotate(-14 210 120)"><ellipse cx="210" cy="120" fill="none" rx="205" ry="40" stroke="#dcd3ff" strokeOpacity="0.2" strokeWidth="1.2" /></g>
          </svg>
          <span className="night-sky__planet-body"><span className="night-sky__planet-skin" /></span>
          <svg className="night-sky__ring" viewBox="0 0 420 240">
            <g fill="none" transform="rotate(-14 210 120)">
              <path d="M5 120a205 40 0 0 0 410 0" stroke="#dcd3ff" strokeOpacity="0.38" strokeWidth="1.6" />
              <path d="M-14 120a224 46 0 0 0 448 0" stroke="#dcd3ff" strokeOpacity="0.16" strokeWidth="0.9" />
            </g>
          </svg>
        </span>
      ) : null}
      {moon || glow ? <span className="night-sky__moon-glow" /> : null}
      {moon ? <img alt="" className="night-sky__moon" src="/assets/ultraviolet/moon.webp" /> : null}
    </div>
  );
}
