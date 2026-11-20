"""Keeping the day's action: 300 seeded click paths over the API (#687, 7-week plan, week 1).

100 paths for each kind of profile: birth date only, approximate birth time, exact birth time.
Every path is a random but repeatable sequence of the things a person can press around
"Giữ để thử hôm nay": open the note, keep an action, keep another one (with the confirm step),
stop keeping, record how it went, pick a mood, reopen, change the birth time, delete the profile.

A small model predicts what the API must answer at each step (US-03 §22). A path passes only
when every answer matches, so any 4xx/5xx outside the contract fails it, and the kept action
read back after every step is the single one the model expects (AC33, one open action per guest).

What the API offers today (measured here, not assumed): only an exact-time profile is offered an
action it can keep. Date-only and approximate profiles get the note and the lighter action as
text, with nothing to keep. ``KEEPABLE`` pins that; widening it is a product change that must
edit this file on purpose.

All birth data is synthetic and drawn from a fixed seed.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.astro.models import TimePrecision
from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
from app.domains.readings import application
from app.domains.readings.lighter_action import ISSUE_LIGHT_PREFIX, LIGHTER_ACTION_PREFIX
from app.domains.readings.models import (
    ClaimTemplateId,
    PlanMode,
    canonical_experiment_action_key,
)
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
CONSENT = "action-experiment-v1"
KINDS = ("date_only", "approximate", "exact")
PATHS_PER_KIND = 100
# Profile kinds the API lets keep an action. See the module docstring before changing it;
# the other two kinds are the open gap in issue #716.
KEEPABLE = frozenset({"exact"})
PRECISION = {
    "date_only": TimePrecision.UNKNOWN.value,
    "approximate": TimePrecision.APPROXIMATE.value,
    "exact": TimePrecision.EXACT.value,
}
OUTCOMES = ("not_tried", "helpful", "no_difference", "not_for_now")
MOODS = ("Rực", "Chill", "Đuối", "Căng", "Lạc trôi")
LENSES = ("relationships", "communication", "work", "energy", "self_care")
WINDOWS = ("dawn", "morning", "noon", "afternoon", "evening", "night")
PLACES = ("vn-hanoi", "vn-ho-chi-minh")
FIRST_BIRTH_DATE = date(1985, 1, 1)
BIRTH_DATE_SPAN_DAYS = 23 * 365


def _approve_lighter_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Serve the checked-in lighter sentences, so the low-mood action (#634) is on the paths."""

    # The general list and the light actions written per Daily issue (#699).
    pool = [
        entry
        for key, entry in load_registry().items()
        if key.startswith((LIGHTER_ACTION_PREFIX, ISSUE_LIGHT_PREFIX))
    ]
    entries = [
        {
            "id": entry.id,
            "category": "reading",
            "text": entry.text,
            "status": "approved",
            "approver": "codex",
            "date": "2026-11-17",
            "digest": copy_digest(entry.text),
        }
        for entry in pool
    ]
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)


@dataclass(frozen=True)
class Target:
    """One thing the screen offers to keep."""

    revision_id: str
    lens: str
    action_key: str
    lighter: bool

    def body(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "background_lens": self.lens,
            "action_key": self.action_key,
            "consent_version": CONSENT,
        }


