"""Codex r55 on the birth-date correction (#119 findings, now U2 #123), as regressions.

1. Malformed correction requests answer a fixed 422 problem that never echoes birth input.
2. Two simultaneous corrections on the local SQLite runtime give one success and one
   ``BIRTH_PROFILE_CHANGED``, never a database-locked error.
3. The PostgreSQL probe's wait for the commit is bounded, surfaces an early failure and cleans up
   its task (checked without PostgreSQL).
"""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.birth.errors import BirthProfileChanged
from tests.saved.copy_flow import ORIGIN, make_app, start_guest

BIRTH_VALUES = ("1992-07-20", "07:30", "Hà Nội")


@pytest.mark.parametrize(
    "body",
    [
        {"birth_date": "1992-07-20", "confirm_birth_date": "1992-07-20"},  # no expected_revision
        {
            "birth_date": "20/07/1992",
            "confirm_birth_date": "1992-07-20",
            "expected_revision": "2026-10-30T00:00:00Z",
        },
        {
            "birth_date": "1992-07-20",
            "confirm_birth_date": "1992-07-20",
            "expected_revision": "2026-10-30T00:00:00Z",
            "birth_time_local": "07:30",
        },
    ],
)
def test_malformed_corrections_never_echo_birth_input(tmp_path: Path, body: dict[str, Any]) -> None:
    app = make_app(tmp_path / "validation.db")
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        response = client.put("/v1/birth-profile/date", headers=headers, json=body)
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.headers["cache-control"].startswith("no-store")
        assert response.json()["code"] == "BIRTH_INPUT_INVALID"
        assert not any(value in response.text for value in (*BIRTH_VALUES, "20/07/1992"))


def test_simultaneous_corrections_conflict_instead_of_locking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "race.db"
    app = make_app(path)
    with TestClient(app, base_url=ORIGIN) as client:
        start_guest(client)
        before = client.get("/v1/birth-profile").json()
        with sqlite3.connect(path) as connection:
            guest_id = UUID(connection.execute("SELECT id FROM guest_sessions").fetchone()[0])
        service = app.state.birth_chart_service

        async def run() -> list[Any]:
            barrier = asyncio.Barrier(2)
            original = AsyncSession.scalar

            async def gate(self: AsyncSession, statement: Any, *args: Any, **kwargs: Any) -> Any:
                result = await original(self, statement, *args, **kwargs)
                text = str(statement)
                if "birth_profiles" in text and "guest_sessions" not in text:
                    # Both tabs have read the profile revision before either writes.
                    try:
                        await asyncio.wait_for(barrier.wait(), 1)
                    except TimeoutError:
                        pass  # serialized by the writer reservation: nobody to meet
                return result

            monkeypatch.setattr(AsyncSession, "scalar", gate)

            async def correct(value: str) -> Any:
                return await service.correct_date(
                    guest_id=guest_id,
                    birth_date=date.fromisoformat(value),
                    confirm_birth_date=date.fromisoformat(value),
                    expected_revision=datetime.fromisoformat(before["profile_revision"]),
                )

            return list(
                await asyncio.gather(
                    correct("1992-07-20"), correct("1993-07-20"), return_exceptions=True
                )
            )

        assert client.portal is not None
        results = client.portal.call(run)
        assert not any(isinstance(item, OperationalError) for item in results), results
        assert sum(isinstance(item, BirthProfileChanged) for item in results) == 1
        assert sum(not isinstance(item, BaseException) for item in results) == 1


async def test_the_probe_wait_fails_fast_when_the_correction_raises() -> None:
    from tests.birth.test_postgres_date_correction_probe import _await_commit

    async def failing() -> None:
        raise ValueError("synthetic failure before commit")

    task = asyncio.create_task(failing())

    async def never() -> bool:
        return False

    with pytest.raises(ValueError, match="synthetic failure"):
        await asyncio.wait_for(_await_commit(task, never), 2)


async def test_the_probe_wait_times_out_and_cancels_a_stalled_correction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.birth import test_postgres_date_correction_probe as probe_module
    from tests.erasure_journal import test_postgres_restore_probe as restore

    monkeypatch.setattr(restore, "BOUND_SECONDS", 0.2)
    stalled = asyncio.create_task(asyncio.sleep(3600))

    async def never() -> bool:
        return False

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(probe_module._await_commit(stalled, never), 2)
    assert stalled.cancelled()
