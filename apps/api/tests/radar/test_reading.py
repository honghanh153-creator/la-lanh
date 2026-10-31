"""radar-readable-v2 (owner feedback 29/10/2026, research report Phần B)."""

import json
import re
from datetime import UTC, datetime
from typing import Any

import pytest

from app.domains.astro.engine import NatalChartEngine, summarize_synastry_dimensions
from app.domains.astro.models import (
    BodyName,
    ChartInput,
    ContactTone,
    RelationshipBundle,
    RelationshipDimension,
    SynastryContact,
)
from app.domains.radar import reading as radar
from app.domains.radar.reading import BODY_LABELS, build_radar_reading
from app.domains.relationships.models import RelationshipVoice

JARGON = (
    "chart", "contact", "radar", "mood", "flirt", "chemistry", "synastry", "composite",
    "mặt trời", "mặt trăng", "sao thủy", "sao kim", "sao hỏa", "sao mộc", "sao thổ",
    "thiên vương", "hải vương", "diêm vương", "tam hợp", "lục hợp", "đối đỉnh", "đồng vị",
    "góc vuông", "nhà ", "cung ",
)  # fmt: skip
# Never say what the absent person thinks, feels, wants or will do; no fate or success claims.
FORBIDDEN = (
    "người kia nghĩ", "người kia đang nghĩ", "người kia cảm thấy", "người kia muốn",
    "người kia sẽ", "người kia thích", "họ nghĩ", "họ đang nghĩ", "họ cảm thấy", "họ muốn",
    "họ sẽ", "họ thích", "thích bạn", "yêu bạn", "để ý bạn", "định mệnh", "soulmate",
    "tri kỷ", "chắc chắn", "red flag", "cờ đỏ", "toxic", "thử lòng", "theo dõi",
    "tỷ lệ", "tỉ lệ", "%", "/100", "mãi mãi", "sinh ra để",
)  # fmt: skip


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


def _with_contacts(*contacts: SynastryContact) -> RelationshipBundle:
    bundle = _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC))
    synastry = bundle.synastry.model_copy(update={"contacts": contacts})
    return bundle.model_copy(
        update={"synastry": synastry, "dimensions": summarize_synastry_dimensions(synastry)}
    )


def _contact(
    a: BodyName, b: BodyName, kind: str, strength: float, *dims: RelationshipDimension
) -> SynastryContact:
    angle = {"trine": 120, "sextile": 60, "square": 90, "opposition": 180, "conjunction": 0}
    tone = ContactTone.FLOW if kind in {"trine", "sextile"} else ContactTone.ACTIVATION
    return SynastryContact(
        body_a=a,
        body_b=b,
        kind=kind,
        orb=1.0,
        exact_angle=angle[kind],
        strength=strength,
        tone=tone,
        dimensions=dims or (RelationshipDimension.RELATING,),
    )


def _clustered_bundle() -> RelationshipBundle:
    return _with_contacts(
        _contact(
            BodyName.MERCURY,
            BodyName.MOON,
            "trine",
            0.92,
            RelationshipDimension.COMMUNICATION,
            RelationshipDimension.EMOTIONAL,
        ),
        _contact(
            BodyName.MOON,
            BodyName.MERCURY,
            "sextile",
            0.84,
            RelationshipDimension.EMOTIONAL,
            RelationshipDimension.COMMUNICATION,
        ),
        _contact(
            BodyName.SATURN,
            BodyName.VENUS,
            "square",
            0.94,
            RelationshipDimension.GROWTH,
            RelationshipDimension.FRICTION,
        ),
        _contact(
            BodyName.MARS,
            BodyName.VENUS,
            "opposition",
            0.80,
            RelationshipDimension.DRIVE,
            RelationshipDimension.FRICTION,
        ),
        _contact(BodyName.PLUTO, BodyName.PLUTO, "trine", 0.99),
    )


def _main(reading: dict[str, Any]) -> list[dict[str, Any]]:
    return [s for s in reading["sections"] if s["layer"] == "main"]


def _section(reading: dict[str, Any], key: str) -> dict[str, Any]:
    return next(s for s in reading["sections"] if s["key"] == key)


