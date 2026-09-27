import { ArrowRight, LockKey, ShieldCheck, Sparkle, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiProblem, acceptRadarInvite, getCurrentRadarInvite, getSession, type RadarResult } from "../../shared/api/client";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { radarVoiceLabel, RADAR_CONTEXT_OPTIONS, RADAR_PENDING_REQUEST_KEY } from "./radarOptions";

type RadarSection = NonNullable<RadarResult["sections"]>[number];

function evidenceSourceLabel(source: RadarSection["evidence"][number]["source"]) {
  const labels: Record<string, string> = {
    synastry: "Giữa hai chart",
    house_overlay: "Vùng tác động",
    composite_midpoint: "Nhịp chart chung",
  };
  return labels[source] ?? "Nguồn dữ liệu chưa hỗ trợ";
}

function RadarEvidence({ evidence, summary }: { evidence: RadarSection["evidence"]; summary: string }) {
  return <details className="radar-evidence-disclosure">
    <summary>{summary}</summary>
    <div className="radar-evidence-list">{evidence.map((item) => <div className="radar-evidence" key={item.evidence_id}>
      <span>{evidenceSourceLabel(item.source)}</span>
      <p>{item.plain}</p>
    </div>)}</div>
  </details>;
}

function RadarLegacyReading({ sections }: { sections: RadarSection[] }) {
  return <section aria-label="Bản đọc chi tiết" className="radar-reading-sections">{sections.map((section, index) => <article className={`radar-reading-card is-${section.key}`} key={section.key}>
    <span className="radar-reading-card__number">{String(index + 1).padStart(2, "0")}</span>
    <div>
      <small>{section.label}</small>
      <h2>{section.title}</h2>
      <p>{section.body}</p>
      <RadarEvidence evidence={section.evidence} summary="Chart nào tạo ra điều này?" />
    </div>
  </article>)}</section>;
}

function RadarDossier({ sections }: { sections: RadarSection[] }) {
  return <section aria-label="Bản đọc chi tiết" className="radar-dossier">
    <nav aria-label="Mục lục bản đọc" className="radar-dossier-index">
      {sections.map((section, index) => <a href={`#radar-chapter-${section.key}`} key={section.key}>
        <span>{String(index + 1).padStart(2, "0")}</span>
        <strong>{section.label}</strong>
      </a>)}
    </nav>

    <div className="radar-dossier-chapters">{sections.map((section, index) => <details className={`radar-dossier-chapter is-${section.key}`} id={`radar-chapter-${section.key}`} key={section.key} open={index === 0}>
      <summary>
        <span className="radar-dossier-chapter__number">{String(index + 1).padStart(2, "0")}</span>
        <span className="radar-dossier-chapter__heading">
          <small>{section.label}</small>
          <span aria-level={2} role="heading">{section.title}</span>
        </span>
        <span aria-hidden="true" className="radar-dossier-chapter__toggle">＋</span>
      </summary>

      <div className="radar-dossier-chapter__body">
        <p className="radar-dossier-lede">{section.body}</p>

        {section.topics?.length ? <ul aria-label="Các chủ đề chính" className="radar-dossier-topics">
          {section.topics.map((topic) => <li key={topic}>{topic}</li>)}
        </ul> : null}

        {section.highlights?.length ? <div className="radar-dossier-highlights">{section.highlights.map((highlight) => <article key={highlight.key}>
          <small>{highlight.label}</small>
          <h3>{highlight.title}</h3>
          <p>{highlight.body}</p>
        </article>)}</div> : null}

        {section.scene ? <aside className="radar-dossier-scene">
          <small>{section.scene.label}</small>
          <h3>{section.scene.title}</h3>
          <p>{section.scene.body}</p>
        </aside> : null}

        {section.perspectives?.length ? <section aria-label="Ba phía của kết nối" className="radar-dossier-perspectives">
          {section.perspectives.map((perspective) => <article className={`is-${perspective.key}`} key={perspective.key}>
            <small>{perspective.label}</small>
            <h3>{perspective.title}</h3>
            <p>{perspective.body}</p>
          </article>)}
        </section> : null}

        {section.observation ? <aside className="radar-dossier-observation">
          <small>{section.observation.label}</small>
          <h3>{section.observation.title}</h3>
          <p>{section.observation.body}</p>
        </aside> : null}

        <RadarEvidence evidence={section.evidence} summary="Vì sao Lá đọc vậy?" />
      </div>
    </details>)}</div>
  </section>;
}

