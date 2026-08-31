import { ShieldCheck, Trash } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { deleteGuest, getBirthProfile } from "../../shared/api/client";
import { signDetails } from "../../shared/astro/signs";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";

export function ProfilePage() {
  const navigate = useNavigate();
  const query = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal) });
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sign = query.data?.calculation.sign ?? query.data?.calculation.candidates[0];

  const remove = async () => {
    try {
      await deleteGuest();
      localStorage.removeItem("la-lanh-mood");
      localStorage.removeItem("la-lanh-saved-note");
      void navigate("/welcome", { replace: true });
    } catch { setError("Chưa xóa được lúc này. Thử lại khi có kết nối nhé."); }
  };

  return (
    <main className="app-page profile-page">
      <header className="section-header"><BrandMark /><h1>Mình</h1></header>
      <section className="profile-card"><span>{sign ? signDetails[sign].symbol : "✦"}</span><div><p className="eyebrow">Lá đang được giữ trên thiết bị này</p><h2>{sign ? `Mặt Trời ${signDetails[sign].label}` : "Lá Khai Sinh"}</h2><p>Phiên khách tự hết hạn sau tối đa 30 ngày không hoạt động.</p></div></section>
      <section className="settings-list"><article><ShieldCheck /><div><strong>Dữ liệu sinh đã mã hóa</strong><p>Không nằm trong cookie, URL hoặc local storage.</p></div></article><button className="danger-row" onClick={() => setConfirming(true)} type="button"><Trash /><span><strong>Xóa Lá và dữ liệu</strong><small>Không thể hoàn tác</small></span></button></section>
      {error ? <p className="inline-error">{error}</p> : null}
      {confirming ? <div className="modal-backdrop"><section aria-modal="true" className="privacy-sheet" role="dialog"><h2>Xóa chiếc Lá này?</h2><p>Phiên khách, consent và mọi snapshot trên server sẽ bị xóa. Note đã lưu trên thiết bị cũng biến mất.</p><button className="danger-button" onClick={() => void remove()} type="button">Xóa vĩnh viễn</button><button className="text-button" onClick={() => setConfirming(false)} type="button">Giữ lại</button></section></div> : null}
      <AppNav />
    </main>
  );
}
