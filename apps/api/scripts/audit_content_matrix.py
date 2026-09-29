from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.domains.astro.models import BodyName, RelationshipDimension
from app.domains.radar.reading import (
    ASPECT_CHANNELS,
    ASPECT_LABELS,
    BODY_ACTIONS,
    BODY_FUNCTIONS,
    BODY_LABELS,
    BODY_RECEPTIONS,
    BODY_SHARED_ROLES,
    CONTEXT_CHECKS,
    SCENE_COPY,
)
from app.domains.readings.interpretive_lenses import (
    CURRENT_FORCES,
    ELEMENTS,
    HOUSE_MODES,
    METHODOLOGY_SOURCE_IDS,
    MODALITIES,
    PLANET_PERSPECTIVES,
    EditorialMode,
    InterpretiveLens,
)
from app.domains.readings.knowledge import (
    ASPECTS,
    HOUSES,
    LENS_ACTIONS,
    LENS_HOOKS,
    LENS_MANIFESTATIONS,
    PLANETS,
    SIGNS,
)
from app.domains.readings.models import INTERPRETATION_KNOWLEDGE_VERSION, BackgroundLens
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS
from app.domains.relationships.knowledge import (
    BOOK_SOURCES,
    EDITORIAL_CONCEPTS,
    RELATIONSHIP_KNOWLEDGE_VERSION,
    VOICE_PROFILES,
)
from app.domains.tarot.knowledge import BOOK_SOURCES as TAROT_BOOK_SOURCES

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASELINE = REPOSITORY_ROOT / "docs" / "operations" / "content-matrix-baseline.json"
RADAR_THEME_KEYS = {
    "communication",
    "emotional",
    "attraction",
    "pace",
    "clarity",
    "freedom",
    "intensity",
    "visibility",
}


def current_metrics() -> dict[str, int]:
    return {
        "daily_planets": len(PLANETS),
        "daily_signs": len(SIGNS),
        "daily_houses": len(HOUSES),
        "daily_aspects": len(ASPECTS),
        "daily_interpretive_lenses": len(InterpretiveLens),
        "daily_editorial_modes": len(EditorialMode),
        "daily_semantic_cycle_days": len(InterpretiveLens) * len(EditorialMode) * 3 * 7,
        "daily_methodology_sources": len(METHODOLOGY_SOURCE_IDS),
        "relationship_sources": len(BOOK_SOURCES),
        "relationship_concepts": len(EDITORIAL_CONCEPTS),
        "relationship_dimensions": len(RelationshipDimension),
        "relationship_voice_profiles": len(VOICE_PROFILES),
        "radar_themes": len(SCENE_COPY),
        "radar_contexts": len(CONTEXT_CHECKS),
        "tarot_sources": len(TAROT_BOOK_SOURCES),
    }


