"""C3a-2 / N-2…N-5, A-6: the 120 planet-by-house cells (draft for owner approval)."""

import re
import unicodedata
from types import ModuleType

import pytest

from app.domains.readings import clarity_lint
from app.domains.readings.house_meanings import HOUSE_MEANINGS, LEAD_SOURCES, meaning_by_key
from app.domains.readings.planet_house_cells import (
    FAST_PLANETS,
    PLANET_HOUSE_CELLS,
    PLANETS,
    SLOW_PLANETS,
    PlanetHouseCell,
    cell,
)
from app.domains.readings.reader_personas import READER_PERSONAS

HOUSES = range(1, 13)
CELLS = tuple(PLANET_HOUSE_CELLS.values())
CELL_IDS = [f"{c.planet}-{c.house}" for c in CELLS]

# Life themes (N-5): only from Jupiter outward, and only ever as one door.
LIFE_THEME_KEYS = frozenset(
    {
        "children",
        "marriage",
        "position",
        "lifelong_goal",
        "living_abroad",
        "land",
        "in_laws",
        "debts",
        "parents_home",
        "parent_public",
        "risk_taking",
    }
)
LIFE_THEME_WORDS = re.compile(
    r"con cái|\bcó con\b|\bcon nhỏ\b|hôn nhân|vợ chồng|cưới|cam kết|gắn bó|lâu dài|đổi việc"
    r"|chuyển việc|chuyển nhà|đổi chỗ ở|sự nghiệp|nghề nghiệp|mua nhà|định cư|nước ngoài"
    r"|xa quê|cha mẹ|bố mẹ|mang thai|chia tay|đất đai|thăng chức|chức vụ",
    re.IGNORECASE,
)
# A-6 and the child words a cell must not carry when children are not one of its doors.
CHILD_WORDS = re.compile(r"\bcon\b(?! (?:người|vật|mắt|số|đường))|\bbé\b|\btrẻ\b", re.IGNORECASE)
# Words naming a ⚠ topic; the theme and the suggestion never carry one (N-3: never first).
SENSITIVE_WORDS = re.compile(
    r"con cái|cha mẹ|bố mẹ|hôn nhân|vợ chồng|họ hàng bên|\bnợ\b|bệnh|tang|cưới|may rủi|liều",
    re.IGNORECASE,
)
# An invitation, never a forecast. "sắp xếp/sắp lại/sắp đặt" is arranging, and "Nếu sắp…" is the
# reader's own plan inside a condition.
FORECAST_WORDS = re.compile(
    r"\bsẽ\b|(?<!Nếu )\bsắp\b(?! (?:xếp|lại|đặt))|chắc chắn|nhất định|định mệnh|số phận"
    r"|\bchắc là\b",
    re.IGNORECASE,
)
# Evidence-layer words (same list as test_house_meanings.py).
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

