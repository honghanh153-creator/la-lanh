import { ArrowLeft, ArrowRight, Check, HeartStraight, ShieldCheck, Sparkle, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { ApiProblem, deleteRadarResult, getRadarConsentOptions } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { RadarEraseSheet } from "./RadarEraseSheet";
import { useRadarEraseTarget } from "./useRadarEraseTarget";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { formatRadarExpiry } from "./radarOptions";
import { markRadarOwnerReturn } from "./radarOwnerReturn";
import { RADAR_HISTORY_QUERY_KEY, useRadarOwnerBinding } from "./useRadarOwnerBinding";
import { useRadarHistory } from "./useRadarHistory";

/**
 * /radar/start, the Hợp gu hub. Owner AP2 (21.11.2026): no "this person agreed" tick on any path;
 * a pair is read only when the other person types their own birth date through the link. This
 * page leads to the invite and keeps the history of earlier results until they expire.
 */
export function RadarPrivateStartPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<string | null>(null);
  const scrolledToHistory = useRef(false);
  const owner = useRadarOwnerBinding();
  const history = useRadarHistory(owner.epoch, owner.isReady, "private_check");
  const erase = useRadarEraseTarget(owner);
  // The owner-approved invite sentences (AP2) come from the server; without them the page keeps
  // the plain invite link.
  const consent = useQuery({ queryKey: ["radar-consent-options"], queryFn: ({ signal }) => getRadarConsentOptions(signal), retry: false, staleTime: 60_000 });
  const sentences = consent.data?.invite_first ? consent.data.sentences : null;
  const remove = useMutation({
    mutationFn: deleteRadarResult,
    onSuccess: (_data, requestId) => {
      queryClient.removeQueries({ queryKey: ["radar-result", owner.epoch, requestId] });
      void queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY });
    },
    onError: () => setMessage("Chưa xóa được kết quả. Dữ liệu vẫn còn nguyên; thử lại khi mạng ổn định."),
  });
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

  return <main className="app-page matching-page radar-page radar-start">
    <header className="matching-header"><button aria-label="Quay lại" className="radar-back" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><BrandMark /><span className="matching-signal"><HeartStraight weight="fill" /> Hợp gu</span></header>
    <RadarFlowSteps current={2} />
    <section className="matching-hero matching-hero--compact radar-private-hero"><h1>Xem hợp gu với một người bạn đã biết.</h1></section>

    {owner.isError ? <section className="radar-public__card radar-owner-gate"><Sparkle /><h2>{owner.error instanceof ApiProblem && owner.error.status === 401 ? "Chart của bạn cần có trước." : "Chưa nối lại được phiên riêng."}</h2><p>{owner.error instanceof ApiProblem && owner.error.status === 401 ? "Chưa cần tài khoản. Tạo chart riêng, thêm giờ và nơi sinh rồi Lá đưa bạn quay lại Radar." : "Dữ liệu cũ vẫn được giữ kín. Kiểm tra mạng rồi thử nối lại nhé."}</p>{owner.error instanceof ApiProblem && owner.error.status === 401 ? <Link className="matching-primary" onClick={startOwnerProfile} to="/consent">Tạo chart của mình <ArrowRight /></Link> : <button className="matching-primary" onClick={owner.retry} type="button">Thử nối lại <ArrowRight /></button>}</section> : null}

    {ownerReady && sentences?.["owner-invite-heading"] && sentences["owner-invite-body"] ? <section aria-labelledby="radar-invite-first-heading" className="radar-invite-first"><ShieldCheck /><div><h2 id="radar-invite-first-heading">{sentences["owner-invite-heading"]}</h2><p>{sentences["owner-invite-body"]}</p></div><Link className="matching-primary" to="/radar/invite">Gửi link mời <ArrowRight /></Link></section> : null}
    {ownerReady && !(sentences?.["owner-invite-heading"] && sentences["owner-invite-body"]) && !consent.isPending ? <div className="radar-no-permission"><ShieldCheck /><p>Để người ấy tự nhập và tự đồng ý.</p><Link to="/radar/invite">Mời họ tự nhập</Link></div> : null}
    {(owner.isPending) && !owner.isError ? <section aria-live="polite" className="radar-owner-refresh"><Sparkle className="matching-pulse" /><p>Đang mở hồ sơ của bạn…</p></section> : null}
    {message && !owner.isError ? <p className="matching-message" role="alert">{message}</p> : null}

    {ownerReady ? <section className="radar-history" id="radar-history"><p className="eyebrow">Những người bạn đã xem gần đây</p>{privateHistory.length ? privateHistory.map((item) => <article key={item.id}><span className={`radar-status is-${item.status}`}>{item.status === "completed" ? <Check /> : <HeartStraight />}</span><div><strong>{item.recipient_label}</strong><p>{item.status === "completed" ? `Tự xoá lúc ${formatRadarExpiry(item.expires_at)}` : "Kết quả đã hết hạn"}</p></div>{item.status === "completed" ? <Link to={`/radar/result/${item.id}`}>Mở</Link> : null}<button aria-label={`Xóa kết quả ${item.recipient_label}`} disabled={remove.isPending} onClick={() => erase.request(item.id, item.recipient_label)} type="button"><Trash /></button></article>) : <p className="radar-history__empty">Chưa có bản đọc nào. Kết quả đầu tiên sẽ nằm ở đây để bạn mở lại.</p>}</section> : null}
    {ownerReady && history.hasNextPage ? <button className="matching-secondary" disabled={history.isFetchingNextPage} onClick={() => void history.fetchNextPage()} type="button">{history.isFetchingNextPage ? "Đang tải…" : "Xem thêm kết quả"}</button> : null}
    {ownerReady && history.isError ? <p role="alert">Chưa tải được lịch sử. <button onClick={() => void history.refetch()} type="button">Thử lại</button></p> : null}
    <RadarEraseSheet body="Bản đọc này sẽ không còn mở được, kể cả từ lịch sử. Việc này không hoàn tác được." erase={erase} onConfirm={(id) => remove.mutate(id)} pending={remove.isPending} title={(name) => `Xoá kết quả với ${name}?`} />
  </main>;
}
