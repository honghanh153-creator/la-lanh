import json
from datetime import UTC, datetime

from app.domains.astro.engine import NatalChartEngine, summarize_synastry_dimensions
from app.domains.astro.models import (
    BodyName,
    ChartInput,
    ContactTone,
    RelationshipBundle,
    RelationshipDimension,
    SynastryContact,
)
from app.domains.radar.reading import BODY_LABELS, build_radar_reading
from app.domains.relationships.models import RelationshipVoice


def _bundle(second_birth: datetime) -> RelationshipBundle:
    engine = NatalChartEngine()
    first = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 5, 15, tzinfo=UTC),
            latitude=21.0285,
            longitude=105.8542,
        )
    )
    second = engine.calculate_chart(
        ChartInput(
            utc_datetime=second_birth,
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    return engine.calculate_relationship_bundle(first, second)


def _clustered_bundle() -> RelationshipBundle:
    bundle = _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC))
    contacts = (
        SynastryContact(
            body_a=BodyName.MERCURY,
            body_b=BodyName.MOON,
            kind="trine",
            orb=0.8,
            exact_angle=120,
            strength=0.92,
            tone=ContactTone.FLOW,
            dimensions=(RelationshipDimension.COMMUNICATION, RelationshipDimension.EMOTIONAL),
        ),
        SynastryContact(
            body_a=BodyName.MOON,
            body_b=BodyName.MERCURY,
            kind="sextile",
            orb=1.1,
            exact_angle=60,
            strength=0.84,
            tone=ContactTone.FLOW,
            dimensions=(RelationshipDimension.EMOTIONAL, RelationshipDimension.COMMUNICATION),
        ),
        SynastryContact(
            body_a=BodyName.SATURN,
            body_b=BodyName.MERCURY,
            kind="square",
            orb=0.6,
            exact_angle=90,
            strength=0.94,
            tone=ContactTone.ACTIVATION,
            dimensions=(
                RelationshipDimension.COMMUNICATION,
                RelationshipDimension.GROWTH,
                RelationshipDimension.FRICTION,
            ),
        ),
        SynastryContact(
            body_a=BodyName.MARS,
            body_b=BodyName.VENUS,
            kind="opposition",
            orb=1.4,
            exact_angle=180,
            strength=0.80,
            tone=ContactTone.ACTIVATION,
            dimensions=(
                RelationshipDimension.DRIVE,
                RelationshipDimension.RELATING,
                RelationshipDimension.FRICTION,
            ),
        ),
        SynastryContact(
            body_a=BodyName.PLUTO,
            body_b=BodyName.PLUTO,
            kind="trine",
            orb=0.1,
            exact_angle=120,
            strength=0.99,
            tone=ContactTone.FLOW,
            dimensions=(RelationshipDimension.RELATING,),
        ),
    )
    synastry = bundle.synastry.model_copy(update={"contacts": contacts})
    return bundle.model_copy(
        update={"synastry": synastry, "dimensions": summarize_synastry_dimensions(synastry)}
    )


def _visible_strings(reading: dict[str, object]) -> list[str]:
    values: list[str] = []
    for key in ("headline", "summary", "disclaimer"):
        value = reading.get(key)
        if isinstance(value, str):
            values.append(value)
    signature = reading.get("pair_signature")
    if isinstance(signature, dict):
        values.extend(value for value in signature.values() if isinstance(value, str))
    compatibility_map = reading.get("compatibility_map")
    if isinstance(compatibility_map, list):
        for item in compatibility_map:
            if isinstance(item, dict):
                values.extend(
                    value
                    for key, value in item.items()
                    if key != "evidence" and isinstance(value, str)
                )
    sections = reading.get("sections")
    if not isinstance(sections, list):
        return values
    for section in sections:
        if not isinstance(section, dict):
            continue
        for key in ("label", "title", "body"):
            value = section.get(key)
            if isinstance(value, str):
                values.append(value)
        topics = section.get("topics")
        if isinstance(topics, list):
            values.extend(value for value in topics if isinstance(value, str))
        for nested_key in ("highlights", "perspectives"):
            nested_values = section.get(nested_key)
            if not isinstance(nested_values, list):
                continue
            for nested in nested_values:
                if isinstance(nested, dict):
                    values.extend(value for value in nested.values() if isinstance(value, str))
        for nested_key in ("scene", "observation"):
            nested = section.get(nested_key)
            if isinstance(nested, dict):
                values.extend(value for value in nested.values() if isinstance(value, str))
    return values