export function RadarContinuePage() {
  const navigate = useNavigate();
  const [consented, setConsented] = useState(false);
  const expectedRequestId = sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY);
  const invite = useQuery({ queryKey: ["current-radar", expectedRequestId], queryFn: ({ signal }) => getCurrentRadarInvite(signal), enabled: Boolean(expectedRequestId), retry: false });
  const session = useQuery({ queryKey: ["session", "radar-recipient"], queryFn: ({ signal }) => getSession(signal), enabled: Boolean(invite.data), retry: false });
  const requestId = invite.data?.request_id;
  useEffect(() => { setConsented(false); }, [requestId]);
  const accept = useMutation({
    mutationFn: () => acceptRadarInvite(requestId ?? ""),
    onSuccess: () => {
      sessionStorage.removeItem(RADAR_PENDING_REQUEST_KEY);
      void navigate("/radar/receipt", { replace: true });
    },
  });
  if (!expectedRequestId) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card"><h1>Mở lại đúng link mời nhé.</h1><p>Radar không tự đoán bạn đang đồng ý cho kết nối nào.</p><Link className="matching-primary" to="/radar">Về Radar</Link></section></main>;
  if (invite.isLoading) return <main className="matching-page matching-page--loading"><Sparkle className="matching-pulse" /><p>Đang kiểm tra đúng lời mời…</p></main>;
  if (!invite.data) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card"><h1>Không tìm thấy lời mời đang chờ.</h1><p>Link có thể đã hết hạn, bị thu hồi hoặc được mở ở tab khác.</p><Link className="matching-primary" to="/radar">Về Radar</Link></section></main>;
  if (invite.data.request_id !== expectedRequestId) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card"><h1>Đây là một lời mời khác.</h1><p>Đóng tab này và mở lại đúng link để tránh đồng ý nhầm người.</p><Link className="matching-primary" to="/radar">Về Radar</Link></section></main>;
  const missingSession = session.error instanceof ApiProblem && session.error.status === 401;
  const chartMissing = accept.error instanceof ApiProblem && accept.error.status === 409;
  const acceptMismatch = accept.error instanceof ApiProblem && accept.error.status === 422;
  const contextLabel = RADAR_CONTEXT_OPTIONS.find(([value]) => value === invite.data.context)?.[1] ?? "Một người";
  return <main className="matching-page radar-public radar-continue"><header className="matching-header"><BrandMark /><span className="matching-signal"><LockKey /> consent riêng</span></header><RadarFlowSteps current={2} /><section className="radar-public__signal"><p className="eyebrow">Lời mời: {contextLabel.toLowerCase()}</p><h1>{invite.data.recipient_label}, đây đúng là lời mời bạn vừa mở?</h1><p>Radar chỉ chạy cho đúng kết nối này, với giọng “{radarVoiceLabel(invite.data.voice)}”. Dữ liệu thô không hiện trong kết quả và không được gửi cho người mời.</p></section>
    {session.isLoading ? <section aria-live="polite" className="radar-owner-refresh"><Sparkle className="matching-pulse" /><p>Đang kiểm tra chart trên thiết bị này…</p></section> : missingSession ? <section className="radar-public__card"><Sparkle /><h2>Tạo chart riêng trước</h2><p>Chưa cần tài khoản. Phiên khách tự hết hạn sau 30 ngày không hoạt động.</p><Link className="matching-primary" to="/consent">Tạo chart của mình <ArrowRight /></Link></section> : session.isError ? <section className="radar-public__card"><h2>Chưa kiểm tra được chart.</h2><p>Dữ liệu chưa được gửi. Kiểm tra mạng rồi thử lại.</p><button className="matching-primary" onClick={() => void session.refetch()} type="button">Thử lại</button></section> : <section className="radar-public__card"><ShieldCheck /><h2>Chỉ đồng ý cho phép đọc hai chart</h2><ul><li>Dùng natal chart, synastry và composite để tạo các tín hiệu nhiều chiều.</li><li>Không chia sẻ ngày, giờ, nơi sinh hoặc tọa độ với người kia.</li><li>Không dùng Radar để xếp hạng, quảng cáo hoặc tìm người lạ.</li></ul><label className="consent-check"><input checked={consented} onChange={(event) => setConsented(event.target.checked)} type="checkbox" /><span>Tôi đồng ý dùng chart của mình cho đúng lần Radar “{invite.data.recipient_label}” và hiểu đây là nội dung tự soi, không phải lời khuyên quyết định.</span></label>{chartMissing ? <p className="matching-message">Chart chưa đủ giờ và nơi sinh.</p> : null}{acceptMismatch ? <p className="matching-message">Lời mời đã thay đổi hoặc hết hạn. Mở lại link gốc để tiếp tục an toàn.</p> : null}{accept.isError && !chartMissing && !acceptMismatch ? <p className="matching-message">Radar chưa tính xong. Chưa có consent nào bị ghi nhận—bạn có thể thử lại.</p> : null}{chartMissing ? <Link className="matching-secondary" to="/birth-time">Hoàn thiện chart của mình</Link> : null}<button className="matching-primary" disabled={!consented || accept.isPending || acceptMismatch} onClick={() => accept.mutate()} type="button">{accept.isPending ? "Đang đọc hai chart…" : accept.isError && !acceptMismatch ? "Thử bật Radar lại" : "Đồng ý & bật Radar"}<ArrowRight /></button></section>}
  </main>;
}

