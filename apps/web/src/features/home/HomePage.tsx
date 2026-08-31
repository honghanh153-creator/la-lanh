import { BookmarkSimple, Check, PaperPlaneTilt, Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getBirthProfile } from "../../shared/api/client";
import { signDetails } from "../../shared/astro/signs";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";

const moods = [
  ["Rực", "✹"], ["Chill", "≈"], ["Đuối", "▰"], ["Căng", "ϟ"], ["Lạc trôi", "◉"],
] as const;

export function HomePage() {
  const query = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal) });
  const [mood, setMood] = useState(() => localStorage.getItem("la-lanh-mood"));
  const [saved, setSaved] = useState(false);
  const sign = query.data?.calculation.sign ?? query.data?.calculation.candidates[0];
  const detail = sign ? signDetails[sign] : null;
  const dateLabel = useMemo(() => new Intl.DateTimeFormat("vi-VN", { weekday: "long", day: "numeric", month: "long" }).format(new Date()), []);

  const save = () => {
    if (!query.data || !detail) return;
    localStorage.setItem("la-lanh-saved-note", JSON.stringify({ snapshotId: query.data.snapshot_id, sign, note: detail.note, savedAt: new Date().toISOString() }));
    setSaved(true);
  };

  return (
    <main className="app-page home-page">
      <header className="home-header"><BrandMark /><Link aria-label="Trang cá nhân" className="profile-orb" to="/profile">✦</Link></header>
      <section className="home-greeting"><p>{dateLabel}</p><h1>Này bạn,</h1><span className="transit-pill"><Sparkle weight="fill" /> Lá Khai Sinh nhắc nhẹ</span></section>
      <article className="paper-panel daily-note">
        <p className="handwritten-kicker">vũ trụ để lại cho bạn một note</p>
        <h2>{detail?.note ?? "Một lời nhắc đang trên đường tới."}</h2>
        <p>Đọc chậm một nhịp. Không cần biến nó thành một việc phải hoàn thành.</p>
      </article>
      <section className="mood-check" aria-labelledby="mood-title"><h2 id="mood-title">Vibe hiện tại?</h2><div>{moods.map(([label, symbol]) => <button aria-pressed={mood === label} className={mood === label ? "mood-chip mood-chip--active" : "mood-chip"} key={label} onClick={() => { setMood(label); localStorage.setItem("la-lanh-mood", label); }} type="button"><span>{symbol}</span>{label}</button>)}</div></section>
      <div className="home-actions"><Link className="electric-button" to="/card"><PaperPlaneTilt /> Chia sẻ</Link><button className="outline-button" onClick={save} type="button">{saved ? <Check /> : <BookmarkSimple />}{saved ? "Đã lưu" : "Lưu lại"}</button></div>
      <aside className="unlock-note"><span aria-hidden="true">☾</span><div><strong>Còn một lớp chưa mở</strong><p>Thêm giờ sinh sau để bật mí Moon sign.</p></div><button disabled type="button">Sắp có</button></aside>
      <AppNav />
    </main>
  );
}
