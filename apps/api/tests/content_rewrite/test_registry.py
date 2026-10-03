from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    ContentClassification,
    RewriteArtifactKey,
    RewriteFieldSpec,
    RewriteRequestEnvelope,
    RewriteSurface,
    RewriteSurfaceSpec,
)
from app.domains.content_rewrite.registry import (
    CANONICAL_REWRITE_SURFACES,
    SurfaceRegistry,
    canonical_surface_registry,
)


def test_canonical_registry_covers_every_personalised_surface() -> None:
    registry = canonical_surface_registry()

    assert registry.surfaces == CANONICAL_REWRITE_SURFACES
    assert registry.require(RewriteSurface.DAILY_HOME).fallback_owner == "readings"
    assert registry.require(RewriteSurface.TAROT).rewritable_fields == (
        "headline",
        "position_readings",
        "synthesis",
        "closing_question",
    )


def test_registry_rejects_duplicate_surface_ownership() -> None:
    spec = canonical_surface_registry().require(RewriteSurface.DAILY_HOME)

    with pytest.raises(ValueError, match="duplicate rewrite surface"):
        SurfaceRegistry((spec, spec))


def test_surface_rejects_duplicate_field_ownership() -> None:
    field = RewriteFieldSpec(name="headline")

    with pytest.raises(ValidationError, match="field ownership must be unique"):
        RewriteSurfaceSpec(
            surface=RewriteSurface.DAILY_HOME,
            fallback_owner="readings",
            schema_version="daily-rewrite/v1",
            gate_version="daily-rewrite-gates/v1",
            fields=(field, field),
            word_budget=70,
        )


@pytest.mark.parametrize(
    "classification",
    (
        ContentClassification.STATIC,
        ContentClassification.LEGAL,
        ContentClassification.TRANSACTIONAL,
        ContentClassification.SECURITY,
    ),
)
def test_non_interpretive_copy_cannot_be_registered(
    classification: ContentClassification,
) -> None:
    with pytest.raises(ValidationError, match="personalised interpretive"):
        RewriteSurfaceSpec(
            surface=RewriteSurface.DAILY_HOME,
            fallback_owner="readings",
            schema_version="daily-rewrite/v1",
            gate_version="daily-rewrite-gates/v1",
            fields=(RewriteFieldSpec(name="consent", classification=classification),),
            word_budget=70,
        )


def test_request_envelope_must_match_registered_contract_version() -> None:
    registry = canonical_surface_registry()
    artifact_key = RewriteArtifactKey(
        surface=RewriteSurface.DAILY_HOME,
        owner=ArtifactOwnerKey(namespace="readings", key=str(uuid4())),
        blueprint_hash="a" * 64,
        model_version="gpt-6-luna",
        prompt_version="daily-v1",
        schema_version="wrong-version/v1",
        gate_version="daily-rewrite-gates/v1",
    )
    envelope = RewriteRequestEnvelope(
        key=artifact_key,
        authorization_receipt_id=str(uuid4()),
        safe_payload={"scene_key": "psychology:work:overload"},
    )

    with pytest.raises(ValueError, match="schema version"):
        registry.validate_request(envelope)


def test_artifact_key_changes_only_when_variant_or_version_changes() -> None:
    owner = ArtifactOwnerKey(namespace="tarot", key=str(uuid4()))
    base = RewriteArtifactKey(
        surface=RewriteSurface.TAROT,
        owner=owner,
        blueprint_hash="b" * 64,
        model_version="gpt-6-luna",
        prompt_version="tarot-v1",
        schema_version="tarot-rewrite/v1",
        gate_version="tarot-rewrite-gates/v1",
    )

    assert base.cache_key == base.model_copy().cache_key
    assert base.cache_key != base.model_copy(update={"candidate_variant": "editorial-2"}).cache_key