def validate_matrix() -> list[str]:
    failures: list[str] = []
    expected_bodies = set(BodyName)
    body_maps = {
        "BODY_LABELS": BODY_LABELS,
        "BODY_FUNCTIONS": BODY_FUNCTIONS,
        "BODY_ACTIONS": BODY_ACTIONS,
        "BODY_RECEPTIONS": BODY_RECEPTIONS,
        "BODY_SHARED_ROLES": BODY_SHARED_ROLES,
    }
    for name, mapping in body_maps.items():
        if set(mapping) != expected_bodies:
            failures.append(f"{name} does not cover every launch body")

    english_planet_labels = {
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
    }
    if english_planet_labels.intersection(BODY_LABELS.values()):
        failures.append("Radar body labels mix English planet names into Vietnamese copy")

    if set(ASPECT_CHANNELS) != set(ASPECT_LABELS):
        failures.append("Radar aspect scoring and labels have different coverage")
    if set(SCENE_COPY) != RADAR_THEME_KEYS:
        failures.append("Radar scene copy does not cover the complete theme catalog")
    if set(CONTEXT_CHECKS) != {"crush", "friend", "partner", "someone"}:
        failures.append("Radar context copy is incomplete")

    if set(PLANETS) - set(PLANET_PERSPECTIVES):
        failures.append("Some Daily Note planets have no interpretive perspective")
    if set(PLANETS) - set(CURRENT_FORCES):
        failures.append("Some Daily Note planets have no transit/current-force copy")
    if len(SIGNS) != 12 or len(HOUSES) != 12 or len(ELEMENTS) != 4:
        failures.append("Daily Note zodiac/house/element launch coverage regressed")
    if len(MODALITIES) != 3 or len(HOUSE_MODES) != 3:
        failures.append("Daily Note modality or house-mode coverage regressed")

    explicit_background_lenses = set(BackgroundLens) - {BackgroundLens.AUTO}
    for name, context_mapping in {
        "LENS_HOOKS": LENS_HOOKS,
        "LENS_MANIFESTATIONS": LENS_MANIFESTATIONS,
        "LENS_ACTIONS": LENS_ACTIONS,
    }.items():
        if set(context_mapping) != explicit_background_lenses:
            failures.append(f"{name} does not cover every explicit Daily Note context")

    forbidden_daily_fragments = {
        "rời màn hình vài phút",
        "trực giác có điều muốn nói",
        "góc rộng: chỉ là sắc độ nền",
        *BANNED_CORE_FRAGMENTS,
    }
    daily_atoms = " ".join(
        atom
        for meaning in SIGNS.values()
        for atom in (
            meaning.style,
            meaning.stress,
            meaning.manifestation,
            *meaning.practices,
            *meaning.hooks,
        )
    )
    if any(fragment in daily_atoms.casefold() for fragment in forbidden_daily_fragments):
        failures.append("Daily Note catalog contains a retired generic or incoherent fragment")
    if any(
        len(set(meaning.practices)) != len(meaning.practices)
        or len(set(meaning.hooks)) != len(meaning.hooks)
        for meaning in SIGNS.values()
    ):
        failures.append("Daily Note sign catalog repeats a hook or action inside one sign")

    source_ids = {source.source_id for source in BOOK_SOURCES}
    if len(source_ids) != len(BOOK_SOURCES):
        failures.append("Relationship source IDs are not unique")
    concept_ids = {concept.concept_id for concept in EDITORIAL_CONCEPTS}
    if len(concept_ids) != len(EDITORIAL_CONCEPTS):
        failures.append("Relationship concept IDs are not unique")
    registered = {concept_id for source in BOOK_SOURCES for concept_id in source.concept_ids}
    if concept_ids != registered:
        failures.append("Relationship sources and executable concepts are out of sync")
    covered_dimensions = {
        dimension for concept in EDITORIAL_CONCEPTS for dimension in concept.dimensions
    }
    if covered_dimensions != set(RelationshipDimension):
        failures.append("Relationship concepts do not cover every product dimension")
    return failures


def load_baseline(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("metrics"), dict):
        raise ValueError(f"Invalid content-matrix baseline: {path}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit versioned Lá Lành content matrices")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--json", action="store_true", help="Print machine-readable evidence")
    args = parser.parse_args()

    metrics = current_metrics()
    failures = validate_matrix()
    baseline = load_baseline(args.baseline)
    baseline_metrics = baseline["metrics"]
    for name, minimum in baseline_metrics.items():
        current = metrics.get(name)
        if not isinstance(minimum, int) or current is None:
            failures.append(f"Unknown or invalid baseline metric: {name}")
        elif current < minimum:
            failures.append(f"{name} regressed from {minimum} to {current}")

    evidence = {
        "status": "failed" if failures else "passed",
        "knowledge_versions": {
            "daily": INTERPRETATION_KNOWLEDGE_VERSION,
            "relationship": RELATIONSHIP_KNOWLEDGE_VERSION,
        },
        "metrics": metrics,
        "failures": failures,
    }
    if args.json:
        print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    elif failures:
        print("Content matrix audit failed:")
        for failure in failures:
            print(f"- {failure}")
    else:
        print(
            "Content matrix audit passed: "
            f"{metrics['daily_semantic_cycle_days']} daily variants, "
            f"{metrics['relationship_concepts']} relationship concepts, "
            f"{metrics['radar_themes']} Radar themes."
        )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
