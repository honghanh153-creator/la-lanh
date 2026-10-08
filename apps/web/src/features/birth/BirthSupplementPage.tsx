import { ArrowLeft, Clock, Gift, LockKey, MapPin, MoonStars, ShieldCheck, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  addBirthSupplement,
  getDailyNote,
  searchBirthPlaces,
  type ApproxWindow,
  type BirthTimeMode,
  type PlaceResult,
  type DailyNote,
} from "../../shared/api/client";
import { clearCachedDailyNote, writeCachedDailyNote } from "../../shared/storage/noteCache";
import { BrandMark } from "../../shared/ui/BrandMark";
import { BirthTimeInput } from "../../shared/ui/BirthTimeInput";
import { birthTimeWindows as windows } from "../../shared/ui/birthTimeOptions";
import { RADAR_PENDING_REQUEST_KEY } from "../radar/radarOptions";

function validTime(value: string): boolean {
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(value);
}

export function BirthSupplementPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [step, setStep] = useState<"prompt" | "time" | "place" | "review" | "success">("prompt");
  const [learnMore, setLearnMore] = useState(false);
  const [mode, setMode] = useState<BirthTimeMode>("exact");
  const [birthTime, setBirthTime] = useState("");
  const [approxWindow, setApproxWindow] = useState<ApproxWindow>("morning");
  const [placeQuery, setPlaceQuery] = useState("");
  const [debouncedPlaceQuery, setDebouncedPlaceQuery] = useState("");
  const [showAllPlaces, setShowAllPlaces] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState<PlaceResult | null>(null);
  const [consented, setConsented] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [awakenedNote, setAwakenedNote] = useState<DailyNote | null>(null);
  const radarPending = Boolean(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY));
  const radarOwnerStart = sessionStorage.getItem("la-lanh-radar-owner-start") === "1";
  const radarFlow = radarPending || radarOwnerStart;

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedPlaceQuery(placeQuery.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [placeQuery]);

  const effectivePlaceQuery = debouncedPlaceQuery.length >= 2 ? debouncedPlaceQuery : "";
  const placesQuery = useQuery({
    queryKey: ["birth-places", showAllPlaces ? "all-current" : effectivePlaceQuery],
    queryFn: ({ signal }) => searchBirthPlaces(showAllPlaces ? "" : effectivePlaceQuery, signal),
    enabled: (showAllPlaces || effectivePlaceQuery.length >= 2)
      && selectedPlace?.display_name !== debouncedPlaceQuery,
  });

  const submitMutation = useMutation({
    mutationFn: () => addBirthSupplement({
      birth_time_mode: mode,
      birth_time_local: mode === "exact" ? birthTime : null,
      approx_window: mode === "approx_window" ? approxWindow : null,
      place_id: selectedPlace?.place_id ?? null,
    }),
    onSuccess: async (payload) => {
      if (payload.profile_level === 1) {
        localStorage.setItem(
          "la-lanh-birth-supplement-snooze-until",
          String(Date.now() + 3 * 24 * 60 * 60 * 1000),
        );
      }
      clearCachedDailyNote();
      await queryClient.invalidateQueries({ queryKey: ["birth-supplement"] });
      if (radarFlow && payload.profile_level === 3) {
        if (radarOwnerStart) sessionStorage.removeItem("la-lanh-radar-owner-start");
        await navigate(radarPending ? "/radar/continue" : "/radar/start", { replace: true });
        return;
      }
      try {
        const refreshed = await queryClient.fetchQuery({
          queryKey: ["daily-note"],
          queryFn: ({ signal }) => getDailyNote(signal),
          staleTime: 0,
        });
        writeCachedDailyNote(refreshed);
        setAwakenedNote(refreshed);
        const auraTransition = refreshed.reading_projection?.aura_transition;
        const hasFullSynthesisGift = mode === "exact"
          && auraTransition?.profile_readiness === "aura_ready"
          && Boolean(auraTransition.transition_id)
          && refreshed.reading_projection?.available_update?.content.mode === "full_synthesis";
        if (hasFullSynthesisGift) {
          await navigate("/aura-cutover", { replace: true });
          return;
        }
      } catch {
        if (mode === "exact") {
          await navigate("/aura-cutover", { replace: true });
          return;
        }
        setError("Chart đã mở, nhưng note mới chưa về kịp. Bạn có thể thử lại ở Home.");
      }
      setStep("success");
    },
    onError: () => setError("Chưa mở được lớp này. Kiểm tra lại giờ/nơi sinh hoặc thử lại sau nhé."),
  });

  const submit = () => {
    if (!consented) {
      setError("Bạn cần đồng ý rõ ràng trước khi gửi giờ/nơi sinh.");
      return;
    }
    if (mode === "exact" && !validTime(birthTime)) {
      setError("Chọn đủ giờ và phút nhé.");
      return;
    }
    if (radarFlow && (mode !== "exact" || !selectedPlace)) {
      setError("Radar hai người cần giờ sinh chính xác và một nơi sinh đã chọn.");
      return;
    }
    setError(null);
    submitMutation.mutate();
  };

  const snooze = () => {
    localStorage.setItem(
      "la-lanh-birth-supplement-snooze-until",
      String(Date.now() + 3 * 24 * 60 * 60 * 1000),
    );
    void navigate("/home", { replace: true });
  };

  const timeSummary = mode === "exact"
    ? `Chính xác · ${birthTime || "chưa nhập"}`
    : mode === "approx_window"
      ? `Gần đúng · ${windows.find((item) => item.value === approxWindow)?.label ?? ""}`
      : "Chưa biết giờ sinh";
  const readingGift = awakenedNote?.reading_projection?.available_update;

  return (
    <main className="flow-page birth-supplement-page">
      <header className="flow-header">
        <button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button>
        <BrandMark />
        <span className="flow-header__step">02 / 02</span>
      </header>
      <section className="birth-intro">
        <span className="birth-intro__planet" aria-hidden="true"><MoonStars weight="duotone" /></span>
        <p className="eyebrow">Mở thêm lớp cá nhân</p>
        <h1>{step === "prompt" ? radarFlow ? "Hoàn thiện chart riêng của bạn." : "Mở thêm một lớp bí mật?" : step === "success" ? readingGift ? "Một món quà Aura đang chờ." : "Một lớp Lá mới đã mở." : "Giờ và nơi sinh là chiếc chìa khóa sâu hơn."}</h1>
        <p>{step === "prompt" ? radarFlow ? "Radar cần chart đủ lớp của cả hai. Dữ liệu sinh của mỗi người vẫn được giữ riêng." : "Thời điểm sinh làm rõ vị trí Moon; đủ giờ và nơi sinh mới tính được Rising cùng các House. Hoàn toàn không bắt buộc." : "Dữ liệu này chỉ dùng để tính lá số và có thể xóa bất cứ lúc nào."}</p>
      </section>
      <div className="birth-form supplement-form">
        {step === "prompt" ? <section className="choice-panel unlock-prompt">
          <p><MoonStars size={18} /> Bạn sẽ nhận được gì?</p>
          <ul><li>Moon và nhịp cảm xúc rõ hơn.</li><li>Rising/House khi có đủ giờ và nơi sinh.</li></ul>
          <button className="electric-button" onClick={() => setStep("time")} type="button">Thêm để mở lớp mới</button>
          <button className="text-button" onClick={snooze} type="button">Để sau</button>
          <button className="detail-link" onClick={() => setLearnMore((value) => !value)} type="button">Dữ liệu này được dùng thế nào?</button>
          {learnMore ? <p className="privacy-plain">Lá Lành gửi dữ liệu lên server để tính chart, mã hóa khi lưu, không đưa vào card/link share và không xin GPS.</p> : null}
        </section> : null}
        {step === "time" ? <>
        <section className="choice-panel" aria-label="Bạn nhớ giờ sinh thế nào">
          <p><Clock size={18} /> Bạn nhớ giờ sinh thế nào?</p>
          <BirthTimeInput mode={mode} onModeChange={setMode} time={birthTime} onTimeChange={setBirthTime} window={approxWindow} onWindowChange={setApproxWindow} modes={radarFlow ? ["exact"] : undefined} />
        </section>
        {error ? <p className="inline-error" role="alert">{error}</p> : null}
        <button className="electric-button" onClick={() => {
          if (mode === "exact" && !validTime(birthTime)) {
            setError("Chọn đủ giờ và phút nhé.");
            return;
          }
          setError(null);
          setStep(mode === "unknown" ? "review" : "place");
        }} type="button">Tiếp tục</button>
        </> : null}
        {step === "place" ? <>
          <section className="choice-panel" aria-label="Nơi sinh">
            <p><MapPin size={18} /> Nơi sinh</p>
            <label>
              <span>Thành phố / tỉnh</span>
              <input
                autoComplete="off"
                onChange={(event) => {
                  setPlaceQuery(event.target.value);
                  setSelectedPlace(null);
                  setShowAllPlaces(false);
                }}
                placeholder="Ví dụ: Hà Nội"
                value={placeQuery}
              />
            </label>
            <p className="privacy-plain">Danh mục 34 tỉnh/thành hiện hành từ 01/07/2025. Tên tỉnh cũ vẫn tìm được và sẽ ghi rõ nơi trực thuộc hiện nay.</p>
            <button className="detail-link" onClick={() => setShowAllPlaces((value) => !value)} type="button">
              {showAllPlaces ? "Thu gọn danh mục" : "Xem đủ 34 tỉnh/thành"}
            </button>
            {placesQuery.data && placesQuery.data.length > 0 ? (
              <div aria-label="Danh sách nơi sinh" className="place-results">
                {placesQuery.data.map((place) => (
                  <button
                    key={place.place_id}
                    onClick={() => {
                      setSelectedPlace(place);
                      setPlaceQuery(place.display_name);
                      setShowAllPlaces(false);
                    }}
                    type="button"
                  >
                    <strong>{place.display_name}</strong>
                    <span>{place.confidence === "former-province-centroid" ? "Tên địa phương trước sắp xếp" : "Danh mục hiện hành · 01/07/2025"}</span>
                  </button>
                ))}
              </div>
            ) : null}
            {placeQuery.trim().length >= 2 && placesQuery.data?.length === 0 ? <p className="privacy-plain">{radarFlow ? "Chưa thấy nơi này. Thử cả tên tỉnh hiện hành hoặc tên trước sắp xếp; đừng chọn đại vì có thể làm lệch House." : "Không thấy nơi này. Thử cả tên tỉnh hiện hành hoặc tên trước sắp xếp."}</p> : null}
          </section>
          <button className="electric-button" disabled={!selectedPlace} onClick={() => setStep("review")} type="button">Dùng nơi đã chọn</button>
          {!radarFlow ? <button className="text-button" onClick={() => { setSelectedPlace(null); setStep("review"); }} type="button">Bỏ qua nơi sinh</button> : null}
        </> : null}
        {step === "review" ? <>
        <section className="choice-panel review-card">
          <p><Clock size={18} /> <strong>Giờ sinh:</strong> {timeSummary}</p>
          <p><MapPin size={18} /> <strong>Nơi sinh:</strong> {selectedPlace?.display_name ?? "Chưa thêm"}</p>
          <button className="detail-link" onClick={() => setStep("time")} type="button">Sửa thông tin</button>
        </section>
        <section className="privacy-consent" aria-label="Đồng ý xử lý giờ và nơi sinh">
          <p className="privacy-consent__title"><ShieldCheck size={18} weight="fill" /> Vì đây là dữ liệu sâu hơn</p>
          <ul>
            <li><LockKey size={16} /> Giờ/nơi sinh được mã hóa khi lưu, không đưa vào link share, không nằm trong localStorage.</li>
            <li><MoonStars size={16} /> Chỉ dùng để tính chart sâu hơn và cá nhân hóa note trong Lá Lành.</li>
          </ul>
          <label className="consent-check">
            <input checked={consented} onChange={(event) => setConsented(event.target.checked)} type="checkbox" />
            <span>Tôi đồng ý để Lá Lành xử lý giờ/nơi sinh cho mục đích mở lớp cá nhân này.</span>
          </label>
          <Link className="detail-link" to="/privacy">Xem quyền dữ liệu & bảo mật</Link>
        </section>
        {error ? <p className="inline-error" role="alert">{error}</p> : null}
        <button className="electric-button" disabled={submitMutation.isPending || !consented} onClick={submit} type="button">
          {submitMutation.isPending ? "Đang mở lớp…" : "Mở lớp Moon / House"}
        </button>
        <button className="text-button" onClick={snooze} type="button">Để sau</button>
        </> : null}
        {step === "success" ? <div className="awakening-reveal" aria-live="polite">
          <section className={`choice-panel unlock-success${awakenedNote?.awakening ? " aura-awakening" : ""}`}>
            <span className="aura-awakening__orb"><Sparkle size={30} weight="fill" /></span>
            <p className="eyebrow">{readingGift ? "Quà Aura đã sẵn sàng" : awakenedNote?.awakening ? "Aura awakening" : "Đã cập nhật dữ liệu sinh"}</p>
            <h2>{readingGift?.message ?? awakenedNote?.awakening?.headline ?? (submitMutation.data?.profile_level === 3 ? "Chart sâu hơn đã sẵn sàng" : "Đã lưu lớp thông tin mới")}</h2>
            <p>{readingGift ? "Lá đã đọc lại nhiều hành tinh, nhà và góc chiếu cùng nhau. Note hiện tại vẫn được giữ nguyên cho tới khi bạn tự chọn mở món quà ở Home." : awakenedNote?.awakening?.summary ?? (mode === "approx_window" ? "Insight nhạy với giờ sinh sẽ được trình bày rộng hơn, không giả là chính xác." : "Lá Lành đã tính lại chart theo dữ liệu bạn vừa cho phép.")}</p>
            {awakenedNote?.awakening ? <div className="awakening-factors" aria-label="Những lớp vừa được tính">
              {awakenedNote.awakening.factors.map((factor) => <span key={factor}>{factor}</span>)}
            </div> : null}
            {awakenedNote?.awakening ? <small>{awakenedNote.awakening.precision_label}</small> : null}
          </section>
          {awakenedNote?.sky_chapter ? <section className="choice-panel sky-gift">
            <span className="sky-gift__label"><Gift weight="fill" /> Quà mở khóa</span>
            <h3>{awakenedNote.sky_chapter.title}</h3>
            <p className="sky-gift__phase">{awakenedNote.sky_chapter.phase_label}</p>
            <strong>{awakenedNote.sky_chapter.signal_label}</strong>
            <p>{awakenedNote.sky_chapter.summary}</p>
            <small>{awakenedNote.sky_chapter.disclaimer}</small>
          </section> : null}
          {error ? <p className="inline-error" role="status">{error}</p> : null}
          <Link className="electric-button" to="/home">{readingGift ? "Về Home mở món quà" : "Xem note hôm nay"}</Link>
          {submitMutation.data?.profile_level === 3 ? <Link className="outline-button" to="/natal"><Sparkle /> Bạn có muốn hiểu mình hơn?</Link> : null}
          <Link className="outline-button" to="/insights/current-sky"><MoonStars /> Mở Bầu trời hiện tại</Link>
        </div> : null}
      </div>
    </main>
  );
}