# S8 (predicted life events) and S9 (assumed circumstances) land with C1-3 (#214), which is not
# merged yet. Until it is, these are copies of its patterns at head e3107df; once
# ``clarity_lint`` has them, the test uses the real ones instead.
_LOCAL_S8_PATTERNS = (
    # pregnancy and fertility
    r"\b(?:có|mang|dính) (?:bầu|thai)\b",
    r"\b(?:bụng|bà|mẹ) bầu\b",
    r"\bthụ (?:thai|tinh)\b",
    r"\bthai (?:kỳ|nhi|sản)\b",
    r"\bsinh (?:con|em bé|bé|nở)\b",
    r"\b(?:có|đón) (?:em bé|thêm (?:con|bé|một bé|thành viên))\b",
    r"\b(?:sẽ|sắp) có (?:con|tin vui)\b",
    r"\blên chức (?:bố|mẹ|ba|cha|ông|bà)\b",
    r"\bhiếm muộn\b",
    # marriage
    r"\bkết hôn\b",
    r"\b(?:lấy|cưới) (?:chồng|vợ)\b",
    r"\b(?:cầu|đính) hôn\b",
    r"\bvề chung (?:một )?nhà\b",
    r"\b(?:sẽ|sắp|chuẩn bị|tính chuyện|đến lúc|tới lúc) (?:làm )?(?:đám )?cưới\b",
    r"\bđám cưới của (?:bạn|hai bạn|hai người)\b",
    # a breakup
    r"\b(?:sẽ|sắp|dễ|có thể|nguy cơ|đến lúc|tới lúc|chuẩn bị|đứng trước) (?:phải )?chia tay\b",
    r"\bchia tay (?:với )?(?:người yêu|người ấy|nửa kia|bạn trai|bạn gái|anh ấy|cô ấy"
    r"|chồng|vợ)\b",
    r"\b(?:hai bạn|hai người|cả hai) (?:sẽ |sắp |dễ )?chia tay\b",
    r"\bđường ai nấy đi\b",
    r"\bly thân\b",
    r"\bngoại tình\b",
    r"\b(?:tình cảm|mối quan hệ|chuyện tình|cuộc tình|hôn nhân) (?:này |của bạn )?"
    r"(?:sẽ |sắp |dễ |có thể )?(?:tan vỡ|đổ vỡ|rạn nứt|kết thúc|chấm dứt)\b",
    r"\b(?:sẽ|sắp) bị (?:đá|bỏ|bỏ rơi|phản bội|cắm sừng)\b",
    r"\bbị cắm sừng\b",
    # losing a job
    r"\bmất (?:việc|chức|ghế|chỗ làm|công việc)\b",
    r"\bthất nghiệp\b",
    r"\bsa thải\b",
    r"\bđuổi việc\b",
    r"\bcho (?:bạn )?nghỉ việc\b",
    r"\bcắt giảm (?:nhân sự|biên chế|người)\b",
    r"\bgiáng chức\b",
    r"\bphá sản\b",
    r"\b(?:sẽ|sắp) (?:phải )?nghỉ việc\b",
    # illness
    r"\b(?:bị|đổ|ngã|lăn ra|phát) ốm\b",
    r"\bốm (?:nặng|đau|liệt)\b",
    r"\b(?:nhập|nằm|vào|ra) viện\b(?! (?:bảo tàng|nghiên cứu|hàn lâm|dưỡng lão))",
    r"\bcấp cứu\b",
    r"\b(?:phải|bị) mổ\b",
    r"\bchấn thương\b",
    r"\bsốt (?:cao|xuất huyết)\b",
    r"\bcảm cúm\b",
    r"\bsức kh(?:ỏe|oẻ) (?:của bạn )?(?:sẽ |sắp |đang |dễ )?"
    r"(?:suy|giảm sút|đi xuống|xấu đi|có vấn đề)\b",
    # the death of a loved one
    r"\bmất (?:đi )?(?:người thân|người thương|người nhà|bố|mẹ|cha|vợ|chồng|ông"
    r"|bà nội|bà ngoại)\b",
    r"\bngười thân (?:sẽ |sắp |có thể |dễ )?(?:mất|ra đi|qua đời|không còn|đau ốm|bệnh)\b",
    r"\b(?:để|chịu|đám|có) tang\b",
    r"\btang (?:lễ|sự|thương)\b",
    r"\bđám ma\b",
    r"\btừ trần\b",
    r"\bkhuất núi\b",
    r"\bra đi mãi mãi\b",
    r"\bmồ côi\b",
    r"\bgóa (?:chồng|vợ|bụa)\b",
    r"\bâm dương cách biệt\b",
    r"\bmất mát (?:người thân|lớn trong gia đình)\b",
    # other life events foretold
    r"\b(?:sẽ|sắp) (?:gặp|tìm thấy|tìm được|có) (?:người yêu|nửa kia|chân ái|ý trung nhân"
    r"|người định mệnh|tình yêu mới|người ấy)\b",
    r"\b(?:sẽ|sắp) (?:chuyển nhà|chuyển việc|đổi việc|ra nước ngoài|định cư)\b",
)
_LOCAL_S9_PATTERNS = (
    # single
    r"\bbạn (?:đang |vẫn |còn |hiện )?(?:độc thân|ế|lẻ bóng|một mình chưa có ai)\b",
    r"\b(?:độc thân|ế|lẻ bóng) như bạn\b",
    r"\bchưa có (?:người yêu|bồ|nửa kia|ai để yêu)\b",
    r"\bbạn chưa (?:lập gia đình|kết hôn|có gia đình|có con)\b",
    # partnered
    r"\b(?:người yêu|bạn trai|bạn gái|nửa kia|người ấy|vợ|chồng|người thương|crush) của bạn\b"
    r"(?! (?:ấy|bè|thân))",
    r"\b(?:ông|bà) xã\b",
    r"\bvợ chồng (?:bạn|nhà bạn|hai bạn)\b",
    r"\b(?:nhà|mẹ|bố|ba) (?:chồng|vợ)\b",
    r"\bgia đình nhỏ của bạn\b",
    # children
    r"\b(?:con|các con|con cái|con nhỏ|bé|nhóc|các bé) (?:của|nhà) bạn\b(?! (?:ấy|bè|thân))",
    r"\bcon bạn\b(?! (?:ấy|bè|thân|học|cùng))",
    r"\b(?:đón|đưa) (?:con|bé|các con)\b",
    r"\b(?:dỗ|ru|chăm|nuôi|tắm cho) (?:con|bé|các con)\b",
    r"\bcho (?:con|bé) (?:bú|ăn|ngủ)\b",
    r"\bbạn (?:là|đang làm) (?:bố|mẹ|cha|ba|cha mẹ|bố mẹ|phụ huynh)\b",
    r"\b(?:bố mẹ|cha mẹ|phụ huynh|mẹ bỉm|bỉm sữa) như bạn\b",
    r"\bmẹ bỉm\b",
    # gender
    r"\bbạn là (?:một )?(?:phụ nữ|đàn ông|đàn bà|con gái|con trai|cô gái|chàng trai|nam|nữ)\b",
    r"\b(?:phụ nữ|đàn ông|con gái|con trai|cô gái|chàng trai|nàng|chàng) như bạn\b",
    r"\bphái (?:đẹp|mạnh|yếu)\b",
    r"\bchị em (?:mình|phụ nữ|ta)\b",
    r"\b(?:các|mấy) (?:nàng|chàng)\b",
    r"\b(?:nàng|chàng|anh|chị|cô) ơi\b",
    r"\bđấng mày râu\b",
    r"\b(?:cô nàng|chàng trai|anh chàng|quý cô|quý ông) (?:Bạch Dương|Kim Ngưu|Song Tử|Cự Giải"
    r"|Sư Tử|Xử Nữ|Thiên Bình|Bọ Cạp|Thiên Yết|Nhân Mã|Ma Kết|Bảo Bình|Song Ngư)\b",
)
_LOCAL_S8 = re.compile("|".join(f"(?:{p})" for p in _LOCAL_S8_PATTERNS), re.IGNORECASE)
_LOCAL_S9 = re.compile("|".join(f"(?:{p})" for p in _LOCAL_S9_PATTERNS), re.IGNORECASE)
_LOCAL_DOOR_WORDS = re.compile(
    r"\b(?:nếu|giả sử|trường hợp|với ai|ai đang|người đang)\b", re.IGNORECASE
)


