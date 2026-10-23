import math

from app.domains.astro.models import Aspect, BodyName, BodyPosition

ASPECTS: tuple[tuple[str, float, float], ...] = (
    ("conjunction", 0.0, 8.0),
    ("sextile", 60.0, 5.0),
    ("square", 90.0, 7.0),
    ("trine", 120.0, 7.0),
    ("opposition", 180.0, 8.0),
)

TRANSIT_ORB_VERSION = "transit-orbs-v1"
SYNASTRY_ORB_VERSION = "synastry-orbs-v2"
RELATIONSHIP_CHART_ORB_VERSION = "relationship-chart-orbs-v1"


def transit_orb_limit(body: BodyName, aspect_kind: str) -> float:
    """Return the versioned transit-to-natal orb for a transiting body."""
    if body in {BodyName.SUN, BodyName.MOON}:
        return 2.0 if aspect_kind == "sextile" else 3.0
    if body in {BodyName.MERCURY, BodyName.VENUS, BodyName.MARS}:
        return 2.0 if aspect_kind == "sextile" else 2.5
    return 1.5 if aspect_kind == "sextile" else 2.0


def synastry_orb_limit(body_a: BodyName, body_b: BodyName, aspect_kind: str) -> float:
    """Versioned product orb for cross-chart contacts.

    Luminary contacts receive the documented 5°/4°/3° allowance. Other
    contacts stay tighter so matching copy is not built from weak geometry.
    """
    luminary = BodyName.SUN in {body_a, body_b} or BodyName.MOON in {body_a, body_b}
    if aspect_kind == "sextile":
        return 3.0 if luminary else 2.5
    if aspect_kind in {"square", "trine"}:
        return 4.0 if luminary else 3.0
    return 5.0 if luminary else 3.5


def relationship_chart_orb_limit(aspect_kind: str) -> float:
    if aspect_kind == "sextile":
        return 3.0
    if aspect_kind in {"square", "trine"}:
        return 4.0
    return 5.0


def angular_distance(first: float, second: float) -> float:
    raw = abs(first - second) % 360.0
    return min(raw, 360.0 - raw)


def orb_bounds(
    domain_a: tuple[float, float], domain_b: tuple[float, float], exact_angle: float
) -> tuple[float, float]:
    """``(orb_min, orb_max)`` of an aspect while both longitudes run over their domains.

    Each domain is ``(low, high)`` with ``high`` unwrapped past 360° when it crosses 0°. The
    signed separation then fills ``[b_low - a_high, b_high - a_low]`` exactly (event-spec/v1
    §3, §9). The orb is piecewise linear in it, with breakpoints at multiples of 180° (where the
    angular distance turns) and where the distance equals the aspect angle (orb 0), so both
    extremes are among the interval ends and those breakpoints.
    """

    low = domain_b[0] - domain_a[1]
    high = domain_b[1] - domain_a[0]
    points = [low, high]
    turn = math.ceil(low / 180.0)
    while turn * 180.0 <= high:
        points.append(turn * 180.0)
        turn += 1
    orbs = [abs(angular_distance(point, 0.0) - exact_angle) for point in points]
    # The orb is 0 where the separation is ±angle (mod 360°); is one of those inside?
    crosses = any(
        math.ceil((low - offset) / 360.0) * 360.0 + offset <= high
        for offset in (exact_angle, -exact_angle)
    )
    return (0.0 if crosses else min(orbs)), max(orbs)


def calculate_aspects(bodies: tuple[BodyPosition, ...]) -> tuple[Aspect, ...]:
    aspects: list[Aspect] = []
    for index, body_a in enumerate(bodies):
        for body_b in bodies[index + 1 :]:
            separation = angular_distance(body_a.longitude, body_b.longitude)
            for kind, exact_angle, maximum_orb in ASPECTS:
                orb = abs(separation - exact_angle)
                if orb <= maximum_orb:
                    relative_speed = body_b.longitude_speed - body_a.longitude_speed
                    future_separation = angular_distance(
                        body_a.longitude + body_a.longitude_speed / 24.0,
                        body_b.longitude + body_b.longitude_speed / 24.0,
                    )
                    aspects.append(
                        Aspect(
                            body_a=body_a.body,
                            body_b=body_b.body,
                            kind=kind,
                            exact_angle=exact_angle,
                            orb=orb,
                            applying=abs(future_separation - exact_angle) < orb
                            if relative_speed != 0
                            else False,
                        )
                    )
                    break
    return tuple(aspects)
