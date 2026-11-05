"""One app-wide answer for request input that fails validation (#170).

FastAPI's default 422 repeats the submitted values in ``detail[].input``: Tarot questions, birth
dates, radar and Lá chung answers. Clients, proxies or error reporting could keep that copy. Every
route that does not already answer its own fixed code (account, birth, human Tarot) now answers
one problem+json without any submitted value, field name or location, and is never cached.
"""

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.routes.guest_sessions import ProblemResponse

INPUT_INVALID = "INPUT_INVALID"
PROBLEM_MEDIA_TYPE = "application/problem+json"
_PROBLEM_REF = "#/components/schemas/ProblemResponse"
_DEFAULT_SCHEMAS = ("HTTPValidationError", "ValidationError")


async def input_invalid(_request: Request, _error: Exception) -> JSONResponse:
    # The error is deliberately unused: its details hold the submitted values.
    return JSONResponse(
        status_code=422,
        content={
            "type": "about:blank",
            "title": "Request input was rejected",
            "status": 422,
            "code": INPUT_INVALID,
        },
        media_type=PROBLEM_MEDIA_TYPE,
        headers={"Cache-Control": "no-store, max-age=0"},
    )


def document_input_problems(schema: dict[str, Any]) -> dict[str, Any]:
    """Describe every 422 as the problem body above instead of ``HTTPValidationError``."""

    for operations in schema.get("paths", {}).values():
        for operation in operations.values():
            responses = operation.get("responses", {})
            current = responses.get("422")
            if current is None:
                continue
            if PROBLEM_MEDIA_TYPE in current.get("content", {}):
                continue  # a router's own documented problem (account, human Tarot)
            responses["422"] = {
                "description": "Request input was rejected",
                "content": {PROBLEM_MEDIA_TYPE: {"schema": {"$ref": _PROBLEM_REF}}},
            }
    schemas = schema.setdefault("components", {}).setdefault("schemas", {})
    for name in _DEFAULT_SCHEMAS:
        schemas.pop(name, None)
    schemas.setdefault("ProblemResponse", ProblemResponse.model_json_schema())
    return schema


def install_input_problem(application: FastAPI) -> None:
    application.add_exception_handler(RequestValidationError, input_invalid)
    generate: Callable[[], dict[str, Any]] = application.openapi

    def openapi() -> dict[str, Any]:
        if application.openapi_schema is None:
            application.openapi_schema = document_input_problems(generate())
        return application.openapi_schema

    application.openapi = openapi  # type: ignore[method-assign]
