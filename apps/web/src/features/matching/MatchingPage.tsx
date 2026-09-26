import {
  ArrowRight,
  Check,
  Circle,
  EyeSlash,
  HeartStraight,
  LockKey,
  MapPin,
  PencilSimple,
  ShieldCheck,
  Sparkle,
  UserCircleCheck,
  Waveform,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  ApiProblem,
  claimOwner,
  getMatchingReadiness,
  grantMatchingConsent,
  saveMatchingProfile,
  setMatchingPoolMembership,
  withdrawMatchingConsent,
  type GenderPreference,
  type MatchingGender,
  type MatchingIntent,
  type MatchingProfile,
  type WeeklyIntent,
} from "../../shared/api/client";
import { markMatchingIntroConverted } from "../../shared/storage/matchingIntroExposure";
import { AppNav } from "../../shared/ui/AppNav";
import { AppSheet } from "../../shared/ui/AppSheet";
import { BrandMark } from "../../shared/ui/BrandMark";
import { checkCopy, deriveMatchingDeck, type MatchingNextAction } from "./readiness";
import "./matching.css";

const intentOptions: Array<[MatchingIntent, string, string]> = [
  ["dating", "Hẹn hò", "muốn xem một kết nối có thể đi xa tới đâu"],
  ["friendship", "Bạn mới", "một người nói chuyện hợp và không gượng"],
  ["open", "Để mở", "chưa đóng khung, nhưng vẫn có ranh giới rõ"],
];

const weeklyOptions: Array<[WeeklyIntent, string]> = [
  ["de_noi_chuyen", "Dễ nói chuyện"],
  ["di_cham", "Đi chậm"],
  ["goc_moi", "Góc mới"],
  ["de_la_can", "Để Lá cân"],
];

const regionOptions: Array<[string, string]> = [
  ["ho-chi-minh", "TP. Hồ Chí Minh"],
  ["ha-noi", "Hà Nội"],
  ["da-nang", "Đà Nẵng"],
  ["can-tho", "Cần Thơ"],
];

type ActiveSheet = "profile" | "consent" | "verification" | null;

