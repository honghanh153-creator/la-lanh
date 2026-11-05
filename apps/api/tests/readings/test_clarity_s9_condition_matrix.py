"""S9 condition matrix (PR #214 rounds 9-10).

Every cell is built from the same parts and its expected S9 comes from ``_expected`` below, a
small truth function, so a rule change has to satisfy all cells, not just the newest example.
Dimensions: reader vs third-party subject x explicit vs inherited subject on the target predicate
x positive vs negative polarity x determiner present/absent x one vs two coordinated
circumstance predicates x condition before/after the main clause x main assumption
(none / has partner / single) x connector (và / hoặc / mà) joining coordinated predicates
x door word repeated after the connector (round 11; only for two predicates with their own
subjects). Conditions in a row form one chain whether or not the door word is repeated.
"và"/"mà" establish the union of the joined circumstances; "hoặc" only what holds in every
alternative (the intersection). Synthetic sentences only.
"""

from __future__ import annotations

from itertools import product

import pytest

from app.domains.readings.clarity_lint import assumes_circumstances

SUBJECTS = {"reader": "bạn", "third": "đồng nghiệp"}
MAINS: dict[bool | None, str] = {
    None: "tối nay cứ thong thả",
    True: "tối nay rủ người yêu của bạn đi dạo",
    False: "một người độc thân như bạn tối nay cứ thong thả",
}
CONNECTORS = ("và", "hoặc", "mà")
Cell = tuple[str, bool, bool, bool, bool, bool, bool | None, str, bool]


def _sentence(cell: Cell) -> str:
    subject, inherited, positive, determiner, two, before, main, joint, repeat = cell
    who = SUBJECTS[subject]
    target = f"{'có' if positive else 'chưa có'} {'một người yêu' if determiner else 'người yêu'}"
    if inherited:
        # The target has no subject of its own: it carries on "<who> rảnh / có con nhỏ".
        condition = f"{who} {'có con nhỏ' if two else 'rảnh'} {joint} {target}"
    elif two:
        door = "nếu " if repeat else ""
        condition = f"{who} có con nhỏ {joint} {door}{who} {target}"
    else:
        condition = f"{who} {target}"
    if before:
        return f"Nếu {condition}, {MAINS[main]}."
    return f"{MAINS[main][0].upper()}{MAINS[main][1:]}, nếu {condition}."


def _expected(cell: Cell) -> bool:
    subject, inherited, positive, determiner, two, before, main, joint, _repeat = cell
    # The target is about the reader only when its subject (own or inherited) is "bạn".
    local = positive if subject == "reader" else None
    # "hoặc": the other alternative ("rảnh" / "có con nhỏ") never establishes a partner, so the
    # intersection holds no partner fact after the condition. "và"/"mà": the union keeps it.
    alternatives = (inherited or two) and joint == "hoặc"
    established = None if alternatives else local
    # The bare "chưa có người yêu" is itself an assumption pattern (with "một" it is not); only a
    # reader condition of the same polarity covers it.
    if not positive and not determiner and local is not False:
        return True
    # The main clause's assumption is covered only by a reader condition opened before it.
    return main is not None and not (before and established is main)


CELLS: list[Cell] = [
    cell
    for cell in product(
        SUBJECTS,
        (False, True),
        (True, False),
        (False, True),
        (False, True),
        (True, False),
        MAINS,
        CONNECTORS,
        (False, True),
    )
    # A single predicate with its own subject has no connector: keep one copy of it. The door
    # word is repeated only before a second predicate with its own subject.
    if (cell[1] or cell[4] or cell[7] == "và") and (not cell[8] or (cell[4] and not cell[1]))
]


@pytest.mark.parametrize("cell", CELLS, ids=lambda cell: "-".join(map(str, cell)))
def test_s9_condition_matrix(cell: Cell) -> None:
    text = _sentence(cell)
    assert assumes_circumstances(text) is _expected(cell), text


def test_s9_matrix_size() -> None:
    assert len(CELLS) == 624
    assert len({_sentence(cell) for cell in CELLS}) == 624


