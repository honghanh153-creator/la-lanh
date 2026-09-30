from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, cast

from app.domains.content.models import canonical_payload_hash
from app.domains.readings import knowledge


def _serialize_current_catalog() -> dict[str, Any]:
    return {
        "planets": {key: asdict(value) for key, value in sorted(knowledge.PLANETS.items())},
        "signs": {key: asdict(value) for key, value in sorted(knowledge.SIGNS.items())},
        "houses": {str(key): asdict(value) for key, value in sorted(knowledge.HOUSES.items())},
        "aspects": {key: asdict(value) for key, value in sorted(knowledge.ASPECTS.items())},
    }


_BUNDLED_DAILY_CATALOG = _serialize_current_catalog()


def bundled_daily_catalog() -> dict[str, Any]:
    """Return a JSON-safe copy of the code-owned known-good Daily matrix."""

    return cast(
        dict[str, Any],
        json.loads(json.dumps(_BUNDLED_DAILY_CATALOG, ensure_ascii=False)),
    )


def activate_daily_catalog(payload: dict[str, Any], *, generation: int) -> bool:
    """Atomically replace the process-local Daily matrix with a validated release.

    Publication remains fail-closed: callers validate the full payload first and
    this converter builds every replacement dictionary before swapping globals.
    Existing persisted readings are unaffected because they store rendered copy.
    """

    catalog = compile_daily_catalog(payload, generation=generation)
    return knowledge.install_runtime_catalog(catalog)


def compile_daily_catalog(
    payload: dict[str, Any], *, generation: int
) -> knowledge.RuntimeKnowledgeCatalog:
    planets = {key: knowledge.PlanetMeaning(**value) for key, value in payload["planets"].items()}
    signs = {
        key: knowledge.SignMeaning(
            style=value["style"],
            stress=value["stress"],
            manifestation=value["manifestation"],
            practices=tuple(value["practices"]),
            hooks=tuple(value["hooks"]),
        )
        for key, value in payload["signs"].items()
    }
    houses = {int(key): knowledge.HouseMeaning(**value) for key, value in payload["houses"].items()}
    aspects = {key: knowledge.AspectMeaning(**value) for key, value in payload["aspects"].items()}

    return knowledge.RuntimeKnowledgeCatalog(
        planets=planets,
        signs=signs,
        houses=houses,
        aspects=aspects,
        version=canonical_payload_hash(payload)[:12],
        generation=generation,
    )


def restore_bundled_daily_catalog() -> None:
    knowledge.restore_bundled_runtime_catalog()


def catalog_summary(payload: dict[str, Any]) -> dict[str, int]:
    return {
        group: len(entries) if isinstance(entries, dict) else 0
        for group, entries in payload.items()
    }
