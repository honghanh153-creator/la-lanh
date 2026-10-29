import { ArrowLeft, ArrowRight } from "@phosphor-icons/react";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { acceptBasicBirthConsent, addBirthSupplement, ApiProblem, createBirthProfile, getBirthProfile, getDailyNote, getSession, updateOnboardingStatus } from "../../shared/api/client";
import { clearChartDerivedData } from "../../shared/storage/clearChartDerivedData";
import { SignalStationFrame } from "../../shared/ui/SignalStationFrame";
import { RADAR_PENDING_REQUEST_KEY } from "../radar/radarOptions";
import { BirthDateEdit } from "./BirthDateEdit";
import { isUnder18, validDate } from "./birthDateInput";
import { OptionalBirthDetails } from "./OptionalBirthDetails";
import { birthDetailsError, emptyBirthDetails, hasBirthDetails, type OptionalBirthInput } from "./optionalBirthInput";

export function BirthDatePage() {
  const [params] = useSearchParams();
  // US-23: `/birth?edit=1` corrects a saved date; plain `/birth` is first entry only.
  return params.get("edit") === "1" ? <BirthDateEdit /> : <BirthDateOnboarding />;
}

function BirthDateOnboarding() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const dayInput = useRef<HTMLInputElement>(null);
  const yearInput = useRef<HTMLInputElement>(null);
  const [day, setDay] = useState("");
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [pending, setPending] = useState(false);
  const [profileCreated, setProfileCreated] = useState(false);
  const [details, setDetails] = useState<OptionalBirthInput>({ ...emptyBirthDetails });
  const [supplementSaved, setSupplementSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Date validation errors sit under the date fields; submit errors stay above the primary action.
  const [errorAtField, setErrorAtField] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void getSession(controller.signal).then(async (session) => {
      // A person who already has an active birth subject corrects it from Mình (US-23), so
      // first entry never posts a second date. Only checked once onboarding has moved on.
      if (session.onboarding_status === "birth_pending") return;
      try {
        await getBirthProfile(controller.signal);
        if (!controller.signal.aborted) void navigate("/profile", { replace: true });
      } catch {
        // No active subject (404, e.g. after a fail-closed restore): stay for re-entry.
      }
    }, (reason: unknown) => {
      if (!controller.signal.aborted && reason instanceof ApiProblem && reason.status === 401) {
        void navigate("/welcome", { replace: true });
      }
    });
    return () => controller.abort();
  }, [navigate]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (pending) return;
    const birthDate = validDate(day, month, year);
    if (!birthDate) {
      setError("Ngày này chưa đúng. Kiểm tra lại ngày, tháng và năm nhé.");
      setErrorAtField(true);
      dayInput.current?.focus();
      return;
    }
    if (isUnder18(birthDate)) {
      setError("Lá Lành hiện dành cho người từ 18 tuổi.");
      setErrorAtField(true);
      yearInput.current?.focus();
      return;
    }
    const detailError = supplementSaved ? null : birthDetailsError(details);
    if (detailError) { setError(detailError); setErrorAtField(false); return; }
    setPending(true);
    setError(null);
    setErrorAtField(false);
    let stage: "date" | "supplement" | "note" = "date";
    try {
      if (!profileCreated) {
        await acceptBasicBirthConsent();
        const profile = await createBirthProfile(birthDate);
        await clearChartDerivedData(queryClient);
        queryClient.setQueryData(["birth-profile"], profile);
        setProfileCreated(true);
      }
      if (hasBirthDetails(details) && !supplementSaved) {
        stage = "supplement";
        await addBirthSupplement({
          birth_time_mode: details.mode,
          birth_time_local: details.mode === "exact" ? details.time : null,
          approx_window: details.mode === "approx_window" ? details.window : null,
          place_id: details.place?.place_id ?? null,
        });
        setSupplementSaved(true);
        await clearChartDerivedData(queryClient);
      }
      stage = "note";
      // The supplementary calculation may have replaced the date-only snapshot.
      if (hasBirthDetails(details)) {
        await queryClient.fetchQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal), staleTime: 0 });
      }
      await queryClient.fetchQuery({
        queryKey: ["daily-note"],
        queryFn: ({ signal }) => getDailyNote(signal),
        staleTime: 0,
      });
      const exactComplete = details.mode === "exact" && Boolean(details.place);
      const radarPending = Boolean(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY));
      const radarOwner = sessionStorage.getItem("la-lanh-radar-owner-start") === "1";
      if (exactComplete && (radarPending || radarOwner)) {
        await updateOnboardingStatus("completed");
        if (radarOwner) sessionStorage.removeItem("la-lanh-radar-owner-start");
        void navigate(radarPending ? "/radar/continue" : "/radar/start", { replace: true });
        return;
      }
      void navigate(
        (radarPending || radarOwner)
          ? "/birth-time"
          : "/reveal",
        { replace: true },
      );
    } catch {
      const hasProfile = queryClient.getQueryData(["birth-profile"]) !== undefined;
      setErrorAtField(false);
      setError(stage === "supplement"
        ? "Ngày sinh đã lưu, nhưng giờ/nơi sinh chưa lưu được. Thử lại hoặc bỏ qua phần bổ sung nhé."
        : hasProfile
        ? "Ngày sinh đã khớp, nhưng Vibe chưa về kịp. Thử tải lại nhé."
        : "Kết nối vừa lỗi một nhịp. Ngày sinh của bạn vẫn được giữ để thử lại.");
    } finally {
      setPending(false);
    }
  };

  const actions = (
    <>
      <button className="signal-station__button" disabled={pending} form="birth-date-form" type="submit">
        {pending ? "Đang khớp tín hiệu…" : profileCreated ? "Thử tải lại" : "Khớp tín hiệu"}
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
      <p className="signal-station__lead">Chỉ cần ngày sinh để bắt đầu. Biết giờ và nơi sinh thì thêm luôn, chưa biết cứ để sau.</p>
      <form autoComplete="off" className="signal-date-form" id="birth-date-form" onSubmit={(event) => void submit(event)} noValidate>
        <fieldset className="signal-date-fields" disabled={pending || profileCreated}>
          <legend className="sr-only">Ngày sinh</legend>
          <label className="signal-date-field">
            <span>Ngày</span>
            <input aria-describedby={error ? "birth-error" : undefined} aria-invalid={Boolean(error && errorAtField)} autoComplete="off" className="signal-date-input" inputMode="numeric" maxLength={2} onChange={(event) => setDay(event.target.value.replace(/\D/g, ""))} placeholder="DD" ref={dayInput} value={day} />
          </label>
          <span className="signal-date-divider" aria-hidden="true">/</span>
          <label className="signal-date-field">
            <span>Tháng</span>
            <input aria-describedby={error ? "birth-error" : undefined} aria-invalid={Boolean(error && errorAtField)} autoComplete="off" className="signal-date-input" inputMode="numeric" maxLength={2} onChange={(event) => setMonth(event.target.value.replace(/\D/g, ""))} placeholder="MM" value={month} />
          </label>
          <span className="signal-date-divider" aria-hidden="true">/</span>
          <label className="signal-date-field">
            <span>Năm</span>
            <input aria-describedby={error ? "birth-error" : undefined} aria-invalid={Boolean(error && errorAtField)} autoComplete="off" className="signal-date-input" inputMode="numeric" maxLength={4} onChange={(event) => setYear(event.target.value.replace(/\D/g, ""))} placeholder="YYYY" ref={yearInput} value={year} />
          </label>
        </fieldset>
        {error && errorAtField ? <p className="signal-date-error" id="birth-error" role="alert">{error}</p> : null}
        <p className="signal-station__privacy">Ngày sinh không xuất hiện khi chia sẻ.</p>
        <p className="signal-station__privacy">Bấm Khớp tín hiệu là đồng ý dùng ngày sinh để tính lá số và note. Không tự bật AI viết lại.</p>
        <OptionalBirthDetails value={details} onChange={(value) => { setDetails(value); setError(null); }} disabled={pending || supplementSaved} error={error && birthDetailsError(details) === error ? error : null} />
        {profileCreated && !pending ? <small>Ngày sinh đã lưu. Thử lại sẽ không tạo hồ sơ mới.</small> : null}
        {pending ? <p className="signal-station__notice" role="status">{hasBirthDetails(details) ? "Đang lưu thông tin bạn cho phép và tính lại lá số…" : "Đang tìm Mặt Trời và viết Vibe đầu tiên…"}</p> : null}
        {error && !errorAtField ? <p className="signal-station__error" id="birth-error" role="alert">{error}</p> : null}
      </form>
    </SignalStationFrame>
  );
}
