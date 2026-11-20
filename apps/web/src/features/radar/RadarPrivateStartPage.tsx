import { ArrowLeft, ArrowRight, Check, HeartStraight, LockKey, MapPin, ShieldCheck, Sparkle, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import {
  ApiProblem,
  crisisNoticeFrom,
  createPrivateRadarCheck,
  deleteRadarResult,
  getRadarConsentOptions,
  searchBirthPlaces,
  type PlaceResult,
  type RadarInvite,
  type RadarInviteFirstSentence,
  type RadarVoice,
} from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { BirthTimeInput } from "../../shared/ui/BirthTimeInput";
import "../matching/matching.css";
import "./radar.css";
import { RadarEraseSheet } from "./RadarEraseSheet";
import { useRadarEraseTarget } from "./useRadarEraseTarget";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { RadarPrecisionGate } from "./RadarPrecisionGate";
import { formatRadarExpiry, radarContextLabel, RADAR_CONTEXT_OPTIONS, RADAR_VOICE_OPTIONS } from "./radarOptions";
import { markRadarOwnerReturn } from "./radarOwnerReturn";
import { RADAR_HISTORY_QUERY_KEY, useRadarOwnerBinding } from "./useRadarOwnerBinding";
import { useRadarCreateKey, useRadarHistory } from "./useRadarHistory";
import { useRadarOwnerPrecision } from "./useRadarOwnerPrecision";
import { adultBirthDate } from "./radarBirthDate";

const INVITE_FIRST_OWNER_KEYS: RadarInviteFirstSentence[] = ["owner-invite-heading", "owner-invite-body", "owner-attest-label", "owner-attest-help", "owner-date-only-storage"];

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
  const [birthTimeMode, setBirthTimeMode] = useState<"exact" | "unknown">("exact");
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
  const history = useRadarHistory(owner.epoch, owner.isReady, "private_check");
  const erase = useRadarEraseTarget(owner);
  const retryKey = useRadarCreateKey(owner.epoch);
  const precision = useRadarOwnerPrecision(owner);
  // AL1: the invite-first screens show only when the server has them on and returns every
  // owner-approved sentence. Anything else keeps today's form.
  const consent = useQuery({ queryKey: ["radar-consent-options"], queryFn: ({ signal }) => getRadarConsentOptions(signal), retry: false, staleTime: 60_000 });
  const sentences = consent.data?.invite_first ? consent.data.sentences : null;
  const inviteFirst = Boolean(sentences && INVITE_FIRST_OWNER_KEYS.every((key) => sentences[key]));
  const ownerDateOnly = precision === "needs_birth_time";
  // A date-only owner's pair is read from both dates, so the other person's time and place are not asked.
  const fullerInput = inviteFirst ? Boolean(selectedPlace) && !ownerDateOnly : true;

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
      setBirthTimeMode("exact");
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
    birthDate
    && (!fullerInput || birthTimeMode === "unknown" || /^([01]\d|2[0-3]):[0-5]\d$/.test(birthTime))
    && (!fullerInput || selectedPlace)
    && attested,
  ), [attested, birthDate, birthTime, birthTimeMode, fullerInput, selectedPlace]);

  const create = useMutation({
    mutationFn: () => {
      const dateOnly = inviteFirst && !fullerInput;
      const input = {
      // A name is optional: without one the history shows the relationship, e.g. "Đồng nghiệp".
      recipient_label: label.trim() || radarContextLabel(context),
      context,
      voice,
      birth_date: birthDate ?? "",
      birth_time_mode: dateOnly ? "date_only" as const : birthTimeMode,
      birth_time_local: !dateOnly && birthTimeMode === "exact" ? birthTime : null,
      place_id: dateOnly ? null : selectedPlace?.place_id ?? null,
      authorization_attested: attested,
      };
      const consentVersion = inviteFirst ? consent.data?.authorized_input_version : undefined;
      return createPrivateRadarCheck(input, retryKey.forDraft(input), consentVersion);
    },
    onSuccess: (result) => {
      retryKey.reset();
      void queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY, refetchType: "none" });
      void navigate(`/radar/result/${result.request_id}`, { replace: true });
    },
    onError: (error) => {
      const notice = crisisNoticeFrom(error);
      if (notice) setMessage(notice);
      else if (error instanceof ApiProblem && error.status === 429) {
        setMessage(error.code === "RADAR_LIMIT_REACHED" ? "Bạn đã giữ 100 lần Radar. Xoá một kết quả cũ để check thêm nhé." : "Bạn đang check hơi nhanh. Chờ một phút rồi thử lại nhé.");
      } else if (error instanceof ApiProblem && error.code === "RADAR_IDEMPOTENCY_CONFLICT") {
        retryKey.reset();
        setMessage("Thông tin hoặc chart đã đổi. Kiểm tra lại rồi bấm check nhé.");
      } else if (error instanceof ApiProblem && error.status === 409) {
        setMessage("Chart của bạn còn thiếu giờ hoặc nơi sinh. Thêm một lần rồi quay lại đây nhé.");
      } else {
        setMessage("Chưa xem được kết quả. Kiểm tra ngày, giờ và nơi sinh rồi thử lại nhé.");
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
  const startOwnerProfile = () => markRadarOwnerReturn("private");
  const privateHistory = history.items;
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
  const showForm = ownerReady && (precision === "ready" || (inviteFirst && ownerDateOnly));

  return <main className="app-page matching-page radar-page radar-start">
    <header className="matching-header"><button aria-label="Quay lại" className="radar-back" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><BrandMark /><span className="matching-signal"><HeartStraight weight="fill" /> xem riêng</span></header>
    <RadarFlowSteps current={2} />
    <section className="matching-hero matching-hero--compact radar-private-hero"><p className="eyebrow">Hợp gu 1:1 · không gửi thông báo</p><h1>Xem hợp gu với một người bạn đã biết.</h1><p>Bạn nhập thông tin sinh đã được họ cho phép dùng. Lá chỉ tính trong lần này—không tạo hồ sơ và không đưa họ vào danh sách tìm kiếm.</p></section>

    {owner.isError ? <section className="radar-public__card radar-owner-gate"><Sparkle /><h2>{owner.error instanceof ApiProblem && owner.error.status === 401 ? "Chart của bạn cần có trước." : "Chưa nối lại được phiên riêng."}</h2><p>{owner.error instanceof ApiProblem && owner.error.status === 401 ? "Chưa cần tài khoản. Tạo chart riêng, thêm giờ và nơi sinh rồi Lá đưa bạn quay lại Radar." : "Dữ liệu cũ vẫn được giữ kín. Kiểm tra mạng rồi thử nối lại nhé."}</p>{owner.error instanceof ApiProblem && owner.error.status === 401 ? <Link className="matching-primary" onClick={startOwnerProfile} to="/consent">Tạo chart của mình <ArrowRight /></Link> : <button className="matching-primary" onClick={owner.retry} type="button">Thử nối lại <ArrowRight /></button>}</section> : null}

    {ownerReady && precision === "needs_birth_time" && !inviteFirst ? <><RadarPrecisionGate onStart={startOwnerProfile} /><div className="radar-no-permission"><ShieldCheck /><p><strong>Chưa được phép dùng dữ liệu?</strong><br />Để người ấy tự nhập và tự đồng ý.</p><Link to="/radar/invite">Mời họ tự nhập</Link></div></> : null}

    {showForm && inviteFirst && sentences ? <section aria-labelledby="radar-invite-first-heading" className="radar-invite-first"><ShieldCheck /><div><h2 id="radar-invite-first-heading">{sentences["owner-invite-heading"]}</h2><p>{sentences["owner-invite-body"]}</p></div><Link className="matching-primary" to="/radar/invite">Gửi link mời <ArrowRight /></Link></section> : null}

    {showForm ? <form className="radar-create radar-private-form" onSubmit={submit}>
      <div className="radar-form-heading"><span>01</span><div><strong>Người bạn muốn check</strong><p>Thông tin này không được gửi cho người ấy.</p></div></div>
      <label><span>Tên gọi để bạn dễ nhớ (không bắt buộc)</span><input autoComplete="off" maxLength={40} onChange={(event) => setLabel(event.target.value)} placeholder="Ví dụ: An, Mèo, người hay seen…" value={label} /></label>
      <fieldset><legend>Hai bạn đang là…</legend><div className="radar-contexts">{RADAR_CONTEXT_OPTIONS.map(([value, text]) => <button aria-pressed={context === value} className={context === value ? "is-selected" : ""} key={value} onClick={() => setContext(value)} type="button">{text}</button>)}</div></fieldset>
      <details className="radar-voice-disclosure"><summary>Giọng đọc · {RADAR_VOICE_OPTIONS.find(([value]) => value === voice)?.[1]}</summary><fieldset><legend>Bạn muốn Radar nói kiểu nào?</legend><div className="radar-voices">{RADAR_VOICE_OPTIONS.map(([value, title, description]) => <button aria-pressed={voice === value} className={voice === value ? "is-selected" : ""} key={value} onClick={() => setVoice(value)} type="button"><strong>{title}</strong><small>{description}</small></button>)}</div></fieldset></details>

      {inviteFirst ? <div className="radar-form-heading"><span>02</span><div><strong>Hoặc nhập ngày sinh của người ấy</strong><p>Không cần giờ hay nơi sinh. Có thì bản đọc đủ hơn.</p></div></div> : null}
      {!inviteFirst ? <>
      <div className="radar-form-heading"><span>02</span><div><strong>Thông tin sinh của họ</strong><p>Có giờ sinh chính xác thì bản đọc đủ hơn. Không rõ giờ vẫn xem được; Lá sẽ bỏ các phần cần giờ sinh.</p></div></div>
      <div className="radar-birth-grid">
        <fieldset className="radar-date-fieldset"><legend>Ngày sinh</legend><div className="radar-date-fields"><label><span>Ngày</span><input aria-label="Ngày sinh — ngày" inputMode="numeric" maxLength={2} onChange={(event) => setBirthDay(event.target.value.replace(/\D/g, ""))} placeholder="DD" required value={birthDay} /></label><i>/</i><label><span>Tháng</span><input aria-label="Ngày sinh — tháng" inputMode="numeric" maxLength={2} onChange={(event) => setBirthMonth(event.target.value.replace(/\D/g, ""))} placeholder="MM" required value={birthMonth} /></label><i>/</i><label><span>Năm</span><input aria-label="Ngày sinh — năm" inputMode="numeric" maxLength={4} onChange={(event) => setBirthYear(event.target.value.replace(/\D/g, ""))} placeholder="YYYY" required value={birthYear} /></label></div></fieldset>
        <fieldset className="radar-time-fieldset"><legend>Giờ sinh</legend><BirthTimeInput mode={birthTimeMode} onModeChange={(mode) => { if (mode !== "approx_window") setBirthTimeMode(mode); if (mode === "unknown") setBirthTime(""); }} time={birthTime} onTimeChange={setBirthTime} modes={["exact", "unknown"]} unknownLabel="Không rõ giờ" unknownHelp="Lá sẽ bỏ các phần cần giờ sinh của người này." /></fieldset>
      </div>
      {(birthDay || birthMonth || birthYear) && !birthDate ? <p className="radar-field-help">Nhập một ngày hợp lệ của người từ 18 tuổi trở lên.</p> : null}
      <label><span>Thành phố / tỉnh nơi sinh</span><div className="radar-place-input"><MapPin /><input autoComplete="off" onChange={(event) => { setPlaceQuery(event.target.value); setSelectedPlace(null); setShowAllPlaces(false); }} placeholder="Gõ Hà Nội, Bình Dương…" required={!inviteFirst} value={placeQuery} /></div></label>
      <p className="radar-field-help">Dùng danh mục 34 tỉnh/thành hiện hành; vẫn nhận tên tỉnh trước sắp xếp.</p>
      <button className="radar-place-catalog-toggle" onClick={() => setShowAllPlaces((value) => !value)} type="button">{showAllPlaces ? "Thu gọn danh mục" : "Xem đủ 34 tỉnh/thành"}</button>
      {places.data?.length ? <div aria-label="Danh sách nơi sinh" className="radar-place-results">{places.data.map((place) => <button key={place.place_id} onClick={() => { setSelectedPlace(place); setPlaceQuery(place.display_name); setShowAllPlaces(false); queryClient.removeQueries({ queryKey: ["radar-places"] }); }} type="button"><strong>{place.display_name}</strong><span>{place.confidence === "former-province-centroid" ? "Tên địa phương trước sắp xếp" : "Danh mục hiện hành · 01/07/2025"}</span></button>)}</div> : null}
      {placeQuery.trim().length >= 2 && places.data?.length === 0 ? <p className="radar-field-help">Chưa thấy nơi này. Thử cả tên tỉnh hiện hành hoặc tên trước sắp xếp.</p> : null}

      </> : <>
        <fieldset className="radar-date-fieldset"><legend>Ngày sinh</legend><div className="radar-date-fields"><label><span>Ngày</span><input aria-label="Ngày sinh — ngày" inputMode="numeric" maxLength={2} onChange={(event) => setBirthDay(event.target.value.replace(/\D/g, ""))} placeholder="DD" required value={birthDay} /></label><i>/</i><label><span>Tháng</span><input aria-label="Ngày sinh — tháng" inputMode="numeric" maxLength={2} onChange={(event) => setBirthMonth(event.target.value.replace(/\D/g, ""))} placeholder="MM" required value={birthMonth} /></label><i>/</i><label><span>Năm</span><input aria-label="Ngày sinh — năm" inputMode="numeric" maxLength={4} onChange={(event) => setBirthYear(event.target.value.replace(/\D/g, ""))} placeholder="YYYY" required value={birthYear} /></label></div></fieldset>
      {(birthDay || birthMonth || birthYear) && !birthDate ? <p className="radar-field-help">Nhập một ngày hợp lệ của người từ 18 tuổi trở lên.</p> : null}
        {!ownerDateOnly ? <details className="radar-fuller-input"><summary>Thêm giờ và nơi sinh (không bắt buộc)</summary>
        <fieldset className="radar-time-fieldset"><legend>Giờ sinh</legend><BirthTimeInput mode={birthTimeMode} onModeChange={(mode) => { if (mode !== "approx_window") setBirthTimeMode(mode); if (mode === "unknown") setBirthTime(""); }} time={birthTime} onTimeChange={setBirthTime} modes={["exact", "unknown"]} unknownLabel="Không rõ giờ" unknownHelp="Lá sẽ bỏ các phần cần giờ sinh của người này." /></fieldset>
      <label><span>Thành phố / tỉnh nơi sinh</span><div className="radar-place-input"><MapPin /><input autoComplete="off" onChange={(event) => { setPlaceQuery(event.target.value); setSelectedPlace(null); setShowAllPlaces(false); }} placeholder="Gõ Hà Nội, Bình Dương…" required={!inviteFirst} value={placeQuery} /></div></label>
      <p className="radar-field-help">Dùng danh mục 34 tỉnh/thành hiện hành; vẫn nhận tên tỉnh trước sắp xếp.</p>
      <button className="radar-place-catalog-toggle" onClick={() => setShowAllPlaces((value) => !value)} type="button">{showAllPlaces ? "Thu gọn danh mục" : "Xem đủ 34 tỉnh/thành"}</button>
      {places.data?.length ? <div aria-label="Danh sách nơi sinh" className="radar-place-results">{places.data.map((place) => <button key={place.place_id} onClick={() => { setSelectedPlace(place); setPlaceQuery(place.display_name); setShowAllPlaces(false); queryClient.removeQueries({ queryKey: ["radar-places"] }); }} type="button"><strong>{place.display_name}</strong><span>{place.confidence === "former-province-centroid" ? "Tên địa phương trước sắp xếp" : "Danh mục hiện hành · 01/07/2025"}</span></button>)}</div> : null}
      {placeQuery.trim().length >= 2 && places.data?.length === 0 ? <p className="radar-field-help">Chưa thấy nơi này. Thử cả tên tỉnh hiện hành hoặc tên trước sắp xếp.</p> : null}

        </details> : null}
      </>}
      {inviteFirst && sentences && !fullerInput ? <div className="radar-consent-note radar-transient-note"><LockKey /><p>{sentences["owner-date-only-storage"]}</p></div> : null}
      {!inviteFirst || fullerInput ? <>
      <div className="radar-consent-note radar-transient-note"><LockKey /><p><strong>Ngày, giờ và nơi sinh không được lưu.</strong><br />Server chỉ giữ dữ liệu bạn có trong bộ nhớ để tính, rồi bỏ ngay. Kết quả rút gọn được mã hóa và chỉ giữ 24 giờ để bạn mở lại; sau đó tự xoá. Bạn có thể xoá sớm hơn.</p></div>
      </> : null}
      {inviteFirst && sentences ? <div className="radar-attestation"><input aria-label={sentences["owner-attest-label"]} checked={attested} id="radar-permission" onChange={(event) => setAttested(event.target.checked)} type="checkbox" /><label htmlFor="radar-permission"><strong>{sentences["owner-attest-label"]}</strong><small>{sentences["owner-attest-help"]}</small></label></div> : <>
      <div className="radar-attestation"><input aria-label="Xác nhận đã được phép dùng thông tin sinh" checked={attested} id="radar-permission" onChange={(event) => setAttested(event.target.checked)} type="checkbox" /><label htmlFor="radar-permission"><strong>Tôi xác nhận người này đã cho phép tôi dùng thông tin sinh của họ để xem Radar.</strong><small>Nếu chưa được phép, đừng nhập hộ. Bạn có thể mời họ tự nhập ở lựa chọn phía dưới.</small></label></div>
      </>}
      <button className="matching-primary" disabled={!complete || create.isPending || owner.isPending} type="submit">{create.isPending ? "Đang xem hai lá số…" : "Xem hợp gu"}<ArrowRight /></button>
      {!inviteFirst ? <>
      <div className="radar-no-permission"><ShieldCheck /><p><strong>Chưa được phép dùng dữ liệu?</strong><br />Để người ấy tự nhập và tự đồng ý.</p><Link to="/radar/invite">Mời họ tự nhập</Link></div>
      </> : null}
    </form> : null}
    {(owner.isPending || (ownerReady && precision === "checking")) && !owner.isError ? <section aria-live="polite" className="radar-owner-refresh"><Sparkle className="matching-pulse" /><p>Đang mở hồ sơ của bạn…</p></section> : null}
    {message && !owner.isError ? <p className="matching-message" role="alert">{message}</p> : null}
    {create.isError && create.error instanceof ApiProblem && create.error.status === 409 && create.error.code !== "RADAR_IDEMPOTENCY_CONFLICT" ? <Link className="matching-secondary" onClick={startOwnerProfile} to="/birth-time">Thêm giờ & nơi sinh của mình</Link> : null}

    {ownerReady ? <section className="radar-history" id="radar-history"><p className="eyebrow">Những người bạn đã xem gần đây</p>{privateHistory.length ? privateHistory.map((item) => <article key={item.id}><span className={`radar-status is-${item.status}`}>{item.status === "completed" ? <Check /> : <HeartStraight />}</span><div><strong>{item.recipient_label}</strong><p>{item.status === "completed" ? `Tự xoá lúc ${formatRadarExpiry(item.expires_at)}` : "Kết quả đã hết hạn"}</p></div>{item.status === "completed" ? <Link to={`/radar/result/${item.id}`}>Mở</Link> : null}<button aria-label={`Xóa kết quả ${item.recipient_label}`} disabled={remove.isPending} onClick={() => erase.request(item.id, item.recipient_label)} type="button"><Trash /></button></article>) : <p className="radar-history__empty">Chưa có bản đọc nào. Kết quả đầu tiên sẽ nằm ở đây để bạn mở lại.</p>}</section> : null}
    {ownerReady && history.hasNextPage ? <button className="matching-secondary" disabled={history.isFetchingNextPage} onClick={() => void history.fetchNextPage()} type="button">{history.isFetchingNextPage ? "Đang tải…" : "Xem thêm kết quả"}</button> : null}
    {ownerReady && history.isError ? <p role="alert">Chưa tải được lịch sử. <button onClick={() => void history.refetch()} type="button">Thử lại</button></p> : null}
    <RadarEraseSheet body="Bản đọc này sẽ không còn mở được, kể cả từ lịch sử. Việc này không hoàn tác được." erase={erase} onConfirm={(id) => remove.mutate(id)} pending={remove.isPending} title={(name) => `Xoá kết quả với ${name}?`} />
  </main>;
}
