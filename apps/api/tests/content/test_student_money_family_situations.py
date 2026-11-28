"""Student Daily bundles on tight money and family pressure (#705). Synthetic inputs only.

Editorial groups describe the copy, never the reader: nothing is collected or inferred about
who reads these cards. Approving any part requires the whole bundle and both frozen light slots
together, the same gate #704 set for its four bundles.

AC2 is checked as text rules: money copy never names an amount and never says who is short;
family copy never treats the family as a support and every family action keeps a way out
(it can be done alone, and it says nothing has to be promised yet).

Both family stories live in capacity-before-agreement (#952 review, finding
952-family-companion-exit). Each issue has one companion line per voice and no per-bundle
companion exists, so a family card shows its issue's line. The avoid-small-conflict and
automatic-caretaking lines push the reader to refuse or to speak up, which cancels the way out.
The capacity lines only ask the reader to look at the calendar first. The whole-card test below
fails if a family story moves to an issue whose companion, action or light slot pushes contact.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import timedelta
from itertools import combinations
from uuid import UUID

import pytest

from app.domains.astro.models import TimePrecision
from app.domains.content import copy_approval
from app.domains.content.copy_approval import (
    BUNDLE_PARTS,
    REGISTRY_PATH,
    CopyEntry,
    approved_bundles,
    copy_digest,
    load_registry,
    parse_registry,
    registry_problems,
)
from app.domains.content_rewrite.gates import evaluate_daily_rewrite
from app.domains.readings import action_tags, companion_pool, daily_psychology, lighter_action
from app.domains.readings.action_tags import ActionTag
from app.domains.readings.application import _companion_line
from app.domains.readings.companion import COMPANION_ISSUE_LINES
from app.domains.readings.daily_personalization import (
    PAIR_RULES,
    PLACEMENT_MEANINGS,
    SupportedSituation,
    eligible_daily_situations,
)
from app.domains.readings.daily_psychology import DAILY_ISSUES, lead_scene
from app.domains.readings.gates import has_observable_action
from app.domains.readings.lighter_action import (
    ACTION_SHAPES,
    light_slots,
    lighter_action_for,
    within_five_minutes,
)
from app.domains.readings.models import (
    LIGHTER_ACTION_MAX_CHARS,
    BackgroundLens,
    DerivedFactor,
    FactorConfidence,
    FactorKind,
    FactorRole,
    PlanMode,
    ReadingDomain,
    ReadingPurpose,
    SemanticArena,
)
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.student_support import needs_contact
from app.domains.readings.voice import DailySections, ReadingVoice, apply_content_voice
from scripts.persona_metrics import light_by_rule
from tests.content.test_daily_variants import (
    _check_action,
    _check_clarity,
    _check_headline,
    _check_scene,
    _check_scene_anchor,
)
from tests.readings.test_daily_rotation import OWNER_A, START, _date_only_plan, _variety
from tests.readings.test_voice import _content

# bundle id -> (editorial group, normal picture group, light picture groups in frozen order)
BUNDLES = {
    "daily.bundle.comparison-loop.13": ("money_tight", "study_work", ("boundary", "study_work")),
    "daily.bundle.group-pressure.13": ("money_tight", "money", ("rest", "boundary")),
    "daily.bundle.capacity-before-agreement.13": (
        "family_pressure",
        "boundary",
        ("boundary", "rest"),
    ),
    "daily.bundle.capacity-before-agreement.14": (
        "family_pressure",
        "study_work",
        ("boundary", "rest"),
    ),
}
FAMILY_ISSUE = "capacity-before-agreement"
MONEY = tuple(bundle for bundle, value in BUNDLES.items() if value[0] == "money_tight")
FAMILY = tuple(bundle for bundle, value in BUNDLES.items() if value[0] == "family_pressure")
ISSUES = {issue.key: issue for issue in DAILY_ISSUES}
REVISIONS = tuple(UUID(int=n) for n in range(1, 65))

# AC2 text rules. Each list is the plain words a line would need to break the rule.
_AMOUNT = re.compile(
    r"\d|bao nhiêu|số tiền|giá tiền|nghìn|ngàn|triệu|trăm|\bk\b|vnđ|\bđồng\b(?! ý)"
)
_SHORT_OF_MONEY = re.compile(
    r"thiếu tiền|hết tiền|cạn tiền|không đủ tiền|không có tiền|nghèo|túng|eo hẹp|"
    r"mua nổi|không đủ sức mua|chật vật"
)
# Góc Tiền bạc (#710, stories defined in #709) owns these four; Daily must not repeat them.
_MONEY_CORNER_STORIES = re.compile(
    r"học phí|tiền nhà|tiền phòng|tiền trọ|cuối tháng|gửi tiền|gửi về|đi chơi|rủ đi"
)
_FAMILY_AS_SUPPORT = re.compile(
    r"chỗ dựa|dựa vào|ủng hộ bạn|luôn bên|luôn thương|hiểu bạn|giúp bạn|chia sẻ với"
)
# The way out ("lối lui"): nothing has to be promised to the family yet.
_WAY_OUT = re.compile(r"chưa cần hứa")
# Lines that push the reader to refuse or to speak up; on a family card they cancel the way out.
_PUSH_TO_SPEAK = re.compile(r"từ chối|nói thật|nói thẳng|nói rõ|nói bấy nhiêu|nói không")


def _keeps_way_out(text: str) -> bool:
    return not needs_contact(text) and not _PUSH_TO_SPEAK.search(text.lower())


def _issue(bundle: str) -> str:
    return bundle.split(".")[2]


def _light_ids(bundle: str) -> tuple[str, str]:
    prefix = f"lighter.issue.{_issue(bundle)}"
    return f"{prefix}.01", f"{prefix}.02"


def _keys(bundle: str) -> tuple[str, ...]:
    return (*(f"{bundle}.{part}" for part in BUNDLE_PARTS), *_light_ids(bundle))


def _texts(bundle: str) -> dict[str, str]:
    entries = load_registry()
    return {part: entries[f"{bundle}.{part}"].text for part in BUNDLE_PARTS}


def _meaning(issue: str) -> str:
    if issue in PLACEMENT_MEANINGS:
        return PLACEMENT_MEANINGS[issue]
    # comparison-loop has no placement of its own; its tendency comes from the Sun-Saturn rule.
    return next(rule.tension_meaning for rule in PAIR_RULES if rule.tension_issue == issue)


def _approved(entry: CopyEntry) -> CopyEntry:
    return replace(
        entry,
        status="approved",
        approver="codex",
        date="2026-11-28",
        digest=copy_digest(entry.text),
    )


def _pending_registry() -> dict[str, CopyEntry]:
    entries = load_registry()
    for bundle in BUNDLES:
        for key in _keys(bundle):
            entries[key] = replace(
                entries[key], status="pending", approver=None, date=None, digest=None
            )
    return entries


def _approve(entries: dict[str, CopyEntry], bundle: str) -> None:
    for key in _keys(bundle):
        entries[key] = _approved(entries[key])


def _assert_unlock(entries: dict[str, CopyEntry], monkeypatch: pytest.MonkeyPatch) -> None:
    assert registry_problems(entries) == []
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: entries)
    # Light slots belong to the issue; an approved sibling bundle may already have unlocked them.
    lit = {
        _issue(bundle)
        for bundle in BUNDLES
        for part in BUNDLE_PARTS
        if (entry := entries.get(f"{bundle}.{part}")) is not None and entry.servable
    }
    for bundle, (_group, shape, light_shapes) in BUNDLES.items():
        part_ids = tuple(f"{bundle}.{part}" for part in BUNDLE_PARTS)
        assert all(key in entries for key in part_ids), f"{bundle}: missing part"
        action_id = f"{bundle}.action"
        assert action_tags.normal_tags().get(action_id) == (
            copy_digest(entries[action_id].text),
            shape,
        )
        assert action_tags.tag_of(action_id, (_issue(bundle),)) == ActionTag("normal", shape)
        if not any(entries[key].servable for key in part_ids):
            for key in _light_ids(bundle):
                assert key in entries, f"{bundle}: missing light slot"
                if _issue(bundle) not in lit:
                    assert not entries[key].servable, f"{key}: light slot approved without bundle"
            continue
        assert all(entries[key].servable for key in part_ids), f"{bundle}: partial approval"
        slots = light_slots(_issue(bundle))
        assert tuple(key for key, _digest, _shape in slots) == _light_ids(bundle)
        assert tuple(slot_shape for _key, _digest, slot_shape in slots) == light_shapes
        for key, digest, slot_shape in slots:
            assert key in entries, f"{bundle}: missing light slot"
            assert entries[key].servable, f"{key}: light slot not servable"
            assert copy_digest(entries[key].text) == digest, f"{key}: frozen digest mismatch"
            assert slot_shape in ACTION_SHAPES
            assert action_tags.tag_of(key, (_issue(bundle),)) == ActionTag("light", slot_shape)
        expected = {entries[key].text for key in _light_ids(bundle)}
        offered = {
            lighter_action_for(revision, f"psychology:{_issue(bundle)}") for revision in REVISIONS
        }
        assert offered == expected, f"{bundle}: both light slots must pass runtime"


def test_batch_is_pending_before_editorial_approval() -> None:
    """AC3. Replace this pre-approval check only in the PR carrying the review receipt."""
    entries = load_registry()
    for bundle in BUNDLES:
        for key in _keys(bundle):
            entry = entries[key]
            assert entry.status == "pending", key
            assert entry.approver is entry.date is entry.digest is None, key
            assert not entry.servable, key


def test_inventory_required_fields_tags_and_light_slots() -> None:
    """AC1. Each bundle is a whole situation with a normal action and two light actions."""
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entries = parse_registry(raw)  # Also rejects duplicate IDs and missing/non-string fields.
    assert registry_problems(entries) == []
    assert len(MONEY) == len(FAMILY) == 2
    assert len({_issue(bundle) for bundle in MONEY}) == len(MONEY)
    assert {_issue(bundle) for bundle in FAMILY} == {FAMILY_ISSUE}
    for bundle, (_group, shape, light_shapes) in BUNDLES.items():
        for part in BUNDLE_PARTS:
            key = f"{bundle}.{part}"
            assert key in entries
            assert entries[key].id == key and entries[key].category == "reading"
            if part in ("headline", "scene"):
                assert entries[key].text.startswith("Khi "), key
            _check_clarity(key, entries[key].text)
        _check_headline(f"{bundle}.headline", entries[f"{bundle}.headline"].text)
        _check_scene(f"{bundle}.scene", entries[f"{bundle}.scene"].text)
        _check_scene_anchor(f"{bundle}.scene", entries[f"{bundle}.scene"].text)
        _check_action(f"{bundle}.action", entries[f"{bundle}.action"].text)
        assert has_observable_action(entries[f"{bundle}.action"].text)
        assert action_tags.normal_tags()[f"{bundle}.action"] == (
            copy_digest(entries[f"{bundle}.action"].text),
            shape,
        )
        assert action_tags.tag_of(f"{bundle}.action", (_issue(bundle),)) == ActionTag(
            "normal", shape
        )
        slots = light_slots(_issue(bundle))
        assert tuple(key for key, _digest, _shape in slots) == _light_ids(bundle)
        assert tuple(slot_shape for _key, _digest, slot_shape in slots) == light_shapes
        for key, digest, slot_shape in slots:
            assert entries[key].category == "reading"
            text = entries[key].text
            _check_clarity(key, text)
            assert len(text) <= LIGHTER_ACTION_MAX_CHARS
            assert has_observable_action(text), key
            assert light_by_rule(text) and within_five_minutes(text), key
            assert copy_digest(entries[key].text) == digest
            assert slot_shape in ACTION_SHAPES
            assert action_tags.tag_of(key, (_issue(bundle),)) == ActionTag("light", slot_shape)


@pytest.mark.parametrize("bundle", MONEY)
def test_money_copy_names_no_amount_and_no_one_short(bundle: str) -> None:
    """AC2. No amount is asked or named, no one is assumed short, #710's stories stay there."""
    for part, text in _texts(bundle).items():
        folded = text.lower()
        assert not _AMOUNT.search(folded), (bundle, part, text)
        assert not _SHORT_OF_MONEY.search(folded), (bundle, part, text)
        assert not _MONEY_CORNER_STORIES.search(folded), (bundle, part, text)


