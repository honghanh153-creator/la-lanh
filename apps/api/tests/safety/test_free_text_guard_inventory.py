"""Discover request text, rather than remembering only the existing input screens.

New body/query strings need a crisis guard or an exact, reasoned exception. Enum,
UUID and date/time values have a closed format; length/pattern alone never exempts text.
The three birthplace search screens share one API; Studio is operator-only.
"""

import inspect
from collections.abc import Iterator
from typing import Annotated, Any

import pytest
from fastapi import Body, Depends, FastAPI
from fastapi.routing import APIRoute, iter_route_contexts
from pydantic import BaseModel, Field, SecretStr

from app.api.crisis_guard import crisis_guard
from app.config import Settings
from app.main import create_app

FieldKey = tuple[str, str, str]
Schema = dict[str, Any]

# Keyed by endpoint AND field. Reusing a protocol name on a new endpoint is not exempt.
EXCEPTIONS: dict[tuple[str, str], dict[str, str]] = {
    ("POST", "/v1/guest-sessions"): {
        "body.consent_version": "Published consent version selected by the client.",
        "body.purpose": "Consent purpose identifier selected by the client.",
        "body.idempotency_key": "Generated retry identifier, not a typed message.",
    },
    ("POST", "/v1/session/content-rewrite-consent"): {
        "body.consent_version": "Published consent version selected by the client.",
    },
    ("POST", "/v1/account/login/code"): {
        "body.email": "Login address with email syntax, not reflective text.",
    },
    ("POST", "/v1/account/login/verify"): {
        "body.code": "Six-digit login challenge.",
    },
    ("POST", "/v1/account/login/google/verify"): {
        "body.code": "Opaque OAuth authorization code.",
    },
    ("POST", "/v1/birth-places/search"): {
        "body.query": (
            "Place lookup shared by OptionalBirthDetails, BirthSupplementPage and "
            "RadarPrivateStartPage. Not sent as reflective text."
        ),
    },
    ("POST", "/v1/birth-profile/supplement"): {
        "body.birth_time_local": "Structured HH:MM time.",
        "body.place_id": "Identifier selected from birthplace search results.",
        "body.consent_version": "Published consent version selected by the client.",
    },
    ("POST", "/v1/la-chung/requests"): {
        "body.idempotency_key": "Generated retry identifier, not a typed message.",
    },
    ("POST", "/v1/public/la-chung/{token}/responses"): {
        "body.statement_ids[]": "Identifiers selected from the fixed statement catalog.",
        "body.idempotency_key": "Generated retry identifier, not a typed message.",
    },
    ("PUT", "/v1/matching/profile"): {
        "body.region_code": "Region identifier selected from the catalog.",
    },
    ("POST", "/v1/matching/consent"): {
        "body.version": "Published consent version selected by the client.",
    },
    ("POST", "/v1/radar/private-checks"): {
        "body.birth_time_local": "Structured HH:MM time.",
        "body.place_id": "Identifier selected from birthplace search results.",
        "body.consent_version": "Published consent version selected by the client.",
    },
    ("POST", "/v1/public/radar/invite/withdraw"): {
        "body.token": "Opaque revocation capability produced by the server.",
    },
    ("POST", "/v1/public/radar/current/accept"): {
        "body.consent_version": "Published consent version selected by the client.",
    },
    ("PUT", "/v1/reading-projections/{scope_key}/aura-transition/acknowledge"): {
        "body.transition_id": "Server-produced SHA-256 transition identifier.",
    },
    ("PUT", "/v1/daily-note/{daily_note_id}/experiment"): {
        "body.action_key": "Server-produced SHA-256 action identifier.",
        "body.consent_version": "Published consent version selected by the client.",
    },
    ("PUT", "/v1/daily-note/{daily_note_id}/resonance"): {
        "body.consent_version": "Published consent version selected by the client.",
    },
    ("GET", "/v1/share-artifacts"): {
        "query.cursor": "Opaque pagination cursor returned by the server.",
    },
    ("POST", "/v1/tarot/sessions"): {
        "body.prompt_id": "Identifier selected from the fixed question catalog.",
        "body.idempotency_key": "Generated retry identifier, not a typed message.",
    },
    ("POST", "/v1/human-tarot/requests"): {
        "body.consent_version": "Published consent version selected by the client.",
        "body.idempotency_key": "Generated retry identifier, not a typed message.",
    },
    ("POST", "/v1/studio/drafts"): {
        "body.payload.*": "Operator-only Content Studio JSON editing, not a public input.",
        "body.reason": "Operator-only Content Studio revision audit reason.",
    },
    ("POST", "/v1/studio/revisions/{revision_id}/publish"): {
        "body.reason": "Operator-only Content Studio publish audit reason.",
    },
    ("POST", "/v1/studio/revisions/{revision_id}/rollback"): {
        "body.reason": "Operator-only Content Studio rollback audit reason.",
    },
}