def _local_assumes_circumstances(sentence: str) -> bool:
    for match in _LOCAL_S9.finditer(sentence):
        clause = re.split(r"[,;:]", sentence[: match.start()])[-1]
        if not _LOCAL_DOOR_WORDS.search(clause):
            return True
    return False


def _s8_pattern(lint: ModuleType) -> re.Pattern[str]:
    return lint.SAFETY_RULES.get("S8", _LOCAL_S8)


def _assumes(lint: ModuleType):
    return getattr(lint, "assumes_circumstances", _local_assumes_circumstances)


def _document(c: PlanetHouseCell) -> clarity_lint.ClarityDocument:
    sections = (
        ("theme", c.theme),
        *((f"way_{index}", way.text) for index, way in enumerate(c.ways)),
        ("suggestion", c.suggestion),
    )
    return clarity_lint.ClarityDocument(
        surface="planet_house_cells", sample_id=f"{c.planet}-{c.house}", sections=sections
    )


def _all_text(c: PlanetHouseCell) -> str:
    return "\n".join(c.sentences())


def test_every_cell_is_present() -> None:
    assert len(PLANETS) == 10
    assert FAST_PLANETS == {"moon", "sun", "mercury", "venus", "mars"}
    assert SLOW_PLANETS == {"jupiter", "saturn", "uranus", "neptune", "pluto"}
    assert set(PLANET_HOUSE_CELLS) == {(p, h) for p in PLANETS for h in HOUSES}
    assert len(PLANET_HOUSE_CELLS) == 120
    for (planet, house), c in PLANET_HOUSE_CELLS.items():
        assert (c.planet, c.house) == (planet, house)
        assert cell(planet, house) is c
    with pytest.raises(KeyError):
        cell("chiron", 1)
    with pytest.raises(KeyError):
        cell("moon", 13)


