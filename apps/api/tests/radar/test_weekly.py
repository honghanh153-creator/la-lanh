""" "Hai bạn tuần này" (Hợp gu AL1 direction C, second half). Off by default.

Keeping a pair stores the other person's birth date beyond the 24-hour check, so it needs the
switch AND the owner's approval of the opt-in sentences; the card is built from the current sky
against both date-only charts, shows an initial only, and the pair is deletable.
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
from app.domains.content.copy_approval import load_registry
from app.domains.radar import weekly
from app.main import create_app
from tests.radar.test_reading import FORBIDDEN, JARGON

ORIGIN = "http://127.0.0.1:5173"
RECIPIENT_OPTIN = (
    "Giữ ngày sinh của tôi, đã mã hoá, tối đa 90 ngày để hai bạn xem phần mỗi tuần. "
    "Tôi xoá được bất cứ lúc nào."
)


def _chart(day: date):  # type: ignore[no-untyped-def]
    engine = NatalChartEngine()
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(day.year, day.month, day.day, 5, tzinfo=UTC),
            latitude=21.0285,
            longitude=105.8542,
        ),
        CalculationConfig.western_recommended(),
    )
    return engine, date_only_reduction(chart)


@pytest.fixture
def approved(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = load_registry()
    monkeypatch.setattr(
        weekly,
        "approved_copy",
        lambda entry_id: registry[entry_id].text if entry_id in registry else None,
    )


def test_every_line_is_registered_and_plain() -> None:
    """Reading lines wait for Codex; the opt-in sentences are owner-approved (AQ1/AR1, 21.11)."""

    registry = load_registry()
    for entry_id in weekly.registry_ids():
        entry = registry[entry_id]
        if entry_id.startswith("privacy."):
            assert (entry.category, entry.status, entry.approver, entry.date) == (
                "privacy",
                "approved",
                "owner",
                "2026-11-21",
            )
        else:
            assert (entry.category, entry.status) == ("reading", "pending")
        low = entry.text.lower()
        assert not [term for term in JARGON if term in low], entry.text
        assert not [term for term in FORBIDDEN if term in low], entry.text
    assert weekly.weekly_sentences() == {
        "optin-label": "Giữ cặp này để mỗi tuần xem hai bạn tuần này.",
        "optin-help": registry["privacy.radar.weekly.optin-help"].text,
        "home-note": "Chỉ hiện chữ cái đầu của tên. Bấm tắt là xoá luôn cặp này.",
        # Owner AR1 (21.11.2026), word for word: the invited person's own box.
        "recipient-optin": RECIPIENT_OPTIN,
    }


def test_week_starts_on_monday_and_the_card_is_deterministic() -> None:
    assert weekly.week_start(date(2026, 11, 20)) == date(2026, 11, 16)
    engine, a = _chart(date(1994, 3, 12))
    _, b = _chart(date(1996, 7, 21))
    first = weekly.weekly_hits(engine, (a, b), date(2026, 11, 16))
    assert first == weekly.weekly_hits(engine, (a, b), date(2026, 11, 16))
    assert all(tone in {"easy", "watch"} and orb <= weekly.ORB for tone, orb in first.values())


@pytest.mark.usefixtures("approved")
def test_card_names_no_date_and_never_guesses() -> None:
    card = weekly.card_for(
        {"communication": ("easy", 1.0), "pace": ("watch", 0.5)}, date(2026, 11, 16)
    )
    assert card is not None
    assert card.easy == "Tuần này dễ: nói chuyện và chốt kế hoạch cùng nhau."
    assert card.watch == "Dễ vướng: vội vàng, nói nhanh hơn nghĩ."
    assert card.try_line == "Thử: chia việc thành phần nhỏ và nói rõ ai làm phần nào."
    quiet = weekly.card_for({}, date(2026, 11, 16))
    assert quiet is not None and quiet.quiet and quiet.easy is None


def test_nothing_shows_while_lines_are_pending() -> None:
    assert weekly.card_for({"communication": ("easy", 1.0)}, date(2026, 11, 16)) is None


def _client(path: Path, *, on: bool) -> TestClient:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{path}",
            cors_origins=[cast(Any, ORIGIN)],
            guest_cookie_secure=False,
            radar_weekly_pairs=on,
        )
    )
    return TestClient(app, base_url=ORIGIN)


def _owner(client: TestClient) -> dict[str, str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "radar-weekly-owner-1234567890",
        },
    )
    headers = {"Origin": ORIGIN, "X-CSRF-Token": str(guest.json()["csrf_token"])}
    client.post("/v1/birth-profile", headers=headers, json={"birth_date": "1994-03-12"})
    client.post(
        "/v1/birth-profile/supplement",
        headers=headers,
        json={
            "birth_time_mode": "exact",
            "birth_time_local": "08:15",
            "place_id": "vn-hanoi",
            "consent_version": "birth-profile-deep-v1",
        },
    )
    assert client.post("/v1/identity/claim", headers=headers).status_code == 200
    return headers


CHECK = {
    "recipient_label": "Mèo Hoang",
    "context": "partner",
    "birth_date": "1996-07-21",
    "birth_time_mode": "unknown",
    "place_id": "vn-hanoi",
    "consent_version": "radar-authorized-input-v1",
    "authorization_attested": True,
}
B_DATE = "1996-07-21"


def _invite(
    client: TestClient, headers: dict[str, str], label: str = "Mèo Hoang"
) -> tuple[TestClient, dict[str, Any], str, dict[str, Any]]:
    """A sends a link; B (no session, no profile) opens it. Returns (B's client, invite, token)."""

    invite = client.post(
        "/v1/radar/requests",
        headers=headers,
        json={"recipient_label": label, "context": "partner"},
    ).json()
    token = invite["share_url"].rsplit("/", 1)[-1]
    recipient = TestClient(client.app, base_url=ORIGIN)
    preview = recipient.get(f"/v1/public/radar/{token}")
    assert preview.status_code == 200
    return recipient, invite, token, preview.json()


def _accept(recipient: TestClient, invite: dict[str, Any], *, keep: bool | None) -> Any:
    body: dict[str, Any] = {
        "request_id": invite["id"],
        "birth_date": B_DATE,
        "consent_version": "radar-pair-date-v1",
    }
    if keep is not None:
        body["keep_weekly"] = keep
    return recipient.post(
        "/v1/public/radar/current/accept-date", headers={"Origin": ORIGIN}, json=body
    )


def _kept(database: Path) -> int:
    with sqlite3.connect(database) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM radar_weekly_pairs").fetchone()[0])


def test_switched_off_keeps_nothing(tmp_path: Path) -> None:
    database = tmp_path / "off.db"
    with _client(database, on=False) as client:
        headers = _owner(client)
        options = client.get("/v1/public/radar/consent-options").json()
        assert options["weekly"] is False and options["weekly_sentences"] == {}
        recipient, invite, _, preview = _invite(client, headers)
        assert preview["weekly_offer"] is False
        assert _accept(recipient, invite, keep=True).status_code == 422
        assert client.get("/v1/radar/weekly").status_code == 404
        assert _kept(database) == 0


def test_switch_alone_does_not_open_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(weekly, "approved_copy", lambda entry_id: None)
    with _client(tmp_path / "switch.db", on=True) as client:
        assert cast(FastAPI, client.app).state.radar_service.weekly_enabled is False
        assert client.get("/v1/public/radar/consent-options").json()["weekly"] is False


def test_the_sender_can_never_keep_a_pair(tmp_path: Path) -> None:
    """AR1: the old sender-side box is gone, on every path (private checks included)."""

    database = tmp_path / "sender.db"
    with _client(database, on=True) as client:
        headers = _owner(client)
        refused = client.post(
            "/v1/radar/private-checks", headers=headers, json={**CHECK, "keep_weekly": True}
        )
        assert refused.status_code == 422
        assert _kept(database) == 0


@pytest.mark.usefixtures("approved")
def test_only_the_recipients_own_tick_keeps_the_pair(tmp_path: Path) -> None:
    database = tmp_path / "on.db"
    with _client(database, on=True) as client:
        headers = _owner(client)
        options = client.get("/v1/public/radar/consent-options").json()
        assert options["weekly"] is True
        assert options["weekly_sentences"]["recipient-optin"] == RECIPIENT_OPTIN

        # Default is No: no field, or an explicit false, keeps nothing.
        for keep in (None, False):
            recipient, invite, _, preview = _invite(client, headers, label="Ai khác")
            assert preview["weekly_offer"] is True
            assert _accept(recipient, invite, keep=keep).status_code == 200
        assert _kept(database) == 0
        assert client.get("/v1/radar/weekly").json()["items"] == []

        recipient, invite, _, _ = _invite(client, headers)
        assert _accept(recipient, invite, keep=True).status_code == 200
        listed = client.get("/v1/radar/weekly")
        assert listed.status_code == 200
        assert listed.headers["cache-control"].startswith("no-store")
        items = listed.json()["items"]
        assert len(items) == 1
        item = items[0]
        assert item["initial"] == "M." and item["context"] == "partner"
        assert item["easy"] or item["watch"] or item["quiet"]
        for raw in ("1996", "Mèo", "Hoang"):
            assert raw not in listed.text

        with sqlite3.connect(database) as connection:
            stored = connection.execute(
                "SELECT birth_date_ciphertext, label_ciphertext, consent_version, expires_at,"
                " created_at FROM radar_weekly_pairs"
            ).fetchone()
        assert "1996" not in stored[0] and "Mèo" not in stored[1]
        assert stored[2] == "radar-weekly-recipient-v1"
        kept_days = (datetime.fromisoformat(stored[3]) - datetime.fromisoformat(stored[4])).days
        assert kept_days == 90

        stranger = TestClient(client.app, base_url=ORIGIN)
        assert stranger.get("/v1/radar/weekly").status_code == 404
        assert client.delete(f"/v1/radar/weekly/{item['id']}", headers=headers).status_code == 204
        assert client.get("/v1/radar/weekly").json()["items"] == []
        assert _kept(database) == 0


@pytest.mark.usefixtures("approved")
def test_withdrawing_the_result_deletes_the_kept_pair(tmp_path: Path) -> None:
    database = tmp_path / "withdraw.db"
    with _client(database, on=True) as client:
        headers = _owner(client)
        recipient, invite, _, _ = _invite(client, headers)
        assert _accept(recipient, invite, keep=True).status_code == 200
        assert _kept(database) == 1
        withdrawn = recipient.post(
            "/v1/public/radar/receipt/withdraw",
            headers={"Origin": ORIGIN},
            json={"request_id": invite["id"]},
        )
        assert withdrawn.status_code == 204
        assert _kept(database) == 0


@pytest.mark.usefixtures("approved")
def test_the_invite_link_deletes_the_pair_after_the_result_is_gone(tmp_path: Path) -> None:
    """The pair outlives the 30-day result; B can still delete it with the link (AR1)."""

    database = tmp_path / "link.db"
    with _client(database, on=True) as client:
        headers = _owner(client)
        recipient, invite, token, _ = _invite(client, headers)
        assert _accept(recipient, invite, keep=True).status_code == 200
        # The result is gone (here: the sender deleted it); the kept pair is not tied to it.
        assert (
            client.delete(f"/v1/radar/results/{invite['id']}", headers=headers).status_code == 204
        )
        assert _kept(database) == 1

        new_device = TestClient(client.app, base_url=ORIGIN)
        assert (
            new_device.post(
                "/v1/public/radar/invite/withdraw",
                headers={"Origin": "https://evil.test"},
                json={"token": token},
            ).status_code
            == 403
        )
        assert _kept(database) == 1
        deleted = new_device.post(
            "/v1/public/radar/invite/withdraw", headers={"Origin": ORIGIN}, json={"token": token}
        )
        assert deleted.status_code == 204
        assert _kept(database) == 0
        again = new_device.post(
            "/v1/public/radar/invite/withdraw", headers={"Origin": ORIGIN}, json={"token": token}
        )
        assert again.status_code == 404


@pytest.mark.usefixtures("approved")
def test_no_room_means_no_offer_and_nothing_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.domains.radar.service as service_module

    monkeypatch.setattr(service_module, "MAX_WEEKLY_PAIRS", 1)
    database = tmp_path / "full.db"
    with _client(database, on=True) as client:
        headers = _owner(client)
        recipient, invite, _, _ = _invite(client, headers)
        assert _accept(recipient, invite, keep=True).status_code == 200
        recipient, invite, _, preview = _invite(client, headers, label="Ai khác")
        assert preview["weekly_offer"] is False
        # A tick sent anyway (an old tab) still gives the result and keeps nothing more.
        assert _accept(recipient, invite, keep=True).status_code == 200
        assert _kept(database) == 1


@pytest.mark.usefixtures("approved")
def test_expired_pairs_and_card_links_are_purged(tmp_path: Path) -> None:
    import asyncio
    from datetime import timedelta

    from app.domains.radar.retention import purge_expired_keepsakes

    database = tmp_path / "purge.db"
    with _client(database, on=True) as client:
        headers = _owner(client)
        recipient, invite, _, _ = _invite(client, headers)
        assert _accept(recipient, invite, keep=True).status_code == 200
        sessions = cast(FastAPI, client.app).state.database.sessions
        now = datetime.now(UTC)
        assert asyncio.run(purge_expired_keepsakes(sessions, now=now))["weekly_pairs"] == 0
        assert _kept(database) == 1
        later = now + timedelta(days=91)
        assert asyncio.run(purge_expired_keepsakes(sessions, now=later))["weekly_pairs"] == 1
        assert _kept(database) == 0