export function MatchingPage() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const startWithProfile = searchParams.get("start") === "profile";
  const autoClaimStarted = useRef(false);
  const query = useQuery({
    queryKey: ["matching-readiness"],
    queryFn: ({ signal }) => getMatchingReadiness(signal),
    retry: false,
  });
  const needsOwner = query.error instanceof ApiProblem && query.error.code === "OWNER_REQUIRED";
  const needsBirth = query.error instanceof ApiProblem && query.error.status === 404;
  const [activeSheet, setActiveSheet] = useState<ActiveSheet>(null);
  const [confirmDiscard, setConfirmDiscard] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [intent, setIntent] = useState<MatchingIntent>("open");
  const [genderIdentity, setGenderIdentity] = useState<MatchingGender>("nonbinary");
  const [genderPreference, setGenderPreference] = useState<GenderPreference>("everyone");
  const [minAge, setMinAge] = useState(22);
  const [maxAge, setMaxAge] = useState(35);
  const [regionCode, setRegionCode] = useState("");
  const [weeklyIntent, setWeeklyIntent] = useState<WeeklyIntent>("de_la_can");
  const [message, setMessage] = useState<string | null>(null);

  const setDraftFromProfile = (profile: MatchingProfile | null) => {
    setDisplayName(profile?.display_name ?? "");
    setIntent(profile?.intent ?? "open");
    setGenderIdentity(profile?.gender_identity ?? "nonbinary");
    setGenderPreference(profile?.gender_preference ?? "everyone");
    setMinAge(profile?.min_age ?? 22);
    setMaxAge(profile?.max_age ?? 35);
    setRegionCode(profile?.region_code ?? "");
    setWeeklyIntent(profile?.weekly_intent ?? "de_la_can");
  };

  useEffect(() => {
    setDraftFromProfile(query.data?.profile ?? null);
  }, [query.data?.profile]);

  const profileDraft = useMemo(() => ({
    display_name: displayName.trim(),
    gender_identity: genderIdentity,
    intent,
    gender_preference: genderPreference,
    min_age: minAge,
    max_age: maxAge,
    region_code: regionCode,
    weekly_intent: weeklyIntent,
  }), [displayName, genderIdentity, intent, genderPreference, minAge, maxAge, regionCode, weeklyIntent]);
  const initialDraft = useMemo(() => profilePayload(query.data?.profile ?? null), [query.data?.profile]);
  const profileDirty = JSON.stringify(profileDraft) !== JSON.stringify(initialDraft);
  const profileReadyToSave = displayName.trim().length >= 2 && minAge <= maxAge && Boolean(regionCode);

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["matching-readiness"] });
  };
  const claim = useMutation({
    mutationFn: claimOwner,
    onSuccess: refresh,
    onError: () => setMessage("Chưa giữ được phiên Vòng Lá. Thử lại khi có kết nối nhé."),
  });
  const save = useMutation({
    mutationFn: saveMatchingProfile,
    onSuccess: async () => {
      markMatchingIntroConverted();
      setActiveSheet(null);
      setConfirmDiscard(false);
      setMessage("Đã giữ ranh giới ghép. Chốt tiếp theo đã mở.");
      await refresh();
    },
    onError: () => setMessage("Chưa lưu được hồ sơ. Các lựa chọn vẫn ở đây để bạn thử lại."),
  });
  const consent = useMutation({
    mutationFn: (active: boolean) => active ? grantMatchingConsent() : withdrawMatchingConsent(),
    onSuccess: async (_data, active) => {
      setActiveSheet(null);
      setMessage(active ? "Đã cấp quyền riêng cho Vòng Lá." : "Đã thu hồi quyền ghép. Hồ sơ không còn đủ điều kiện vào pool.");
      await refresh();
    },
    onError: () => setMessage("Chưa cập nhật được quyền ghép lúc này."),
  });
  const membership = useMutation({
    mutationFn: setMatchingPoolMembership,
    onSuccess: async (_data, active) => {
      setMessage(active ? "Bạn đã vào vòng gần nhất." : "Bạn đã rời vòng. Không ai nhận được thông báo.");
      await refresh();
    },
    onError: (error) => setMessage(error instanceof ApiProblem && error.code === "MATCHING_NOT_READY"
      ? "Một chốt an toàn vừa thay đổi. Lá chưa đưa hồ sơ vào vòng."
      : "Chưa cập nhật được trạng thái tham gia."),
  });
  const runOwnerClaim = claim.mutate;

  useEffect(() => {
    if (!startWithProfile || !needsOwner || autoClaimStarted.current) return;
    autoClaimStarted.current = true;
    runOwnerClaim();
  }, [needsOwner, runOwnerClaim, startWithProfile]);

  useEffect(() => {
    if (!startWithProfile || !query.data || activeSheet !== null) return;
    if (!query.data.profile) setActiveSheet("profile");
    setSearchParams({}, { replace: true });
  }, [activeSheet, query.data, setSearchParams, startWithProfile]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    save.mutate(profileDraft);
  };

  const requestCloseSheet = () => {
    if (activeSheet === "profile" && profileDirty && !confirmDiscard) {
      setConfirmDiscard(true);
      return;
    }
    if (activeSheet === "profile" && confirmDiscard) {
      setConfirmDiscard(false);
      return;
    }
    setActiveSheet(null);
  };

  if (query.isLoading) {
    return <main className="matching-page matching-page--loading"><Waveform className="matching-pulse" /><p>Đang dò điều kiện an toàn…</p></main>;
  }

  if (needsOwner) {
    if (startWithProfile && !claim.isError) {
      return <main className="matching-page matching-page--loading"><Waveform className="matching-pulse" /><p>Đang mở hồ sơ ghép…</p></main>;
    }
    return <main className="app-page matching-page">
      <header className="matching-header"><BrandMark /><span className="matching-signal"><Circle weight="fill" /> private</span></header>
      <section className="matching-hero matching-hero--gate">
        <span className="matching-orbit"><HeartStraight weight="duotone" /></span>
        <p className="eyebrow">Vòng Lá · chỉ mở khi bạn chọn</p>
        <h1>Năm kiểu kết nối.<br />Không phải bảng xếp hạng người.</h1>
        <p>Mỗi tối thứ Bảy, Lá thử tìm năm nhịp khác nhau từ chart thật và ranh giới do chính bạn đặt.</p>
      </section>
      <div className="matching-value-grid">
        <article><EyeSlash /><strong>Request kín · chặng sau</strong><span>Khi ghép mở, chỉ lộ nếu hai người cùng chọn.</span></article>
        <article><ShieldCheck /><strong>Bạn giữ quyền</strong><span>Rời pool, block hoặc thu hồi consent bất cứ lúc nào.</span></article>
      </div>
      <section className="matching-account-gate">
        <LockKey /><div><strong>Đây mới là lúc cần xác nhận thiết bị</strong><p>Daily Note vẫn dùng như khách. Vòng Lá cần một hồ sơ riêng ổn định để giữ ranh giới và các chốt an toàn; ghép và mutual là chặng sau.</p></div>
      </section>
      <button className="matching-primary" disabled={claim.isPending} onClick={() => claim.mutate()} type="button">{claim.isPending ? "Đang giữ phiên…" : "Bắt đầu chuẩn bị"}<ArrowRight /></button>
      <Link className="matching-secondary" to="/home">Chưa tham gia lúc này</Link>
      {message ? <p className="matching-message" role="status">{message}</p> : null}
      <AppNav />
    </main>;
  }

  if (needsBirth || query.isError || !query.data) {
    return <main className="app-page matching-page"><header className="matching-header"><BrandMark /></header><section className="matching-empty"><Sparkle /><p className="eyebrow">Thiếu một lớp nền</p><h1>Vòng Lá cần biết chiếc Lá của bạn trước.</h1><p>Hoàn thiện ngày, giờ và nơi sinh rồi quay lại. Đây là điều kiện để không ghép bằng vài câu chung chung.</p><Link className="matching-primary" to="/birth-time">Hoàn thiện Lá <ArrowRight /></Link></section><AppNav /></main>;
  }

  const readiness = query.data;
  const deck = deriveMatchingDeck(readiness);
  const consented = readiness.consent_version === "matching-v1";
  const pendingSheet = save.isPending || consent.isPending;

  const openSheet = (sheet: Exclude<ActiveSheet, null>) => {
    setMessage(null);
    setConfirmDiscard(false);
    setActiveSheet(sheet);
  };

  return <main className="app-page matching-page matching-page--deck">
    <header className="matching-header"><BrandMark /><span className="matching-signal"><Circle weight="fill" /> Vòng Lá</span></header>
    <section className="matching-hero matching-hero--compact">
      <p className="eyebrow">Trạm ghép · riêng và có chủ đích</p>
      <h1>Năm nhịp hợp.<br />Không chấm điểm người.</h1>
      <p>Chart gợi cách hai người vận hành; ranh giới của bạn mới quyết định ai được bước vào.</p>
    </section>

    <section className="matching-deck" aria-labelledby="matching-deck-title">
      <div className="matching-deck__progress-head">
        <span>{deck.completed}/5 chốt</span>
        <span>{deck.completed === 5 ? "đủ điều kiện" : "đang chuẩn bị"}</span>
      </div>
      <div
        aria-label={`${deck.completed} trên 5 điều kiện đã hoàn tất`}
        aria-valuemax={5}
        aria-valuemin={0}
        aria-valuenow={deck.completed}
        className="matching-signal-progress"
        role="progressbar"
      >
        {deck.orderedChecks.map((check, index) => <span className={check.complete ? "is-complete" : check.key === deck.blocker ? "is-current" : ""} key={check.key}><i />{index < 4 ? <b /> : null}</span>)}
      </div>
      <div className="matching-deck__next">
        <span className="matching-deck__icon">{deck.completed === 5 ? <Check weight="bold" /> : <span>{String(deck.completed + 1).padStart(2, "0")}</span>}</span>
        <div><p className="eyebrow">{deck.completed === 5 ? "Trạng thái" : "Chốt tiếp theo"}</p><h2 id="matching-deck-title">{deck.title}</h2><p>{deck.detail}</p></div>
      </div>
      <PrimaryAction action={deck.action} disabled={membership.isPending} label={deck.ctaLabel} onMembership={(active) => membership.mutate(active)} onOpen={openSheet} />
      <details className="matching-conditions">
        <summary>Xem đủ 5 điều kiện</summary>
        <div>
          {deck.orderedChecks.map((check) => <article className={check.complete ? "is-complete" : ""} key={check.key}>
            <span>{check.complete ? <Check weight="bold" /> : <Circle />}</span>
            <div><strong>{checkCopy[check.key].title}</strong><p>{checkCopy[check.key].detail}</p></div>
            {check.key === "matching_consent" && check.complete ? <button className="matching-inline-action" onClick={() => openSheet("consent")} type="button">Quản lý</button> : null}
            {check.key === "photo_verification" && check.complete ? <button className="matching-inline-action" onClick={() => openSheet("verification")} type="button">Xem</button> : null}
          </article>)}
        </div>
      </details>
    </section>

    {readiness.profile ? <section className="matching-receipt" aria-label="Hồ sơ ghép hiện tại">
      <UserCircleCheck />
      <div><small>Hồ sơ ghép</small><strong>{readiness.profile.display_name}</strong><p>{intentOptions.find(([value]) => value === readiness.profile?.intent)?.[1]} · {readiness.profile.min_age}–{readiness.profile.max_age} · {regionOptions.find(([value]) => value === readiness.profile?.region_code)?.[1] ?? readiness.profile.region_code.replaceAll("-", " ")}</p></div>
      <button onClick={() => openSheet("profile")} type="button"><PencilSimple aria-hidden="true" /> Sửa</button>
    </section> : null}

    <section className="matching-promise">
      <EyeSlash /><div><strong>Ghép và mutual chưa mở ở bản này</strong><p>Khi chặng đó mở, request sẽ kín và chỉ lộ nếu hai người cùng chọn; không hiển thị vị trí chính xác.</p></div>
    </section>
    {message ? <p className="matching-message" role="status">{message}</p> : null}

    <AppSheet
      closeDisabled={save.isPending}
      eyebrow="Hồ sơ ghép · bạn đặt ranh giới"
      onClose={requestCloseSheet}
      open={activeSheet === "profile"}
      title={confirmDiscard ? "Bỏ những gì vừa sửa?" : readiness.profile ? "Sửa hồ sơ ghép" : "Tạo hồ sơ ghép"}
    >
      {confirmDiscard ? <div className="matching-discard">
        <p>Những thay đổi chưa được gửi. Bạn muốn quay lại chỉnh hay bỏ chúng?</p>
        <button className="matching-primary" onClick={() => setConfirmDiscard(false)} type="button">Tiếp tục chỉnh</button>
        <button className="matching-secondary" onClick={() => { setDraftFromProfile(readiness.profile); setConfirmDiscard(false); setActiveSheet(null); }} type="button">Bỏ thay đổi</button>
      </div> : <form className="matching-form" onSubmit={submit}>
        <label><span>Tên hiển thị</span><input autoComplete="nickname" maxLength={32} minLength={2} onChange={(event) => setDisplayName(event.target.value)} placeholder="Tên gọi, không phải tên pháp lý" required value={displayName} /></label>
        <fieldset><legend>Bạn vào đây để…</legend><div className="matching-choice-grid">{intentOptions.map(([value, label, detail]) => <button aria-pressed={intent === value} className={intent === value ? "is-selected" : ""} key={value} onClick={() => setIntent(value)} type="button"><strong>{label}</strong><small>{detail}</small></button>)}</div></fieldset>
        <div className="matching-form__row"><label><span>Bạn tự mô tả</span><select onChange={(event) => setGenderIdentity(event.target.value as MatchingGender)} value={genderIdentity}><option value="woman">Nữ</option><option value="man">Nam</option><option value="nonbinary">Phi nhị nguyên</option></select></label><label><span>Muốn gặp</span><select onChange={(event) => setGenderPreference(event.target.value as GenderPreference)} value={genderPreference}><option value="everyone">Mọi giới</option><option value="women">Nữ</option><option value="men">Nam</option><option value="nonbinary">Phi nhị nguyên</option></select></label></div>
        <div className="matching-form__row"><label><span>Tuổi từ</span><input max={maxAge} min={18} onChange={(event) => setMinAge(Number(event.target.value))} type="number" value={minAge} /></label><label><span>Đến</span><input max={120} min={minAge} onChange={(event) => setMaxAge(Number(event.target.value))} type="number" value={maxAge} /></label></div>
        <div className="matching-form__field"><label htmlFor="matching-region"><span>Khu vực muốn kết nối</span></label><select aria-describedby="matching-region-note" id="matching-region" onChange={(event) => setRegionCode(event.target.value)} required value={regionCode}><option disabled value="">Chọn thành phố</option>{regionOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><small id="matching-region-note">Chỉ lưu thành phố; không dùng GPS hoặc hiển thị khoảng cách số.</small></div>
        <fieldset><legend>Tuần này bạn muốn</legend><div className="matching-weekly">{weeklyOptions.map(([value, label]) => <button aria-pressed={weeklyIntent === value} className={weeklyIntent === value ? "is-selected" : ""} key={value} onClick={() => setWeeklyIntent(value)} type="button">{label}</button>)}</div><small>Chỉ đổi thứ tự ưu tiên trong nhóm đã qua điều kiện cứng.</small></fieldset>
        {save.isError ? <p className="matching-sheet-error" role="alert">Chưa lưu được. Các lựa chọn vẫn ở đây để bạn thử lại.</p> : null}
        <div className="matching-form__submit">
          <small>{profileReadyToSave ? "Bạn có thể sửa hoặc rút hồ sơ bất cứ lúc nào." : "Điền tên, khoảng tuổi hợp lệ và thành phố để lưu."}</small>
          <button className="matching-primary" disabled={save.isPending} type="submit">{save.isPending ? "Đang lưu…" : readiness.profile ? "Lưu thay đổi" : "Lưu hồ sơ ghép"}<ArrowRight /></button>
        </div>
      </form>}
    </AppSheet>

    <AppSheet closeDisabled={consent.isPending} eyebrow="Quyền riêng · matching-v1" onClose={requestCloseSheet} open={activeSheet === "consent"} title="Dữ liệu nào được dùng cho Vòng Lá?">
      <div className="matching-consent-sheet">
        <ul><li>Điều kiện cứng bạn tự chọn trong hồ sơ ghép.</li><li>Synastry rút gọn thành evidence; ranker không nhận ngày, giờ hay nơi sinh thô.</li><li>Block, số lần xuất hiện và trạng thái an toàn.</li></ul>
        <p className="matching-fineprint"><MapPin /> Không GPS, không khoảng cách số, không mood hoặc nội dung chat để xếp hạng.</p>
        <p className="matching-sheet-note">Bạn có thể thu hồi bất cứ lúc nào. Thu hồi sẽ đưa hồ sơ ra khỏi trạng thái sẵn sàng.</p>
        {consent.isError ? <p className="matching-sheet-error" role="alert">Chưa cập nhật được quyền ghép. Không có trạng thái nào được tự đổi.</p> : null}
        <button className={consented ? "matching-danger-action" : "matching-primary"} disabled={consent.isPending} onClick={() => consent.mutate(!consented)} type="button">{consent.isPending ? "Đang cập nhật…" : consented ? "Thu hồi quyền ghép" : "Tôi đồng ý dùng dữ liệu cho Vòng Lá"}</button>
      </div>
    </AppSheet>

    <AppSheet closeDisabled={pendingSheet} eyebrow="Chốt an toàn cuối" onClose={requestCloseSheet} open={activeSheet === "verification"} title="Xác minh ảnh trước khi vào pool">
      <div className="matching-verification-sheet">
        <span className={`matching-verification-state is-${readiness.verification_status}`}><ShieldCheck /><strong>{verificationLabel(readiness.verification_status)}</strong></span>
        <p>Ảnh chỉ phục vụ kiểm tra người thật và an toàn. Ảnh không đi vào chart, synastry hoặc ranker.</p>
        {readiness.verification_reason_code ? <p className="matching-sheet-note">Mã lý do: {readiness.verification_reason_code}</p> : null}
        <div className="matching-release-note"><LockKey /><p>Bản review chưa nối kho ảnh riêng và moderation thật, nên Lá cố ý không cho tự duyệt hoặc upload giả. Chốt này vẫn đóng cho tới khi provider an toàn được tích hợp.</p></div>
        <button className="matching-secondary" onClick={() => setActiveSheet(null)} type="button">Đã hiểu</button>
      </div>
    </AppSheet>
    <AppNav />
  </main>;
}

