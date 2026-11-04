"""HM-2/HM-3 (#190 item 3): the running readings take each house from the sourced table.

``knowledge.HOUSES`` and ``daily_personalization.HOUSE_ARENAS`` used to fold the twelve houses
into a few groups (house 5 = "hẹn hò", 6 and 10 = work, 4 and 12 = private life, 5 → self-care).
Now every house names its own set of meanings, in display-safe order: a modern-only meaning
never leads, a ⚠ meaning never leads or stands alone, and only house 5's children reach the
phrase, last, in the broad "chuyện con cái" form.
"""

from typing import Any, cast

import pytest

from app.domains.readings import knowledge
from app.domains.readings.clarity_lint import ClarityDocument, lint_document
from app.domains.readings.daily_personalization import (
    DOOR_ARENAS,
    HOUSE_ARENAS,
    HouseContext,
    SupportedSituation,
)
from app.domains.readings.house_meanings import (
    HOUSE_MEANINGS,
    LEAD_SOURCES,
    OWNER_DOOR_ORDER,
    MeaningSource,
    door_words,
    house_phrase,
    many_doors,
    meaning_by_key,
)
from app.domains.readings.interpretive_lenses import (
    PLANET_PERSPECTIVES,
    EditorialMode,
    InterpretiveLens,
    sign_structure,
)
from app.domains.readings.models import SemanticArena

HOUSES = range(1, 13)
# Labels the old tables used for one house or a group of houses; none may come back.
OLD_GROUP_LABELS = ("hẹn hò", "đời sống riêng", "quan hệ một-một", "đời sống bên trong")


@pytest.mark.parametrize("house", HOUSES)
def test_knowledge_house_names_its_own_sourced_doors(house: int) -> None:
    doors = many_doors(house)
    assert knowledge.HOUSES[house].arena == house_phrase(house)
    assert house_phrase(house) == (
        ", ".join(door_words(m) for m in doors[:-1]) + f" hay {door_words(doors[-1])}"
    )
    lead = doors[0]
    if house not in OWNER_DOOR_ORDER:
        assert lead.source in LEAD_SOURCES and lead.source is not MeaningSource.MODERN
    assert not lead.sensitive
    assert all(m.daily_allowed for m in doors)
    plain = [m for m in doors if not m.sensitive]
    # N-3: at least three ways a topic shows up, all of them this house's own meanings.
    assert len(plain) >= 3
    assert all(m in HOUSE_MEANINGS[house] for m in doors)
    # A ⚠ door is never first and never alone; only the house's curated first meaning may be one.
    sensitive = [m for m in doors if m.sensitive]
    assert sensitive in ([], [HOUSE_MEANINGS[house][0]])
    if sensitive:
        assert doors[-1] is sensitive[0]
    assert not any(label in house_phrase(house) for label in OLD_GROUP_LABELS)


def test_owner_override_reorders_house_six_only() -> None:
    # Owner decision in chat 04.11.2026 (PR #215): daily work first, small animals last.
    assert set(OWNER_DOOR_ORDER) == {6}
    assert house_phrase(6) == "công việc hằng ngày, thói quen chăm sóc cơ thể hay vật nuôi nhỏ"
    assert many_doors(6)[0].source is MeaningSource.MODERN
    # The rule still holds for every other house.
    for house in HOUSES:
        if house != 6:
            assert many_doors(house)[0].source in LEAD_SOURCES


def test_twelve_houses_are_twelve_different_sets() -> None:
    assert sorted(knowledge.HOUSES) == list(HOUSES)
    assert len({knowledge.HOUSES[h].arena for h in HOUSES}) == 12
    door_sets = [frozenset(m.key for m in many_doors(h)) for h in HOUSES]
    assert len(set(door_sets)) == 12
    # No door is shared between two houses, so no house is a copy of another.
    keys = [key for doors in door_sets for key in doors]
    assert len(keys) == len(set(keys))
    # The fixed one-word label table (6 and 10 → "công việc", 4 and 12 → "đời sống riêng")
    # is gone; a short single label per house is exactly what N-1 forbids.
    assert not hasattr(knowledge, "_short_arena")


def test_house_five_opens_with_joy_and_names_children_last() -> None:
    phrase = knowledge.HOUSES[5].arena
    assert phrase == "niềm vui, sáng tạo, tình yêu hay chuyện con cái"
    assert [m.key for m in many_doors(5)] == [
        "pleasure_feasts",
        "creativity",
        "romance",
        "children",
    ]
    # Love has only a modern source in house 5: a door, never the opening one.
    assert not phrase.startswith("tình yêu")
    assert phrase.endswith("hay chuyện con cái")
    # Risk-taking (⚠) and the other ⚠ meanings of every house stay out of the phrase.
    assert all("may rủi" not in knowledge.HOUSES[h].arena for h in HOUSES)
    for house in HOUSES:
        if house != 5:
            assert not any(m.sensitive for m in many_doors(house))


