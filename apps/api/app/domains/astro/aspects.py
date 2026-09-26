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
