import type { TarotCard } from "../../shared/api/client";

export type NamedCard = Pick<TarotCard, "title_en" | "title_vi">;

/**
 * Card name as plain text: the traditional English title and the Vietnamese title together
 * (owner decision 19/10/2026, US-20 AC12), e.g. "The Devil · Sợi Ràng". Used for labels, live
 * regions and accessible names, so a reader who knows the classic deck recognises the card.
 */
export function cardName(card: NamedCard): string {
  return card.title_en && card.title_en !== card.title_vi ? `${card.title_en} · ${card.title_vi}` : card.title_vi;
}
