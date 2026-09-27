from app.domains.astro.models import RelationshipDimension, RelationshipDimensionEvidence
from app.domains.relationships.knowledge import (
    BOOK_SOURCES,
    EDITORIAL_CONCEPTS,
    PUBLISHABLE_PROMPT_CONCEPT_IDS,
    RELATIONSHIP_KNOWLEDGE_VERSION,
    VOICE_PROFILES,
    build_editorial_plan,
    concepts_for_dimension,
    voice_profile,
)
from app.domains.relationships.models import RelationshipVoice


def test_relationship_corpus_has_ten_unique_traceable_sources() -> None:
    assert RELATIONSHIP_KNOWLEDGE_VERSION
    assert len(BOOK_SOURCES) == 10
    assert len({source.source_id for source in BOOK_SOURCES}) == 10
    assert all(source.official_url.startswith("https://") for source in BOOK_SOURCES)


def test_every_source_carries_non_diagnostic_product_boundaries() -> None:
    for source in BOOK_SOURCES:
        prohibited = " ".join(source.prohibited_uses).lower()
        assert "diagnose" in prohibited
        assert "rank" in prohibited
        assert source.allowed_uses
        assert source.concept_ids
        assert "excerpt" not in type(source).model_fields


def test_editorial_concepts_are_conditional_prompts_not_verdicts() -> None:
    assert EDITORIAL_CONCEPTS
    assert concepts_for_dimension(RelationshipDimension.COMMUNICATION)
    for concept in EDITORIAL_CONCEPTS:
        assert concept.prompt_pattern
        assert concept.safety_boundary
        assert concept.source_ids
        assert "%" not in concept.prompt_pattern


def test_every_registered_book_concept_has_a_traceable_editorial_rule() -> None:
    source_ids = {source.source_id for source in BOOK_SOURCES}
    expected_concepts = {concept_id for source in BOOK_SOURCES for concept_id in source.concept_ids}
    actual_concepts = {concept.concept_id for concept in EDITORIAL_CONCEPTS}

    assert actual_concepts == expected_concepts
    assert all(set(concept.source_ids) <= source_ids for concept in EDITORIAL_CONCEPTS)
    assert all(concepts_for_dimension(dimension) for dimension in RelationshipDimension)


def test_voice_profiles_are_explicit_choices_not_chart_inference() -> None:
    assert {profile.voice for profile in VOICE_PROFILES} == set(RelationshipVoice)
    for choice in RelationshipVoice:
        profile = voice_profile(choice)
        assert profile.voice is choice
        assert 0 <= profile.slang_budget <= 1
        assert profile.required_moves
        assert profile.prohibited_moves


def test_editorial_plan_is_deterministic_diverse_and_evidence_bound() -> None:
    evidence = tuple(
        RelationshipDimensionEvidence(
            dimension=dimension,
            contact_count=index + 1,
            evidence_ids=(f"synastry:{dimension.value}:one", f"synastry:{dimension.value}:two"),
            strongest_strength=1 - index * 0.05,
        )
        for index, dimension in enumerate(RelationshipDimension)
    )

    first = build_editorial_plan(evidence, voice=RelationshipVoice.PLAYFUL_GROUNDED, limit=3)
    replay = build_editorial_plan(evidence, voice=RelationshipVoice.PLAYFUL_GROUNDED, limit=3)

    assert first == replay
    assert len(first.prompts) == 3
    assert len({prompt.dimension for prompt in first.prompts}) == 3
    assert len({prompt.concept_id for prompt in first.prompts}) == 3
    assert all(prompt.evidence_ids for prompt in first.prompts)
    assert all(prompt.concept_id in PUBLISHABLE_PROMPT_CONCEPT_IDS for prompt in first.prompts)
    assert first.voice_profile.voice is RelationshipVoice.PLAYFUL_GROUNDED
    assert "không phải kết luận" in first.disclaimer


def test_editorial_plan_rejects_empty_evidence_and_unbounded_length() -> None:
    try:
        build_editorial_plan((), limit=1)
    except ValueError as error:
        assert "inspectable evidence" in str(error)
    else:
        raise AssertionError("empty relationship evidence must fail closed")

    for invalid_limit in (0, 4):
        try:
            build_editorial_plan(
                (
                    RelationshipDimensionEvidence(
                        dimension=RelationshipDimension.COMMUNICATION,
                        contact_count=1,
                        evidence_ids=("synastry:mercury:moon",),
                        strongest_strength=0.8,
                    ),
                ),
                limit=invalid_limit,
            )
        except ValueError as error:
            assert "between 1 and 3" in str(error)
        else:
            raise AssertionError("invalid relationship editorial limit must fail closed")
