from __future__ import annotations

import json
from datetime import date
from hashlib import sha256

from app.domains.astro.aspects import ASPECTS, transit_orb_limit
from app.domains.astro.models import (
    Aspect,
    BodyName,
    DateOnlySunResult,
    GrahaDrishti,
    NakshatraPosition,
    NatalChart,
    TimePrecision,
    Tradition,
    TransitToNatalContact,
    TransitToNatalSnapshot,
)
from app.domains.readings.models import (
    JYOTISH_INTERPRETATION_KNOWLEDGE_VERSION,
    WESTERN_INTERPRETATION_KNOWLEDGE_VERSION,
    BackgroundLens,
    CompositionTarget,
    DerivedFactor,
    FactorConfidence,
    FactorKind,
    FactorRole,
    FactorSource,
    PlanMode,
    ReadingDomain,
    ReadingPlan,
    ReadingPurpose,
    _normalized_vietnamese_word_count,
)

PLANNER_RULES_VERSION = "factor-planner-v2"
TRANSIT_SALIENCE_THRESHOLD = 0.45

_PERSONAL_BODIES = {
    BodyName.SUN,
    BodyName.MOON,
    BodyName.MERCURY,
    BodyName.VENUS,
    BodyName.MARS,
}
_JYOTISH_BODIES = _PERSONAL_BODIES | {
    BodyName.JUPITER,
    BodyName.SATURN,
    BodyName.TRUE_NODE,
    BodyName.MEAN_NODE,
    BodyName.SOUTH_NODE,
}
_BODY_DOMAIN = {
    BodyName.SUN: ReadingDomain.CORE,
    BodyName.MOON: ReadingDomain.EMOTIONS,
    BodyName.MERCURY: ReadingDomain.MIND,
    BodyName.VENUS: ReadingDomain.RELATING,
    BodyName.MARS: ReadingDomain.DRIVE,
    BodyName.JUPITER: ReadingDomain.CORE,
    BodyName.SATURN: ReadingDomain.CORE,
    BodyName.URANUS: ReadingDomain.CORE,
    BodyName.NEPTUNE: ReadingDomain.EMOTIONS,
    BodyName.PLUTO: ReadingDomain.DRIVE,
    BodyName.TRUE_NODE: ReadingDomain.CORE,
    BodyName.MEAN_NODE: ReadingDomain.CORE,
    BodyName.SOUTH_NODE: ReadingDomain.CORE,
    BodyName.CHIRON: ReadingDomain.EMOTIONS,
}
_BODY_SALIENCE = {
    BodyName.SUN: 1.0,
    BodyName.MOON: 0.98,
    BodyName.MERCURY: 0.86,
    BodyName.VENUS: 0.88,
    BodyName.MARS: 0.86,
    BodyName.JUPITER: 0.72,
    BodyName.SATURN: 0.76,
    BodyName.URANUS: 0.56,
    BodyName.NEPTUNE: 0.56,
    BodyName.PLUTO: 0.58,
    BodyName.TRUE_NODE: 0.62,
    BodyName.MEAN_NODE: 0.62,
    BodyName.SOUTH_NODE: 0.6,
    BodyName.CHIRON: 0.5,
}
_TRANSIT_BODY_WEIGHT = {
    BodyName.SUN: 0.8,
    BodyName.MOON: 0.55,
    BodyName.MERCURY: 0.65,
    BodyName.VENUS: 0.7,
    BodyName.MARS: 0.75,
    BodyName.JUPITER: 1.0,
    BodyName.SATURN: 1.1,
    BodyName.URANUS: 1.15,
    BodyName.NEPTUNE: 1.15,
    BodyName.PLUTO: 1.2,
    BodyName.TRUE_NODE: 0.9,
    BodyName.MEAN_NODE: 0.9,
    BodyName.SOUTH_NODE: 0.9,
    BodyName.CHIRON: 0.8,
}
_ASPECT_LIMIT = {kind: maximum_orb for kind, _, maximum_orb in ASPECTS}
_HARMONIOUS_ASPECTS = {"sextile", "trine"}
_TENSION_ASPECTS = {"square", "opposition"}
_TRANSIT_PURPOSES = {
    ReadingPurpose.DAILY_NOTE,
    ReadingPurpose.READING_DETAIL,
    ReadingPurpose.PERSONALIZED_SKY,
}
_MAX_NATAL_FACTORS = {
    ReadingPurpose.DAILY_NOTE: 4,
    ReadingPurpose.AURA: 5,
    ReadingPurpose.READING_DETAIL: 6,
    ReadingPurpose.PERSONALIZED_SKY: 4,
}
_PLAN_ALLOWED_LANGUAGE = (
    "reflective and probabilistic Vietnamese",
    "everyday manifestation grounded in selected factors",
    "phase-only transit timing",
)
_PLAN_FORBIDDEN_LANGUAGE = (
    "absolute personality verdicts",
    "diagnosis or professional advice",
    "event prediction or decision instructions",
    "unreferenced astrology facts",
)
_FACTOR_ALLOWED_LANGUAGE = (
    "tentative interpretation",
    "plain-language everyday pattern",
)
_FACTOR_FORBIDDEN_LANGUAGE = (
    "certainty",
    "diagnosis",
    "fate",
)


