import { ArrowClockwise, ArrowLeft, Hourglass, LockKey, Sparkle, Trash, UserFocus } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  ApiProblem,
  cancelHumanTarotRequest,
  getHumanTarotRequest,
  type HumanTarotRequest,
  type HumanTarotResult,
} from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { formatVietnamDay, formatVietnamTime } from "./humanTarot";
import { TarotCardArt } from "./TarotCardArt";
import { CardName } from "./TarotCardLabel";
import "./tarot.css";
import "./tarot-polish.css";
import "./human-tarot.css";

// The browser timer only triggers a refetch at the release time; the server decides what opens.
const MAX_TIMER_MS = 6 * 60 * 60 * 1000;

function useRefetchAt(iso: string | undefined, refetch: () => void) {
  useEffect(() => {
    if (!iso) return undefined;
    const delay = new Date(iso).getTime() - Date.now() + 1000;
    if (delay <= 0 || delay > MAX_TIMER_MS) return undefined;
    const timer = window.setTimeout(refetch, delay);
    return () => window.clearTimeout(timer);
  }, [iso, refetch]);
}

export function HumanTarotRequestPage() {
  const { requestId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirm, setConfirm] = useState(false);
  const query = useQuery({
    queryKey: ["human-tarot-request", requestId],
    queryFn: ({ signal }) => getHumanTarotRequest(requestId, signal),
    retry: false,
    refetchOnWindowFocus: true,
  });
  const request = query.data;
  const { refetch } = query;
  useRefetchAt(request?.status === "waiting" ? request.release_at : undefined, () => void refetch());
  const cancel = useMutation({
    mutationFn: () => cancelHumanTarotRequest(requestId),
    onSuccess: async () => {
      setConfirm(false);
      await queryClient.invalidateQueries({ queryKey: ["human-tarot-availability"] });
      await refetch();
    },
    onError: (error) => {
      if (error instanceof ApiProblem && error.code === "SESSION_CHANGED") {
        void navigate("/welcome?restart=1", { replace: true, state: { sessionChanged: true } });
      }
    },
  });

  if (query.isLoading) {
    return <Frame><section className="tarot-loading" aria-label="Đang mở yêu cầu"><span /></section></Frame>;
  }
  if (query.isError || !request) {
    return <Frame><section className="tarot-state">
      <h1>Không mở được yêu cầu này.</h1>
      <p>Yêu cầu có thể đã hết hạn, đã được xoá hoặc thuộc một trình duyệt khác.</p>
      <Link className="tarot-primary" to="/tarot">Về Tarot</Link>
    </section></Frame>;
  }
  const releaseTime = formatVietnamTime(request.release_at);
  const releaseDay = formatVietnamDay(request.release_at);
  const checkAgain = <button className="tarot-secondary human-tarot-check" disabled={query.isFetching} onClick={() => void refetch()} type="button">
    <ArrowClockwise aria-hidden="true" />{query.isFetching ? "Đang kiểm tra…" : "Kiểm tra lại"}
  </button>;
  const cancelArea = (label: string, warning: string) => confirm ? (
    <div className="tarot-delete-confirm" role="alert">
      <strong>{warning}</strong>
      <p>Không có nút hoàn tác. Lượt hôm nay không được trả lại.</p>
      <div>
        <button disabled={cancel.isPending} onClick={() => cancel.mutate()} type="button"><Trash aria-hidden="true" />{cancel.isPending ? "Đang xoá…" : label}</button>
        <button onClick={() => setConfirm(false)} type="button">Giữ lại</button>
      </div>
    </div>
  ) : <button className="tarot-delete" onClick={() => setConfirm(true)} type="button"><Trash aria-hidden="true" /> {label}</button>;

  return <Frame>
    <section className="human-tarot-receipt" aria-labelledby="human-tarot-title">
      <p className="tarot-kicker"><UserFocus aria-hidden="true" /> {request.status === "ready" ? "Bài do người bốc viết" : "Nhờ người bốc"}</p>
      {request.status === "waiting" ? <>
        <h1 id="human-tarot-title">Đã nhận câu hỏi · Hẹn bạn lúc {releaseTime}, {releaseDay}</h1>
        <Delivery request={request} />
        <p>Bài sẽ mở lúc {releaseTime}. Bạn quay lại lúc đó nhé.</p>
        {checkAgain}
      </> : null}
      {request.status === "ready" ? <h1 id="human-tarot-title">Bài của bạn đã mở lúc {releaseTime}, {releaseDay}.</h1> : null}
      {request.status === "late" ? <>
        <h1 id="human-tarot-title">Bài của bạn chưa hoàn tất.</h1>
        <p>Bạn có thể quay lại sau hoặc huỷ yêu cầu.</p>
        <Delivery request={request} />
        {checkAgain}
      </> : null}
      {request.status === "unfulfilled" ? <>
        <h1 id="human-tarot-title">Hôm nay người bốc chưa kịp viết bài cho bạn.</h1>
        <p>Yêu cầu đã kết thúc; bạn có thể tự bốc ngay.</p>
        <Link className="tarot-primary" to="/tarot"><Sparkle aria-hidden="true" />Tự bốc ngay</Link>
      </> : null}
      {request.status === "cancelled" ? <>
        <h1 id="human-tarot-title">Đã xoá trong app.</h1>
        <p role="status">{request.copy_cleared ? "Đã xoá bản tạm trên Google Sheet." : "Bản tạm trên Google Sheet đang được xoá."}</p>
        {request.copy_cleared ? null : checkAgain}
        <Link className="tarot-primary" to="/tarot">Về Tarot</Link>
      </> : null}
      {request.question && request.status !== "cancelled" ? <div className="tarot-question-ticket"><span>Câu bạn đã gửi</span><strong>{request.question}</strong></div> : null}
    </section>
    {request.status === "ready" && request.result ? <Result result={request.result} /> : null}
    <footer className="tarot-result-actions">
      {request.status === "waiting" || request.status === "late" ? cancelArea("Huỷ yêu cầu", "Huỷ là người bốc sẽ không viết bài này nữa.") : null}
      {request.status === "ready" ? <>
        <Link className="tarot-primary" to="/tarot"><Sparkle aria-hidden="true" />Hỏi một chuyện khác</Link>
        {cancelArea("Xoá bài này", "Xoá là mất hẳn bài này.")}
      </> : null}
      {cancel.isError ? <p className="tarot-error" role="alert">Chưa xoá được. Bạn có thể thử lại.</p> : null}
    </footer>
    <p className="tarot-private"><LockKey aria-hidden="true" /> Chỉ trình duyệt này mở được yêu cầu. Giờ mở bài do máy chủ quyết định.</p>
  </Frame>;
}

