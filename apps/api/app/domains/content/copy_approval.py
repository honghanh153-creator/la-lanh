"""Pending/approved flag for new user-facing copy (owner decision 06.11.2026).

New sentences enter ``copy_registry.json`` as ``pending``. Runtime serves an entry only when it
is ``approved`` with a matching digest; otherwise the caller's current approved sentence is
served. Codex may approve a daily batch (``scripts/codex-copy-review.mjs``); privacy, consent,
crisis and safety copy stays owner-only. ``scripts.fallback_approval`` pins approved entries
only, so adding a pending entry does not trip the owner gate.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

REGISTRY_PATH = Path(__file__).with_name("copy_registry.json")
REGISTRY_VERSION = "copy-registry/v1"
STATUSES = frozenset({"pending", "approved"})
APPROVERS = frozenset({"codex", "owner"})
OWNER_ONLY_CATEGORIES = frozenset({"privacy", "consent", "crisis", "safety"})


def copy_digest(text: str) -> str:
    return sha256(unicodedata.normalize("NFC", text).encode()).hexdigest()


@dataclass(frozen=True)
class CopyEntry:
    id: str
    category: str
    text: str
    status: str
    approver: str | None = None
    date: str | None = None
    digest: str | None = None

    def problems(self) -> list[str]:
        found: list[str] = []
        if self.status not in STATUSES:
            found.append(f"{self.id}: status must be pending or approved")
        if not self.text.strip():
            found.append(f"{self.id}: empty text")
        if self.status == "approved":
            if self.approver not in APPROVERS:
                found.append(f"{self.id}: approved entry needs approver codex or owner")
            if not self.date:
                found.append(f"{self.id}: approved entry needs a date")
            if self.digest != copy_digest(self.text):
                found.append(f"{self.id}: digest does not match the text")
            if self.category in OWNER_ONLY_CATEGORIES and self.approver != "owner":
                found.append(f"{self.id}: {self.category} copy can only be approved by the owner")
        return found

    @property
    def servable(self) -> bool:
        return self.status == "approved" and not self.problems()


_REQUIRED_TEXT = ("id", "category", "text", "status")
_OPTIONAL_TEXT = ("approver", "date", "digest")


def _entry(raw: object) -> CopyEntry:
    if not isinstance(raw, dict) or set(raw) - {*_REQUIRED_TEXT, *_OPTIONAL_TEXT}:
        raise ValueError("copy entry must be an object with known fields")
    for key in _REQUIRED_TEXT:
        if not isinstance(raw.get(key), str):
            raise ValueError(f"copy entry field {key} must be a string")
    for key in _OPTIONAL_TEXT:
        if raw.get(key) is not None and not isinstance(raw[key], str):
            raise ValueError(f"copy entry field {key} must be a string or null")
    return CopyEntry(**raw)


def parse_registry(data: object) -> dict[str, CopyEntry]:
    if not isinstance(data, dict) or data.get("version") != REGISTRY_VERSION:
        raise ValueError(f"copy registry must be an object with version {REGISTRY_VERSION}")
    raw_entries = data.get("entries", [])
    if not isinstance(raw_entries, list):
        raise ValueError("copy registry entries must be a list")
    entries: dict[str, CopyEntry] = {}
    for raw in raw_entries:
        entry = _entry(raw)
        if entry.id in entries:
            raise ValueError(f"duplicate copy entry: {entry.id}")
        entries[entry.id] = entry
    return entries


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, CopyEntry]:
    return parse_registry(json.loads(path.read_text(encoding="utf-8")))


def registry_problems(entries: dict[str, CopyEntry]) -> list[str]:
    found = [problem for entry in entries.values() for problem in entry.problems()]
    return [*found, *bundle_problems(entries)]


def approved_pin(entries: dict[str, CopyEntry]) -> str:
    """Hash of the approved entries only; pending entries never reach runtime."""

    approved = sorted(
        (e.id, e.category, e.text, e.approver or "", e.digest or "")
        for e in entries.values()
        if e.status == "approved"
    )
    return sha256(json.dumps(approved, ensure_ascii=False).encode()).hexdigest()


@lru_cache(maxsize=1)
def _runtime_registry() -> dict[str, CopyEntry]:
    try:
        return load_registry(REGISTRY_PATH)
    except (OSError, ValueError, TypeError):
        # Fail closed: an unreadable registry serves the current approved sentences.
        return {}


def approved_texts(prefix: str) -> tuple[str, ...]:
    """Approved sentences whose id starts with ``prefix``, in id order; never pending ones."""

    registry = _runtime_registry()
    return tuple(
        registry[key].text
        for key in sorted(registry)
        if key.startswith(prefix) and registry[key].servable
    )


def copy_text(entry_id: str, fallback: str) -> str:
    """The approved sentence for ``entry_id``, or ``fallback`` (current approved copy)."""

    entry = _runtime_registry().get(entry_id)
    return entry.text if entry is not None and entry.servable else fallback


# Daily bundles (owner decision 10.11.2026): headline, scene and action written together as
# ``daily.bundle.<situation>.<nn>.<part>`` and served only as a whole.
BUNDLE_PREFIX = "daily.bundle."
BUNDLE_PARTS = ("headline", "scene", "action")


def bundle_problems(entries: dict[str, CopyEntry]) -> list[str]:
    """Every bundle id must be ``daily.bundle.<situation>.<nn>.<part>`` with all three parts."""

    groups: dict[str, set[str]] = {}
    found: list[str] = []
    for key in entries:
        if not key.startswith(BUNDLE_PREFIX):
            continue
        parts = key[len(BUNDLE_PREFIX) :].split(".")
        if len(parts) != 3 or not all(parts) or parts[2] not in BUNDLE_PARTS:
            found.append(f"{key}: bundle id must be daily.bundle.<situation>.<nn>.<part>")
            continue
        groups.setdefault(f"{parts[0]}.{parts[1]}", set()).add(parts[2])
    for bundle, present in sorted(groups.items()):
        missing = [part for part in BUNDLE_PARTS if part not in present]
        if missing:
            found.append(f"daily.bundle.{bundle}: missing {', '.join(missing)}")
    return found


def approved_bundles(situation: str) -> tuple[tuple[str, str, str], ...]:
    """(headline, scene, action) bundles of ``situation`` whose three lines are all approved."""

    registry = _runtime_registry()
    prefix = f"{BUNDLE_PREFIX}{situation}."
    numbers = sorted(
        {key[len(prefix) :].split(".")[0] for key in registry if key.startswith(prefix)}
    )
    bundles: list[tuple[str, str, str]] = []
    for number in numbers:
        lines = [registry.get(f"{prefix}{number}.{part}") for part in BUNDLE_PARTS]
        if all(line is not None and line.servable for line in lines):
            bundles.append(tuple(line.text for line in lines))  # type: ignore[union-attr,misc]
    return tuple(bundles)
