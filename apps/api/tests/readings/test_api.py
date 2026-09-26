from collections.abc import Iterator
from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.birth.test_birth_api import (
    MemoryBirthRepository,
    birth_client,
    birth_repository,
    create_guest,
)

__all__ = ["birth_client", "birth_repository"]


@pytest.fixture
def reading_client() -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        yield client


def _create_deep_profile(client: TestClient) -> None:
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
