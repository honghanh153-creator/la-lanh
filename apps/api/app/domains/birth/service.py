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
    BirthDateChangeLimited,
    BirthDateChangeRequiresEdit,
    BirthDateConfirmationMismatch,
    BirthDateOutOfRange,
    BirthDateUnchanged,
    BirthProfileChanged,
    BirthProfileNotFound,
    BirthSupplementConsentInvalid,
    BirthSupplementInvalid,
)
from app.domains.birth.models import (
    DATE_CHANGE_LIMIT,
    DATE_CHANGE_WINDOW,
    ApproxWindow,
    BirthReveal,
    BirthSnapshotRecord,
    BirthSupplement,
    BirthSupplementEdit,
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
        _require_adult_date(birth_date, current)
        active = await self._repository.find_current(guest_id)
        if active is not None and self._stored_date(active) != birth_date:
            # D4, checked again under the lock in save_or_replay; this only avoids the compute.
            raise BirthDateChangeRequiresEdit
        canonical_input = f"{guest_id}:date-only-v1:{birth_date.isoformat()}"
        input_hash = self._hasher.digest("birth-input", canonical_input)
        replay = await self._repository.find_by_input_hash(guest_id, input_hash)
        if replay is not None:
            stored, resumed = await self._repository.save_or_replay(replay)
            return self._reveal(stored, resumed=resumed)
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

    async def correct_date(
        self,
        *,
        guest_id: UUID,
        birth_date: date,
        confirm_birth_date: date,
        expected_revision: datetime,
        now: datetime | None = None,
    ) -> BirthReveal:
        """Replace a saved birth date (US-23).

        Phase 1 here: validate (confirmation, the 18+ rule before anything is read or computed,
        an active subject, a different date, the revision fence, the rolling limit), then compute
        and encrypt the new date-only chart without any lock or write. A failure leaves everything
        as it was. Phases 2 and 3 are ``BirthRepository.replace_date``. No value is logged.
        """

        current = now or datetime.now(UTC)
        if confirm_birth_date != birth_date:
            raise BirthDateConfirmationMismatch
        _require_adult_date(birth_date, current)  # D6: refused before compute, nothing kept
        stored = await self._repository.find_current(guest_id)
        if stored is None:
            raise BirthProfileNotFound
        if self._stored_date(stored) == birth_date:
            raise BirthDateUnchanged
        if stored.profile_revision != expected_revision:
            raise BirthProfileChanged
        since = current - DATE_CHANGE_WINDOW
        if await self._repository.recent_date_changes(guest_id, since=since) >= DATE_CHANGE_LIMIT:
            raise BirthDateChangeLimited
        result = await self._run_compute(self._engine.calculate_date_only_sun, birth_date)
        replaced = await self._repository.replace_date(
            BirthSnapshotRecord(
                id=uuid4(),
                guest_id=guest_id,
                profile_id=stored.profile_id,
                input_hash=self._hasher.digest(
                    "birth-input", f"{guest_id}:date-only-v1:{birth_date.isoformat()}"
                ),
                birth_date_ciphertext=self._envelope.encrypt(
                    birth_date.isoformat().encode(),
                    context=f"birth-date:{guest_id}".encode(),
                ),
                result=result,
                created_at=current,
            ),
            expected_revision=expected_revision,
            now=current,
            limit=DATE_CHANGE_LIMIT,
            window=DATE_CHANGE_WINDOW,
        )
        return self._reveal(replaced, resumed=False)

    def _stored_date(self, stored: BirthSnapshotRecord) -> date:
        return date.fromisoformat(
            self._envelope.decrypt(
                stored.birth_date_ciphertext,
                context=f"birth-date:{stored.guest_id}".encode(),
            ).decode()
        )

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
            profile_revision=stored.profile_revision,
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
            expected_snapshot_id=stored.id,
            expected_updated_at=stored.profile_revision,
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
            profile_revision=stored.profile_revision,
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

    async def supplement_edit(self, guest_id: UUID) -> BirthSupplementEdit:
        """Private edit form only; general state/projections never contain raw time."""
        stored = await self._repository.find_supplement(guest_id)
        if stored is None:
            raise BirthProfileNotFound
        mode = BirthTimeMode.UNKNOWN
        local_time = None
        window = None
        place = None
        if stored.birth_time_ciphertext:
            raw = self._envelope.decrypt(
                stored.birth_time_ciphertext, context=f"birth-time:{guest_id}".encode()
            ).decode()
            mode_value, value = raw.split(":", maxsplit=1)
            mode = BirthTimeMode(mode_value)
            if mode is BirthTimeMode.EXACT:
                local_time = value
            elif mode is BirthTimeMode.APPROX_WINDOW:
                window = ApproxWindow(value)
        if stored.birth_place_ciphertext:
            raw = self._envelope.decrypt(
                stored.birth_place_ciphertext, context=f"birth-place:{guest_id}".encode()
            ).decode()
            place = self._places.get(raw.split("|", maxsplit=1)[0])
        return BirthSupplementEdit(mode, local_time, window, place)

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
        birth_time_local: str | None,
        place_id: str,
        config: CalculationConfig,
        birth_time_mode: BirthTimeMode = BirthTimeMode.EXACT,
        now: datetime | None = None,
    ) -> NatalChart:
        """Calculate an exact chart without persisting any supplied birth input."""
        current = now or datetime.now(UTC)
        youngest_allowed = _years_before(current.date(), 18)
        oldest_allowed = _years_before(current.date(), 120)
        if birth_date < oldest_allowed or birth_date > youngest_allowed:
            raise BirthDateOutOfRange
        if birth_time_mode not in {BirthTimeMode.EXACT, BirthTimeMode.UNKNOWN}:
            raise BirthSupplementInvalid
        local_time: time | None
        precision: TimePrecision
        if birth_time_mode is BirthTimeMode.UNKNOWN:
            if birth_time_local is not None:
                raise BirthSupplementInvalid
            local_time, precision = time(hour=12), TimePrecision.UNKNOWN
        else:
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
        chart = (
            await self._run_compute(
                lambda value: self._engine.calculate_chart(value, config),
                chart_input,
            )
        ).model_copy(update={"time_precision": precision})
        if precision is TimePrecision.UNKNOWN:
            stable_bodies = tuple(body for body in chart.bodies if body.body.value != "moon")
            stable_aspects = tuple(
                aspect
                for aspect in chart.aspects
                if "moon" not in {aspect.body_a.value, aspect.body_b.value}
            )
            chart = chart.model_copy(
                update={
                    "bodies": stable_bodies,
                    "aspects": stable_aspects,
                    "houses": None,
                    "angles": None,
                }
            )
        return chart

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


def _require_adult_date(birth_date: date, now: datetime) -> None:
    """The product-wide 18+ rule (US-02), identical at onboarding and correction (US-23 D6)."""

    if birth_date < _years_before(now.date(), 120) or birth_date > _years_before(now.date(), 18):
        raise BirthDateOutOfRange


def _years_before(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)
