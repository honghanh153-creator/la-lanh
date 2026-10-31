from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.config import Settings
from app.domains.birth.errors import BirthProfileChanged
from app.domains.birth.tables import BirthProfileRow, ChartSnapshotRow
from app.domains.daily.tables import DailyNoteRow
from app.domains.readings.models import ReadingPurpose
from app.domains.readings.tables import ReadingPlanRow
from app.main import create_app
from tests.birth.test_birth_api import (
    MemoryBirthRepository,
    birth_client,
    birth_repository,
    create_guest,
)

__all__ = ["birth_client", "birth_repository"]


@pytest.fixture
def reading_client(tmp_path: Path) -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'readings.db'}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        yield client


def _create_deep_profile(client: TestClient) -> str:
    csrf = create_guest(client)
    headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf}
    assert (
        client.post(
            "/v1/birth-profile",
            json={"birth_date": "1990-01-01"},
            headers=headers,
        ).status_code
        == 200
    )

    assert (
        client.post(
            "/v1/birth-profile/supplement",
            json={
                "birth_time_mode": "exact",
                "birth_time_local": "19:00",
                "approx_window": None,
                "place_id": "vn-ho-chi-minh",
                "consent_version": "birth-profile-deep-v1",
            },
            headers=headers,
        ).status_code
        == 200
    )

    return csrf


def _restore_legacy_date_only_pointer(client: TestClient) -> None:
    """Old databases could retain precision fields with a date-only live pointer."""
    database = cast(FastAPI, client.app).state.database

    async def restore() -> None:
        async with database.sessions() as session, session.begin():
            profile = await session.scalar(select(BirthProfileRow))
            basic = await session.scalar(
                select(ChartSnapshotRow).order_by(ChartSnapshotRow.created_at).limit(1)
            )
            assert profile is not None and basic is not None
            assert profile.birth_time_ciphertext is not None
            assert profile.birth_place_ciphertext is not None
            assert basic.id != profile.current_snapshot_id
            profile.current_snapshot_id = basic.id

    assert client.portal is not None
    client.portal.call(restore)


def test_birth_editor_restores_owned_values_without_exposing_them_in_state(
    reading_client: TestClient,
) -> None:
    _create_deep_profile(reading_client)
    response = reading_client.get("/v1/birth-profile/supplement/edit")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert response.json()["birth_time_local"] == "19:00"
    assert response.json()["place"]["place_id"] == "vn-ho-chi-minh"
    state = reading_client.get("/v1/birth-profile/supplement").json()
    assert "birth_time_local" not in state and "place" not in state