@pytest.mark.parametrize("c", CELLS, ids=CELL_IDS)
def test_cell_shape(c: PlanetHouseCell) -> None:
    assert c.theme.endswith(".") and c.theme[0].isupper(), c.theme
    assert 3 <= len(c.ways) <= 4
    for way in c.ways:
        assert way.text == way.text.strip() and way.text[0].islower(), way.text
        assert not way.text.endswith((".", "!", "?", ",")), way.text
    assert re.fullmatch(r"Nếu [^.]+, thì [^.]+\.", c.suggestion), c.suggestion
    for sentence in c.sentences():
        assert unicodedata.normalize("NFC", sentence) == sentence
        assert not re.search(r"\d", sentence), sentence
        assert clarity_lint.syllables(sentence) <= 22, sentence


@pytest.mark.parametrize("c", CELLS, ids=CELL_IDS)
def test_every_door_comes_from_a_daily_meaning_of_that_house(c: PlanetHouseCell) -> None:
    house_keys = {m.key for m in HOUSE_MEANINGS[c.house]}
    keys = [way.meaning for way in c.ways]
    assert len(keys) == len(set(keys)), "one meaning per door"
    assert c.sources == tuple(keys)
    for key in keys:
        assert key in house_keys, (key, c.house)
        assert meaning_by_key(key).daily_allowed, key


@pytest.mark.parametrize("c", CELLS, ids=CELL_IDS)
def test_first_door_is_classical_and_not_sensitive(c: PlanetHouseCell) -> None:
    lead = meaning_by_key(c.ways[0].meaning)
    assert lead.source in LEAD_SOURCES, f"MODERN-only meaning first: {lead.key}"
    assert not lead.sensitive


@pytest.mark.parametrize("c", CELLS, ids=CELL_IDS)
def test_sensitive_door_never_alone_never_first(c: PlanetHouseCell) -> None:
    sensitive = [w for w in c.ways if meaning_by_key(w.meaning).sensitive]
    if not sensitive:
        return
    assert c.planet in SLOW_PLANETS
    assert len(c.ways) >= 3
    assert len(c.ways) - len(sensitive) >= 2
    assert c.ways[0] not in sensitive
    assert not SENSITIVE_WORDS.search(c.theme), c.theme
    assert not SENSITIVE_WORDS.search(c.suggestion), c.suggestion


@pytest.mark.parametrize("c", CELLS, ids=CELL_IDS)
def test_theme_and_suggestion_never_name_a_sensitive_topic(c: PlanetHouseCell) -> None:
    assert not SENSITIVE_WORDS.search(c.theme), c.theme
    assert not SENSITIVE_WORDS.search(c.suggestion), c.suggestion


