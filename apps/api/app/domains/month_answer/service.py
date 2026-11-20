"""Month answers for one guest: load the chart, pick the fact, compose (AK2, 20.11.2026).

Reads only. The typed question never reaches this layer: the route turns it into closed labels
(topic, kind) and drops it. Nothing here stores or logs anything about the person.
"""

from __future__ import annotations

from asyncio import to_thread
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, DateOnlySunResult, NatalChart
from app.domains.birth.errors import BirthProfileChanged
from app.domains.birth.service import BirthChartService
from app.domains.content.copy_approval import approved_copy
from app.domains.daily.service import DailyNoteService
from app.domains.month_answer.answer import (
    CopySource,
    MonthAnswer,
    WindowAnswer,
    compose,
    window_answer,
)
from app.domains.month_answer.facts import (
    PRODUCT_TIMEZONE,
    Topic,
    easier_window,
    month_fact,
    month_key,
)
from app.domains.month_answer.question import QuestionKind

# The Khám phá card: one line and one small thing per area, no dates (S21). "Bản thân" uses the
# mind topic's copy.
OVERVIEW_AREAS: tuple[tuple[str, Topic], ...] = (
    ("work", Topic.WORK),
    ("love", Topic.LOVE),
    ("money", Topic.MONEY),
    ("self", Topic.MIND),
)
OVERVIEW_LABELS = {"work": "Công việc", "love": "Tình cảm", "money": "Tiền", "self": "Bản thân"}


class MonthAnswerUnavailable(Exception):
    """Copy for this answer is not approved yet, or the engine is missing."""


@dataclass(frozen=True, slots=True)
class OverviewItem:
    area: str
    label: str
    line: str
    try_: str


def today_in_vietnam(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(PRODUCT_TIMEZONE).date()


class MonthAnswerService:
    def __init__(
        self,
        engine: NatalChartEngine | None,
        birth_service: BirthChartService | None,
        daily_service: DailyNoteService,
        copy_source: CopySource = approved_copy,
    ) -> None:
        self._engine = engine
        self._birth = birth_service
        self._daily = daily_service
        self._copy = copy_source

    async def _chart(self, guest_id: UUID) -> NatalChart | DateOnlySunResult:
        snapshot = await self._daily.current_birth_snapshot(guest_id)
        chart: NatalChart | None = None
        if self._birth is not None:
            chart = await self._birth.chart_for_config(
                guest_id, CalculationConfig.western_recommended()
            )
        current = await self._daily.current_birth_snapshot(guest_id)
        if (current.id, current.profile_revision) != (snapshot.id, snapshot.profile_revision):
            raise BirthProfileChanged
        return chart if chart is not None else snapshot.result

    def _engine_or_raise(self) -> NatalChartEngine:
        if self._engine is None:
            raise MonthAnswerUnavailable
        return self._engine

    async def answer(
        self,
        guest_id: UUID,
        topic: Topic,
        kind: QuestionKind = QuestionKind.HOW,
        *,
        today: date | None = None,
    ) -> MonthAnswer:
        engine = self._engine_or_raise()
        chart = await self._chart(guest_id)
        month = month_key(today or today_in_vietnam())
        fact = await to_thread(month_fact, engine, chart, topic, month)
        answer = compose(fact, kind, self._copy)
        if answer is None:
            raise MonthAnswerUnavailable
        return answer

    async def window(
        self, guest_id: UUID, topic: Topic, *, today: date | None = None
    ) -> WindowAnswer | None:
        engine = self._engine_or_raise()
        chart = await self._chart(guest_id)
        start = today or today_in_vietnam()
        found = await to_thread(easier_window, engine, chart, topic, start)
        if found is None:
            return None
        result = window_answer(found, self._copy)
        if result is None:
            raise MonthAnswerUnavailable
        return result

    async def overview(
        self, guest_id: UUID, *, today: date | None = None
    ) -> tuple[str, tuple[OverviewItem, ...]]:
        engine = self._engine_or_raise()
        chart = await self._chart(guest_id)
        month = month_key(today or today_in_vietnam())
        items: list[OverviewItem] = []
        for area, topic in OVERVIEW_AREAS:
            fact = await to_thread(month_fact, engine, chart, topic, month)
            answer = compose(fact, QuestionKind.HOW, self._copy)
            if answer is None:
                raise MonthAnswerUnavailable
            items.append(OverviewItem(area, OVERVIEW_LABELS[area], answer.theme, answer.act))
        return month, tuple(items)
