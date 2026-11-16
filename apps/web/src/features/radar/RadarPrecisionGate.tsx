import { ArrowRight, Sparkle } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

/** Shown instead of a Radar form when the owner's chart has no birth time or place yet. */
export function RadarPrecisionGate({ onStart }: { onStart: () => void }) {
  return <section className="radar-public__card radar-owner-gate">
    <Sparkle />
    <h2>Radar cần chart đủ giờ và nơi sinh của bạn trước.</h2>
    <Link className="matching-primary" onClick={onStart} to="/birth-time">Thêm giờ & nơi sinh của mình <ArrowRight /></Link>
  </section>;
}
