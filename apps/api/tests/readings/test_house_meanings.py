"""C3a-1 / N-1: the twelve houses as sourced sets of meanings, and the four reader personas."""

import importlib
import re
import unicodedata
from types import ModuleType

import pytest

from app.domains.readings.house_meanings import (
    HOUSE_MEANINGS,
    LEAD_SOURCES,
    MeaningSource,
    SourcedMeaning,
    display_order,
    meaning_by_key,
)
from app.domains.readings.reader_personas import READER_PERSONAS, AgeBand

ALL_MEANINGS = tuple(m for meanings in HOUSE_MEANINGS.values() for m in meanings)
DAILY_MEANINGS = tuple(m for m in ALL_MEANINGS if m.daily_allowed)
HOUSES = range(1, 13)

# Words that belong to the evidence layer ("Vì sao Lá đọc vậy?"), never to the plain text.
_SIGNS = (
    "bạch dương|kim ngưu|song tử|cự giải|sư tử|xử nữ|thiên bình|bọ cạp|thiên yết|hổ cáp"
    "|nhân mã|ma kết|bảo bình|song ngư"
)
_PLANETS = (
    "mặt trời|mặt trăng|sao thủy|sao kim|sao hỏa|sao mộc|sao thổ|thiên vương|hải vương"
    "|diêm vương|chiron|la hầu|kế đô"
)
_ASPECTS = "góc chiếu|góc vuông|vuông góc|lục hợp|tam hợp|đối đỉnh|giao hội|xung chiếu|trùng tụ"
FORBIDDEN = re.compile(
    rf"\bnhà \d|\bnhà thứ\b|\bcung\b|\bchủ tinh\b|\bmọc\b|\bthiên đỉnh\b|\bđầu nhà\b"
    rf"|\bnghịch hành\b|\btransit\b|\bdasha\b|\b(?:{_SIGNS}|{_PLANETS}|{_ASPECTS})\b",
    re.IGNORECASE,
)
# Synthetic-data guard: no dates of any shape in persona or meaning text.
DATE_LIKE = re.compile(r"\d{1,4}[-/.]\d{1,2}(?:[-/.]\d{1,4})?|\b(?:19|20)\d{2}\b")


def _words(text: str) -> list[str]:
    return [token for token in text.split() if re.search(r"\w", token)]


def test_every_house_is_present_with_four_to_eight_meanings() -> None:
    assert sorted(HOUSE_MEANINGS) == list(HOUSES)
    for house, meanings in HOUSE_MEANINGS.items():
        assert 4 <= len(meanings) <= 8, house
        assert all(isinstance(m, SourcedMeaning) for m in meanings)


def test_houses_are_distinct_sets() -> None:
    sets = [frozenset(m.key for m in meanings) for meanings in HOUSE_MEANINGS.values()]
    assert len(set(sets)) == 12
    texts = [m.text for m in ALL_MEANINGS]
    assert len(texts) == len(set(texts)), "a meaning text appears twice"


def test_keys_are_unique_ascii_slugs() -> None:
    keys = [m.key for m in ALL_MEANINGS]
    assert len(keys) == len(set(keys))
    for key in keys:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", key), key


def test_every_meaning_has_a_source() -> None:
    for meaning in ALL_MEANINGS:
        assert isinstance(meaning.source, MeaningSource), meaning.key
    assert {m.source for m in ALL_MEANINGS} == set(MeaningSource)


def test_meaning_texts_are_short_plain_vietnamese() -> None:
    for meaning in ALL_MEANINGS:
        text = meaning.text
        assert text == text.strip() and text, meaning.key
        assert unicodedata.normalize("NFC", text) == text, meaning.key
        assert 1 <= len(_words(text)) <= 6, (meaning.key, text)
        assert not re.search(r"\d", text), meaning.key
        assert not text.endswith((".", "!", "?")), meaning.key


def test_no_house_sign_planet_or_aspect_words_in_texts() -> None:
    for meaning in ALL_MEANINGS:
        assert not FORBIDDEN.search(meaning.text), (meaning.key, meaning.text)
    assert not any("học trò" in m.text for m in ALL_MEANINGS), "no source for 'học trò'"


def test_never_in_daily_topics_are_flagged() -> None:
    never_daily = {m.key for m in ALL_MEANINGS if not m.daily_allowed}
    assert never_daily >= {
        "illness",
        "lawsuits",
        "death_loss",
        "longevity",
        "legacy",
        "confinement",
        "hospital",
    }
    for meaning in ALL_MEANINGS:
        if not meaning.daily_allowed:
            assert meaning.sensitive, f"{meaning.key}: never-in-daily must also be ⚠"