@pytest.mark.parametrize("bundle", FAMILY)
def test_family_copy_keeps_a_way_out_and_never_assumes_support(bundle: str) -> None:
    """AC2. The family is never framed as a support; the action is doable alone, with a way out."""
    texts = _texts(bundle)
    assert "gia đình" in texts["scene"]
    for part, text in texts.items():
        assert not _FAMILY_AS_SUPPORT.search(text.lower()), (bundle, part, text)
    assert _WAY_OUT.search(texts["action"]), bundle
    # Doable without reaching anyone, so the reader is never pushed to talk to the family.
    assert not needs_contact(texts["action"]), bundle


@pytest.mark.parametrize("voice", ReadingVoice)
@pytest.mark.parametrize("bundle", FAMILY)
def test_family_card_keeps_the_way_out_in_every_line(bundle: str, voice: ReadingVoice) -> None:
    """#952 review: the companion and the light slots must not cancel the action's way out."""
    entries = load_registry()
    issue = _issue(bundle)
    lines = {
        "action": entries[f"{bundle}.action"].text,
        "companion": getattr(COMPANION_ISSUE_LINES[issue].line, voice.value),
        **{key: entries[key].text for key in _light_ids(bundle)},
    }
    for name, text in lines.items():
        assert _keeps_way_out(text), (bundle, voice.value, name, text)


