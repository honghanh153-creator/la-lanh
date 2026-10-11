"""Synthetic resource limits, retry and ownership regression proof."""

import asyncio
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.config import Settings
from app.domains.radar.service import MAX_RETAINED_REQUESTS, RadarLimitReached, RadarService
from app.domains.radar.tables import RadarRequestRow
from app.domains.relationships.models import RelationshipVoice
from app.main import create_app
from tests.radar.test_flow import ORIGIN, _full_profile
from tests.radar.test_flow import _client as _sqlite_client


def test_retry_migration_preserves_legacy_rows_and_enforces_unique_digest(tmp_path: Path) -> None:
    module = import_module("migrations.versions.20261011_0036_radar_bounded_creation")
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    try:
        with engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE radar_requests (id INTEGER PRIMARY KEY, label TEXT)")
            )
            connection.execute(
                text("INSERT INTO radar_requests VALUES (1, 'legacy'), (2, 'legacy-two')")
            )
            with Operations.context(MigrationContext.configure(connection)):
                module.upgrade()
            assert connection.scalar(text("SELECT COUNT(*) FROM radar_requests")) == 2
            columns = {
                column["name"]: column
                for column in inspect(connection).get_columns("radar_requests")
            }
            assert columns["idempotency_hash"]["nullable"] and columns["request_hash"]["nullable"]
            connection.execute(
                text("UPDATE radar_requests SET idempotency_hash = :hash WHERE id = 1"),
                {"hash": b"x" * 32},
            )
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                text("UPDATE radar_requests SET idempotency_hash = :hash WHERE id = 2"),
                {"hash": b"x" * 32},
            )
    finally:
        engine.dispose()


