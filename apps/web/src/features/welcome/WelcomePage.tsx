import { ArrowRight } from "@phosphor-icons/react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { BrandMark } from "../../shared/ui/BrandMark";
import { PrimaryButton } from "../../shared/ui/PrimaryButton";

const welcomeSlides = [
  {
    eyebrow: "Không phải horoscope chung chung",
    title: (
      <>
        Một lời nhắc <em>đúng lúc.</em>
      </>
    ),
    body: "Lá Lành đọc chuyển động thật của bầu trời và gửi bạn một note nhỏ mỗi ngày.",
    action: "Tiếp tục",
  },
  {
    eyebrow: "Bắt đầu thật nhẹ",
    title: (
      <>
        Chỉ cần ngày sinh. <em>Thế là đủ.</em>
      </>
    ),
    body: "Giờ và nơi sinh có thể thêm sau, khi bạn muốn lời nhắn chạm sâu hơn.",
    action: "Bắt đầu",
  },
] as const;

export function WelcomePage() {
  const navigate = useNavigate();
  const [slideIndex, setSlideIndex] = useState(0);
  const slide = welcomeSlides[slideIndex];
  const isLastSlide = slideIndex === welcomeSlides.length - 1;

  const advance = () => {
    if (isLastSlide) void navigate("/birth");
    else setSlideIndex((current) => current + 1);
  };

  return (
    <main className="welcome" aria-labelledby="welcome-title">
      <header className="welcome__header">
        <BrandMark />
        <span className="welcome__spark" aria-hidden="true">
          ✦
        </span>
      </header>

      <div className="celestial-collage" aria-hidden="true">
        <span className="celestial-collage__orbit" />
        <span className="celestial-collage__sun" />
        <span className="celestial-collage__moon" />
        <span className="celestial-collage__star">✦</span>
      </div>

      <section
        className="welcome__copy"
        aria-label={`Giới thiệu ${slideIndex + 1} trên ${welcomeSlides.length}`}
        aria-live="polite"
      >
        <p className="eyebrow">{slide.eyebrow}</p>
        <h1 id="welcome-title">{slide.title}</h1>
        <p>{slide.body}</p>
      </section>

      <footer className="welcome__footer">
        <div className="pagination" aria-label="Tiến độ giới thiệu">
          {welcomeSlides.map((item, index) => (
            <span
              className={index === slideIndex ? "pagination__dot pagination__dot--active" : "pagination__dot"}
              aria-label={`${index === slideIndex ? "Đang ở" : "Trang"} ${index + 1}: ${item.eyebrow}`}
              key={item.eyebrow}
            />
          ))}
        </div>
        <PrimaryButton onClick={advance}>
          <span>{slide.action}</span>
          <ArrowRight aria-hidden="true" size={21} weight="bold" />
        </PrimaryButton>
        {!isLastSlide ? (
          <button className="text-button" onClick={() => void navigate("/birth")} type="button">
            Bỏ qua giới thiệu
          </button>
        ) : (
          <button className="text-button" onClick={() => setSlideIndex(0)} type="button">
            Quay lại
          </button>
        )}
        <Link className="welcome__login-link" to="/existing-user">
          Mình đã có tài khoản
        </Link>
      </footer>
    </main>
  );
}
