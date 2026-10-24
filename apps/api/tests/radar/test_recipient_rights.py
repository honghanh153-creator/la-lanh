"""P09 D2: B keeps view and withdrawal of a consented result without the receipt."""

from pathlib import Path

from fastapi.testclient import TestClient

from tests.radar.test_flow import (
    ORIGIN,
    _assert_no_raw_birth_data,
    _client,
    _full_profile,
    _shift_completion,
)


def _accepted_invite(owner: TestClient) -> tuple[TestClient, str, str, str, dict[str, object]]:
    """A invites B, B accepts. Returns B's client, B's CSRF, request id, token, B's result."""
    owner_csrf = _full_profile(owner, "radar-owner-guest-123456789", "1994-03-12", "08:15")
    headers = {"Origin": ORIGIN, "X-CSRF-Token": owner_csrf}
    assert owner.post("/v1/identity/claim", headers=headers).status_code == 200
    created = owner.post(
        "/v1/radar/requests",
        headers=headers,
        json={"recipient_label": "Mèo", "context": "friend"},
    )
    assert created.status_code == 200
    request_id = created.json()["id"]
    token = created.json()["share_url"].rsplit("/", 1)[-1]
    recipient = TestClient(owner.app, base_url=ORIGIN)
    assert recipient.get(f"/v1/public/radar/{token}").status_code == 200
    recipient_csrf = _full_profile(
        recipient, "radar-recipient-guest-1234567", "1996-07-21", "19:40"
    )
    accepted = recipient.post(
        "/v1/public/radar/current/accept",
        headers={"Origin": ORIGIN, "X-CSRF-Token": recipient_csrf},
        json={"request_id": request_id, "consent_version": "radar-pair-v1"},
    )
    assert accepted.status_code == 200
    return recipient, recipient_csrf, request_id, token, accepted.json()


def _drop_receipt(client: TestClient) -> None:
    client.cookies.delete("la_lanh_radar_receipt", path="/v1/public/radar/receipt")
    assert client.get("/v1/public/radar/receipt").status_code == 404


def test_recipient_session_views_and_withdraws_without_the_receipt(tmp_path: Path) -> None:
    with _client(tmp_path / "radar.db") as owner:
        recipient, recipient_csrf, request_id, _, accepted = _accepted_invite(owner)
        _drop_receipt(recipient)

        listed = recipient.get("/v1/radar/received")
        assert listed.status_code == 200
        items = listed.json()["items"]
        assert [item["request_id"] for item in items] == [request_id]
        assert items[0]["context"] == "friend"
        # B never sees the label A chose for B.
        assert "Mèo" not in listed.text and "recipient_label" not in items[0]

        viewed = recipient.get(f"/v1/radar/received/{request_id}")
        assert viewed.status_code == 200
        assert viewed.json()["request_id"] == request_id
        assert viewed.json()["mode"] == "consented_invite"
        assert viewed.json()["headline"] == accepted["headline"]
        assert viewed.json()["recipient_label"] is None and "Mèo" not in viewed.text
        _assert_no_raw_birth_data(viewed.json())

        # Withdrawal is a mutation: it needs B's CSRF token and a trusted origin.
        assert (
            recipient.post(
                f"/v1/radar/received/{request_id}/withdraw", headers={"Origin": ORIGIN}
            ).status_code
            == 404
        )
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 200
        withdrawn = recipient.post(
            f"/v1/radar/received/{request_id}/withdraw",
            headers={"Origin": ORIGIN, "X-CSRF-Token": recipient_csrf},
        )
        assert withdrawn.status_code == 204
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 404
        assert recipient.get(f"/v1/radar/received/{request_id}").status_code == 404
        assert recipient.get("/v1/radar/received").json()["items"] == []


