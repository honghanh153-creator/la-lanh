"""Hợp gu AL1 (owner, 20.11.2026): birth-date-only readings and the invite-first consent.

- An owner whose own profile has only a birth date is not blocked; the pair is then read from
  both birth dates ("Dựa vào: ngày sinh của hai bạn."), ranked against date-only pairs.
- Đồng nghiệp and Gia đình exist; until their registry lines are approved they serve the
  approved "someone" sentences.
- The paths that need new owner-only consent sentences (the other person's date alone under a
  tick, and the one-field invite) stay closed unless the switch is on AND the owner approved
  every sentence.
"""

import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput
from app.domains.birth.service import date_only_reduction
from app.domains.radar import consent_drafts
from app.domains.radar import reading as radar
from app.domains.radar.reading import build_radar_reading
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
APPROVED = {key: f"Câu đã duyệt {index}." for index, key in enumerate(consent_drafts.SENTENCE_KEYS)}


def _client(path: Path, *, invite_first: bool = False) -> TestClient:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{path}",
            cors_origins=[cast(Any, ORIGIN)],
            guest_cookie_secure=False,
            radar_invite_first_consent=invite_first,
        )
    )
    return TestClient(app, base_url=ORIGIN)


def _guest(client: TestClient, key: str, birth_date: str) -> dict[str, str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": key,
        },
    )
    assert guest.status_code == 200
    headers = {"Origin": ORIGIN, "X-CSRF-Token": str(guest.json()["csrf_token"])}
    assert (
        client.post(
            "/v1/birth-profile", headers=headers, json={"birth_date": birth_date}
        ).status_code
        == 200
    )
    assert client.post("/v1/identity/claim", headers=headers).status_code == 200
    return headers


def _date_only_chart(day: date):  # type: ignore[no-untyped-def]
    engine = NatalChartEngine()
    noon = datetime(day.year, day.month, day.day, 5, 0, tzinfo=UTC)  # 12:00 in Vietnam
    chart = engine.calculate_chart(
        ChartInput(utc_datetime=noon, latitude=21.0285, longitude=105.8542),
        CalculationConfig.western_recommended(),
    )
    return engine, date_only_reduction(chart)


def _date_only_bundle(a: date, b: date):  # type: ignore[no-untyped-def]
    engine, chart_a = _date_only_chart(a)
    _, chart_b = _date_only_chart(b)
    return engine.calculate_relationship_bundle(chart_a, chart_b)


def test_date_only_reading_says_what_it_rests_on_and_is_deterministic() -> None:
    bundle = _date_only_bundle(date(1994, 3, 12), date(1996, 7, 21))
    first = build_radar_reading(bundle, context="coworker", basis=radar.BASIS_DATE_ONLY)
    second = build_radar_reading(bundle, context="coworker", basis=radar.BASIS_DATE_ONLY)

    assert first == second
    metadata = first["metadata"]
    assert metadata["basis"] == "date_only"
    assert metadata["basis_note"] == "Dựa vào: ngày sinh của hai bạn."
    assert metadata["tier_calibration_version"] == "radar-tier-ref-date-v1"
    # Nothing a birth date cannot fix: no Moon, no houses.
    assert all("moon" not in {c["body_a"], c["body_b"]} for c in first["strongest_contacts"])
    assert not bundle.synastry.house_overlays


def test_date_only_pairs_rank_against_date_only_pairs() -> None:
    ease = radar.TIER_REFERENCE_DATE_ONLY[10]  # the median of date-only pairs
    assert radar.rank_percentile(ease, radar.TIER_REFERENCE_DATE_ONLY) == pytest.approx(50.0)
    assert radar.rank_percentile(ease) < 50.0  # the full-chart reference would undersell it


def test_full_basis_reading_is_unchanged_by_al1() -> None:
    bundle = _date_only_bundle(date(1990, 1, 1), date(1992, 2, 2))
    full = build_radar_reading(bundle, context="friend")
    assert "basis" not in full["metadata"]
    assert full["metadata"]["tier_calibration_version"] == "radar-tier-ref-v1"
    with pytest.raises(ValueError):
        build_radar_reading(bundle, context="friend", basis="guess")


@pytest.mark.parametrize("context", ["coworker", "family"])
def test_new_contexts_serve_approved_someone_copy_while_pending(context: str) -> None:
    bundle = _date_only_bundle(date(1988, 5, 9), date(1991, 11, 30))
    new = build_radar_reading(bundle, context=context, basis=radar.BASIS_DATE_ONLY)
    someone = build_radar_reading(bundle, context="someone", basis=radar.BASIS_DATE_ONLY)
    assert new["pair_signature"] == someone["pair_signature"]
    assert new["sections"] == someone["sections"]