def test_radar_uses_consistent_vietnamese_body_labels() -> None:
    assert BODY_LABELS[BodyName.MERCURY] == "Sao Thủy"
    assert BODY_LABELS[BodyName.VENUS] == "Sao Kim"
    assert BODY_LABELS[BodyName.MARS] == "Sao Hỏa"
    assert BODY_LABELS[BodyName.JUPITER] == "Sao Mộc"
    assert BODY_LABELS[BodyName.SATURN] == "Sao Thổ"
    assert BODY_LABELS[BodyName.URANUS] == "Thiên Vương"
    assert BODY_LABELS[BodyName.NEPTUNE] == "Hải Vương"
    assert BODY_LABELS[BodyName.PLUTO] == "Diêm Vương"


def test_reading_exposes_pair_signature_three_independent_indices_and_receipts() -> None:
    reading = build_radar_reading(
        _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC)), context="crush"
    )

    assert reading["version"] == "radar-result-v2"
    assert set(reading["pair_signature"]) == {"kicker", "headline", "summary", "themes"}
    assert [item["key"] for item in reading["compatibility_map"]] == [
        "resonance",
        "coordination",
        "friction",
    ]
    assert all(0 <= item["value"] <= 100 for item in reading["compatibility_map"])
    assert [item["key"] for item in reading["sections"]] == [
        "fit",
        "friction",
        "perspective",
        "check",
    ]
    assert all(item["evidence"] for item in reading["sections"][:3])
    assert all(
        receipt["evidence_id"] for item in reading["sections"] for receipt in item["evidence"]
    )
    perspective_sources = {receipt["source"] for receipt in reading["sections"][2]["evidence"]}
    assert perspective_sources == {"house_overlay", "composite_midpoint"}
    section_evidence_ids = {
        receipt["evidence_id"] for item in reading["sections"] for receipt in item["evidence"]
    }
    indicator_evidence_ids = {
        receipt["evidence_id"]
        for item in reading["compatibility_map"]
        for receipt in item["evidence"]
    }
    assert section_evidence_ids | indicator_evidence_ids == set(reading["metadata"]["evidence_ids"])
    assert "tổng" not in " ".join(item["meaning"] for item in reading["compatibility_map"])


def test_dossier_clusters_related_contacts_and_exposes_layered_chapters() -> None:
    reading = build_radar_reading(_clustered_bundle(), context="crush")

    fit, friction, perspective, check = reading["sections"]

    assert fit["depth"] == "layered"
    assert len(fit["evidence"]) >= 2
    assert len(fit["highlights"]) >= 2
    assert fit["scene"]["title"]
    assert all(item["evidence_ids"] for item in fit["highlights"])
    assert friction["highlights"]
    assert friction["scene"]["body"]
    assert {item["key"] for item in perspective["perspectives"]} >= {"you", "them"}
    assert check["observation"]["body"]
    assert reading["pair_signature"]["themes"]
    assert all(
        section["body"] != highlight["body"]
        for section in reading["sections"]
        for highlight in section["highlights"]
    )
    assert not any("pluto:trine:pluto" in item for item in reading["metadata"]["evidence_ids"])
    main_copy = " ".join(
        [
            *(section["body"] for section in reading["sections"]),
            *(
                highlight["body"]
                for section in reading["sections"]
                for highlight in section["highlights"]
            ),
        ]
    )
    assert "contact" not in main_copy
    assert "Trong chart chung" not in main_copy

    section_evidence_ids = {
        evidence_id
        for section in reading["sections"]
        for evidence_id in (receipt["evidence_id"] for receipt in section["evidence"])
    }
    indicator_evidence_ids = {
        receipt["evidence_id"]
        for item in reading["compatibility_map"]
        for receipt in item["evidence"]
    }
    assert section_evidence_ids | indicator_evidence_ids == set(reading["metadata"]["evidence_ids"])
    for section in reading["sections"]:
        disclosed = {receipt["evidence_id"] for receipt in section["evidence"]}
        for highlight in section["highlights"]:
            assert set(highlight["evidence_ids"]) <= disclosed
    for indicator in reading["compatibility_map"]:
        assert indicator["evidence"]
        assert {receipt["evidence_id"] for receipt in indicator["evidence"]} <= set(
            reading["metadata"]["evidence_ids"]
        )


def test_radar_publishes_evidence_bound_editorial_actions() -> None:
    reading = build_radar_reading(
        _clustered_bundle(),
        context="crush",
        voice=RelationshipVoice.PLAYFUL_GROUNDED,
    )

    check = reading["sections"][-1]
    actions = check["highlights"]

    assert actions
    assert reading["metadata"]["voice"] == "playful_grounded"
    assert reading["metadata"]["voice_label"] == "Hơi cợt, vẫn có căn"
    assert reading["metadata"]["concept_ids"] == [item["concept_id"] for item in actions]
    disclosed = {receipt["evidence_id"] for receipt in check["evidence"]}
    assert all(set(item["evidence_ids"]) <= disclosed for item in actions)
    assert actions[0]["body"].startswith("Mini test")
    assert len({item["body"].split(":", 1)[0] for item in actions}) == len(actions)


