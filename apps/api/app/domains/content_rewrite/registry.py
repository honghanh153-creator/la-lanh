from __future__ import annotations

from collections.abc import Iterable

from app.domains.content_rewrite.models import (
    RewriteFieldSpec,
    RewriteRequestEnvelope,
    RewriteSurface,
    RewriteSurfaceSpec,
)

CANONICAL_REWRITE_SURFACES = frozenset(RewriteSurface)


class SurfaceRegistry:
    def __init__(self, specs: Iterable[RewriteSurfaceSpec]) -> None:
        by_surface: dict[RewriteSurface, RewriteSurfaceSpec] = {}
        for spec in specs:
            if spec.surface in by_surface:
                raise ValueError(f"duplicate rewrite surface: {spec.surface.value}")
            by_surface[spec.surface] = spec
        self._by_surface = by_surface

    @property
    def surfaces(self) -> frozenset[RewriteSurface]:
        return frozenset(self._by_surface)

    def require(self, surface: RewriteSurface) -> RewriteSurfaceSpec:
        try:
            return self._by_surface[surface]
        except KeyError as error:
            raise LookupError(f"rewrite surface is not registered: {surface.value}") from error

    def validate_request(self, envelope: RewriteRequestEnvelope) -> None:
        spec = self.require(envelope.key.surface)
        if envelope.key.schema_version != spec.schema_version:
            raise ValueError("rewrite request schema version does not match the surface contract")
        if envelope.key.gate_version != spec.gate_version:
            raise ValueError("rewrite request gate version does not match the surface contract")
        if envelope.key.owner.namespace != spec.fallback_owner:
            raise ValueError("rewrite request owner does not match the surface contract")

    def assert_complete(self) -> None:
        missing = CANONICAL_REWRITE_SURFACES.difference(self.surfaces)
        extra = self.surfaces.difference(CANONICAL_REWRITE_SURFACES)
        if missing or extra:
            names = ", ".join(sorted(surface.value for surface in missing | extra))
            raise ValueError(f"canonical rewrite registry is incomplete: {names}")


def _fields(*names: str) -> tuple[RewriteFieldSpec, ...]:
    return tuple(RewriteFieldSpec(name=name) for name in names)


def canonical_surface_registry() -> SurfaceRegistry:
    specs = (
        RewriteSurfaceSpec(
            surface=RewriteSurface.DAILY_HOME,
            fallback_owner="readings",
            schema_version="daily-rewrite/v1",
            gate_version="daily-rewrite-gates/v1",
            fields=_fields("title", "scene", "action"),
            word_budget=70,
            forbidden_claims=("prediction", "diagnosis", "decision_instruction"),
        ),
        RewriteSurfaceSpec(
            surface=RewriteSurface.DAILY_DETAIL,
            fallback_owner="readings",
            schema_version="daily-detail-rewrite/v1",
            gate_version="reading-detail-rewrite-gates/v1",
            fields=_fields("hook", "explanation", "manifestation", "bounded_action"),
            word_budget=240,
            forbidden_claims=("prediction", "diagnosis"),
        ),
        RewriteSurfaceSpec(
            surface=RewriteSurface.REVEAL,
            fallback_owner="readings",
            schema_version="reveal-rewrite/v1",
            gate_version="natal-rewrite-gates/v1",
            fields=_fields("headline", "synthesis", "section_intros", "examples"),
            word_budget=500,
            forbidden_claims=("single_placement_identity", "prediction"),
        ),
        RewriteSurfaceSpec(
            surface=RewriteSurface.NATAL,
            fallback_owner="readings",
            schema_version="natal-rewrite/v1",
            gate_version="natal-rewrite-gates/v1",
            fields=_fields("headline", "synthesis", "section_intros", "examples"),
            word_budget=900,
            forbidden_claims=("single_placement_identity", "prediction"),
        ),
        *(
            RewriteSurfaceSpec(
                surface=surface,
                fallback_owner="readings",
                schema_version=f"{surface.value}-rewrite/v1",
                gate_version="insight-rewrite-gates/v1",
                fields=_fields("hook", "explanation", "everyday_example", "bounded_action"),
                word_budget=420,
                forbidden_claims=("identity_label", "prediction"),
            )
            for surface in (
                RewriteSurface.PLANET_INSIGHT,
                RewriteSurface.HOUSE_INSIGHT,
                RewriteSurface.ASPECT_INSIGHT,
                RewriteSurface.TRANSIT_INSIGHT,
            )
        ),
        RewriteSurfaceSpec(
            surface=RewriteSurface.RADAR,
            fallback_owner="radar",
            schema_version="radar-rewrite/v1",
            gate_version="relationship-rewrite-gates/v1",
            fields=_fields("overview", "strengths", "frictions", "asymmetry", "prompt"),
            word_budget=900,
            forbidden_claims=("success_probability", "soulmate", "manipulation"),
        ),
        RewriteSurfaceSpec(
            surface=RewriteSurface.MATCHING,
            fallback_owner="matching",
            schema_version="matching-rewrite/v1",
            gate_version="relationship-rewrite-gates/v1",
            fields=_fields("card_summary", "strengths", "frictions", "icebreaker"),
            word_budget=420,
            forbidden_claims=("success_probability", "soulmate", "manipulation"),
        ),
        RewriteSurfaceSpec(
            surface=RewriteSurface.TAROT,
            fallback_owner="tarot",
            schema_version="tarot-rewrite/v1",
            gate_version="tarot-rewrite-gates/v1",
            fields=_fields("headline", "position_readings", "synthesis", "closing_question"),
            word_budget=800,
            forbidden_claims=("prediction", "professional_advice", "urgency"),
        ),
        RewriteSurfaceSpec(
            surface=RewriteSurface.SHARE_CARD,
            fallback_owner="share",
            schema_version="share-card-rewrite/v1",
            gate_version="share-rewrite-gates/v1",
            fields=_fields("headline", "summary"),
            word_budget=90,
            forbidden_claims=("private_context", "hidden_evidence"),
        ),
        RewriteSurfaceSpec(
            surface=RewriteSurface.RECAP,
            fallback_owner="share",
            schema_version="recap-rewrite/v1",
            gate_version="share-rewrite-gates/v1",
            fields=_fields("headline", "summary"),
            word_budget=180,
            forbidden_claims=("invented_activity", "private_context"),
        ),
    )
    registry = SurfaceRegistry(specs)
    registry.assert_complete()
    return registry