@pytest.mark.parametrize(
    "text",
    (
        # The companions this batch first used (avoid-small-conflict, automatic-caretaking).
        "Từ chối nhẹ nhàng vẫn là từ chối. Bạn làm được.",
        "Chữ được bật ra nhanh ghê. Lần này thử nói thật xem.",
        "Giúp được bao nhiêu thì nói bấy nhiêu, vậy là đủ.",
        "Nói thẳng với gia đình là tối nay bạn bận.",
    ),
)
def test_way_out_rule_rejects_lines_that_push_refusal_or_contact(text: str) -> None:
    assert not _keeps_way_out(text)


@pytest.mark.parametrize(
    "text",
    (
        "Ghi số tiền bạn còn lại tuần này trước khi mua áo lớp.",
        "Hỏi lớp trưởng áo lớp giá bao nhiêu.",
        "Khi bạn hết tiền mà nhóm lớp vẫn đặt áo.",
        "Khi bạn không mua nổi máy mới như người khác.",
        "Khi tới hạn đóng học phí mà bạn chưa đủ.",
    ),
)
def test_money_rules_reject_amounts_and_shortage(text: str) -> None:
    folded = text.lower()
    assert (
        _AMOUNT.search(folded)
        or _SHORT_OF_MONEY.search(folded)
        or _MONEY_CORNER_STORIES.search(folded)
    )


