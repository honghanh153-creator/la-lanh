import asyncio
from collections.abc import Callable
from datetime import UTC, date, datetime, time
from typing import TypeVar
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput, NatalChart, TimePrecision
from app.domains.birth.errors import (
    BirthChartBusy,
    BirthDateOutOfRange,
    BirthProfileNotFound,
    BirthSupplementConsentInvalid,
    BirthSupplementInvalid,
)
from app.domains.birth.models import (
    ApproxWindow,
    BirthReveal,
    BirthSnapshotRecord,
    BirthSupplement,
    BirthSupplementResult,
    BirthSupplementState,
    BirthTimeMode,
)
from app.domains.birth.repository import BirthRepository
from app.domains.geo.models import PlaceResult
from app.domains.geo.service import PlaceSearchService
from app.infrastructure.crypto import EnvelopeCipher, SecretHasher

ComputeArgument = TypeVar("ComputeArgument")
ComputeResult = TypeVar("ComputeResult")


class BirthChartService:
    def __init__(
        self,
        repository: BirthRepository,
        engine: NatalChartEngine,
        envelope: EnvelopeCipher,
        hasher: SecretHasher,
        places: PlaceSearchService | None = None,
    ) -> None:
        self._repository = repository
        self._engine = engine
        self._envelope = envelope
        self._hasher = hasher
        self._places = places or PlaceSearchService()
        self._compute_slots = asyncio.Semaphore(2)

    async def create_date_only(
        self,
        *,
        guest_id: UUID,
        birth_date: date,
        now: datetime | None = None,
    ) -> BirthReveal:
        current = now or datetime.now(UTC)
        youngest_allowed = _years_before(current.date(), 18)
        oldest_allowed = _years_before(current.date(), 120)
        if birth_date < oldest_allowed or birth_date > youngest_allowed:
            raise BirthDateOutOfRange
        canonical_input = f"{guest_id}:date-only-v1:{birth_date.isoformat()}"
        input_hash = self._hasher.digest("birth-input", canonical_input)
        replay = await self._repository.find_by_input_hash(guest_id, input_hash)
        if replay is not None:
            return self._reveal(replay, resumed=True)
        result = await self._run_compute(self._engine.calculate_date_only_sun, birth_date)
        encrypted_date = self._envelope.encrypt(
            birth_date.isoformat().encode(),
            context=f"birth-date:{guest_id}".encode(),
        )
        stored, resumed = await self._repository.save_or_replay(
            BirthSnapshotRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=uuid4(),
                input_hash=input_hash,
                birth_date_ciphertext=encrypted_date,
                result=result,
                created_at=current,
            )
        )
        return self._reveal(stored, resumed=resumed)

    async def current(self, guest_id: UUID) -> BirthReveal:
        stored = await self._repository.find_current(guest_id)
        if stored is None:
            raise BirthProfileNotFound
        birth_date = date.fromisoformat(
            self._envelope.decrypt(
                stored.birth_date_ciphertext,
                context=f"birth-date:{guest_id}".encode(),
            ).decode()
        )
        return BirthReveal(
            profile_id=stored.profile_id,
            snapshot_id=stored.id,
            birth_date=birth_date,
            result=stored.result,
            created_at=stored.created_at,
            resumed=True,
        )

    def search_places(self, query: str) -> tuple[PlaceResult, ...]:
        normalized_query = query.strip()
        if len(query) > 80 or (normalized_query and len(normalized_query) < 2):
            raise BirthSupplementInvalid
        return self._places.search(normalized_query)

    async def add_supplement(
        self,
        *,
        guest_id: UUID,
        birth_time_mode: BirthTimeMode,
        birth_time_local: str | None,
        approx_window: ApproxWindow | None,
        place_id: str | None,
        consent_version: str,
        now: datetime | None = None,
    ) -> BirthSupplementResult:
        if consent_version != "birth-profile-deep-v1":
            raise BirthSupplementConsentInvalid
        current = now or datetime.now(UTC)
        stored = await self._repository.find_current(guest_id)
        if stored is None:
            raise BirthProfileNotFound
        birth_date = date.fromisoformat(
            self._envelope.decrypt(
                stored.birth_date_ciphertext,
                context=f"birth-date:{guest_id}".encode(),
            ).decode()
        )
        local_time, precision = _resolve_time(birth_time_mode, birth_time_local, approx_window)
        place = self._places.get(place_id) if place_id else None
        if place_id and place is None:
            raise BirthSupplementInvalid

        chart = None
        profile_level = 1
        timezone_id = place.timezone_id if place is not None else None
        if birth_time_mode is not BirthTimeMode.UNKNOWN:
            profile_level = 2
        if place is not None and local_time is not None:
            profile_level = 3
            local_datetime = datetime.combine(
                birth_date,
                local_time,
                tzinfo=ZoneInfo(place.timezone_id),
            )
            chart_input = ChartInput(
                utc_datetime=local_datetime.astimezone(UTC),
                latitude=place.latitude,
                longitude=place.longitude,
            )
            canonical_input = (
                f"supplement-v1:{birth_date.isoformat()}:{birth_time_mode.value}:"
                f"{birth_time_local}:{approx_window}:{place.place_id}"
            ).encode()
            input_hash = self._hasher.digest("birth-input", canonical_input.decode())
            replay = await self._repository.find_by_input_hash(guest_id, input_hash)
            chart = (
                replay.result
                if replay is not None and isinstance(replay.result, NatalChart)
                else await self._run_compute(self._engine.calculate_chart, chart_input)
            )
            chart = chart.model_copy(update={"time_precision": precision})

        encrypted_time = (
            self._envelope.encrypt(
                f"{birth_time_mode.value}:{birth_time_local or approx_window or ''}".encode(),
                context=f"birth-time:{guest_id}".encode(),
            )
            if birth_time_mode is not BirthTimeMode.UNKNOWN
            else None
        )
        encrypted_place = (
            self._envelope.encrypt(
                f"{place.place_id}|{place.display_name}|{place.timezone_id}|{place.latitude}|{place.longitude}".encode(),
                context=f"birth-place:{guest_id}".encode(),
            )
            if place is not None
            else None
        )
        snapshot_id = None
        pending_snapshot = None
        if chart is not None:
            if place is None:
                raise BirthSupplementInvalid
            pending_snapshot = BirthSnapshotRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=stored.profile_id,
                input_hash=self._hasher.digest("birth-input", canonical_input.decode()),
                birth_date_ciphertext=stored.birth_date_ciphertext,
                result=chart,
                created_at=current,
            )
        saved = await self._repository.save_supplement(
            guest_id,
            pending_snapshot,
            BirthSupplement(
                birth_time_mode=birth_time_mode,
                birth_time_ciphertext=encrypted_time,
                approx_window=approx_window,
                birth_place_ciphertext=encrypted_place,
                consent_version=consent_version,
            ),
        )
        if saved is not None:
            snapshot_id = saved.id
        return BirthSupplementResult(
            profile_id=stored.profile_id,
            snapshot_id=snapshot_id,
            profile_level=profile_level,
            time_precision=precision.value,
            place_display_name=place.display_name if place is not None else None,
            timezone_id=timezone_id,
            chart=chart,
        )

    async def _run_compute(
        self,
        operation: Callable[[ComputeArgument], ComputeResult],
        argument: ComputeArgument,
    ) -> ComputeResult:
        try:
            await asyncio.wait_for(self._compute_slots.acquire(), timeout=0.05)
        except TimeoutError as error:
            raise BirthChartBusy from error
        try:
            return await asyncio.to_thread(operation, argument)
        finally:
            self._compute_slots.release()

    def _reveal(self, stored: BirthSnapshotRecord, *, resumed: bool) -> BirthReveal:
        stored_date = date.fromisoformat(
            self._envelope.decrypt(
                stored.birth_date_ciphertext,
                context=f"birth-date:{stored.guest_id}".encode(),
            ).decode()
        )
        return BirthReveal(
            profile_id=stored.profile_id,
            snapshot_id=stored.id,
            birth_date=stored_date,
            result=stored.result,
            created_at=stored.created_at,
            resumed=resumed,
        )

    async def supplement_state(self, guest_id: UUID) -> BirthSupplementState:
        stored = await self._repository.find_supplement(guest_id)
        if stored is None:
            raise BirthProfileNotFound
        mode = BirthTimeMode.UNKNOWN
        approx_window = None
        if stored.birth_time_ciphertext:
            raw_time = self._envelope.decrypt(
                stored.birth_time_ciphertext,
                context=f"birth-time:{guest_id}".encode(),
            ).decode()
            mode_value, value = raw_time.split(":", maxsplit=1)
            mode = BirthTimeMode(mode_value)
            if mode is BirthTimeMode.APPROX_WINDOW and value:
                approx_window = ApproxWindow(value)
        place_display_name = None
        timezone_id = None
        if stored.birth_place_ciphertext:
            raw_place = self._envelope.decrypt(
                stored.birth_place_ciphertext,
                context=f"birth-place:{guest_id}".encode(),
            ).decode()
            _, place_display_name, timezone_id, _, _ = raw_place.split("|", maxsplit=4)
        return BirthSupplementState(
            profile_id=stored.profile_id,
            profile_level=stored.profile_level,
            time_precision=stored.time_precision,
            birth_time_mode=mode,
            approx_window=approx_window,
            place_display_name=place_display_name,
            timezone_id=timezone_id,
        )

    async def chart_for_config(
        self,
        guest_id: UUID,
        config: CalculationConfig,
    ) -> NatalChart | None:
        """Recompute from encrypted private input without exposing that input to the client."""
        current, supplement = await asyncio.gather(
            self._repository.find_current(guest_id),
            self._repository.find_supplement(guest_id),
        )
        if current is None:
            raise BirthProfileNotFound
        if supplement is None:
            return None
        if supplement.birth_time_ciphertext is None or supplement.birth_place_ciphertext is None:
            return None
        birth_date = date.fromisoformat(
            self._envelope.decrypt(
                current.birth_date_ciphertext,
                context=f"birth-date:{guest_id}".encode(),
            ).decode()
        )
        raw_time = self._envelope.decrypt(
            supplement.birth_time_ciphertext,
            context=f"birth-time:{guest_id}".encode(),
        ).decode()
        mode_value, value = raw_time.split(":", maxsplit=1)
        mode = BirthTimeMode(mode_value)
        approx_window = ApproxWindow(value) if mode is BirthTimeMode.APPROX_WINDOW else None
        local_time, precision = _resolve_time(
            mode,
            value if mode is BirthTimeMode.EXACT else None,
            approx_window,
        )
        if local_time is None:
            return None
        raw_place = self._envelope.decrypt(
            supplement.birth_place_ciphertext,
            context=f"birth-place:{guest_id}".encode(),
        ).decode()
        _, _, timezone_id, latitude, longitude = raw_place.split("|", maxsplit=4)
        local_datetime = datetime.combine(
            birth_date,
            local_time,
            tzinfo=ZoneInfo(timezone_id),
        )
        chart_input = ChartInput(
            utc_datetime=local_datetime.astimezone(UTC),
            latitude=float(latitude),
            longitude=float(longitude),
            house_system=config.house_system,
        )
        chart = (
            await self._run_compute(
                lambda value: self._engine.calculate_chart(value, config),
                chart_input,
            )
        ).model_copy(update={"time_precision": precision})
        if precision is not TimePrecision.EXACT:
            chart = chart.model_copy(update={"houses": None, "angles": None})
        return chart

    async def calculate_transient_chart(
        self,
        *,
        birth_date: date,
        birth_time_local: str,
        place_id: str,
        config: CalculationConfig,
        now: datetime | None = None,
    ) -> NatalChart:
        """Calculate an exact chart without persisting any supplied birth input."""
        current = now or datetime.now(UTC)
        youngest_allowed = _years_before(current.date(), 18)
        oldest_allowed = _years_before(current.date(), 120)
        if birth_date < oldest_allowed or birth_date > youngest_allowed:
            raise BirthDateOutOfRange
        local_time, precision = _resolve_time(BirthTimeMode.EXACT, birth_time_local, None)
        place = self._places.get(place_id)
        if place is None or local_time is None:
            raise BirthSupplementInvalid
        local_datetime = datetime.combine(
            birth_date,
            local_time,
            tzinfo=ZoneInfo(place.timezone_id),
        )
        chart_input = ChartInput(
            utc_datetime=local_datetime.astimezone(UTC),
            latitude=place.latitude,
            longitude=place.longitude,
            house_system=config.house_system,
        )
        return (
            await self._run_compute(
                lambda value: self._engine.calculate_chart(value, config),
                chart_input,
            )
        ).model_copy(update={"time_precision": precision})

    async def remove_supplement(
        self, guest_id: UUID, *, remove_time: bool, remove_place: bool
    ) -> BirthSupplementState:
        if not remove_time and not remove_place:
            raise BirthSupplementInvalid
        await self._repository.clear_supplement(
            guest_id,
            remove_time=remove_time,
            remove_place=remove_place,
        )
        return await self.supplement_state(guest_id)


def _resolve_time(
    mode: BirthTimeMode, birth_time_local: str | None, approx_window: ApproxWindow | None
) -> tuple[time | None, TimePrecision]:
    if mode is BirthTimeMode.UNKNOWN:
        return None, TimePrecision.UNKNOWN
    if mode is BirthTimeMode.EXACT:
        if birth_time_local is None:
            raise BirthSupplementInvalid
        try:
            hour, minute = birth_time_local.split(":", maxsplit=1)
            return time(hour=int(hour), minute=int(minute)), TimePrecision.EXACT
        except ValueError as error:
            raise BirthSupplementInvalid from error
    if approx_window is None:
        raise BirthSupplementInvalid
    midpoint = {
        ApproxWindow.MORNING: time(hour=8),
        ApproxWindow.NOON: time(hour=12),
        ApproxWindow.AFTERNOON: time(hour=15),
        ApproxWindow.EVENING: time(hour=19),
        ApproxWindow.NIGHT: time(hour=23),
    }[approx_window]
    return midpoint, TimePrecision.APPROXIMATE


def _years_before(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)