def test_new_context_uses_its_line_once_approved(monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = _date_only_bundle(date(1988, 5, 9), date(1991, 11, 30))
    base = build_radar_reading(bundle, context="coworker", basis=radar.BASIS_DATE_ONLY)
    tier_key = base["pair_signature"]["tier"]["key"]

    def approved(entry_id: str, fallback: str) -> str:
        return "Dễ làm chung" if entry_id == f"radar.coworker.tier.{tier_key}" else fallback

    monkeypatch.setattr(radar, "copy_text", approved)
    reading = build_radar_reading(bundle, context="coworker", basis=radar.BASIS_DATE_ONLY)
    assert reading["pair_signature"]["tier"]["label"] == "Dễ làm chung"


def test_invite_first_needs_every_sentence_approved(monkeypatch: pytest.MonkeyPatch) -> None:
    assert consent_drafts.invite_first_sentences() is None  # drafts ship pending
    monkeypatch.setattr(consent_drafts, "approved_copy", lambda entry_id: "Câu.")
    assert set(consent_drafts.invite_first_sentences() or {}) == set(consent_drafts.SENTENCE_KEYS)


def test_date_only_owner_is_sent_to_the_invite_while_switched_off(tmp_path: Path) -> None:
    """No time or place of the other person is collected just to be dropped."""

    with _client(tmp_path / "date-owner.db") as client:
        headers = _guest(client, "radar-date-owner-123456789", "1994-03-12")
        response = client.post(
            "/v1/radar/private-checks",
            headers=headers,
            json={
                "recipient_label": "Mèo",
                "context": "family",
                "birth_date": "1966-08-02",
                "birth_time_mode": "exact",
                "birth_time_local": "07:30",
                "place_id": "vn-hanoi",
                "consent_version": "radar-authorized-input-v1",
                "authorization_attested": True,
            },
        )
        assert response.status_code == 409
        invite = client.post(
            "/v1/radar/requests",
            headers=headers,
            json={"recipient_label": "Mèo", "context": "family"},
        )
        assert invite.status_code == 200


def test_switched_off_paths_stay_closed(tmp_path: Path) -> None:
    with _client(tmp_path / "closed.db") as client:
        headers = _guest(client, "radar-closed-owner-12345678", "1994-03-12")
        options = client.get("/v1/public/radar/consent-options")
        assert options.status_code == 200
        assert options.headers["cache-control"].startswith("no-store")
        assert options.json() == {
            "invite_first": False,
            "sentences": {},
            "authorized_input_version": "radar-authorized-input-v1",
            "date_consent_version": "radar-pair-date-v1",
        }
        date_only = {
            "recipient_label": "Mèo",
            "context": "crush",
            "birth_date": "1996-07-21",
            "birth_time_mode": "date_only",
            "consent_version": "radar-authorized-input-v2",
            "authorization_attested": True,
        }
        assert (
            client.post("/v1/radar/private-checks", headers=headers, json=date_only).status_code
            == 422
        )
        invite = client.post(
            "/v1/radar/requests",
            headers=headers,
            json={"recipient_label": "Mèo", "context": "crush"},
        ).json()
        recipient = TestClient(client.app, base_url=ORIGIN)
        token = invite["share_url"].rsplit("/", 1)[-1]
        assert recipient.get(f"/v1/public/radar/{token}").status_code == 200
        refused = recipient.post(
            "/v1/public/radar/current/accept-date",
            headers={"Origin": ORIGIN},
            json={
                "request_id": invite["id"],
                "birth_date": "1996-07-21",
                "consent_version": "radar-pair-date-v1",
            },
        )
        assert refused.status_code == 404


def test_switch_alone_does_not_open_unapproved_paths(tmp_path: Path) -> None:
    with _client(tmp_path / "switch-only.db", invite_first=True) as client:
        assert client.get("/v1/public/radar/consent-options").json()["invite_first"] is False
        service = cast(FastAPI, client.app).state.radar_service
        assert service.invite_first_enabled is False


@pytest.fixture
def approved_sentences(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(consent_drafts, "approved_copy", lambda entry_id: "Câu đã duyệt.")
    import app.api.v1.routes.radar as routes
    import app.domains.radar.service as service_module

    monkeypatch.setattr(service_module, "invite_first_sentences", lambda: APPROVED)
    monkeypatch.setattr(routes, "invite_first_sentences", lambda: APPROVED)


@pytest.mark.usefixtures("approved_sentences")
def test_one_field_invite_reads_the_pair_without_storing_the_date(tmp_path: Path) -> None:
    database = tmp_path / "one-field.db"
    with _client(database, invite_first=True) as client:
        options = client.get("/v1/public/radar/consent-options").json()
        assert options["invite_first"] is True
        assert options["sentences"] == APPROVED
        assert options["authorized_input_version"] == "radar-authorized-input-v2"

        headers = _guest(client, "radar-one-field-owner-1234567", "1994-03-12")
        invite = client.post(
            "/v1/radar/requests",
            headers=headers,
            json={"recipient_label": "Mèo", "context": "coworker"},
        ).json()
        with sqlite3.connect(database) as connection:
            profiles_before = connection.execute("SELECT COUNT(*) FROM birth_profiles").fetchone()

        recipient = TestClient(client.app, base_url=ORIGIN)  # no guest session, no profile
        token = invite["share_url"].rsplit("/", 1)[-1]
        second_tab = TestClient(client.app, base_url=ORIGIN)  # opened the same link earlier
        assert second_tab.get(f"/v1/public/radar/{token}").status_code == 200
        preview = recipient.get(f"/v1/public/radar/{token}")
        assert preview.json()["requires_exact_birth_profile"] is False
        body = {
            "request_id": invite["id"],
            "birth_date": "1996-07-21",
            "consent_version": "radar-pair-date-v1",
        }
        assert (
            recipient.post(
                "/v1/public/radar/current/accept-date",
                headers={"Origin": "https://evil.test"},
                json=body,
            ).status_code
            == 403
        )
        too_young = {**body, "birth_date": f"{date.today().year - 10}-01-01"}
        assert (
            recipient.post(
                "/v1/public/radar/current/accept-date", headers={"Origin": ORIGIN}, json=too_young
            ).status_code
            == 422
        )
        accepted = recipient.post(
            "/v1/public/radar/current/accept-date", headers={"Origin": ORIGIN}, json=body
        )
        assert accepted.status_code == 200
        assert accepted.headers["cache-control"].startswith("no-store")
        assert accepted.headers["referrer-policy"] == "no-referrer"
        assert accepted.json()["metadata"]["basis"] == "date_only"
        assert "1996" not in accepted.text and "Mèo" not in accepted.text
        assert "la_lanh_radar_receipt" in accepted.headers["set-cookie"]

        # B reopens with the receipt; A sees the pair; the token cannot be used twice.
        assert recipient.get("/v1/public/radar/receipt").status_code == 200
        owner_view = client.get(f"/v1/radar/results/{invite['id']}")
        assert owner_view.status_code == 200
        assert owner_view.json()["metadata"]["basis"] == "date_only"
        replay = second_tab.post(
            "/v1/public/radar/current/accept-date", headers={"Origin": ORIGIN}, json=body
        )
        assert replay.status_code in {404, 422}

        with sqlite3.connect(database) as connection:
            assert (
                connection.execute("SELECT COUNT(*) FROM birth_profiles").fetchone()
                == profiles_before
            )
            row = connection.execute(
                "SELECT recipient_guest_id, consent_version, status FROM radar_requests"
            ).fetchone()
        assert row == (None, "radar-pair-date-v1", "completed")

        # B withdraws with the receipt: neither side can open the result any more.
        withdrawn = recipient.post(
            "/v1/public/radar/receipt/withdraw",
            headers={"Origin": ORIGIN},
            json={"request_id": invite["id"]},
        )
        assert withdrawn.status_code == 204
        assert client.get(f"/v1/radar/results/{invite['id']}").status_code == 404


@pytest.mark.usefixtures("approved_sentences")
def test_date_only_attestation_when_switched_on(tmp_path: Path) -> None:
    with _client(tmp_path / "attest-v2.db", invite_first=True) as client:
        headers = _guest(client, "radar-attest-v2-owner-1234567", "1994-03-12")
        body = {
            "recipient_label": "Mèo",
            "context": "crush",
            "birth_date": "1996-07-21",
            "birth_time_mode": "date_only",
            "consent_version": "radar-authorized-input-v2",
            "authorization_attested": True,
        }
        ok = client.post("/v1/radar/private-checks", headers=headers, json=body)
        assert ok.status_code == 200
        assert ok.json()["metadata"]["basis"] == "date_only"
        assert ok.json()["metadata"]["basis_note"] == "Dựa vào: ngày sinh của hai bạn."
        assert "precision_note" not in ok.json()["metadata"]
        assert "1996" not in ok.text
        old_attestation = {**body, "consent_version": "radar-authorized-input-v1"}
        assert (
            client.post(
                "/v1/radar/private-checks", headers=headers, json=old_attestation
            ).status_code
            == 422
        )
        with_place = {**body, "place_id": "vn-hanoi"}
        assert (
            client.post("/v1/radar/private-checks", headers=headers, json=with_place).status_code
            == 422
        )