@pytest.mark.parametrize(
    "text",
    (
        "Nhắn gia đình là bạn chỉ kèm em được hai tối.",
        "Nói với gia đình phần bạn làm được, chưa cần hứa thêm.",
        "Ghi phần bạn làm được rồi gửi cho gia đình.",
        "Ghi phần bạn làm được, gia đình luôn bên bạn.",
        "Ghi riêng phần bạn làm được và phần không tiện.",
    ),
)
def test_family_rules_reject_contact_support_or_no_way_out(text: str) -> None:
    assert (
        needs_contact(text) or _FAMILY_AS_SUPPORT.search(text.lower()) or not _WAY_OUT.search(text)
    )


def test_unlock_gate_on_checked_in_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    _assert_unlock(load_registry(), monkeypatch)


def test_unservable_parts_never_enter_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = load_registry()
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: entries)
    for bundle in BUNDLES:
        parts = [entries[f"{bundle}.{part}"] for part in BUNDLE_PARTS]
        assert all(entry.status == "pending" and not entry.servable for entry in parts)
        assert tuple(entry.text for entry in parts) not in approved_bundles(_issue(bundle))
        for entry in parts:
            assert copy_approval.approved_copy(entry.id) is None
        for key in _light_ids(bundle):
            assert copy_approval.approved_copy(key) is None