def test_voice_changes_delivery_without_changing_chart_claims() -> None:
    bundle = _clustered_bundle()
    straight = build_radar_reading(
        bundle,
        context="partner",
        voice=RelationshipVoice.STRAIGHT_WARM,
    )
    gentle = build_radar_reading(
        bundle,
        context="partner",
        voice=RelationshipVoice.GENTLE_SPECIFIC,
    )

    assert straight["pair_signature"] == gentle["pair_signature"]
    assert straight["compatibility_map"] == gentle["compatibility_map"]
    assert straight["metadata"]["evidence_ids"] == gentle["metadata"]["evidence_ids"]
    assert straight["metadata"]["concept_ids"] == gentle["metadata"]["concept_ids"]
    assert straight["sections"][-1]["highlights"] != gentle["sections"][-1]["highlights"]


def test_context_changes_scenario_not_chart_evidence_or_indices() -> None:
    bundle = _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC))

    crush = build_radar_reading(bundle, context="crush")
    friend = build_radar_reading(bundle, context="friend")

    assert crush["compatibility_map"] == friend["compatibility_map"]
    assert crush["pair_signature"] == friend["pair_signature"]
    assert crush["metadata"]["evidence_ids"] == friend["metadata"]["evidence_ids"]
    assert crush["sections"][-1]["body"] != friend["sections"][-1]["body"]
    assert (
        crush["sections"][-1]["observation"]["body"]
        != friend["sections"][-1]["observation"]["body"]
    )


def test_different_pair_changes_thesis_and_multiple_sections() -> None:
    first = build_radar_reading(
        _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC)), context="someone"
    )
    second = build_radar_reading(
        _bundle(datetime(1985, 11, 2, 22, 5, tzinfo=UTC)), context="someone"
    )

    assert first["headline"] != second["headline"]
    changed_sections = sum(
        left["body"] != right["body"]
        for left, right in zip(first["sections"], second["sections"], strict=True)
    )
    assert changed_sections >= 2


def test_public_copy_is_short_conditional_and_contains_no_raw_birth_data() -> None:
    reading = build_radar_reading(
        _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC)), context="partner"
    )
    public_text = " ".join(_visible_strings(reading)).lower()

    serialized = json.dumps(reading, ensure_ascii=False).lower()

    assert len(public_text.split()) < 1_700
    assert "1990" not in serialized
    assert "1992" not in serialized
    assert "21.0285" not in serialized
    assert "soulmate" not in serialized
    assert "red flag" not in serialized
    assert "chắc chắn" not in serialized


def test_sparse_single_cluster_does_not_invent_a_distinct_tension() -> None:
    bundle = _clustered_bundle()
    one_contact = (
        SynastryContact(
            body_a=BodyName.MERCURY,
            body_b=BodyName.MOON,
            kind="trine",
            orb=0.8,
            exact_angle=120,
            strength=0.92,
            tone=ContactTone.FLOW,
            dimensions=(RelationshipDimension.COMMUNICATION, RelationshipDimension.EMOTIONAL),
        ),
    )
    sparse = bundle.model_copy(
        update={"synastry": bundle.synastry.model_copy(update={"contacts": one_contact})}
    )

    reading = build_radar_reading(sparse, context="friend")

    assert reading["sections"][0]["evidence"]
    assert reading["sections"][1]["evidence"] == []
    assert reading["sections"][1]["highlights"] == []
    assert "chưa đủ rõ" in reading["pair_signature"]["headline"].lower()
    assert len(reading["pair_signature"]["themes"]) == 1


def test_zero_eligible_contacts_returns_an_honest_low_signal_report() -> None:
    bundle = _clustered_bundle()
    generational_only = (
        SynastryContact(
            body_a=BodyName.PLUTO,
            body_b=BodyName.NEPTUNE,
            kind="trine",
            orb=0.2,
            exact_angle=120,
            strength=0.95,
            tone=ContactTone.FLOW,
        ),
    )
    sparse = bundle.model_copy(
        update={"synastry": bundle.synastry.model_copy(update={"contacts": generational_only})}
    )

    reading = build_radar_reading(sparse, context="someone")

    assert reading["version"] == "radar-result-v2"
    assert all(item["value"] == 0 for item in reading["compatibility_map"])
    assert reading["sections"][0]["highlights"] == []
    assert "dữ liệu phù hợp còn mỏng" in reading["summary"]
