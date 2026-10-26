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
import ast
import dataclasses
import inspect
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
from app.domains.readings import companion, daily_psychology, gates, renderers, voice
from app.domains.readings.application import DETERMINISTIC_CONTENT_VERSION
from app.domains.readings.renderers import DETERMINISTIC_RENDERER_VERSION
from app.domains.tarot import engine as tarot_engine
from app.domains.tarot import examples as tarot_examples
from app.domains.tarot import knowledge as tarot_knowledge
from app.domains.tarot import meaning_brief as tarot_meaning_brief
from app.domains.tarot import question_frame as tarot_question_frame
from app.domains.tarot import roles as tarot_roles
from app.domains.tarot import stance as tarot_stance
from app.domains.tarot import variants as tarot_variants
from app.domains.tarot import voice as tarot_voice

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


def source_literals(source: str) -> list[str]:
    """Copy written inside function bodies: every non-ASCII string literal (f-strings keep their
    text with ``{}`` for each placeholder), docstrings excluded, each literal once (audit O04).

    Module tables are pinned by ``module_tables``; prose built inside functions was not, so a
    sentence could change without the approval noticing. Non-ASCII is the copy marker: keys,
    codes and log messages are ASCII.
    """

    tree = ast.parse(source)
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    seen: set[int] = set()
    found: list[str] = []
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            continue
        for node in ast.walk(function):
            if id(node) in seen or id(node) in docstrings:
                continue
            seen.add(id(node))
            if isinstance(node, ast.JoinedStr):
                seen.update(id(part) for part in node.values)
                text = "".join(
                    str(part.value) if isinstance(part, ast.Constant) else "{}"
                    for part in node.values
                )
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
            else:
                continue
            if not text.isascii():
                found.append(text)
    return found


def function_literals(module: ModuleType) -> dict[str, str]:
    """One order-independent hash of a module's in-function copy."""

    literals = sorted(source_literals(inspect.getsource(module)))
    text = json.dumps(literals, ensure_ascii=False, separators=(",", ":"))
    return {f"{module.__name__}#function_literals": sha256(text.encode()).hexdigest()}


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
                **function_literals(daily_psychology),
                **function_literals(companion),
                **function_literals(voice),
                **function_literals(renderers),
            },
        },
        "tarot": {
            "renderer_version": tarot_engine.TAROT_RENDERER_VERSION,
            "knowledge_version": tarot_knowledge.KNOWLEDGE_VERSION,
            "deck_version": tarot_knowledge.DECK_VERSION,
            # Framed readings (US-20 B2-1..B2-4b), owner approval 2026-10-18.
            "framed_renderer_version": tarot_engine.FRAMED_RENDERER_VERSION,
            "framed_knowledge_version": tarot_engine.FRAMED_KNOWLEDGE_VERSION,
            "gate_version": tarot_engine.TAROT_GATE_VERSION,
            "question_rules_version": tarot_question_frame.QUESTION_RULES_VERSION,
            "role_copy_version": tarot_roles.ROLE_COPY_VERSION,
            "stance_version": tarot_stance.STANCE_VERSION,
            "variants_version": tarot_variants.TAROT_VARIANTS_VERSION,
            "variant_catalog_version": tarot_variants.TAROT_VARIANT_CATALOG_VERSION,
            "tables": {
                **module_tables(tarot_knowledge),
                **module_tables(tarot_engine),
                **module_tables(tarot_question_frame),
                **module_tables(tarot_roles),
                **module_tables(tarot_stance),
                **module_tables(tarot_variants),
                # Older copy the framed and legacy renderers reuse (goal reflections/actions,
                # links, brief limits, Roast/gentle frames and tails, example scenes). Pinned
                # 2026-10-18; byte-identical to production release 836222282dfc.
                **module_tables(tarot_meaning_brief),
                **module_tables(tarot_voice),
                **module_tables(tarot_examples),
                "app.domains.tarot.knowledge.all_cards()": sha256(cards.encode()).hexdigest(),
                # In-function copy (audit O04), pinned 2026-10-22 at c3fab33 = production.
                **{
                    key: value
                    for module in (
                        tarot_knowledge,
                        tarot_engine,
                        tarot_question_frame,
                        tarot_roles,
                        tarot_stance,
                        tarot_variants,
                        tarot_meaning_brief,
                        tarot_voice,
                        tarot_examples,
                    )
                    for key, value in function_literals(module).items()
                },
            },
        },
        "radar": {
            "renderer_version": radar_reading.RENDERER_VERSION,
            "gate_version": radar_reading.GATE_VERSION,
            "tables": {**module_tables(radar_reading), **function_literals(radar_reading)},
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
