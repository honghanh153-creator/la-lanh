"""Read-only runtime over a built grammar (spec §5). G0: not wired into any served reading.

Only a frame with a valid manifest is composed. A missing or corrupt manifest returns a status
the caller turns into ``variety_exception`` and the approved fallback store; nothing is ever
composed freely from the catalog.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.domains.grammar.build import BUILD_DIR, catalog_sha256, digest
from app.domains.grammar.composer import COMPOSER_VERSION, parse_code
from app.domains.grammar.gate import GATE_VERSION
from app.domains.grammar.models import SPEC_VERSION, Voice


class GrammarStatus(StrEnum):
    OK = "ok"
    MANIFEST_MISSING = "manifest_missing"
    MANIFEST_CORRUPT = "manifest_corrupt"


@dataclass(frozen=True)
class GrammarSelection:
    frame_id: str
    voice: Voice
    variant: int
    position: int
    bucket: str
    code: str  # full combination code: replay, voice switch and sharing use it
    text: str


@dataclass(frozen=True)
class GrammarRuntime:
    status: GrammarStatus
    manifest: dict[str, Any] | None = None
    allowlist: dict[str, dict[str, dict[str, str]]] | None = None
    schedules: dict[str, list[list[str]]] | None = None

    @property
    def length(self) -> int:
        return int(self.manifest["L"]) if self.manifest else 0

    def select(
        self, frame_id: str, *, variant: int, position: int, bucket: str
    ) -> GrammarSelection:
        """The direct sentence of ``frame_id`` at schedule ``variant`` and position ``p``."""

        if self.status is not GrammarStatus.OK or not self.schedules or not self.allowlist:
            raise LookupError(f"grammar unavailable: {self.status}")
        order = self.schedules[frame_id][variant]
        master = order[position % len(order)]
        expected = parse_code(master)
        codes = sorted(
            code
            for code in self.allowlist[frame_id][bucket]
            if all(parse_code(code)[slot] == value for slot, value in expected.items())
        )
        code = codes[position % len(codes)]
        return GrammarSelection(
            frame_id=frame_id,
            voice=Voice.DIRECT,
            variant=variant,
            position=position % len(order),
            bucket=bucket,
            code=code,
            text=self.allowlist[frame_id][bucket][code],
        )

    def roast(self, selection: GrammarSelection, roast_frame_id: str) -> GrammarSelection:
        """Voice switch: look the same code up in the Roast frame; never re-run the schedule."""

        if not self.allowlist:
            raise LookupError(f"grammar unavailable: {self.status}")
        return GrammarSelection(
            frame_id=roast_frame_id,
            voice=Voice.ROAST,
            variant=selection.variant,
            position=selection.position,
            bucket=selection.bucket,
            code=selection.code,
            text=self.allowlist[roast_frame_id][selection.bucket][selection.code],
        )


def schedule_position(seed: str, day_index: int, length: int, variants: int) -> tuple[int, int]:
    """(variant, p) from the per-person seed: ``p = (day_index + offset) mod L`` (spec §5)."""

    variant = int(seed[:8], 16) % variants
    offset = int(seed[8:16], 16) % length
    return variant, (day_index + offset) % length


def load_grammar(directory: Path) -> GrammarRuntime:
    build = directory / BUILD_DIR
    manifest_path = build / "manifest.json"
    if not manifest_path.exists():
        return GrammarRuntime(GrammarStatus.MANIFEST_MISSING)
    try:
        manifest = json.loads(manifest_path.read_text())
        texts = {name: (build / name).read_text() for name in manifest["files"]}
        valid = (
            manifest["spec_version"] == SPEC_VERSION
            and manifest["composer_version"] == COMPOSER_VERSION
            and manifest["gate_version"] == GATE_VERSION
            and manifest["catalog_sha256"] == catalog_sha256(directory)
            and all(digest(text) == manifest["files"][name] for name, text in texts.items())
        )
        if not valid:
            return GrammarRuntime(GrammarStatus.MANIFEST_CORRUPT)
        return GrammarRuntime(
            GrammarStatus.OK,
            manifest=manifest,
            allowlist=json.loads(texts["allowlist.json"]),
            schedules=json.loads(texts["schedules.json"]),
        )
    except (OSError, KeyError, TypeError, ValueError):
        return GrammarRuntime(GrammarStatus.MANIFEST_CORRUPT)
