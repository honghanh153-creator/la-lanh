"""S9 condition matrix (PR #214 round 9).

Every cell is built from the same parts and its expected S9 comes from ``_expected`` below, a
small truth function, so a rule change has to satisfy all cells, not just the newest example.
Dimensions: reader vs third-party subject x explicit vs inherited subject on the target predicate
x positive vs negative polarity x determiner present/absent x one vs two coordinated
circumstance predicates x condition before/after the main clause x main assumption
(none / has partner / single). Synthetic sentences only.
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
Cell = tuple[str, bool, bool, bool, bool, bool, bool | None]


def _sentence(cell: Cell) -> str:
    subject, inherited, positive, determiner, two, before, main = cell
    who = SUBJECTS[subject]
    target = f"{'có' if positive else 'chưa có'} {'một người yêu' if determiner else 'người yêu'}"
    if inherited:
        # The target has no subject of its own: it carries on "<who> rảnh / có con nhỏ".
        condition = f"{who} {'có con nhỏ' if two else 'rảnh'} và {target}"
    elif two:
        condition = f"{who} có con nhỏ và {who} {target}"
    else:
        condition = f"{who} {target}"
    if before:
        return f"Nếu {condition}, {MAINS[main]}."
    return f"{MAINS[main][0].upper()}{MAINS[main][1:]}, nếu {condition}."


def _expected(cell: Cell) -> bool:
    subject, _inherited, positive, determiner, _two, before, main = cell
    # The target is about the reader only when its subject (own or inherited) is "bạn".
    established = positive if subject == "reader" else None
    # The bare "chưa có người yêu" is itself an assumption pattern (with "một" it is not); only a
    # reader condition of the same polarity covers it.
    if not positive and not determiner and established is not False:
        return True
    # The main clause's assumption is covered only by a reader condition opened before it.
    return main is not None and not (before and established is main)


CELLS: list[Cell] = list(
    product(
        SUBJECTS,
        (False, True),
        (True, False),
        (False, True),
        (False, True),
        (True, False),
        MAINS,
    )
)


@pytest.mark.parametrize("cell", CELLS, ids=lambda cell: "-".join(map(str, cell)))
def test_s9_condition_matrix(cell: Cell) -> None:
    text = _sentence(cell)
    assert assumes_circumstances(text) is _expected(cell), text


def test_s9_matrix_size() -> None:
    assert len(CELLS) == 192
    assert len({_sentence(cell) for cell in CELLS}) == 192


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
    ],
)
def test_s9_coordinated_condition_inherits_only_the_reader(text: str, flagged: bool) -> None:
    assert assumes_circumstances(text) is flagged
