"""Keeping the day's action: 300 seeded click paths over the API (#687, 7-week plan, week 1).

100 paths for each kind of profile: birth date only, approximate birth time, exact birth time.
Every path is a random but repeatable sequence of the things a person can press around
"Giữ để thử hôm nay": open the note, keep an action, keep another one (with the confirm step),
stop keeping, record how it went, pick a mood, reopen, change the birth time, delete the profile.

A small model predicts what the API must answer at each step (US-03 §22). A path passes only
when every answer matches, so any 4xx/5xx outside the contract fails it, and the kept action
read back after every step is the single one the model expects (AC33, one open action per guest).

What the API offers (measured here, not assumed): with the `keep_action_all_profiles` setting on,
every kind of profile is offered the card's action and the lighter action to keep (#716). Off
(the default until the owner turns it on, R2 kind 4), only an exact-time profile is, and a
hand-built keep from the others is refused, so nothing new is stored for them. ``KEEPABLE``
pins both; changing it is a product change that must edit this file on purpose.
A date-only path may end by adding a birth time, which must delete the kept action too.

All birth data is synthetic and drawn from a fixed seed.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.domains.astro.models import TimePrecision
from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
from app.domains.experiments.postgres import EXPERIMENT_PURPOSE
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.tables import ConsentRow
from app.domains.readings import application
from app.domains.readings.lighter_action import LIGHTER_ACTION_PREFIX
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
# Profile kinds the API lets keep an action, by the `keep_action_all_profiles` setting. See the
# module docstring before changing it. A kind left out must get no offer and a 404 for a
# hand-built keep.
KEEPABLE = {True: frozenset(KINDS), False: frozenset({"exact"})}
PATHS_PER_KIND_SWITCHED_OFF = 30
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

    pool = [
        entry for key, entry in load_registry().items() if key.startswith(LIGHTER_ACTION_PREFIX)
    ]
    entries = [
        {
            "id": f"{LIGHTER_ACTION_PREFIX}{number:02d}",
            "category": "reading",
            "text": entry.text,
            "status": "approved",
            "approver": "codex",
            "date": "2026-11-17",
            "digest": copy_digest(entry.text),
        }
        for number, entry in enumerate(pool, start=1)
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
    birth_time: dict[str, Any] | None = None
    kept: int = 0
    steps: int = 0
    all_profiles: bool = True

    @property
    def keepable(self) -> frozenset[str]:
        return KEEPABLE[self.all_profiles]

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
        self.birth_time = body

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
        if self.kind in self.keepable:
            assert experiment is not None, f"a {self.kind} profile must be offered an action"
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
        if self.kind not in self.keepable:
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
        if picked == "Đuối" and self.kind in self.keepable:
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
        if self.kind in self.keepable:
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

        dependent = self.held
        draw = self._exact_time if self.kind == "exact" else self._approximate_time
        body = draw()
        while body == self.birth_time:  # the same time again changes nothing; draw a new one
            body = draw()
        self._supplement(body)
        if self.kind == "date_only":  # the person added a birth time for the first time
            self.kind = "approximate"
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


def _app(*, all_profiles: bool = True) -> Any:
    return create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=[ORIGIN],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
            keep_action_all_profiles=all_profiles,
        )
    )


def _run_paths(
    kind: str, count: int, first: int = 0, *, all_profiles: bool = True
) -> tuple[int, int, list[str]]:
    """Run ``count`` paths. Returns (paths that kept an action, presses, failures).

    Each path gets its own app and empty database: one person is one client, and the admission
    limit (429) is about many requests from one address, which is not what these paths measure.
    """

    kept = steps = 0
    failures: list[str] = []
    for index in range(first, first + count):
        app = _app(all_profiles=all_profiles)
        seed = 687_000 + KINDS.index(kind) * 1000 + index
        with TestClient(app, base_url=ORIGIN) as client:
            rng = random.Random(seed)  # noqa: S311
            path = Path(client=client, rng=rng, kind=kind, all_profiles=all_profiles)
            try:
                path.run(index)
            except AssertionError as error:
                detail = str(error).splitlines()[0][:200] if str(error) else "assertion"
                failures.append(f"{kind} path {index} (seed {seed}), step {path.steps}: {detail}")
        kept += path.kept > 0
        steps += path.steps
    return kept, steps, failures


@pytest.mark.parametrize("all_profiles", [True, False], ids=["switch-on", "switch-off"])
@pytest.mark.parametrize("kind", KINDS)
def test_100_click_paths_answer_only_what_the_contract_allows(
    kind: str,
    all_profiles: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _approve_lighter_pool(monkeypatch)
    count = PATHS_PER_KIND if all_profiles else PATHS_PER_KIND_SWITCHED_OFF
    kept, steps, failures = _run_paths(kind, count, all_profiles=all_profiles)
    with capsys.disabled():
        print(  # the PR quotes this line as evidence
            f"\n#687 {kind} ({'switch on' if all_profiles else 'switch off'}): "
            f"{count - len(failures)}/{count} paths without an error, {steps} presses, "
            f"{kept} paths kept an action"
        )
    assert failures == []
    assert kept == (count if kind in KEEPABLE[all_profiles] else 0)


def _one_path(kind: str, *, all_profiles: bool = True) -> Path:
    client = TestClient(_app(all_profiles=all_profiles), base_url=ORIGIN)
    client.__enter__()
    rng = random.Random(716)  # noqa: S311
    return Path(client=client, rng=rng, kind=kind, all_profiles=all_profiles)


@pytest.mark.parametrize("kind", ["approximate", "exact"])
def test_the_same_birth_time_again_keeps_the_action_and_a_new_one_deletes_it(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC2 (#716): only a real change of time or place removes the kept action."""

    _approve_lighter_pool(monkeypatch)
    path = _one_path(kind)
    try:
        path.start(0)
        path.keep()
        held = path.held
        assert held is not None and path.birth_time is not None
        path._supplement(dict(path.birth_time))
        path.check_current()  # nothing changed, so the action is still kept
        path.change_birth_time()  # a different time: deleted, then a new one can be kept
        assert path.held is not None and path.held["id"] != held["id"]
    finally:
        path.client.__exit__(None, None, None)