function PrimaryAction({
  action,
  disabled,
  label,
  onMembership,
  onOpen,
}: {
  action: MatchingNextAction;
  disabled: boolean;
  label: string;
  onMembership: (active: boolean) => void;
  onOpen: (sheet: Exclude<ActiveSheet, null>) => void;
}) {
  if (action === "birth") return <Link className="matching-primary" to="/birth-time">{label}<ArrowRight /></Link>;
  if (action === "profile" || action === "consent" || action === "verification") return <button className="matching-primary" onClick={() => onOpen(action)} type="button">{label}<ArrowRight /></button>;
  if (action === "join" || action === "leave") return <button className="matching-primary" disabled={disabled} onClick={() => onMembership(action === "join")} type="button">{label}<ArrowRight /></button>;
  return <button className="matching-primary" disabled type="button">{label}</button>;
}

function profilePayload(profile: MatchingProfile | null) {
  return {
    display_name: profile?.display_name.trim() ?? "",
    gender_identity: profile?.gender_identity ?? "nonbinary",
    intent: profile?.intent ?? "open",
    gender_preference: profile?.gender_preference ?? "everyone",
    min_age: profile?.min_age ?? 22,
    max_age: profile?.max_age ?? 35,
    region_code: profile?.region_code ?? "",
    weekly_intent: profile?.weekly_intent ?? "de_la_can",
  };
}

function verificationLabel(status: "not_started" | "pending" | "pass" | "fail") {
  if (status === "pending") return "Đang chờ duyệt";
  if (status === "pass") return "Đã xác minh";
  if (status === "fail") return "Cần xác minh lại";
  return "Chưa bắt đầu";
}