function Delivery({ request }: { request: HumanTarotRequest }) {
  if (request.delivery === "delivered") return <p className="human-tarot-delivery" role="status">Người bốc đã nhận câu hỏi.</p>;
  if (request.delivery === "error") return <p className="human-tarot-delivery is-error" role="status">Chưa chuyển được tới người bốc. App đang thử lại; lượt của bạn vẫn được giữ.</p>;
  if (request.delivery === "pending") return <p className="human-tarot-delivery" role="status"><Hourglass aria-hidden="true" /> Đang chuyển tới người bốc.</p>;
  return null;
}

function Result({ result }: { result: HumanTarotResult }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, []);
  return <section className="tarot-reading human-tarot-result" aria-labelledby="human-tarot-result-title">
    <h2 id="human-tarot-result-title" ref={heading} tabIndex={-1}>Bài người bốc viết cho bạn</h2>
    <ul aria-label="Các lá người bốc đã rút" className="human-tarot-cards">
      {result.cards.map((item, index) => <li key={item.position_key}>
        <TarotCardArt card={item.card} compact decorative />
        <span><small>0{index + 1} · {item.position_label}</small><strong><CardName card={item.card} /></strong></span>
      </li>)}
    </ul>
    <article className="tarot-reading-card human-tarot-reading">
      <div className="tarot-reading-copy">
        {result.reading.split("\n").map((paragraph, index) => <p key={index}>{paragraph}</p>)}
        <div className="tarot-action">
          <Sparkle aria-hidden="true" />
          <div><strong>Một bước nhỏ</strong><p>{result.step}</p></div>
        </div>
      </div>
    </article>
    <p className="human-tarot-disclaimer">Bài là góc nhìn để bạn tự suy nghĩ, không phải lời tiên đoán hay lời khuyên chuyên môn.</p>
  </section>;
}

function Frame({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  return <main className="tarot-page">
    <header className="tarot-header">
      <button aria-label="Quay lại" onClick={() => void navigate(-1)} type="button"><ArrowLeft aria-hidden="true" /></button>
      <div className="tarot-header__title"><strong>Tarot</strong><span><LockKey aria-hidden="true" /> Riêng tư</span></div>
      <BrandMark />
    </header>
    {children}
  </main>;
}
