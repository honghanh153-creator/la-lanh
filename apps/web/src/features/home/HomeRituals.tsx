import { ArrowRight, X } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

import { type NightNudgeState, useNightNudge, useWeekRecap } from "./homeRitualState";

export function NightNudgeNotice({ enable, dismiss }: NightNudgeState) {
  return (
    <aside aria-label="Gợi ý giao diện ban đêm" className="home-la-notice home-night-nudge">
      <p className="home-la-notice__title">Khuya rồi. Bật nền tối cho dịu mắt nhé?</p>
      <button className="home-la-notice__cta home-night-nudge__on" onClick={enable} type="button">Bật nền tối</button>
      <button aria-label="Để sau" className="home-la-notice__close home-night-nudge__close" onClick={dismiss} type="button"><X aria-hidden="true" /></button>
    </aside>
  );
}

export function NightNudge({ now = new Date() }: { now?: Date }) {
  const nudge = useNightNudge(now);
  return nudge ? <NightNudgeNotice {...nudge} /> : null;
}

export function WeekRecapNotice({ count, onDismiss }: { count: number; onDismiss?: () => void }) {
  return (
    <section aria-labelledby="home-week-recap-title" className="home-la-notice home-week-recap">
      <p className="home-la-notice__eyebrow home-week-recap__eyebrow">Chủ nhật · nhìn lại tuần</p>
      <h2 className="home-la-notice__title" id="home-week-recap-title">Tuần này bạn giữ lại {count} note.</h2>
      <p className="home-la-notice__body">Đọc lại một note bạn đã lưu, xem điều gì vẫn còn đúng sau vài ngày.</p>
      <Link className="home-la-notice__cta home-week-recap__cta" to="/saved">Mở note đã lưu <ArrowRight aria-hidden="true" /></Link>
      {onDismiss ? <button aria-label="Để sau" className="home-la-notice__close" onClick={onDismiss} type="button"><X aria-hidden="true" /></button> : null}
    </section>
  );
}

export function WeekRecap({ now = new Date() }: { now?: Date }) {
  const count = useWeekRecap(now);
  return count ? <WeekRecapNotice count={count} /> : null;
}
