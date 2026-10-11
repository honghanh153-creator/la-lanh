import { BookmarkSimple, MoonStars, X } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useContext, useState } from "react";
import { Link } from "react-router-dom";

import { listSavedNotes } from "../../shared/api/client";
import { ThemeContext } from "../../shared/theme/themeContext";

const NIGHT_DISMISS_KEY = "la-lanh-night-nudge-dismissed-v1";

function localDate(at: Date): string {
  return `${at.getFullYear()}-${String(at.getMonth() + 1).padStart(2, "0")}-${String(at.getDate()).padStart(2, "0")}`;
}

/** After 21:00 on a light theme, Lá offers the dark "night" look once a night. */
export function NightNudge({ now = new Date() }: { now?: Date }) {
  const theme = useContext(ThemeContext);
  const hour = now.getHours();
  const night = hour >= 21 || hour < 5;
  const key = localDate(hour < 5 ? new Date(now.getTime() - 6 * 3_600_000) : now);
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem(NIGHT_DISMISS_KEY) === key; } catch { return false; }
  });
  if (!theme || theme.theme === "dark" || !night || dismissed) return null;
  const dismiss = () => {
    setDismissed(true);
    // Stores only tonight's date so the offer does not repeat.
    try { localStorage.setItem(NIGHT_DISMISS_KEY, key); } catch { /* Storage may be unavailable. */ }
  };
  return (
    <aside aria-label="Gợi ý giao diện ban đêm" className="home-night-nudge">
      <MoonStars aria-hidden="true" weight="duotone" />
      <p>Khuya rồi. Bật nền tối cho dịu mắt nhé?</p>
      <button className="home-night-nudge__on" onClick={() => { theme.setTheme("dark"); dismiss(); }} type="button">Bật nền tối</button>
      <button aria-label="Để sau" className="home-night-nudge__close" onClick={dismiss} type="button"><X aria-hidden="true" /></button>
    </aside>
  );
}

/**
 * Sunday: a short look back at notes the user chose to save this week. Built
 * only from the user's own saved notes; nothing is compared with anyone else.
 */
export function WeekRecap({ now = new Date() }: { now?: Date }) {
  const sunday = now.getDay() === 0;
  const saved = useQuery({
    queryKey: ["saved-notes"],
    queryFn: ({ signal }) => listSavedNotes(signal),
    enabled: sunday,
    retry: false,
  });
  if (!sunday || !saved.data) return null;
  const weekAgo = now.getTime() - 7 * 86_400_000;
  const thisWeek = saved.data.filter((item) => Date.parse(item.saved_at) >= weekAgo);
  // Nothing saved this week: stay quiet instead of adding an empty block.
  if (!thisWeek.length) return null;
  return (
    <section aria-labelledby="home-week-recap-title" className="home-week-recap">
      <div>
        <p className="home-week-recap__eyebrow">Chủ nhật · nhìn lại tuần</p>
        <h2 id="home-week-recap-title">Tuần này bạn giữ lại {thisWeek.length} note.</h2>
        <p>Đọc lại một note bạn đã lưu, xem điều gì vẫn còn đúng sau vài ngày.</p>
        <Link className="home-week-recap__cta" to="/saved"><BookmarkSimple aria-hidden="true" /> Mở note đã lưu</Link>
      </div>
    </section>
  );
}