def test_only_the_recipient_session_reaches_a_received_result(tmp_path: Path) -> None:
    with _client(tmp_path / "radar.db") as owner:
        _, _, request_id, _, _ = _accepted_invite(owner)
        stranger = TestClient(owner.app, base_url=ORIGIN)
        stranger_csrf = _full_profile(
            stranger, "radar-stranger-guest-1234567", "1990-01-02", "06:30"
        )
        anonymous = TestClient(owner.app, base_url=ORIGIN)

        # A owns the result but is not its recipient: A's session never opens B's side.
        for client in (owner, stranger):
            assert client.get("/v1/radar/received").json()["items"] == []
            assert client.get(f"/v1/radar/received/{request_id}").status_code == 404
        assert anonymous.get("/v1/radar/received").status_code == 401
        assert anonymous.get(f"/v1/radar/received/{request_id}").status_code == 404
        assert (
            stranger.post(
                f"/v1/radar/received/{request_id}/withdraw",
                headers={"Origin": ORIGIN, "X-CSRF-Token": stranger_csrf},
            ).status_code
            == 404
        )
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 200


def test_invite_link_withdraws_without_receipt_or_session_and_never_opens_a_view(
    tmp_path: Path,
) -> None:
    with _client(tmp_path / "radar.db") as owner:
        _, _, request_id, token, _ = _accepted_invite(owner)
        # B on a new device: no guest session, no receipt, only the invite link.
        fresh = TestClient(owner.app, base_url=ORIGIN)
        assert fresh.get(f"/v1/public/radar/{token}").status_code == 404

        # B on a new device cannot learn the request id, so only the token is sent; a request
        # id binding is not accepted on this path.
        with_binding = fresh.post(
            "/v1/public/radar/invite/withdraw",
            headers={"Origin": ORIGIN},
            json={"request_id": request_id, "token": token},
        )
        assert with_binding.status_code == 422
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 200
        wrong_token = fresh.post(
            "/v1/public/radar/invite/withdraw",
            headers={"Origin": ORIGIN},
            json={"token": "x" * 43},
        )
        assert wrong_token.status_code == 404
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 200

        withdrawn = fresh.post(
            "/v1/public/radar/invite/withdraw",
            headers={"Origin": ORIGIN},
            json={"token": token},
        )
        assert withdrawn.status_code == 204
        assert withdrawn.headers["cache-control"].startswith("no-store")
        assert withdrawn.headers["referrer-policy"] == "no-referrer"
        assert withdrawn.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 404
        replay = fresh.post(
            "/v1/public/radar/invite/withdraw",
            headers={"Origin": ORIGIN},
            json={"token": token},
        )
        assert replay.status_code == 404


def test_received_rights_end_with_the_result_window(tmp_path: Path) -> None:
    database = tmp_path / "radar.db"
    with _client(database) as owner:
        recipient, recipient_csrf, request_id, token, _ = _accepted_invite(owner)
        _shift_completion(database, request_id, days=29)
        assert len(recipient.get("/v1/radar/received").json()["items"]) == 1
        _shift_completion(database, request_id, days=2)
        assert recipient.get("/v1/radar/received").json()["items"] == []
        assert recipient.get(f"/v1/radar/received/{request_id}").status_code == 404
        assert (
            recipient.post(
                f"/v1/radar/received/{request_id}/withdraw",
                headers={"Origin": ORIGIN, "X-CSRF-Token": recipient_csrf},
            ).status_code
            == 404
        )
        assert (
            recipient.post(
                "/v1/public/radar/invite/withdraw",
                headers={"Origin": ORIGIN},
                json={"token": token},
            ).status_code
            == 404
        )


def test_a_private_check_never_appears_as_received(tmp_path: Path) -> None:
    with _client(tmp_path / "radar.db") as owner:
        owner_csrf = _full_profile(owner, "radar-private-owner-123456789", "1994-03-12", "08:15")
        headers = {"Origin": ORIGIN, "X-CSRF-Token": owner_csrf}
        assert owner.post("/v1/identity/claim", headers=headers).status_code == 200
        created = owner.post(
            "/v1/radar/private-checks",
            headers=headers,
            json={
                "recipient_label": "Người hay seen",
                "context": "crush",
                "birth_date": "1996-07-21",
                "birth_time_local": "19:40",
                "place_id": "vn-dak-lak",
                "consent_version": "radar-authorized-input-v1",
                "authorization_attested": True,
            },
        )
        assert created.status_code == 200
        request_id = created.json()["request_id"]
        assert owner.get("/v1/radar/received").json()["items"] == []
        assert owner.get(f"/v1/radar/received/{request_id}").status_code == 404
