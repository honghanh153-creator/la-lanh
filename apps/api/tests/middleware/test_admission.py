import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.admission import AdmissionControlMiddleware, AdmissionPolicy


def test_guest_creation_is_bounded_before_the_endpoint_runs() -> None:
    app = FastAPI()
    calls = 0

    @app.post("/v1/guest-sessions")
    async def create_guest() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"status": "created"}

    app.add_middleware(AdmissionControlMiddleware, window_seconds=60)
    with TestClient(app) as client:
        for _ in range(10):
            assert client.post("/v1/guest-sessions").status_code == 200
        limited = client.post("/v1/guest-sessions")

    assert limited.status_code == 429
    assert limited.headers["retry-after"]
    assert limited.headers["cache-control"] == "no-store"
    assert limited.json()["code"] == "ADMISSION_LIMITED"
    assert calls == 10


def test_unmetered_health_route_is_not_affected() -> None:
    app = FastAPI()

    @app.get("/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(AdmissionControlMiddleware)
    with TestClient(app) as client:
        for _ in range(20):
            assert client.get("/v1/health").status_code == 200


def test_invite_creation_and_resend_have_separate_limits() -> None:
    app = FastAPI()
    calls = {"create": 0, "resend": 0, "revoke": 0}

    @app.post("/v1/la-chung/requests")
    async def create_invite() -> dict[str, str]:
        calls["create"] += 1
        return {"status": "created"}

    @app.post("/v1/la-chung/requests/{request_id}/resend")
    async def resend_invite(request_id: str) -> dict[str, str]:
        calls["resend"] += 1
        return {"request_id": request_id}

    @app.post("/v1/la-chung/requests/{request_id}/revoke")
    async def revoke_invite(request_id: str) -> dict[str, str]:
        calls["revoke"] += 1
        return {"request_id": request_id}

    app.add_middleware(AdmissionControlMiddleware, window_seconds=60)
    with TestClient(app) as client:
        for _ in range(10):
            assert client.post("/v1/la-chung/requests").status_code == 200
        assert client.post("/v1/la-chung/requests").status_code == 429

        for _ in range(20):
            assert client.post("/v1/la-chung/requests/request-1/resend").status_code == 200
        assert client.post("/v1/la-chung/requests/request-1/resend").status_code == 429

        for _ in range(25):
            assert client.post("/v1/la-chung/requests/request-1/revoke").status_code == 200

    assert calls == {"create": 10, "resend": 20, "revoke": 25}


def test_birth_and_public_route_families_share_their_policy_buckets() -> None:
    app = FastAPI()

    @app.post("/v1/birth-profile")
    @app.post("/v1/birth-profile/supplement")
    async def birth_compute() -> dict[str, str]:
        return {"status": "computed"}

    @app.get("/v1/public/la-chung/{token}")
    @app.post("/v1/public/la-chung/{token}/responses")
    async def public_capability(token: str) -> dict[str, str]:
        return {"token": token}

    app.add_middleware(AdmissionControlMiddleware, window_seconds=60)
    with TestClient(app) as client:
        for _ in range(10):
            assert client.post("/v1/birth-profile").status_code == 200
            assert client.post("/v1/birth-profile/supplement").status_code == 200
        assert client.post("/v1/birth-profile").status_code == 429

        for _ in range(60):
            assert client.get("/v1/public/la-chung/token").status_code == 200
            assert client.post("/v1/public/la-chung/token/responses").status_code == 200
        assert client.get("/v1/public/la-chung/token").status_code == 429


def test_global_limit_rejects_a_new_peer_without_charging_its_bucket() -> None:
    middleware = AdmissionControlMiddleware(FastAPI(), window_seconds=60)
    policy = AdmissionPolicy("global-test", per_peer=2, global_limit=2)

    async def exercise() -> None:
        assert (await middleware._admit(policy, "peer-a"))[0] is True
        assert (await middleware._admit(policy, "peer-b"))[0] is True
        assert (await middleware._admit(policy, "peer-c"))[0] is False

    asyncio.run(exercise())