def _default_view(reading: dict[str, Any]) -> list[str]:
    """What the page shows before anything is opened."""

    signature = reading["pair_signature"]
    texts = [signature["tier"]["label"], signature["summary"], signature["headline"]]
    for area in signature["areas"]:
        texts += [area["label"], area["level_label"], area["note"]]
    for section in _main(reading):
        texts += [section["label"], section["title"], section["body"]]
        texts += [section.get("question") or ""]
    texts.append(reading["disclaimer"])
    return [text for text in texts if text]


def _copy_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in _copy_strings(item)]
    if isinstance(value, list | tuple):
        return [s for item in value for s in _copy_strings(item)]
    return []


def test_radar_uses_consistent_vietnamese_body_labels() -> None:
    assert BODY_LABELS[BodyName.MERCURY] == "Sao Thủy"
    assert BODY_LABELS[BodyName.VENUS] == "Sao Kim"
    assert BODY_LABELS[BodyName.MARS] == "Sao Hỏa"
    assert BODY_LABELS[BodyName.JUPITER] == "Sao Mộc"
    assert BODY_LABELS[BodyName.SATURN] == "Sao Thổ"
    assert BODY_LABELS[BodyName.URANUS] == "Thiên Vương"
    assert BODY_LABELS[BodyName.NEPTUNE] == "Hải Vương"
    assert BODY_LABELS[BodyName.PLUTO] == "Diêm Vương"


def test_reading_shows_a_named_tier_areas_and_one_more_layer() -> None:
    reading = build_radar_reading(
        _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC)), context="crush"
    )

    assert reading["version"] == "radar-result-v2"
    assert reading["metadata"]["renderer_version"] == "radar-readable-v2"
    assert reading["metadata"]["tier_calibration_version"] == "radar-tier-ref-v1"
    signature = reading["pair_signature"]
    tier = signature["tier"]
    assert tier["key"] in {key for key, _ in radar.TIER_BANDS}
    assert tier["label"] == radar.TIER_LABELS["crush"][tier["key"]]
    assert "score" not in tier  # SHOW_TIER_SCORE is off: no scalar score in the projection
    assert signature["kicker"] == tier["label"]
    assert reading["summary"] == signature["summary"]
    assert [area["key"] for area in signature["areas"]] == ["spark", "opening", "closeness"]
    assert all(area["level_label"] and area["note"] for area in signature["areas"])
    assert reading["compatibility_map"] == []
    assert reading["disclaimer"] == radar.CLOSING_LINE
    main_keys = [s["key"] for s in _main(reading)]
    assert main_keys[0] == "fit"
    assert main_keys[-1] == "check"
    assert _section(reading, "check")["question"]
    layers = {s["key"]: s["layer"] for s in reading["sections"]}
    assert layers["why"] == layers["perspective"] == "more"

    section_ids = {r["evidence_id"] for s in reading["sections"] for r in s["evidence"]}
    assert section_ids == set(reading["metadata"]["evidence_ids"])
    why = _section(reading, "why")
    disclosed = {r["evidence_id"] for r in why["evidence"]}
    assert why["factors"] and all(set(f["evidence_ids"]) <= disclosed for f in why["factors"])
    perspective_sources = {r["source"] for r in _section(reading, "perspective")["evidence"]}
    assert perspective_sources == {"house_overlay", "composite_midpoint"}


def test_headline_has_no_forced_but_and_no_hedging_kicker() -> None:
    for birth in (
        datetime(1992, 7, 21, 12, 40, tzinfo=UTC),
        datetime(1985, 11, 2, 22, 5, tzinfo=UTC),
    ):
        for context in radar.CONTEXTS:
            reading = build_radar_reading(_bundle(birth), context=context)
            assert "nhưng" not in reading["headline"].lower()
            assert reading["pair_signature"]["kicker"] in radar.TIER_LABELS[context].values()
    for table in (radar.HEADLINES, radar.TIER_LABELS):
        assert not any("nhưng" in text.lower() for text in _copy_strings(table))


