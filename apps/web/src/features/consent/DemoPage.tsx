import { ArrowLeft, ArrowRight } from "@phosphor-icons/react";
import { useNavigate } from "react-router-dom";

import { BrandMark } from "../../shared/ui/BrandMark";

export function DemoPage() {
  const navigate = useNavigate();
  return (
    <main className="flow-page demo-page">
      <header className="flow-header"><button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><BrandMark /><span /></header>
      <section className="paper-panel demo-note">
        <span className="demo-badge">Bản xem thử · không cá nhân hóa</span>
        <p className="accent-kicker">một note cho ngày bất kỳ</p>
        <h1>Đừng vội rep.</h1>
        <p>Cho cảm xúc đi trước lý trí một nhịp. Vài phút im lặng có thể nói đúng điều hơn một câu trả lời vội.</p>
      </section>
      <footer className="flow-actions">
        <button className="electric-button" onClick={() => void navigate("/consent")} type="button">Tạo Lá của riêng mình <ArrowRight /></button>
        <button className="text-button" onClick={() => void navigate("/consent")} type="button">Xem lại quyền riêng tư</button>
        <button className="text-button" onClick={() => void navigate("/welcome")} type="button">Thoát bản xem thử</button>
      </footer>
    </main>
  );
}
