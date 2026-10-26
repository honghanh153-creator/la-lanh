"""R02 (audit 2026-10-22, US-22 AC07): a served private check never cites a contact that is only
within orb at the invented noon of an unknown birth time."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import BodyName, CalculationConfig, ChartInput, TimePrecision
from app.domains.radar.reading import build_radar_reading
from app.domains.relationships.models import RelationshipVoice

WITNESS = "syn:sun:opposition:sun:4.80"


def _bundle(*, unknown: bool):  # type: ignore[no-untyped-def]
    engine, config = NatalChartEngine(), CalculationConfig.western_recommended()
    a = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 5, 15, tzinfo=UTC),
            latitude=21.0285,
            longitude=105.8542,
        ),
        config,
    )
    noon = datetime(1992, 7, 7, 12, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")).astimezone(UTC)
    b = engine.calculate_chart(
        ChartInput(utc_datetime=noon, latitude=10.8231, longitude=106.6297), config
    )
    if unknown:  # as BirthService.calculate_transient_chart does for an unknown time
        b = b.model_copy(
            update={
                "time_precision": TimePrecision.UNKNOWN,
                "bodies": tuple(x for x in b.bodies if x.body is not BodyName.MOON),
                "aspects": tuple(x for x in b.aspects if BodyName.MOON not in {x.body_a, x.body_b}),
                "houses": None,
                "angles": None,
            }
        )
    return engine.calculate_relationship_bundle(a, b)


@pytest.mark.parametrize("context", ["crush", "friend", "partner", "someone"])
@pytest.mark.parametrize("voice", list(RelationshipVoice))
def test_unknown_time_reading_does_not_cite_an_uncertain_contact(
    context: str, voice: RelationshipVoice
) -> None:
    served = json.dumps(build_radar_reading(_bundle(unknown=True), context=context, voice=voice))
    assert WITNESS not in served
    assert re.search(r"syn:[a-z_]+:[a-z]+:moon:", served) is None  # B's Moon is never used


def test_control_the_same_noon_with_a_known_time_still_cites_it() -> None:
    served = json.dumps(build_radar_reading(_bundle(unknown=False), context="crush"))
    assert WITNESS in served
