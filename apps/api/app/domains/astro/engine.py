from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, date, datetime, time, timedelta
from threading import Lock
from typing import cast

from app.domains.astro.aspects import (
    ASPECTS,
    RELATIONSHIP_CHART_ORB_VERSION,
    SYNASTRY_ORB_VERSION,
    TRANSIT_ORB_VERSION,
    angular_distance,
    calculate_aspects,
    relationship_chart_orb_limit,
    synastry_orb_limit,
    transit_orb_limit,
)
from app.domains.astro.ffi import SwissEphemerisNative
from app.domains.astro.models import (
    Ayanamsa,
    BodyName,
    BodyPosition,
    CalculationConfig,
    ChartAngles,
    ChartInput,
    ChartType,
    CompatibilityScore,
    CompositeAspect,
    CompositeChart,
    CompositePoint,
    ContactTone,
    DateOnlySunResult,
    DavisonRelationshipChart,
    EngineProvenance,
    GrahaDrishti,
    HouseOverlay,
    HousePosition,
    HouseSystem,
    NakshatraPosition,
    NatalChart,
    NavamsaChart,
    NavamsaPoint,
    NodeMode,
    RelationshipBundle,
    RelationshipDimension,
    RelationshipDimensionEvidence,
    SynastryContact,
    SynastryFacts,
    TimePrecision,
    Tradition,
    TransitPhase,
    TransitSnapshot,
    TransitToNatalContact,
    TransitToNatalSnapshot,
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
    HouseSystem.EQUAL: "E",
}
AYANAMSA_IDS = {
    Ayanamsa.LAHIRI: 1,
    Ayanamsa.RAMAN: 3,
    Ayanamsa.KRISHNAMURTI: 5,
}
NAKSHATRAS = (
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
)
CLASSICAL_GRAHAS = (
    BodyName.SUN,
    BodyName.MOON,
    BodyName.MERCURY,
    BodyName.VENUS,
    BodyName.MARS,
    BodyName.JUPITER,
    BodyName.SATURN,
)


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
        self._transit_cache: OrderedDict[
            tuple[float, bool, int | None, str], tuple[BodyPosition, ...]
        ] = OrderedDict()
        self._transit_cache_lock = Lock()

    def provenance_for(self, config: CalculationConfig) -> EngineProvenance:
        return EngineProvenance(
            version=self._native.version,
            profile=self._profile,
            tradition=config.tradition,
            zodiac=config.zodiac,
            ayanamsa=config.ayanamsa,
            config_hash=config.fingerprint,
        )

    @property
    def provenance(self) -> EngineProvenance:
        return self.provenance_for(CalculationConfig.western_recommended())

    def _julian_day(self, value: datetime) -> float:
        utc_value = value.astimezone(UTC)
        return self._native.julian_day(
            utc_value.year,
            utc_value.month,
            utc_value.day,
            decimal_utc_hour(utc_value),
        )

    def _body_position(
        self,
        julian_day_ut: float,
        body: BodyName,
        body_id: int,
        *,
        sidereal: bool = False,
    ) -> BodyPosition:
        native = self._native.calculate(julian_day_ut, body_id, sidereal=sidereal)
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

    def calculate_chart(
        self,
        chart_input: ChartInput,
        config: CalculationConfig | None = None,
    ) -> NatalChart:
        resolved = config or CalculationConfig(
            house_system=chart_input.house_system,
        )
        julian_day_ut = self._julian_day(chart_input.utc_datetime)
        sidereal = resolved.tradition is Tradition.JYOTISH
        sidereal_mode = AYANAMSA_IDS[resolved.ayanamsa] if resolved.ayanamsa else None
        with self._native.calculation_scope(sidereal_mode):
            node_body = (
                (BodyName.TRUE_NODE, 11)
                if resolved.node_mode is NodeMode.TRUE
                else (BodyName.MEAN_NODE, 10)
            )
            body_ids = tuple(item for item in BODY_IDS if item[0] is not BodyName.TRUE_NODE)
            body_ids += (node_body,)
            body_list = [
                self._body_position(julian_day_ut, body, body_id, sidereal=sidereal)
                for body, body_id in body_ids
            ]
            if resolved.tradition is Tradition.JYOTISH:
                node = body_list[-1]
                body_list.append(
                    BodyPosition(
                        body=BodyName.SOUTH_NODE,
                        longitude=normalize_longitude(node.longitude + 180),
                        latitude=-node.latitude,
                        distance_au=node.distance_au,
                        longitude_speed=node.longitude_speed,
                        retrograde=node.retrograde,
                        sign=sign_for_longitude(node.longitude + 180),
                        degree_in_sign=normalize_longitude(node.longitude + 180) % 30,
                    )
                )
            bodies = tuple(body_list)
            houses: tuple[HousePosition, ...] | None = None
            angles: ChartAngles | None = None
            if chart_input.latitude is not None and chart_input.longitude is not None:
                native_houses = self._native.houses(
                    julian_day_ut,
                    chart_input.latitude,
                    chart_input.longitude,
                    HOUSE_CODES[resolved.house_system],
                    sidereal=sidereal,
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
        nakshatras = _nakshatras(bodies) if resolved.tradition is Tradition.JYOTISH else ()
        drishti = _graha_drishti(bodies) if resolved.tradition is Tradition.JYOTISH else ()
        return NatalChart(
            chart_type=ChartType.NATAL,
            julian_day_ut=julian_day_ut,
            bodies=bodies,
            houses=houses,
            angles=angles,
            aspects=calculate_aspects(bodies),
            house_system=resolved.house_system,
            time_precision=TimePrecision.EXACT,
            provenance=self.provenance_for(resolved),
            config=resolved,
            config_hash=resolved.fingerprint,
            nakshatras=nakshatras,
            graha_drishti=drishti,
        )

    def calculate_daily_transit(
        self, transit_date: date, config: CalculationConfig | None = None
    ) -> TransitSnapshot:
        resolved = config or CalculationConfig.western_recommended()
        transit_datetime = datetime.combine(transit_date, time(hour=12), tzinfo=UTC)
        julian_day_ut = self._julian_day(transit_datetime)
        sidereal = resolved.tradition is Tradition.JYOTISH
        sidereal_mode = AYANAMSA_IDS[resolved.ayanamsa] if resolved.ayanamsa else None
        bodies = self._transiting_bodies(
            julian_day_ut,
            sidereal,
            sidereal_mode,
            resolved.node_mode,
            resolved.fingerprint,
        )
        return TransitSnapshot(
            transit_date=transit_date,
            julian_day_ut=julian_day_ut,
            bodies=bodies,
            provenance=self.provenance_for(resolved),
            config=resolved,
            config_hash=resolved.fingerprint,
        )

    def calculate_transit_to_natal(
        self,
        natal: NatalChart,
        observed_at: datetime,
    ) -> TransitToNatalSnapshot:
        """Calculate factual transit contacts at an exact instant.

        This layer deliberately returns geometry, not interpretations. Phase is
        derived from the current longitudinal speeds; exact means within 0.2°.
        """
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        resolved = natal.config
        julian_day_ut = self._julian_day(observed_at)
        sidereal = resolved.tradition is Tradition.JYOTISH
        sidereal_mode = AYANAMSA_IDS[resolved.ayanamsa] if resolved.ayanamsa else None
        transiting = self._transiting_bodies(
            julian_day_ut,
            sidereal,
            sidereal_mode,
            resolved.node_mode,
            resolved.fingerprint,
        )
        future_julian_day_ut = self._julian_day(observed_at + timedelta(hours=1))
        future_transiting = {
            position.body: position
            for position in self._transiting_bodies(
                future_julian_day_ut,
                sidereal,
                sidereal_mode,
                resolved.node_mode,
                resolved.fingerprint,
            )
        }

        contacts: list[TransitToNatalContact] = []
        for transit in transiting:
            for natal_body in natal.bodies:
                separation = angular_distance(transit.longitude, natal_body.longitude)
                for kind, exact_angle, _ in ASPECTS:
                    orb = abs(separation - exact_angle)
                    if orb > transit_orb_limit(transit.body, kind):
                        continue
                    phase = _transit_phase(
                        future_transiting[transit.body].longitude,
                        natal_body.longitude,
                        exact_angle,
                        orb,
                    )
                    contacts.append(
                        TransitToNatalContact(
                            transit_body=transit.body,
                            natal_body=natal_body.body,
                            kind=kind,
                            exact_angle=exact_angle,
                            orb=round(orb, 4),
                            phase=phase,
                        )
                    )
                    break
        return TransitToNatalSnapshot(
            observed_at=observed_at.astimezone(UTC),
            contacts=tuple(sorted(contacts, key=lambda item: item.orb)),
            orb_policy_version=TRANSIT_ORB_VERSION,
            provenance=self.provenance_for(resolved),
            config=resolved,
            config_hash=resolved.fingerprint,
        )

    def _transiting_bodies(
        self,
        julian_day_ut: float,
        sidereal: bool,
        sidereal_mode: int | None,
        node_mode: NodeMode,
        config_hash: str,
    ) -> tuple[BodyPosition, ...]:
        """Reuse non-personal sky positions for identical instant/config keys."""
        key = (julian_day_ut, sidereal, sidereal_mode, config_hash)
        with self._transit_cache_lock:
            cached = self._transit_cache.get(key)
            if cached is not None:
                self._transit_cache.move_to_end(key)
                return cached
        with self._native.calculation_scope(sidereal_mode):
            node_body = (
                (BodyName.TRUE_NODE, 11) if node_mode is NodeMode.TRUE else (BodyName.MEAN_NODE, 10)
            )
            body_ids = tuple(
                node_body if body is BodyName.TRUE_NODE else (body, body_id)
                for body, body_id in BODY_IDS
            )
            calculated = tuple(
                self._body_position(julian_day_ut, body, body_id, sidereal=sidereal)
                for body, body_id in body_ids
            )
        with self._transit_cache_lock:
            self._transit_cache[key] = calculated
            self._transit_cache.move_to_end(key)
            if len(self._transit_cache) > 256:
                self._transit_cache.popitem(last=False)
        return calculated

    def calculate_synastry(self, chart_a: NatalChart, chart_b: NatalChart) -> SynastryFacts:
        _validate_relationship_pair(chart_a, chart_b)
        contacts: list[SynastryContact] = []
        for body_a in chart_a.bodies:
            for body_b in chart_b.bodies:
                separation = angular_distance(body_a.longitude, body_b.longitude)
                for kind, exact_angle, _ in ASPECTS:
                    orb = abs(separation - exact_angle)
                    maximum_orb = synastry_orb_limit(body_a.body, body_b.body, kind)
                    if orb > maximum_orb:
                        continue
                    contacts.append(
                        SynastryContact(
                            body_a=body_a.body,
                            body_b=body_b.body,
                            kind=kind,
                            exact_angle=exact_angle,
                            orb=round(orb, 4),
                            strength=round(max(0.0, 1.0 - orb / maximum_orb), 4),
                            tone=_relationship_tone(kind),
                            dimensions=_relationship_dimensions(body_a.body, body_b.body, kind),
                        )
                    )
                    break
        overlays = _house_overlays(chart_a, chart_b)
        return SynastryFacts(
            contacts=tuple(sorted(contacts, key=lambda item: (-item.strength, item.orb))),
            house_overlays=overlays,
            orb_policy_version=SYNASTRY_ORB_VERSION,
            provenance=chart_a.provenance,
        )

    def calculate_composite_midpoint(
        self, chart_a: NatalChart, chart_b: NatalChart
    ) -> CompositeChart:
        _validate_relationship_pair(chart_a, chart_b)
        by_body_b = {position.body: position for position in chart_b.bodies}
        points: list[CompositePoint] = []
        for position_a in chart_a.bodies:
            position_b = by_body_b.get(position_a.body)
            if position_b is None:
                continue
            longitude = midpoint_longitude(position_a.longitude, position_b.longitude)
            points.append(
                CompositePoint(
                    body=position_a.body,
                    longitude=longitude,
                    sign=sign_for_longitude(longitude),
                    degree_in_sign=longitude % 30.0,
                )
            )
        aspects: list[CompositeAspect] = []
        for index, point_a in enumerate(points):
            for point_b in points[index + 1 :]:
                separation = angular_distance(point_a.longitude, point_b.longitude)
                for kind, exact_angle, _ in ASPECTS:
                    orb = abs(separation - exact_angle)
                    maximum_orb = relationship_chart_orb_limit(kind)
                    if orb > maximum_orb:
                        continue
                    aspects.append(
                        CompositeAspect(
                            body_a=point_a.body,
                            body_b=point_b.body,
                            kind=kind,
                            exact_angle=exact_angle,
                            orb=round(orb, 4),
                            strength=round(max(0.0, 1.0 - orb / maximum_orb), 4),
                        )
                    )
                    break
        return CompositeChart(
            points=tuple(points),
            aspects=tuple(sorted(aspects, key=lambda item: (-item.strength, item.orb))),
            orb_policy_version=RELATIONSHIP_CHART_ORB_VERSION,
            provenance=chart_a.provenance,
        )

    def calculate_davison_relationship(
        self,
        input_a: ChartInput,
        input_b: ChartInput,
        config: CalculationConfig | None = None,
    ) -> DavisonRelationshipChart:
        """Calculate the uncorrected time/place midpoint relationship chart."""
        latitude_a = input_a.latitude
        longitude_a = input_a.longitude
        latitude_b = input_b.latitude
        longitude_b = input_b.longitude
        if None in {latitude_a, longitude_a, latitude_b, longitude_b}:
            raise ValueError("Davison relationship chart requires both exact birth places")
        latitude_a = cast(float, latitude_a)
        longitude_a = cast(float, longitude_a)
        latitude_b = cast(float, latitude_b)
        longitude_b = cast(float, longitude_b)
        resolved = config or CalculationConfig(
            house_system=input_a.house_system,
        )
        if resolved.tradition is not Tradition.WESTERN:
            raise ValueError("Davison v1 is available for Western charts only")
        timestamp = (
            input_a.utc_datetime.astimezone(UTC).timestamp()
            + input_b.utc_datetime.astimezone(UTC).timestamp()
        ) / 2
        midpoint_input = ChartInput(
            utc_datetime=datetime.fromtimestamp(timestamp, tz=UTC),
            latitude=(latitude_a + latitude_b) / 2,
            longitude=(longitude_a + longitude_b) / 2,
            house_system=resolved.house_system,
        )
        chart = self.calculate_chart(midpoint_input, resolved)
        return DavisonRelationshipChart(
            midpoint_input=midpoint_input,
            chart=chart,
            provenance=chart.provenance,
        )

    def calculate_navamsa(self, chart: NatalChart) -> NavamsaChart:
        """Return factual D9 positions without interpretation or house claims."""
        if chart.config.tradition is not Tradition.JYOTISH:
            raise ValueError("Navamsa requires a Jyotish sidereal chart")
        if chart.time_precision is not TimePrecision.EXACT:
            raise ValueError("Navamsa requires exact birth time")
        points = tuple(
            NavamsaPoint(
                body=body.body,
                source_longitude=body.longitude,
                longitude=navamsa_longitude(body.longitude),
                sign=sign_for_longitude(navamsa_longitude(body.longitude)),
                degree_in_sign=navamsa_longitude(body.longitude) % 30,
            )
            for body in chart.bodies
        )
        return NavamsaChart(points=points, provenance=chart.provenance)

    def calculate_relationship_bundle(
        self,
        chart_a: NatalChart,
        chart_b: NatalChart,
        *,
        input_a: ChartInput | None = None,
        input_b: ChartInput | None = None,
    ) -> RelationshipBundle:
        _validate_relationship_pair(chart_a, chart_b)
        if chart_a.config.tradition is not Tradition.WESTERN:
            raise ValueError("Relationship bundle v1 supports Western charts only")
        synastry = self.calculate_synastry(chart_a, chart_b)
        composite = self.calculate_composite_midpoint(chart_a, chart_b)
        davison = None
        if input_a is not None and input_b is not None:
            davison = self.calculate_davison_relationship(input_a, input_b, chart_a.config)
        dimensions = summarize_synastry_dimensions(synastry)
        return RelationshipBundle(
            synastry=synastry,
            composite=composite,
            davison=davison,
            dimensions=dimensions,
            provenance=chart_a.provenance,
        )

    def calculate_compatibility(
        self, chart_a: NatalChart, chart_b: NatalChart
    ) -> CompatibilityScore:
        synastry = self.calculate_synastry(chart_a, chart_b)
        moon = _body_score(synastry.contacts, (BodyName.MOON,))
        venus = _body_score(synastry.contacts, (BodyName.VENUS,))
        mars = _body_score(synastry.contacts, (BodyName.MARS,))
        total = (moon * 0.36) + (venus * 0.34) + (mars * 0.30)
        return CompatibilityScore(
            moon_score=moon,
            venus_score=venus,
            mars_score=mars,
            total_score=round(total, 4),
            strongest_contacts=tuple(sorted(synastry.contacts, key=lambda item: item.orb)[:5]),
            provenance=chart_a.provenance,
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
            chart_type=ChartType.DATE_ONLY_NATAL,
            status="certain" if certain else "candidates",
            sign=samples[0] if certain else None,
            candidates=tuple(samples),
            provenance=self.provenance,
        )


def _transit_phase(
    future_transit_longitude: float,
    natal_longitude: float,
    exact_angle: float,
    orb: float,
) -> TransitPhase:
    if orb <= 0.2:
        return TransitPhase.EXACT
    future_separation = angular_distance(future_transit_longitude, natal_longitude)
    future_orb = abs(future_separation - exact_angle)
    return TransitPhase.APPROACHING if future_orb < orb else TransitPhase.SEPARATING


def midpoint_longitude(first: float, second: float) -> float:
    first = normalize_longitude(first)
    second = normalize_longitude(second)
    diff = (second - first + 540.0) % 360.0 - 180.0
    return normalize_longitude(first + diff / 2.0)


def navamsa_longitude(sidereal_longitude: float) -> float:
    """Map a sidereal D1 longitude to its D9 longitude across all 108 cells."""
    return normalize_longitude(sidereal_longitude * 9)


def house_for_longitude(longitude: float, houses: tuple[HousePosition, ...]) -> int:
    """Place a longitude in versioned half-open cusp intervals."""
    if len(houses) != 12:
        raise ValueError("house placement requires twelve cusps")
    value = normalize_longitude(longitude)
    ordered = sorted(houses, key=lambda item: item.number)
    for index, house in enumerate(ordered):
        start = normalize_longitude(house.longitude)
        end = normalize_longitude(ordered[(index + 1) % 12].longitude)
        span = (end - start) % 360
        offset = (value - start) % 360
        if offset < span:
            return house.number
    # A degenerate cusp set should fail rather than inventing a placement.
    raise ValueError("longitude could not be assigned to a house")


def _validate_relationship_pair(chart_a: NatalChart, chart_b: NatalChart) -> None:
    if chart_a.config_hash != chart_b.config_hash:
        raise ValueError("relationship charts require identical calculation config")
    if chart_a.config.tradition is not chart_b.config.tradition:
        raise ValueError("relationship charts require the same tradition")


def _house_overlays(chart_a: NatalChart, chart_b: NatalChart) -> tuple[HouseOverlay, ...]:
    if chart_a.houses is None or chart_b.houses is None:
        return ()
    overlays: list[HouseOverlay] = []
    for body in chart_a.bodies:
        overlays.append(
            HouseOverlay(
                body_owner="a",
                body=body.body,
                house_owner="b",
                house=house_for_longitude(body.longitude, chart_b.houses),
                target_house_system=chart_b.house_system,
            )
        )
    for body in chart_b.bodies:
        overlays.append(
            HouseOverlay(
                body_owner="b",
                body=body.body,
                house_owner="a",
                house=house_for_longitude(body.longitude, chart_a.houses),
                target_house_system=chart_a.house_system,
            )
        )
    return tuple(overlays)


def _relationship_tone(kind: str) -> ContactTone:
    if kind in {"trine", "sextile"}:
        return ContactTone.FLOW
    if kind in {"square", "opposition"}:
        return ContactTone.ACTIVATION
    return ContactTone.MIXED


def _relationship_dimensions(
    body_a: BodyName,
    body_b: BodyName,
    kind: str,
) -> tuple[RelationshipDimension, ...]:
    bodies = {body_a, body_b}
    dimensions: list[RelationshipDimension] = []
    if BodyName.MERCURY in bodies:
        dimensions.append(RelationshipDimension.COMMUNICATION)
    if BodyName.MOON in bodies:
        dimensions.append(RelationshipDimension.EMOTIONAL)
    if BodyName.VENUS in bodies:
        dimensions.append(RelationshipDimension.RELATING)
    if BodyName.MARS in bodies:
        dimensions.append(RelationshipDimension.DRIVE)
    if bodies & {BodyName.JUPITER, BodyName.SATURN, BodyName.SUN}:
        dimensions.append(RelationshipDimension.GROWTH)
    if kind in {"square", "opposition"}:
        dimensions.append(RelationshipDimension.FRICTION)
    if not dimensions:
        dimensions.append(RelationshipDimension.RELATING)
    return tuple(dict.fromkeys(dimensions))


def _dimension_evidence(
    dimension: RelationshipDimension,
    contacts: tuple[SynastryContact, ...],
) -> RelationshipDimensionEvidence:
    relevant = [contact for contact in contacts if dimension in contact.dimensions]
    identifiers = tuple(
        f"synastry:{contact.body_a.value}:{contact.body_b.value}:{contact.kind}"
        for contact in relevant[:5]
    )
    return RelationshipDimensionEvidence(
        dimension=dimension,
        contact_count=len(relevant),
        evidence_ids=identifiers,
        strongest_strength=max((contact.strength for contact in relevant), default=0.0),
    )


def summarize_synastry_dimensions(
    synastry: SynastryFacts,
) -> tuple[RelationshipDimensionEvidence, ...]:
    """Create the privacy-minimized multidimensional projection for consumers."""
    return tuple(
        _dimension_evidence(dimension, synastry.contacts) for dimension in RelationshipDimension
    )


def _body_score(contacts: tuple[SynastryContact, ...], bodies: tuple[BodyName, ...]) -> float:
    relevant = [
        contact for contact in contacts if contact.body_a in bodies or contact.body_b in bodies
    ]
    if not relevant:
        return 0.0
    best = min(relevant, key=lambda item: item.orb)
    return round(max(0.0, 1.0 - (best.orb / 8.0)), 4)


def _nakshatras(bodies: tuple[BodyPosition, ...]) -> tuple[NakshatraPosition, ...]:
    span = 360 / 27
    pada_span = span / 4
    results: list[NakshatraPosition] = []
    for body in bodies:
        offset = normalize_longitude(body.longitude)
        index = min(int(offset // span), 26)
        degree = offset - index * span
        results.append(
            NakshatraPosition(
                body=body.body,
                name=NAKSHATRAS[index],
                index=index + 1,
                pada=min(int(degree // pada_span) + 1, 4),
                degree_in_nakshatra=degree,
            )
        )
    return tuple(results)


def _graha_drishti(bodies: tuple[BodyPosition, ...]) -> tuple[GrahaDrishti, ...]:
    by_body = {item.body: item for item in bodies}
    special = {
        BodyName.MARS: {4, 8},
        BodyName.JUPITER: {5, 9},
        BodyName.SATURN: {3, 10},
    }
    results: list[GrahaDrishti] = []
    for source_name in CLASSICAL_GRAHAS:
        source = by_body[source_name]
        source_sign = int(source.longitude // 30)
        valid_houses = {7, *special.get(source_name, set())}
        for target_name in CLASSICAL_GRAHAS:
            if target_name is source_name:
                continue
            target_sign = int(by_body[target_name].longitude // 30)
            houses_apart = ((target_sign - source_sign) % 12) + 1
            if houses_apart in valid_houses:
                kind = "special" if houses_apart != 7 else "opposition"
                results.append(
                    GrahaDrishti(
                        from_body=source_name,
                        to_body=target_name,
                        houses_apart=houses_apart,
                        kind=kind,
                    )
                )
    return tuple(results)
