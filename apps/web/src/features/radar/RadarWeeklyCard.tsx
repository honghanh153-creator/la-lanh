import { HeartStraight, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteRadarWeekly, getRadarConsentOptions, getRadarWeekly } from "../../shared/api/client";
import { radarContextLabel } from "./radarOptions";
import "./radarWeekly.css";

/**
 * "Hai bạn tuần này" on Hôm nay (Hợp gu AL1 direction C, off by default). Shows only pairs the
 * owner chose to keep, by initial; turning one off deletes it. Renders nothing while the feature
 * is off, the lines are not approved, or there is no kept pair.
 */
export function RadarWeeklyCard() {
  const queryClient = useQueryClient();
  const options = useQuery({ queryKey: ["radar-consent-options"], queryFn: ({ signal }) => getRadarConsentOptions(signal), retry: false, staleTime: 60_000 });
  const on = options.data?.weekly === true;
  const weekly = useQuery({ queryKey: ["radar-weekly"], queryFn: ({ signal }) => getRadarWeekly(signal), enabled: on, retry: false, gcTime: 0 });
  const remove = useMutation({
    mutationFn: deleteRadarWeekly,
    onSettled: () => void queryClient.invalidateQueries({ queryKey: ["radar-weekly"] }),
  });
  const items = weekly.data?.items ?? [];
  const note = options.data?.weekly_sentences?.["home-note"];
  if (!on || !items.length) return null;
  return <section aria-labelledby="radar-weekly-heading" className="radar-weekly">
    <h2 id="radar-weekly-heading"><HeartStraight weight="fill" /> Hai bạn tuần này</h2>
    {items.map((item) => <article key={item.id}>
      <p className="radar-weekly__who">Bạn × {item.initial ?? "người ấy"} · {radarContextLabel(item.context)}</p>
      {item.quiet ? <p>{item.quiet}</p> : null}
      {item.easy ? <p>{item.easy}</p> : null}
      {item.watch ? <p>{item.watch}</p> : null}
      {item.try_line ? <p>{item.try_line}</p> : null}
      <button aria-label={`Tắt nhắc cặp Bạn × ${item.initial ?? "người ấy"}`} disabled={remove.isPending} onClick={() => remove.mutate(item.id)} type="button"><Trash /> Tắt nhắc cặp này</button>
    </article>)}
    {note ? <p className="radar-weekly__note">{note}</p> : null}
    {remove.isError ? <p role="alert">Chưa tắt được. Thử lại nhé.</p> : null}
  </section>;
}
