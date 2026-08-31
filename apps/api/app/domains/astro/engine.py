from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from app.domains.astro.aspects import calculate_aspects
from app.domains.astro.ffi import SwissEphemerisNative
from app.domains.astro.models import (
    BodyName,
    BodyPosition,
    ChartAngles,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    HousePosition,
    HouseSystem,
    NatalChart,
    ZodiacSign,
)

BODY_IDS: tuple[tuple[BodyName, int], ...] = (
    (BodyName.SUN, 0),
    (BodyName.MOON, 1),
    (BodyName.MERCURY, 2),
    (BodyName.VENUS, 3),
    (BodyName.MARS, 4),
    (BodyName.JUPITER, 5),
    (BodyName.SATURN, 6),
    (BodyName.URANUS, 7),
    (BodyName.NEPTUNE, 8),
    (BodyName.PLUTO, 9),
    (BodyName.TRUE_NODE, 11),
    (BodyName.CHIRON, 15),
)
SIGNS = tuple(ZodiacSign)
HOUSE_CODES = {
    HouseSystem.PLACIDUS: "P",
    HouseSystem.WHOLE_SIGN: "W",
}


def normalize_longitude(value: float) -> float:
    return value % 360.0


def sign_for_longitude(longitude: float) -> ZodiacSign:
    return SIGNS[int(normalize_longitude(longitude) // 30)]


def decimal_utc_hour(value: datetime) -> float:
    utc_value = value.astimezone(UTC)
    return (
        utc_value.hour
        + utc_value.minute / 60.0
        + utc_value.second / 3600.0
        + utc_value.microsecond / 3_600_000_000.0
    )


class NatalChartEngine:
    def __init__(
        self,
        native: SwissEphemerisNative | None = None,
        profile: str = "astro_reference_v1",
    ) -> None:
        self._native = native or SwissEphemerisNative()
        self._profile = profile

    @property
    def provenance(self) -> EngineProvenance:
        return EngineProvenance(version=self._native.version, profile=self._profile)

    def _julian_day(self, value: datetime) -> float:
        utc_value = value.astimezone(UTC)
        return self._native.julian_day(
            utc_value.year,
            utc_value.month,
            utc_value.day,
            decimal_utc_hour(utc_value),
        )

    def _body_position(self, julian_day_ut: float, body: BodyName, body_id: int) -> BodyPosition:
        native = self._native.calculate(julian_day_ut, body_id)
        longitude = normalize_longitude(native.longitude)
        return BodyPosition(
            body=body,
            longitude=longitude,
            latitude=native.latitude,
            distance_au=native.distance_au,
            longitude_speed=native.longitude_speed,
            retrograde=native.longitude_speed < 0,
            sign=sign_for_longitude(longitude),
            degree_in_sign=longitude % 30.0,
        )

    def calculate_chart(self, chart_input: ChartInput) -> NatalChart:
        julian_day_ut = self._julian_day(chart_input.utc_datetime)
        bodies = tuple(
            self._body_position(julian_day_ut, body, body_id) for body, body_id in BODY_IDS
        )
        houses: tuple[HousePosition, ...] | None = None
        angles: ChartAngles | None = None
        if chart_input.latitude is not None and chart_input.longitude is not None:
            native_houses = self._native.houses(
                julian_day_ut,
                chart_input.latitude,
                chart_input.longitude,
                HOUSE_CODES[chart_input.house_system],
            )
            houses = tuple(
                HousePosition(
                    number=index,
                    longitude=normalize_longitude(longitude),
                    sign=sign_for_longitude(longitude),
                )
                for index, longitude in enumerate(native_houses.cusps, start=1)
            )
            angles = ChartAngles(
                ascendant=normalize_longitude(native_houses.ascendant),
                midheaven=normalize_longitude(native_houses.midheaven),
                armc=normalize_longitude(native_houses.armc),
                vertex=normalize_longitude(native_houses.vertex),
            )
        return NatalChart(
            julian_day_ut=julian_day_ut,
            bodies=bodies,
            houses=houses,
            angles=angles,
            aspects=calculate_aspects(bodies),
            provenance=self.provenance,
        )

    def calculate_date_only_sun(self, birth_date: date) -> DateOnlySunResult:
        # A civil date can occur anywhere from UTC+14 to UTC-12. Cover the complete
        # interval instead of inventing a noon birth time.
        interval_start = datetime.combine(birth_date, time.min, tzinfo=UTC) - timedelta(hours=14)
        interval_end = datetime.combine(birth_date, time.max, tzinfo=UTC) + timedelta(hours=12)
        samples: list[ZodiacSign] = []
        cursor = interval_start
        while cursor < interval_end:
            sun = self._body_position(self._julian_day(cursor), BodyName.SUN, 0)
            if sun.sign not in samples:
                samples.append(sun.sign)
            cursor += timedelta(hours=6)
        final_sun = self._body_position(self._julian_day(interval_end), BodyName.SUN, 0)
        if final_sun.sign not in samples:
            samples.append(final_sun.sign)

        certain = len(samples) == 1
        return DateOnlySunResult(
            birth_date=birth_date,
            status="certain" if certain else "candidates",
            sign=samples[0] if certain else None,
            candidates=tuple(samples),
            interval_start_utc=interval_start,
            interval_end_utc=interval_end,
            provenance=self.provenance,
        )