def test_friction_paragraph_appears_only_above_the_threshold() -> None:
    clustered = build_radar_reading(_clustered_bundle(), context="partner")
    friction = _section(clustered, "friction")
    assert friction["layer"] == "main" and friction["evidence"]
    assert friction["body"] in _copy_strings(radar.TENSION_COPY)
    assert any(area["level"] == "watch" for area in clustered["pair_signature"]["areas"])

    calm = build_radar_reading(
        _with_contacts(
            _contact(BodyName.MERCURY, BodyName.MOON, "trine", 0.92),
            _contact(BodyName.SUN, BodyName.VENUS, "sextile", 0.7),
        ),
        context="partner",
    )
    assert "friction" not in {s["key"] for s in calm["sections"]}
    assert all(area["level"] != "watch" for area in calm["pair_signature"]["areas"])
    assert len(calm["pair_signature"]["themes"]) == 1

    # Just under the threshold: a weak square stays a "cân bằng" factor, not a paragraph.
    weak = build_radar_reading(
        _with_contacts(
            _contact(BodyName.MERCURY, BodyName.MOON, "trine", 0.92),
            _contact(BodyName.MARS, BodyName.SUN, "square", 0.5),
        ),
        context="friend",
    )
    assert "friction" not in {s["key"] for s in weak["sections"]}


def test_context_changes_tier_words_areas_and_copy_not_evidence() -> None:
    bundle = _clustered_bundle()
    readings = {context: build_radar_reading(bundle, context=context) for context in radar.CONTEXTS}

    tiers = {r["pair_signature"]["tier"]["key"] for r in readings.values()}
    assert len(tiers) == 1  # the rank is the pair's, not the context's
    assert len({r["pair_signature"]["tier"]["label"] for r in readings.values()}) >= 3
    assert (
        len({tuple(a["label"] for a in r["pair_signature"]["areas"]) for r in readings.values()})
        == 4
    )
    ids = {tuple(r["metadata"]["evidence_ids"]) for r in readings.values()}
    assert len(ids) == 1
    for left, right in (("crush", "friend"), ("friend", "partner"), ("crush", "partner")):
        a, b = readings[left], readings[right]
        assert a["headline"] != b["headline"]
        for key in ("fit", "friction", "check"):
            assert _section(a, key)["body"] != _section(b, key)["body"]


def test_voice_changes_only_the_practice_layer() -> None:
    bundle = _clustered_bundle()
    straight = build_radar_reading(bundle, context="partner", voice=RelationshipVoice.STRAIGHT_WARM)
    playful = build_radar_reading(
        bundle, context="partner", voice=RelationshipVoice.PLAYFUL_GROUNDED
    )

    assert straight["pair_signature"] == playful["pair_signature"]
    assert _main(straight) == _main(playful)
    assert straight["metadata"]["concept_ids"] == playful["metadata"]["concept_ids"]
    practice = _section(playful, "practice")
    assert practice["layer"] == "more"
    playful_prefixes = ("Mini test", "Thử bản đời thường", "Check nhẹ")
    assert all(item["body"].startswith(playful_prefixes) for item in practice["highlights"])
    assert practice["highlights"] != _section(straight, "practice")["highlights"]
    disclosed = {r["evidence_id"] for r in practice["evidence"]}
    assert all(set(item["evidence_ids"]) <= disclosed for item in practice["highlights"])
    assert playful["metadata"]["voice_label"] == "Hơi cợt, vẫn có căn"


def test_different_pair_changes_the_reading() -> None:
    first = build_radar_reading(
        _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC)), context="someone"
    )
    second = build_radar_reading(_clustered_bundle(), context="someone")
    assert (first["headline"], _section(first, "fit")["body"]) != (
        second["headline"],
        _section(second, "fit")["body"],
    )


@pytest.mark.parametrize("context", radar.CONTEXTS)
def test_default_view_is_short_plain_and_private(context: str) -> None:
    reading = build_radar_reading(
        _bundle(datetime(1992, 7, 21, 12, 40, tzinfo=UTC)), context=context
    )
    default = " ".join(_default_view(reading)).lower()
    assert len(re.findall(r"[^\W_]+", default)) <= 400
    assert not [term for term in JARGON if term in default]
    serialized = json.dumps(reading, ensure_ascii=False).lower()
    for raw in ("1990", "1992", "21.0285", "106.6297"):
        assert raw not in serialized