@pytest.mark.parametrize("house", HOUSES)
@pytest.mark.parametrize("daily", [True, False])
def test_display_order_never_leads_with_sensitive_or_unverified(house: int, daily: bool) -> None:
    ordered = display_order(house, daily=daily)
    lead = ordered[0]
    assert not lead.sensitive
    assert lead.source is not MeaningSource.MODERN
    assert lead.source in LEAD_SOURCES
    # Same meanings, each once; the lead is the first eligible one in curated order.
    expected = [m for m in HOUSE_MEANINGS[house] if m.daily_allowed or not daily]
    assert sorted(m.key for m in ordered) == sorted(m.key for m in expected)
    assert lead == next(m for m in expected if not m.sensitive and m.source in LEAD_SOURCES)
    rest = [m for m in expected if m is not lead]
    assert list(ordered[1:]) == rest


@pytest.mark.parametrize("house", HOUSES)
def test_daily_order_excludes_never_in_daily_topics(house: int) -> None:
    ordered = display_order(house, daily=True)
    assert all(m.daily_allowed for m in ordered)
    # Each house keeps at least three doors for a many-door sentence (N-3).
    assert len(ordered) >= 3
    assert sum(not m.sensitive for m in ordered) >= 3


@pytest.mark.parametrize("house", [0, 13, -1])
def test_display_order_rejects_unknown_house(house: int) -> None:
    with pytest.raises(ValueError, match="1-12"):
        display_order(house, daily=False)


def test_house_five_opens_with_children_and_keeps_the_settled_sources() -> None:
    house = HOUSE_MEANINGS[5]
    assert house[0].key == "children"
    sources = {m.key: (m.source, m.sensitive) for m in house}
    assert sources == {
        "children": (MeaningSource.CLASSICAL, True),
        "pleasure_feasts": (MeaningSource.BOTH, False),
        "creativity": (MeaningSource.MODERN, False),
        "romance": (MeaningSource.MODERN, False),
        "sport_play": (MeaningSource.MODERN, False),
        "risk_taking": (MeaningSource.BOTH, True),
        "learning_intelligence": (MeaningSource.JYOTISH, False),
    }
    assert "con cái" in meaning_by_key("children").text
    # Love is a modern-only door in this house: never the first thing a reader sees.
    assert display_order(5, daily=True)[0].key == "pleasure_feasts"


def test_house_seven_holds_love_and_marriage() -> None:
    love = meaning_by_key("love")
    marriage = meaning_by_key("marriage")
    assert love in HOUSE_MEANINGS[7] and marriage in HOUSE_MEANINGS[7]
    assert love.source is MeaningSource.BOTH and not love.sensitive
    assert marriage.source is MeaningSource.BOTH and marriage.sensitive
    assert "tình yêu" in love.text and "hôn nhân" in marriage.text


def test_meaning_by_key_rejects_unknown_key() -> None:
    with pytest.raises(KeyError):
        meaning_by_key("dating")


def _lint_module() -> ModuleType:
    # The plain-language lint lands with C1 (#179); until then this check is skipped.
    try:
        return importlib.import_module("app.domains.readings.clarity_lint")
    except ModuleNotFoundError:
        pytest.skip("clarity_lint (C1, #179) is not on this branch yet")


def test_texts_pass_the_plain_language_rules() -> None:
    lint = _lint_module()
    for meaning in ALL_MEANINGS:
        document = lint.ClarityDocument(
            surface="house_meanings",
            sample_id=meaning.key,
            sections=(("meaning", meaning.text),),
        )
        counts = lint.lint_document(document)
        plain = {rule: n for rule, n in counts.items() if rule.startswith("A") or rule == "H1"}
        assert not any(plain.values()), (meaning.key, plain)
        if meaning.daily_allowed:
            safety = {rule: n for rule, n in counts.items() if rule.startswith("S")}
            assert not any(safety.values()), (meaning.key, safety)


def test_four_synthetic_personas() -> None:
    assert [p.key for p in READER_PERSONAS] == [
        "single_no_children",
        "married_with_children",
        "hoping_for_child",
        "older_grown_children",
    ]
    by_key = {p.key: p for p in READER_PERSONAS}
    single = by_key["single_no_children"]
    assert not (single.has_partner or single.has_children or single.hoping_for_child)
    family = by_key["married_with_children"]
    assert family.has_partner and family.has_children and not family.children_grown
    hoping = by_key["hoping_for_child"]
    assert hoping.hoping_for_child and not hoping.has_children
    older = by_key["older_grown_children"]
    assert older.age_band is AgeBand.OLDER and older.has_children and older.children_grown
    for persona in READER_PERSONAS:
        assert persona.description.strip(), persona.key
        assert not DATE_LIKE.search(persona.description), persona.key
        assert not re.search(r"\d", persona.description), persona.key
        if persona.children_grown:
            assert persona.has_children
        for key in persona.tender_meaning_keys:
            meaning_by_key(key)


def test_children_is_tender_for_the_persona_hoping_for_a_child() -> None:
    hoping = next(p for p in READER_PERSONAS if p.hoping_for_child)
    assert "children" in hoping.tender_meaning_keys
    assert meaning_by_key("children").sensitive