@pytest.mark.parametrize(
    ("text", "flagged"),
    [
        ("Nếu bạn có con nhỏ và chưa có người yêu, tối nay cứ thong thả.", False),
        ("Nếu bạn rảnh hoặc chưa có người yêu, tối nay cứ thong thả.", False),
        ("Nếu bạn có con nhỏ mà chưa có người yêu, tối nay cứ thong thả.", False),
        ("Nếu đồng nghiệp có con nhỏ và chưa có người yêu, tối nay cứ thong thả.", True),
        ("Nếu bạn rảnh và đồng nghiệp chưa có người yêu, tối nay cứ thong thả.", True),
        ("Nếu bạn rảnh và một phụ huynh gọi, hãy đón con.", True),
        ("Nếu bạn rảnh và con nhỏ ốm, hãy đón con.", True),
        ("Nếu bạn rảnh và là phụ huynh, hãy đón con.", False),
        ("Nếu bạn rảnh hoặc là phụ huynh, hãy đón con.", True),
        ("Nếu bạn rảnh hoặc có con nhỏ, hãy đón con sớm.", True),
        ("Nếu bạn có con nhỏ hoặc đang nuôi con, hãy đón con sớm.", False),
        ("Nếu bạn có con nhỏ và rảnh, hãy đón con sớm.", False),
        ("Nếu bạn rảnh mà có con nhỏ, hãy đón con sớm.", False),
    ],
)
def test_s9_coordinated_condition_inherits_only_the_reader(text: str, flagged: bool) -> None:
    assert assumes_circumstances(text) is flagged


DOORS = ("nếu", "khi", "lúc", "giả sử", "trường hợp")


@pytest.mark.parametrize("door", DOORS)
@pytest.mark.parametrize(
    ("template", "flagged"),
    [
        # Round 11 (Codex auto-10 P1): a repeated door after "hoặc" stays in the same chain.
        ("{D} bạn rảnh hoặc {d} bạn có con nhỏ, hãy đón con sớm.", True),
        ("{D} bạn rảnh hoặc {d} có con nhỏ, hãy đón con sớm.", True),
        ("{D} bạn có con nhỏ hoặc {d} bạn đang nuôi con, hãy đón con sớm.", False),
        ("{D} bạn rảnh và {d} bạn có con nhỏ, hãy đón con sớm.", False),
        ("{D} bạn rảnh mà {d} bạn có con nhỏ, hãy đón con sớm.", False),
        ("{D} bạn rảnh, {d} bạn có con nhỏ, hãy đón con sớm.", False),
        ("{D} bạn có con nhỏ, hoặc {d} bạn rảnh, hãy đón con sớm.", True),
        ("{D} bạn có con nhỏ và rảnh hoặc {d} bạn có con nhỏ, hãy đón con sớm.", False),
        ("{D} bạn có con nhỏ và rảnh hoặc {d} bạn rảnh, hãy đón con sớm.", True),
        # Self-audit shapes that must not bypass S9.
        ("{D} bạn có con nhỏ hoặc {d} không, hãy đón con sớm.", True),
        ("{D} bạn không có con nhỏ, hãy đón con sớm.", True),
        ("{D} không có con nhỏ, hãy đón con sớm.", True),
        ("Trừ khi bạn có con nhỏ, hãy đón con sớm.", True),
        ("Trừ khi bạn không có con nhỏ, hãy đón con sớm.", True),
        # A main clause ends the chain; the next condition opens its own chain.
        ("{D} bạn rảnh, hãy nghỉ, hoặc {d} bạn có con nhỏ, hãy đón con sớm.", False),
        # Round 13: the earlier branch's fact does not carry into a sibling branch.
        ("{D} bạn có con nhỏ, hãy nghỉ, hoặc {d} bạn rảnh, hãy đón con sớm.", True),
        ("Hãy đón con sớm, {d} bạn có con nhỏ.", True),
    ],
)
def test_s9_repeated_door_stays_in_chain(door: str, template: str, flagged: bool) -> None:
    text = template.format(D=door[0].upper() + door[1:], d=door)
    assert assumes_circumstances(text) is flagged, text