@pytest.mark.parametrize("c", [c for c in CELLS if c.planet in FAST_PLANETS])
def test_fast_planets_speak_only_of_mood_and_small_things(c: PlanetHouseCell) -> None:
    for way in c.ways:
        meaning = meaning_by_key(way.meaning)
        assert not meaning.sensitive, way.meaning
        assert way.meaning not in LIFE_THEME_KEYS, way.meaning
    match = LIFE_THEME_WORDS.search(_all_text(c))
    assert match is None, (c.planet, c.house, match and match.group(0))


def test_saturn_and_mars_in_house_five_never_mention_children() -> None:
    for planet in ("saturn", "mars"):
        c = cell(planet, 5)
        assert "children" not in c.sources
        assert not CHILD_WORDS.search(_all_text(c)), planet


def test_children_appear_only_with_jupiter_in_house_five() -> None:
    with_children = [(c.planet, c.house) for c in CELLS if "children" in c.sources]
    assert with_children == [("jupiter", 5)]
    jupiter = cell("jupiter", 5)
    assert jupiter.ways[-1].meaning == "children"
    for c in CELLS:
        if (c.planet, c.house) != ("jupiter", 5):
            assert not CHILD_WORDS.search(_all_text(c)), (c.planet, c.house)


@pytest.mark.parametrize("c", CELLS, ids=CELL_IDS)
def test_no_forecast_and_no_evidence_layer_words(c: PlanetHouseCell) -> None:
    for sentence in c.sentences():
        assert not FORECAST_WORDS.search(sentence), sentence
        assert not FORBIDDEN.search(sentence), sentence


@pytest.mark.parametrize("c", CELLS, ids=CELL_IDS)
def test_cell_passes_the_plain_language_and_safety_rules(c: PlanetHouseCell) -> None:
    counts = clarity_lint.lint_document(_document(c))
    assert {rule: n for rule, n in counts.items() if n} == {}


@pytest.mark.parametrize("c", CELLS, ids=CELL_IDS)
def test_cell_predicts_no_life_event_and_assumes_no_circumstance(c: PlanetHouseCell) -> None:
    s8 = _s8_pattern(clarity_lint)
    assumes = _assumes(clarity_lint)
    for sentence in c.sentences():
        normalised = clarity_lint.normalize_text(sentence)
        assert not s8.search(normalised), ("S8", sentence)
        assert not assumes(normalised), ("S9", sentence)


def test_local_s8_s9_copies_still_catch_what_they_should() -> None:
    assert _LOCAL_S8.search("Tháng này bạn sắp có tin vui.")
    assert _LOCAL_S8.search("Hai bạn sẽ kết hôn.")
    assert _local_assumes_circumstances("Đón con sớm rồi về nấu cơm.")
    assert not _local_assumes_circumstances("Nếu bạn đang độc thân, đi chơi với bạn bè.")


def test_no_sentence_repeats_across_cells() -> None:
    seen: dict[str, str] = {}
    for c in CELLS:
        for sentence in c.sentences():
            key = " ".join(sentence.casefold().split()).strip(".")
            assert key not in seen, f"{sentence!r} in {c.planet}-{c.house} and {seen[key]}"
            seen[key] = f"{c.planet}-{c.house}"


def test_surface_has_no_shared_sentence() -> None:
    report = clarity_lint.lint_surface("planet_house_cells", [_document(c) for c in CELLS])
    assert report.rules["A6"] == 0
    assert not any(report.hard_zero.values())


@pytest.mark.parametrize("persona", READER_PERSONAS, ids=lambda p: p.key)
def test_tender_topics_never_stand_alone_for_any_persona(persona) -> None:
    tender_anywhere = {key for p in READER_PERSONAS for key in p.tender_meaning_keys}
    for c in CELLS:
        assert c.ways[0].meaning not in tender_anywhere, (c.planet, c.house)
        safe = [w for w in c.ways if w.meaning not in persona.tender_meaning_keys]
        assert len(safe) >= 2, (persona.key, c.planet, c.house)
