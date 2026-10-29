import { LinkBreak } from "@phosphor-icons/react";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { listShareLinks, revokeShareArtifact, type ShareLink } from "../../shared/api/client";

const FORMAT_LABEL: Record<ShareLink["format"], string> = {
  story_9_16: "Ảnh dọc 9:16",
  square_1_1: "Ảnh vuông 1:1",
};

const STATUS_LABEL: Record<ShareLink["status"], string> = {
  active: "Đang mở",
  revoked: "Đã thu hồi",
  expired: "Đã hết hạn",
};

function day(value: string): string {
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" }).format(new Date(value));
}

/**
 * The person's own share links (US-23 D2), including links made before a birth-date correction.
 * The server lists dates, format and status only: a link's address cannot be shown again because
 * only its hash is stored. Revoking is the only action; unsaving a note never revokes a link.
 */
export function ShareLinksSection() {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<string | null>(null);
  const links = useInfiniteQuery({
    queryKey: ["share-links"],
    queryFn: ({ pageParam, signal }) => listShareLinks(signal, pageParam),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    retry: false,
  });
  const revoke = useMutation({
    mutationFn: (artifactId: string) => revokeShareArtifact(artifactId),
    onSuccess: async () => {
      setMessage("Đã thu hồi link. Người đang giữ link sẽ không mở được nữa.");
      await queryClient.invalidateQueries({ queryKey: ["share-links"] });
    },
    onError: () => setMessage("Chưa thu hồi được link. Thử lại khi có kết nối nhé."),
  });
  const items = links.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <section aria-labelledby="share-links-title" className="settings-section share-links">
      <h2 id="share-links-title">Link đã chia sẻ</h2>
      <p>Mỗi link mở được 14 ngày. Link không hiện lại địa chỉ; bạn có thể thu hồi bất cứ lúc nào.</p>
      {message ? <p className="success-message" role="status">{message}</p> : null}
      {links.isPending ? <p role="status">Đang tải các link…</p> : null}
      {links.isError ? <p className="inline-error" role="alert">Chưa tải được danh sách link. Thử lại sau nhé.</p> : null}
      {links.isSuccess && items.length === 0 ? <p>Bạn chưa có link chia sẻ nào.</p> : null}
      {items.length > 0 ? (
        <ul className="share-links__list">
          {items.map((link) => (
            <li className="share-links__item" key={link.id}>
              <div>
                <strong>{FORMAT_LABEL[link.format]} · {STATUS_LABEL[link.status]}</strong>
                <small>Tạo {day(link.created_at)} · {link.status === "revoked" && link.revoked_at ? `thu hồi ${day(link.revoked_at)}` : `hết hạn ${day(link.expires_at)}`}</small>
              </div>
              {link.status === "active" ? (
                <button
                  className="detail-link"
                  disabled={revoke.isPending}
                  onClick={() => {
                    if (window.confirm("Thu hồi link này? Người đang giữ link sẽ không mở được nữa.")) {
                      setMessage(null);
                      revoke.mutate(link.id);
                    }
                  }}
                  type="button"
                >
                  <LinkBreak aria-hidden="true" size={16} /> Thu hồi link
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      {links.hasNextPage ? (
        <button className="text-button" disabled={links.isFetchingNextPage} onClick={() => void links.fetchNextPage()} type="button">
          {links.isFetchingNextPage ? "Đang tải…" : "Xem thêm link"}
        </button>
      ) : null}
    </section>
  );
}