# Round 12 (Codex auto-11 P1): a fact carries a value, not only an axis and polarity. A
# condition covers an assumption only when axis, polarity and value match; a specific condition
# covers the general assumption of its axis, a general one never covers a specific assumption,
# and different values (đàn ông / phụ nữ, a child / a young child) never cover each other.
VALUE_CONDITIONS: dict[str, dict[str | None, tuple[str, ...]]] = {
    "gender": {
        "female": ("bạn là phụ nữ", "bạn là một cô gái", "bạn là nữ"),
        "male": ("bạn là đàn ông", "bạn là một chàng trai", "bạn là nam"),
    },
    "partner": {
        None: ("bạn có người yêu", "bạn đang hẹn hò"),
        "married": ("bạn đã kết hôn", "bạn có chồng"),
    },
    "children": {
        None: ("bạn có con", "bạn là phụ huynh"),
        "young": ("bạn có con nhỏ", "bạn đang nuôi con nhỏ"),
    },
}
VALUE_ASSUMPTIONS: dict[str, dict[str | None, tuple[str, ...]]] = {
    "gender": {
        "female": ("phụ nữ như bạn nên nghỉ sớm", "cô gái như bạn nên nghỉ sớm"),
        "male": ("đàn ông như bạn nên nghỉ sớm", "chàng trai như bạn nên nghỉ sớm"),
    },
    "partner": {
        None: ("hãy rủ người yêu của bạn đi dạo", "hãy nhắn cho nửa kia của bạn"),
        "married": ("hãy rủ chồng của bạn đi dạo", "vợ chồng bạn nên nghỉ sớm"),
    },
    "children": {
        None: ("hãy dành thời gian cho con của bạn", "hãy đón con sớm"),
        "young": ("hãy dành thời gian cho con nhỏ của bạn", "hãy cho bé ngủ sớm"),
    },
}
VALUE_DOORS = ("Nếu", "Khi")
ValueCell = tuple[str, str | None, str, str | None, str, str, bool]


def _value_expected(cell: ValueCell) -> bool:
    axis, cond_value, _cond, asm_value, _asm, _door, before = cell
    if not before:
        return True
    if cond_value == asm_value:
        return False
    # Gender values never imply each other; elsewhere the specific covers the general.
    return axis == "gender" or asm_value is not None


VALUE_CELLS: list[ValueCell] = [
    (axis, cond_value, cond, asm_value, asm, door, before)
    for axis in VALUE_CONDITIONS
    for cond_value, conds in VALUE_CONDITIONS[axis].items()
    for cond in conds
    for asm_value, asms in VALUE_ASSUMPTIONS[axis].items()
    for asm in asms
    for door in VALUE_DOORS
    for before in (True, False)
]


def _value_sentence(cell: ValueCell) -> str:
    _axis, _cv, cond, _av, asm, door, before = cell
    if before:
        return f"{door} {cond}, {asm}."
    return f"{asm[0].upper()}{asm[1:]}, {door.lower()} {cond}."


@pytest.mark.parametrize("cell", VALUE_CELLS, ids=lambda cell: "-".join(map(str, cell)))
def test_s9_value_matrix(cell: ValueCell) -> None:
    text = _value_sentence(cell)
    assert assumes_circumstances(text) is _value_expected(cell), text


def test_s9_value_matrix_size() -> None:
    assert len(VALUE_CELLS) == 224
    assert len({_value_sentence(cell) for cell in VALUE_CELLS}) == 224


