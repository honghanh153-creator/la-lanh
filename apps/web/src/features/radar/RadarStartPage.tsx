import { ArrowLeft, ArrowRight, Check, Copy, HeartStraight, LockKey, Sparkle, Trash } from "@phosphor-icons/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import {
  ApiProblem,
  createRadarInvite,
  deleteRadarResult,
  getRadarShareLink,
  revokeRadarInvite,
  type RadarInvite,
  type RadarVoice,
} from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { RadarEraseSheet } from "./RadarEraseSheet";
import { useRadarEraseTarget } from "./useRadarEraseTarget";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { RADAR_CONTEXT_OPTIONS, RADAR_VOICE_OPTIONS } from "./radarOptions";
import { RADAR_HISTORY_QUERY_KEY, useRadarOwnerBinding } from "./useRadarOwnerBinding";
import { useRadarCreateKey, useRadarHistory } from "./useRadarHistory";

export function RadarStartPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [label, setLabel] = useState("");
  const [context, setContext] = useState<RadarInvite["context"]>("crush");
  const [voice, setVoice] = useState<RadarVoice>("straight_warm");
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const activeOwnerEpoch = useRef<string | null>(null);
  const shareRequestSequence = useRef(0);
  const scrolledToHistory = useRef(false);
  const owner = useRadarOwnerBinding();
  const query = useRadarHistory(owner.epoch, owner.isReady, "consented_invite");
  const eraseTarget = useRadarEraseTarget(owner);
  const retryKey = useRadarCreateKey(owner.epoch);

  useEffect(() => {
    if (!owner.epoch) return;
    if (activeOwnerEpoch.current && activeOwnerEpoch.current !== owner.epoch) {
      setLabel("");
      setContext("crush");
      setVoice("straight_warm");
      setShareUrl(null);
      setMessage(null);
    }
    activeOwnerEpoch.current = owner.epoch;
  }, [owner.epoch]);

  useEffect(() => {
    if (location.hash !== "#radar-history") {
      scrolledToHistory.current = false;
      return;
    }
    if (!query.isFetching && !scrolledToHistory.current) {
      const target = document.getElementById("radar-history");
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        scrolledToHistory.current = true;
      }
    }
  }, [location.hash, query.isFetching]);

  const create = useMutation({
    mutationFn: () => {
      const input = { recipient_label: label.trim(), context, voice };
      return createRadarInvite(input, retryKey.forDraft(input));
    },
    onMutate: () => {
      shareRequestSequence.current += 1;
      setShareUrl(null);
    },
    onSuccess: async (invite) => {
      retryKey.reset();
      setShareUrl(invite.share_url ? new URL(invite.share_url, window.location.origin).toString() : null);
      setLabel("");
      await queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY });
    },
    onError: (error) => {
      if (error instanceof ApiProblem && error.status === 429) {
        setMessage(error.code === "RADAR_LIMIT_REACHED" ? "Bạn đã giữ 100 lần Radar. Xoá một kết quả cũ để tạo thêm nhé." : "Bạn đang tạo Radar hơi nhanh. Chờ một phút rồi thử lại nhé.");
      } else if (error instanceof ApiProblem && error.code === "RADAR_IDEMPOTENCY_CONFLICT") {
        retryKey.reset();
        setMessage("Thông tin hoặc chart đã đổi. Kiểm tra lại rồi bấm tạo link nhé.");
      } else if (error instanceof ApiProblem && error.status === 409) {
        setMessage("Radar cần chart đủ giờ và nơi sinh của bạn trước.");
      } else setMessage("Chưa tạo được link Radar. Thử lại sau một nhịp nhé.");
    },
  });
  const revoke = useMutation({
    mutationFn: revokeRadarInvite,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY }),
    onError: () => setMessage("Chưa thu hồi được link. Link vẫn còn hiệu lực; thử lại khi mạng ổn định."),
  });
  const erase = useMutation({
    mutationFn: deleteRadarResult,
    onSuccess: async () => {
      setShareUrl(null);
      setMessage("Đã xoá lần Radar này. Link và kết quả không còn mở được.");
      await queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY });
    },
    onError: () => setMessage("Chưa xoá được. Thử lại khi mạng ổn định nhé."),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setMessage(null);
    if (label.trim().length < 1) return;
    create.mutate();
  };

  const startOwnerProfile = () => sessionStorage.setItem("la-lanh-radar-owner-start", "1");
  const inviteHistory = query.items;

  const copy = async (value: string) => {
    await navigator.clipboard.writeText(value);
    setMessage("Đã copy link riêng. Gửi đúng cho người bạn muốn check nhé.");
  };

  const revealLink = async (invite: RadarInvite) => {
    const sequence = ++shareRequestSequence.current;
    setMessage(null);
    try {
      const updated = await getRadarShareLink(invite.id);
      if (sequence !== shareRequestSequence.current || !owner.isReady) return;
      if (updated.share_url) {
        const absolute = new URL(updated.share_url, window.location.origin).toString();
        setShareUrl(absolute);
        await copy(absolute);
      }
    } catch {
      if (sequence === shareRequestSequence.current) setMessage("Chưa lấy lại được link. Thử thêm một lần nhé.");
    }
  };


  return <main className="app-page matching-page radar-page radar-start">
    <header className="matching-header"><button aria-label="Quay lại" className="radar-back" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><BrandMark /><span className="matching-signal"><HeartStraight weight="fill" /> private</span></header>
    <RadarFlowSteps current={2} />
    <section className="matching-hero matching-hero--compact"><p className="eyebrow">Radar 1:1</p><h1>Bạn muốn check ai?</h1><p>Chỉ nhập tên gọi để bạn dễ nhớ. Đừng nhập ngày sinh thay họ—link sẽ để chính họ tự quyết định.</p></section>

    {owner.isError ? <section className="radar-public__card radar-owner-gate"><Sparkle /><h2>{owner.error instanceof ApiProblem && owner.error.status === 401 ? "Chart của bạn cần có trước." : "Chưa nối lại được phiên riêng."}</h2><p>{owner.error instanceof ApiProblem && owner.error.status === 401 ? "Chưa cần tài khoản. Tạo chart riêng, thêm giờ và nơi sinh rồi Lá đưa bạn quay lại đây để tạo link." : "Dữ liệu cũ vẫn được giữ kín. Kiểm tra mạng rồi thử nối lại nhé."}</p>{owner.error instanceof ApiProblem && owner.error.status === 401 ? <Link className="matching-primary" onClick={startOwnerProfile} to="/consent">Tạo chart của mình <ArrowRight /></Link> : <button className="matching-primary" onClick={owner.retry} type="button">Thử nối lại <ArrowRight /></button>}</section> : null}

    {owner.isReady ? <form className="radar-create" onSubmit={submit}>
      <label><span>Tên gọi của người ấy</span><input autoComplete="off" maxLength={40} onChange={(event) => setLabel(event.target.value)} placeholder="Ví dụ: Mèo, An, người hay seen…" required value={label} /></label>
      <fieldset><legend>Hai bạn đang là…</legend><div className="radar-contexts">{RADAR_CONTEXT_OPTIONS.map(([value, text]) => <button aria-pressed={context === value} className={context === value ? "is-selected" : ""} key={value} onClick={() => setContext(value)} type="button">{text}</button>)}</div></fieldset>
      <details className="radar-voice-disclosure"><summary>Giọng đọc · {RADAR_VOICE_OPTIONS.find(([value]) => value === voice)?.[1]}</summary><fieldset><legend>Bạn muốn Radar nói kiểu nào?</legend><div className="radar-voices">{RADAR_VOICE_OPTIONS.map(([value, title, description]) => <button aria-pressed={voice === value} className={voice === value ? "is-selected" : ""} key={value} onClick={() => setVoice(value)} type="button"><strong>{title}</strong><small>{description}</small></button>)}</div></fieldset></details>
      <div className="radar-consent-note"><LockKey /><p><strong>Không cần dữ liệu của người kia ở bước này.</strong><br />Radar chỉ chạy khi họ tự hoàn thiện chart và đồng ý dùng cho lần check này.</p></div>
      <button className="matching-primary" disabled={create.isPending || owner.isPending || !label.trim()} type="submit">{create.isPending ? "Đang tạo link riêng…" : "Tạo link bật Radar"}<ArrowRight /></button>
    </form> : null}
    {owner.isPending && !owner.isError ? <section aria-live="polite" className="radar-owner-refresh"><Sparkle className="matching-pulse" /><p>Đang nối Radar với phiên chart hiện tại…</p></section> : null}
    {message && !owner.isError ? <p className="matching-message" role="status">{message}</p> : null}
    {create.isError && create.error instanceof ApiProblem && create.error.status === 409 && create.error.code !== "RADAR_IDEMPOTENCY_CONFLICT" ? <Link className="matching-secondary" to="/birth-time">Thêm giờ & nơi sinh của mình</Link> : null}
    {shareUrl && owner.isReady ? <section className="radar-share" aria-live="polite"><Sparkle weight="fill" /><div><strong>Link riêng đã sẵn sàng</strong><p>Hết hạn sau 7 ngày. Bạn có thể thu hồi trước khi người kia bật Radar.</p></div><button onClick={() => void copy(shareUrl)} type="button"><Copy /> Copy link</button></section> : null}

    {owner.isReady ? <section className="radar-history" id="radar-history"><p className="eyebrow">Đang chờ & đã mở</p>{inviteHistory.length ? inviteHistory.map((invite) => <article key={invite.id}><span className={`radar-status is-${invite.status}`}>{invite.status === "completed" ? <Check /> : <HeartStraight />}</span><div><strong>{invite.recipient_label}</strong><p>{statusText(invite.status)}</p></div>{invite.status === "pending" ? <><button aria-label={`Copy link cho ${invite.recipient_label}`} onClick={() => void revealLink(invite)} type="button"><Copy /></button><button aria-label={`Thu hồi link cho ${invite.recipient_label}`} onClick={() => revoke.mutate(invite.id)} type="button"><Trash /></button></> : <>{invite.status === "completed" ? <Link to={`/radar/result/${invite.id}`}>Mở</Link> : null}<button aria-label={`Xoá lần Radar với ${invite.recipient_label}`} disabled={erase.isPending} onClick={() => eraseTarget.request(invite.id, invite.recipient_label)} type="button"><Trash /></button></>}</article>) : query.isPending ? <p role="status">Đang tải lời mời…</p> : !query.isError ? <p className="radar-history__empty">Chưa có lời mời nào. Link đầu tiên sẽ nằm ở đây để bạn theo dõi.</p> : null}</section> : null}
    {owner.isReady && query.hasNextPage ? <button className="matching-secondary" disabled={query.isFetchingNextPage} onClick={() => void query.fetchNextPage()} type="button">{query.isFetchingNextPage ? "Đang tải…" : "Xem thêm lời mời"}</button> : null}
    {owner.isReady && query.isError ? <p role="alert">Chưa tải được lịch sử. <button onClick={() => void query.refetch()} type="button">Thử lại</button></p> : null}
    <RadarEraseSheet body="Kết quả của cả hai và link sẽ không còn mở được. Việc này không hoàn tác được." erase={eraseTarget} onConfirm={(id) => erase.mutate(id)} pending={erase.isPending} title={(name) => `Xoá lần Radar với ${name}?`} />
  </main>;
}

function statusText(status: RadarInvite["status"]) {
  if (status === "pending") return "Đang chờ người kia đồng ý";
  if (status === "completed") return "Radar đã bắt được sóng";
  if (status === "withdrawn") return "Người kia đã rút dữ liệu";
  if (status === "expired") return "Link đã hết hạn";
  return "Link đã thu hồi";
}
