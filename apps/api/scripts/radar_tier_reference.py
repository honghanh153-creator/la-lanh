"""Reference distribution for Hợp gu tiers (``radar-tier-ref-v1``).

Tiers are ranked, not raw: a pair's ease signal is placed against 2,000 synthetic pairs built
from a fixed seed, so each tier holds a known share of pairs instead of every pair landing in a
compressed middle band. Synthetic only: no user data, no network.

    uv run python -m scripts.radar_tier_reference           # print quantiles and shares
    uv run python -m scripts.radar_tier_reference --check   # fail if reading.py differs

The pair mix mirrors ``radar-pairs-v1``: person A always has an exact birth time (Radar needs an
exact owner chart); person B has an unknown time for 25% of pairs and is then treated like
``BirthService.calculate_transient_chart`` (no Moon, houses or angles).

``--basis date_only`` builds ``radar-tier-ref-date-v1`` (Hợp gu AL1): both people are read from
their birth dates alone, as ``BirthChartService.calculate_date_only_chart`` does (local noon in
Asia/Ho_Chi_Minh, then no Moon, houses or angles).

    uv run python -m scripts.radar_tier_reference --basis date_only [--check]
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput, NatalChart, TimePrecision
from app.domains.birth.service import DATE_ONLY_REFERENCE_POINT, date_only_reduction
from app.domains.radar import reading

SEED = "la-lanh-radar-tier-ref-v1"
DATE_ONLY_SEED = "la-lanh-radar-tier-ref-date-v1"
PAIRS = 2_000
UNKNOWN_TIME_SHARE = 0.25
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
FIRST_DAY = date(1960, 1, 1)
LAST_DAY = date(2007, 12, 31)
PLACES = (
    (21.0285, 105.8542),  # Hà Nội
    (10.8231, 106.6297),  # TP Hồ Chí Minh
    (16.0544, 108.2022),  # Đà Nẵng
    (20.8449, 106.6881),  # Hải Phòng
    (10.0452, 105.7469),  # Cần Thơ
    (16.4637, 107.5909),  # Huế
    (12.2388, 109.1967),  # Nha Trang
    (11.9404, 108.4583),  # Đà Lạt
    (18.6796, 105.6813),  # Vinh
    (13.7829, 109.2196),  # Quy Nhơn
)


def _chart(
    engine: NatalChartEngine, rng: random.Random, *, unknown: bool, date_only: bool = False
) -> NatalChart:
    day = FIRST_DAY + timedelta(days=rng.randrange((LAST_DAY - FIRST_DAY).days + 1))
    minute = 12 * 60 if unknown or date_only else rng.randrange(24 * 60)
    latitude, longitude = PLACES[rng.randrange(len(PLACES))]
    if date_only:
        latitude, longitude = DATE_ONLY_REFERENCE_POINT
    local = datetime.combine(day, time(minute // 60, minute % 60), TZ)
    chart = engine.calculate_chart(
        ChartInput(utc_datetime=local.astimezone(UTC), latitude=latitude, longitude=longitude),
        CalculationConfig.western_recommended(),
    )
    if date_only:
        return date_only_reduction(chart)
    if not unknown:
        return chart
    return chart.model_copy(
        update={
            "time_precision": TimePrecision.UNKNOWN,
            "bodies": tuple(b for b in chart.bodies if b.body.value != "moon"),
            "aspects": tuple(
                a for a in chart.aspects if "moon" not in {a.body_a.value, a.body_b.value}
            ),
            "houses": None,
            "angles": None,
        }
    )


def reference_signals(
    pairs: int = PAIRS, *, basis: str = reading.BASIS_FULL
) -> list[reading.PairSignals | None]:
    engine = NatalChartEngine()
    date_only = basis == reading.BASIS_DATE_ONLY
    seed = DATE_ONLY_SEED if date_only else SEED
    rng = random.Random(seed)  # noqa: S311 - a reproducible synthetic fixture, not a secret
    reference = reading.TIER_REFERENCE_DATE_ONLY if date_only else reading.TIER_REFERENCE
    out: list[reading.PairSignals | None] = []
    for _ in range(pairs):
        a = _chart(engine, rng, unknown=False, date_only=date_only)
        b = _chart(engine, rng, unknown=rng.random() < UNKNOWN_TIME_SHARE, date_only=date_only)
        out.append(
            reading.pair_signals(engine.calculate_relationship_bundle(a, b), reference=reference)
        )
    return out


def quantiles(values: list[float], steps: int = 20) -> tuple[float, ...]:
    """p0, p5, ..., p100 with linear interpolation (Hyndman-Fan type 7), rounded to 4 places."""

    ordered = sorted(values)
    cuts = statistics.quantiles(ordered, n=steps, method="inclusive")
    return tuple(round(value, 4) for value in (ordered[0], *cuts, ordered[-1]))


def report(
    signals: list[reading.PairSignals | None], *, basis: str = reading.BASIS_FULL
) -> dict[str, object]:
    ranked = [item for item in signals if item is not None]
    tiers = Counter(item.tier for item in ranked)
    return {
        "calibration_version": reading.TIER_CALIBRATION_DATE_ONLY_VERSION
        if basis == reading.BASIS_DATE_ONLY
        else reading.TIER_CALIBRATION_VERSION,
        "pairs": len(signals),
        "low_signal_pairs": len(signals) - len(ranked),
        "ease_quantiles": list(quantiles([item.ease for item in ranked])),
        "tier_share": {key: round(tiers[key] / len(ranked), 3) for key, _ in reading.TIER_BANDS},
        "tension_share": round(sum(item.tension is not None for item in ranked) / len(ranked), 3),
        "tension_threshold": reading.TENSION_THRESHOLD,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--basis", choices=reading.BASES, default=reading.BASIS_FULL)
    args = parser.parse_args()
    signals = reference_signals(basis=args.basis)
    result = report(signals, basis=args.basis)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    expected = (
        reading.TIER_REFERENCE_DATE_ONLY
        if args.basis == reading.BASIS_DATE_ONLY
        else reading.TIER_REFERENCE
    )
    if args.check and tuple(result["ease_quantiles"]) != expected:  # type: ignore[arg-type]
        raise SystemExit(
            "radar tier reference differs from reading.TIER_REFERENCE; regenerate it, bump "
            "TIER_CALIBRATION_VERSION and refresh the fallback approval"
        )


if __name__ == "__main__":
    main()