@contextmanager
def _client(path: Path) -> Iterator[TestClient]:
    raw = os.environ.get("LA_LANH_RADAR_TEST_POSTGRES_URL")
    if not raw:
        with _sqlite_client(path) as client:
            yield client
        return
    url = make_url(raw)
    if (url.drivername, url.host, url.port, url.database) != (
        "postgresql+asyncpg",
        "127.0.0.1",
        55434,
        "la_lanh_security_test",
    ):
        pytest.fail("refusing any database except isolated loopback synthetic test database")
    app = create_app(
        Settings(
            _env_file=None,
            environment="test",
            database_url=raw,
            cors_origins=[cast(Any, ORIGIN)],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url=ORIGIN) as client:
        assert client.portal is not None

        async def reset() -> None:
            async with app.state.database.engine.begin() as connection:
                assert (
                    await connection.scalar(text("SELECT version_num FROM alembic_version"))
                    == "20261011_0036"
                )
                await connection.execute(
                    text("TRUNCATE guest_sessions, rewrite_send_fences CASCADE")
                )

        client.portal.call(reset)
        yield client


def _start(client: TestClient) -> tuple[dict[str, str], dict[str, Any]]:
    csrf = _full_profile(client, str(uuid4()), "1994-03-12", "08:15")
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
    assert client.post("/v1/identity/claim", headers=headers).status_code == 200
    response = client.post(
        "/v1/radar/requests",
        headers={**headers, "Idempotency-Key": str(uuid4())},
        json={"recipient_label": "Mèo", "context": "crush"},
    )
    assert response.status_code == 200
    return headers, response.json()


async def _seed(
    service: RadarService, first_id: str, count: int, mixed: bool = False
) -> tuple[UUID, UUID]:
    async with service._sessions() as session, session.begin():
        template = await session.get(RadarRequestRow, UUID(first_id))
        assert template is not None
        tied_at = datetime.now(UTC) + timedelta(seconds=1)
        for index in range(count):
            id = uuid4()
            session.add(
                RadarRequestRow(
                    id=id,
                    principal_id=template.principal_id,
                    owner_guest_id=template.owner_guest_id,
                    recipient_label_ciphertext=service._envelope.encrypt(
                        f"Synthetic {index}".encode(),
                        context=f"radar-label:{id}".encode(),
                    ),
                    context="friend",
                    voice="straight_warm",
                    mode="private_check" if mixed and index % 2 else "consented_invite",
                    status=["revoked", "expired", "withdrawn"][index % 3],
                    created_at=tied_at,
                    expires_at=datetime.now(UTC) + timedelta(days=1),
                )
            )
        return template.principal_id, template.owner_guest_id


def test_combined_capacity_serializes_concurrent_creates_and_delete_frees_space(
    tmp_path: Path,
) -> None:
    with _client(tmp_path / "quota.db") as client:
        headers, first = _start(client)
        service = cast(FastAPI, client.app).state.radar_service
        assert client.portal is not None
        principal, guest = client.portal.call(_seed, service, first["id"], 98, True)

        async def race():  # type: ignore[no-untyped-def]
            return await asyncio.gather(
                *(
                    service.create(
                        principal_id=principal,
                        owner_guest_id=guest,
                        recipient_label="New",
                        context="crush",
                        voice=RelationshipVoice.STRAIGHT_WARM,
                    )
                    for _ in range(3)
                ),
                return_exceptions=True,
            )

        results = client.portal.call(race)
        assert sum(isinstance(item, tuple) for item in results) == 1
        assert sum(isinstance(item, RadarLimitReached) for item in results) == 2
        denied = client.post(
            "/v1/radar/requests",
            headers=headers,
            json={"recipient_label": "More", "context": "friend"},
        )
        assert denied.status_code == 429
        assert denied.json()["code"] == "RADAR_LIMIT_REACHED"
        assert "no-store" in denied.headers["cache-control"]
        assert (
            client.post(f"/v1/radar/requests/{first['id']}/revoke", headers=headers).status_code
            == 204
        )
        assert (
            client.post(
                "/v1/radar/requests",
                headers=headers,
                json={"recipient_label": "More", "context": "friend"},
            ).status_code
            == 429
        )
        assert client.delete(f"/v1/radar/results/{first['id']}", headers=headers).status_code == 204
        assert (
            client.post(
                "/v1/radar/requests",
                headers=headers,
                json={"recipient_label": "More", "context": "friend"},
            ).status_code
            == 200
        )


def test_retry_is_owner_bound_conflicting_or_revoked_retry_does_not_recreate(
    tmp_path: Path,
) -> None:
    with _client(tmp_path / "retry.db") as client:
        headers, first = _start(client)
        key = str(uuid4())
        headers = {**headers, "Idempotency-Key": key}
        body = {"recipient_label": "Same", "context": "crush"}
        a = client.post("/v1/radar/requests", headers=headers, json=body)
        b = client.post("/v1/radar/requests", headers=headers, json=body)
        assert a.status_code == b.status_code == 200
        assert a.json() == b.json()
        conflict = client.post(
            "/v1/radar/requests", headers=headers, json={**body, "recipient_label": "Changed"}
        )
        assert conflict.status_code == 409
        assert conflict.json()["code"] == "RADAR_IDEMPOTENCY_CONFLICT"
        assert (
            client.post(f"/v1/radar/requests/{a.json()['id']}/revoke", headers=headers).status_code
            == 204
        )
        assert client.post("/v1/radar/requests", headers=headers, json=body).status_code == 422
        # Switch browser identity without creating a second event loop for the
        # same asyncpg connection pool. No cookies from the first owner survive.
        client.cookies.clear()
        other = client
        other_headers, _ = _start(other)
        own = other.post(
            "/v1/radar/requests", headers={**other_headers, "Idempotency-Key": key}, json=body
        )
        assert own.status_code == 200 and own.json()["id"] != a.json()["id"]
        assert other.get(f"/v1/radar/requests?before={first['id']}").status_code == 404
        assert (
            other.post(f"/v1/radar/requests/{first['id']}/share", headers=other_headers).status_code
            == 404
        )


def test_parallel_same_key_creates_one_invite_and_replays_at_capacity(tmp_path: Path) -> None:
    with _client(tmp_path / "parallel-replay.db") as client:
        _, first = _start(client)
        service = cast(FastAPI, client.app).state.radar_service
        assert client.portal is not None
        principal, guest = client.portal.call(_seed, service, first["id"], 98)
        key = str(uuid4())

        async def race() -> list[Any]:
            return await asyncio.gather(
                *(
                    service.create(
                        principal_id=principal,
                        owner_guest_id=guest,
                        recipient_label="Same",
                        context="crush",
                        voice=RelationshipVoice.STRAIGHT_WARM,
                        idempotency_key=key,
                    )
                    for _ in range(3)
                )
            )

        results = client.portal.call(race)
        assert len({item[0].id for item in results}) == 1
        assert len({item[1] for item in results}) == 1

        async def count() -> int:
            from sqlalchemy import func, select

            async with service._sessions() as session:
                return int(
                    await session.scalar(select(func.count()).select_from(RadarRequestRow)) or 0
                )

        assert client.portal.call(count) == 100


def test_history_pages_are_bounded_and_old_share_does_not_enumerate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with _client(tmp_path / "pages.db") as client:
        headers, first = _start(client)
        service = cast(FastAPI, client.app).state.radar_service
        assert client.portal is not None
        client.portal.call(_seed, service, first["id"], 64, True)
        ids: list[str] = []
        cursor = ""
        while True:
            response = client.get("/v1/radar/requests?mode=consented_invite" + cursor)
            assert response.status_code == 200
            page = response.json()
            assert len(page) <= 20
            assert all(item["mode"] == "consented_invite" for item in page)
            ids.extend(item["id"] for item in page)
            if len(page) < 20:
                break
            cursor = "&before=" + page[-1]["id"]
        assert len(ids) == len(set(ids)) == 33
        assert first["id"] in ids
        assert len(client.get("/v1/radar/requests?limit=50").json()) == 50
        for invalid in ("limit=51", "limit=0", "before=invalid"):
            assert client.get("/v1/radar/requests?" + invalid).status_code == 422

        async def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("share must not enumerate history")

        monkeypatch.setattr(service, "list_owned", forbidden)
        shared = client.post(f"/v1/radar/requests/{first['id']}/share", headers=headers)
        assert shared.status_code == 200
        assert shared.json()["share_url"] == first["share_url"]


def test_private_retries_keep_one_result_and_quota_denial_does_not_compute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with _client(tmp_path / "private.db") as client:
        headers, first = _start(client)
        headers = {**headers, "Idempotency-Key": str(uuid4())}
        body = {
            "recipient_label": "Friend",
            "context": "friend",
            "birth_date": "1996-07-21",
            "birth_time_mode": "unknown",
            "place_id": "vn-hanoi",
            "consent_version": "radar-authorized-input-v1",
            "authorization_attested": True,
        }
        a = client.post("/v1/radar/private-checks", headers=headers, json=body)
        assert a.status_code == 200
        service = cast(FastAPI, client.app).state.radar_service
        assert client.portal is not None
        client.portal.call(_seed, service, first["id"], MAX_RETAINED_REQUESTS - 2)

        async def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("must not recompute a replay or over-capacity request")

        monkeypatch.setattr(service._birth, "calculate_transient_chart", forbidden)
        b = client.post("/v1/radar/private-checks", headers=headers, json=body)
        assert b.status_code == 200 and b.json() == a.json()
        fresh = client.post(
            "/v1/radar/private-checks",
            headers={**headers, "Idempotency-Key": str(uuid4())},
            json=body,
        )
        assert fresh.status_code == 429
        assert fresh.json()["code"] == "RADAR_LIMIT_REACHED"
        changed = client.post(
            "/v1/radar/private-checks", headers=headers, json={**body, "birth_date": "1997-07-21"}
        )
        assert changed.status_code == 409
        assert changed.json()["code"] == "RADAR_IDEMPOTENCY_CONFLICT"
