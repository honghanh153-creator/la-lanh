import { ArrowLeft, ArrowRight } from "@phosphor-icons/react";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiProblem, createBirthProfile, getDailyNote, getSession } from "../../shared/api/client";
import { SignalStationFrame } from "../../shared/ui/SignalStationFrame";
import { RADAR_PENDING_REQUEST_KEY } from "../radar/radarOptions";

function validDate(day: string, month: string, year: string): string | null {
  if (!/^\d{1,2}$/.test(day) || !/^\d{1,2}$/.test(month) || !/^\d{4}$/.test(year)) {
    return null;
  }
  const numericDay = Number(day);
  const numericMonth = Number(month);
  const numericYear = Number(year);
  const value = new Date(Date.UTC(numericYear, numericMonth - 1, numericDay));
  if (
    numericYear < new Date().getFullYear() - 120 || numericYear > new Date().getFullYear()
    || value.getUTCFullYear() !== numericYear
    || value.getUTCMonth() !== numericMonth - 1
    || value.getUTCDate() !== numericDay
    || value > new Date()
  ) return null;
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
}

function isUnder18(birthDate: string): boolean {
  const birth = new Date(`${birthDate}T00:00:00.000Z`);
  const today = new Date();
  let age = today.getUTCFullYear() - birth.getUTCFullYear();
  const monthDelta = today.getUTCMonth() - birth.getUTCMonth();
  const birthdayNotReached = monthDelta < 0
    || (monthDelta === 0 && today.getUTCDate() < birth.getUTCDate());
  if (birthdayNotReached) age -= 1;
  return age < 18;
}

export function BirthDatePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const dayInput = useRef<HTMLInputElement>(null);
  const yearInput = useRef<HTMLInputElement>(null);
  const [day, setDay] = useState("");
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [pending, setPending] = useState(false);
  const [profileCreated, setProfileCreated] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void getSession(controller.signal).catch((reason: unknown) => {
      if (!controller.signal.aborted && reason instanceof ApiProblem && reason.status === 401) {
        void navigate("/welcome", { replace: true });
      }
    });
    return () => controller.abort();
  }, [navigate]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const birthDate = validDate(day, month, year);
    if (!birthDate) {
      setError("Ngày này chưa đúng. Kiểm tra lại ngày, tháng và năm nhé.");
      dayInput.current?.focus();
      return;
    }
    if (isUnder18(birthDate)) {
      setError("Lá Lành hiện dành cho người từ 18 tuổi.");
      yearInput.current?.focus();
      return;
    }
    setPending(true);
    setError(null);
    try {
      if (!profileCreated) {
        const profile = await createBirthProfile(birthDate);
        queryClient.setQueryData(["birth-profile"], profile);
        setProfileCreated(true);
      }
      await queryClient.fetchQuery({
        queryKey: ["daily-note"],
        queryFn: ({ signal }) => getDailyNote(signal),
        staleTime: 60_000,
      });
      void navigate(
        Boolean(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY))
          || sessionStorage.getItem("la-lanh-radar-owner-start") === "1"
          ? "/birth-time"
          : "/reveal",
        { replace: true },
      );
    } catch {
      const hasProfile = queryClient.getQueryData(["birth-profile"]) !== undefined;
      setError(hasProfile
        ? "Ngày sinh đã khớp, nhưng Vibe chưa về kịp. Thử tải lại nhé."
        : "Kết nối vừa lỗi một nhịp. Ngày sinh của bạn vẫn được giữ để thử lại.");
    } finally {
      setPending(false);
    }
  };

  const actions = (
    <>
      <button className="signal-station__button" disabled={pending} form="birth-date-form" type="submit">
        {pending ? "Đang khớp tín hiệu…" : profileCreated ? "Tải lại Vibe" : "Khớp tín hiệu"}
        <ArrowRight aria-hidden="true" />
      </button>
      <button className="signal-station__back" disabled={pending} onClick={() => void navigate(-1)} type="button">
        <ArrowLeft aria-hidden="true" /> Quay lại
      </button>
    </>
  );

  return (
    <SignalStationFrame act={1} actions={actions} loading={pending} titleId="birth-title">
      <h1 id="birth-title">Bạn xuất hiện ngày nào?</h1>
      <p className="signal-station__lead">Chỉ ngày sinh thôi. Giờ và nơi sinh có thể bật mí sau.</p>
      <form autoComplete="off" className="signal-date-form" id="birth-date-form" onSubmit={(event) => void submit(event)} noValidate>
        <fieldset className="signal-date-fields" disabled={pending}>
          <legend className="sr-only">Ngày sinh</legend>
          <label className="signal-date-field">
            <span>Ngày</span>
            <input aria-describedby={error ? "birth-error" : undefined} aria-invalid={Boolean(error)} autoComplete="off" className="signal-date-input" inputMode="numeric" maxLength={2} onChange={(event) => setDay(event.target.value.replace(/\D/g, ""))} placeholder="DD" ref={dayInput} value={day} />
          </label>
          <span className="signal-date-divider" aria-hidden="true">/</span>
          <label className="signal-date-field">
            <span>Tháng</span>
            <input aria-describedby={error ? "birth-error" : undefined} aria-invalid={Boolean(error)} autoComplete="off" className="signal-date-input" inputMode="numeric" maxLength={2} onChange={(event) => setMonth(event.target.value.replace(/\D/g, ""))} placeholder="MM" value={month} />
          </label>
          <span className="signal-date-divider" aria-hidden="true">/</span>
          <label className="signal-date-field">
            <span>Năm</span>
            <input aria-describedby={error ? "birth-error" : undefined} aria-invalid={Boolean(error)} autoComplete="off" className="signal-date-input" inputMode="numeric" maxLength={4} onChange={(event) => setYear(event.target.value.replace(/\D/g, ""))} placeholder="YYYY" ref={yearInput} value={year} />
          </label>
        </fieldset>
        <p className="signal-station__privacy">Ngày sinh không xuất hiện khi chia sẻ.</p>
        {pending ? <p className="signal-station__notice" role="status">Đang tìm Mặt Trời và viết Vibe đầu tiên…</p> : null}
        {error ? <p className="signal-station__error" id="birth-error" role="alert">{error}</p> : null}
      </form>
    </SignalStationFrame>
  );
}