def _text_fields(
    schema: Schema, document: Schema, path: str, seen: frozenset[str] = frozenset()
) -> Iterator[str]:
    if (
        not {"$ref", "type", "anyOf", "oneOf", "allOf", "enum", "const", "properties"}
        & schema.keys()
    ):
        # An Any/untyped JSON field can contain text, including in a newly added endpoint.
        yield f"{path}.*"
    if "$ref" in schema:
        ref: str = schema["$ref"]
        assert ref.startswith("#/components/schemas/"), f"Unknown request schema: {ref}"
        if ref not in seen:
            target = document["components"]["schemas"][ref.rsplit("/", 1)[1]]
            yield from _text_fields(target, document, path, seen | {ref})
        else:
            yield f"{path}.*"
    for keyword in ("anyOf", "oneOf", "allOf"):
        for branch in schema.get(keyword, []):
            yield from _text_fields(branch, document, path, seen)
    if (
        schema.get("type") == "string"
        and "enum" not in schema
        and "const" not in schema
        and schema.get("format") not in {"uuid", "date", "date-time", "time", "binary"}
    ):
        yield path
    for name, value in schema.get("properties", {}).items():
        yield from _text_fields(value, document, f"{path}.{name}", seen)
    if "items" in schema:
        yield from _text_fields(schema["items"], document, f"{path}[]", seen)
    additional = schema.get("additionalProperties", False)
    if additional is True or additional == {}:
        yield f"{path}.*"
    elif isinstance(additional, dict):
        yield from _text_fields(additional, document, f"{path}.*", seen)


def _guarded_fields(dependant: Any) -> set[str]:
    fields: set[str] = set()
    call = dependant.call
    if getattr(call, "__code__", None) is crisis_guard("probe").__code__:
        fields.update(
            field
            for field in inspect.getclosurevars(call).nonlocals["fields"]
            if not any(character in field for character in ".[]*")
        )
    for child in dependant.dependencies:
        fields.update(_guarded_fields(child))
    return fields


def _inventory(application: FastAPI) -> tuple[set[FieldKey], set[FieldKey]]:
    document = application.openapi()
    candidates: set[FieldKey] = set()
    guarded: set[FieldKey] = set()
    for route in iter_route_contexts(application.routes):
        if not isinstance(route.original_route, APIRoute):
            continue
        assert route.path_format is not None
        # A hidden endpoint with request fields must not silently escape this inventory.
        assert route.include_in_schema or not (route.body_field or route.dependant.query_params), (
            f"Request-bearing route hidden from safety inventory: {route.path}"
        )
        for method in route.methods or ():
            operation = document.get("paths", {}).get(route.path_format, {}).get(method.lower())
            if operation is None:
                continue
            fields: set[str] = set()
            for parameter in operation.get("parameters", []):
                if parameter["in"] == "query":
                    fields.update(
                        _text_fields(
                            parameter.get("schema", {}), document, f"query.{parameter['name']}"
                        )
                    )
            for media_type, body in operation.get("requestBody", {}).get("content", {}).items():
                prefix = "body" if media_type == "application/json" else f"body[{media_type}]"
                fields.update(_text_fields(body.get("schema", {}), document, prefix))
            candidates.update((method, route.path_format, field) for field in fields)
            guarded.update(
                (method, route.path_format, f"body.{field}")
                for field in _guarded_fields(route.dependant)
            )
    return candidates, guarded


def _assert_covered(application: FastAPI, *, exact_exceptions: bool = False) -> None:
    candidates, guarded = _inventory(application)
    exceptions = {
        (method, path, field)
        for (method, path), fields in EXCEPTIONS.items()
        for field, reason in fields.items()
        if reason.strip()
    }
    missing = candidates - guarded - exceptions
    assert not missing, (
        f"Request text needs crisis_guard or a reasoned exception: {sorted(missing)}"
    )
    if exact_exceptions:
        stale = exceptions - candidates
        assert not stale, f"Stale safety exceptions: {sorted(stale)}"
        assert not exceptions & guarded, "A guard must not silently become an exception"


