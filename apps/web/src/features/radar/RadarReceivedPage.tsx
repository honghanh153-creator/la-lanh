import { ArrowRight, Sparkle } from "@phosphor-icons/react";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  currentSessionEpoch,
  getReceivedRadarResult,
  getSession,
  listReceivedRadar,
  withdrawReceivedRadar,
} from "../../shared/api/client";
import { AppSheet } from "../../shared/ui/AppSheet";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { RadarResultView } from "./RadarContinuePage";
import { formatRadarExpiry, RADAR_CONTEXT_OPTIONS } from "./radarOptions";
import { evictRadarReadings, isTerminalDenial } from "./radarReadingCache";

// P09 D2: B reopens results from B's own guest session, without the receipt cookie. Cached reads are
// keyed by the server-confirmed session epoch, so another session on this device never sees them.
function useRecipientSession() {
  const session = useQuery({
    queryKey: ["radar-recipient-session"],
    queryFn: ({ signal }) => getSession(signal),
    refetchOnMount: "always",
    retry: false,
    staleTime: 0,
  });
  return { epoch: session.isSuccess ? currentSessionEpoch() : null, session };
}

function contextLabel(context: string) {
  return RADAR_CONTEXT_OPTIONS.find(([value]) => value === context)?.[1] ?? "Một người";
}

function MissingCard({ title, body, onRetry }: { title: string; body: string; onRetry?: () => void }) {
  return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty">
    <div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/moon.webp" /></div>
    <h1>{title}</h1><p>{body}</p>
    {onRetry ? <button className="matching-primary" onClick={onRetry} type="button">Thử lại</button> : null}
    <Link className="matching-secondary" to="/radar">Về Radar Hợp Gu</Link>
  </section></main>;
}

export function RadarReceivedPage() {
  const { epoch, session } = useRecipientSession();
  const list = useInfiniteQuery({
    queryKey: ["radar-received", epoch],
    queryFn: ({ pageParam, signal }) => listReceivedRadar(signal, pageParam),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (page) => page.next_before ?? undefined,
    enabled: epoch !== null,
    retry: false,
  });

  if (session.isPending || list.isPending) {
    if (session.isError) return <MissingCard body="Mở lại Lá trên thiết bị bạn đã dùng để đồng ý, rồi thử lại." title="Chưa nhận ra phiên của bạn." />;
    return <main className="matching-page matching-page--loading"><Sparkle className="matching-pulse" /><p>Đang tìm kết quả bạn đã nhận…</p></main>;
  }
  if (list.isError) return <MissingCard body="Thử lại sau một chút nhé." onRetry={() => void list.refetch()} title="Chưa tải được danh sách." />;

  const items = list.data.pages.flatMap((page) => page.items);
  return <main className="matching-page radar-public radar-received">
    <header className="matching-header"><BrandMark /></header>
    <section className="radar-public__signal">
      <p className="eyebrow">Quyền của bạn</p>
      <h1>Kết quả bạn đã nhận</h1>
      <p>Những lần ai đó mời bạn check Hợp gu và bạn đã đồng ý. Mỗi kết quả mở được trong 30 ngày kể từ lúc bạn đồng ý. Bạn không cần nhập lại ngày sinh.</p>
    </section>
    {items.length ? <ul className="radar-received__list">
      {items.map((item) => <li key={item.request_id}>
        <Link className="radar-received__item" to={`/radar/received/${encodeURIComponent(item.request_id)}`}>
          <strong>Hợp gu · {contextLabel(item.context)}</strong>
          <span>Còn mở đến {formatRadarExpiry(item.expires_at)}</span>
          <ArrowRight aria-hidden="true" />
        </Link>
      </li>)}
    </ul> : <p className="radar-received__empty">Chưa có kết quả nào bạn đã đồng ý trong 30 ngày qua.</p>}
    {list.hasNextPage ? <button className="matching-secondary" disabled={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()} type="button">{list.isFetchingNextPage ? "Đang tải thêm…" : "Xem thêm"}</button> : null}
    <Link className="matching-secondary" to="/radar">Về Radar Hợp Gu</Link>
  </main>;
}

