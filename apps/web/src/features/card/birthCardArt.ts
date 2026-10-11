import type { ZodiacSign } from "../../shared/api/client";
import { signDetails } from "../../shared/astro/signs";
import { elementBySign, elementNames, personaTag, SHARE_PRIVACY_FOOTER, type ShareArtSpec } from "./shareArt";

export const BIRTH_CARD_SUPPORT = "Một phần bản đồ của bạn — không phải chiếc hộp định nghĩa bạn.";

/**
 * Lá Khai Sinh share art. Inputs are the sun sign (shown as provenance, as the reveal already does)
 * and the server persona label; birth date/time/place are never passed in.
 */
export function birthArtSpec(sign: ZodiacSign, personaLabel?: string | null): ShareArtSpec {
  const detail = signDetails[sign];
  const element = elementBySign[sign];
  return {
    kicker: "Lá Khai Sinh",
    hook: detail.note,
    support: BIRTH_CARD_SUPPORT,
    badge: `Mặt Trời ${detail.label} · ${elementNames[element]}`,
    tag: personaTag(personaLabel),
    element,
    sign,
    footer: SHARE_PRIVACY_FOOTER,
  };
}
