"""Two keep requests at once on PostgreSQL, for every kind of profile (#873, from #716).

Keeping a Daily action rests on the guest row lock (``SELECT ... FOR UPDATE`` in
``_require_owned_active_target``) and the version compare-and-swap, so a guest has at most one open
action even when requests race. #740 opened keeping to date-only and approximate-time profiles
through that same path, but only sequential click paths were tested, and SQLite cannot test the
race (two writers fail with "database is locked"). This runs against a migrated, throwaway
PostgreSQL only: the ``postgres-concurrency`` CI job, or a local one set in
``LA_LANH_TEST_POSTGRES_URL``. Otherwise it is skipped.

Each round sends two requests together on one app (the app's event loop interleaves them):

* the same action kept twice: one kept action, version 1, both answers name it;
* two different actions kept: one is kept, the other is asked to confirm (409);
* two confirmed replacements on the same version: one wins (version 2), the other is a stale 409.

After each round exactly one action is open and no request fails with a server error.
Fictional people only: synthetic birth dates and a fixed random seed.
"""

from __future__ import annotations

import os
import random
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from app.config import Settings
from app.main import create_app
from tests.daily.test_keep_action_paths import (
    KINDS,
    ORIGIN,
    Path,
    Target,
    _approve_lighter_pool,
)

ROUNDS = 5


@pytest.fixture
def postgres_url() -> str:
    database_url = os.environ.get("LA_LANH_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("set LA_LANH_TEST_POSTGRES_URL for isolated PostgreSQL verification")
    url = make_url(database_url)
    if (
        url.drivername != "postgresql+asyncpg"
        or url.host != "127.0.0.1"
        or url.port not in (55432, 55434)
        or url.database != "la_lanh_security_test"
    ):
        pytest.fail("refusing to use any database except the isolated localhost test database")
    return database_url


@pytest.fixture(autouse=True)
def _lighter_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    # The checked-in lighter sentences, as the click paths serve them (#634): two actions to keep.
    _approve_lighter_pool(monkeypatch)


@pytest.fixture
def client(postgres_url: str) -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url=postgres_url,
            cors_origins=[ORIGIN],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
            keep_action_all_profiles=True,
        )
    )
    with TestClient(app, base_url=ORIGIN) as test_client:
        yield test_client


def _together(*calls: Callable[[], Any]) -> list[Any]:
    """Send the calls at the same time (TestClient hands each one to the app's event loop)."""

    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = [pool.submit(call) for call in calls]
        return [future.result() for future in futures]


def _person(client: TestClient, kind: str, round_no: int) -> Path:
    path = Path(client=client, rng=random.Random(873_000 + round_no), kind=kind)  # noqa: S311
    path.start(10_000 + round_no)
    assert path.targets, f"{kind}: the note offers an action to keep"
    return path


def _two_targets(path: Path) -> tuple[Target, Target]:
    distinct = {(t.revision_id, t.action_key, t.lens): t for t in path.targets}
    targets = list(distinct.values())
    assert len(targets) >= 2, f"{path.kind}: the card's action and the lighter one are offered"
    return targets[0], targets[1]


def _open_action(path: Path) -> dict[str, Any]:
    current = path.client.get("/v1/daily-note/experiment")
    assert current.status_code == 200, current.text
    payload: dict[str, Any] | None = current.json()
    assert payload is not None and payload["state"] == "chosen", payload
    return payload


@pytest.mark.parametrize("kind", KINDS)
def test_the_same_action_kept_twice_at_once_is_kept_once(client: TestClient, kind: str) -> None:
    for round_no in range(ROUNDS):
        path = _person(client, kind, round_no)
        body = path.targets[0].body()
        first, second = _together(partial(path._put, body), partial(path._put, body))
        statuses = sorted((first.status_code, second.status_code))
        assert all(status < 500 for status in statuses), (kind, statuses)
        assert set(statuses) <= {200, 409}, (kind, statuses, first.text, second.text)
        kept = [r.json() for r in (first, second) if r.status_code == 200]
        assert kept and {k["id"] for k in kept} == {kept[0]["id"]}
        assert all(k["version"] == 1 for k in kept)
        assert _open_action(path)["id"] == kept[0]["id"]


@pytest.mark.parametrize("kind", KINDS)
def test_two_different_actions_kept_at_once_keep_exactly_one(client: TestClient, kind: str) -> None:
    for round_no in range(ROUNDS):
        path = _person(client, kind, 100 + round_no)
        a, b = _two_targets(path)
        first, second = _together(partial(path._put, a.body()), partial(path._put, b.body()))
        statuses = sorted((first.status_code, second.status_code))
        assert statuses == [200, 409], (kind, statuses, first.text, second.text)
        winner = next(r.json() for r in (first, second) if r.status_code == 200)
        held = _open_action(path)
        assert held["id"] == winner["id"] and held["version"] == 1


@pytest.mark.parametrize("kind", KINDS)
def test_two_replacements_on_the_same_version_let_one_win(client: TestClient, kind: str) -> None:
    for round_no in range(ROUNDS):
        path = _person(client, kind, 200 + round_no)
        a, b = _two_targets(path)
        kept = path._put(a.body())
        assert kept.status_code == 200, kept.text
        expected = {"expected_experiment_id": kept.json()["id"], "expected_version": 1}
        replace = {**b.body(), **expected}
        first, second = _together(partial(path._put, replace), partial(path._put, replace))
        statuses = sorted((first.status_code, second.status_code))
        assert all(status < 500 for status in statuses), (kind, statuses)
        assert set(statuses) <= {200, 409}, (kind, statuses, first.text, second.text)
        winners = [r.json() for r in (first, second) if r.status_code == 200]
        assert winners and {w["id"] for w in winners} == {winners[0]["id"]}
        assert winners[0]["version"] == 2
        held = _open_action(path)
        assert held["id"] == winners[0]["id"] and held["action_key"] == b.action_key
