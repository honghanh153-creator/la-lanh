import type { NamedCard } from "./tarotCardName";

/** The English · Vietnamese pair for visible headings, with the English part marked as English. */
export function CardName({ card }: { card: NamedCard }) {
  if (!card.title_en || card.title_en === card.title_vi) return <>{card.title_vi}</>;
  return <><span lang="en">{card.title_en}</span> · {card.title_vi}</>;
}