@pytest.fixture
def inventory_app() -> FastAPI:
    return create_app(
        Settings(
            _env_file=None,
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            content_studio_enabled=True,
            content_studio_api_token=SecretStr("synthetic-inventory-studio-token"),
        )
    )


def test_every_request_text_field_has_a_guard_or_reasoned_exception(inventory_app: FastAPI) -> None:
    _assert_covered(inventory_app, exact_exceptions=True)


class NewInput(BaseModel):
    message: str | None = None


def test_new_optional_free_text_route_fails_until_guarded() -> None:
    application = FastAPI()

    @application.post("/synthetic/new")
    def unguarded(body: NewInput) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body.message"):
        _assert_covered(application)

    guarded_application = FastAPI()

    @guarded_application.post("/synthetic/new", dependencies=[Depends(crisis_guard("message"))])
    def guarded(body: NewInput) -> None:
        pass

    _assert_covered(guarded_application)


def test_protocol_field_name_is_not_an_exception_on_a_new_endpoint() -> None:
    application = FastAPI()

    class ProtocolLikeInput(BaseModel):
        consent_version: str

    @application.post("/synthetic/new")
    def unguarded(body: ProtocolLikeInput) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body.consent_version"):
        _assert_covered(application)


def test_nested_request_text_is_not_covered_by_a_top_level_guard() -> None:
    application = FastAPI()

    class NestedInput(BaseModel):
        messages: list[NewInput]

    @application.post("/synthetic/nested", dependencies=[Depends(crisis_guard("messages"))])
    def unguarded(body: NestedInput) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body.messages\[\].message"):
        _assert_covered(application)


def test_new_query_text_is_not_silently_excluded() -> None:
    application = FastAPI()

    @application.get("/synthetic/search")
    def unguarded(query: str) -> None:
        pass

    with pytest.raises(AssertionError, match=r"query.query"):
        _assert_covered(application)


def test_new_field_on_a_guarded_endpoint_still_needs_its_own_guard() -> None:
    application = FastAPI()

    class ExtendedInput(NewInput):
        extra_note: str

    @application.post("/synthetic/new", dependencies=[Depends(crisis_guard("message"))])
    def guarded(body: ExtendedInput) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body.extra_note"):
        _assert_covered(application)


def test_removing_a_real_endpoint_guard_is_detected(inventory_app: FastAPI) -> None:
    route = next(
        route
        for route in iter_route_contexts(inventory_app.routes)
        if route.path == "/v1/tarot/sessions" and "POST" in (route.methods or ())
    )
    route.dependant.dependencies[:] = [
        dependency
        for dependency in route.dependant.dependencies
        if "question" not in _guarded_fields(dependency)
    ]
    with pytest.raises(AssertionError, match=r"body.question"):
        _assert_covered(inventory_app)


def test_untyped_json_field_cannot_hide_new_text() -> None:
    application = FastAPI()

    class UntypedInput(BaseModel):
        note: Any

    @application.post("/synthetic/new")
    def unguarded(body: UntypedInput) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body.note"):
        _assert_covered(application)


def test_a_scalar_guard_does_not_cover_untyped_nested_text() -> None:
    application = FastAPI()

    class UntypedInput(BaseModel):
        note: Any

    @application.post("/synthetic/new", dependencies=[Depends(crisis_guard("note"))])
    def unguarded(body: UntypedInput) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body.note"):
        _assert_covered(application)


def test_dotted_guard_name_does_not_cover_a_nested_field() -> None:
    application = FastAPI()

    class NestedInput(BaseModel):
        note: NewInput

    @application.post("/synthetic/new", dependencies=[Depends(crisis_guard("note.message"))])
    def unguarded(body: NestedInput) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body.note.message"):
        _assert_covered(application)


class RecursiveInput(BaseModel):
    message: str
    children: list["RecursiveInput"] = Field(default_factory=list)


def test_recursive_request_does_not_hide_nested_text() -> None:
    application = FastAPI()

    @application.post("/synthetic/new", dependencies=[Depends(crisis_guard("message"))])
    def unguarded(body: RecursiveInput) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body.children"):
        _assert_covered(application)


def test_json_guard_is_not_credited_for_other_body_media_types() -> None:
    application = FastAPI()

    @application.post("/synthetic/new", dependencies=[Depends(crisis_guard("message"))])
    def unguarded(body: Annotated[NewInput, Body(media_type="text/plain")]) -> None:
        pass

    with pytest.raises(AssertionError, match=r"body\[text/plain\].message"):
        _assert_covered(application)
