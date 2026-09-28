import { ArrowLeft, Check, LockKey, MoonStars, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  ApiProblem,
  acknowledgeAuraTransition,
  getDailyNote,
  type DailyNote,
  type ReadingContent,
} from "../../shared/api/client";
import { useReadingUpdateActivation } from "../../shared/hooks/useReadingUpdateActivation";
import { readCachedDailyNote, writeCachedDailyNote } from "../../shared/storage/noteCache";
import "../../shared/styles/signal-note.css";
import { BrandMark } from "../../shared/ui/BrandMark";

const ACK_PREFIX = "la-lanh-aura-transition-ack-v1:";

const unlockLabels: Record<string, string> = {
  multi_factor: "Nhiều yếu tố được đọc cùng nhau",
  house_arena: "Các House và lĩnh vực đời sống",
  rising_angles: "Rising và các góc chính xác",
  current_sky: "Bầu trời hiện tại nối vào câu chuyện",
};

function acknowledgementKey(transitionId: string): string {
  return `${ACK_PREFIX}${transitionId}`;
}

function hasAcknowledged(transitionId: string | null): boolean {
  return Boolean(transitionId && localStorage.getItem(acknowledgementKey(transitionId)) === "1");
}

function acknowledge(transitionId: string): void {
  localStorage.setItem(acknowledgementKey(transitionId), "1");
}

