import { ArrowLeft, ArrowRight, Check, HeartStraight, LockKey, MapPin, ShieldCheck, Sparkle, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import {
  ApiProblem,
  createPrivateRadarCheck,
  deleteRadarResult,
  listRadarInvites,
  searchBirthPlaces,
  type PlaceResult,
  type RadarInvite,
  type RadarVoice,
} from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { RADAR_CONTEXT_OPTIONS, RADAR_VOICE_OPTIONS } from "./radarOptions";
import { RADAR_HISTORY_QUERY_KEY, useRadarOwnerBinding } from "./useRadarOwnerBinding";

function adultBirthDate(day: string, month: string, year: string): string | null {
  if (!/^\d{1,2}$/.test(day) || !/^\d{1,2}$/.test(month) || !/^\d{4}$/.test(year)) return null;
  const dayValue = Number(day);
  const monthValue = Number(month);
  const yearValue = Number(year);
  const value = new Date(Date.UTC(yearValue, monthValue - 1, dayValue));
  if (value.getUTCDate() !== dayValue || value.getUTCMonth() !== monthValue - 1 || value.getUTCFullYear() !== yearValue) return null;
  const today = new Date();
  let age = today.getUTCFullYear() - yearValue;
  if (today.getUTCMonth() < monthValue - 1 || (today.getUTCMonth() === monthValue - 1 && today.getUTCDate() < dayValue)) age -= 1;
  if (age < 18 || age > 120) return null;
  return `${year}-${String(monthValue).padStart(2, "0")}-${String(dayValue).padStart(2, "0")}`;
}

export function RadarPrivateStartPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [label, setLabel] = useState("");
  const [context, setContext] = useState<RadarInvite["context"]>("crush");
  const [voice, setVoice] = useState<RadarVoice>("straight_warm");
  const [birthDay, setBirthDay] = useState("");
  const [birthMonth, setBirthMonth] = useState("");
  const [birthYear, setBirthYear] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [placeQuery, setPlaceQuery] = useState("");
  const [debouncedPlaceQuery, setDebouncedPlaceQuery] = useState("");
  const [showAllPlaces, setShowAllPlaces] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState<PlaceResult | null>(null);
  const [attested, setAttested] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const scrolledToHistory = useRef(false);
  const activeOwnerEpoch = useRef<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedPlaceQuery(placeQuery.trim()), 280);
    return () => window.clearTimeout(timer);
  }, [placeQuery]);

  const owner = useRadarOwnerBinding();
  const history = useQuery({
    queryKey: [...RADAR_HISTORY_QUERY_KEY, owner.epoch],
    queryFn: ({ signal }) => listRadarInvites(signal),
    enabled: owner.isReady,
    retry: false,
  });

  const effectivePlaceQuery = debouncedPlaceQuery.length >= 2 ? debouncedPlaceQuery : "";
  const places = useQuery({
    queryKey: ["radar-places", owner.epoch, showAllPlaces ? "all-current" : effectivePlaceQuery],
    queryFn: ({ signal }) => searchBirthPlaces(showAllPlaces ? "" : effectivePlaceQuery, signal),
    enabled: owner.isReady
      && (showAllPlaces || effectivePlaceQuery.length >= 2)
      && selectedPlace?.display_name !== debouncedPlaceQuery,
    gcTime: 0,
  });

  useEffect(() => () => {
    queryClient.removeQueries({ queryKey: ["radar-places"] });
  }, [owner.epoch, queryClient]);

  useEffect(() => {
    if (!owner.epoch) return;
    if (activeOwnerEpoch.current && activeOwnerEpoch.current !== owner.epoch) {
      setLabel("");
      setContext("crush");
      setVoice("straight_warm");
      setBirthDay("");
      setBirthMonth("");
      setBirthYear("");
      setBirthTime("");
      setPlaceQuery("");
      setDebouncedPlaceQuery("");
      setShowAllPlaces(false);
      setSelectedPlace(null);
      setAttested(false);
      setMessage(null);
    }
    activeOwnerEpoch.current = owner.epoch;
  }, [owner.epoch]);

  const birthDate = useMemo(
    () => adultBirthDate(birthDay, birthMonth, birthYear),
    [birthDay, birthMonth, birthYear],
  );
  const complete = useMemo(() => Boolean(
    label.trim() && birthDate && birthTime && selectedPlace && attested,
  ), [attested, birthDate, birthTime, label, selectedPlace]);

  const create = useMutation({
    mutationFn: () => createPrivateRadarCheck({
      recipient_label: label.trim(),
      context,
      voice,
      birth_date: birthDate ?? "",
      birth_time_local: birthTime,
      place_id: selectedPlace?.place_id ?? "",
      authorization_attested: attested,
    }),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY, refetchType: "none" });
      void navigate(`/radar/result/${result.request_id}`, { replace: true });
    },
    onError: (error) => {
      if (error instanceof ApiProblem && error.status === 409) {
        setMessage("Chart của bạn còn thiếu giờ hoặc nơi sinh. Thêm một lần rồi quay lại đây nhé.");
      } else {
        setMessage("Chưa bắt được Radar. Kiểm tra ngày, giờ và nơi sinh rồi thử lại nhé.");
      }
    },
  });
  const remove = useMutation({
    mutationFn: deleteRadarResult,
    onSuccess: (_data, requestId) => {
      queryClient.removeQueries({ queryKey: ["radar-result", owner.epoch, requestId] });
      void queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY });
    },
    onError: () => setMessage("Chưa xóa được kết quả. Dữ liệu vẫn còn nguyên; thử lại khi mạng ổn định."),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setMessage(null);
    if (complete) create.mutate();
  };
  const startOwnerProfile = () => sessionStorage.setItem("la-lanh-radar-owner-start", "1");
  const privateHistory = useMemo(
    () => history.data?.filter((item) => item.mode === "private_check") ?? [],
    [history.data],
  );
  useEffect(() => {
    if (location.hash !== "#radar-history") {
      scrolledToHistory.current = false;
      return;
    }
    if (!history.isFetching && !scrolledToHistory.current) {
      const target = document.getElementById("radar-history");
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        scrolledToHistory.current = true;
      }
    }
  }, [history.isFetching, location.hash]);

  const ownerReady = owner.isReady;

  return <main className="app-page matching-page radar-page radar-start">
    <header className="matching-header"><button aria-label="Quay lại" className="radar-back" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><BrandMark /><span className="matching-signal"><HeartStraight weight="fill" /> check kín</span></header>
    <RadarFlowSteps current={2} />
    <section className="matching-hero matching-hero--compact radar-private-hero"><p className="eyebrow">Radar 1:1 · không gửi thông báo</p><h1>Check kín một người bạn đã biết.</h1><p>Bạn nhập thông tin sinh đã được họ cho phép dùng. Lá chỉ tính trong lần này—không tạo hồ sơ và không đưa họ vào danh sách tìm kiếm.</p></section>

    {owner.isError ? <section className="radar-public__card radar-owner-gate"><Sparkle /><h2>{owner.error instanceof ApiProblem && owner.error.status === 401 ? "Chart của bạn cần có trước." : "Chưa nối lại được phiên riêng."}</h2><p>{owner.error instanceof ApiProblem && owner.error.status === 401 ? "Chưa cần tài khoản. Tạo chart riêng, thêm giờ và nơi sinh rồi Lá đưa bạn quay lại Radar." : "Dữ liệu cũ vẫn được giữ kín. Kiểm tra mạng rồi thử nối lại nhé."}</p>{owner.error instanceof ApiProblem && owner.error.status === 401 ? <Link className="matching-primary" onClick={startOwnerProfile} to="/consent">Tạo chart của mình <ArrowRight /></Link> : <button className="matching-primary" onClick={owner.retry} type="button">Thử nối lại <ArrowRight /></button>}</section> : null}

    {ownerReady ? <form className="radar-create radar-private-form" onSubmit={submit}>
      <div className="radar-form-heading"><span>01</span><div><strong>Người bạn muốn check</strong><p>Thông tin này không được gửi cho người ấy.</p></div></div>
      <label><span>Tên gọi để bạn dễ nhớ</span><input autoComplete="off" maxLength={40} onChange={(event) => setLabel(event.target.value)} placeholder="Ví dụ: An, Mèo, người hay seen…" required value={label} /></label>
      <fieldset><legend>Hai bạn đang là…</legend><div className="radar-contexts">{RADAR_CONTEXT_OPTIONS.map(([value, text]) => <button aria-pressed={context === value} className={context === value ? "is-selected" : ""} key={value} onClick={() => setContext(value)} type="button">{text}</button>)}</div></fieldset>
      <fieldset><legend>Bạn muốn Radar nói kiểu nào?</legend><div className="radar-voices">{RADAR_VOICE_OPTIONS.map(([value, title, description]) => <button aria-pressed={voice === value} className={voice === value ? "is-selected" : ""} key={value} onClick={() => setVoice(value)} type="button"><strong>{title}</strong><small>{description}</small></button>)}</div></fieldset>

      <div className="radar-form-heading"><span>02</span><div><strong>Thông tin sinh của họ</strong><p>Đủ giờ và nơi sinh giúp đọc Moon, Rising, House và các góc hai chart.</p></div></div>
      <div className="radar-birth-grid">
        <fieldset className="radar-date-fieldset"><legend>Ngày sinh</legend><div className="radar-date-fields"><label><span>Ngày</span><input aria-label="Ngày sinh — ngày" inputMode="numeric" maxLength={2} onChange={(event) => setBirthDay(event.target.value.replace(/\D/g, ""))} placeholder="DD" required value={birthDay} /></label><i>/</i><label><span>Tháng</span><input aria-label="Ngày sinh — tháng" inputMode="numeric" maxLength={2} onChange={(event) => setBirthMonth(event.target.value.replace(/\D/g, ""))} placeholder="MM" required value={birthMonth} /></label><i>/</i><label><span>Năm</span><input aria-label="Ngày sinh — năm" inputMode="numeric" maxLength={4} onChange={(event) => setBirthYear(event.target.value.replace(/\D/g, ""))} placeholder="YYYY" required value={birthYear} /></label></div></fieldset>
        <label><span>Giờ sinh chính xác</span><input onChange={(event) => setBirthTime(event.target.value)} required type="time" value={birthTime} /></label>
      </div>
      {(birthDay || birthMonth || birthYear) && !birthDate ? <p className="radar-field-help">Nhập một ngày hợp lệ của người từ 18 tuổi trở lên.</p> : null}
      <label><span>Thành phố / tỉnh nơi sinh</span><div className="radar-place-input"><MapPin /><input autoComplete="off" onChange={(event) => { setPlaceQuery(event.target.value); setSelectedPlace(null); setShowAllPlaces(false); }} placeholder="Gõ Hà Nội, Bình Dương…" required value={placeQuery} /></div></label>
      <p className="radar-field-help">Dùng danh mục 34 tỉnh/thành hiện hành; vẫn nhận tên tỉnh trước sắp xếp.</p>
      <button className="radar-place-catalog-toggle" onClick={() => setShowAllPlaces((value) => !value)} type="button">{showAllPlaces ? "Thu gọn danh mục" : "Xem đủ 34 tỉnh/thành"}</button>
      {places.data?.length ? <div aria-label="Danh sách nơi sinh" className="radar-place-results">{places.data.map((place) => <button key={place.place_id} onClick={() => { setSelectedPlace(place); setPlaceQuery(place.display_name); setShowAllPlaces(false); queryClient.removeQueries({ queryKey: ["radar-places"] }); }} type="button"><strong>{place.display_name}</strong><span>{place.confidence === "former-province-centroid" ? "Tên địa phương trước sắp xếp" : "Danh mục hiện hành · 01/07/2025"}</span></button>)}</div> : null}
      {placeQuery.trim().length >= 2 && places.data?.length === 0 ? <p className="radar-field-help">Chưa thấy nơi này. Thử cả tên tỉnh hiện hành hoặc tên trước sắp xếp.</p> : null}

      <div className="radar-consent-note radar-transient-note"><LockKey /><p><strong>Ngày, giờ và nơi sinh không được lưu.</strong><br />Server chỉ giữ chúng trong bộ nhớ để tính, rồi bỏ ngay. Lịch sử chỉ giữ kết quả rút gọn đã mã hóa trong 30 ngày.</p></div>
      <div className="radar-attestation"><input aria-label="Xác nhận đã được phép dùng thông tin sinh" checked={attested} id="radar-permission" onChange={(event) => setAttested(event.target.checked)} type="checkbox" /><label htmlFor="radar-permission"><strong>Tôi xác nhận người này đã cho phép tôi dùng thông tin sinh của họ để xem Radar.</strong><small>Nếu chưa được phép, đừng nhập hộ. Bạn có thể mời họ tự nhập ở lựa chọn phía dưới.</small></label></div>
      <button className="matching-primary" disabled={!complete || create.isPending || owner.isPending} type="submit">{create.isPending ? "Đang bắt hai tín hiệu…" : "Check kín ngay"}<ArrowRight /></button>
      <div className="radar-no-permission"><ShieldCheck /><p><strong>Chưa được phép dùng dữ liệu?</strong><br />Để người ấy tự nhập và tự đồng ý.</p><Link to="/radar/invite">Mời họ tự nhập</Link></div>
    </form> : null}
    {owner.isPending && !owner.isError ? <section aria-live="polite" className="radar-owner-refresh"><Sparkle className="matching-pulse" /><p>Đang nối Radar với phiên chart hiện tại…</p></section> : null}
    {message && !owner.isError ? <p className="matching-message" role="alert">{message}</p> : null}
    {create.isError && create.error instanceof ApiProblem && create.error.status === 409 ? <Link className="matching-secondary" onClick={startOwnerProfile} to="/birth-time">Thêm giờ & nơi sinh của mình</Link> : null}

    {ownerReady ? <section className="radar-history" id="radar-history"><p className="eyebrow">Những lần check gần đây</p>{privateHistory.length ? privateHistory.map((item) => <article key={item.id}><span className={`radar-status is-${item.status}`}>{item.status === "completed" ? <Check /> : <HeartStraight />}</span><div><strong>{item.recipient_label}</strong><p>{item.status === "completed" ? "Kết quả được giữ tối đa 30 ngày" : "Kết quả đã hết hạn"}</p></div>{item.status === "completed" ? <Link to={`/radar/result/${item.id}`}>Mở</Link> : null}<button aria-label={`Xóa kết quả ${item.recipient_label}`} onClick={() => remove.mutate(item.id)} type="button"><Trash /></button></article>) : <p className="radar-history__empty">Chưa có bản đọc nào. Kết quả đầu tiên sẽ nằm ở đây để bạn mở lại.</p>}</section> : null}
  </main>;
}
