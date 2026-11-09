"""#224: a domain 422 with no body (e.g. RadarInvalid) answers the documented ProblemResponse."""

from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from app.api.input_problem import install_input_problem


def _app() -> FastAPI:
    application = FastAPI()

    @application.post("/domain-invalid")
    async def domain_invalid() -> Response:
        response = Response(status_code=422)
        response.set_cookie("zz_test_cookie", "zz-synthetic")
        return response

    @application.post("/ok")
    async def ok() -> dict[str, str]:
        return {"ok": "yes"}

    install_input_problem(application)
    return application


def test_empty_domain_422_gets_problem_body_and_keeps_cookie() -> None:
    response = TestClient(_app()).post("/domain-invalid")
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert response.json()["code"] == "INPUT_INVALID"
    assert response.cookies.get("zz_test_cookie") == "zz-synthetic"


def test_other_responses_untouched() -> None:
    assert TestClient(_app()).post("/ok").json() == {"ok": "yes"}
