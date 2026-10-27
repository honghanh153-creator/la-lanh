"""B2-4a: per-session variants, question-specific role sentences, Roast frames, versions.

US-20 AC15, AC16, AC17, AC18, AC19. Task: docs/plans/2026-10-18-b2-4-tarot-variety-roast-task.md.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import string
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import delete, select

from app.db.session import Database
from app.domains.guest.tables import GuestSessionRow
from app.domains.readings.review_agent import ContentReviewAgent
from app.domains.tarot import roles, stance
from app.domains.tarot.engine import (
    _POSITIONS,
    FRAMED_KNOWLEDGE_VERSION,
    FRAMED_RENDERER_VERSION,
    LEGACY_RENDERER_VERSION,
    TAROT_GATE_VERSION,
    TarotContentRejected,
    TarotReadingEngine,
    _CardMeaning,
    _position_views,
    _resource_step,
    _tension_parts,
    current_renderer_version,
)
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import (
    QUESTION_RULES_VERSION,
    TarotContext,
    TarotOrigin,
    TarotQuestionForm,
    TarotReading,
    TarotReadingProvenance,
    TarotSessionView,
    TarotSpread,
    TarotSpreadMap,
    TarotStanceLevel,
    TarotVoice,
)
from app.domains.tarot.service import TarotSessionService
from app.domains.tarot.tables import TarotSessionRow, TarotVariantCursorRow
from app.domains.tarot.variants import (
    DEFAULT_VARIANTS,
    HEADLINE_VARIANTS,
    TAROT_VARIANT_CATALOG_VERSION,
    TarotVariants,
    choose_variants,
    stored_variants,
    tarot_variety_seed,
)
from app.domains.tarot.voice import GENTLE_CONTEXTS, GENTLE_MEANING_TAILS, ROAST_MEANING_TAILS
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

ENGINE = TarotReadingEngine()
CARDS = [card.id for card in all_cards()]
SPREAD = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
KEY = b"k" * 32
OTHER_KEY = b"o" * 32
YES_NO = "Mình có nên nhận thêm việc ở chỗ làm không?"
FORMS = {
    TarotQuestionForm.YES_NO: YES_NO,
    TarotQuestionForm.HOW: "Làm thế nào để mình chia việc rõ hơn với nhóm?",
    TarotQuestionForm.WHY: "Vì sao mình hay ôm việc của người khác?",
    TarotQuestionForm.OPEN: "Mình cần nhìn rõ điều gì trong công việc lúc này?",
    TarotQuestionForm.TIMING: "Khi nào mình nên nghỉ việc?",
}
CIPHER = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"r" * 32))
HASHER = SecretHasher(b"synthetic-hash-key" * 2)


def _render(
    question: str,
    spread_map: TarotSpreadMap,
    *,
    context: TarotContext = TarotContext.WORK,
    voice: TarotVoice = TarotVoice.PLAYFUL_GROUNDED,
    variants: TarotVariants | None = None,
    offset: int = 0,
) -> TarotReading:
    assessment = ENGINE.assess_question(question, context)
    assert assessment.accepted and assessment.frame is not None
    count = len(_POSITIONS[spread_map])
    return ENGINE.render(
        card_ids=tuple(CARDS[(offset + 7 * i) % 78] for i in range(count)),
        spread=SPREAD[count],
        spread_map=spread_map,
        context=context,
        question=question,
        voice=voice,
        question_intent=assessment.intent,
        frame=assessment.frame,
        variants=variants,
    )


# ---------------------------------------------------------------- AC15 selection (pure)


def test_ac15_selection_is_deterministic_and_keyed_by_owner_and_catalog() -> None:
    guest = uuid4()
    keys = ("clear", "missed", "next")
    first = choose_variants(KEY, guest, 4, keys)
    assert first == choose_variants(KEY, guest, 4, keys)
    assert set(first.frames) == set(keys) and set(first.scenes) == set(keys)
    assert all(index == 0 for index in first.scenes.values())  # one scene per card x topic
    seed = tarot_variety_seed(KEY, guest, TAROT_VARIANT_CATALOG_VERSION)
    assert seed != tarot_variety_seed(KEY, uuid4(), TAROT_VARIANT_CATALOG_VERSION)
    assert seed != tarot_variety_seed(OTHER_KEY, guest, TAROT_VARIANT_CATALOG_VERSION)
    assert seed != tarot_variety_seed(KEY, guest, "tarot-variant-catalog-v2")
    assert choose_variants(None, guest, 4, keys) == DEFAULT_VARIANTS


def test_ac15_consecutive_sessions_differ_on_every_axis() -> None:
    guest = uuid4()
    keys = tuple(key for key, _ in _POSITIONS[TarotSpreadMap.FIVE_CHOICE])
    chosen = [choose_variants(KEY, guest, position, keys) for position in range(30)]
    for before, after in itertools.pairwise(chosen):
        assert before.lead != after.lead and before.headline != after.headline
        assert all(before.frame(key) != after.frame(key) for key in keys)
    # Every value appears once per cycle.
    assert {variant.headline for variant in chosen[:HEADLINE_VARIANTS]} == {0, 1, 2}
    assert {variant.lead for variant in chosen[: roles.LEAD_VARIANTS]} == set(range(5))


def test_ac15_stored_record_holds_indices_only_and_fails_loudly_when_malformed() -> None:
    record = choose_variants(KEY, uuid4(), 0, ("focus",)).model_dump(mode="json")
    assert set(record) == {"version", "key_version", "lead", "headline", "frames", "scenes"}
    assert stored_variants({"variants": record}) == TarotVariants.model_validate(record)
    # Only an absent key is the pre-B2-4 case; a full default record (no key, empty maps) replays.
    assert stored_variants({}) == DEFAULT_VARIANTS
    default = json.loads(json.dumps(DEFAULT_VARIANTS.model_dump(mode="json")))
    assert default["frames"] == {} and default["scenes"] == {}
    assert stored_variants({"variants": default}) == DEFAULT_VARIANTS


@pytest.mark.parametrize(
    "broken",
    [
        None,  # present null is not absence
        {},  # present but empty: would invent an all-zero draw
        {"seed": "x"},
        {"version": "unknown-version"},
        "lead=1",
        [0, 1],
    ],
)
def test_ac15_present_malformed_records_fail_instead_of_defaulting(broken: Any) -> None:
    with pytest.raises(ValidationError):
        stored_variants({"variants": broken})


_RECORD = TarotVariants(key_version=1, lead=1, headline=2, frames={"clear": 1}, scenes={"clear": 0})


@pytest.mark.parametrize(
    "change",
    [
        {"version": "tarot-variants-v2"},
        {"version": None},
        {"lead": True},  # bool would coerce to index 1
        {"lead": "1"},
        {"lead": 1.0},
        {"lead": 9},
        {"headline": None},
        {"key_version": -1},
        {"frames": {"clear": True}},
        {"frames": {"clear": "1"}},
        {"frames": {"clear": 3}},
        {"frames": None},
        {"scenes": {"clear": 1}},
        {"extra": 0},
    ],
)
def test_ac15_stored_record_is_strict_about_every_field(change: dict[str, Any]) -> None:
    record = {**_RECORD.model_dump(mode="json"), **change}
    with pytest.raises(ValidationError):
        stored_variants({"variants": record})


@pytest.mark.parametrize(
    "field", ["version", "key_version", "lead", "headline", "frames", "scenes"]
)
def test_ac15_stored_record_needs_all_six_fields(field: str) -> None:
    record = _RECORD.model_dump(mode="json")
    del record[field]
    with pytest.raises(ValidationError):
        stored_variants({"variants": record})


# ---------------------------------------------------------------- AC15 through the service


@pytest.fixture
async def database(tmp_path: Any) -> AsyncIterator[Database]:
    db = Database(f"sqlite+aiosqlite:///{tmp_path / 'tarot-variants.db'}")
    await db.initialize()
    try:
        yield db
    finally:
        await db.dispose()


async def _guest(db: Database) -> UUID:
    guest_id, now = uuid4(), datetime.now(UTC)
    async with db.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id,
                token_hash=guest_id.bytes * 2,
                csrf_hash=b"c" * 32,
                state="active",
                onboarding_status="birth_pending",
                created_at=now,
                last_active_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
    return guest_id


def _service(db: Database, key: bytes | None) -> TarotSessionService:
    return TarotSessionService(db.sessions, CIPHER, HASHER, variety_key=key)


async def _start(
    service: TarotSessionService,
    guest: UUID,
    *,
    question: str = YES_NO,
    voice: TarotVoice = TarotVoice.PLAYFUL_GROUNDED,
    context: TarotContext = TarotContext.WORK,
    idempotency: str = "tarot-variants-start-0000000001",
) -> TarotSessionView:
    return await service.start(
        guest_id=guest,
        context=context,
        question=question,
        spread=TarotSpread.THREE_CARD,
        voice=voice,
        origin=TarotOrigin.DIRECT,
        idempotency_key=idempotency,
    )


async def _complete(service: TarotSessionService, guest: UUID, view: TarotSessionView) -> Any:
    for fan in (3, 30, 60):
        view = await service.select_card(
            guest_id=guest, session_id=view.id, fan_index=fan, expected_version=view.version
        )
    return view


async def _payload(db: Database, service: TarotSessionService, session_id: UUID) -> Any:
    async with db.sessions() as session:
        row = (
            await session.scalars(select(TarotSessionRow).where(TarotSessionRow.id == session_id))
        ).one()
        return service._decrypt(row)


async def test_ac15_variants_are_drawn_at_start_and_replayed_after_key_rotation_and_restart(
    database: Database,
) -> None:
    guest = await _guest(database)
    starting = _service(database, KEY)
    started = await _start(starting, guest)
    payload = await _payload(database, starting, started.id)
    keys = tuple(key for key, _ in _POSITIONS[TarotSpreadMap(payload["spread_map"])])
    assert payload["variants"] == choose_variants(KEY, guest, 0, keys).model_dump(mode="json")

    # The key rotates and the process restarts before the last card: the stored draw wins.
    rotated = _service(database, OTHER_KEY)
    done = await _complete(rotated, guest, started)
    assert done.reading is not None
    stored = await _payload(database, rotated, started.id)
    expected = ENGINE.render(
        card_ids=tuple(stored["deck_order"][i] for i in stored["selected_indices"]),
        spread=TarotSpread.THREE_CARD,
        spread_map=TarotSpreadMap(stored["spread_map"]),
        context=TarotContext.WORK,
        question=YES_NO,
        voice=TarotVoice.PLAYFUL_GROUNDED,
        question_intent=done.reading.question_intent,
        frame=rotated._question_frame(stored),
        variants=TarotVariants.model_validate(payload["variants"]),
    )
    assert done.reading == expected
    assert stored["variants"] == payload["variants"]
    # Reopening (another process, no key at all) returns the reading that was drawn.
    reopened = await _service(database, None).get(guest, started.id)
    assert reopened.reading == done.reading


async def test_ac15_consecutive_sessions_of_a_guest_get_different_variants(
    database: Database,
) -> None:
    guest = await _guest(database)
    service = _service(database, KEY)
    records = []
    for index in range(3):
        view = await _start(service, guest, idempotency=f"tarot-variants-start-000000000{index}")
        records.append(
            TarotVariants.model_validate((await _payload(database, service, view.id))["variants"])
        )
    for before, after in itertools.pairwise(records):
        assert before.headline != after.headline and before.lead != after.lead


async def _cursor(db: Database, guest: UUID) -> int | None:
    async with db.sessions() as session:
        row = await session.get(TarotVariantCursorRow, guest)
        return None if row is None else row.next_position


async def test_ac15_deleting_a_reading_or_cleanup_never_rewinds_the_position(
    database: Database,
) -> None:
    guest = await _guest(database)
    service = _service(database, KEY)
    keys = ("clear", "missed", "next")
    a = await _complete(service, guest, await _start(service, guest, idempotency="cursor-a" * 4))
    b = await _complete(service, guest, await _start(service, guest, idempotency="cursor-b" * 4))
    await service.delete(guest, a.id)
    c = await _complete(service, guest, await _start(service, guest, idempotency="cursor-c" * 4))
    variants = {
        name: (await _payload(database, service, view.id))["variants"]
        for name, view in (("b", b), ("c", c))
    }
    assert variants["b"] == choose_variants(KEY, guest, 1, keys).model_dump(mode="json")
    assert variants["c"] == choose_variants(KEY, guest, 2, keys).model_dump(mode="json")
    assert variants["b"] != variants["c"]
    assert b.reading is not None and c.reading is not None and b.reading != c.reading
    assert await _cursor(database, guest) == 3
    # Retention cleanup removes rows, not the cursor.
    later = datetime.now(UTC) + TarotSessionService.RETENTION_WINDOW + timedelta(minutes=1)
    assert await service.cleanup(now=later) == 2
    d = await _start(service, guest, idempotency="cursor-d" * 4)
    assert (await _payload(database, service, d.id))["variants"] == choose_variants(
        KEY, guest, 3, keys
    ).model_dump(mode="json")
    assert await _cursor(database, guest) == 4


async def test_ac15_replay_allocates_nothing_and_the_cursor_goes_with_the_guest(
    database: Database,
) -> None:
    guest = await _guest(database)
    service = _service(database, KEY)
    first = await _start(service, guest)
    replay = await _start(service, guest)  # same idempotency key and request
    assert replay.id == first.id and await _cursor(database, guest) == 1
    async with database.sessions() as session, session.begin():
        await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guest))
    assert await _cursor(database, guest) is None


async def test_ac15_concurrent_starts_get_distinct_positions(database: Database) -> None:
    guest = await _guest(database)
    service = _service(database, KEY)
    views = await asyncio.gather(
        *(_start(service, guest, idempotency=f"cursor-race-{index:020d}") for index in range(4))
    )
    records = sorted(
        [
            json.dumps((await _payload(database, service, view.id))["variants"], sort_keys=True)
            for view in views
        ]
    )
    keys = ("clear", "missed", "next")
    expected = sorted(
        json.dumps(
            choose_variants(KEY, guest, position, keys).model_dump(mode="json"), sort_keys=True
        )
        for position in range(4)
    )
    assert records == expected and len(set(records)) == 4
    assert await _cursor(database, guest) == 4


async def test_ac15_without_a_key_or_a_record_every_index_is_zero(database: Database) -> None:
    guest = await _guest(database)
    service = _service(database, None)
    view = await _start(service, guest)
    assert (await _payload(database, service, view.id))["variants"] == DEFAULT_VARIANTS.model_dump(
        mode="json"
    )


# ---------------------------------------------------------------- AC16 question-specific text


def test_ac16_same_card_and_role_read_differently_for_each_question_form() -> None:
    texts = {
        form: _render(question, TarotSpreadMap.THREE_UNBLOCK).positions[0].meaning_here
        for form, question in FORMS.items()
    }
    assert len(set(texts.values())) == len(FORMS)  # index-0 variants: only the question differs
    card = _render(YES_NO, TarotSpreadMap.THREE_UNBLOCK).positions[0].card
    core = _CardMeaning.for_context(card, TarotContext.WORK).core
    assert all(core in text for text in texts.values())  # the role still reads its field


def test_ac16_leads_never_repeat_inside_a_reading_and_never_quote_the_question() -> None:
    for lead in range(roles.LEAD_VARIANTS):
        reading = _render(
            YES_NO, TarotSpreadMap.FIVE_CLARITY, variants=TarotVariants(key_version=1, lead=lead)
        )
        leads = [p.meaning_here.split(",")[0] for p in reading.positions]
        assert len(set(leads)) == 5
        assert all(f"{x}," in roles.LEADS[TarotQuestionForm.YES_NO] for x in leads)
    for form_leads in roles.LEADS.values():
        assert len(form_leads) == roles.LEAD_VARIANTS == len(set(form_leads))
        for text in form_leads:
            assert text.endswith(",") and len(text.split()) <= roles.LEAD_MAX_WORDS


def test_ac16_session_frame_changes_the_sentence_for_the_same_question() -> None:
    texts = {
        _render(
            YES_NO,
            TarotSpreadMap.THREE_UNBLOCK,
            variants=TarotVariants(key_version=1, frames={"clear": index}),
        )
        .positions[0]
        .meaning_here
        for index in range(roles.FRAME_VARIANTS)
    }
    assert len(texts) == roles.FRAME_VARIANTS


_SENTENCES = ContentReviewAgent._sentences


@pytest.mark.parametrize("roast", [False, True])
def test_frames_fit_the_density_limit_and_read_their_field_for_every_card_and_topic(
    roast: bool,
) -> None:
    """Every role frame x the longest lead x every card x topic: <= 28 words per sentence."""

    longest = max(
        (x for leads in roles.LEADS.values() for x in leads), key=lambda x: len(x.split())
    )
    for key, role in roles.ROLES.items():
        for card in all_cards():
            for context in TarotContext:
                meaning = _CardMeaning.for_context(card, context)
                tension = _tension_parts(meaning.tension)[0]
                resource = _resource_step(meaning.resource)
                for index in range(roles.FRAME_VARIANTS):
                    text = roles.meaning_for(
                        key,
                        core=meaning.core,
                        tension=tension,
                        resource=resource,
                        frame=index,
                        roast=roast,
                        lead=longest,
                    )
                    worst = max(len(s.split()) for s in _SENTENCES(text))
                    assert worst <= 28, (key, index, card.id, context, text)
                    expected = {
                        roles.RoleField.CORE: (meaning.core,),
                        roles.RoleField.TENSION: (tension,),
                        roles.RoleField.OPTION: (meaning.core, tension),
                        roles.RoleField.RESOURCE: () if role.step else (resource,),
                    }[role.field]
                    assert all(part in text for part in expected), (key, index)


# ---------------------------------------------------------------- AC19 Roast


def _slots(template: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


def test_ac19_roast_copy_maps_one_to_one_by_combination_code() -> None:
    for key, role in roles.ROLES.items():
        assert len(role.frames) == len(role.roast) == roles.FRAME_VARIANTS
        for index, (direct, roast) in enumerate(zip(role.frames, role.roast, strict=True)):
            assert _slots(direct) == _slots(roast), roles.frame_code(key, index)
    assert set(stance.HEADLINES) == set(stance.ROAST_HEADLINES)
    for key, frames in stance.HEADLINES.items():
        roast_frames = stance.ROAST_HEADLINES[key]
        assert len(frames) == len(roast_frames) == HEADLINE_VARIANTS
        for direct, roasted in zip(frames, roast_frames, strict=True):
            assert _slots(direct) == _slots(roasted)
    assert set(stance.CONCLUSIONS) == set(stance.ROAST_CONCLUSIONS)
    assert set(stance.CONJUNCTIONS) == set(stance.ROAST_CONJUNCTIONS)


def test_every_headline_frame_fits_the_budget_with_the_longest_slots() -> None:
    title = max(len(card.title_vi.split()) for card in all_cards())
    action = max(
        len(text.split()) for text in (*stance.ACTION_PHRASES.values(), stance.GENERIC_ACTION)
    )
    topic = max(len(text.split()) for text in stance.TOPIC_PHRASES.values())
    words = {
        "focal": " ".join(["x"] * title),
        "pair": " ".join(["x"] * (2 * title + 1)),
        "action": " ".join(["a"] * action),
        "topic": " ".join(["t"] * topic),
        "target": " ".join(["a"] * max(action, topic + 1)),
    }
    for table in (stance.HEADLINES, stance.ROAST_HEADLINES):
        for key, frames in table.items():
            for template in frames:
                assert len(template.format(**words).split()) <= 18, (key, template)


def test_ac19_every_stance_headline_and_conclusion_states_only_its_level() -> None:
    markers = stance.MARKERS
    for level in TarotStanceLevel:
        for table in (stance.HEADLINES, stance.ROAST_HEADLINES):
            for template in table[level.value]:
                text = template.lower()
                assert markers[level] in text
                assert not [m for lv, m in markers.items() if lv is not level and m in text]
        for conclusions in (stance.CONCLUSIONS, stance.ROAST_CONCLUSIONS):
            assert markers[level] in conclusions[level].lower()
    for form in (TarotQuestionForm.TIMING, TarotQuestionForm.HOW, TarotQuestionForm.WHY):
        for table in (stance.HEADLINES, stance.ROAST_HEADLINES):
            for template in table[form.value]:
                assert not [m for m in markers.values() if m in template.lower()]
    assert all("sẵn sàng" in t for t in stance.ROAST_HEADLINES[TarotQuestionForm.TIMING.value])


def test_ac19_roast_reading_uses_roast_frames_conclusion_links_and_headline() -> None:
    variants = TarotVariants(key_version=1, headline=1, frames={"clear": 2, "missed": 1})
    reading = _render(
        YES_NO, TarotSpreadMap.THREE_UNBLOCK, voice=TarotVoice.ROAST, variants=variants
    )
    assert reading.voice is TarotVoice.ROAST and reading.stance is not None
    clear = reading.positions[0]
    assert "chuyện đã rõ mười mươi:" in clear.meaning_here.lower()
    # Roast frames carry the voice; the per-position tails stay with the gentle register only.
    prose = " ".join(p.meaning_here for p in reading.positions)
    assert not [tail for tail in ROAST_MEANING_TAILS.values() if tail in prose]
    action = reading.stance.action
    phrase = stance.ACTION_PHRASES[action] if action else stance.GENERIC_ACTION
    assert reading.stance.conclusion == stance.ROAST_CONCLUSIONS[reading.stance.level].format(
        action=phrase
    )
    roast_links = {c for pair in stance.ROAST_CONJUNCTIONS.values() for c in pair}
    assert any(f". {c} " in reading.summary for c in roast_links)
    views = _position_views(reading.positions, reading.context)
    assert reading.headline == stance.dynamic_headline(
        TarotQuestionForm.YES_NO,
        reading.stance,
        action,
        TarotContext.WORK,
        views[2],
        views[1],
        variant=1,
        roast=True,
    )
    focal = views[2].title
    # The stance gate now holds Roast to its headline and to the Roast conclusion.
    with pytest.raises(TarotContentRejected, match="headline does not state the stance"):
        ENGINE.validate(reading.model_copy(update={"headline": f"{focal}: chuyện để sau."}))
    direct = stance.CONCLUSIONS[reading.stance.level].format(action=phrase)
    tampered = reading.stance.model_copy(update={"conclusion": direct})
    with pytest.raises(TarotContentRejected, match="stance does not match"):
        ENGINE.validate(reading.model_copy(update={"stance": tampered}))


@pytest.mark.parametrize("context", sorted(GENTLE_CONTEXTS))
def test_ac19_gentle_contexts_keep_direct_frames_with_the_gentle_tail(
    context: TarotContext,
) -> None:
    question = "Mình có nên nghỉ ngơi sớm hơn tối nay không?"
    roast = _render(question, TarotSpreadMap.THREE_UNBLOCK, context=context, voice=TarotVoice.ROAST)
    plain = _render(question, TarotSpreadMap.THREE_UNBLOCK, context=context)
    assert roast.voice is TarotVoice.ROAST
    assert roast.positions[0].meaning_here.startswith(plain.positions[0].meaning_here)
    assert any(
        tail in p.meaning_here for p in roast.positions for tail in GENTLE_MEANING_TAILS.values()
    )
    assert roast.headline == plain.headline


async def test_ac19_sensitive_questions_never_get_roast_through_the_service(
    database: Database,
) -> None:
    guest = await _guest(database)
    service = _service(database, KEY)
    question = "Mình có nên nói với sếp chuyện mất ngủ không?"
    started = await _start(service, guest, question=question, voice=TarotVoice.ROAST)
    done = await _complete(service, guest, started)
    assert done.reading is not None and done.reading.voice is TarotVoice.PLAYFUL_GROUNDED
    prose = " ".join(p.meaning_here for p in done.reading.positions).lower()
    roast_openings = {
        frame.split("{")[0].strip().lower()
        for role in roles.ROLES.values()
        for frame in role.roast
        if frame.split("{")[0].strip()
    }
    assert not [opening for opening in roast_openings if opening in prose]


# ---------------------------------------------------------------- AC17/AC18 versions


def test_ac18_framed_readings_record_v8_v6_v5_and_legacy_keeps_v6_v4_v4() -> None:
    # T02/T03 (27/10/2026) moved framed readings from renderer v7 / knowledge v5 to v8 / v6.
    framed = _render(YES_NO, TarotSpreadMap.THREE_UNBLOCK)
    assert framed.provenance.renderer_version == FRAMED_RENDERER_VERSION == "tarot-renderer-v8"
    assert framed.provenance.knowledge_version == FRAMED_KNOWLEDGE_VERSION == "tarot-knowledge-v6"
    assert framed.provenance.gate_version == TAROT_GATE_VERSION == "tarot-gates-v5"
    legacy = ENGINE.render(
        card_ids=tuple(CARDS[:3]),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.WORK,
        question=YES_NO,
        voice=TarotVoice.PLAYFUL_GROUNDED,
    )
    assert (
        legacy.provenance.renderer_version,
        legacy.provenance.knowledge_version,
        legacy.provenance.gate_version,
    ) == (LEGACY_RENDERER_VERSION, "tarot-knowledge-v4", "tarot-gates-v4")
    assert current_renderer_version(QUESTION_RULES_VERSION) == FRAMED_RENDERER_VERSION
    assert current_renderer_version("tarot-question-rules-v1") == LEGACY_RENDERER_VERSION


def test_ac18_provenance_has_no_stale_defaults() -> None:
    with pytest.raises(ValidationError):
        TarotReadingProvenance(source_ids=("x",))  # type: ignore[call-arg]


def test_ac17_a_stored_b2_3_framed_reading_still_validates() -> None:
    reading = _render(YES_NO, TarotSpreadMap.THREE_UNBLOCK)
    stored = json.loads(json.dumps(reading.model_dump(mode="json")))
    stored["provenance"]["renderer_version"] = "tarot-renderer-v6"
    stored["provenance"]["knowledge_version"] = "tarot-knowledge-v4"
    restored = TarotReading.model_validate(stored)
    assert restored.provenance.renderer_version == "tarot-renderer-v6"
    assert restored.stance == reading.stance
