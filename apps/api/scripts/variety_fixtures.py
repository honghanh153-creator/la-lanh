"""Generate the synthetic fixtures for the variety baseline (P1).

Everything is derived from a fixed seed, so a rerun produces byte-identical files.
No real user data. Spec: docs/foundation/la-lanh-variety-measurement-spec.md §1.

    uv run python -m scripts.variety_fixtures          # write
    uv run python -m scripts.variety_fixtures --check  # fail if the committed files drift
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

SEED = "la-lanh-variety-fixtures-v1"
OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "variety"
EXACT_PROFILES = 900
DATE_ONLY_PROFILES = 300
SAME_DATE_PAIRS = 20
RADAR_PAIRS = 50

# Coordinates of Vietnamese cities (public geography). Times are local Asia/Ho_Chi_Minh.
PLACES: tuple[tuple[str, float, float], ...] = (
    ("ha-noi", 21.0285, 105.8542),
    ("ho-chi-minh", 10.8231, 106.6297),
    ("da-nang", 16.0544, 108.2022),
    ("hue", 16.4637, 107.5909),
    ("can-tho", 10.0452, 105.7469),
    ("hai-phong", 20.8449, 106.6881),
    ("nha-trang", 12.2388, 109.1967),
    ("da-lat", 11.9404, 108.4583),
)


def _birth_date(rng: random.Random) -> date:
    start, end = date(1970, 1, 1), date(2008, 12, 31)
    return start + timedelta(days=rng.randrange((end - start).days + 1))


def _exact(rng: random.Random, profile_id: str) -> dict[str, Any]:
    place, lat, lon = PLACES[rng.randrange(len(PLACES))]
    return {
        "id": profile_id,
        "time_known": True,
        "birth_date": _birth_date(rng).isoformat(),
        "birth_time_local": f"{rng.randrange(24):02d}:{rng.randrange(60):02d}",
        "place": place,
        "latitude": lat,
        "longitude": lon,
        "focus": None,
    }


def _date_only(birth: date, profile_id: str) -> dict[str, Any]:
    return {"id": profile_id, "time_known": False, "birth_date": birth.isoformat(), "focus": None}


def build() -> dict[str, dict[str, Any]]:
    rng = random.Random(SEED)  # noqa: S311 - deterministic synthetic fixtures, not security
    profiles = [_exact(rng, f"exact-{i:04d}") for i in range(EXACT_PROFILES)]
    profiles += [_date_only(_birth_date(rng), f"date-{i:04d}") for i in range(DATE_ONLY_PROFILES)]
    pairs = []
    for i in range(SAME_DATE_PAIRS):
        birth = _birth_date(rng)
        pairs.append([_date_only(birth, f"same-{i:02d}-a"), _date_only(birth, f"same-{i:02d}-b")])
    radar = []
    for i in range(RADAR_PAIRS):
        a = _exact(rng, f"radar-{i:02d}-a")
        b = _exact(rng, f"radar-{i:02d}-b")
        if i % 2:  # half of the partners have no known birth time
            b = {**b, "time_known": False, "birth_time_local": None}
        radar.append({"id": f"radar-{i:02d}", "a": a, "b": b})
    return {
        "profiles-v1.json": _wrap(
            "variety-profiles-v1",
            {"profiles": profiles, "same_birthdate_pairs": pairs},
            "Focus is null for everyone: the focus feature (F) does not exist yet.",
        ),
        "radar-pairs-v1.json": _wrap("variety-radar-pairs-v1", {"pairs": radar}, None),
    }


def _wrap(version: str, body: dict[str, Any], note: str | None) -> dict[str, Any]:
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
    meta: dict[str, Any] = {
        "version": version,
        "seed": SEED,
        "synthetic": True,
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }
    if note:
        meta["note"] = note
    return {"meta": meta, **body}


def render(doc: dict[str, Any]) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    drift = []
    for name, doc in build().items():
        path = OUT / name
        text = render(doc)
        if args.check:
            if not path.exists() or path.read_text() != text:
                drift.append(name)
        else:
            path.write_text(text)
    if drift:
        sys.exit(f"variety fixtures drifted: {', '.join(drift)} (run scripts.variety_fixtures)")
    print("variety fixtures " + ("current" if args.check else f"written to {OUT}"))


if __name__ == "__main__":
    main()
