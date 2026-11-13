"""Every body the engine can emit has a Vietnamese display name in each display map (#143).

Exact birth times give aspects to Saturn…Pluto, the nodes and Chiron; a missing entry let the
English enum value ("Saturn") leak into the Khám phá aspect line.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import BodyName, CalculationConfig, ChartInput
from app.domains.daily.service import BODY_LABELS as DAILY_BODY_LABELS
from app.domains.radar.reading import BODY_LABELS as RADAR_BODY_LABELS
from app.domains.readings.knowledge import BODY_LABELS as KNOWLEDGE_BODY_LABELS
from app.domains.readings.service import BODY_VI, InsightReadingService

REPO_ROOT = Path(__file__).resolve().parents[4]
WEB_CURRENT_SKY = REPO_ROOT / "apps/web/src/features/insights/CurrentSkyPage.tsx"

# "Chiron" is the name the app already shows in Vietnamese copy; no other body keeps its English
# enum spelling.
KEPT_ENGLISH = {BodyName.CHIRON}
ENGLISH_NAMES = re.compile(
    r"\b(Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto|"
    r"True Node|Mean Node|South Node|True_Node|Mean_Node|South_Node)\b"
)


def _web_current_sky_labels() -> dict[str, str]:
    source = WEB_CURRENT_SKY.read_text(encoding="utf-8")
    block = re.search(r"const BODY_LABELS[^=]*=\s*\{(?P<body>.*?)\};", source, re.DOTALL)
    assert block, "BODY_LABELS not found in CurrentSkyPage.tsx"
    return dict(re.findall(r"(\w+):\s*\"([^\"]+)\"", block.group("body")))


def _maps() -> dict[str, dict[str, str]]:
    return {
        "readings.service.BODY_VI": {body.value: label for body, label in BODY_VI.items()},
        "daily.service.BODY_LABELS": {
            body.value: label for body, label in DAILY_BODY_LABELS.items()
        },
        "radar.reading.BODY_LABELS": {
            body.value: label for body, label in RADAR_BODY_LABELS.items()
        },
        "readings.knowledge.BODY_LABELS": dict(KNOWLEDGE_BODY_LABELS),
        "web CurrentSkyPage BODY_LABELS": _web_current_sky_labels(),
    }


@pytest.mark.parametrize("map_name", sorted(_maps()))
def test_every_engine_body_has_a_vietnamese_display_name(map_name: str) -> None:
    labels = _maps()[map_name]
    missing = [body.value for body in BodyName if not labels.get(body.value, "").strip()]
    assert not missing, f"{map_name} has no Vietnamese name for {missing}"
    english = [
        body.value
        for body in BodyName
        if body not in KEPT_ENGLISH and ENGLISH_NAMES.search(labels[body.value])
    ]
    assert not english, f"{map_name} shows English names for {english}"


def test_reading_service_uses_the_same_names_as_daily_and_radar() -> None:
    assert BODY_VI == DAILY_BODY_LABELS == RADAR_BODY_LABELS


def test_exact_time_aspect_lines_never_show_an_english_body_name() -> None:
    engine = NatalChartEngine()
    service = InsightReadingService()
    seen_slow_body = False
    for month in range(1, 13):
        chart = engine.calculate_chart(
            ChartInput(
                utc_datetime=datetime(1991, month, 15, 3, 30, tzinfo=UTC),
                latitude=21.0285,
                longitude=105.8542,
            ),
            CalculationConfig.western_recommended(),
        )
        reading = service.overview(chart, observed_at=datetime(2026, 11, 4, tzinfo=UTC))
        for claim in reading.claims:
            lines = (*claim.evidence, claim.watch_for)
            seen_slow_body |= any(
                label in line
                for line in lines
                for label in ("Sao Thổ", "Thiên Vương", "Hải Vương", "Diêm Vương")
            )
            for line in lines:
                assert not ENGLISH_NAMES.search(line), line
    assert seen_slow_body, "sweep never produced an aspect to a slow body"


def test_jyotish_overview_still_reads_the_six_classic_bodies_only() -> None:
    chart = NatalChartEngine().calculate_chart(
        ChartInput(
            utc_datetime=datetime(1991, 6, 15, 3, 30, tzinfo=UTC),
            latitude=21.0285,
            longitude=105.8542,
        ),
        CalculationConfig.jyotish_recommended(),
    )
    claims = (
        InsightReadingService().overview(chart, observed_at=datetime(2026, 9, 4, tzinfo=UTC)).claims
    )
    assert [claim.id for claim in claims] == [
        f"{body.value}-sign"
        for body in (
            BodyName.SUN,
            BodyName.MOON,
            BodyName.MERCURY,
            BodyName.VENUS,
            BodyName.MARS,
            BodyName.JUPITER,
        )
    ]
