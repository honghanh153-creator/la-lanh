"""S9 condition matrix (PR #214 rounds 9-10).

Every cell is built from the same parts and its expected S9 comes from ``_expected`` below, a
small truth function, so a rule change has to satisfy all cells, not just the newest example.
Dimensions: reader vs third-party subject x explicit vs inherited subject on the target predicate
x positive vs negative polarity x determiner present/absent x one vs two coordinated
circumstance predicates x condition before/after the main clause x main assumption
(none / has partner / single) x connector (và / hoặc / mà) joining coordinated predicates.
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
Cell = tuple[str, bool, bool, bool, bool, bool, bool | None, str]


def _sentence(cell: Cell) -> str:
    subject, inherited, positive, determiner, two, before, main, joint = cell
    who = SUBJECTS[subject]
    target = f"{'có' if positive else 'chưa có'} {'một người yêu' if determiner else 'người yêu'}"
    if inherited:
        # The target has no subject of its own: it carries on "<who> rảnh / có con nhỏ".
        condition = f"{who} {'có con nhỏ' if two else 'rảnh'} {joint} {target}"
    elif two:
        condition = f"{who} có con nhỏ {joint} {who} {target}"
    else:
        condition = f"{who} {target}"
    if before:
        return f"Nếu {condition}, {MAINS[main]}."
    return f"{MAINS[main][0].upper()}{MAINS[main][1:]}, nếu {condition}."


def _expected(cell: Cell) -> bool:
    subject, inherited, positive, determiner, two, before, main, joint = cell
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
    )
    # A single predicate with its own subject has no connector: keep one copy of it.
    if cell[1] or cell[4] or cell[7] == "và"
]


@pytest.mark.parametrize("cell", CELLS, ids=lambda cell: "-".join(map(str, cell)))
def test_s9_condition_matrix(cell: Cell) -> None:
    text = _sentence(cell)
    assert assumes_circumstances(text) is _expected(cell), text


def test_s9_matrix_size() -> None:
    assert len(CELLS) == 480
    assert len({_sentence(cell) for cell in CELLS}) == 480


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