def test_birth_editor_never_returns_another_guests_details(
    reading_client: TestClient,
) -> None:
    _create_deep_profile(reading_client)
    reading_client.cookies.clear()
    assert reading_client.get("/v1/birth-profile/supplement/edit").status_code == 401
    created = reading_client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "guest-editor-second-owner-1234567890",
        },
    )
    assert created.status_code == 200
    csrf = created.json()["csrf_token"]
    assert reading_client.get("/v1/birth-profile/supplement/edit").status_code == 404
    assert (
        reading_client.post(
            "/v1/birth-profile",
            json={"birth_date": "1992-06-10"},
            headers={"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf},
        ).status_code
        == 200
    )
    response = reading_client.get("/v1/birth-profile/supplement/edit")
    assert response.json() == {
        "birth_time_mode": "unknown",
        "birth_time_local": None,
        "approx_window": None,
        "place": None,
    }


def test_birth_editor_clears_precision_after_erasure(reading_client: TestClient) -> None:
    csrf = _create_deep_profile(reading_client)
    response = reading_client.request(
        "DELETE",
        "/v1/birth-profile/supplement",
        json={"remove_time": True, "remove_place": True},
        headers={"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    editor = reading_client.get("/v1/birth-profile/supplement/edit")
    assert editor.json()["birth_time_local"] is None
    assert editor.json()["place"] is None


def test_birth_change_before_publication_cannot_reactivate_previous_subject(
    reading_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _create_deep_profile(reading_client)
    app = cast(FastAPI, reading_client.app)
    service = app.state.reading_application_service
    repository = service._repository
    publish = repository.publish_available
    changed = False

    async def change_before_publish(guest_id, profile_id, scope_key, revision_id):  # type: ignore[no-untyped-def]
        nonlocal changed
        changed = True
        await app.state.birth_chart_service.create_date_only(
            guest_id=guest_id, birth_date=date(1991, 11, 15)
        )
        return await publish(guest_id, profile_id, scope_key, revision_id)

    monkeypatch.setattr(repository, "publish_available", change_before_publish)

    async def project_old_source() -> None:
        async with app.state.database.sessions() as session:
            profile = await session.scalar(select(BirthProfileRow))
            assert profile is not None
            guest_id = profile.guest_id
        snapshot = await app.state.daily_note_service.current_birth_snapshot(guest_id)
        with pytest.raises(BirthProfileChanged):
            await service.project(
                guest_id=guest_id, snapshot=snapshot, purpose=ReadingPurpose.DAILY_NOTE
            )

    assert reading_client.portal is not None
    reading_client.portal.call(project_old_source)
    assert changed


@pytest.mark.parametrize("boundary", ["legacy_note", "projection"])
def test_daily_response_never_mixes_birth_sources(
    reading_client: TestClient, monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    _create_deep_profile(reading_client)
    app = cast(FastAPI, reading_client.app)
    service = (
        app.state.daily_note_service
        if boundary == "legacy_note"
        else app.state.reading_application_service
    )
    method = "today" if boundary == "legacy_note" else "project"
    original = getattr(service, method)
    changed = False

    async def change_after_result(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal changed
        result = await original(*args, **kwargs)
        guest_id = args[0] if args else kwargs["guest_id"]
        await app.state.birth_chart_service.create_date_only(
            guest_id=guest_id, birth_date=date(1991, 11, 15)
        )
        changed = True
        return result

    monkeypatch.setattr(service, method, change_after_result)
    response = reading_client.get("/v1/daily-note")
    assert changed
    assert response.status_code == 409
    assert response.json()["code"] == "BIRTH_PROFILE_CHANGED"


def test_late_legacy_daily_write_cannot_replace_current_subject_note(
    reading_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _create_deep_profile(reading_client)
    app = cast(FastAPI, reading_client.app)
    daily = app.state.daily_note_service
    repository = daily._repository
    save = repository.get_or_create
    changed = False

    async def change_before_save(record):  # type: ignore[no-untyped-def]
        nonlocal changed
        if not changed:
            changed = True
            await app.state.birth_chart_service.create_date_only(
                guest_id=record.guest_id, birth_date=date(1991, 11, 15)
            )
            await daily.today(record.guest_id)
        return await save(record)

    monkeypatch.setattr(repository, "get_or_create", change_before_save)
    response = reading_client.get("/v1/daily-note")
    assert changed
    assert response.status_code == 409

    async def stored_source_is_current() -> bool:
        async with app.state.database.sessions() as session:
            profile = await session.scalar(select(BirthProfileRow))
            note = await session.scalar(select(DailyNoteRow))
            assert profile is not None and note is not None
            return bool(profile.current_snapshot_id == note.chart_snapshot_id)

    assert reading_client.portal is not None
    assert reading_client.portal.call(stored_source_is_current)


@pytest.mark.parametrize("path", ["/v1/insights/overview", "/v1/insights/readings/reading_detail"])
@pytest.mark.parametrize("date_only_pointer", [False, True])
def test_insight_cannot_bind_pre_erasure_chart_to_post_erasure_snapshot(
    reading_client: TestClient, monkeypatch: pytest.MonkeyPatch, path: str, date_only_pointer: bool
) -> None:
    _create_deep_profile(reading_client)
    if date_only_pointer:
        _restore_legacy_date_only_pointer(reading_client)
    birth = cast(FastAPI, reading_client.app).state.birth_chart_service
    chart_for_config = birth.chart_for_config
    erased = False

    async def erase_after_calculation(guest_id, config):  # type: ignore[no-untyped-def]
        nonlocal erased
        chart = await chart_for_config(guest_id, config)
        await birth.remove_supplement(guest_id, remove_time=True, remove_place=True)
        erased = True
        return chart

    monkeypatch.setattr(birth, "chart_for_config", erase_after_calculation)
    response = reading_client.get(path)
    assert erased
    assert response.status_code == 409
    assert response.json()["code"] == "BIRTH_PROFILE_CHANGED"
    assert reading_client.get("/v1/birth-profile").json()["calculation"]["chart_type"] == (
        "date_only_natal"
    )


def test_insight_is_locked_until_deep_birth_fields_exist(
    birth_client: TestClient,
) -> None:
    csrf = create_guest(birth_client)
    response = birth_client.post(
        "/v1/birth-profile",
        json={"birth_date": "1990-01-01"},
        headers={"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf},
    )
    assert response.status_code == 200

    insight = birth_client.get("/v1/insights/overview")
    assert insight.status_code == 200
    assert insight.json() == {
        "status": "locked",
        "required_fields": ["birth_time", "birth_place"],
        "reading": None,
        "bodies": [],
        "houses_available": False,
        "time_precision": "unknown",
    }


def test_precision_erasure_removes_derived_reading_even_without_retained_natal(
    reading_client: TestClient,
) -> None:
    csrf = _create_deep_profile(reading_client)
    headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf}
    _restore_legacy_date_only_pointer(reading_client)
    assert reading_client.get("/v1/insights/readings/reading_detail").status_code == 200
    database = cast(FastAPI, reading_client.app).state.database

    async def legacy_snapshot_cleanup() -> int:
        async with database.sessions() as session, session.begin():
            profile = await session.scalar(select(BirthProfileRow))
            assert profile is not None
            await session.execute(
                delete(ChartSnapshotRow).where(ChartSnapshotRow.id != profile.current_snapshot_id)
            )
            return int(await session.scalar(select(func.count()).select_from(ReadingPlanRow)) or 0)

    assert reading_client.portal is not None
    assert reading_client.portal.call(legacy_snapshot_cleanup) > 0
    assert (
        reading_client.request(
            "DELETE",
            "/v1/birth-profile/supplement",
            headers=headers,
            json={"remove_time": True, "remove_place": True},
        ).status_code
        == 200
    )

    async def remaining_plans() -> int:
        async with database.sessions() as session:
            return int(await session.scalar(select(func.count()).select_from(ReadingPlanRow)) or 0)

    assert reading_client.portal.call(remaining_plans) == 0


def test_switching_tradition_recomputes_private_input_server_side(
    birth_client: TestClient,
    birth_repository: MemoryBirthRepository,
) -> None:
    _create_deep_profile(birth_client)

    western = birth_client.get("/v1/insights/overview?tradition=western")
    jyotish = birth_client.get("/v1/insights/overview?tradition=jyotish")

    assert western.status_code == jyotish.status_code == 200
    western_payload = cast(dict[str, object], western.json())
    jyotish_payload = cast(dict[str, object], jyotish.json())
    assert cast(dict[str, object], western_payload["reading"])["tradition"] == "western"
    assert cast(dict[str, object], jyotish_payload["reading"])["tradition"] == "jyotish"
    assert western_payload["bodies"] != jyotish_payload["bodies"]
    claims = cast(list[object], cast(dict[str, object], jyotish_payload["reading"])["claims"])
    assert len(claims) >= 4
    stored = next(iter(birth_repository.supplements.values()))
    assert stored.birth_time_ciphertext is not None
    assert "19:00" not in stored.birth_time_ciphertext


def test_reading_detail_and_personalized_sky_expose_one_safe_rich_contract(
    reading_client: TestClient,
) -> None:
    _create_deep_profile(reading_client)

    overview = reading_client.get("/v1/insights/overview?tradition=western")
    detail = reading_client.get("/v1/insights/readings/reading_detail?tradition=western")
    sky = reading_client.get("/v1/insights/readings/personalized_sky?tradition=western")

    assert overview.status_code == detail.status_code == sky.status_code == 200
    overview_payload = overview.json()
    detail_payload = detail.json()
    sky_payload = sky.json()
    assert overview_payload["status"] == "ready"
    assert overview_payload["reading"] is not None
    assert overview_payload["reading_projection"] == detail_payload
    assert detail_payload["active"]["mode"] == "full_synthesis"
    assert detail_payload["active"]["purpose"] == "reading_detail"
    assert detail_payload["active"]["tradition"] == "western"
    assert detail_payload["active"]["sections"]["transit"] is None
    assert detail_payload["active"]["evidence"]["title"] == "Căn cứ trong lá số"
    assert sky_payload["active"]["purpose"] == "personalized_sky"
    assert sky_payload["active"]["sections"]["transit"] is None or isinstance(
        sky_payload["active"]["sections"]["transit"], str
    )

    repeated = reading_client.get("/v1/insights/readings/personalized_sky?tradition=western")
    assert repeated.status_code == 200
    assert repeated.json() == sky_payload

    serialized = str(
        {
            "overview_projection": overview_payload["reading_projection"],
            "detail": detail_payload,
            "sky": sky_payload,
        }
    )
    for forbidden in (
        "1990-01-01",
        "19:00",
        "birth_date",
        "birth_time",
        "birth_place",
        "10.8231",
        "106.6297",
        "gate_policy_version",
        "renderer_version",
        "prompt",
        "provider",
    ):
        assert forbidden not in serialized


def test_an_approximate_birth_time_reads_the_time_stable_chart(
    reading_client: TestClient,
) -> None:
    """#143 E1: an approximate time used to give an empty "limited" reading that talked about
    itself. Planet signs (except the Moon) and aspects do not move within a time window, so the
    reading uses them and leaves houses, angles and the Moon out."""

    csrf = create_guest(reading_client)
    headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf}
    reading_client.post("/v1/birth-profile", json={"birth_date": "1990-09-01"}, headers=headers)
    reading_client.post(
        "/v1/birth-profile/supplement",
        json={
            "birth_time_mode": "approx_window",
            "birth_time_local": None,
            "approx_window": "morning",
            "place_id": "vn-ho-chi-minh",
            "consent_version": "birth-profile-deep-v1",
        },
        headers=headers,
    )

    overview = reading_client.get("/v1/insights/overview?tradition=western")

    assert overview.status_code == 200
    active = cast(
        dict[str, object], cast(dict[str, object], overview.json()["reading_projection"])["active"]
    )
    assert active["mode"] == "full_synthesis"
    assert active["precision"] == "approximate", "never labelled exact"
    assert active.get("experiment") is None, "exact-only experiment stays closed"
    sections = cast(dict[str, str], active["sections"])
    prose = " ".join(text for text in sections.values() if text)
    assert "Chưa cần đoán cho đầy trang" not in prose
    evidence = " ".join(cast(list[str], cast(dict[str, object], active["evidence"])["claims"]))
    for time_bound in ("Mặt Trăng", "Nhà ", "Cung mọc", "Thiên đỉnh", "Nakshatra"):
        assert time_bound not in evidence, (time_bound, evidence)