@pytest.mark.parametrize(
    ("text", "flagged"),
    [
        ("Nếu bạn là đàn ông, phụ nữ như bạn nên nghỉ sớm.", True),
        ("Nếu bạn là phụ nữ, đàn ông như bạn nên nghỉ sớm.", True),
        ("Nếu bạn là nam, cô gái như bạn nên nghỉ sớm.", True),
        ("Nếu bạn là nữ, chàng trai như bạn nên nghỉ sớm.", True),
        ("Nếu bạn là đàn ông, đấng mày râu cũng cần nghỉ.", False),
        ("Nếu bạn là đàn ông, phái đẹp cũng cần nghỉ.", True),
        ("Nếu bạn là phụ nữ, chị em mình cũng cần nghỉ.", False),
        ("Nếu bạn là phụ nữ hoặc là đàn ông, phụ nữ như bạn nên nghỉ sớm.", True),
        ("Nếu bạn là phụ nữ, phụ nữ như bạn nên nghỉ sớm.", False),
        ("Nếu bạn có người yêu, ông xã của bạn sẽ vui.", True),
        ("Nếu bạn đã kết hôn hoặc có người yêu, hãy rủ người yêu của bạn đi dạo.", False),
        ("Nếu bạn đã kết hôn hoặc có người yêu, hãy rủ chồng của bạn đi dạo.", True),
        ("Nếu bạn độc thân, bạn chưa kết hôn nên cứ thong thả.", False),
        ("Nếu bạn chưa kết hôn, bạn đang độc thân nên cứ thong thả.", True),
        ("Nếu bạn là phụ huynh, hãy cho bé ngủ sớm.", True),
        ("Nếu bạn có con nhỏ, hãy cho bé ngủ sớm.", False),
    ],
)
def test_s9_cross_value_named_cases(text: str, flagged: bool) -> None:
    assert assumes_circumstances(text) is flagged, text


# Round 13 (Codex auto-12 P1): a condition chain's facts cover only the main clause(s) it
# governs, up to the next condition chain or the sentence end. Branch scope dimension: the
# assumption's covering fact is in the same branch, only in a sibling (earlier) branch, or
# nowhere; crossed with the connector before the second door, the door word and the axis.
BRANCH_FACTS = {
    "gender": ("bạn là phụ nữ", "chị em mình nên đi dạo", "bạn là đàn ông"),
    "children": ("bạn có con nhỏ", "hãy cho bé ngủ sớm", "bạn rảnh"),
    "partner": ("bạn có người yêu", "hãy rủ người yêu của bạn đi dạo", "bạn rảnh"),
}
BRANCH_SCOPES = ("same", "sibling", "none")
BRANCH_JOINS = ("hoặc", "còn", "")
BRANCH_DOORS = ("nếu", "khi")
BranchCell = tuple[str, str, str, str]

BRANCH_CELLS: list[BranchCell] = list(
    product(BRANCH_FACTS, BRANCH_SCOPES, BRANCH_JOINS, BRANCH_DOORS)
)


def _branch_sentence(cell: BranchCell) -> str:
    axis, scope, join, door = cell
    fact, assumption, other = BRANCH_FACTS[axis]
    first, second = {"same": (other, fact), "sibling": (fact, other), "none": (other, other)}[scope]
    lead = f"{join} " if join else ""
    return f"{door.capitalize()} {first}, hãy nghỉ, {lead}{door} {second}, {assumption}."


@pytest.mark.parametrize("cell", BRANCH_CELLS, ids=lambda cell: "-".join(cell))
def test_s9_branch_scope_matrix(cell: BranchCell) -> None:
    text = _branch_sentence(cell)
    assert assumes_circumstances(text) is (cell[1] != "same"), text


def test_s9_branch_scope_matrix_size() -> None:
    assert len(BRANCH_CELLS) == 54
    assert len({_branch_sentence(cell) for cell in BRANCH_CELLS}) == 54


@pytest.mark.parametrize(
    ("text", "flagged"),
    [
        ("Nếu bạn là phụ nữ, hãy nghỉ, hoặc nếu bạn là đàn ông, chị em mình nên đi dạo.", True),
        ("Nếu bạn là đàn ông, hãy nghỉ, hoặc nếu bạn là phụ nữ, chị em mình nên đi dạo.", False),
        ("Nếu bạn rảnh, hãy nghỉ, hoặc nếu bạn có con nhỏ, hãy đón con sớm.", False),
        ("Nếu bạn có con nhỏ, hãy nghỉ, hoặc nếu bạn rảnh, hãy đón con sớm.", True),
        ("Nếu bạn có con nhỏ, hãy nghỉ và cho bé ngủ sớm.", False),
    ],
)
def test_s9_branch_scope_named_cases(text: str, flagged: bool) -> None:
    assert assumes_circumstances(text) is flagged, text