@pytest.mark.parametrize("bundle", BUNDLES)
def test_one_complete_bundle_unlocks_without_the_others(
    bundle: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    _approve(entries, bundle)
    _assert_unlock(entries, monkeypatch)
    assert tuple(entries[f"{bundle}.{part}"].text for part in BUNDLE_PARTS) in approved_bundles(
        _issue(bundle)
    )


@pytest.mark.parametrize("bundle", BUNDLES)
@pytest.mark.parametrize(
    "parts", [parts for count in (1, 2) for parts in combinations(BUNDLE_PARTS, count)]
)
def test_gate_rejects_partial_bundle_approval(
    bundle: str,
    parts: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    for part in parts:
        entries[f"{bundle}.{part}"] = _approved(entries[f"{bundle}.{part}"])
    with pytest.raises(AssertionError, match="partial approval"):
        _assert_unlock(entries, monkeypatch)


@pytest.mark.parametrize("bundle", BUNDLES)
@pytest.mark.parametrize("slot", (0, 1))
@pytest.mark.parametrize("failure", ("approved", "missing"))
def test_gate_rejects_light_slot_changes_while_bundle_is_pending(
    bundle: str,
    slot: int,
    failure: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    key = _light_ids(bundle)[slot]
    if failure == "approved":
        entries[key] = _approved(entries[key])
    else:
        del entries[key]
    with pytest.raises(AssertionError, match="light slot"):
        _assert_unlock(entries, monkeypatch)


@pytest.mark.parametrize("bundle", BUNDLES)
@pytest.mark.parametrize("slot", (0, 1))
@pytest.mark.parametrize("failure", ("pending", "missing", "edited"))
def test_gate_rejects_unavailable_or_reworded_light_slot(
    bundle: str,
    slot: int,
    failure: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    _approve(entries, bundle)
    key = _light_ids(bundle)[slot]
    if failure == "pending":
        entries[key] = replace(entries[key], status="pending")
    elif failure == "missing":
        del entries[key]
    else:
        entries[key] = _approved(replace(entries[key], text="Ngồi yên một phút rồi thở chậm."))
        assert entries[key].servable  # Fresh approval cannot bypass the frozen catalog.
    with pytest.raises(AssertionError, match=r"light slot|frozen digest"):
        _assert_unlock(entries, monkeypatch)


@pytest.mark.parametrize("bundle", BUNDLES)
@pytest.mark.parametrize("part", BUNDLE_PARTS)
def test_gate_rejects_missing_bundle_part(
    bundle: str, part: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = _pending_registry()
    del entries[f"{bundle}.{part}"]
    with pytest.raises(AssertionError):
        _assert_unlock(entries, monkeypatch)


@pytest.mark.parametrize("field", ("digest", "approver", "date", "status"))
def test_registry_gate_rejects_invalid_approval_even_when_not_servable(
    field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    key = "daily.bundle.group-pressure.13.action"
    valid = _approved(entries[key])
    entries[key] = {
        "digest": replace(valid, digest="0" * 64),
        "approver": replace(valid, approver=None),
        "date": replace(valid, date=None),
        "status": replace(valid, status="ready"),
    }[field]
    assert not entries[key].servable
    assert registry_problems(entries)
    with pytest.raises(AssertionError):
        _assert_unlock(entries, monkeypatch)


@pytest.mark.parametrize("bundle", BUNDLES)
@pytest.mark.parametrize("failure", ("missing", "shape", "digest", "weight"))
def test_gate_rejects_invalid_normal_action_tag(
    bundle: str, failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = _pending_registry()
    key = f"{bundle}.action"
    tags = dict(action_tags.normal_tags())
    if failure == "missing":
        del tags[key]
    elif failure == "shape":
        tags[key] = (tags[key][0], "connection")
    elif failure == "digest":
        tags[key] = ("0" * 64, tags[key][1])
    else:
        original = action_tags.tag_of
        monkeypatch.setattr(
            action_tags,
            "tag_of",
            lambda entry_id, issues: (
                ActionTag("light", "boundary") if entry_id == key else original(entry_id, issues)
            ),
        )
    monkeypatch.setattr(action_tags, "normal_tags", lambda: tags)
    with pytest.raises(AssertionError):
        _assert_unlock(entries, monkeypatch)


@pytest.mark.parametrize("failure", ("missing", "shape", "weight"))
def test_gate_rejects_broken_light_catalog(failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
    entries = _pending_registry()
    bundle = "daily.bundle.capacity-before-agreement.13"
    _approve(entries, bundle)
    catalog = dict(lighter_action.ISSUE_LIGHT_CATALOG)
    slots = catalog[FAMILY_ISSUE]
    if failure == "weight":
        original = action_tags.tag_of
        key = _light_ids(bundle)[0]
        monkeypatch.setattr(
            action_tags,
            "tag_of",
            lambda entry_id, issues: (
                ActionTag("normal", "rest") if entry_id == key else original(entry_id, issues)
            ),
        )
    else:
        catalog[FAMILY_ISSUE] = (
            slots[:1]
            if failure == "missing"
            else ((slots[0][0], slots[0][1], "connection"), slots[1])
        )
    monkeypatch.setattr(lighter_action, "ISSUE_LIGHT_CATALOG", catalog)
    with pytest.raises(AssertionError):
        _assert_unlock(entries, monkeypatch)


@pytest.mark.parametrize(
    "bundle,arena,voice",
    [
        (bundle, arena, voice)
        for bundle in BUNDLES
        for arena in (SemanticArena.GENERAL, *ISSUES[_issue(bundle)].arenas)
        for voice in ReadingVoice
    ],
)
def test_card_renders_whole_in_each_arena_voice_and_light_slot(
    bundle: str,
    arena: SemanticArena,
    voice: ReadingVoice,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _pending_registry()
    _approve(entries, bundle)
    # Isolate this bundle so the real selector has to pick it, without changing production copy.
    selected = {
        key: entry
        for key, entry in entries.items()
        if key.startswith(f"{bundle}.") or key in _light_ids(bundle)
    }
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: selected)
    issue = _issue(bundle)
    supported = SupportedSituation(
        issue_key=issue,
        meaning=_meaning(issue),
        factor_refs=(),
        rule_key="student-fixture",
        rank=(1, 0, 0),
    )
    monkeypatch.setattr(daily_psychology, "eligible_daily_situations", lambda _plan: (supported,))
    lens = None if arena is SemanticArena.GENERAL else BackgroundLens(arena.value)
    plan = _date_only_plan(None).model_copy(update={"background_lens": lens})
    candidate = DeterministicVietnameseRenderer().render(plan)
    headline, scene, action = (entries[f"{bundle}.{part}"].text for part in BUNDLE_PARTS)
    lead = daily_psychology._ARENA_LEADS.get(arena)
    assert (candidate.hook, candidate.manifestation, candidate.micro_action) == (
        headline,
        lead_scene(lead, scene) if lead else scene,
        action,
    )
    blueprint = candidate.semantic_blueprint
    assert blueprint is not None and blueprint.daily_meaning is not None
    assert blueprint.scene_key == blueprint.action_key == f"psychology:{issue}:bundle-0"
    assert blueprint.daily_meaning.observation_question == ISSUES[issue].observation_question
    assert blueprint.daily_meaning.reader_takeaway == ISSUES[issue].takeaway
    assert blueprint.daily_meaning.core_meaning.endswith(ISSUES[issue].meaning)
    assert candidate.companion is candidate.companion_roast is None
    assert companion_pool.EXTRA_LINE_SELECTION_ENABLED is False
    companion = _companion_line(candidate, ReadingPurpose.DAILY_NOTE)
    assert companion == COMPANION_ISSUE_LINES[issue].line.direct
    content = _content(
        DailySections(candidate.hook, candidate.thesis, candidate.manifestation, action),
        purpose=ReadingPurpose.DAILY_NOTE,
    )
    content = content.model_copy(
        update={"sections": content.sections.model_copy(update={"companion": companion})}
    )
    shown = apply_content_voice(content, voice).sections
    assert (shown.hook, shown.manifestation, shown.micro_action) == (
        headline,
        candidate.manifestation,
        action,
    )
    assert shown.companion == getattr(COMPANION_ISSUE_LINES[issue].line, voice.value)
    assert shown.companion is not None
    report = evaluate_daily_rewrite(
        {
            "title": shown.hook,
            "scene": shown.manifestation,
            "action": action,
            "companion": shown.companion,
        },
        meaning_brief=blueprint.daily_meaning,
        companion_brief=COMPANION_ISSUE_LINES[issue],
    )
    assert report.failure_codes == ROAST_OFF_BRIEF.get((issue, voice), ())
    assert report.passed is (not report.failure_codes)
    offered = {lighter_action_for(revision, blueprint.mechanism_key) for revision in REVISIONS}
    assert offered == {entries[key].text for key in _light_ids(bundle)}
    if bundle in FAMILY:
        # #952 review: the card as shown, companion included, keeps the way out in this voice.
        for text in (action, shown.companion, *(entries[key].text for key in _light_ids(bundle))):
            assert _keeps_way_out(text), (bundle, voice.value, text)


# Luna's gate requires the direct nudge; these authored roast lines use other wording and
# voice.py serves the authored card without sending it through Luna (same as #704).
ROAST_OFF_BRIEF: dict[tuple[str, ReadingVoice], tuple[str, ...]] = {}


# Synthetic Sun placements that select each issue through real eligibility.
PLACEMENTS = {
    "group-pressure": ("sun", "aquarius", ReadingDomain.CORE),
    FAMILY_ISSUE: ("sun", "capricorn", ReadingDomain.CORE),
}


@pytest.mark.parametrize("bundle", BUNDLES)
def test_bundle_rotates_with_every_bundle_of_its_issue(
    bundle: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = load_registry()
    issue = _issue(bundle)
    numbers = sorted(
        int(key.split(".")[3])
        for key in entries
        if key.startswith(f"daily.bundle.{issue}.") and key.endswith(".headline")
    )
    # 12 older bundles, plus this batch's one (money) or two (family) bundles.
    assert numbers == list(range(1, 15 if issue == FAMILY_ISSUE else 14))
    for number in numbers:
        for part in BUNDLE_PARTS:
            key = f"daily.bundle.{issue}.{number:02d}.{part}"
            entries[key] = _approved(entries[key])
    _approve(entries, bundle)
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: entries)
    expected = {
        tuple(entries[f"daily.bundle.{issue}.{number:02d}.{part}"].text for part in BUNDLE_PARTS)
        for number in numbers
    }
    cycle = len(numbers)
    assert len(approved_bundles(issue)) == len(expected) == cycle
    template = _date_only_plan(None)
    body, sign, domain = PLACEMENTS.get(issue, ("sun", "virgo", ReadingDomain.CORE))
    factor = DerivedFactor.model_validate(
        {
            **template.factors[0].model_dump(),
            "id": f"natal:{body}:sign:{sign}",
            "kind": FactorKind.PLANET_PLACEMENT,
            "domain": domain,
            "subjects": (body,),
            "role": FactorRole.PRIMARY,
            "confidence": FactorConfidence.HIGH,
            "evidence_refs": (f"natal:{body}:longitude",),
        }
    )
    if issue not in PLACEMENTS:
        # comparison-loop is reached only through pair angles; pin the situation instead.
        supported = SupportedSituation(
            issue_key=issue,
            meaning=_meaning(issue),
            factor_refs=(factor.id,),
            rule_key="student-fixture",
            rank=(2, 0, 0),
        )
        monkeypatch.setattr(
            daily_psychology, "eligible_daily_situations", lambda _plan: (supported,)
        )
    observed = []
    cycle_start = START - timedelta(days=_variety(OWNER_A, START).day_index % cycle)
    for day in range(cycle):
        plan = template.model_copy(
            update={
                "factors": (factor,),
                "hero_factor_refs": (factor.id,),
                "mode": PlanMode.FULL_SYNTHESIS,
                "precision": TimePrecision.EXACT,
                "daily_variety": _variety(OWNER_A, cycle_start + timedelta(days=day)),
            }
        )
        if issue in PLACEMENTS:
            assert {s.issue_key for s in eligible_daily_situations(plan)} == {issue}
        candidate = DeterministicVietnameseRenderer().render(plan)
        observed.append((candidate.hook, candidate.manifestation, candidate.micro_action))
        assert candidate.semantic_blueprint is not None
        assert candidate.semantic_blueprint.mechanism_key == f"psychology:{issue}"
    assert len(set(observed)) == cycle
    assert set(observed) == expected
