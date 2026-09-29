import { ArrowDown } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { getBirthProfile, getDailyNote, updateOnboardingStatus } from "../../shared/api/client";
import { isDateOnlyCalculation, sunSignsFromCalculation } from "../../shared/astro/chart";
import { signDetails } from "../../shared/astro/signs";
import { SignalStationFrame } from "../../shared/ui/SignalStationFrame";
import { ReadingDisclaimer } from "../../shared/ui/ReadingDisclaimer";

const elementBySign = {
  aries: "Lửa · trực giác · khởi đầu", leo: "Lửa · biểu đạt · ấm áp", sagittarius: "Lửa · khám phá · tự do",
  taurus: "Đất · bền bỉ · cảm nhận", virgo: "Đất · tinh tế · chăm chút", capricorn: "Đất · đường dài · vững vàng",
  gemini: "Khí · tò mò · kết nối", libra: "Khí · hài hòa · thẩm mỹ", aquarius: "Khí · khác biệt · ý tưởng",
  cancer: "Nước · che chở · nhạy cảm", scorpio: "Nước · chiều sâu · chuyển hóa", pisces: "Nước · trực giác · mộng mơ",
} as const;

export function RevealPage() {
  const navigate = useNavigate();
  const [completing, setCompleting] = useState(false);
  const [completionError, setCompletionError] = useState<string | null>(null);
  const query = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal), staleTime: 60_000 });
  const noteQuery = useQuery({ queryKey: ["daily-note"], queryFn: ({ signal }) => getDailyNote(signal), staleTime: 60_000 });

  if (query.isLoading || noteQuery.isLoading) return (
    <SignalStationFrame act={2} className="signal-station--loading" loading titleId="reveal-loading-title">
      <span className="signal-station__pulse" aria-hidden="true" />
      <h1 id="reveal-loading-title">Đang mở Vibe đầu tiên…</h1>
      <p className="signal-station__lead">Một lần tải cho Mặt Trời và note của bạn.</p>
    </SignalStationFrame>
  );

  if (!query.data) return (
    <SignalStationFrame
      act={1}
      actions={<button className="signal-station__button" onClick={() => void navigate("/birth")} type="button">Nhập ngày sinh</button>}
      titleId="missing-reveal-title"
    >
      <h1 id="missing-reveal-title">Chưa tìm thấy tín hiệu.</h1>
      <p className="signal-station__lead">Ngày sinh chưa được khớp hoặc kết nối vừa gián đoạn.</p>
    </SignalStationFrame>
  );

  const { calculation } = query.data;
  const signs = sunSignsFromCalculation(calculation);
  const primary = signDetails[signs[0]];
  const isDateOnly = isDateOnlyCalculation(calculation);
  const isCusp = isDateOnly && signs.length > 1;
  const vibeLabel = isCusp ? "Giao mùa" : (noteQuery.data?.persona_label ?? primary.label);

  const complete = async () => {
    if (completing) return;
    setCompleting(true);
    setCompletionError(null);
    try {
      await updateOnboardingStatus("completed");
      void navigate("/home", { replace: true });
    } catch {
      setCompletionError("Chưa mở được Note hôm nay. Tín hiệu của bạn vẫn được giữ để thử lại.");
    } finally {
      setCompleting(false);
    }
  };

  const actions = (
    <>
      {completionError ? <p className="signal-station__error" role="alert">{completionError}</p> : null}
      <button className="signal-station__button" disabled={completing} onClick={() => void complete()} type="button">
        {completing ? "Đang mở Note…" : "Mở Note hôm nay"} <ArrowDown aria-hidden="true" />
      </button>
      <ReadingDisclaimer compact>
        Nội dung dùng để tự soi và đối chiếu; quyết định vẫn thuộc về bạn.
      </ReadingDisclaimer>
    </>
  );

  return (
    <SignalStationFrame act={2} actions={actions} loading={completing} titleId="reveal-title">
      <section className="signal-reveal-card">
        <h1 id="reveal-title">Vibe · {vibeLabel}</h1>
        <p className="signal-reveal-card__pill">
          {isCusp
            ? `Mặt Trời ở ranh giới ${signs.map((sign) => signDetails[sign].label).join(" · ")}`
            : `Mặt Trời ${primary.label} · ${elementBySign[signs[0]]}`}
        </p>
        <p className="signal-reveal-card__line">
          {isCusp ? "Ngày này chạm đúng ranh giới. Lá không đoán cung khi chưa có giờ sinh." : primary.note}
        </p>
        <p className="signal-reveal-card__source">
          Đọc từ ngày sinh · chưa dùng giờ/nơi sinh · Swiss Ephemeris {calculation.provenance.version}
        </p>
        {noteQuery.isError ? <p className="signal-station__notice" role="status">Vibe đang dùng lớp Mặt Trời đã tính; Note hôm nay sẽ tải lại ở Home.</p> : null}
      </section>
    </SignalStationFrame>
  );
}
