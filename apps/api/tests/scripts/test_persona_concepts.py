"""Concept scoring on personas-1000: parsing, version building and report reproduction."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import persona_concepts as pc
from scripts import persona_concepts7 as pc7
from scripts.persona_validate import problems

QA = pc.QA
CONCEPTS = QA / "concepts"


def _parts7() -> dict[str, str]:
    text = (CONCEPTS / "mocks-v7.md").read_text(encoding="utf-8")
    return pc.split_concepts(text, (*pc7.PACKAGE7, *pc.ADDONS))


def test_the_committed_1000_personas_pass_the_validator() -> None:
    data = json.loads((QA / "personas-1000.json").read_text(encoding="utf-8"))
    assert problems(data) == []


def test_mocks_v6_and_v7_parse_every_concept_code() -> None:
    parts6 = pc.split_concepts((CONCEPTS / "mocks-v6.md").read_text(encoding="utf-8"))
    assert set(pc.PACKAGE) | set(pc.ADDONS) <= set(parts6)
    assert {"LN", "H"} <= set(_parts7())


def test_single_part_versions_carry_no_pointer_to_the_other_part() -> None:
    parts7 = _parts7()
    fixes = pc7.fix_only(parts7)
    assert "LN" not in fixes and "H" not in fixes
    assert not any("Lá nhây" in v or "[Xem bài]" in v for v in fixes.values())
    assert "xem H" not in pc7.alone(parts7, "LN")["LN"]
    assert "(LN)" not in pc7.alone(parts7, "H")["H"]


def test_a_feature_needs_30_personas_before_a_verdict() -> None:
    assert pc7._verdict(29, True).startswith("chưa đủ bằng chứng")
    assert pc7._verdict(30, True) == "đạt"
    assert pc7._verdict(30, False) == "trượt"


def test_v7_packets_rebuild_the_committed_manifest(tmp_path: Path) -> None:
    pc7.cmd_packets(
        QA / "personas-1000.json", CONCEPTS / "mocks-v6.md", CONCEPTS / "mocks-v7.md", tmp_path
    )
    rebuilt = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    committed = json.loads((CONCEPTS / "judged-v7" / "manifest.json").read_text(encoding="utf-8"))
    assert rebuilt == committed


@pytest.mark.parametrize(
    ("report", "build"),
    [
        (
            "report-concepts.md",
            lambda out: pc.cmd_report(
                QA / "personas-1000.json",
                CONCEPTS / "judged-1000",
                out,
                str(CONCEPTS / "summary-1000.md"),
            ),
        ),
        (
            "report-concepts-v7.md",
            lambda out: pc7.cmd_report(
                QA / "personas-1000.json", CONCEPTS / "judged-v7", CONCEPTS / "judged-1000", out
            ),
        ),
    ],
)
def test_committed_concept_reports_rebuild_from_the_judged_files(
    tmp_path: Path, report: str, build: Callable[[Path], None]
) -> None:
    out = tmp_path / report
    build(out)
    assert out.read_text(encoding="utf-8") == (QA / report).read_text(encoding="utf-8")