export function RadarReceivedResultPage() {
  const requestId = useParams().requestId ?? "";
  const queryClient = useQueryClient();
  const { epoch, session } = useRecipientSession();
  const [confirming, setConfirming] = useState(false);
  const [withdrawn, setWithdrawn] = useState(false);
  // After a withdrawal attempt whose outcome is unknown, the reading is reloaded from the server before
  // anything is promised about it.
  const [unconfirmed, setUnconfirmed] = useState(false);
  const queryKey = ["radar-received-result", epoch, requestId];
  const query = useQuery({
    queryKey,
    queryFn: ({ signal }) => getReceivedRadarResult(requestId, signal),
    enabled: epoch !== null && Boolean(requestId),
    gcTime: 0,
    refetchOnMount: "always",
    retry: false,
  });
  const withdraw = useMutation({
    mutationFn: () => withdrawReceivedRadar(requestId),
    onMutate: () => queryClient.cancelQueries({ queryKey }),
    onSuccess: async () => {
      await evictRadarReadings(queryClient);
      setWithdrawn(true);
    },
    onError: async (error) => {
      await evictRadarReadings(queryClient);
      if (!isTerminalDenial(error)) setUnconfirmed(true);
    },
  });

  if (withdrawn) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty"><div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/pair.webp" /></div><h1>Chart của bạn đã được rút.</h1><p>Kết quả chung đã bị xóa; cả hai phía đều không thể mở lại.</p><Link className="matching-primary" to="/radar/received">Về kết quả bạn đã nhận</Link></section></main>;
  if (session.isPending || (epoch !== null && (query.isPending || query.isFetching && !query.data))) {
    if (session.isError) return <MissingCard body="Mở lại Lá trên thiết bị bạn đã dùng để đồng ý, rồi thử lại." title="Chưa nhận ra phiên của bạn." />;
    return <main className="matching-page matching-page--loading"><Sparkle className="matching-pulse" /><p>{unconfirmed ? "Chưa xác nhận được việc rút chart. Đang kiểm tra lại…" : "Đang mở lại bản đọc của bạn…"}</p></main>;
  }
  // A definitive denial hides retained prose; a connection failure keeps a retry without showing stale data.
  if (!query.data || (query.isError && isTerminalDenial(query.error))) {
    // Only a definitive denial (of the read or of the withdrawal) is terminal; an inconclusive re-read keeps a retry.
    return isTerminalDenial(query.error) || isTerminalDenial(withdraw.error)
      ? <MissingCard body="Có thể bản đọc đã hết hạn hoặc chart đã được rút." title="Bản đọc này không còn mở được." />
      : <MissingCard body="Chưa kết nối được để mở lại bản đọc. Thử lại sau một chút nhé." onRetry={() => void query.refetch()} title="Chưa mở được bản đọc." />;
  }

  return <>
    {unconfirmed ? <p className="matching-message radar-receipt-error" role="alert">Chưa rút được chart: bản đọc vẫn còn trên máy chủ. Bạn có thể thử rút lại.</p> : null}
    <RadarResultView
      actionLabel={unconfirmed ? "Thử rút chart lại" : "Rút chart của tôi khỏi kết quả này"}
      onWithdraw={() => setConfirming(true)}
      result={query.data}
      withdrawing={withdraw.isPending}
    />
    <WithdrawSheet
      onCancel={() => setConfirming(false)}
      onConfirm={() => { setConfirming(false); withdraw.mutate(); }}
      open={confirming}
      pending={withdraw.isPending}
    />
  </>;
}

export function WithdrawSheet({ open, pending, onCancel, onConfirm }: { open: boolean; pending: boolean; onCancel: () => void; onConfirm: () => void }) {
  return <AppSheet closeDisabled={pending} onClose={onCancel} open={open} title="Rút chart khỏi kết quả này?">
    <p className="uv-confirm__body">Kết quả chung sẽ bị xóa với cả hai người và không mở lại được nữa. Việc này không hoàn tác được.</p>
    <div className="uv-confirm__actions">
      <button className="outline-button" disabled={pending} onClick={onCancel} type="button">Giữ lại</button>
      <button className="uv-danger-button" disabled={pending} onClick={onConfirm} type="button">Rút chart</button>
    </div>
  </AppSheet>;
}
