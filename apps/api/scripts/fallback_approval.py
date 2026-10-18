"""Independent approval of the fallback store (variety measurement spec §4b, created in G0).

The fallback store is the live deterministic renderer: Daily psychology and Lá's lines (both
voices), Tarot knowledge and Hợp gu copy. ``docs/operations/fallback-approval.json`` pins the
content hash of every source table and the renderer and gate versions; CI fails when the
current code differs, so the store served on a ``variety_exception`` is always the approved one.

    uv run python -m scripts.fallback_approval          # refresh hashes (keeps the evidence)
    uv run python -m scripts.fallback_approval --check  # CI
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from enum import Enum
from hashlib import sha256
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic import BaseModel

from app.domains.radar import reading as radar_reading
from app.domains.readings import companion, daily_psychology, gates, voice
from app.domains.readings.application import DETERMINISTIC_CONTENT_VERSION
from app.domains.readings.renderers import DETERMINISTIC_RENDERER_VERSION
from app.domains.tarot import engine as tarot_engine
from app.domains.tarot import knowledge as tarot_knowledge

ROOT = Path(__file__).resolve().parents[3]
APPROVAL = ROOT / "docs" / "operations" / "fallback-approval.json"
_TABLE_NAME = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
_SKIP = object()


def canonical(value: Any) -> Any:
    """JSON-ready, order-independent form of a content table; non-data objects are skipped."""

    if isinstance(value, Enum):
        return canonical(value.value)
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, BaseModel):
        return canonical(value.model_dump(mode="json"))
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return canonical(dataclasses.asdict(value))
    if isinstance(value, dict):
        items = {str(canonical(k)): canonical(v) for k, v in value.items()}
        return {k: v for k, v in sorted(items.items()) if v is not _SKIP}
    if isinstance(value, list | tuple):
        return [item for item in (canonical(v) for v in value) if item is not _SKIP]
    if isinstance(value, set | frozenset):
        members = [canonical(v) for v in value]
        return sorted((i for i in members if i is not _SKIP), key=lambda i: json.dumps(i))
    return _SKIP


def module_tables(module: ModuleType) -> dict[str, str]:
    tables: dict[str, str] = {}
    for name, value in sorted(vars(module).items()):
        # Content tables hold text; bare numbers and flags are tuning, not copy.
        if (
            not _TABLE_NAME.match(name)
            or name.endswith("VERSION")
            or isinstance(value, bool | int | float)
        ):
            continue
        data = canonical(value)
        if data is _SKIP:
            continue
        text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        tables[f"{module.__name__}.{name}"] = sha256(text.encode()).hexdigest()
    return tables


def current() -> dict[str, Any]:
    cards = json.dumps(canonical(tarot_knowledge.all_cards()), ensure_ascii=False, sort_keys=True)
    return {
        "daily": {
            "renderer_version": DETERMINISTIC_RENDERER_VERSION,
            "content_version": DETERMINISTIC_CONTENT_VERSION,
            "psychology_version": daily_psychology.DAILY_PSYCHOLOGY_MATRIX_VERSION,
            "companion_version": companion.COMPANION_VOICE_VERSION,
            "tables": {
                **module_tables(daily_psychology),
                **module_tables(companion),
                **module_tables(voice),
            },
        },
        "tarot": {
            "renderer_version": tarot_engine.TAROT_RENDERER_VERSION,
            "knowledge_version": tarot_knowledge.KNOWLEDGE_VERSION,
            "deck_version": tarot_knowledge.DECK_VERSION,
            "tables": {
                **module_tables(tarot_knowledge),
                **module_tables(tarot_engine),
                "app.domains.tarot.knowledge.all_cards()": sha256(cards.encode()).hexdigest(),
            },
        },
        "radar": {
            "renderer_version": radar_reading.RENDERER_VERSION,
            "gate_version": radar_reading.GATE_VERSION,
            "tables": module_tables(radar_reading),
        },
        "gate_versions": {
            "anti_influence": gates.ANTI_INFLUENCE_GATE_VERSION,
            "editorial": gates.EDITORIAL_GATE_VERSION,
            "evidence": gates.EVIDENCE_GATE_VERSION,
            "meaning": gates.MEANING_GATE_VERSION,
            "privacy": gates.PRIVACY_GATE_VERSION,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    approval = json.loads(APPROVAL.read_text())
    computed = current()
    if args.check:
        if approval.get("approved") != computed:
            approved = approval.get("approved", {})
            changed = sorted(
                f"{surface}.{key}"
                for surface, block in computed.items()
                for key in (block if isinstance(block, dict) else {})
                if approved.get(surface, {}).get(key) != block[key]
            )
            sys.exit(
                "fallback store differs from docs/operations/fallback-approval.json: "
                f"{changed[:8]}. A content change needs owner approval, then "
                "`uv run python -m scripts.fallback_approval` and the evidence updated."
            )
        print("fallback approval current")
        return
    approval["approved"] = computed
    APPROVAL.write_text(json.dumps(approval, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"fallback approval written to {APPROVAL}")


if __name__ == "__main__":
    main()