@pytest.mark.parametrize("house", HOUSES)
def test_house_arenas_keep_each_house_and_only_sourced_doors_pick_a_scene(house: int) -> None:
    context = HOUSE_ARENAS[house]
    assert isinstance(context, HouseContext)
    assert context.house == house
    assert context.doors == tuple(m.key for m in many_doors(house))
    expected = tuple(dict.fromkeys(DOOR_ARENAS[key] for key in context.doors if key in DOOR_ARENAS))
    assert context.arenas == expected
    assert SemanticArena.GENERAL not in context.arenas


def test_house_arenas_are_twelve_distinct_houses() -> None:
    assert sorted(HOUSE_ARENAS) == list(HOUSES)
    assert len({HOUSE_ARENAS[h] for h in HOUSES}) == 12
    assert len({HOUSE_ARENAS[h].doors for h in HOUSES}) == 12


def test_only_lead_eligible_doors_choose_a_daily_scene() -> None:
    for key in DOOR_ARENAS:
        meaning = meaning_by_key(key)
        assert meaning.source in LEAD_SOURCES, key
        assert not meaning.sensitive, key
    # Children (⚠) and love (modern-only in house 5) never choose house 5's scene.
    assert "children" not in DOOR_ARENAS
    assert "romance" not in DOOR_ARENAS
    assert HOUSE_ARENAS[5].arenas == (SemanticArena.SELF_CARE,)
    # House 6's sourced lead (small animals) has no everyday scene, and its modern doors
    # (daily work, body care) may not pick one.
    assert HOUSE_ARENAS[6].arenas == ()


def test_supported_situation_reads_arenas_from_its_house() -> None:
    bare = SupportedSituation("quick-reply", "m", (), "r", (1, 0, 0))
    assert bare.arenas == ()
    placed = SupportedSituation("quick-reply", "m", (), "r", (1, 0, 0), HOUSE_ARENAS[3])
    assert placed.arenas == HOUSE_ARENAS[3].arenas
    assert SemanticArena.COMMUNICATION in placed.arenas


def _lens_copy(lens: InterpretiveLens, house: int | None) -> tuple[str, str, str]:
    element, modality, _, _ = sign_structure("leo")
    context = None if house is None else cast(Any, (None, knowledge.HOUSES[house]))
    return knowledge._lens_copy(
        lens=lens,
        planet_a=knowledge.PLANETS["sun"],
        planet_b=knowledge.PLANETS["moon"],
        hook_need_a="được nhìn thấy",
        hook_need_b="được an toàn",
        perspective_a=PLANET_PERSPECTIVES["sun"],
        perspective_b=PLANET_PERSPECTIVES["moon"],
        element_a=element,
        modality_a=modality,
        context_phrase=knowledge.HOUSES[5].manifestation,
        context=context,
        background_lens=None,
        default_reaction="làm theo điều vốn thuận tay mà quên kiểm tra nhu cầu còn lại",
        editorial_mode=EditorialMode.MECHANISM,
        action_slot=0,
        reflection_slot=0,
        dynamic=False,
        aspect_name=None,
    )


def test_rendered_house_copy_names_the_doors() -> None:
    _, growth, _ = _lens_copy(InterpretiveLens.GROWTH, 5)
    assert growth.startswith(
        "Trong chuyện niềm vui, sáng tạo, tình yêu hay chuyện con cái, bạn có thể "
    )
    _, _, regulation = _lens_copy(InterpretiveLens.REGULATION, 10)
    assert regulation.startswith("Trước khi xử lý chuyện nghề nghiệp, danh dự hay chức vụ, thử ")
    # Without a known house the copy is byte-identical to before.
    _, growth_none, _ = _lens_copy(InterpretiveLens.GROWTH, None)
    assert growth_none.startswith("Trong tình huống này, bạn có thể ")
    _, _, regulation_none = _lens_copy(InterpretiveLens.REGULATION, None)
    assert regulation_none.startswith("Trước khi xử lý chuyện ở tình huống này, thử ")


@pytest.mark.parametrize("house", HOUSES)
def test_rendered_house_copy_passes_the_safety_rules(house: int) -> None:
    sections = []
    for lens in (InterpretiveLens.GROWTH, InterpretiveLens.REGULATION):
        hook, manifestation, action = _lens_copy(lens, house)
        sections += [(f"{lens.value}-hook", hook), (f"{lens.value}-scene", manifestation)]
        sections.append((f"{lens.value}-action", action))
    counts = lint_document(
        ClarityDocument(surface="house_wiring", sample_id=str(house), sections=tuple(sections))
    )
    assert not {rule: n for rule, n in counts.items() if rule.startswith(("S", "H")) and n}
    assert counts["A16"] == 0  # no house, sign or ruler words in the body
