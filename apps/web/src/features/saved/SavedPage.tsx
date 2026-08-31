import { BookmarkSimple } from "@phosphor-icons/react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";

type SavedNote = { note: string; savedAt: string; sign: string };

export function SavedPage() {
  const [saved, setSaved] = useState<SavedNote | null>(() => {
    const value = localStorage.getItem("la-lanh-saved-note");
    if (!value) return null;
    try { return JSON.parse(value) as SavedNote; } catch { return null; }
  });
  return (
    <main className="app-page saved-page">
      <header className="section-header"><BrandMark /><h1>Đã lưu</h1></header>
      {saved ? <article className="paper-panel saved-note"><p className="eyebrow">Một note bạn không muốn bỏ lỡ</p><h2>{saved.note}</h2><p>{new Intl.DateTimeFormat("vi-VN", { dateStyle: "long" }).format(new Date(saved.savedAt))}</p><button className="detail-link" onClick={() => { localStorage.removeItem("la-lanh-saved-note"); setSaved(null); }} type="button">Bỏ lưu</button></article> : <section className="empty-state"><BookmarkSimple size={52} /><h2>Chưa có note nào nằm lại.</h2><p>Khi một lời nhắc chạm đúng lúc, lưu nó ở đây.</p><Link className="electric-button" to="/home">Về note hôm nay</Link></section>}
      <AppNav />
    </main>
  );
}
