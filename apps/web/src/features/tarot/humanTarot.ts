import { useQuery } from "@tanstack/react-query";

import { getHumanTarotAvailability, type HumanTarotAvailability } from "../../shared/api/client";

export type TarotMode = "self" | "human";

export function formatVietnamTime(iso: string): string {
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(new Date(iso));
}

/** dd/MM in Vietnam time (the locale's own separator varies between engines). */
export function formatVietnamDay(iso: string): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "2-digit",
    timeZone: "Asia/Ho_Chi_Minh",
  }).formatToParts(new Date(iso));
  const part = (type: string) => parts.find((item) => item.type === type)?.value ?? "";
  return `${part("day")}/${part("month")}`;
}

/** The availability of the human reader, or null while unknown or switched off (option hidden). */
export function useHumanTarotAvailability(): HumanTarotAvailability | null {
  const query = useQuery({
    queryKey: ["human-tarot-availability"],
    queryFn: ({ signal }) => getHumanTarotAvailability(signal),
    retry: false,
    refetchOnWindowFocus: true,
  });
  return query.data?.enabled ? query.data : null;
}