def test_copy_tables_never_read_minds_or_claim_fate() -> None:
    tables = (
        radar.TIER_LABELS,
        radar.TIER_REASONS,
        radar.HEADLINES,
        radar.FIT_COPY,
        radar.TENSION_COPY,
        radar.SUGGESTIONS,
        radar.LOW_SIGNAL_SUGGESTIONS,
        radar.FACTOR_COPY,
        radar.LOW_SIGNAL_COPY,
        radar.CLOSING_LINE,
    )
    for text in _copy_strings(tables):
        low = text.lower()
        assert not [term for term in FORBIDDEN if term in low], text
        assert not [term for term in JARGON if term in low], text


def test_no_sentence_is_written_in_two_copy_cells() -> None:
    """Each sentence has one home, so a reading never says the same thing twice."""

    homes: dict[str, set[tuple[str, ...]]] = {}

    def walk(value: object, path: tuple[str, ...]) -> None:
        if isinstance(value, str):
            for part in re.split(r"(?<=[.!?])\s+", value):
                if len(part.split()) >= 4:
                    homes.setdefault(part.strip().lower(), set()).add(path)
        elif isinstance(value, dict):
            for key, item in value.items():
                walk(item, (*path, str(key)))
        elif isinstance(value, list | tuple):
            for index, item in enumerate(value):
                walk(item, (*path, str(index)))

    for name in (
        "TIER_REASONS",
        "HEADLINES",
        "FIT_COPY",
        "TENSION_COPY",
        "SUGGESTIONS",
        "LOW_SIGNAL_SUGGESTIONS",
        "FACTOR_COPY",
        "LOW_SIGNAL_COPY",
        "CLOSING_LINE",
    ):
        walk(getattr(radar, name), (name,))
    assert not {text: paths for text, paths in homes.items() if len(paths) > 1}


def test_every_theme_and_context_has_copy() -> None:
    themes = set(radar.THEME_PLAIN)
    for table in (radar.HEADLINES, radar.FIT_COPY, radar.TENSION_COPY, radar.SUGGESTIONS):
        assert set(table) == themes
        assert all(set(row) == set(radar.CONTEXTS) for row in table.values())
    assert set(radar.FACTOR_COPY) == themes
    for context in radar.CONTEXTS:
        covered = [theme for _, _, group in radar.AREAS[context] for theme in group]
        assert sorted(covered) == sorted(themes)  # each theme in exactly one area
        assert set(radar.TIER_LABELS[context]) == {key for key, _ in radar.TIER_BANDS} | {"unclear"}


def test_rank_percentile_is_monotone_and_bands_split_as_documented() -> None:
    reference = radar.TIER_REFERENCE
    assert list(reference) == sorted(reference)
    grid = [reference[0] - 0.1 + i * 0.001 for i in range(1100)]
    ranks = [radar.rank_percentile(value) for value in grid]
    assert ranks == sorted(ranks) and ranks[0] == 0.0 and ranks[-1] == 100.0
    assert radar.rank_percentile(reference[10]) == pytest.approx(50.0)
    assert [radar.tier_for(p) for p in (99, 85, 84.9, 60, 30, 10, 9.9, 0)] == [
        "very_easy",
        "very_easy",
        "easy",
        "easy",
        "complementary",
        "warming_up",
        "patient",
        "patient",
    ]


def test_owner_switch_adds_a_rank_number_only_when_turned_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _clustered_bundle()
    assert "score" not in build_radar_reading(bundle, context="friend")["pair_signature"]["tier"]
    monkeypatch.setattr(radar, "SHOW_TIER_SCORE", True)
    score = build_radar_reading(bundle, context="friend")["pair_signature"]["tier"]["score"]
    assert isinstance(score, int) and 0 <= score <= 100


def test_zero_eligible_contacts_returns_an_honest_low_signal_report() -> None:
    sparse = _with_contacts(_contact(BodyName.PLUTO, BodyName.NEPTUNE, "trine", 0.95))

    reading = build_radar_reading(sparse, context="someone")

    assert reading["version"] == "radar-result-v2"
    assert reading["pair_signature"]["tier"]["key"] == "unclear"
    assert all(area["level"] == "quiet" for area in reading["pair_signature"]["areas"])
    assert "friction" not in {s["key"] for s in reading["sections"]}
    assert _section(reading, "why")["factors"] == []
    assert reading["summary"] == radar.LOW_SIGNAL_COPY["summary"]
    assert reading["disclaimer"] == radar.CLOSING_LINE
