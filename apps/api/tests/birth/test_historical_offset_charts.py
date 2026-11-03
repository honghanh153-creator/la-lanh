"""Birth charts read North Vietnam 1960-1975 clocks as UTC+7 (synthetic people only)."""

from datetime import UTC, date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput, NatalChart, TimePrecision
from app.domains.birth.models import BirthSnapshotRecord, BirthTimeMode
from app.domains.birth.service import BirthChartService
from app.domains.geo.service import PLACE_BY_ID
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider
from tests.birth.test_birth_api import MemoryBirthRepository

NOW = datetime(2026, 11, 3, 9, 0, tzinfo=UTC)
BIRTH_DATE = date(1965, 5, 1)
BIRTH_TIME = "08:00"
CONSENT = "birth-profile-deep-v1"


def _service() -> tuple[BirthChartService, MemoryBirthRepository, NatalChartEngine]:
    repository = MemoryBirthRepository()
    engine = NatalChartEngine()
    envelope = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"k" * 32))
    service = BirthChartService(repository, engine, envelope, SecretHasher(b"h" * 32))
    return service, repository, engine


def _expected(engine: NatalChartEngine, place_id: str, hours: float) -> NatalChart:
    place = PLACE_BY_ID[place_id]
    local = datetime(1965, 5, 1, 8, 0, tzinfo=timezone(timedelta(hours=hours)))
    return engine.calculate_chart(
        ChartInput(
            utc_datetime=local.astimezone(UTC),
            latitude=place.latitude,
            longitude=place.longitude,
        )
    )


async def _with_supplement(service: BirthChartService, place_id: str) -> tuple[UUID, NatalChart]:
    guest_id = uuid4()
    await service.create_date_only(guest_id=guest_id, birth_date=BIRTH_DATE, now=NOW)
    result = await service.add_supplement(
        guest_id=guest_id,
        birth_time_mode=BirthTimeMode.EXACT,
        birth_time_local=BIRTH_TIME,
        approx_window=None,
        place_id=place_id,
        consent_version=CONSENT,
        now=NOW,
    )
    assert result.chart is not None
    return guest_id, result.chart


@pytest.mark.asyncio
async def test_northern_exact_birth_uses_utc7_and_stays_exact() -> None:
    service, _, engine = _service()
    _, chart = await _with_supplement(service, "vn-hanoi")
    expected = _expected(engine, "vn-hanoi", 7)
    assert chart.julian_day_ut == expected.julian_day_ut
    assert chart.angles == expected.angles
    assert chart.time_precision is TimePrecision.EXACT
    # The bug this fixes: one hour moves the Ascendant by roughly 15 degrees.
    southern = _expected(engine, "vn-hanoi", 8)
    assert chart.angles is not None and southern.angles is not None
    assert chart.angles.ascendant != southern.angles.ascendant


@pytest.mark.asyncio
async def test_southern_birth_keeps_its_replay_key_and_offset() -> None:
    service, repository, engine = _service()
    guest_id, chart = await _with_supplement(service, "vn-hue")
    assert chart.julian_day_ut == _expected(engine, "vn-hue", 8).julian_day_ut
    legacy_key = SecretHasher(b"h" * 32).digest(
        "birth-input", f"supplement-v1:{BIRTH_DATE.isoformat()}:exact:{BIRTH_TIME}:None:vn-hue"
    )
    assert (guest_id, legacy_key) in repository.by_input


@pytest.mark.asyncio
async def test_resaving_a_northern_birth_never_replays_the_chart_stored_at_utc8() -> None:
    service, repository, engine = _service()
    guest_id = uuid4()
    await service.create_date_only(guest_id=guest_id, birth_date=BIRTH_DATE, now=NOW)
    stale = _expected(engine, "vn-hanoi", 8)
    legacy_key = SecretHasher(b"h" * 32).digest(
        "birth-input", f"supplement-v1:{BIRTH_DATE.isoformat()}:exact:{BIRTH_TIME}:None:vn-hanoi"
    )
    current = repository.current[guest_id]
    repository.by_input[(guest_id, legacy_key)] = BirthSnapshotRecord(
        id=uuid4(),
        guest_id=guest_id,
        profile_id=current.profile_id,
        input_hash=legacy_key,
        birth_date_ciphertext=current.birth_date_ciphertext,
        result=stale,
        created_at=NOW,
    )
    result = await service.add_supplement(
        guest_id=guest_id,
        birth_time_mode=BirthTimeMode.EXACT,
        birth_time_local=BIRTH_TIME,
        approx_window=None,
        place_id="vn-hanoi",
        consent_version=CONSENT,
        now=NOW,
    )
    assert result.chart is not None
    assert result.chart.julian_day_ut == _expected(engine, "vn-hanoi", 7).julian_day_ut


@pytest.mark.asyncio
async def test_straddling_province_is_marked_approximate_not_guessed() -> None:
    service, _, engine = _service()
    guest_id, chart = await _with_supplement(service, "vn-quang-tri")
    assert chart.time_precision is TimePrecision.APPROXIMATE
    assert chart.julian_day_ut == _expected(engine, "vn-quang-tri", 7.5).julian_day_ut
    on_read = await service.chart_for_config(guest_id, CalculationConfig.western_recommended())
    assert on_read is not None
    assert on_read.time_precision is TimePrecision.APPROXIMATE
    assert (on_read.houses, on_read.angles) == (None, None)


@pytest.mark.asyncio
async def test_recompute_on_read_picks_up_the_northern_offset() -> None:
    # chart_for_config re-derives the instant from the encrypted inputs on every read, so an
    # existing northern profile gets the corrected chart without any data migration.
    service, _, engine = _service()
    guest_id, _ = await _with_supplement(service, "vn-former-quang-binh")
    on_read = await service.chart_for_config(guest_id, CalculationConfig.western_recommended())
    assert on_read is not None
    expected = _expected(engine, "vn-former-quang-binh", 7)
    assert on_read.julian_day_ut == expected.julian_day_ut
    assert on_read.time_precision is TimePrecision.EXACT
    assert on_read.angles == expected.angles


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("place_id", "hours", "precision"),
    [
        ("vn-ha-tinh", 7, TimePrecision.EXACT),
        ("vn-hue", 8, TimePrecision.EXACT),
        ("vn-quang-tri", 7.5, TimePrecision.APPROXIMATE),
    ],
)
async def test_transient_partner_chart_follows_the_same_rule(
    place_id: str, hours: float, precision: TimePrecision
) -> None:
    service, _, engine = _service()
    chart = await service.calculate_transient_chart(
        birth_date=BIRTH_DATE,
        birth_time_local=BIRTH_TIME,
        place_id=place_id,
        config=CalculationConfig.western_recommended(),
        now=NOW,
    )
    assert chart.julian_day_ut == _expected(engine, place_id, hours).julian_day_ut
    assert chart.time_precision is precision
    assert (chart.houses is None) is (precision is TimePrecision.APPROXIMATE)
