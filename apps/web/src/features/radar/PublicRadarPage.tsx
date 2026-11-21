import { ArrowRight, EyeSlash, LockKey, ShieldCheck, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  acceptRadarInviteWithDate,
  ApiProblem,
  declineRadarInvite,
  getPublicRadarInvite,
  getRadarConsentOptions,
  type PublicRadarInvite,
  type RadarConsentOptions,
  type RadarInviteFirstSentence,
  withdrawRadarByInvite,
} from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { radarVoiceLabel, RADAR_PENDING_REQUEST_KEY } from "./radarOptions";
import { WithdrawSheet } from "./RadarReceivedPage";
import { adultBirthDate } from "./radarBirthDate";
import { evictRadarReadings, isTerminalDenial } from "./radarReadingCache";

const RECIPIENT_KEYS: RadarInviteFirstSentence[] = ["recipient-heading", "recipient-body", "recipient-consent", "recipient-decline"];

export function PublicRadarPage() {
  return <div className="app-shell ultraviolet-app"><PublicRadarContent /></div>;
}

function PublicRadarContent() {
  const navigate = useNavigate();
  const token = useParams().token ?? "";
  const query = useQuery({ queryKey: ["public-radar", token], queryFn: ({ signal }) => getPublicRadarInvite(token, signal), retry: false });
  // AL1: the one-field invite shows only when the server has it on with every sentence owner-approved.
  const consent = useQuery({ queryKey: ["radar-consent-options"], queryFn: ({ signal }) => getRadarConsentOptions(signal), retry: false, staleTime: 60_000 });
  const decline = useMutation({
    mutationFn: () => declineRadarInvite(query.data?.request_id ?? ""),
    onSuccess: () => {
      sessionStorage.removeItem(RADAR_PENDING_REQUEST_KEY);
      void navigate("/", { replace: true });
    },
  });
  if (query.isLoading || consent.isLoading) return <main className="matching-page matching-page--loading"><Sparkle className="matching-pulse" /><p>Đang mở lời mời…</p></main>;
  if (!query.data) return <UsedInvite token={token} />;
  const invite = query.data;
  const options = consent.data;
  if (options?.invite_first && RECIPIENT_KEYS.every((key) => options.sentences[key])) {
    return <OneFieldInvite decline={decline} invite={invite} options={options} />;
  }
  const continueFlow = () => sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, invite.request_id);
  return <main className="matching-page radar-public">
    <header className="matching-header"><BrandMark /><span className="matching-signal"><LockKey /> link riêng</span></header>
    <RadarFlowSteps current={1} />
    <section className="radar-public__signal"><span><Sparkle weight="fill" /></span><p className="eyebrow">Có người muốn xem hai bạn hợp nhau thế nào</p><h1>Hai bạn hợp nhau ở điểm nào? Mở ra xem cùng nhau nhé.</h1><p>Radar đặt lá số của hai người cạnh nhau, để xem cách hai bạn nói chuyện, cảm xúc, điểm hút nhau và chỗ dễ lệch nhau.</p></section>
    <section className="radar-public__card"><article><EyeSlash /><div><strong>Dữ liệu sinh không được trao đổi</strong><p>Người gửi không nhìn thấy ngày, giờ hay nơi sinh của bạn.</p></div></article><article><ShieldCheck /><div><strong>Bạn quyết định riêng cho lần này</strong><p>Chưa đồng ý thì Radar chưa tính. Bạn có thể rút kết quả sau đó.</p></div></article><article><LockKey /><div><strong>Giọng đọc: {radarVoiceLabel(invite.voice)}</strong><p>Bạn biết trước cách Radar sẽ nói. Đây không phải lời phán hay xác suất thành công.</p></div></article></section>
    <Link className="matching-primary" onClick={continueFlow} to="/radar/continue">Xem mình cần làm gì <ArrowRight /></Link>
    {decline.isError ? <p className="matching-message" role="alert">Chưa đóng được lời mời. Dữ liệu chưa thay đổi—bạn có thể thử lại.</p> : null}
    <button className="matching-secondary" disabled={decline.isPending} onClick={() => decline.mutate()} type="button">{decline.isPending ? "Đang đóng lời mời…" : decline.isError ? "Thử đóng lại" : "Không tham gia"}</button>
  </main>;
}

