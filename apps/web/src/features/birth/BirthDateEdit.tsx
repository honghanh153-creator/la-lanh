import { ArrowLeft, ArrowRight } from "@phosphor-icons/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type FormEvent, type Ref } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiProblem, correctBirthDate, getBirthProfile, type BirthReveal } from "../../shared/api/client";
import { withdrawCorrectedChart } from "../../shared/storage/clearChartDerivedData";
import { SignalStationFrame } from "../../shared/ui/SignalStationFrame";
import { isUnder18, validDate } from "./birthDateInput";

type DateParts = { day: string; month: string; year: string };

const EMPTY: DateParts = { day: "", month: "", year: "" };
const AGE_MESSAGE = "Lá Lành hiện dành cho người từ 18 tuổi.";

function partsOf(isoDate: string): DateParts {
  const [year, month, day] = isoDate.split("-");
  return { day: day ?? "", month: month ?? "", year: year ?? "" };
}

function messageFor(error: unknown): { text: string; age?: boolean; reload?: boolean; ambiguous?: boolean } {
  const code = error instanceof ApiProblem ? error.code : null;
  switch (code) {
    case "BIRTH_DATE_UNCHANGED":
      return { text: "Ngày này đã được lưu." };
    case "BIRTH_DATE_OUT_OF_RANGE":
      return { text: AGE_MESSAGE, age: true };
    case "BIRTH_DATE_CHANGE_LIMITED":
      return { text: "Bạn đã đổi ngày sinh vài lần hôm nay. Thử lại sau nhé." };
    case "BIRTH_PROFILE_CHANGED":
      return { text: "Hồ sơ vừa được cập nhật ở nơi khác. Mình đã tải lại ngày hiện tại.", reload: true };
    case "BIRTH_DATE_CONFIRMATION_MISMATCH":
      return { text: "Hai lần nhập chưa giống nhau. Kiểm tra lại nhé." };
    default:
      return { text: UNCHANGED_MESSAGE, ambiguous: true };
  }
}

const UNCHANGED_MESSAGE = "Chưa tính được Lá mới. Lá cũ vẫn giữ nguyên.";
const RECONCILED_MESSAGE = "Ngày sinh đã được đổi dù trang chưa nhận được trả lời. Mình đã tải lại hồ sơ hiện tại.";
const UNKNOWN_MESSAGE = "Chưa rõ thay đổi đã được lưu chưa. Kiểm tra lại ngày sinh trong Mình nhé.";

function DateFields({ idPrefix, legend, value, onChange, disabled, invalid, firstInput }: {
  idPrefix: string;
  legend: string;
  value: DateParts;
  onChange: (value: DateParts) => void;
  disabled: boolean;
  invalid: boolean;
  firstInput?: Ref<HTMLInputElement>;
}) {
  const field = (key: keyof DateParts, label: string, placeholder: string, maxLength: number) => (
    <label className="signal-date-field">
      <span>{label}</span>
      <input
        aria-describedby={invalid ? `${idPrefix}-error` : undefined}
        aria-invalid={invalid}
        autoComplete="off"
        className="signal-date-input"
        inputMode="numeric"
        maxLength={maxLength}
        onChange={(event) => onChange({ ...value, [key]: event.target.value.replace(/\D/g, "") })}
        placeholder={placeholder}
        ref={key === "day" ? firstInput : undefined}
        value={value[key]}
      />
    </label>
  );
  return (
    <fieldset className="signal-date-fields" disabled={disabled}>
      <legend className="sr-only">{legend}</legend>
      {field("day", "Ngày", "DD", 2)}
      <span className="signal-date-divider" aria-hidden="true">/</span>
      {field("month", "Tháng", "MM", 2)}
      <span className="signal-date-divider" aria-hidden="true">/</span>
      {field("year", "Năm", "YYYY", 4)}
    </fieldset>
  );
}

/**
 * US-23: correct a saved birth date. The current date is prefilled; a save asks for the new date
 * once more as a typo check, and the 18+ rule runs before anything is sent (D6). The server
 * refuses a stale revision from another tab, the same date and a fourth change in 24 hours.
 */
