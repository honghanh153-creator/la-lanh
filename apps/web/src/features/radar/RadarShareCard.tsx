import { DownloadSimple, LinkSimple, ShareNetwork, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { createRadarCard, getRadarConsentOptions, listRadarCards, revokeRadarCard, type RadarResult } from "../../shared/api/client";
import { shareArtAlt } from "../card/shareArt";
import { ShareArtPreview } from "../card/ShareArtPreview";
import { useShareArt } from "../card/useShareArt";
import { radarCardSpec, radarInitial } from "./radarCardArt";

const FORMAT = "square_1_1" as const;

/**
 * Hợp gu card (AL1 direction C): an image drawn on this device with the tier, one line and the
 * relationship. No name unless the owner asks for the first letter. A revocable link is offered
 * only when the server has card links on.
 */
export function RadarShareCard({ result }: { result: RadarResult }) {
  const [open, setOpen] = useState(false);
  const [showInitial, setShowInitial] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const requestId = result.request_id ?? "";
  const tier = result.pair_signature?.tier?.label ?? result.pair_signature?.kicker ?? "";
  const line = result.pair_signature?.headline ?? result.headline;
  const spec = useMemo(() => (open ? radarCardSpec({
    context: result.context ?? "someone",
    tier,
    line,
    initial: showInitial ? radarInitial(result.recipient_label) : null,
  }) : null), [open, result.context, result.recipient_label, tier, line, showInitial]);
  const art = useShareArt(spec, FORMAT);
  const options = useQuery({ queryKey: ["radar-consent-options"], queryFn: ({ signal }) => getRadarConsentOptions(signal), retry: false, staleTime: 60_000, enabled: open });
  const linksOn = options.data?.card_links === true;
  const links = useQuery({ queryKey: ["radar-cards", requestId], queryFn: ({ signal }) => listRadarCards(requestId, signal), enabled: open && linksOn && Boolean(requestId), retry: false, gcTime: 0 });
  const create = useMutation({
    mutationFn: () => createRadarCard(requestId, showInitial),
    onSuccess: async (card) => {
      void queryClient.invalidateQueries({ queryKey: ["radar-cards", requestId] });
      if (!card.share_url) return;
      try {
        await navigator.clipboard.writeText(new URL(card.share_url, window.location.origin).toString());
        setMessage("Đã chép link xem thẻ. Bạn thu hồi được bất cứ lúc nào.");
      } catch {
        setMessage("Đã tạo link xem thẻ nhưng chưa chép được. Thử lại nhé.");
      }
    },
    onError: () => setMessage("Chưa tạo được link. Thử lại sau nhé."),
  });
  const revoke = useMutation({
    mutationFn: revokeRadarCard,
    onSuccess: () => {
      setMessage("Đã thu hồi link. Ai mở link đó sẽ không xem được nữa.");
      void queryClient.invalidateQueries({ queryKey: ["radar-cards", requestId] });
    },
    onError: () => setMessage("Chưa thu hồi được. Thử lại nhé."),
  });

  const download = async () => {
    if (!art.ready) return;
    try {
      const file = await art.pngFile("la-lanh-hop-gu.png");
      const url = URL.createObjectURL(file);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = file.name;
      anchor.click();
      URL.revokeObjectURL(url);
      setMessage("Đã lưu ảnh thẻ.");
    } catch {
      setMessage("Chưa lưu được ảnh. Thử lại nhé.");
    }
  };

  if (!requestId) return null;
  if (!open) return <button className="matching-secondary radar-card-open" onClick={() => setOpen(true)} type="button"><ShareNetwork /> Tạo thẻ</button>;
  return <section aria-labelledby="radar-card-heading" className="radar-card">
    <h2 id="radar-card-heading">Thẻ Hợp gu</h2>
    {spec ? <ShareArtPreview alt={shareArtAlt(spec, FORMAT)} format={FORMAT} svg={art.svg} /> : null}
    <label className="consent-check"><input checked={showInitial} onChange={(event) => setShowInitial(event.target.checked)} type="checkbox" /><span>Hiện chữ cái đầu của tên</span></label>
    <button className="matching-primary" disabled={!art.ready} onClick={() => void download()} type="button"><DownloadSimple /> Lưu ảnh</button>
    {linksOn ? <button className="matching-secondary" disabled={create.isPending} onClick={() => create.mutate()} type="button"><LinkSimple /> {create.isPending ? "Đang tạo link…" : "Gửi link xem thẻ"}</button> : null}
    {linksOn && links.data?.some((item) => item.status === "active") ? <ul className="radar-card__links">{links.data.filter((item) => item.status === "active").map((item) => <li key={item.id}><span>Link tạo lúc {new Date(item.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Ho_Chi_Minh" })}</span><button aria-label="Thu hồi link này" disabled={revoke.isPending} onClick={() => revoke.mutate(item.id)} type="button"><Trash /> Thu hồi</button></li>)}</ul> : null}
    {message ? <p className="matching-message" role="status">{message}</p> : null}
  </section>;
}