@dataclass
class Path:
    """One person's session and what the model says the server holds for them."""

    client: TestClient
    rng: random.Random
    kind: str
    headers: dict[str, str] = field(default_factory=dict)
    note_id: str = ""
    auto_revision_id: str = ""
    targets: list[Target] = field(default_factory=list)
    refused: list[Target] = field(default_factory=list)
    held: dict[str, Any] | None = None
    held_target: Target | None = None
    closed_revisions: set[str] = field(default_factory=set)
    stale: list[dict[str, Any]] = field(default_factory=list)
    kept: int = 0
    steps: int = 0

    # --- the three kinds of profile -------------------------------------------------------

    def start(self, index: int) -> None:
        self.client.cookies.clear()
        guest = self.client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": f"keep-paths-{self.kind}-{index:04d}-1234567890",
            },
        )
        assert guest.status_code in (200, 201), guest.text
        self.headers = {"Origin": ORIGIN, "X-CSRF-Token": guest.json()["csrf_token"]}
        born = FIRST_BIRTH_DATE + timedelta(days=self.rng.randrange(BIRTH_DATE_SPAN_DAYS))
        profile = self.client.post(
            "/v1/birth-profile", json={"birth_date": born.isoformat()}, headers=self.headers
        )
        assert profile.status_code == 200, profile.text
        # The first note is always opened with the date alone, as in the app.
        assert self.client.get("/v1/daily-note").status_code == 200
        if self.kind == "approximate":
            self._supplement(self._approximate_time())
        elif self.kind == "exact":
            self._supplement(self._exact_time())
        self._open_note()

    def _approximate_time(self) -> dict[str, Any]:
        return {
            "birth_time_mode": "approx_window",
            "birth_time_local": None,
            "approx_window": self.rng.choice(WINDOWS),
            "place_id": self.rng.choice(PLACES),
            "consent_version": "birth-profile-deep-v1",
        }

    def _exact_time(self) -> dict[str, Any]:
        return {
            "birth_time_mode": "exact",
            "birth_time_local": f"{self.rng.randrange(24):02d}:{self.rng.randrange(60):02d}",
            "place_id": self.rng.choice(PLACES),
            "consent_version": "birth-profile-deep-v1",
        }

    def _supplement(self, body: dict[str, Any]) -> None:
        response = self.client.post("/v1/birth-profile/supplement", json=body, headers=self.headers)
        assert response.status_code == 200, response.text

    def _open_note(self) -> None:
        """Open today's note, take the deeper reading when one is waiting, list what is offered."""

        note = self.client.get("/v1/daily-note")
        assert note.status_code == 200, note.text
        assert note.headers["cache-control"] == "no-store, max-age=0"
        payload = note.json()
        projection = payload["reading_projection"]
        active = projection["active"]
        update = projection.get("available_update")
        if self.kind != "date_only" and update is not None:
            activated = self.client.put(
                f"/v1/reading-projections/{projection['scope_key']}/activate",
                json={"expected_revision_id": update["revision_id"]},
                headers=self.headers,
            )
            assert activated.status_code == 200, activated.text
            active = activated.json()["active"]
        self.note_id = payload["id"]
        self.auto_revision_id = active["revision_id"]
        assert active["precision"] == PRECISION[self.kind]
        self.targets = []
        self.refused = []
        self._list_offers(active, "auto")

    def _list_offers(self, active: dict[str, Any], lens: str) -> None:
        revision_id = active["revision_id"]
        experiment = active["experiment"]
        lighter = active["lighter_action"]
        # The lighter action (#634) is offered as text to every kind of profile.
        assert lighter is not None
        if self.kind in KEEPABLE:
            assert experiment is not None, "an exact-time profile must be offered an action"
            assert lighter["experiment"] is not None
            self.targets.append(Target(revision_id, lens, experiment["action_key"], False))
            self.targets.append(
                Target(revision_id, lens, lighter["experiment"]["action_key"], True)
            )
            return
        assert experiment is None, f"a {self.kind} profile was offered an action to keep"
        assert lighter["experiment"] is None
        # What a hand-built request would name; the server must refuse both.
        revision = UUID(revision_id)
        card_key = canonical_experiment_action_key(revision, active["sections"]["micro_action"])
        lighter_key = canonical_experiment_action_key(revision, lighter["action"])
        self.refused.append(Target(revision_id, lens, card_key, False))
        self.refused.append(Target(revision_id, lens, lighter_key, True))

    # --- what a person can press ------------------------------------------------------------

    def keep(self, target: Target | None = None) -> None:
        if self.kind not in KEEPABLE:
            refused = self.rng.choice(self.refused)
            assert self._put(refused.body()).status_code == 404
            return
        target = target or self.rng.choice(self.targets)
        closed = target.revision_id in self.closed_revisions
        if self.held is not None and self.held_target == target:
            again = self._put(target.body())
            assert again.status_code == 200, again.text
            assert again.json() == self.held
            return
        if self.held is None:
            response = self._put(target.body())
            if closed:  # that card's action was already kept and closed with an outcome
                assert response.status_code == 409, response.text
                return
            assert response.status_code == 200, response.text
            assert response.json()["version"] == 1
            self._now_holding(response.json(), target)
            return
        # Another action is kept: the server asks for a confirmation first.
        assert self._put(target.body()).status_code == 409
        self.check_current()  # the screen reloads before asking again
        previous = self.held
        confirmed = self._put(
            {
                **target.body(),
                "expected_experiment_id": previous["id"],
                "expected_version": previous["version"],
            }
        )
        if closed:
            assert confirmed.status_code == 409, confirmed.text
            return
        assert confirmed.status_code == 200, confirmed.text
        assert confirmed.json()["id"] != previous["id"]
        assert confirmed.json()["version"] == previous["version"] + 1
        self.stale.append(previous)
        self._now_holding(confirmed.json(), target)

    def _put(self, body: dict[str, Any]) -> Any:
        return self.client.put(
            f"/v1/daily-note/{self.note_id}/experiment", json=body, headers=self.headers
        )

    def _now_holding(self, payload: dict[str, Any], target: Target) -> None:
        assert payload["state"] == "chosen"
        assert payload["outcome"] is None
        assert payload["action_key"] == target.action_key
        assert payload["revision_id"] == target.revision_id
        assert payload["background_lens"] == target.lens
        assert payload["daily_note_id"] == self.note_id
        self.held, self.held_target = payload, target
        self.kept += 1

    def undo(self) -> None:
        if self.held is None:
            self._stale_mutation()
            return
        undone = self.client.request(
            "DELETE",
            "/v1/daily-note/experiment",
            json={"experiment_id": self.held["id"], "expected_version": self.held["version"]},
            headers=self.headers,
        )
        assert undone.status_code == 204, undone.text
        self.stale.append(self.held)
        self.held = self.held_target = None

    def outcome(self) -> None:
        if self.held is None or self.held_target is None:
            self._stale_mutation()
            return
        chosen = self.rng.choice(OUTCOMES)
        reflected = self.client.post(
            "/v1/daily-note/experiment/outcome",
            json={
                "experiment_id": self.held["id"],
                "expected_version": self.held["version"],
                "outcome": chosen,
            },
            headers=self.headers,
        )
        assert reflected.status_code == 200, reflected.text
        assert reflected.json()["state"] == "reflected"
        assert reflected.json()["outcome"] == chosen
        self.closed_revisions.add(self.held_target.revision_id)
        self.stale.append(self.held)
        self.held = self.held_target = None

    def _stale_mutation(self) -> None:
        """A late tap from an old screen: it must be refused and change nothing."""

        old = self.rng.choice(self.stale) if self.stale else {"id": str(uuid4()), "version": 1}
        body = {"experiment_id": old["id"], "expected_version": old["version"]}
        if self.rng.random() < 0.5:
            late = self.client.request(
                "DELETE", "/v1/daily-note/experiment", json=body, headers=self.headers
            )
        else:
            late = self.client.post(
                "/v1/daily-note/experiment/outcome",
                json={**body, "outcome": self.rng.choice(OUTCOMES)},
                headers=self.headers,
            )
        assert late.status_code == 409, late.text

    def late_tap(self) -> None:
        self._stale_mutation()

    def mood(self) -> None:
        picked = self.rng.choice(MOODS)
        response = self.client.put(
            f"/v1/daily-note/{self.note_id}/mood", json={"mood": picked}, headers=self.headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["mood"] == picked
        if picked == "Đuối" and self.kind in KEEPABLE:
            # The low-mood day: the lighter action of today's card is the one kept.
            lighter = next(
                t for t in self.targets if t.lighter and t.revision_id == self.auto_revision_id
            )
            self.keep(lighter)

    def other_lens(self) -> None:
        lens = self.rng.choice(LENSES)
        response = self.client.post(
            "/v1/daily-note/context", json={"background_lens": lens}, headers=self.headers
        )
        if response.status_code == 422:  # contract: the gates refused this lens today
            assert response.json()["code"] == "READING_CONTENT_REJECTED"
            return
        assert response.status_code == 200, response.text
        active = response.json()["active"]
        assert active["precision"] == PRECISION[self.kind]
        if any(t.lens == lens for t in (*self.targets, *self.refused)):
            return
        self._list_offers(active, lens)

    def reopen(self) -> None:
        """Home and the note page read the same server state after a reload."""

        note = self.client.get("/v1/daily-note")
        assert note.status_code == 200, note.text
        assert note.json()["id"] == self.note_id
        active = note.json()["reading_projection"]["active"]
        assert active["revision_id"] == self.auto_revision_id
        offered = active["experiment"]
        if self.kind in KEEPABLE:
            assert offered["action_key"] == self.targets[0].action_key
        else:
            assert offered is None

    def check_current(self) -> None:
        current = self.client.get("/v1/daily-note/experiment")
        assert current.status_code == 200, current.text
        assert current.headers["cache-control"] == "no-store, max-age=0"
        assert current.json() == self.held

    # --- how a path ends ----------------------------------------------------------------------

    def change_birth_time(self) -> None:
        """A new time or place makes the kept action stale: it is deleted, never carried over."""

        if self.kind == "date_only":
            self.reopen()
            return
        dependent = self.held
        body = self._exact_time() if self.kind == "exact" else self._approximate_time()
        self._supplement(body)
        if dependent is not None:
            self.stale.append(dependent)
        self.held = self.held_target = None
        self.check_current()
        if dependent is not None:
            late = self.client.post(
                "/v1/daily-note/experiment/outcome",
                json={
                    "experiment_id": dependent["id"],
                    "expected_version": dependent["version"],
                    "outcome": "helpful",
                },
                headers=self.headers,
            )
            assert late.status_code == 409, late.text
        self.closed_revisions.clear()
        self._open_note()
        self.keep()
        self.check_current()

    def delete_profile(self) -> None:
        deleted = self.client.request("DELETE", "/v1/guest-session", headers=self.headers)
        assert deleted.status_code == 204, deleted.text
        assert self.client.get("/v1/daily-note/experiment").status_code == 401
        assert self.client.get("/v1/daily-note").status_code == 401

    def run(self, index: int) -> None:
        self.start(index)
        self.check_current()
        self.keep()  # every path presses (or, where nothing is offered, forges) a keep first
        self.check_current()
        presses: tuple[Callable[[], None], ...] = (
            self.keep,
            self.keep,
            self.undo,
            self.outcome,
            self.late_tap,
            self.mood,
            self.other_lens,
            self.reopen,
        )
        for _ in range(self.rng.randint(4, 8)):
            self.rng.choice(presses)()
            self.steps += 1
            self.check_current()
        self.rng.choice((self.reopen, self.change_birth_time, self.delete_profile))()


def _run_paths(kind: str, count: int, first: int = 0) -> tuple[int, int, list[str]]:
    """Run ``count`` paths. Returns (paths that kept an action, presses, failures).

    Each path gets its own app and empty database: one person is one client, and the admission
    limit (429) is about many requests from one address, which is not what these paths measure.
    """

    kept = steps = 0
    failures: list[str] = []
    for index in range(first, first + count):
        app = create_app(
            Settings(
                environment="test",
                database_url="sqlite+aiosqlite:///:memory:",
                cors_origins=[ORIGIN],
                guest_cookie_name="la_lanh_guest",
                guest_cookie_secure=False,
            )
        )
        seed = 687_000 + KINDS.index(kind) * 1000 + index
        with TestClient(app, base_url=ORIGIN) as client:
            path = Path(client=client, rng=random.Random(seed), kind=kind)  # noqa: S311
            try:
                path.run(index)
            except AssertionError as error:
                detail = str(error).splitlines()[0][:200] if str(error) else "assertion"
                failures.append(f"{kind} path {index} (seed {seed}), step {path.steps}: {detail}")
        kept += path.kept > 0
        steps += path.steps
    return kept, steps, failures


@pytest.mark.parametrize("kind", KINDS)
def test_100_click_paths_answer_only_what_the_contract_allows(
    kind: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _approve_lighter_pool(monkeypatch)
    kept, steps, failures = _run_paths(kind, PATHS_PER_KIND)
    with capsys.disabled():
        print(  # the PR quotes this line as evidence
            f"\n#687 {kind}: {PATHS_PER_KIND - len(failures)}/{PATHS_PER_KIND} paths without an "
            f"error, {steps} presses, {kept} paths kept an action"
        )
    assert failures == []
    assert kept == (PATHS_PER_KIND if kind in KEEPABLE else 0)


def _always_exact(*_args: object, **_kwargs: object) -> tuple[PlanMode, TimePrecision]:
    return PlanMode.FULL_SYNTHESIS, TimePrecision.EXACT


def _never_exact(
    claims: tuple[Any, ...], plan_precision: TimePrecision | None = None
) -> tuple[PlanMode, TimePrecision]:
    if any(claim.template_id is ClaimTemplateId.DATE_ONLY_VIBE for claim in claims):
        return PlanMode.VIBE_FALLBACK, TimePrecision.UNKNOWN
    return PlanMode.FULL_SYNTHESIS, TimePrecision.APPROXIMATE


@pytest.mark.parametrize(
    ("kind", "broken"),
    [("date_only", _always_exact), ("approximate", _always_exact), ("exact", _never_exact)],
)
def test_paths_go_red_when_a_profile_kind_loses_its_own_handling(
    kind: str,
    broken: Callable[..., tuple[PlanMode, TimePrecision]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC4: the paths really check each kind; collapsing the precision branch fails them all."""

    _approve_lighter_pool(monkeypatch)
    monkeypatch.setattr(application, "_public_mode_and_precision", broken)
    _, _, failures = _run_paths(kind, 5)
    assert len(failures) == 5