export function AuraCutoverPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const hasFocusedHeading = useRef(false);
  const cachedAtStart = readCachedDailyNote();
  const [message, setMessage] = useState<string | null>(null);
  const focusHeadingOnMount = useCallback((heading: HTMLHeadingElement | null) => {
    if (!heading || hasFocusedHeading.current) return;
    hasFocusedHeading.current = true;
    heading.focus();
  }, []);
  const query = useQuery({
    queryKey: ["daily-note"],
    queryFn: async ({ signal }) => {
      const freshNote = await getDailyNote(signal);
      writeCachedDailyNote(freshNote);
      return freshNote;
    },
    initialData: cachedAtStart?.note,
    initialDataUpdatedAt: cachedAtStart ? 0 : undefined,
    retry: false,
  });
  const note = query.data;
  const projection = note?.reading_projection;
  const transition = projection?.aura_transition;
  const transitionId = transition?.transition_id ?? null;
  const preview = projection?.available_update?.content
    ?? (projection?.active.mode === "full_synthesis" ? projection.active : null);
  const alreadyActive = projection?.active.mode === "full_synthesis";
  const canActivate = Boolean(
    projection
    && transition?.profile_readiness === "aura_ready"
    && transitionId
    && projection.available_update
    && !alreadyActive,
  );
  const acknowledged = Boolean(
    transition?.acknowledged || (query.isError && hasAcknowledged(transitionId)),
  );

  const activationMutation = useReadingUpdateActivation({
    onSuccess: () => {
      setMessage("Aura đã trở thành bản Note hôm nay của bạn.");
      void queryClient.invalidateQueries({ queryKey: ["daily-note"] });
      void navigate("/home", { replace: true });
    },
    onError: (error) => {
      if (error instanceof ApiProblem && error.status === 409) {
        setMessage("Bản Aura đã thay đổi ở nơi khác. Lá Lành đã tải lại trạng thái hiện tại; bạn không mất bản Note đang dùng.");
        void query.refetch();
        return;
      }
      setMessage("Món quà chưa mở được. Bản Note hiện tại vẫn được giữ nguyên; bạn có thể thử lại.");
    },
  });

  const acknowledgementMutation = useMutation({
    mutationFn: ({ scopeKey, currentTransitionId }: {
      scopeKey: string;
      currentTransitionId: string;
    }) => acknowledgeAuraTransition(scopeKey, currentTransitionId),
    onSuccess: (updatedProjection, variables) => {
      acknowledge(variables.currentTransitionId);
      queryClient.setQueryData<DailyNote>(["daily-note"], (current) => {
        if (!current) return current;
        const updated = { ...current, reading_projection: updatedProjection };
        writeCachedDailyNote(updated);
        return updated;
      });
      void navigate("/home", { replace: true });
    },
    onError: (error) => {
      if (error instanceof ApiProblem && error.status === 409) {
        setMessage("Lựa chọn Aura đã thay đổi ở nơi khác. Lá Lành đang tải lại trạng thái mới nhất.");
        void query.refetch();
        return;
      }
      setMessage("Chưa thể lưu lựa chọn này. Bản Note hiện tại vẫn nguyên vẹn; bạn có thể thử lại.");
    },
  });

  const keepCurrent = () => {
    if (!projection || !transitionId) return;
    acknowledgementMutation.mutate({
      scopeKey: projection.scope_key,
      currentTransitionId: transitionId,
    });
  };

  const activate = () => {
    if (!projection?.available_update) return;
    activationMutation.mutate({
      scopeKey: projection.scope_key,
      revisionId: projection.available_update.revision_id,
    });
  };

  return (
    <main className="flow-page aura-cutover-page">
      <header className="flow-header">
        <button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft aria-hidden="true" /></button>
        <BrandMark />
        <span className="flow-header__step">Aura · lớp mới</span>
      </header>

      {query.isPending && !note ? <section className="aura-cutover-state" aria-live="polite"><span className="entry-loading__orbit" /><p>Đang mở receipt Aura…</p></section> : null}

      {query.isError && note ? <p className="cache-status" role="status">Đang xem receipt đã mở gần nhất trên máy. Bạn vẫn có thể chọn rõ ràng.</p> : null}

      {!query.isPending && !note ? (
        <section className="choice-panel aura-cutover-state" role="alert">
          <Sparkle aria-hidden="true" size={28} />
          <h1 ref={focusHeadingOnMount} tabIndex={-1}>Receipt Aura chưa về kịp.</h1>
          <p>Không có lớp mới nào được tự động đổi. Thử tải lại hoặc quay về Note hiện tại.</p>
          <button className="electric-button" onClick={() => void query.refetch()} type="button">Thử lại</button>
          <Link className="text-button" to="/home">Về Home</Link>
        </section>
      ) : null}

      {note && transition?.profile_readiness !== "aura_ready" ? (
        <section className="choice-panel aura-cutover-state" role="status">
          <p className="eyebrow"><LockKey aria-hidden="true" /> Chưa đủ điều kiện để mở Aura</p>
          <h1 ref={focusHeadingOnMount} tabIndex={-1}>{transition?.profile_readiness === "limited" ? "Kết quả hiện tại vẫn còn giới hạn." : "Aura chưa sẵn sàng."}</h1>
          <p>Receipt chỉ hiển thị những lớp được engine xác nhận. Không có preview hoặc chuyển bản đọc nào được tạo từ màn hình này.</p>
          <Link className="electric-button" to="/birth-time">Bổ sung dữ liệu sinh</Link>
          <Link className="text-button" to="/home">Về Home</Link>
        </section>
      ) : null}

      {note && transition?.profile_readiness === "aura_ready" ? (
        <>
          <section className="aura-cutover-hero" aria-labelledby="aura-cutover-title">
            <span className="aura-cutover-hero__orb" aria-hidden="true"><Sparkle weight="fill" size={34} /></span>
            <p className="eyebrow">Một lớp đọc mới đã được tính</p>
            <h1 id="aura-cutover-title" ref={focusHeadingOnMount} tabIndex={-1}>Aura không tự thay Note của bạn.</h1>
            <p>Giờ đây bạn có thể xem món quà, đọc thử một đoạn, rồi tự chọn dùng Aura hôm nay hoặc giữ bản hiện tại.</p>
            {acknowledged ? <p className="aura-cutover-ack" role="status"><Check aria-hidden="true" /> Bạn đã xem lựa chọn này trước đó.</p> : null}
          </section>

          <section className="choice-panel aura-receipt" aria-labelledby="aura-receipt-title">
            <p className="eyebrow"><MoonStars aria-hidden="true" /> Receipt mở khóa</p>
            <h2 id="aura-receipt-title">Những lớp được xác nhận</h2>
            <ul>
              {(transition.unlock_layers ?? []).map((layer) => <li key={layer}><Check aria-hidden="true" /> {unlockLabels[layer] ?? "Một lớp diễn giải được xác nhận"}</li>)}
            </ul>
            <small>Receipt này chỉ là mô tả lớp đã được tính; nó không thay thế quyền quyết định của bạn.</small>
          </section>

          {preview ? <AuraPreview content={preview} /> : (
            <section className="choice-panel aura-cutover-state" role="status">
              <h2>Preview đang được chuẩn bị.</h2>
              <p>Không có bản đọc mới nào được hiện ra khi server chưa gửi đủ evidence. Bản hiện tại vẫn nguyên vẹn.</p>
            </section>
          )}

          <section className="aura-cutover-actions" aria-label="Chọn bản đọc hôm nay">
            <Link className="natal-unlock-link" to="/natal"><Sparkle aria-hidden="true" /><span><strong>Bạn có muốn hiểu mình hơn?</strong><small>Mở bản Natal: pattern hay lặp lại, điều đang học và cách tự đối chiếu.</small></span></Link>
            {canActivate ? <button className="electric-button" disabled={activationMutation.isPending} onClick={activate} type="button">
              {activationMutation.isPending ? "Đang mở Aura…" : "Dùng Aura hôm nay"}
            </button> : null}
            {!alreadyActive ? <button className="outline-button" disabled={acknowledgementMutation.isPending} onClick={keepCurrent} type="button">{acknowledgementMutation.isPending ? "Đang lưu lựa chọn…" : "Giữ Note hiện tại"}</button> : <Link className="electric-button" to="/home">Tiếp tục với Aura</Link>}
            {message ? <p className="aura-cutover-message" role="status">{message}</p> : null}
          </section>
        </>
      ) : null}
    </main>
  );
}

function AuraPreview({ content }: { content: ReadingContent }) {
  return (
    <section className="choice-panel aura-preview" aria-labelledby="aura-preview-title">
      <p className="eyebrow">Preview Note Aura</p>
      <h2 id="aura-preview-title">{content.sections.hook}</h2>
      <p>{content.sections.thesis}</p>
      <div className="aura-preview__line"><strong>Ngoài đời có thể trông như…</strong><span>{content.sections.manifestation}</span></div>
      <small>{content.disclaimer}</small>
    </section>
  );
}
