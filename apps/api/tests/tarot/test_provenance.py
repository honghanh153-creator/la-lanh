"""B2-4b: provenance-coded Luna payload for framed Tarot readings (US-20 AC06).

Task: docs/plans/2026-10-18-b2-4b-tarot-provenance-task.md. Luna stays off; these tests only
build and validate payloads locally.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest

from app.domains.tarot import provenance, roles
from app.domains.tarot.engine import _POSITIONS, TarotReadingEngine
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.meaning_brief import BRIEF_LIMITS
from app.domains.tarot.models import (
    TarotContext,
    TarotOrigin,
    TarotReading,
    TarotSelectedCard,
    TarotSessionState,
    TarotSessionView,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)
from app.domains.tarot.rewrite import compile_tarot_rewrite_request
from app.domains.tarot.variants import TarotVariants
from app.infrastructure.generation.privacy import (
    TAROT_FOCUS_SENTENCES,
    PrivacyMinimiser,
    UnsafeRewritePayload,
)

ENGINE = TarotReadingEngine()
CARDS = [card.id for card in all_cards()]
SPREAD = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
GUEST = UUID("20000000-0000-4000-8000-000000000b24")
NOW = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
BANK = Path(__file__).resolve().parents[4] / "docs" / "fixtures" / "tarot-question-bank-v1.json"
ITEMS: list[dict[str, Any]] = json.loads(BANK.read_text())["items"]
CANARY = "zqcanary7tim"
PRIVATE = "chị Lan ở phòng 302"


def _reading(
    question: str,
    spread_map: TarotSpreadMap,
    *,
    context: TarotContext = TarotContext.WORK,
    voice: TarotVoice = TarotVoice.PLAYFUL_GROUNDED,
    seed: int = 0,
) -> TarotReading:
    assessment = ENGINE.assess_question(question, context)
    assert assessment.accepted and assessment.frame is not None
    keys = [key for key, _ in _POSITIONS[spread_map]]
    return ENGINE.render(
        card_ids=tuple(CARDS[(seed * 7 + i * 11) % 78] for i in range(len(keys))),
        spread=SPREAD[len(keys)],
        spread_map=spread_map,
        context=context,
        question=question,
        voice=voice,
        question_intent=assessment.intent,
        frame=assessment.frame,
        variants=TarotVariants(
            key_version=1,
            lead=seed % 5,
            headline=seed % 3,
            frames={key: (seed + i) % 3 for i, key in enumerate(keys)},
        ),
    )


def _view(reading: TarotReading) -> TarotSessionView:
    return TarotSessionView(
        id=UUID("70000000-0000-4000-8000-000000000b24"),
        version=len(reading.positions) + 1,
        state=TarotSessionState.COMPLETE,
        context=reading.context,
        spread=reading.spread,
        spread_map=reading.spread_map,
        voice=reading.voice,
        origin=TarotOrigin.DIRECT,
        question=reading.question,
        required_cards=len(reading.positions),
        selected_cards=tuple(
            TarotSelectedCard(
                fan_index=index,
                position_key=position.key,
                position_label=position.label,
                card=position.card,
            )
            for index, position in enumerate(reading.positions)
        ),
        reading=reading,
        created_at=NOW,
        updated_at=NOW,
        expires_at=NOW + timedelta(days=29),
    )


def _payload(reading: TarotReading) -> dict[str, Any]:
    request = compile_tarot_rewrite_request(
        GUEST, _view(reading), model_version="gpt-6-luna", prompt_version="surface-rewrite-v3"
    )
    assert request is not None
    return cast(dict[str, Any], request.safe_payload)


def _untraced(payload: dict[str, Any]) -> list[str]:
    return provenance.untraced_paths(
        payload, focus_sentences=TAROT_FOCUS_SENTENCES, limits=frozenset(BRIEF_LIMITS)
    )


# ---------------------------------------------------------------- schema and tracing


def test_ac06_framed_payload_is_brief_v3_with_a_source_per_position() -> None:
    reading = _reading("Mình có nên nhận thêm việc ở chỗ làm không?", TarotSpreadMap.THREE_UNBLOCK)
    payload = _payload(reading)
    brief = payload["meaning_brief"]
    assert brief["version"] == "tarot-meaning-brief-v3"
    assert brief["spread_map"] == "three_unblock"
    assert brief["stance"]["level"] == reading.stance.level.value  # type: ignore[union-attr]
    assert set(brief["stance"]) == {"kind", "level", "action", "options"}  # labels, no prose
    assert all(
        set(p["source"]) == {"frame", "lead", "gentle", "reflection", "action", "scene"}
        for p in payload["positions"]
    )
    # T02/T03: the step role carries the asked action's scene and step as closed codes; the
    # other positions keep the card x topic scene (no scene code).
    *others, step = payload["positions"]
    frame = ENGINE.assess_question(reading.question, TarotContext.WORK).frame
    assert frame is not None and frame.action is not None
    code = f"act.{frame.action.value}.{frame.topic.value}"
    assert (step["source"]["scene"], step["source"]["action"]) == (code, code)
    assert all(p["source"]["scene"] is None for p in others)
    assert [(p["everyday_scene"], p["small_action"]) for p in payload["positions"]] == [
        (p.everyday_scene, p.small_action) for p in reading.positions
    ]
    # The texts equal what the reader sees, but they were rebuilt from the codes.
    assert [p["meaning_here"] for p in payload["positions"]] == [
        p.meaning_here for p in reading.positions
    ]
    assert brief["local_summary"] == reading.summary
    assert _untraced(payload) == []
    safe = cast(dict[str, Any], PrivacyMinimiser().minimise(_request_surface(), payload))
    assert safe["meaning_brief"]["version"] == "tarot-meaning-brief-v3"


def _request_surface() -> Any:
    from app.domains.content_rewrite.models import RewriteSurface

    return RewriteSurface.TAROT


@pytest.mark.parametrize("voice", [TarotVoice.PLAYFUL_GROUNDED, TarotVoice.GENTLE_SPECIFIC])
def test_ac06_every_string_traces_across_the_bank_sample(voice: TarotVoice) -> None:
    accepted = [item for item in ITEMS if item["expected"]["accepted"]]
    for seed, item in enumerate(accepted[::9]):
        for spread_map in TarotSpreadMap:
            reading = _reading(
                item["question"],
                spread_map,
                context=TarotContext(item["context"]),
                voice=voice,
                seed=seed,
            )
            payload = _payload(reading)
            assert _untraced(payload) == [], (item["id"], spread_map)
            PrivacyMinimiser().minimise(_request_surface(), payload)


def _set(payload: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    copy = json.loads(json.dumps(payload))
    node: Any = copy
    parts = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    for part in parts[:-1]:
        node = node[int(part[1:-1])] if part.startswith("[") else node[part]
    last = parts[-1]
    if last.startswith("["):
        node[int(last[1:-1])] = value
    else:
        node[last] = value
    return cast(dict[str, Any], copy)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("positions[0].meaning_here", "Lá này cho thấy chị Lan ở phòng 302 đang giận."),
        ("positions[1].everyday_scene", "Có lần zqcanary7tim nhắn cho bạn."),
        ("positions[2].small_action", "Nhắn cho chị Lan trước 9 giờ."),
        ("positions[0].reflection_question", "Bạn nghĩ gì về chị Lan?"),
        ("positions[0].card_title", "Lá của chị Lan"),
        ("positions[0].position_label", "Điều chị Lan biết"),
        ("meaning_brief.local_summary", "Tóm lại, chị Lan ở phòng 302."),
        ("meaning_brief.goals[0].meaning", "Nói chuyện với chị Lan."),
        ("meaning_brief.stance.action", "noi_voi_chi_lan"),
        ("focus_sentence", "Chị Lan có giận không?"),
        ("positions[0].source.frame", "clear.2"),  # a real code that does not reproduce the text
        ("positions[0].source.lead", "why.1"),
    ],
)
def test_ac06_any_untraceable_string_is_reported(path: str, value: Any) -> None:
    reading = _reading("Mình có nên nhận thêm việc ở chỗ làm không?", TarotSpreadMap.THREE_UNBLOCK)
    payload = _payload(reading)
    tampered = _set(payload, path, value)
    assert _untraced(tampered), path


def test_ac06_unknown_fields_are_untraced_and_rejected_by_the_schema() -> None:
    reading = _reading("Mình có nên nhận thêm việc ở chỗ làm không?", TarotSpreadMap.THREE_UNBLOCK)
    payload = _payload(reading)
    extra = _set(payload, "meaning_brief.question_hint", "chị Lan")
    assert "meaning_brief.question_hint" in _untraced(extra)
    with pytest.raises(UnsafeRewritePayload):
        PrivacyMinimiser().minimise(_request_surface(), extra)
    # v3 needs a source on every position; v2 positions must not carry one.
    missing = json.loads(json.dumps(payload))
    del missing["positions"][0]["source"]
    with pytest.raises(UnsafeRewritePayload):
        PrivacyMinimiser().minimise(_request_surface(), missing)
    downgraded = _set(payload, "meaning_brief.version", "tarot-meaning-brief-v2")
    with pytest.raises(UnsafeRewritePayload):
        PrivacyMinimiser().minimise(_request_surface(), downgraded)


def test_ac06_a_reading_the_catalog_cannot_reproduce_is_never_compiled() -> None:
    reading = _reading("Mình có nên nhận thêm việc ở chỗ làm không?", TarotSpreadMap.THREE_UNBLOCK)
    positions = list(reading.positions)
    positions[0] = positions[0].model_copy(
        update={"meaning_here": f"{positions[0].meaning_here} Chị Lan ở phòng 302 cũng vậy."}
    )
    edited = reading.model_copy(update={"positions": tuple(positions)})
    assert provenance.framed_positions(edited) is None
    assert (
        compile_tarot_rewrite_request(
            GUEST, _view(edited), model_version="gpt-6-luna", prompt_version="surface-rewrite-v3"
        )
        is None
    )
    summary = reading.model_copy(update={"summary": f"{reading.summary} Chị Lan biết rồi."})
    assert provenance.framed_brief(summary) is None


def test_ac06_roast_and_legacy_paths_are_unchanged() -> None:
    roast = _reading(
        "Mình có nên nhận thêm việc ở chỗ làm không?",
        TarotSpreadMap.THREE_UNBLOCK,
        voice=TarotVoice.ROAST,
    )
    assert (
        compile_tarot_rewrite_request(
            GUEST, _view(roast), model_version="gpt-6-luna", prompt_version="surface-rewrite-v3"
        )
        is None
    )
    legacy = ENGINE.render(
        card_ids=tuple(CARDS[:3]),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.WORK,
        question="Mình cần nói rõ điều gì trước khi nhận thêm việc?",
        voice=TarotVoice.PLAYFUL_GROUNDED,
    )
    payload = _payload(legacy)
    assert payload["meaning_brief"]["version"] == "tarot-meaning-brief-v2"
    assert all("source" not in position for position in payload["positions"])


# ---------------------------------------------------------------- privacy canary


def _fold(value: str) -> str:
    return unicodedata.normalize("NFC", " ".join(value.casefold().split()))


def _ngrams(phrase: str, size: int) -> set[str]:
    words = _fold(phrase).split()
    return {" ".join(words[i : i + size]) for i in range(len(words) - size + 1)}


def _catalog_corpus() -> str:
    from app.domains.tarot import stance
    from app.domains.tarot.engine import _CardMeaning, card_scene

    texts: list[str] = []
    for card in all_cards():
        texts.append(card.title_vi)
        for context in TarotContext:
            meaning = _CardMeaning.for_context(card, context)
            texts += [meaning.core, meaning.tension, meaning.resource, card_scene(card.id, context)]
    for role in roles.ROLES.values():
        texts += [*role.frames, *role.roast]
    texts += [lead for leads in roles.LEADS.values() for lead in leads]
    texts += list(stance.ACTION_PHRASES.values())
    return _fold(" \n ".join(texts))


@pytest.mark.parametrize(
    "spread_map",
    [TarotSpreadMap.ONE_FOCUS, TarotSpreadMap.THREE_UNBLOCK, TarotSpreadMap.FIVE_CONVERSATION],
)
def test_ac06_private_canary_never_reaches_the_payload(spread_map: TarotSpreadMap) -> None:
    question = f"Mình có nên nói với {PRIVATE} chuyện chia ca không {CANARY}?"
    assessment = ENGINE.assess_question(question, TarotContext.WORK)
    assert assessment.accepted
    for seed in range(6):
        reading = _reading(question, spread_map, seed=seed)
        assert CANARY in reading.question  # the reader's own question stays local
        payload = _payload(reading)
        outbound = _fold(json.dumps(payload, ensure_ascii=False))
        assert CANARY not in outbound
        corpus = _catalog_corpus()
        for size in range(2, len(PRIVATE.split()) + 1):
            for gram in _ngrams(PRIVATE, size):
                # A coincidental catalog phrase is allowed: it traces to the catalog, not input.
                assert gram not in outbound or gram in corpus, gram
        assert _untraced(payload) == []


class _CapturingRepository:
    """In-memory stand-in for the job repository; the real ContentRewriteService (registry,
    authorization, PrivacyMinimiser) runs in front of it, and nothing leaves the process."""

    def __init__(self) -> None:
        self.records: list[Any] = []

    async def enqueue(self, record: Any) -> tuple[Any, bool]:
        self.records.append(record)
        return record, True


class _Authorized:
    async def is_authorized(self, request: Any) -> bool:
        del request
        return True


async def test_ac06_canary_through_the_service_queue_path(tmp_path: Any) -> None:
    from app.db.session import Database
    from app.domains.content_rewrite.service import ContentRewriteService
    from app.domains.tarot.service import TarotSessionService
    from tests.tarot.test_variants import CIPHER, HASHER, KEY, _guest

    db = Database(f"sqlite+aiosqlite:///{tmp_path / 'tarot-provenance.db'}")
    await db.initialize()
    try:
        guest = await _guest(db)
        repository = _CapturingRepository()
        service = TarotSessionService(
            db.sessions,
            CIPHER,
            HASHER,
            generation_enabled=True,
            generation_model="gpt-6-luna",
            content_rewrite_service=ContentRewriteService(
                repository,  # type: ignore[arg-type]
                _Authorized(),
            ),
            variety_key=KEY,
        )
        view = await service.start(
            guest_id=guest,
            context=TarotContext.WORK,
            question=f"Mình có nên nói với {PRIVATE} chuyện chia ca không {CANARY}?",
            spread=TarotSpread.THREE_CARD,
            voice=TarotVoice.PLAYFUL_GROUNDED,
            origin=TarotOrigin.DIRECT,
            idempotency_key="tarot-provenance-canary-0001",
        )
        for fan in (3, 30, 60):
            view = await service.select_card(
                guest_id=guest,
                session_id=view.id,
                fan_index=fan,
                expected_version=view.version,
                external_generation_authorized=True,
            )
        assert view.reading is not None
        (record,) = repository.records
        request = record.request  # as queued: already minimised by the real service
        assert "source" in request.safe_payload["positions"][0]
        assert "action" not in request.safe_payload["positions"][0]["source"]  # null dropped
        outbound = _fold(json.dumps(request.model_dump(mode="json"), ensure_ascii=False))
        assert CANARY not in outbound
        assert not [g for g in _ngrams(PRIVATE, 2) if g in outbound and g not in _catalog_corpus()]
        assert request.safe_payload["meaning_brief"]["version"] == "tarot-meaning-brief-v3"
        assert _untraced(cast(dict[str, Any], request.safe_payload)) == []
    finally:
        await db.dispose()


# ---------------------------------------------------------------- Codex P2 regressions (#27)


@pytest.mark.parametrize("spread_map", list(TarotSpreadMap))
@pytest.mark.parametrize(
    "voice", [TarotVoice.STRAIGHT_WARM, TarotVoice.GENTLE_SPECIFIC, TarotVoice.PLAYFUL_GROUNDED]
)
def test_ac06_the_minimised_payload_still_traces(
    spread_map: TarotSpreadMap, voice: TarotVoice
) -> None:
    """The queue and the provider adapter emit the minimised form, which drops null optional
    codes (``source.action`` off the step role, ``source.lead``); it must trace too."""

    reading = _reading(
        "Làm thế nào để mình chia việc rõ hơn với nhóm?", spread_map, voice=voice, seed=3
    )
    raw = _payload(reading)
    assert _untraced(raw) == []
    outgoing = cast(dict[str, Any], PrivacyMinimiser().minimise(_request_surface(), raw))
    assert _untraced(outgoing) == []
    sources = [position["source"] for position in outgoing["positions"]]
    if len(sources) > 1:
        assert any("action" not in source for source in sources)  # the case that broke


def test_ac06_omitted_optional_codes_resolve_as_null() -> None:
    reading = _reading("Làm thế nào để mình chia việc rõ hơn với nhóm?", TarotSpreadMap.FIVE_LOOP)
    raw = _payload(reading)
    stripped = json.loads(json.dumps(raw))
    for position in stripped["positions"]:
        if position["source"].get("action") is None:
            position["source"].pop("action")
        position["source"].pop("lead")  # a lead that is present must still match the text
    untraced = _untraced(stripped)
    assert untraced and all(path.endswith("meaning_here") for path in untraced)


@pytest.mark.parametrize(
    ("question", "context", "cards", "scene", "action"),
    [
        # CONSIDER: the step prepares the asked action.
        ("Mình có nên gửi bản thảo này đi không?", TarotContext.WORK, ("major-hermit",),
         "act.gui_di.work", "prep.gui_di"),
        # No partner named: the partner-only relationships scene gives way to the general row.
        ("Mình có nên nhắn lại cho mẹ sau lần cãi nhau không?", TarotContext.RELATIONSHIPS,
         ("major-sun", "major-star", "wands-8", "cups-9", "pentacles-8"),
         "act.nhan_lai.general", "act.nhan_lai.relationships"),
        # A choice the cards do not settle: a step that names neither option, the card scene.
        ("Mình nên nhắn lại hay chờ thêm?", TarotContext.RELATIONSHIPS,
         ("major-hermit", "major-sun", "wands-8", "cups-9", "pentacles-8"), None, "prep.choice"),
    ],
)  # fmt: skip
def test_r47_steps_and_scenes_trace_to_closed_codes(
    question: str,
    context: TarotContext,
    cards: tuple[str, ...],
    scene: str | None,
    action: str,
) -> None:
    """Codex r47: preparation and choice steps and the general fallback scene are rebuilt from
    closed codes; Tarot Luna would otherwise fail closed on these readings."""

    assessment = ENGINE.assess_question(question, context)
    assert assessment.frame is not None
    reading = ENGINE.render(
        card_ids=cards,
        spread=SPREAD[len(cards)],
        context=context,
        question=question,
        voice=TarotVoice.STRAIGHT_WARM,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )
    payload = _payload(reading)
    step = payload["positions"][-1]
    assert (step["source"]["scene"], step["source"]["action"]) == (scene, action)
    assert step["small_action"] == reading.positions[-1].small_action
    assert _untraced(payload) == []
    assert "mẹ" not in json.dumps(payload, ensure_ascii=False)
