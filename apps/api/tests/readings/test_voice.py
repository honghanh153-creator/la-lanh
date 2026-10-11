import re
import unicodedata
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from app.domains.astro.models import TimePrecision, Tradition, ZodiacSign
from app.domains.readings.daily_personalization import PLACEMENT_MEANINGS
from app.domains.readings.daily_psychology import (
    _ARENA_LEADS,
    DAILY_ISSUES,
    LEGACY_ARENA_LEADS,
    DailyIssuePattern,
    lead_scene,
)
from app.domains.readings.models import (
    BackgroundLens,
    PlanMode,
    ReadingContentProjection,
    ReadingEvidenceProjection,
    ReadingPurpose,
    ReadingRevisionSource,
    ReadingSectionsProjection,
    SemanticArena,
    experiment_projection_for,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.review_agent import ContentReviewAgent, ReviewSample
from app.domains.readings.voice import (
    ROAST_ISSUES,
    ROAST_PLACEMENT_MEANINGS,
    DailySections,
    ReadingVoice,
    apply_content_voice,
    roast_daily_sections,
    roast_legacy_text,
)
from scripts.review_content_release import _date_only, _full_chart

# Identity, body, intelligence, fatalism, certainty and profanity never appear.
BANNED_WORDS = (
    "ngu",
    "đần",
    "ngốc",
    "béo",
    "mập",
    "xấu",
    "vô dụng",
    "thất bại",
    "lười",
    "điên",
    "khùng",
    "chắc chắn sẽ",
    "định mệnh",
    "số phận",
    "trầm cảm",
    "đồ ngốc",
    "vãi",
    "đéo",
    "đm",
)
SHARP_ONLY = tuple(voice.jab for voice in ROAST_ISSUES.values()) + tuple(
    voice.action_frame for voice in ROAST_ISSUES.values()
)


def _roast_lines() -> tuple[str, ...]:
    lines: list[str] = []
    for voice in ROAST_ISSUES.values():
        lines.extend(roast for _, roast in voice.headlines)
        lines.extend(
            (
                voice.jab,
                voice.gentle_jab,
                voice.scene_tag,
                voice.action_frame,
                voice.gentle_action_frame,
            )
        )
    lines.extend(ROAST_PLACEMENT_MEANINGS.values())
    return tuple(lines)


def _contains_word(text: str, word: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text.casefold()) is not None


def test_every_direct_headline_has_one_distinct_roast_headline() -> None:
    direct = [headline for issue in DAILY_ISSUES for headline in issue.headlines]
    roast = {
        original: replacement
        for voice in ROAST_ISSUES.values()
        for original, replacement in voice.headlines
    }

    assert len(direct) == len(set(direct)) == 90
    assert set(roast) == set(direct)
    assert len(set(roast.values())) == len(roast)
    assert all(roast[headline] != headline for headline in direct)
    assert set(ROAST_PLACEMENT_MEANINGS) == set(PLACEMENT_MEANINGS)


def test_roast_lines_avoid_banned_words_and_stay_readable() -> None:
    for line in _roast_lines():
        assert not any(_contains_word(line, word) for word in BANNED_WORDS), line
        assert len(line.split()) <= 28, line
        assert line[-1] in ".?!:", line
        # No claim about what another person privately thinks or feels.
        assert not re.search(r"người kia (?:đang )?(?:nghĩ|giận|ghét|thích|muốn)", line), line


def _sections_for(
    issue_key: str, *, arena: SemanticArena | None, legacy: bool = False
) -> DailySections:
    issue = next(issue for issue in DAILY_ISSUES if issue.key == issue_key)
    placement = PLACEMENT_MEANINGS.get(issue_key, "Dữ kiện chưa đủ.")
    if legacy:
        # Saved v6 notes: fragment lead, four-sentence thesis carrying the meaning.
        lead = LEGACY_ARENA_LEADS.get(arena) if arena is not None else None
        scene = issue.scenes[0] if lead is None else f"{lead} {issue.scenes[0]}"
        thesis = f"{placement} {issue.meaning} Một câu rút ra cũ. Cảnh là ví dụ."
    else:
        lead = _ARENA_LEADS.get(arena) if arena is not None else None
        scene = issue.scenes[0] if lead is None else lead_scene(lead, issue.scenes[0])
        thesis = f"{placement} {issue.takeaway}"
    return DailySections(issue.headlines[0], thesis, scene, issue.advice[0])


@pytest.mark.parametrize("legacy", [False, True], ids=["current", "saved-v6"])
@pytest.mark.parametrize("issue", DAILY_ISSUES, ids=lambda issue: issue.key)
def test_roast_keeps_issue_scene_and_exact_action(issue: DailyIssuePattern, legacy: bool) -> None:
    key = issue.key
    direct = _sections_for(key, arena=SemanticArena.WORK, legacy=legacy)
    roast = roast_daily_sections(direct)
    voice = ROAST_ISSUES[key]

    assert roast.hook == dict(voice.headlines)[direct.hook]
    assert roast.thesis.startswith(f"{voice.jab} ")
    assert (issue.meaning if legacy else issue.takeaway) in roast.thesis
    assert roast.manifestation.startswith(direct.manifestation)
    assert roast.micro_action.endswith(direct.micro_action)
    assert roast.micro_action == f"{voice.action_frame} {direct.micro_action}"


@pytest.mark.parametrize("legacy", [False, True], ids=["current", "saved-v6"])
@pytest.mark.parametrize("arena", [SemanticArena.ENERGY, SemanticArena.SELF_CARE])
def test_energy_and_self_care_examples_only_get_gentle_teasing(
    arena: SemanticArena, legacy: bool
) -> None:
    for key, voice in ROAST_ISSUES.items():
        direct = _sections_for(key, arena=arena, legacy=legacy)
        roast = roast_daily_sections(direct)

        assert roast.thesis.startswith(f"{voice.gentle_jab} ")
        assert roast.micro_action == f"{voice.gentle_action_frame} {direct.micro_action}"
        assert not any(sharp in roast.thesis or sharp in roast.micro_action for sharp in SHARP_ONLY)
        # The direct placement sentence is kept rather than its sharper roast.
        assert direct.thesis in roast.thesis


def test_unmatched_ai_or_natal_text_passes_through_unchanged() -> None:
    rewritten = DailySections(
        "Một câu do bản viết lại tạo ra.",
        "Một luận điểm khác với ma trận đã duyệt.",
        "Khi đọc một đoạn khác, bạn có thể nghĩ khác.",
        "Ghi một việc nhỏ khác với hành động đã duyệt.",
    )

    assert roast_daily_sections(rewritten) == rewritten
    assert roast_legacy_text("Đừng vội rep.") == "Đừng vội rep."


def _content(sections: DailySections, *, purpose: ReadingPurpose) -> ReadingContentProjection:
    revision_id = uuid4()
    return ReadingContentProjection(
        revision_id=revision_id,
        source=ReadingRevisionSource.DETERMINISTIC,
        mode=PlanMode.FULL_SYNTHESIS,
        purpose=purpose,
        tradition=Tradition.WESTERN,
        precision=TimePrecision.EXACT,
        sections=ReadingSectionsProjection(
            hook=sections.hook,
            thesis=sections.thesis,
            manifestation=sections.manifestation,
            transit=None,
            micro_action=sections.micro_action,
        ),
        evidence=ReadingEvidenceProjection(
            title="Căn cứ",
            claims=("Mặt Trời ở Ma Kết",),
            framework_disclosure="Chiêm tinh là một khung tham khảo.",
        ),
        disclaimer="Đây là một góc tự soi, không thay cho quyết định của bạn.",
        created_at=datetime(2026, 10, 11, tzinfo=UTC),
        experiment=experiment_projection_for(revision_id, sections.micro_action),
    )


def test_projection_voice_changes_wording_only_and_keeps_action_key() -> None:
    direct = _content(
        _sections_for("missing-context", arena=SemanticArena.COMMUNICATION),
        purpose=ReadingPurpose.DAILY_NOTE,
    )
    roast = apply_content_voice(direct, ReadingVoice.ROAST)

    assert apply_content_voice(direct, ReadingVoice.DIRECT) is direct
    assert roast.sections.hook != direct.sections.hook
    assert roast.evidence == direct.evidence
    assert roast.disclaimer == direct.disclaimer
    assert roast.revision_id == direct.revision_id
    assert roast.experiment is not None and direct.experiment is not None
    assert roast.experiment.action_key == direct.experiment.action_key
    assert roast.experiment.action == roast.sections.micro_action
    assert roast.experiment.action.endswith(direct.experiment.action)

    natal = _content(
        _sections_for("missing-context", arena=None), purpose=ReadingPurpose.READING_DETAIL
    )
    assert apply_content_voice(natal, ReadingVoice.ROAST) is natal


def _fold(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", value.casefold())
        if unicodedata.category(char) != "Mn"
    )


def test_rendered_daily_cards_are_all_voiced_and_pass_content_review() -> None:
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    samples: list[ReviewSample] = []
    seen: set[str] = set()
    for index, sign in enumerate(ZodiacSign):
        for lens in BackgroundLens:
            chart = _date_only(sign) if index % 2 == 0 else _full_chart(index % 10)
            plan = planner.plan(
                chart,
                purpose=ReadingPurpose.DAILY_NOTE,
                background_lens=lens,
                editorial_seed=(date(2026, 10, 11) + timedelta(days=index)).isoformat(),
            )
            candidate = renderer.render(plan)
            direct = DailySections(
                candidate.hook, candidate.thesis, candidate.manifestation, candidate.micro_action
            )
            roast = roast_daily_sections(direct)
            assert roast.hook != direct.hook
            assert roast.micro_action.endswith(direct.micro_action)
            assert direct.manifestation in roast.manifestation
            fingerprint = f"{roast.manifestation}|{roast.micro_action}"
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            samples.append(
                ReviewSample(
                    persona_id=f"roast-{len(samples)}",
                    surface="daily",
                    sections=(
                        ("hook", roast.hook),
                        ("thesis", roast.thesis),
                        ("scene", roast.manifestation),
                        ("action", roast.micro_action),
                    ),
                    disclaimer=candidate.disclaimer,
                    provenance_ids=tuple(claim.factor_ref for claim in candidate.evidence.claims),
                    evidence_validated=True,
                )
            )

    result = ContentReviewAgent().review(tuple(samples))
    assert result.passed, result.findings
    assert not any("chac chan se" in _fold(sample.sections[1][1]) for sample in samples)


def test_scene_tags_never_add_advice_inside_the_scene() -> None:
    for voice in ROAST_ISSUES.values():
        tag = voice.scene_tag.casefold()
        assert not any(_contains_word(tag, word) for word in ("hãy", "thử", "nên", "đừng")), tag
