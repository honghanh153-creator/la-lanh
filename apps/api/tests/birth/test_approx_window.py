"""PL-37: an approximate birth-time window maps to a midpoint on the entered birth date.

Before PL-37 nobody born 00-06h had a window; they picked "night" and were stored at 23:00 of
the entered date, up to ~20 h from the real time. Synthetic dates only.
"""

from datetime import UTC, datetime, time
from itertools import pairwise
from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.domains.astro.models import TimePrecision
from app.domains.birth.models import ApproxWindow, BirthTimeMode
from app.domains.birth.service import _resolve_time
from tests.birth.test_birth_api import birth_client, birth_repository, create_guest

__all__ = ["birth_client", "birth_repository"]

# The local clock range each window covers in the web picker (birthTimeOptions.ts).
WINDOW_RANGES: dict[ApproxWindow, tuple[int, int]] = {
    ApproxWindow.DAWN: (0, 6),
    ApproxWindow.MORNING: (6, 10),
    ApproxWindow.NOON: (10, 14),
    ApproxWindow.AFTERNOON: (14, 18),
    ApproxWindow.EVENING: (18, 22),
    ApproxWindow.NIGHT: (22, 24),
}


def test_every_window_has_a_range_and_the_ranges_tile_the_day() -> None:
    assert set(WINDOW_RANGES) == set(ApproxWindow)
    edges = sorted(WINDOW_RANGES.values())
    assert edges[0][0] == 0 and edges[-1][1] == 24
    assert all(left[1] == right[0] for left, right in pairwise(edges))


@pytest.mark.parametrize(
    ("window", "expected"),
    [
        (ApproxWindow.DAWN, time(hour=3)),
        (ApproxWindow.MORNING, time(hour=8)),
        (ApproxWindow.NOON, time(hour=12)),
        (ApproxWindow.AFTERNOON, time(hour=15)),
        (ApproxWindow.EVENING, time(hour=19)),
        (ApproxWindow.NIGHT, time(hour=23)),
    ],
)
def test_window_midpoint_is_inside_its_range(window: ApproxWindow, expected: time) -> None:
    resolved, precision = _resolve_time(BirthTimeMode.APPROX_WINDOW, None, window)
    assert resolved == expected
    assert precision is TimePrecision.APPROXIMATE
    start, end = WINDOW_RANGES[window]
    assert start <= expected.hour < end


def test_a_dawn_birth_is_charted_at_three_am_of_the_entered_date(
    birth_client: TestClient,
) -> None:
    csrf = create_guest(birth_client)
    headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf}
    created = birth_client.post(
        "/v1/birth-profile", json={"birth_date": "1990-09-01"}, headers=headers
    )
    assert created.status_code == 200

    response = birth_client.post(
        "/v1/birth-profile/supplement",
        json={
            "birth_time_mode": "approx_window",
            "birth_time_local": None,
            "approx_window": "dawn",
            "place_id": "vn-ho-chi-minh",
            "consent_version": "birth-profile-deep-v1",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    payload = cast(dict[str, object], response.json())
    assert payload["time_precision"] == "approximate"
    chart = cast(dict[str, object], payload["chart"])
    # 03:00 in Ho Chi Minh City (UTC+7 in 1990) is 20:00 UTC the previous day.
    expected_ut = datetime(1990, 8, 31, 20, tzinfo=UTC)
    j2000 = datetime(2000, 1, 1, 12, tzinfo=UTC)
    expected_jd = 2451545.0 + (expected_ut - j2000).total_seconds() / 86400
    assert chart["julian_day_ut"] == pytest.approx(expected_jd, abs=1e-6)

    state = birth_client.get("/v1/birth-profile/supplement")
    assert state.status_code == 200
    assert state.json()["birth_time_mode"] == "approx_window"
    assert state.json()["approx_window"] == "dawn"
    edit = birth_client.get("/v1/birth-profile/supplement/edit")
    assert edit.status_code == 200
    assert edit.json()["approx_window"] == "dawn"


def test_an_unknown_window_is_rejected(birth_client: TestClient) -> None:
    csrf = create_guest(birth_client)
    headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf}
    birth_client.post("/v1/birth-profile", json={"birth_date": "1990-09-01"}, headers=headers)
    response = birth_client.post(
        "/v1/birth-profile/supplement",
        json={
            "birth_time_mode": "approx_window",
            "birth_time_local": None,
            "approx_window": "midnight",
            "place_id": "vn-ho-chi-minh",
            "consent_version": "birth-profile-deep-v1",
        },
        headers=headers,
    )
    assert response.status_code == 422