def test_adding_a_birth_time_deletes_the_action_a_date_only_profile_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC2 (#716): the first birth time makes a date-only kept action stale."""

    _approve_lighter_pool(monkeypatch)
    path = _one_path("date_only")
    try:
        path.start(0)
        path.keep()
        held = path.held
        assert held is not None
        path.change_birth_time()
        assert path.kind == "approximate"
        assert path.held is not None and path.held["id"] != held["id"]
    finally:
        path.client.__exit__(None, None, None)


def test_deleting_the_profile_removes_the_kept_action_for_every_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _approve_lighter_pool(monkeypatch)
    for kind in KINDS:
        path = _one_path(kind)
        try:
            path.start(0)
            path.keep()
            assert path.held is not None
            path.delete_profile()
        finally:
            path.client.__exit__(None, None, None)


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


def _stored(path: Path) -> tuple[int, int]:
    """(experiment rows, experiment consent rows) in the path's database."""

    async def count(sessions: Any) -> tuple[int, int]:
        async with sessions() as session:
            experiments = await session.scalar(select(func.count()).select_from(DailyExperimentRow))
            consents = await session.scalar(
                select(func.count())
                .select_from(ConsentRow)
                .where(ConsentRow.purpose == EXPERIMENT_PURPOSE)
            )
            return int(experiments or 0), int(consents or 0)

    app = cast(Any, path.client.app)
    return cast(tuple[int, int], path.client.portal.call(count, app.state.database.sessions))  # type: ignore[union-attr]


def _offer_matches_server(path: Path, active: dict[str, Any], lens: str = "auto") -> None:
    """The invariant behind Codex P1 on #740: offered exactly when the server would accept it."""

    offered = active["experiment"]
    revision = UUID(active["revision_id"])
    key = canonical_experiment_action_key(revision, active["sections"]["micro_action"])
    answer = path._put(Target(active["revision_id"], lens, key, False).body())
    if offered is None:
        assert answer.status_code == 404, answer.text
    else:
        assert offered["action_key"] == key
        assert answer.status_code == 200, answer.text
        undone = path.client.request(
            "DELETE",
            "/v1/daily-note/experiment",
            json={
                "experiment_id": answer.json()["id"],
                "expected_version": answer.json()["version"],
            },
            headers=path.headers,
        )
        assert undone.status_code == 204, undone.text


@pytest.mark.parametrize("all_profiles", [True, False], ids=["switch-on", "switch-off"])
@pytest.mark.parametrize("kind", KINDS)
def test_the_note_left_active_after_a_new_birth_time_offers_nothing_it_cannot_keep(
    kind: str, all_profiles: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex P1 on #740: a note on an old chart snapshot shows no keep button.

    The person changes the birth time (or adds one) and does not open the new reading yet. The
    old note stays on screen, also after acknowledging the new reading; the server refuses a
    keep for it, so it must not offer one, and a hand-built keep for it stores nothing (no
    experiment row, no consent row). Opening the new reading offers its actions again, and
    both can then really be kept.
    """

    _approve_lighter_pool(monkeypatch)
    path = _one_path(kind, all_profiles=all_profiles)
    try:
        path.start(0)
        draw = path._exact_time if kind == "exact" else path._approximate_time
        body = draw()
        while body == path.birth_time:
            body = draw()
        path._supplement(body)
        note = path.client.get("/v1/daily-note")
        assert note.status_code == 200, note.text
        projection = note.json()["reading_projection"]
        update = projection["available_update"]
        assert update is not None, "a new birth time must wait as an update"
        old = projection["active"]
        assert old["revision_id"] == path.auto_revision_id
        assert old["experiment"] is None
        assert old["lighter_action"]["experiment"] is None
        transition = projection["aura_transition"]["transition_id"]
        if transition is not None:
            acknowledged = path.client.put(
                f"/v1/reading-projections/{projection['scope_key']}/aura-transition/acknowledge",
                json={"transition_id": transition},
                headers=path.headers,
            )
            assert acknowledged.status_code == 200, acknowledged.text
            assert acknowledged.json()["active"]["experiment"] is None
            assert acknowledged.json()["active"]["lighter_action"]["experiment"] is None
        revision = UUID(old["revision_id"])
        for lighter, action in (
            (False, old["sections"]["micro_action"]),
            (True, old["lighter_action"]["action"]),
        ):
            key = canonical_experiment_action_key(revision, action)
            forged = Target(old["revision_id"], "auto", key, lighter)
            assert path._put(forged.body()).status_code == 404
        assert path.client.get("/v1/daily-note/experiment").json() is None
        assert _stored(path) == (0, 0)

        activated = path.client.put(
            f"/v1/reading-projections/{projection['scope_key']}/activate",
            json={"expected_revision_id": update["revision_id"]},
            headers=path.headers,
        )
        assert activated.status_code == 200, activated.text
        active = activated.json()["active"]
        if ("approximate" if kind == "date_only" else kind) not in KEEPABLE[all_profiles]:
            assert active["experiment"] is None
            _offer_matches_server(path, active)
            assert _stored(path) == (0, 0)
            return
        card = Target(active["revision_id"], "auto", active["experiment"]["action_key"], False)
        kept = path._put(card.body())
        assert kept.status_code == 200, kept.text
        lighter_key = active["lighter_action"]["experiment"]["action_key"]
        swapped = path._put(
            {
                **Target(active["revision_id"], "auto", lighter_key, True).body(),
                "expected_experiment_id": kept.json()["id"],
                "expected_version": kept.json()["version"],
            }
        )
        assert swapped.status_code == 200, swapped.text
        assert swapped.json()["action_key"] == lighter_key
        assert _stored(path)[1] == 1
    finally:
        path.client.__exit__(None, None, None)


@pytest.mark.parametrize("all_profiles", [True, False], ids=["switch-on", "switch-off"])
def test_going_back_to_the_first_birth_time_before_acknowledging_keeps_offer_and_server_in_step(
    all_profiles: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex reproduction on #740: time A, then B (update waits), back to A, acknowledge B.

    Whatever snapshot the profile is on after that, the note offers its action exactly when
    the server would accept the keep, on the acknowledgement answer and after a reload.
    """

    _approve_lighter_pool(monkeypatch)
    path = _one_path("exact", all_profiles=all_profiles)
    try:
        path.start(0)
        first = dict(path.birth_time or {})
        other = path._exact_time()
        while other == first:
            other = path._exact_time()
        path._supplement(other)
        waiting = path.client.get("/v1/daily-note").json()["reading_projection"]
        assert waiting["available_update"] is not None
        path._supplement(first)
        transition = waiting["aura_transition"]["transition_id"]
        assert transition is not None
        acknowledged = path.client.put(
            f"/v1/reading-projections/{waiting['scope_key']}/aura-transition/acknowledge",
            json={"transition_id": transition},
            headers=path.headers,
        )
        if acknowledged.status_code == 200:
            _offer_matches_server(path, acknowledged.json()["active"])
        else:  # the waiting update was withdrawn with the change back
            assert acknowledged.status_code == 409, acknowledged.text
        reloaded = path.client.get("/v1/daily-note").json()["reading_projection"]["active"]
        _offer_matches_server(path, reloaded)
    finally:
        path.client.__exit__(None, None, None)


def test_turning_the_switch_off_stops_new_keeps_and_lets_a_kept_action_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rollback (#716): off again, nothing new is kept for a date-only profile.

    An action kept while the switch was on stays until the person closes it (outcome or
    undo) or it expires with the usual retention; turning the switch off does not delete it.
    """

    _approve_lighter_pool(monkeypatch)
    path = _one_path("date_only", all_profiles=True)
    try:
        path.start(0)
        path.keep(path.targets[0])
        held = path.held
        assert held is not None
        app = cast(Any, path.client.app)
        app.state.experiment_service._repository._keep_action_all_profiles = False
        refused = path._put(
            {
                **path.targets[1].body(),
                "expected_experiment_id": held["id"],
                "expected_version": held["version"],
            }
        )
        assert refused.status_code == 404, refused.text
        assert path.client.get("/v1/daily-note/experiment").json() == held
        closed = path.client.post(
            "/v1/daily-note/experiment/outcome",
            json={
                "experiment_id": held["id"],
                "expected_version": held["version"],
                "outcome": "helpful",
            },
            headers=path.headers,
        )
        assert closed.status_code == 200, closed.text
        assert path._put(path.targets[1].body()).status_code == 404
    finally:
        path.client.__exit__(None, None, None)
