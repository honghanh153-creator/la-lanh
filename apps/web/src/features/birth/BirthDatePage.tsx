import { ArrowLeft, ArrowRight, LockKey, Planet, ShieldCheck, Trash } from "@phosphor-icons/react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiProblem, createBirthProfile, createGuest, getSession } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";

function idempotencyKey(): string {
  const existing = sessionStorage.getItem("la-lanh-guest-create-key");
  if (existing) return existing;
  const value = crypto.randomUUID();
  sessionStorage.setItem("la-lanh-guest-create-key", value);
  return value;
}

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

function isChildBirthDate(birthDate: string): boolean {
  const birth = new Date(`${birthDate}T00:00:00.000Z`);
  const today = new Date();
  let age = today.getUTCFullYear() - birth.getUTCFullYear();
  const monthDelta = today.getUTCMonth() - birth.getUTCMonth();
  const birthdayNotReached = monthDelta < 0
    || (monthDelta === 0 && today.getUTCDate() < birth.getUTCDate());
  if (birthdayNotReached) age -= 1;
  return age < 16;
}

async function ensureGuestSession() {
  try {
    await getSession();
  } catch (error) {
    if (error instanceof ApiProblem && error.status === 401) {
      await createGuest(idempotencyKey());
      sessionStorage.removeItem("la-lanh-guest-create-key");
      return;
    }
    throw error;
  }
}

export function BirthDatePage() {
  const navigate = useNavigate();
  const [day, setDay] = useState("");
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [consented, setConsented] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const birthDate = validDate(day, month, year);
    if (!birthDate) {
      setError("Ngày này chưa đúng. Kiểm tra lại ngày, tháng và năm nhé.");
      return;
    }
    if (isChildBirthDate(birthDate)) {
      setError("Lá Lành chưa xử lý dữ liệu của người dưới 16 tuổi khi chưa có xác nhận của phụ huynh hoặc người giám hộ.");
      return;
    }
    if (!consented) {
      setError("Bạn cần tick đồng ý trước khi Lá Lành gửi ngày sinh để tính Lá Khai Sinh.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      await ensureGuestSession();
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
        <span className="flow-header__step">01 / 02</span>
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
        <section className="privacy-consent" aria-label="Đồng ý xử lý dữ liệu ngày sinh">
          <p className="privacy-consent__title"><ShieldCheck size={18} weight="fill" /> Trước khi gửi ngày sinh</p>
          <ul>
            <li><Planet size={16} /> Dữ liệu dùng để tính Lá Khai Sinh và note cá nhân hóa.</li>
            <li><LockKey size={16} /> Ngày sinh được gửi qua kênh bảo mật, mã hóa khi lưu; không nằm trong cookie hay URL.</li>
            <li><Trash size={16} /> Phiên khách tự hết hạn sau 30 ngày và có thể xóa ngay trong mục Mình.</li>
          </ul>
          <label className="consent-check">
            <input checked={consented} onChange={(event) => setConsented(event.target.checked)} type="checkbox" />
            <span>Tôi đã hiểu và đồng ý để Lá Lành xử lý ngày sinh cho mục đích này.</span>
          </label>
          <Link className="detail-link" to="/privacy">Xem quyền dữ liệu & bảo mật</Link>
        </section>
        {error ? <p className="inline-error" role="alert">{error}</p> : null}
        <button className="electric-button" disabled={pending} type="submit">
          {pending ? "Đang đọc chuyển động thật…" : "Bật mí Lá của mình"}<ArrowRight />
        </button>
      </form>
    </main>
  );
}