export function BirthDateEdit() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const firstInput = useRef<HTMLInputElement>(null);
  const confirmInput = useRef<HTMLInputElement>(null);
  const profile = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal), retry: false });
  const [value, setValue] = useState<DateParts>(EMPTY);
  const [confirm, setConfirm] = useState<DateParts>(EMPTY);
  const [stage, setStage] = useState<"edit" | "confirm">("edit");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<{ text: string; age?: boolean } | null>(null);
  const loaded = profile.data;

  useEffect(() => {
    if (loaded) setValue(partsOf(loaded.birth_date));
  }, [loaded]);

  useEffect(() => {
    if (stage === "confirm") confirmInput.current?.focus();
  }, [stage]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (pending || !loaded) return;
    const birthDate = validDate(value.day, value.month, value.year);
    if (!birthDate) {
      setError({ text: "Ngày này chưa đúng. Kiểm tra lại ngày, tháng và năm nhé." });
      setStage("edit");
      firstInput.current?.focus();
      return;
    }
    if (isUnder18(birthDate)) {
      setError({ text: AGE_MESSAGE, age: true });
      setStage("edit");
      return;
    }
    if (birthDate === loaded.birth_date) {
      setError({ text: "Ngày này đã được lưu." });
      return;
    }
    if (stage === "edit") {
      setError(null);
      setConfirm(EMPTY);
      setStage("confirm");
      return;
    }
    const confirmed = validDate(confirm.day, confirm.month, confirm.year);
    if (confirmed !== birthDate) {
      setError({ text: "Hai lần nhập chưa giống nhau. Kiểm tra lại nhé." });
      confirmInput.current?.focus();
      return;
    }
    if (!loaded.profile_revision) {
      setError({ text: "Chưa tải được ngày hiện tại. Thử lại sau nhé." });
      return;
    }
    setPending(true);
    setError(null);
    try {
      await correctBirthDate({
        birth_date: birthDate,
        confirm_birth_date: confirmed,
        expected_revision: loaded.profile_revision,
      });
      // The cleanup refetches the active profile; that answer is the latest server revision and
      // is kept even if another tab corrected again meanwhile (Codex r55).
      await withdrawCorrectedChart(queryClient);
      void navigate("/reveal", { replace: true, state: { corrected: true } });
    } catch (failure) {
      const message = messageFor(failure);
      if (message.ambiguous) {
        // A timeout or transport failure says nothing about the commit, which happens before the
        // send drain. Read the profile again: a new revision means the change is in.
        setError({ text: await reconcile(loaded.profile_revision) });
        return;
      }
      setError(message);
      if (message.reload) {
        setStage("edit");
        const current = await profile.refetch();
        if (current.data) setValue(partsOf(current.data.birth_date));
      }
    } finally {
      setPending(false);
    }
  };

  const reconcile = async (submitted: string): Promise<string> => {
    const current = await profile.refetch();
    if (current.isError || !current.data) return UNKNOWN_MESSAGE;
    if (current.data.profile_revision === submitted) return UNCHANGED_MESSAGE;
    await withdrawCorrectedChart(queryClient);
    const latest = queryClient.getQueryData<BirthReveal>(["birth-profile"]) ?? current.data;
    setValue(partsOf(latest.birth_date));
    setStage("edit");
    return RECONCILED_MESSAGE;
  };

  const actions = (
    <>
      <button className="signal-station__button" disabled={pending || !loaded} form="birth-edit-form" type="submit">
        {pending ? "Đang tạo lại Lá…" : stage === "confirm" ? "Đổi ngày sinh" : "Tiếp tục"}
        <ArrowRight aria-hidden="true" />
      </button>
      <button className="signal-station__back" disabled={pending} onClick={() => void navigate("/profile")} type="button">
        <ArrowLeft aria-hidden="true" /> Giữ như cũ
      </button>
    </>
  );

  return (
    <SignalStationFrame act={1} actions={actions} loading={pending} titleId="birth-edit-title">
      <h1 id="birth-edit-title">Sửa ngày sinh</h1>
      <p className="signal-station__lead">Đổi ngày sinh sẽ tạo lại Lá của bạn. Giờ và nơi sinh được xoá; bạn có thể thêm lại sau.</p>
      {profile.isPending ? <p role="status">Đang tải ngày đã lưu…</p> : null}
      {profile.isError ? <p className="signal-station__error" role="alert">Chưa tải được ngày đã lưu. Thử lại sau nhé.</p> : null}
      <form autoComplete="off" className="signal-date-form" id="birth-edit-form" noValidate onSubmit={(event) => void submit(event)}>
        <DateFields
          disabled={pending || !loaded || stage === "confirm"}
          firstInput={firstInput}
          idPrefix="birth-edit"
          invalid={Boolean(error) && stage === "edit"}
          legend="Ngày sinh mới"
          onChange={(next) => { setValue(next); setError(null); }}
          value={value}
        />
        {stage === "confirm" ? (
          <>
            <p className="signal-station__privacy">Nhập lại ngày mới một lần nữa để chắc chắn không gõ nhầm.</p>
            <DateFields
              disabled={pending}
              firstInput={confirmInput}
              idPrefix="birth-confirm"
              invalid={Boolean(error)}
              legend="Nhập lại ngày sinh mới"
              onChange={(next) => { setConfirm(next); setError(null); }}
              value={confirm}
            />
            <button className="text-button" disabled={pending} onClick={() => { setStage("edit"); setError(null); }} type="button">Sửa lại ngày</button>
          </>
        ) : null}
        <p className="signal-station__privacy">Note đã lưu và link đã chia sẻ được giữ; bạn bỏ lưu hoặc thu hồi link trong Đã lưu.</p>
        {error ? (
          <p className="signal-station__error" id={stage === "confirm" ? "birth-confirm-error" : "birth-edit-error"} role="alert">
            {error.text}
            {error.age ? <> <Link state={{ confirmDelete: true }} to="/profile">Xóa Lá và dữ liệu</Link></> : null}
          </p>
        ) : null}
      </form>
    </SignalStationFrame>
  );
}
