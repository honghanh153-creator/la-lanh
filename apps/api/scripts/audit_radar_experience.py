"""Fail a release when Radar works technically but reads like generic filler."""

import json
from datetime import UTC, datetime

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import ChartInput, RelationshipBundle
from app.domains.radar.reading import build_radar_reading
from app.domains.relationships.models import RelationshipVoice

FORBIDDEN = (
    "soulmate",
    "red flag",
    "chắc chắn",
    "định mệnh",
    "hai nhu cầu bật lên",
    "composite",
    "cross-aspect",
    "jyotish",
    "sau mutual",
    "a→b",
)
CONTEXTS = ("crush", "friend", "partner", "someone")


def _bundle() -> RelationshipBundle:
    engine = NatalChartEngine()
    first = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 5, 15, tzinfo=UTC),
            latitude=21.0285,
            longitude=105.8542,
        )
    )
    second = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1992, 7, 21, 12, 40, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    return engine.calculate_relationship_bundle(first, second)


def audit() -> None:
    bundle = _bundle()
    context_bodies: set[str] = set()
    voice_bodies: set[str] = set()
    for context in CONTEXTS:
        for voice in RelationshipVoice:
            reading = build_radar_reading(bundle, context=context, voice=voice)
            check = reading["sections"][-1]
            actions = check["highlights"]
            if not actions:
                raise SystemExit(f"experience gate: {context}/{voice} has no useful action")
            disclosed = {item["evidence_id"] for item in check["evidence"]}
            if any(not set(item["evidence_ids"]) <= disclosed for item in actions):
                raise SystemExit(f"experience gate: {context}/{voice} action lacks evidence")
            concepts = [item["concept_id"] for item in actions]
            if concepts != reading["metadata"]["concept_ids"]:
                raise SystemExit(f"experience gate: {context}/{voice} concept trace mismatch")
            visible = " ".join(
                [reading["headline"], reading["summary"], check["body"]]
                + [item["body"] for item in actions]
            ).lower()
            if any(term in visible for term in FORBIDDEN):
                raise SystemExit(f"experience gate: {context}/{voice} contains unsafe filler")
            if len(set(item["body"] for item in actions)) != len(actions):
                raise SystemExit(f"experience gate: {context}/{voice} repeats an action")
            serialized = json.dumps(reading, ensure_ascii=False)
            if any(raw in serialized for raw in ("1990", "1992", "21.0285", "106.6297")):
                raise SystemExit("experience gate: raw birth data reached the public projection")
            context_bodies.add(check["body"])
            if context == "crush":
                voice_bodies.add("|".join(item["body"] for item in actions))
    if len(context_bodies) != len(CONTEXTS):
        raise SystemExit("experience gate: context does not change the real-life guidance")
    if len(voice_bodies) != len(RelationshipVoice):
        raise SystemExit("experience gate: voice choice does not materially change delivery")
    print(
        "Radar experience audit passed: "
        f"{len(CONTEXTS)} contexts x {len(RelationshipVoice)} voices; "
        "actions are distinct, evidence-bound, contextual and privacy-minimized."
    )


if __name__ == "__main__":
    audit()
