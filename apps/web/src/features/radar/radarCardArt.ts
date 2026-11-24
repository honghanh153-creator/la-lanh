import { SHARE_PRIVACY_FOOTER, type ShareArtSpec } from "../card/shareArt";
import { radarContextLabel } from "./radarOptions";

/** The Hợp gu card image: tier, one line, the relationship and at most an initial. Never a
 *  birth date, a real name or a chart term (AL1 direction C). */
export function radarCardSpec(card: { context: string; tier: string; line: string; initial?: string | null }): ShareArtSpec {
  return {
    kicker: card.initial ? `Hợp gu · Bạn × ${card.initial}` : "Hợp gu",
    hook: card.tier,
    support: card.line,
    badge: radarContextLabel(card.context),
    tag: null,
    element: null,
    sign: null,
    footer: SHARE_PRIVACY_FOOTER,
  };
}

/** "M." from the nickname the owner chose; null when it has no letter. */
export function radarInitial(label: string | null | undefined): string | null {
  const letter = [...(label ?? "").normalize("NFC").trim()].find((char) => /\p{L}/u.test(char));
  return letter ? `${letter.toUpperCase()}.` : null;
}