function RadarResultFooter({ ownerView, mode }: { ownerView: boolean; mode?: RadarResult["mode"] }) {
  if (!ownerView) return <section className="radar-next-step"><p className="eyebrow">Quyền của bạn</p><h2>Bản đọc này mở lại được trên thiết bị này trong 7 ngày.</h2><p>Bạn có thể rút chart bất cứ lúc nào; khi rút, cả hai phía đều không thể mở lại kết quả.</p><Link className="matching-secondary" to="/radar">Về Radar Hợp Gu</Link></section>;
  const historyUrl = mode === "consented_invite" ? "/radar/invite#radar-history" : "/radar/start#radar-history";
  return <>
    <section className="radar-next-step">
      <p className="eyebrow">Tiếp theo</p>
      <h2>Muốn check thêm một kết nối?</h2>
      <p>Mỗi bản đọc là riêng cho đúng hai chart. Kết quả cũ vẫn nằm trong lịch sử cho tới khi bạn xóa hoặc hết hạn.</p>
      <div>
        <Link className="matching-primary" to="/radar/start">Check thêm một người <ArrowRight /></Link>
        <Link className="matching-secondary" to={historyUrl}>Xem các lần check</Link>
      </div>
    </section>
    <AppNav />
  </>;
}

export function RadarResultView({ result, onWithdraw, withdrawing = false, actionLabel = "Rút chart của tôi khỏi kết quả này", ownerView = false }: { result: RadarResult; onWithdraw?: () => void; withdrawing?: boolean; actionLabel?: string; ownerView?: boolean }) {
  const signature = result.pair_signature;
  const compatibilityMap = result.compatibility_map ?? [];
  const sections = result.sections ?? [];
  const hasDossier = sections.some((section) => section.depth !== undefined);

  if (result.version !== "radar-result-v2" || !signature || !compatibilityMap.length || !sections.length) {
    return <main className={`matching-page radar-result${ownerView ? " radar-result--owner" : ""}`}><header className="matching-header"><BrandMark /><span className="matching-signal"><Sparkle /> Radar đã bắt sóng</span></header><RadarFlowSteps current={3} /><section className="radar-result__hero"><p className="eyebrow">{result.recipient_label ? `Bạn × ${result.recipient_label}` : "Bản đọc hai người"}</p><h1>{result.headline}</h1><p>{result.summary}</p></section><section className="radar-dimensions">{result.dimensions.map((item, index) => <article key={item.key}><span>{String(index + 1).padStart(2, "0")}</span><div><small>{item.signal}</small><h2>{item.label}</h2><p>{item.body}</p><details><summary>Vì sao Radar đọc như vậy?</summary><p>{item.evidence_ids.length ? `Dựa trên ${item.evidence_ids.length} contact giữa hai chart. Mở dữ liệu kỹ thuật chỉ để kiểm chứng, không dùng để phán người.` : "Lớp này chưa có đủ contact mạnh để kết luận."}</p></details></div></article>)}</section><p className="radar-disclaimer">{result.disclaimer}</p>{onWithdraw ? <button className="radar-withdraw" disabled={withdrawing} onClick={onWithdraw} type="button"><Trash /> {actionLabel}</button> : null}<RadarResultFooter mode={result.mode} ownerView={ownerView} /></main>;
  }

  return <main className={`matching-page radar-result radar-result--v2${ownerView ? " radar-result--owner" : ""}`}>
    <header className="matching-header"><BrandMark /><span className="matching-signal"><Sparkle /> Radar đã bắt sóng</span></header>
    <RadarFlowSteps current={3} />
    <section className="radar-result__hero radar-signature">
      <p className="eyebrow">{result.recipient_label ? `Bạn × ${result.recipient_label}` : "Bản đọc hai người"}</p>
      <span className="radar-signature__kicker">{signature.kicker}</span>
      <h1>{signature.headline}</h1>
      <p>{signature.summary}</p>
      {result.metadata?.voice_label ? <small className="radar-reading-voice">Giọng đọc bạn chọn · {result.metadata.voice_label}</small> : null}
    </section>

    <section aria-labelledby="radar-map-title" className="radar-compatibility-map">
      <div className="radar-section-heading"><div><p className="eyebrow">Compatibility map</p><h2 id="radar-map-title">Ba tín hiệu, đọc riêng từng cái.</h2></div><Sparkle /></div>
      <p className="radar-map-note">Không cộng thành 100. Cao ở “Bắt sóng” vẫn có thể cao ở “Lực cấn”.</p>
      <div className="radar-map-grid">{compatibilityMap.map((item) => <article className={`is-${item.key}`} key={item.key}>
        <div className="radar-map-index"><strong>{item.value}</strong><span>/100</span></div>
        <h3>{item.label}</h3>
        <div aria-label={`${item.label}: ${item.value} trên 100`} className="radar-meter" role="img"><i style={{ width: `${item.value}%` }} /></div>
        <p>{item.meaning}</p>
        {item.evidence?.length ? <RadarEvidence evidence={item.evidence} summary="Vì sao có con số này?" /> : null}
      </article>)}</div>
    </section>

    {hasDossier ? <RadarDossier sections={sections} /> : <RadarLegacyReading sections={sections} />}

    <aside className="radar-disclaimer"><Sparkle /><p>{result.disclaimer}</p></aside>
    {onWithdraw ? <button className="radar-withdraw" disabled={withdrawing} onClick={onWithdraw} type="button"><Trash /> {actionLabel}</button> : null}
    <RadarResultFooter mode={result.mode} ownerView={ownerView} />
  </main>;
}
