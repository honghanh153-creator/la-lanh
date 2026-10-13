import { ArrowLeft, ArrowRight } from "@phosphor-icons/react";
import { useNavigate } from "react-router-dom";

import { NightSky } from "../../shared/ui/NightSky";

export function DemoPage() {
  const navigate = useNavigate();
  return (
    <main className="flow-page demo-page">
      <header className="flow-header uv-topbar"><button aria-label="Quay lại" className="icon-button uv-topbar__icon" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><span className="demo-badge uv-topbar__title">Bản xem thử · không cá nhân hóa</span><span aria-hidden="true" className="uv-topbar__spacer" /></header>
      <section className="paper-panel demo-note">
        <NightSky moon planet stars={4} />
        <p className="accent-kicker eyebrow">một note cho ngày bất kỳ</p>
        <h1>Đừng vội rep.</h1>
        <p>Cho cảm xúc đi trước lý trí một nhịp. Vài phút im lặng có thể nói đúng điều hơn một câu trả lời vội.</p>
      </section>
      <footer className="flow-actions">
        <button className="electric-button" onClick={() => void navigate("/consent")} type="button">Tạo Lá của riêng mình <ArrowRight /></button>
        <button className="text-button" onClick={() => void navigate("/privacy")} type="button">Xem lại quyền riêng tư</button>
        <button className="text-button" onClick={() => void navigate("/welcome")} type="button">Thoát bản xem thử</button>
      </footer>
    </main>
  );
}
