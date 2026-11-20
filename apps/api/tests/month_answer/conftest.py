"""Month-answer tests: a pinned clock and a registry where the month sentences are approved."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import UTC, datetime

import pytest
import time_machine

from app.domains.content import copy_approval
from app.domains.content.copy_approval import CopyEntry, copy_digest, load_registry

PINNED = datetime(2026, 11, 20, 5, 0, tzinfo=UTC)  # noon in Vietnam, 20.11.2026


@pytest.fixture(autouse=True)
def _pinned_clock() -> Iterator[None]:
    with time_machine.travel(PINNED, tick=True):
        yield


def _approved(entry: CopyEntry) -> CopyEntry:
    approver = "owner" if entry.category in copy_approval.OWNER_ONLY_CATEGORIES else "codex"
    return replace(
        entry,
        status="approved",
        approver=approver,
        date="2026-11-20",
        digest=copy_digest(entry.text),
    )


@pytest.fixture
def approve_month(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Serve the pending month sentences as if approved (``owner=True`` adds consent and crisis)."""

    def apply(*, owner: bool = False) -> None:
        registry = dict(load_registry())
        for key, entry in registry.items():
            month = key.startswith("month.")
            owner_month = key in {"consent.month.typed_question", "crisis.self_harm.notice.month"}
            if month or (owner and owner_month):
                registry[key] = _approved(entry)
        monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)

    return apply


def registry_texts(prefix: str) -> dict[str, str]:
    raw = json.loads(copy_approval.REGISTRY_PATH.read_text(encoding="utf-8"))
    return {e["id"]: e["text"] for e in raw["entries"] if e["id"].startswith(prefix)}