/** AL1 one-field invite: the other person types only their own birth date and consents. */
function OneFieldInvite({ invite, options, decline }: {
  invite: PublicRadarInvite;
  options: RadarConsentOptions;
  decline: { mutate: () => void; isPending: boolean; isError: boolean };
}) {
  const navigate = useNavigate();
  const [day, setDay] = useState("");
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");
  const [consented, setConsented] = useState(false);
  // Owner AR1 (21.11.2026): a separate box, unticked by default and ticked only by this person. No tick, nothing kept.
  const [keepWeekly, setKeepWeekly] = useState(false);
  const birthDate = adultBirthDate(day, month, year);
  const sentences = options.sentences;
  const weeklyOptIn = invite.weekly_offer === true && options.weekly === true ? options.weekly_sentences?.["recipient-optin"] : undefined;
  const accept = useMutation({
    mutationFn: () => acceptRadarInviteWithDate(invite.request_id, birthDate ?? "", options.date_consent_version, Boolean(weeklyOptIn) && keepWeekly),
    onSuccess: () => void navigate("/radar/receipt", { replace: true }),
  });
  const invalid = accept.error instanceof ApiProblem && accept.error.status === 422;
  return <main className="matching-page radar-public">
    <header className="matching-header"><BrandMark /><span className="matching-signal"><LockKey /> link riêng</span></header>
    <RadarFlowSteps current={2} />
    <section className="radar-public__signal"><span><Sparkle weight="fill" /></span><h1>{sentences["recipient-heading"]}</h1><p>{sentences["recipient-body"]}</p></section>
    <form className="radar-public__card radar-one-field" onSubmit={(event) => { event.preventDefault(); if (birthDate && consented) accept.mutate(); }}>
      <fieldset className="radar-date-fieldset"><legend>Ngày sinh của bạn</legend><div className="radar-date-fields"><label><span>Ngày</span><input aria-label="Ngày sinh của bạn — ngày" inputMode="numeric" maxLength={2} onChange={(event) => setDay(event.target.value.replace(/\D/g, ""))} placeholder="DD" required value={day} /></label><i>/</i><label><span>Tháng</span><input aria-label="Ngày sinh của bạn — tháng" inputMode="numeric" maxLength={2} onChange={(event) => setMonth(event.target.value.replace(/\D/g, ""))} placeholder="MM" required value={month} /></label><i>/</i><label><span>Năm</span><input aria-label="Ngày sinh của bạn — năm" inputMode="numeric" maxLength={4} onChange={(event) => setYear(event.target.value.replace(/\D/g, ""))} placeholder="YYYY" required value={year} /></label></div></fieldset>
      {(day || month || year) && !birthDate ? <p className="radar-field-help">Nhập một ngày hợp lệ của người từ 18 tuổi trở lên.</p> : null}
      <label className="consent-check"><input checked={consented} onChange={(event) => setConsented(event.target.checked)} type="checkbox" /><span>{sentences["recipient-consent"]}</span></label>
      {weeklyOptIn ? <label className="consent-check radar-weekly-optin"><input checked={keepWeekly} onChange={(event) => setKeepWeekly(event.target.checked)} type="checkbox" /><span>{weeklyOptIn}</span></label> : null}
      {invalid ? <p className="matching-message" role="alert">Kiểm tra lại ngày sinh rồi thử lại nhé.</p> : null}
      {accept.isError && !invalid ? <p className="matching-message" role="alert">Chưa xem được kết quả. Bạn chưa đồng ý gì cả, có thể thử lại.</p> : null}
      <button className="matching-primary" disabled={!birthDate || !consented || accept.isPending} type="submit">{accept.isPending ? "Đang xem hai lá số…" : "Đồng ý & xem kết quả"}<ArrowRight /></button>
    </form>
    <p className="radar-field-help">{sentences["recipient-decline"]}</p>
    {decline.isError ? <p className="matching-message" role="alert">Chưa đóng được lời mời. Dữ liệu chưa thay đổi—bạn có thể thử lại.</p> : null}
    <button className="matching-secondary" disabled={decline.isPending} onClick={() => decline.mutate()} type="button">{decline.isPending ? "Đang đóng lời mời…" : decline.isError ? "Thử đóng lại" : "Không tham gia"}</button>
  </main>;
}

// P09 D2: a used invite no longer previews. Whoever holds the link may still withdraw the result; this page
// never opens the reading, because the person who sent the link holds it too.
function UsedInvite({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);
  // The token names no result id, so every cached Radar reading is cleared, also when the outcome is unknown.
  const withdraw = useMutation({
    mutationFn: () => withdrawRadarByInvite(token),
    onSettled: () => evictRadarReadings(queryClient),
  });
  if (withdraw.isSuccess) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty"><div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/pair.webp" /></div><h1>Chart của bạn đã được rút.</h1><p>Kết quả chung đã bị xóa; cả hai phía đều không thể mở lại.</p><Link className="matching-primary" to="/radar">Về Radar Hợp Gu</Link></section></main>;
  return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty">
    <div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/moon.webp" /></div>
    <h1>Link này không còn mở lời mời.</h1>
    <p>Có thể link đã hết hạn, bị thu hồi hoặc đã được dùng. Nếu bạn là người đã đồng ý và muốn rút chart của mình khỏi kết quả, bạn có thể làm ngay tại đây. Trang này không mở lại bản đọc.</p>
    {withdraw.isError ? <p className="matching-message" role="alert">{isTerminalDenial(withdraw.error)
      ? "Link này không còn dùng được. Có thể kết quả đã hết hạn hoặc đã được rút trước đó."
      : "Chưa xác nhận được việc rút chart. Kiểm tra mạng rồi thử lại; nếu link báo không còn dùng được, có thể chart đã được rút."}</p> : null}
    <button className="matching-primary" disabled={withdraw.isPending} onClick={() => setConfirming(true)} type="button">{withdraw.isPending ? "Đang rút chart…" : "Rút chart khỏi kết quả"}</button>
    <Link className="matching-secondary" to="/radar/received">Xem kết quả bạn đã nhận</Link>
    <Link className="matching-secondary" to="/radar">Tìm hiểu Radar Hợp Gu</Link>
    <WithdrawSheet onCancel={() => setConfirming(false)} onConfirm={() => { setConfirming(false); withdraw.mutate(); }} open={confirming} pending={withdraw.isPending} />
  </section></main>;
}
