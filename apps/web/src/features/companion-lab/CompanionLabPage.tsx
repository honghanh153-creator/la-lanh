import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from "react";

import type { AppVibe } from "../../shared/vibe/vibe";
import { AuraSproutCompanion } from "../../shared/ui/companion/AuraSproutCompanion";
import { SkyWindowCompanion } from "../../shared/ui/companion/SkyWindowCompanion";
import type { CompanionReaction } from "../../shared/ui/companion/companionTypes";
import {
  DAY_PHASE_LABEL, GROWTH_LEVEL_LABEL, GROWTH_RULE_COPY, createSeed, dayStage, growthLevel, type FestivalKey,
} from "../../shared/ui/companion/growth";
import "./companion-lab.css";

type FestivalChoice = "auto" | "none" | FestivalKey;

const HOUR_PRESETS = [7, 12, 17, 20, 23] as const;
const DAY_PRESETS = [0, 7, 30, 120] as const;

function atHour(hour: number, base = new Date()): Date {
  const safe = Math.min(23.99, Math.max(0, hour));
  const h = Math.floor(safe);
  const m = Math.round((safe - h) * 60);
  return new Date(base.getFullYear(), base.getMonth(), base.getDate(), h, m);
}

function formatHour(hour: number): string {
  const safe = Math.min(23.99, hour);
  const h = Math.floor(safe);
  const m = Math.round((safe - h) * 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function festivalProp(choice: FestivalChoice): FestivalKey | null | "auto" {
  return choice === "none" ? null : choice;
}

/** Reads the companion's live aria-label so QA can see what a screen reader hears. */
function SpokenLabel({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [text, setText] = useState("");
  useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    const read = () => setText(node.querySelector("svg[role='img']")?.getAttribute("aria-label") ?? "");
    read();
    const observer = new MutationObserver(read);
    observer.observe(node, { subtree: true, attributes: true, attributeFilter: ["aria-label"] });
    return () => observer.disconnect();
  }, []);
  return (
    <div ref={ref} className="clab__figure">
      <div className="clab__art">{children}</div>
      <p className="clab__spoken"><span>Trình đọc màn hình:</span> {text}</p>
    </div>
  );
}

/** QA page to compare companion prototypes B and C. Nothing here is stored. */
export function CompanionLabPage() {
  const uid = useId();
  const [hour, setHour] = useState(() => {
    const now = new Date();
    return now.getHours() + Math.round(now.getMinutes() / 15) / 4;
  });
  const [days, setDays] = useState(7);
  const [vibe, setVibe] = useState<AppVibe>("direct");
  const [seed, setSeed] = useState(() => createSeed());
  const [festival, setFestival] = useState<FestivalChoice>("auto");
  const [still, setStill] = useState(false);
  const [welcomeBack, setWelcomeBack] = useState(false);
  const [reacting, setReacting] = useState<CompanionReaction>(null);
  const [showGrid, setShowGrid] = useState(false);
  const [taps, setTaps] = useState({ aura: 0, sky: 0 });

  const now = useMemo(() => atHour(hour), [hour]);
  const stage = dayStage(now);
  const level = growthLevel(days);
  const common = { now, growthDays: days, seed, vibe, reacting, still, welcomeBack, festival: festivalProp(festival) };

  return (
    <main className="clab" data-vibe={vibe}>
      <header className="clab__head">
        <p className="clab__eyebrow">Phòng thử nội bộ</p>
        <h1>Bạn đồng hành lớn dần</h1>
        <p>So sánh <strong>B · Mầm Aura</strong> và <strong>C · Cửa sổ trời</strong> theo giờ, số ngày ghé, vibe và lễ hội. Trang này không lưu gì.</p>
      </header>

      <section className="clab__controls" aria-label="Bảng điều khiển">
        <div className="clab__field clab__field--wide">
          <div className="clab__labelrow"><label htmlFor={`${uid}-hour`}>Giờ trong ngày</label><output htmlFor={`${uid}-hour`}>{formatHour(hour)} · {DAY_PHASE_LABEL[stage.phase]}</output></div>
          <input id={`${uid}-hour`} type="range" min={0} max={24} step={0.25} value={hour} onChange={(event) => setHour(Number(event.target.value))} />
          <div className="clab__chips" role="group" aria-label="Giờ mẫu">
            {HOUR_PRESETS.map((preset) => (
              <button key={preset} type="button" aria-pressed={Math.floor(hour) === preset && hour % 1 === 0} onClick={() => setHour(preset)}>{preset}h</button>
            ))}
          </div>
        </div>

        <div className="clab__field clab__field--wide">
          <div className="clab__labelrow"><label htmlFor={`${uid}-days`}>Số ngày đã ghé</label><output htmlFor={`${uid}-days`}>{days} ngày · {GROWTH_LEVEL_LABEL[level]} (cấp {level})</output></div>
          <input id={`${uid}-days`} type="range" min={0} max={120} step={1} value={days} onChange={(event) => setDays(Number(event.target.value))} />
          <div className="clab__chips" role="group" aria-label="Số ngày mẫu">
            {DAY_PRESETS.map((preset) => (
              <button key={preset} type="button" aria-pressed={days === preset} onClick={() => setDays(preset)}>{preset} ngày</button>
            ))}
          </div>
        </div>

        <fieldset className="clab__field">
          <legend>Vibe</legend>
          <div className="clab__chips">
            {(["direct", "roast"] as const).map((value) => (
              <label key={value} className="clab__choice">
                <input type="radio" name={`${uid}-vibe`} checked={vibe === value} onChange={() => setVibe(value)} />
                {value === "direct" ? "Thẳng & dễ hiểu" : "Roast 🔥"}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset className="clab__field">
          <legend>Phản ứng</legend>
          <div className="clab__chips">
            {([[null, "Không"], ["happy", "Vui"], ["think", "Suy nghĩ"]] as const).map(([value, text]) => (
              <label key={text} className="clab__choice">
                <input type="radio" name={`${uid}-react`} checked={reacting === value} onChange={() => setReacting(value)} />
                {text}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="clab__field">
          <label htmlFor={`${uid}-festival`}>Lễ hội</label>
          <select id={`${uid}-festival`} value={festival} onChange={(event) => setFestival(event.target.value as FestivalChoice)}>
            <option value="auto">Tự động theo lịch</option>
            <option value="none">Không</option>
            <option value="tet">Xem trước Tết</option>
            <option value="trung-thu">Xem trước Trung Thu</option>
          </select>
        </div>

        <div className="clab__field">
          <span className="clab__label">Seed ngẫu nhiên</span>
          <div className="clab__chips">
            <code>{seed.toString(16).padStart(8, "0")}</code>
            <button type="button" onClick={() => setSeed(createSeed())}>Đổi seed</button>
          </div>
        </div>

        <div className="clab__field clab__toggles">
          <label className="clab__choice"><input type="checkbox" checked={still} onChange={(event) => setStill(event.target.checked)} /> Xem tĩnh (giảm chuyển động)</label>
          <label className="clab__choice"><input type="checkbox" checked={welcomeBack} onChange={(event) => setWelcomeBack(event.target.checked)} /> Quà chào bạn quay lại</label>
          <label className="clab__choice"><input type="checkbox" checked={showGrid} onChange={(event) => setShowGrid(event.target.checked)} /> Bảng xem nhanh</label>
        </div>
      </section>

      <section className="clab__stage" aria-label="So sánh hai phương án">
        <article className="clab__card">
          <h2>B · Mầm Aura <small>đã chạm {taps.aura} lần</small></h2>
          <SpokenLabel>
            <AuraSproutCompanion {...common} size={280} onTap={() => setTaps((t) => ({ ...t, aura: t.aura + 1 }))} />
          </SpokenLabel>
        </article>
        <article className="clab__card">
          <h2>C · Cửa sổ trời <small>đã chạm {taps.sky} lần</small></h2>
          <SpokenLabel>
            <SkyWindowCompanion {...common} size={260} onTap={() => setTaps((t) => ({ ...t, sky: t.sky + 1 }))} />
          </SpokenLabel>
        </article>
      </section>

      <p className="clab__rule">{GROWTH_RULE_COPY}</p>

      {showGrid ? (
        <section className="clab__grid" aria-label="Bảng xem nhanh theo giờ và số ngày">
          {(["aura", "sky"] as const).map((kind) => (
            <div key={kind} className="clab__matrix">
              <h2>{kind === "aura" ? "B · Mầm Aura" : "C · Cửa sổ trời"}</h2>
              <table>
                <thead>
                  <tr>
                    <th scope="col">Ngày \ Giờ</th>
                    {HOUR_PRESETS.map((preset) => <th key={preset} scope="col">{preset}h</th>)}
                  </tr>
                </thead>
                <tbody>
                  {DAY_PRESETS.map((d) => (
                    <tr key={d}>
                      <th scope="row">{d} ngày</th>
                      {HOUR_PRESETS.map((preset) => (
                        <td key={preset}>
                          {kind === "aura"
                            ? <AuraSproutCompanion now={atHour(preset)} growthDays={d} seed={seed} vibe={vibe} still festival={festivalProp(festival)} size={120} />
                            : <SkyWindowCompanion now={atHour(preset)} growthDays={d} seed={seed} vibe={vibe} still festival={festivalProp(festival)} size={110} />}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </section>
      ) : null}
    </main>
  );
}