def normalized_vietnamese_word_count(text: str) -> int:
    return _normalized_vietnamese_word_count(text)


class ReadingPlanner:
    """Select and compose immutable reading factors without calculating a chart."""

    def plan(
        self,
        chart: NatalChart | DateOnlySunResult,
        *,
        purpose: ReadingPurpose,
        transits: TransitToNatalSnapshot | None = None,
        background_lens: BackgroundLens | None = None,
        editorial_seed: str | None = None,
    ) -> ReadingPlan:
        if background_lens is BackgroundLens.AUTO:
            background_lens = None
        if isinstance(chart, DateOnlySunResult):
            if transits is not None:
                raise ValueError("date-only Vibe does not accept transit contacts")
            return self._date_only_plan(chart, purpose, background_lens, editorial_seed)
        self._validate_transits(chart, transits)
        if chart.time_precision is not TimePrecision.EXACT:
            return self._limited_plan(chart, purpose, background_lens, editorial_seed)

        candidates = self._natal_candidates(chart, purpose)
        selected, hero_refs = self._select_natal(candidates, purpose, editorial_seed)
        transit_factor = self._select_transit(chart, transits, purpose, candidates)
        if transit_factor is not None:
            selected = self._include_transit_dependency(selected, candidates, transit_factor)
            selected.append(transit_factor)

        selected = self._assign_roles(selected, hero_refs)
        mode = PlanMode.FULL_SYNTHESIS if hero_refs else PlanMode.LIMITED
        composition = self._composition(has_transit=transit_factor is not None)
        return self._build_plan(
            tradition=chart.config.tradition,
            config_hash=chart.config_hash,
            purpose=purpose,
            precision=chart.time_precision,
            mode=mode,
            factors=tuple(selected),
            hero_factor_refs=hero_refs,
            composition=composition,
            background_lens=background_lens,
            editorial_seed=editorial_seed,
        )

    def _date_only_plan(
        self,
        result: DateOnlySunResult,
        purpose: ReadingPurpose,
        background_lens: BackgroundLens | None,
        editorial_seed: str | None,
    ) -> ReadingPlan:
        status_value = (
            result.sign.value
            if result.sign is not None
            else ",".join(candidate.value for candidate in result.candidates)
        )
        status_value = status_value or "unknown"
        factor_id = f"date_only:sun:vibe:{result.status}:{status_value}"
        factor = DerivedFactor(
            id=factor_id,
            tradition=result.provenance.tradition,
            source=FactorSource.NATAL,
            kind=FactorKind.DATE_ONLY_VIBE,
            domain=ReadingDomain.CORE,
            role=FactorRole.FALLBACK,
            subjects=(BodyName.SUN.value,),
            evidence_refs=(f"date_only:sun:{result.status}:{status_value}",),
            strength=1.0 if result.sign is not None else 0.5,
            salience=1.0,
            confidence=(
                FactorConfidence.MEDIUM if result.sign is not None else FactorConfidence.LIMITED
            ),
            allowed_language=("one-factor Vibe fallback", "Sun-only context"),
            forbidden_language=("full-chart synthesis", "Moon placement", "angle claims"),
        )
        return self._build_plan(
            tradition=result.provenance.tradition,
            config_hash=result.provenance.config_hash,
            purpose=purpose,
            precision=TimePrecision.UNKNOWN,
            mode=PlanMode.VIBE_FALLBACK,
            factors=(factor,),
            hero_factor_refs=(factor.id,),
            composition=self._composition(has_transit=False),
            background_lens=background_lens,
            editorial_seed=editorial_seed,
        )

    def _limited_plan(
        self,
        chart: NatalChart,
        purpose: ReadingPurpose,
        background_lens: BackgroundLens | None,
        editorial_seed: str | None,
    ) -> ReadingPlan:
        # Current NatalChart carries midpoint facts for approximate inputs but no
        # interval stability proof. Those facts are therefore ineligible.
        return self._build_plan(
            tradition=chart.config.tradition,
            config_hash=chart.config_hash,
            purpose=purpose,
            precision=chart.time_precision,
            mode=PlanMode.LIMITED,
            factors=(),
            hero_factor_refs=(),
            composition=self._composition(has_transit=False),
            background_lens=background_lens,
            editorial_seed=editorial_seed,
        )

    def _natal_candidates(
        self, chart: NatalChart, purpose: ReadingPurpose
    ) -> tuple[DerivedFactor, ...]:
        tradition = chart.config.tradition
        eligible_bodies = set(BodyName) if tradition is Tradition.WESTERN else _JYOTISH_BODIES
        factors: list[DerivedFactor] = []
        placement_ids: dict[BodyName, str] = {}
        for position in chart.bodies:
            if position.body not in eligible_bodies:
                continue
            factor_id = f"natal:{position.body.value}:sign:{position.sign.value}"
            placement_ids[position.body] = factor_id
            salience = self._purpose_salience(
                _BODY_SALIENCE[position.body], _BODY_DOMAIN[position.body], purpose
            )
            factors.append(
                DerivedFactor(
                    id=factor_id,
                    tradition=tradition,
                    source=FactorSource.NATAL,
                    kind=FactorKind.PLANET_PLACEMENT,
                    domain=_BODY_DOMAIN[position.body],
                    role=FactorRole.SUPPORTING,
                    subjects=(position.body.value,),
                    evidence_refs=(
                        factor_id,
                        f"natal:{position.body.value}:degree_in_sign:{position.degree_in_sign:.3f}",
                        f"natal:{position.body.value}:motion:"
                        f"{'retrograde' if position.retrograde else 'direct'}",
                    ),
                    strength=_BODY_SALIENCE[position.body],
                    salience=salience,
                    confidence=FactorConfidence.HIGH,
                    allowed_language=_FACTOR_ALLOWED_LANGUAGE,
                    forbidden_language=_FACTOR_FORBIDDEN_LANGUAGE,
                )
            )

        if chart.houses:
            for position in chart.bodies:
                if position.body not in placement_ids:
                    continue
                house = self._house_for_longitude(chart, position.longitude)
                if house is None:
                    continue
                factor_id = f"natal:{position.body.value}:house:{house}"
                factors.append(
                    DerivedFactor(
                        id=factor_id,
                        tradition=tradition,
                        source=FactorSource.NATAL,
                        kind=FactorKind.HOUSE_PLACEMENT,
                        domain=_BODY_DOMAIN[position.body],
                        role=FactorRole.SUPPORTING,
                        subjects=(position.body.value, f"house:{house}"),
                        evidence_refs=(factor_id,),
                        child_refs=(placement_ids[position.body],),
                        strength=0.72,
                        salience=self._purpose_salience(
                            _BODY_SALIENCE[position.body] * 0.76,
                            _BODY_DOMAIN[position.body],
                            purpose,
                        ),
                        confidence=FactorConfidence.HIGH,
                        allowed_language=_FACTOR_ALLOWED_LANGUAGE,
                        forbidden_language=_FACTOR_FORBIDDEN_LANGUAGE,
                    )
                )

        if chart.angles:
            for angle_name, longitude in (
                ("ascendant", chart.angles.ascendant),
                ("midheaven", chart.angles.midheaven),
            ):
                factor_id = f"natal:angle:{angle_name}:longitude:{longitude:.6f}"
                factors.append(
                    DerivedFactor(
                        id=factor_id,
                        tradition=tradition,
                        source=FactorSource.NATAL,
                        kind=FactorKind.ANGLE,
                        domain=(
                            ReadingDomain.CORE if angle_name == "ascendant" else ReadingDomain.DRIVE
                        ),
                        role=FactorRole.SUPPORTING,
                        subjects=(angle_name,),
                        evidence_refs=(factor_id,),
                        strength=0.82,
                        salience=0.78,
                        confidence=FactorConfidence.HIGH,
                        allowed_language=_FACTOR_ALLOWED_LANGUAGE,
                        forbidden_language=_FACTOR_FORBIDDEN_LANGUAGE,
                    )
                )

        if tradition is Tradition.WESTERN:
            factors.extend(self._western_aspect_factors(chart, placement_ids, purpose))
        else:
            factors.extend(self._jyotish_factors(chart, placement_ids, purpose))
        return tuple(sorted(factors, key=lambda item: (-item.salience, item.id)))

    def _western_aspect_factors(
        self,
        chart: NatalChart,
        placement_ids: dict[BodyName, str],
        purpose: ReadingPurpose,
    ) -> tuple[DerivedFactor, ...]:
        factors = []
        for aspect in chart.aspects:
            if aspect.body_a not in placement_ids or aspect.body_b not in placement_ids:
                continue
            first, second = sorted((aspect.body_a, aspect.body_b), key=lambda body: body.value)
            maximum_orb = _ASPECT_LIMIT.get(aspect.kind)
            if maximum_orb is None:
                continue
            exactness = max(0.0, 1.0 - aspect.orb / maximum_orb)
            factor_id = (
                f"natal:aspect:{first.value}:{aspect.kind}:{second.value}:orb:{aspect.orb:.3f}"
            )
            domain = self._shared_domain(first, second)
            factors.append(
                DerivedFactor(
                    id=factor_id,
                    tradition=Tradition.WESTERN,
                    source=FactorSource.NATAL,
                    kind=FactorKind.NATAL_ASPECT,
                    domain=domain,
                    role=self._aspect_role(aspect),
                    subjects=(first.value, second.value),
                    evidence_refs=(
                        factor_id,
                        f"natal:aspect:{first.value}:{second.value}:"
                        f"phase:{'applying' if aspect.applying else 'separating'}",
                    ),
                    child_refs=(placement_ids[first], placement_ids[second]),
                    strength=round(exactness, 6),
                    salience=self._purpose_salience(0.7 + exactness * 0.45, domain, purpose),
                    confidence=FactorConfidence.HIGH,
                    allowed_language=_FACTOR_ALLOWED_LANGUAGE,
                    forbidden_language=_FACTOR_FORBIDDEN_LANGUAGE,
                )
            )
        return tuple(factors)

    def _jyotish_factors(
        self,
        chart: NatalChart,
        placement_ids: dict[BodyName, str],
        purpose: ReadingPurpose,
    ) -> tuple[DerivedFactor, ...]:
        factors = [
            factor
            for item in chart.nakshatras
            if (factor := self._nakshatra_factor(item, placement_ids, purpose)) is not None
        ]
        factors.extend(
            factor
            for item in chart.graha_drishti
            if (factor := self._drishti_factor(item, placement_ids, purpose)) is not None
        )
        return tuple(factors)

    def _nakshatra_factor(
        self,
        item: NakshatraPosition,
        placement_ids: dict[BodyName, str],
        purpose: ReadingPurpose,
    ) -> DerivedFactor | None:
        if item.body not in placement_ids:
            return None
        factor_id = f"jyotish:{item.body.value}:nakshatra:{item.index}:pada:{item.pada}"
        domain = _BODY_DOMAIN[item.body]
        return DerivedFactor(
            id=factor_id,
            tradition=Tradition.JYOTISH,
            source=FactorSource.NATAL,
            kind=FactorKind.NAKSHATRA,
            domain=domain,
            role=FactorRole.SUPPORTING,
            subjects=(item.body.value,),
            evidence_refs=(factor_id, f"jyotish:nakshatra:name:{item.name}"),
            child_refs=(placement_ids[item.body],),
            strength=0.86,
            salience=self._purpose_salience(0.92, domain, purpose),
            confidence=FactorConfidence.HIGH,
            allowed_language=("Jyotish vocabulary only",),
            forbidden_language=("Western aspect vocabulary",),
        )

    def _drishti_factor(
        self,
        item: GrahaDrishti,
        placement_ids: dict[BodyName, str],
        purpose: ReadingPurpose,
    ) -> DerivedFactor | None:
        if item.from_body not in placement_ids or item.to_body not in placement_ids:
            return None
        factor_id = (
            f"jyotish:drishti:{item.from_body.value}:{item.to_body.value}:"
            f"houses:{item.houses_apart}:{item.kind}"
        )
        domain = self._shared_domain(item.from_body, item.to_body)
        return DerivedFactor(
            id=factor_id,
            tradition=Tradition.JYOTISH,
            source=FactorSource.NATAL,
            kind=FactorKind.GRAHA_DRISHTI,
            domain=domain,
            role=FactorRole.REINFORCEMENT,
            subjects=(item.from_body.value, item.to_body.value),
            evidence_refs=(factor_id,),
            child_refs=(placement_ids[item.from_body], placement_ids[item.to_body]),
            strength=0.82,
            salience=self._purpose_salience(0.94, domain, purpose),
            confidence=FactorConfidence.HIGH,
            allowed_language=("Jyotish vocabulary only",),
            forbidden_language=("Western aspect vocabulary",),
        )

    def _select_natal(
        self,
        candidates: tuple[DerivedFactor, ...],
        purpose: ReadingPurpose,
        editorial_seed: str | None,
    ) -> tuple[list[DerivedFactor], tuple[str, ...]]:
        maximum = _MAX_NATAL_FACTORS[purpose]
        by_id = {factor.id: factor for factor in candidates}
        selected: list[DerivedFactor] = []
        selected_ids: set[str] = set()

        higher_order_candidates = [
            factor
            for factor in candidates
            if len(factor.child_refs) >= 2
            and all(child_ref in by_id for child_ref in factor.child_refs)
        ]
        if purpose is ReadingPurpose.DAILY_NOTE:
            personal_values = {body.value for body in _PERSONAL_BODIES}
            focus_domain = self._daily_focus_domain(editorial_seed)
            higher_order_candidates.sort(
                key=lambda factor: (
                    -sum(subject in personal_values for subject in factor.subjects),
                    factor.domain is not focus_domain,
                    -factor.salience,
                    factor.id,
                )
            )
        higher_order = None
        if higher_order_candidates:
            if purpose is ReadingPurpose.DAILY_NOTE and editorial_seed:
                # Rotate within the strongest personal factors so a new local day
                # changes the visible synthesis, not merely its revision identity.
                pool = higher_order_candidates[: min(4, len(higher_order_candidates))]
                try:
                    day_index = date.fromisoformat(editorial_seed).toordinal()
                except ValueError:
                    day_index = int(sha256(editorial_seed.encode()).hexdigest()[:8], 16)
                higher_order = pool[day_index % len(pool)]
            else:
                higher_order = higher_order_candidates[0]
        if higher_order is not None:
            selected.append(higher_order)
            selected_ids.add(higher_order.id)
            selected.extend(by_id[ref] for ref in higher_order.child_refs)
            selected_ids.update(higher_order.child_refs)
            if higher_order.tradition is Tradition.WESTERN:
                contextual_house = next(
                    (
                        factor
                        for factor in candidates
                        if factor.kind is FactorKind.HOUSE_PLACEMENT
                        and set(factor.child_refs).intersection(higher_order.child_refs)
                    ),
                    None,
                )
                if contextual_house is not None:
                    selected.append(contextual_house)
                    selected_ids.add(contextual_house.id)

        used_subjects = {subject for factor in selected for subject in factor.subjects}
        for factor in candidates:
            if len(selected) >= maximum:
                break
            if factor.id in selected_ids:
                continue
            if not set(factor.subjects).issubset(used_subjects):
                selected.append(factor)
                selected_ids.add(factor.id)
                used_subjects.update(factor.subjects)
        for factor in candidates:
            if len(selected) >= maximum:
                break
            if factor.id not in selected_ids:
                selected.append(factor)
                selected_ids.add(factor.id)

        for factor in tuple(selected):
            for child_ref in factor.child_refs:
                if child_ref not in selected_ids:
                    selected.append(by_id[child_ref])
                    selected_ids.add(child_ref)

        if higher_order is not None:
            return selected, (higher_order.id,)
        independent = self._independent_pair(selected)
        return selected, tuple(factor.id for factor in independent)

    def _select_transit(
        self,
        chart: NatalChart,
        transits: TransitToNatalSnapshot | None,
        purpose: ReadingPurpose,
        natal_candidates: tuple[DerivedFactor, ...],
    ) -> DerivedFactor | None:
        # Western transit contacts must not leak into Jyotish readings. Jyotish
        # remains natal-only until a dedicated gochara/drishti corpus is approved.
        if (
            transits is None
            or purpose not in _TRANSIT_PURPOSES
            or chart.config.tradition is Tradition.JYOTISH
        ):
            return None
        placement_ids = {
            factor.subjects[0]: factor.id
            for factor in natal_candidates
            if factor.kind is FactorKind.PLANET_PLACEMENT
        }
        eligible = [
            factor
            for contact in transits.contacts
            if (factor := self._transit_factor(chart, contact, placement_ids)) is not None
        ]
        return min(eligible, key=lambda item: (-item.salience, item.id), default=None)

    def _transit_factor(
        self,
        chart: NatalChart,
        contact: TransitToNatalContact,
        placement_ids: dict[str, str],
    ) -> DerivedFactor | None:
        if contact.natal_body not in _PERSONAL_BODIES:
            return None
        natal_ref = placement_ids.get(contact.natal_body.value)
        if natal_ref is None:
            return None
        maximum_orb = transit_orb_limit(contact.transit_body, contact.kind)
        exactness = max(0.0, 1.0 - contact.orb / maximum_orb)
        natal_weight = 1.2 if contact.natal_body in {BodyName.SUN, BodyName.MOON} else 1.0
        salience = exactness * _TRANSIT_BODY_WEIGHT[contact.transit_body] * natal_weight
        if salience < TRANSIT_SALIENCE_THRESHOLD:
            return None
        factor_id = (
            f"transit:{contact.transit_body.value}:{contact.kind}:"
            f"natal:{contact.natal_body.value}:orb:{contact.orb:.3f}:phase:{contact.phase.value}"
        )
        return DerivedFactor(
            id=factor_id,
            tradition=chart.config.tradition,
            source=FactorSource.TRANSIT,
            kind=FactorKind.TRANSIT_CONTACT,
            domain=ReadingDomain.CURRENT_SKY,
            role=FactorRole.TRANSIT,
            subjects=(contact.transit_body.value, contact.natal_body.value),
            evidence_refs=(factor_id,),
            child_refs=(natal_ref,),
            strength=round(exactness, 6),
            salience=round(salience, 6),
            confidence=FactorConfidence.HIGH,
            phase=contact.phase,
            allowed_language=("phase-only timing", "secondary current context"),
            forbidden_language=("calendar dates", "duration", "event prediction"),
        )

    @staticmethod
    def _validate_transits(chart: NatalChart, transits: TransitToNatalSnapshot | None) -> None:
        if transits is None:
            return
        if transits.config.tradition is not chart.config.tradition:
            raise ValueError("transit tradition must match natal tradition")
        if transits.config_hash != chart.config_hash:
            raise ValueError("transit config must match natal config")

    @staticmethod
    def _include_transit_dependency(
        selected: list[DerivedFactor],
        candidates: tuple[DerivedFactor, ...],
        transit: DerivedFactor,
    ) -> list[DerivedFactor]:
        selected_ids = {factor.id for factor in selected}
        candidate_by_id = {factor.id: factor for factor in candidates}
        for child_ref in transit.child_refs:
            if child_ref not in selected_ids:
                selected.append(candidate_by_id[child_ref])
                selected_ids.add(child_ref)
        return selected

    @staticmethod
    def _assign_roles(
        selected: list[DerivedFactor], hero_refs: tuple[str, ...]
    ) -> list[DerivedFactor]:
        assigned = []
        for index, factor in enumerate(selected):
            if factor.source is FactorSource.TRANSIT:
                role = FactorRole.TRANSIT
            elif factor.kind in {FactorKind.NATAL_ASPECT, FactorKind.GRAHA_DRISHTI}:
                role = factor.role
            elif factor.id in hero_refs and index == 0:
                role = FactorRole.PRIMARY
            elif factor.id in hero_refs:
                role = FactorRole.REINFORCEMENT
            else:
                role = FactorRole.SUPPORTING
            assigned.append(
                factor if factor.role is role else factor.model_copy(update={"role": role})
            )
        return assigned

    @staticmethod
    def _independent_pair(
        factors: list[DerivedFactor],
    ) -> tuple[DerivedFactor, ...]:
        natal = [factor for factor in factors if factor.source is FactorSource.NATAL]
        for index, first in enumerate(natal):
            for second in natal[index + 1 :]:
                if set(first.subjects).isdisjoint(second.subjects) and set(
                    first.evidence_refs
                ).isdisjoint(second.evidence_refs):
                    return (first, second)
        return ()

    @staticmethod
    def _composition(*, has_transit: bool) -> CompositionTarget:
        return CompositionTarget(
            natal_percent=70 if has_transit else 100,
            transit_percent=30 if has_transit else 0,
        )

    @staticmethod
    def _purpose_salience(base: float, domain: ReadingDomain, purpose: ReadingPurpose) -> float:
        boost = 0.0
        if purpose is ReadingPurpose.DAILY_NOTE and domain in {
            ReadingDomain.CORE,
            ReadingDomain.EMOTIONS,
        }:
            boost = 0.08
        elif purpose is ReadingPurpose.AURA and domain in {
            ReadingDomain.CORE,
            ReadingDomain.RELATING,
            ReadingDomain.DRIVE,
        }:
            boost = 0.06
        elif purpose is ReadingPurpose.PERSONALIZED_SKY:
            boost = 0.02
        return round(base + boost, 6)

    @staticmethod
    def _shared_domain(first: BodyName, second: BodyName) -> ReadingDomain:
        first_domain = _BODY_DOMAIN[first]
        second_domain = _BODY_DOMAIN[second]
        return first_domain if first_domain is second_domain else ReadingDomain.CORE

    @staticmethod
    def _aspect_role(aspect: Aspect) -> FactorRole:
        if aspect.kind in _TENSION_ASPECTS:
            return FactorRole.TENSION
        if aspect.kind in _HARMONIOUS_ASPECTS:
            return FactorRole.REINFORCEMENT
        return FactorRole.SUPPORTING

    @staticmethod
    def _house_for_longitude(chart: NatalChart, longitude: float) -> int | None:
        if not chart.houses:
            return None
        cusps = sorted(chart.houses, key=lambda house: house.number)
        normalized = longitude % 360
        for index, house in enumerate(cusps):
            start = house.longitude % 360
            end = cusps[(index + 1) % len(cusps)].longitude % 360
            if start <= end and start <= normalized < end:
                return house.number
            if start > end and (normalized >= start or normalized < end):
                return house.number
        return None

    def _build_plan(
        self,
        *,
        tradition: Tradition,
        config_hash: str,
        purpose: ReadingPurpose,
        precision: TimePrecision,
        mode: PlanMode,
        factors: tuple[DerivedFactor, ...],
        hero_factor_refs: tuple[str, ...],
        composition: CompositionTarget,
        background_lens: BackgroundLens | None,
        editorial_seed: str | None,
    ) -> ReadingPlan:
        knowledge_version = (
            WESTERN_INTERPRETATION_KNOWLEDGE_VERSION
            if tradition is Tradition.WESTERN
            else JYOTISH_INTERPRETATION_KNOWLEDGE_VERSION
        )
        payload = {
            "schema_version": "reading-plan/v1",
            "rules_version": PLANNER_RULES_VERSION,
            "knowledge_version": knowledge_version,
            "tradition": tradition.value,
            "config_hash": config_hash,
            "purpose": purpose.value,
            "precision": precision.value,
            "mode": mode.value,
            "factors": [factor.model_dump(mode="json") for factor in factors],
            "hero_factor_refs": hero_factor_refs,
            "composition": composition.model_dump(mode="json"),
            "background_lens": background_lens.value if background_lens else None,
            "editorial_seed": editorial_seed,
            "allowed_language": _PLAN_ALLOWED_LANGUAGE,
            "forbidden_language": _PLAN_FORBIDDEN_LANGUAGE,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return ReadingPlan(
            rules_version=PLANNER_RULES_VERSION,
            knowledge_version=knowledge_version,
            plan_hash=sha256(canonical.encode()).hexdigest()[:32],
            tradition=tradition,
            config_hash=config_hash,
            purpose=purpose,
            precision=precision,
            mode=mode,
            factors=factors,
            hero_factor_refs=hero_factor_refs,
            composition=composition,
            background_lens=background_lens,
            editorial_seed=editorial_seed,
            allowed_language=_PLAN_ALLOWED_LANGUAGE,
            forbidden_language=_PLAN_FORBIDDEN_LANGUAGE,
        )

    @staticmethod
    def _daily_focus_domain(editorial_seed: str | None) -> ReadingDomain:
        domains = (
            ReadingDomain.CORE,
            ReadingDomain.EMOTIONS,
            ReadingDomain.MIND,
            ReadingDomain.RELATING,
            ReadingDomain.DRIVE,
        )
        digest = sha256((editorial_seed or "evergreen").encode()).digest()
        return domains[int.from_bytes(digest[:2], "big") % len(domains)]
