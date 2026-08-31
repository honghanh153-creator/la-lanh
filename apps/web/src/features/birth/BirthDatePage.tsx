import { ArrowLeft, ArrowRight, Planet, ShieldCheck } from "@phosphor-icons/react";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { createBirthProfile } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";

function validDate(day: string, month: string, year: string): string | null {
  if (!/^\d{1,2}$/.test(day) || !/^\d{1,2}$/.test(month) || !/^\d{4}$/.test(year)) {
    return null;
  }
  const numericDay = Number(day);
  const numericMonth = Number(month);
  const numericYear = Number(year);
  const value = new Date(Date.UTC(numericYear, numericMonth - 1, numericDay));
  if (
    numericYear < 1800 || numericYear > new Date().getFullYear()
    || value.getUTCFullYear() !== numericYear
    || value.getUTCMonth() !== numericMonth - 1
    || value.getUTCDate() !== numericDay
    || value > new Date()
  ) return null;
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
}

export function BirthDatePage() {
  const navigate = useNavigate();
  const [day, setDay] = useState("");
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const birthDate = validDate(day, month, year);
    if (!birthDate) {
      setError("Ngày này chưa đúng. Kiểm tra lại ngày, tháng và năm nhé.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      await createBirthProfile(birthDate);
      void navigate("/reveal");
    } catch {
      setError("Chưa đọc được bầu trời lúc này. Dữ liệu chưa bị lưu — thử lại nhé.");
    } finally {
      setPending(false);
    }
  };

  return (
    <main className="flow-page birth-page">
      <header className="flow-header">
        <button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button>
        <BrandMark />
        <span className="flow-header__step">02 / 02</span>
      </header>
      <section className="birth-intro">
        <span className="birth-intro__planet" aria-hidden="true"><Planet weight="duotone" /></span>
        <p className="eyebrow">Lá Khai Sinh</p>
        <h1>Bạn đáp xuống Trái Đất ngày nào?</h1>
        <p>Chỉ cần ngày sinh. Giờ và nơi sinh có thể bật mí sau.</p>
      </section>
      <form className="birth-form" onSubmit={(event) => void submit(event)} noValidate>
        <fieldset>
          <legend className="sr-only">Ngày sinh</legend>
          <label><span>Ngày</span><input autoComplete="bday-day" inputMode="numeric" maxLength={2} onChange={(event) => setDay(event.target.value.replace(/\D/g, ""))} placeholder="DD" value={day} /></label>
          <span className="date-divider">/</span>
          <label><span>Tháng</span><input autoComplete="bday-month" inputMode="numeric" maxLength={2} onChange={(event) => setMonth(event.target.value.replace(/\D/g, ""))} placeholder="MM" value={month} /></label>
          <span className="date-divider">/</span>
          <label className="birth-form__year"><span>Năm</span><input autoComplete="bday-year" inputMode="numeric" maxLength={4} onChange={(event) => setYear(event.target.value.replace(/\D/g, ""))} placeholder="YYYY" value={year} /></label>
        </fieldset>
        <p className="birth-form__privacy"><ShieldCheck size={18} /> Được mã hóa · tự xóa sau 30 ngày nếu chưa đăng nhập</p>
        {error ? <p className="inline-error" role="alert">{error}</p> : null}
        <button className="electric-button" disabled={pending} type="submit">
          {pending ? "Đang đọc chuyển động thật…" : "Bật mí Lá của mình"}<ArrowRight />
        </button>
      </form>
    </main>
  );
}
